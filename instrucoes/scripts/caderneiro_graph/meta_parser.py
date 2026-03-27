"""Parser meta-estrutural do caderneiro.

Extrai nós e arestas que modelam as relações internas do caderneiro:
quais artefatos geracao.md manda criar, quais atualizar-caderno.md
verifica, quais scripts existem no filesystem, e quais operações
modelos.md classifica por nível.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import EdgeInfo, NodeInfo

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Qualified-name helpers
# ---------------------------------------------------------------------------
# Formato: file_path::name — consistente com GraphStore._make_qualified()

_CONDITIONS_FILE = "_meta_conditions"


def _qn_artifact(path: str) -> str:
    """QN de artefato gerado (file_path = instrucoes/geracao.md)."""
    return f"instrucoes/geracao.md::{path}"


def _qn_script(name: str, file_path: str) -> str:
    """QN de script do filesystem."""
    return f"{file_path}::{name}"


def _qn_section(file_path: str, section_name: str) -> str:
    """QN de seção dentro de um arquivo-fonte."""
    return f"{file_path}::{section_name}"


def _qn_rule(file_path: str, section_name: str, rule_name: str) -> str:
    """QN de regra dentro de uma seção (via parent_name)."""
    return f"{file_path}::{section_name}.{rule_name}"


def _qn_condition(expr: str) -> str:
    """QN de condição deduplicada (normalizada)."""
    return f"{_CONDITIONS_FILE}::{expr.lower().strip()}"


def _make_condition_node(expr: str) -> NodeInfo:
    """Cria nó Condition deduplicável por expr normalizada."""
    normalized = expr.lower().strip()
    return NodeInfo(
        kind="Condition",
        name=normalized,
        file_path=_CONDITIONS_FILE,
        line_start=0,
        line_end=0,
        extra={"expression": expr},
    )


# ---------------------------------------------------------------------------
# Source parsers
# ---------------------------------------------------------------------------

# Regex para paths em backticks dentro de bold: **`path`** ou ** `path`**
# O espaço opcional entre ** e ` evita falha silenciosa em variações de formatação.
_RE_BOLD_BACKTICK = re.compile(r"\*\*\s*`([^`]+)`")

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

# Regex para anotações de dependência entre artefatos (Fase 2)
_RE_DEPENDS_ON = re.compile(
    r"<!--\s*depends_on:\s*([^\s|>]+)"
    r"(?:\s*\|\s*tipo:\s*(REQUIRES|REFERENCES))?"
    r"(?:\s*\|\s*quando:\s*([^>]+?))?\s*-->",
    re.IGNORECASE,
)

# Condições comuns extraídas do texto ao redor de artefatos.
# Os padrões aceitam tanto a forma literal ("FERRAMENTA == X") quanto a
# sintaxe de template ("{{FERRAMENTA}} == X"), onde "}}" aparece entre
# o nome da variável e o operador "==".
_CONDITION_PATTERNS = [
    # Aceita "{{FERRAMENTA}} == CLAUDE_CODE" e "FERRAMENTA == CLAUDE_CODE ou AMBAS".
    # Não exige "ou AMBAS" literalmente pois pode haver backtick entre os tokens.
    (re.compile(r"FERRAMENTA\s*(?:}})?\s*==\s*CLAUDE_CODE", re.I), "FERRAMENTA == CLAUDE_CODE ou AMBAS"),
    (re.compile(r"FERRAMENTA\s*(?:}})?\s*==\s*OPENCODE", re.I), "FERRAMENTA == OPENCODE ou AMBAS"),
    (re.compile(r"MODULO_TRANSCRICAO\s*(?:}})?\s*==\s*true", re.I), "MODULO_TRANSCRICAO == true"),
    (re.compile(r"PLATAFORMA\s*(?:}})?\s*==\s*NOTION", re.I), "PLATAFORMA == NOTION"),
    (re.compile(r"sempre\s+gerado", re.I), "sempre"),
]


def _extract_condition(line: str) -> str:
    """Tenta extrair condição de uma linha de geracao.md."""
    for pattern, label in _CONDITION_PATTERNS:
        if pattern.search(line):
            return label
    return "sempre"


def _parse_geracao(
    caderneiro_root: Path,
    conditions_seen: dict[str, NodeInfo],
) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Parseia geracao.md Etapa 8 para extrair artefatos gerados.

    Cria nós Section e Rule além de GeneratedArtifact, e arestas
    CONTAINS (estrutural), VALIDATES e APPLIES_WHEN (semânticas).
    """
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

    if etapa8_start == -1:
        _logger.warning(
            "meta_parser: etapa 'Gerar os arquivos' não encontrada em %s — "
            "nenhum artefato será extraído. Verifique se o heading da etapa "
            "corresponde ao padrão esperado (ex: '8. **Gerar os arquivos').",
            _GERACAO_FILE,
        )

    etapa8_text = content[etapa8_start:etapa9_start] if etapa8_start != -1 else ""

    # Número da linha do início da etapa 8 no arquivo completo
    etapa8_line_offset = content[:etapa8_start].count("\n") + 1 if etapa8_start != -1 else 0

    # Seção "etapa8"
    _ETAPA8 = "etapa8"
    _ETAPA8_QN = _qn_section(_GERACAO_FILE, _ETAPA8)
    nodes.append(NodeInfo(
        kind="Section",
        name=_ETAPA8,
        file_path=_GERACAO_FILE,
        line_start=etapa8_line_offset,
        line_end=etapa8_line_offset,
        extra={"number": "8", "title": "Gerar os arquivos de contexto", "parent_file": _GERACAO_FILE},
    ))
    edges.append(EdgeInfo(
        kind="CONTAINS",
        source=_ROOT_QN,
        target=_ETAPA8_QN,
        file_path=_GERACAO_FILE,
        line=etapa8_line_offset,
    ))

    # Extrair artefatos do Etapa 8 — janela deslizante para capturar depends_on
    lines = etapa8_text.split("\n")
    pending_depends: list[tuple[str, str, str | None]] = []  # (path, tipo, quando)
    _artifact_count = 0

    for i, line in enumerate(lines):
        # Coletar anotações depends_on antes do artefato (Fase 2)
        for m in _RE_DEPENDS_ON.finditer(line):
            dep_path = m.group(1).strip()
            dep_tipo = (m.group(2) or "REQUIRES").upper()
            dep_quando = m.group(3).strip() if m.group(3) else None
            pending_depends.append((dep_path, dep_tipo, dep_quando))
            # Linha com depends_on não tem artefato — continua

        matches = _RE_BOLD_BACKTICK.findall(line)
        for match in matches:
            path = match.strip()
            # Filtrar: só paths que parecem arquivos/diretórios do caderno
            if not any(path.endswith(ext) for ext in (".md", ".json", ".py", "/")):
                if "/" not in path and "." not in path:
                    pending_depends.clear()
                    continue

            condition = _extract_condition(line)
            abs_line = etapa8_line_offset + i

            # Nó GeneratedArtifact (mantido por compatibilidade)
            artifact_node = NodeInfo(
                kind="GeneratedArtifact",
                name=path,
                file_path=_GERACAO_FILE,
                line_start=abs_line,
                line_end=abs_line,
                extra={"condition": condition, "source_section": "etapa8"},
            )
            nodes.append(artifact_node)
            artifact_qn = _qn_artifact(path)
            _artifact_count += 1

            # Aresta GENERATES — atalho de BFS necessário.
            # CONTAINS é excluído do BFS semântico, portanto sem GENERATES
            # o nó SourceFile não alcançaria GeneratedArtifacts no BFS de
            # impacto. VALIDATES (Rule→Artifact) existe para rastreabilidade
            # fina, mas não substitui GENERATES para o BFS de alto nível.
            edges.append(EdgeInfo(
                kind="GENERATES",
                source=_ROOT_QN,
                target=artifact_qn,
                file_path=_GERACAO_FILE,
                line=abs_line,
            ))

            # Nó Rule para este artefato
            rule_node = NodeInfo(
                kind="Rule",
                name=path,
                file_path=_GERACAO_FILE,
                line_start=abs_line,
                line_end=abs_line,
                parent_name=_ETAPA8,
                extra={"text": line.strip(), "condition": condition, "rule_type": "generates"},
            )
            nodes.append(rule_node)
            rule_qn = _qn_rule(_GERACAO_FILE, _ETAPA8, path)

            # CONTAINS: etapa8 → rule
            edges.append(EdgeInfo(
                kind="CONTAINS",
                source=_ETAPA8_QN,
                target=rule_qn,
                file_path=_GERACAO_FILE,
                line=abs_line,
            ))

            # VALIDATES: rule → artifact
            edges.append(EdgeInfo(
                kind="VALIDATES",
                source=rule_qn,
                target=artifact_qn,
                file_path=_GERACAO_FILE,
                line=abs_line,
            ))

            # APPLIES_WHEN: rule → condition (deduplicado).
            # "sempre" não é emitido: ausência de APPLIES_WHEN já implica
            # que a rule é sempre ativa — modelar ausência como restrição
            # explícita é ruído ontológico.
            if condition != "sempre":
                cond_qn = _qn_condition(condition)
                if cond_qn not in conditions_seen:
                    conditions_seen[cond_qn] = _make_condition_node(condition)
                edges.append(EdgeInfo(
                    kind="APPLIES_WHEN",
                    source=rule_qn,
                    target=cond_qn,
                    file_path=_GERACAO_FILE,
                    line=abs_line,
                ))

            # Arestas REQUIRES/REFERENCES acumuladas (Fase 2)
            for dep_path, dep_tipo, dep_quando in pending_depends:
                dep_extra: dict = {"declared_at_line": abs_line}
                if dep_quando:
                    dep_extra["condition"] = dep_quando
                edges.append(EdgeInfo(
                    kind=dep_tipo,
                    source=artifact_qn,
                    target=_qn_artifact(dep_path),
                    file_path=_GERACAO_FILE,
                    line=abs_line,
                    extra=dep_extra,
                ))
            pending_depends = []

    if _artifact_count == 0 and etapa8_text:
        _logger.warning(
            "meta_parser: etapa 'Gerar os arquivos' encontrada em %s mas nenhum "
            "artefato foi extraído. Verifique se os paths estão no formato "
            "**`path`** (bold + backtick). O check_consistency reportará "
            "resultados incorretos.",
            _GERACAO_FILE,
        )

    # Extrair commands da Etapa 9
    etapa9_text = content[etapa9_start:] if etapa9_start < len(content) else ""
    etapa9_line_offset = content[:etapa9_start].count("\n") + 1 if etapa9_start < len(content) else 0

    _ETAPA9 = "etapa9"
    _ETAPA9_QN = _qn_section(_GERACAO_FILE, _ETAPA9)
    if etapa9_text:
        nodes.append(NodeInfo(
            kind="Section",
            name=_ETAPA9,
            file_path=_GERACAO_FILE,
            line_start=etapa9_line_offset,
            line_end=etapa9_line_offset,
            extra={"number": "9", "title": "Criar skills individuais", "parent_file": _GERACAO_FILE},
        ))
        edges.append(EdgeInfo(
            kind="CONTAINS",
            source=_ROOT_QN,
            target=_ETAPA9_QN,
            file_path=_GERACAO_FILE,
            line=etapa9_line_offset,
        ))

    for ext_dir in [".claude/commands/", ".opencode/commands/"]:
        if ext_dir in etapa9_text:
            condition = (
                "FERRAMENTA == CLAUDE_CODE ou AMBAS"
                if ".claude" in ext_dir
                else "FERRAMENTA == OPENCODE ou AMBAS"
            )
            artifact_node = NodeInfo(
                kind="GeneratedArtifact",
                name=ext_dir,
                file_path=_GERACAO_FILE,
                line_start=0,
                line_end=0,
                extra={"condition": condition, "source_section": "etapa9"},
            )
            nodes.append(artifact_node)
            artifact_qn = _qn_artifact(ext_dir)

            edges.append(EdgeInfo(
                kind="GENERATES",
                source=_ROOT_QN,
                target=artifact_qn,
                file_path=_GERACAO_FILE,
            ))

            if etapa9_text:
                rule_node = NodeInfo(
                    kind="Rule",
                    name=ext_dir,
                    file_path=_GERACAO_FILE,
                    line_start=etapa9_line_offset,
                    line_end=etapa9_line_offset,
                    parent_name=_ETAPA9,
                    extra={"text": ext_dir, "condition": condition, "rule_type": "generates"},
                )
                nodes.append(rule_node)
                rule_qn = _qn_rule(_GERACAO_FILE, _ETAPA9, ext_dir)

                edges.append(EdgeInfo(
                    kind="CONTAINS",
                    source=_ETAPA9_QN,
                    target=rule_qn,
                    file_path=_GERACAO_FILE,
                    line=etapa9_line_offset,
                ))
                edges.append(EdgeInfo(
                    kind="VALIDATES",
                    source=rule_qn,
                    target=artifact_qn,
                    file_path=_GERACAO_FILE,
                    line=etapa9_line_offset,
                ))
                cond_qn = _qn_condition(condition)
                if cond_qn not in conditions_seen:
                    conditions_seen[cond_qn] = _make_condition_node(condition)
                edges.append(EdgeInfo(
                    kind="APPLIES_WHEN",
                    source=rule_qn,
                    target=cond_qn,
                    file_path=_GERACAO_FILE,
                    line=etapa9_line_offset,
                ))

    return nodes, edges


def _parse_mapa(
    caderneiro_root: Path,
    conditions_seen: dict[str, NodeInfo],
) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Parseia atualizar-caderno.md para extrair verificações do Mapa de Referência.

    Cada linha do Mapa vira uma aresta CHECKS direta de
    atualizar-caderno.md (SourceFile) para o GeneratedArtifact,
    com metadata (número, condição) na aresta.
    Também cria nós Section, Rule e arestas CONTAINS/VALIDATES/APPLIES_WHEN.
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

    # Encontrar posição do Mapa de Referência no arquivo
    mapa_pos = content.find("Mapa de Referência")
    if mapa_pos == -1:
        mapa_pos = 0
    mapa_line = content[:mapa_pos].count("\n") + 1

    _SECTION = "mapa-de-referencia"
    _SECTION_QN = _qn_section(_MAPA_FILE, _SECTION)
    nodes.append(NodeInfo(
        kind="Section",
        name=_SECTION,
        file_path=_MAPA_FILE,
        line_start=mapa_line,
        line_end=mapa_line,
        extra={"title": "Mapa de Referência", "parent_file": _MAPA_FILE},
    ))
    edges.append(EdgeInfo(
        kind="CONTAINS",
        source=_ROOT_QN,
        target=_SECTION_QN,
        file_path=_MAPA_FILE,
        line=mapa_line,
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

        artifact_qn = _qn_artifact(check_target)

        # Aresta direta: atualizar-caderno.md CHECKS artefato (compatibilidade)
        edges.append(EdgeInfo(
            kind="CHECKS",
            source=_ROOT_QN,
            target=artifact_qn,
            file_path=_MAPA_FILE,
            line=line_num,
            extra={
                "map_number": num,
                "map_target": target_path,
                "condition": condition,
            },
        ))

        # Nó Rule para esta linha do Mapa
        rule_node = NodeInfo(
            kind="Rule",
            name=check_target,
            file_path=_MAPA_FILE,
            line_start=line_num,
            line_end=line_num,
            parent_name=_SECTION,
            extra={"text": target_path, "condition": condition, "rule_type": "checks", "map_number": num},
        )
        nodes.append(rule_node)
        rule_qn = _qn_rule(_MAPA_FILE, _SECTION, check_target)

        # CONTAINS: section → rule
        edges.append(EdgeInfo(
            kind="CONTAINS",
            source=_SECTION_QN,
            target=rule_qn,
            file_path=_MAPA_FILE,
            line=line_num,
        ))

        # VALIDATES: rule → artifact
        edges.append(EdgeInfo(
            kind="VALIDATES",
            source=rule_qn,
            target=artifact_qn,
            file_path=_MAPA_FILE,
            line=line_num,
        ))

        # APPLIES_WHEN: rule → condition (deduplicado).
        # "sempre" não é emitido — ausência de APPLIES_WHEN já implica
        # que a rule é sempre ativa.
        if condition.lower().strip() != "sempre":
            cond_qn = _qn_condition(condition)
            if cond_qn not in conditions_seen:
                conditions_seen[cond_qn] = _make_condition_node(condition)
            edges.append(EdgeInfo(
                kind="APPLIES_WHEN",
                source=rule_qn,
                target=cond_qn,
                file_path=_MAPA_FILE,
                line=line_num,
            ))

    return nodes, edges


def _parse_scripts(caderneiro_root: Path) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Lista recursivamente instrucoes/scripts/ do filesystem.

    Emite arestas CONTAINS de instrucoes/scripts/ (GeneratedArtifact) para
    cada Script, modelando a relação estrutural de pertencimento ao diretório.
    CONTAINS é estrutural e oculto por padrão na visualização.
    """
    scripts_dir = caderneiro_root / "instrucoes" / "scripts"
    if not scripts_dir.is_dir():
        return [], []

    nodes: list[NodeInfo] = []
    edges: list[EdgeInfo] = []
    # QN do diretório instrucoes/scripts/ como GeneratedArtifact (pai CONTAINS)
    _scripts_dir_qn = _qn_artifact("instrucoes/scripts/")

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
                # instrucoes/scripts/ CONTAINS Script (estrutural, oculto por padrão)
                edges.append(EdgeInfo(
                    kind="CONTAINS",
                    source=_scripts_dir_qn,
                    target=_qn_script(path.name + "/", rel_str),
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
            # instrucoes/scripts/ CONTAINS Script (estrutural, oculto por padrão)
            edges.append(EdgeInfo(
                kind="CONTAINS",
                source=_scripts_dir_qn,
                target=_qn_script(path.name, rel_str),
                file_path=rel_str,
            ))

    return nodes, edges


def _parse_script_references(
    caderneiro_root: Path,
    script_nodes: list[NodeInfo],
) -> list[EdgeInfo]:
    """Cria arestas REFERENCES de geracao.md para Scripts mencionados no texto.

    Detecta menções na forma `nome_do_script` em geracao.md e cria aresta
    REFERENCES do SourceFile geracao.md para o nó Script correspondente.
    Conecta Scripts ao grafo semântico, permitindo análise de impacto que
    alcance Scripts a partir de geracao.md.
    """
    geracao_path = caderneiro_root / "instrucoes" / "geracao.md"
    if not geracao_path.is_file() or not script_nodes:
        return []

    content = geracao_path.read_text(encoding="utf-8")
    _GERACAO_FILE = "instrucoes/geracao.md"
    _ROOT_QN = f"{_GERACAO_FILE}::geracao.md"

    edges: list[EdgeInfo] = []
    for node in script_nodes:
        script_qn = f"{node.file_path}::{node.name}"
        # Buscar `nome` como backtick isolado — não como parte de path completo.
        # Ex: `caderneiro_graph/` bate em "`caderneiro_graph/`" mas não em
        # "`instrucoes/scripts/caderneiro_graph/cli.py`".
        pattern = re.compile(r"`" + re.escape(node.name) + r"`")
        m = pattern.search(content)
        if m:
            line_num = content[:m.start()].count("\n") + 1
            edges.append(EdgeInfo(
                kind="REFERENCES",
                source=_ROOT_QN,
                target=script_qn,
                file_path=_GERACAO_FILE,
                line=line_num,
            ))

    return edges


def _parse_modelos(caderneiro_root: Path) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Parseia modelos.md para extrair classificação de nível das operações.

    Cria Section "operacoes-do-caderno" e Rule nodes para cada operação.
    DEFINES_LEVEL é mantido do SourceFile (atalho de BFS), e também emitido
    do Rule para rastreabilidade fina — sem duplicar a contagem em
    check_consistency, pois esta conta apenas arestas com source==SourceFile.
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
    section_line = content[:caderno_section].count("\n") + 1 if caderno_section else 0
    search_text = content[caderno_section:]

    # Seção "operacoes-do-caderno"
    _SECTION = "operacoes-do-caderno"
    _SECTION_QN = _qn_section(_MODELOS_FILE, _SECTION)
    nodes.append(NodeInfo(
        kind="Section",
        name=_SECTION,
        file_path=_MODELOS_FILE,
        line_start=section_line,
        line_end=section_line,
        extra={"title": "Operações do Caderno", "parent_file": _MODELOS_FILE},
    ))
    edges.append(EdgeInfo(
        kind="CONTAINS",
        source=_ROOT_QN,
        target=_SECTION_QN,
        file_path=_MODELOS_FILE,
        line=section_line,
    ))

    for m in _RE_OPERATION_ROW.finditer(search_text):
        name = m.group(1)
        level = m.group(2)
        line_num = content[:caderno_section + m.start()].count("\n") + 1
        artifact_qn = _qn_artifact(f"instrucoes/{name}.md")

        # Aresta DEFINES_LEVEL do SourceFile — atalho de BFS e compatibilidade
        # com check_consistency() que conta arestas DEFINES_LEVEL por kind.
        edges.append(EdgeInfo(
            kind="DEFINES_LEVEL",
            source=_ROOT_QN,
            target=artifact_qn,
            file_path=_MODELOS_FILE,
            line=line_num,
            extra={"operation": name, "level": level},
        ))

        # Nó Rule para esta operação
        rule_node = NodeInfo(
            kind="Rule",
            name=name,
            file_path=_MODELOS_FILE,
            line_start=line_num,
            line_end=line_num,
            parent_name=_SECTION,
            extra={"text": name, "level": level, "rule_type": "defines_level"},
        )
        nodes.append(rule_node)
        rule_qn = _qn_rule(_MODELOS_FILE, _SECTION, name)

        # CONTAINS: section → rule
        edges.append(EdgeInfo(
            kind="CONTAINS",
            source=_SECTION_QN,
            target=rule_qn,
            file_path=_MODELOS_FILE,
            line=line_num,
        ))

        # VALIDATES: rule → artifact (rastreabilidade fina)
        edges.append(EdgeInfo(
            kind="VALIDATES",
            source=rule_qn,
            target=artifact_qn,
            file_path=_MODELOS_FILE,
            line=line_num,
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
    - Section: seções dentro de arquivos-fonte (ex: "Etapa 8")
    - Rule: linhas de regra dentro de seções
    - Condition: expressões de condição deduplicadas

    Arestas:
    - GENERATES: SourceFile → GeneratedArtifact (geracao.md manda criar)
    - CHECKS: SourceFile → GeneratedArtifact (atualizar-caderno.md verifica)
    - DEFINES_LEVEL: SourceFile → GeneratedArtifact (modelos.md classifica nível)
    - CONTAINS: SourceFile→Section, Section→Rule, GeneratedArtifact→Script (hierarquia estrutural)
    - VALIDATES: Rule → GeneratedArtifact (regra exige este artefato)
    - APPLIES_WHEN: Rule → Condition (regra se aplica quando condição é verdadeira)
    - REQUIRES: GeneratedArtifact → GeneratedArtifact (dependência forte)
    - REFERENCES: SourceFile→Script (geracao.md menciona script), GeneratedArtifact→GeneratedArtifact (dependência fraca)
    """
    all_nodes: list[NodeInfo] = []
    all_edges: list[EdgeInfo] = []

    # Dict compartilhado para deduplicação de nós Condition entre parsers
    conditions_seen: dict[str, NodeInfo] = {}

    # Parsers que recebem conditions_seen
    for parser_fn in [_parse_geracao, _parse_mapa]:
        nodes, edges = parser_fn(caderneiro_root, conditions_seen)
        all_nodes.extend(nodes)
        all_edges.extend(edges)

    # _parse_scripts primeiro para alimentar _parse_script_references
    script_nodes, script_edges = _parse_scripts(caderneiro_root)
    all_nodes.extend(script_nodes)
    all_edges.extend(script_edges)

    # REFERENCES de geracao.md para Scripts mencionados no texto
    all_edges.extend(_parse_script_references(caderneiro_root, script_nodes))

    for parser_fn in [_parse_modelos]:
        nodes, edges = parser_fn(caderneiro_root)
        all_nodes.extend(nodes)
        all_edges.extend(edges)

    # Adicionar nós Condition deduplicados (file_path = "_meta_conditions")
    all_nodes.extend(conditions_seen.values())

    return all_nodes, all_edges
