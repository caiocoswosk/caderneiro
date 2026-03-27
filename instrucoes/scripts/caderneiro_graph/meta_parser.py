"""Parser meta-estrutural do caderneiro.

Extrai nós e arestas que modelam as relações internas do caderneiro:
quais artefatos geracao.md manda criar, quais atualizar-caderno.md
verifica, quais scripts existem no filesystem, e quais operações
modelos.md classifica por nível.
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import EdgeInfo, NodeInfo

# ---------------------------------------------------------------------------
# Qualified-name helpers
# ---------------------------------------------------------------------------
# Formato: file_path::name — consistente com GraphStore._make_qualified()


def _qn_artifact(path: str) -> str:
    """QN de artefato gerado (file_path = instrucoes/geracao.md)."""
    return f"instrucoes/geracao.md::{path}"


def _qn_script(name: str, file_path: str) -> str:
    """QN de script do filesystem."""
    return f"{file_path}::{name}"


# ---------------------------------------------------------------------------
# Source parsers
# ---------------------------------------------------------------------------

# Regex para paths em backticks dentro de bold: **`path`**
_RE_BOLD_BACKTICK = re.compile(r"\*\*`([^`]+)`")

# Regex para localizar etapas em geracao.md (insensível ao número da etapa)
_RE_ETAPA_GERAR = re.compile(r"^\d+\.\s+\*\*Gerar os arquivos", re.MULTILINE)
_RE_ETAPA_CRIAR = re.compile(r"^\d+\.\s+\*\*Criar skills", re.MULTILINE)

# Regex para linhas da tabela do Mapa de Referência
# | 1 | `CLAUDE.md` | FERRAMENTA == ... | referência | aspectos |
_RE_MAP_ROW = re.compile(
    r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|",
    re.MULTILINE,
)

# Regex para linhas da tabela de operações em modelos.md
# | processar-aula | COMPLEXO | justificativa |
_RE_OPERATION_ROW = re.compile(
    r"^\|\s*([\w-]+)\s*\|\s*(SIMPLES|MEDIO|COMPLEXO)\s*\|",
    re.MULTILINE,
)

# Condições comuns extraídas do texto ao redor de artefatos
_CONDITION_PATTERNS = [
    (re.compile(r"FERRAMENTA\s*==\s*CLAUDE_CODE\s+ou\s+AMBAS", re.I), "FERRAMENTA == CLAUDE_CODE ou AMBAS"),
    (re.compile(r"FERRAMENTA\s*==\s*OPENCODE\s+ou\s+AMBAS", re.I), "FERRAMENTA == OPENCODE ou AMBAS"),
    (re.compile(r"MODULO_TRANSCRICAO\s*==\s*true", re.I), "MODULO_TRANSCRICAO == true"),
    (re.compile(r"PLATAFORMA\s*==\s*NOTION", re.I), "PLATAFORMA == NOTION"),
    (re.compile(r"sempre\s+gerado", re.I), "sempre"),
]


def _extract_condition(line: str) -> str:
    """Tenta extrair condição de uma linha de geracao.md."""
    for pattern, label in _CONDITION_PATTERNS:
        if pattern.search(line):
            return label
    return "sempre"


def _parse_geracao(caderneiro_root: Path) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Parseia geracao.md Etapa 8 para extrair artefatos gerados."""
    geracao_path = caderneiro_root / "instrucoes" / "geracao.md"
    if not geracao_path.is_file():
        return [], []

    content = geracao_path.read_text(encoding="utf-8")
    _GERACAO_FILE = "instrucoes/geracao.md"
    _ROOT_QN = f"{_GERACAO_FILE}::geracao.md"

    nodes: list[NodeInfo] = []
    edges: list[EdgeInfo] = []

    # Nó raiz representando geracao.md como fonte
    nodes.append(NodeInfo(
        kind="SourceFile",
        name="geracao.md",
        file_path=_GERACAO_FILE,
        line_start=0,
        line_end=0,
        extra={"role": "generator"},
    ))

    # Encontrar etapa "Gerar os arquivos" e etapa seguinte "Criar skills"
    m_gerar = _RE_ETAPA_GERAR.search(content)
    m_criar = _RE_ETAPA_CRIAR.search(content)
    etapa8_start = m_gerar.start() if m_gerar else -1
    etapa9_start = m_criar.start() if m_criar else len(content)

    etapa8_text = content[etapa8_start:etapa9_start] if etapa8_start != -1 else ""

    # Extrair artefatos do Etapa 8
    lines = etapa8_text.split("\n")
    for i, line in enumerate(lines):
        matches = _RE_BOLD_BACKTICK.findall(line)
        for match in matches:
            path = match.strip()
            # Filtrar: só paths que parecem arquivos/diretórios do caderno
            if not any(path.endswith(ext) for ext in (".md", ".json", ".py", "/")):
                # Verificar se é um path sem extensão mas parece diretório
                if "/" not in path and "." not in path:
                    continue

            condition = _extract_condition(line)
            node = NodeInfo(
                kind="GeneratedArtifact",
                name=path,
                file_path="instrucoes/geracao.md",
                line_start=i + 1,
                line_end=i + 1,
                extra={"condition": condition, "source_section": "etapa8"},
            )
            nodes.append(node)
            edges.append(EdgeInfo(
                kind="GENERATES",
                source=_ROOT_QN,
                target=_qn_artifact(path),
                file_path="instrucoes/geracao.md",
                line=i + 1,
            ))

    # Extrair commands da Etapa 9
    etapa9_text = content[etapa9_start:] if etapa9_start < len(content) else ""
    for ext_dir in [".claude/commands/", ".opencode/commands/"]:
        if ext_dir in etapa9_text:
            condition = (
                "FERRAMENTA == CLAUDE_CODE ou AMBAS"
                if ".claude" in ext_dir
                else "FERRAMENTA == OPENCODE ou AMBAS"
            )
            node = NodeInfo(
                kind="GeneratedArtifact",
                name=ext_dir,
                file_path="instrucoes/geracao.md",
                line_start=0,
                line_end=0,
                extra={"condition": condition, "source_section": "etapa9"},
            )
            nodes.append(node)
            edges.append(EdgeInfo(
                kind="GENERATES",
                source=_ROOT_QN,
                target=_qn_artifact(ext_dir),
                file_path="instrucoes/geracao.md",
            ))

    return nodes, edges


def _parse_mapa(caderneiro_root: Path) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Parseia atualizar-caderno.md para extrair verificações do Mapa de Referência.

    Cada linha do Mapa vira uma aresta CHECKS direta de
    atualizar-caderno.md (SourceFile) para o GeneratedArtifact,
    com metadata (número, condição) na aresta.
    """
    mapa_path = caderneiro_root / "instrucoes" / "atualizar-caderno.md"
    if not mapa_path.is_file():
        return [], []

    content = mapa_path.read_text(encoding="utf-8")
    _MAPA_FILE = "instrucoes/atualizar-caderno.md"
    _ROOT_QN = f"{_MAPA_FILE}::atualizar-caderno.md"

    nodes: list[NodeInfo] = []
    edges: list[EdgeInfo] = []

    # Nó raiz representando atualizar-caderno.md como fonte
    nodes.append(NodeInfo(
        kind="SourceFile",
        name="atualizar-caderno.md",
        file_path=_MAPA_FILE,
        line_start=0,
        line_end=0,
        extra={"role": "validator"},
    ))

    for m in _RE_MAP_ROW.finditer(content):
        num = int(m.group(1))
        target_path = m.group(2).strip()
        condition = m.group(3).strip()
        line_num = content[:m.start()].count("\n") + 1

        # Normalizar wildcards para diretório base
        check_target = target_path
        if "*" in check_target:
            check_target = check_target.rsplit("/", 1)[0] + "/"

        # Aresta direta: atualizar-caderno.md CHECKS artefato
        edges.append(EdgeInfo(
            kind="CHECKS",
            source=_ROOT_QN,
            target=_qn_artifact(check_target),
            file_path=_MAPA_FILE,
            line=line_num,
            extra={
                "map_number": num,
                "map_target": target_path,
                "condition": condition,
            },
        ))

    return nodes, edges


def _parse_scripts(caderneiro_root: Path) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Lista recursivamente instrucoes/scripts/ do filesystem."""
    scripts_dir = caderneiro_root / "instrucoes" / "scripts"
    if not scripts_dir.is_dir():
        return [], []

    nodes: list[NodeInfo] = []
    edges: list[EdgeInfo] = []

    for path in sorted(scripts_dir.rglob("*")):
        if path.name.startswith(".") and path.name != ".gitignore":
            continue
        if path.name == "__pycache__":
            continue
        if path.suffix == ".pyc":
            continue

        rel = path.relative_to(caderneiro_root)
        rel_str = str(rel)

        # Para diretórios, registrar apenas o diretório de primeiro nível
        if path.is_dir():
            # Só registrar subdiretórios diretos de scripts/
            if path.parent == scripts_dir:
                node = NodeInfo(
                    kind="Script",
                    name=path.name + "/",
                    file_path=rel_str,
                    line_start=0,
                    line_end=0,
                    extra={"type": "directory"},
                )
                nodes.append(node)
                edges.append(EdgeInfo(
                    kind="COPIES",
                    source=_qn_script(path.name + "/", rel_str),
                    target=_qn_artifact("instrucoes/scripts/"),
                    file_path=rel_str,
                ))
            continue

        # Arquivos diretamente em scripts/ (não em subdiretórios)
        if path.parent == scripts_dir:
            node = NodeInfo(
                kind="Script",
                name=path.name,
                file_path=rel_str,
                line_start=0,
                line_end=0,
                extra={"type": "file"},
            )
            nodes.append(node)
            edges.append(EdgeInfo(
                kind="COPIES",
                source=_qn_script(path.name, rel_str),
                target=_qn_artifact("instrucoes/scripts/"),
                file_path=rel_str,
            ))

    return nodes, edges


def _parse_modelos(caderneiro_root: Path) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Parseia modelos.md para extrair classificação de nível das operações.

    Cada operação vira uma aresta DEFINES_LEVEL direta de
    modelos.md (SourceFile) para o GeneratedArtifact correspondente,
    com metadata (nível) na aresta.
    """
    modelos_path = caderneiro_root / "instrucoes" / "modelos.md"
    if not modelos_path.is_file():
        return [], []

    content = modelos_path.read_text(encoding="utf-8")
    _MODELOS_FILE = "instrucoes/modelos.md"
    _ROOT_QN = f"{_MODELOS_FILE}::modelos.md"

    nodes: list[NodeInfo] = []
    edges: list[EdgeInfo] = []

    # Nó raiz representando modelos.md como fonte
    nodes.append(NodeInfo(
        kind="SourceFile",
        name="modelos.md",
        file_path=_MODELOS_FILE,
        line_start=0,
        line_end=0,
        extra={"role": "model-levels"},
    ))

    # Procurar na seção "Operações do Caderno"
    caderno_section = content.find("Operações do Caderno")
    if caderno_section == -1:
        caderno_section = 0
    search_text = content[caderno_section:]

    for m in _RE_OPERATION_ROW.finditer(search_text):
        name = m.group(1)
        level = m.group(2)
        line_num = content[:caderno_section + m.start()].count("\n") + 1

        # Aresta direta: modelos.md DEFINES_LEVEL artefato de instrução
        edges.append(EdgeInfo(
            kind="DEFINES_LEVEL",
            source=_ROOT_QN,
            target=_qn_artifact(f"instrucoes/{name}.md"),
            file_path=_MODELOS_FILE,
            line=line_num,
            extra={"operation": name, "level": level},
        ))

    return nodes, edges


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_meta(caderneiro_root: Path) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Parseia a meta-estrutura do caderneiro.

    Retorna nós e arestas representando:
    - SourceFile: arquivos-fonte (geracao.md, atualizar-caderno.md, modelos.md)
    - GeneratedArtifact: artefatos que geracao.md manda criar em cadernos
    - Script: arquivos/diretórios em instrucoes/scripts/ (filesystem)

    Arestas:
    - GENERATES: SourceFile → GeneratedArtifact (geracao.md manda criar)
    - CHECKS: SourceFile → GeneratedArtifact (atualizar-caderno.md verifica)
    - COPIES: Script → GeneratedArtifact (script é copiado para o caderno)
    - DEFINES_LEVEL: SourceFile → GeneratedArtifact (modelos.md classifica nível)
    """
    all_nodes: list[NodeInfo] = []
    all_edges: list[EdgeInfo] = []

    for parser_fn in [_parse_geracao, _parse_mapa, _parse_scripts, _parse_modelos]:
        nodes, edges = parser_fn(caderneiro_root)
        all_nodes.extend(nodes)
        all_edges.extend(edges)

    return all_nodes, all_edges
