#!/usr/bin/env python3
"""Gerador SSoT do meta-grafo do caderneiro.

Lê instrucoes/meta-schema.yaml e atualiza as zonas estruturais de:
  - instrucoes/modelos.md        (tabela operação → nível)
  - instrucoes/atualizar-caderno.md  (Mapa de Referência, blocos 1 e 2)

geracao.md NÃO é modificado — apenas validado com warnings.

Uso direto:
    python3 instrucoes/scripts/meta_generate.py [--caderno .] [--dry-run] [-v]

Ou via CLI do caderneiro_graph:
    python3 instrucoes/scripts/caderneiro_graph/cli.py --caderno . meta generate [--dry-run]
"""

from __future__ import annotations

import argparse
import difflib
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Campos obrigatórios em cada entrada do schema
_REQUIRED_FIELDS = {
    "nome", "nivel", "artefato", "condicao", "justificativa",
    "mapa_block", "map_number", "geracao_reference", "map_aspects",
}


# ---------------------------------------------------------------------------
# Carregamento do schema
# ---------------------------------------------------------------------------

def load_schema(caderneiro_root: Path) -> dict:
    """Lê e valida instrucoes/meta-schema.yaml."""
    try:
        import yaml  # type: ignore
    except ImportError:
        raise RuntimeError(
            "PyYAML não instalado. Execute: pip install pyyaml"
        )

    schema_path = caderneiro_root / "instrucoes" / "meta-schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema não encontrado: {schema_path}\n"
            "Crie instrucoes/meta-schema.yaml antes de executar meta generate."
        )

    with schema_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    operacoes = data.get("operacoes", [])
    for op in operacoes:
        missing = _REQUIRED_FIELDS - set(op.keys())
        if missing:
            raise ValueError(
                f"Campo(s) obrigatório(s) ausente(s) na operação '{op.get('nome', '?')}': "
                + ", ".join(sorted(missing))
            )

    return data


# ---------------------------------------------------------------------------
# Renderização de zonas
# ---------------------------------------------------------------------------

def _parse_existing_justificativas(zone_content: str) -> dict[str, str]:
    """Extrai justificativas existentes da zona de modelos para preservação."""
    result: dict[str, str] = {}
    for line in zone_content.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        parts = [c.strip() for c in line.strip("|").split("|")]
        if len(parts) >= 3:
            result[parts[0]] = parts[2]
    return result


def render_modelos_zone(operations: list[dict], existing_zone: str = "") -> str:
    """Gera linhas da tabela de modelos ordenadas por map_number."""
    existing = _parse_existing_justificativas(existing_zone)
    sorted_ops = sorted(operations, key=lambda o: o["map_number"])
    lines = []
    for op in sorted_ops:
        justificativa = existing.get(op["nome"], op["justificativa"])
        lines.append(f"| {op['nome']} | {op['nivel']} | {justificativa} |")
    return "\n".join(lines)


def render_mapa_zone(operations: list[dict], block_num: int) -> str:
    """Gera linhas do Mapa de Referência para um bloco, ordenadas por map_number."""
    block_ops = [o for o in operations if o["mapa_block"] == block_num]
    sorted_ops = sorted(block_ops, key=lambda o: o["map_number"])
    lines = []
    for op in sorted_ops:
        artefato = op["artefato"]
        # Normaliza map_aspects: remove quebras de linha internas (vem de yaml >-)
        aspects = " ".join(op["map_aspects"].split())
        lines.append(
            f"| {op['map_number']} | `{artefato}` | {op['condicao']} "
            f"| `{op['geracao_reference']}` | {aspects} |"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reescrita de zona
# ---------------------------------------------------------------------------

def rewrite_zone(content: str, marker_prefix: str, new_zone: str) -> tuple[str, bool]:
    """Substitui conteúdo entre markers HTML de geração.

    Markers esperados:
        <!-- meta-generate:{marker_prefix}:start -->
        <!-- meta-generate:{marker_prefix}:end -->

    Retorna (novo_conteúdo, houve_mudança).
    Levanta RuntimeError se os markers não forem encontrados.
    """
    start_marker = f"<!-- meta-generate:{marker_prefix}:start -->"
    end_marker = f"<!-- meta-generate:{marker_prefix}:end -->"

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        raise RuntimeError(
            f"Markers não encontrados para '{marker_prefix}'.\n"
            f"Adicione ao arquivo:\n  {start_marker}\n  {end_marker}"
        )

    # Conteúdo atual entre os markers (excluindo os próprios markers e suas linhas)
    after_start = content.index("\n", start_idx) + 1
    before_end = content.rindex("\n", 0, end_idx)
    current_zone = content[after_start:before_end]

    if current_zone == new_zone:
        return content, False

    new_content = content[:after_start] + new_zone + content[before_end:]
    return new_content, True


# ---------------------------------------------------------------------------
# Validação de geracao.md (somente warnings)
# ---------------------------------------------------------------------------

_RE_BOLD_BACKTICK = re.compile(r"\*\*`([^`]+)`\*\*")


def validate_geracao(caderneiro_root: Path, operations: list[dict]) -> list[str]:
    """Verifica presença de cada operação na Etapa 8 de geracao.md.

    Retorna lista de warnings (não bloqueia a geração).
    """
    geracao_path = caderneiro_root / "instrucoes" / "geracao.md"
    if not geracao_path.exists():
        return [f"geracao.md não encontrado: {geracao_path}"]

    content = geracao_path.read_text(encoding="utf-8")

    # Encontrar seção Etapa 8
    etapa8_match = re.search(r"^## Etapa 8", content, re.MULTILINE)
    etapa9_match = re.search(r"^## Etapa 9", content, re.MULTILINE)

    if etapa8_match:
        start = etapa8_match.start()
        end = etapa9_match.start() if etapa9_match else len(content)
        etapa8_content = content[start:end]
    else:
        etapa8_content = content

    mentioned = set(_RE_BOLD_BACKTICK.findall(etapa8_content))

    warnings = []
    for op in operations:
        artefato = op["artefato"]
        # Verifica tanto o caminho completo quanto só o nome do arquivo
        filename = Path(artefato).name
        if artefato not in mentioned and filename not in mentioned:
            warnings.append(
                f"  ⚠️  '{op['nome']}': '{artefato}' não encontrado na Etapa 8 de geracao.md"
            )
    return warnings


# ---------------------------------------------------------------------------
# Execução de meta check
# ---------------------------------------------------------------------------

def run_meta_check(caderneiro_root: Path) -> tuple[bool, str]:
    """Executa meta check e retorna (passou, output)."""
    cli_path = caderneiro_root / "instrucoes" / "scripts" / "caderneiro_graph" / "cli.py"
    result = subprocess.run(
        [sys.executable, str(cli_path), "--caderno", str(caderneiro_root), "meta", "check"],
        capture_output=True,
        text=True,
    )
    output = (result.stdout + result.stderr).strip()
    passed = result.returncode == 0 and "nenhum gap" in output
    return passed, output


# ---------------------------------------------------------------------------
# Diff helper
# ---------------------------------------------------------------------------

def _show_diff(original: str, updated: str, filename: str) -> None:
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )
    sys.stdout.writelines(diff)


# ---------------------------------------------------------------------------
# Entrada principal
# ---------------------------------------------------------------------------

def generate(
    caderneiro_root: Path,
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> int:
    """Workflow A3: atualiza zonas e verifica consistência após cada arquivo.

    Retorna 0 em sucesso, 1 em falha.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    # 1. Carregar schema
    try:
        schema = load_schema(caderneiro_root)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1

    operations = schema["operacoes"]
    modified_files: list[str] = []

    # 2. Atualizar modelos.md
    modelos_path = caderneiro_root / "instrucoes" / "modelos.md"
    try:
        modelos_content = modelos_path.read_text(encoding="utf-8")
        # Extrair zona atual para preservar justificativas
        sm = modelos_content.find("<!-- meta-generate:modelos:start -->")
        em = modelos_content.find("<!-- meta-generate:modelos:end -->")
        existing_zone = ""
        if sm != -1 and em != -1:
            after_sm = modelos_content.index("\n", sm) + 1
            before_em = modelos_content.rindex("\n", 0, em)
            existing_zone = modelos_content[after_sm:before_em]

        new_zone = render_modelos_zone(operations, existing_zone)
        updated, changed = rewrite_zone(modelos_content, "modelos", new_zone)
    except RuntimeError as e:
        print(f"ERRO em modelos.md: {e}", file=sys.stderr)
        return 1

    if changed:
        if dry_run:
            print(f"\n--- dry-run: modelos.md ---")
            _show_diff(modelos_content, updated, "instrucoes/modelos.md")
        else:
            modelos_path.write_text(updated, encoding="utf-8")
        modified_files.append("instrucoes/modelos.md")

        if not dry_run:
            # A3: verificar após modelos.md
            passed, output = run_meta_check(caderneiro_root)
            if not passed:
                print(f"\nERRO: meta check falhou após atualizar modelos.md:\n{output}", file=sys.stderr)
                return 1

    # 3. Atualizar atualizar-caderno.md (blocos 1 e 2)
    mapa_path = caderneiro_root / "instrucoes" / "atualizar-caderno.md"
    try:
        mapa_content = mapa_path.read_text(encoding="utf-8")
        updated_mapa = mapa_content
        mapa_changed = False

        for block_num in sorted({op["mapa_block"] for op in operations}):
            new_zone = render_mapa_zone(operations, block_num)
            updated_mapa, changed = rewrite_zone(updated_mapa, f"mapa:{block_num}", new_zone)
            if changed:
                mapa_changed = True
    except RuntimeError as e:
        print(f"ERRO em atualizar-caderno.md: {e}", file=sys.stderr)
        return 1

    if mapa_changed:
        if dry_run:
            print(f"\n--- dry-run: atualizar-caderno.md ---")
            _show_diff(mapa_content, updated_mapa, "instrucoes/atualizar-caderno.md")
        else:
            mapa_path.write_text(updated_mapa, encoding="utf-8")
        modified_files.append("instrucoes/atualizar-caderno.md")

        if not dry_run:
            # A3: verificar após atualizar-caderno.md
            passed, output = run_meta_check(caderneiro_root)
            if not passed:
                print(f"\nERRO: meta check falhou após atualizar atualizar-caderno.md:\n{output}", file=sys.stderr)
                return 1

    # 4. Validar geracao.md (somente warnings)
    warnings = validate_geracao(caderneiro_root, operations)
    if warnings:
        print("\nAVISOS — geracao.md (não bloqueante):")
        for w in warnings:
            print(w)
        print("  → Atualize geracao.md Etapa 8 manualmente para cada item acima.\n")

    # 5. Sumário
    if not modified_files:
        print("Nenhuma modificação necessária.")
    elif dry_run:
        print(f"\n[dry-run] Arquivos que seriam modificados: {', '.join(modified_files)}")
    else:
        print(f"\nModificados: {', '.join(modified_files)}")
        print("Meta check: OK")

    return 0


# ---------------------------------------------------------------------------
# Invocação direta
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador SSoT do meta-grafo do caderneiro")
    parser.add_argument("--caderno", default=".", help="Raiz do caderneiro")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar diff sem modificar arquivos")
    parser.add_argument("-v", "--verbose", action="store_true", help="Logging detalhado")
    args = parser.parse_args()
    sys.exit(generate(Path(args.caderno).resolve(), dry_run=args.dry_run, verbose=args.verbose))
