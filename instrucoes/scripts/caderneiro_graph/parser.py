"""Parser de markdown acadêmico para extração de nós e arestas.

Suporta os 3 templates (Técnico, Teórico, Híbrido) com headings H1-H4.
Extrai Topic, Lesson, Concept, Section, Exercise, GlossaryTerm, Formula.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .models import EdgeInfo, NodeInfo

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# H1: Topic
RE_H1 = re.compile(r"^# (\S+)\s+(.+)$")

# H2: Aula
RE_H2_AULA = re.compile(r"^## Aula (\d+):?\s*(.+)")

# H2: Seções especiais (skip)
RE_H2_SKIP = re.compile(r"^## (Sumário|Referências|📚)")

# H2 genérico
RE_H2 = re.compile(r"^## (.+)")

# H3 genérico
RE_H3 = re.compile(r"^### (.+)")

# H4 genérico
RE_H4 = re.compile(r"^#### (.+)")

# Metadata da aula
RE_DATE = re.compile(r"📅\s*Data de Adição:\s*(.+)")
RE_STUDY_TIME = re.compile(r"⏱️\s*Tempo Estimado.*?:\s*(.+)")
RE_DIFFICULTY = re.compile(r"📊\s*Dificuldade:\s*(.+)")

# Tempo total do tópico
RE_TOTAL_TIME = re.compile(r"⏱️\s*\*\*Tempo total de estudo:\*\*\s*(.+)")

# H3: padrões por tipo
RE_H3_SKIP = re.compile(r"^### 📌 Objetivos|^### 📝 TL;DR")

RE_H3_CONCEPT = re.compile(
    r"^### (?:"
    r"🎯 (?:Conceito|Introdução|Parte \d+.*)|"
    r"📖 Definição Formal|"
    r"💻 (?:Implementação|Parte \d+.*)|"
    r"🔍 (?:Quando Usar|Propriedades)|"
    r"📊 (?:Comparação.*|Análise.*)|"
    r"💡 (?:Intuição|Dica)|"
    r"🔄 (?:Integração|Parte \d+.*)"
    r")"
)

RE_H3_GLOSSARY = re.compile(r"^### 📖 Glossário")

RE_H3_EXERCISE = re.compile(r"^### ✏️ Exercícios")

# H4: sub-seções
RE_H4_CONCEPT = re.compile(
    r"^#### (?:Conceito|Propriedades|Algoritmo|Código Completo|"
    r"Implementação.*|Conexão.*|Diagrama.*|Aplicações.*|"
    r"Versão .*|Pontos-chave)"
)

RE_H4_EXERCISE = re.compile(r"^#### Exercícios.*")

# Exercícios (marcadores de dificuldade)
RE_EXERCISE_MARKER = re.compile(r"^(🟢|🟡|🔴)\s*\*\*(.+?)\*\*")

# Glossário: termos dentro de <details>
RE_GLOSSARY_TERM = re.compile(r"[-*]\s*\*\*(.+?):\*\*\s*(.+)")

# Fórmulas display math
RE_FORMULA = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)

# Links markdown
RE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# Pré-requisitos explícitos
RE_PREREQUISITE = re.compile(r"^>\s*📋\s*Pré-requisito:\s*\[(.+?)\]\((.+?)\)")


# ---------------------------------------------------------------------------
# Slugify
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    """Converte texto em slug para qualified names."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


# ---------------------------------------------------------------------------
# Heading detection
# ---------------------------------------------------------------------------

def _detect_heading_level(line: str) -> Optional[int]:
    """Retorna o nível do heading (1-4) ou None."""
    if line.startswith("#### "):
        return 4
    if line.startswith("### "):
        return 3
    if line.startswith("## "):
        return 2
    if line.startswith("# ") and not line.startswith("##"):
        return 1
    return None


def _find_section_end(lines: list[str], start: int, max_level: int) -> int:
    """Encontra a linha final de uma seção (antes do próximo heading de nível <= max_level)."""
    for i in range(start + 1, len(lines)):
        level = _detect_heading_level(lines[i])
        if level is not None and level <= max_level:
            return i - 1
    return len(lines) - 1


# ---------------------------------------------------------------------------
# Topic file parser
# ---------------------------------------------------------------------------

def parse_topic_file(file_path: str, content: str) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Extrai nós e arestas de um arquivo de conteúdo (conteudos/*.md)."""
    lines = content.splitlines()
    nodes: list[NodeInfo] = []
    edges: list[EdgeInfo] = []

    topic_qn: Optional[str] = None
    current_lesson_qn: Optional[str] = None
    prev_lesson_qn: Optional[str] = None
    current_h3_qn: Optional[str] = None
    current_h3_kind: Optional[str] = None
    lesson_num: Optional[str] = None
    exercise_counter = 0
    formula_counter = 0
    in_sumario = False

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1
        stripped = line.strip()

        # Track se estamos dentro de ## Sumário
        if RE_H2_SKIP.match(stripped):
            in_sumario = True
            continue
        if stripped.startswith("## ") and not RE_H2_SKIP.match(stripped):
            in_sumario = False

        # ---- H1: Topic ----
        m = RE_H1.match(stripped)
        if m and topic_qn is None:
            emoji, name = m.group(1), m.group(2)
            topic_qn = file_path
            section_end = len(lines)

            extra: dict = {"emoji": emoji}
            # Procurar tempo total nas próximas linhas
            for j in range(line_idx + 1, min(line_idx + 10, len(lines))):
                tm = RE_TOTAL_TIME.match(lines[j].strip())
                if tm:
                    extra["total_study_time"] = tm.group(1).strip()
                    break

            nodes.append(NodeInfo(
                kind="Topic", name=name, file_path=file_path,
                line_start=1, line_end=section_end, extra=extra,
            ))
            continue

        # ---- H2: Aula ----
        m = RE_H2_AULA.match(stripped)
        if m and topic_qn:
            lesson_num = m.group(1).zfill(2)
            lesson_name = m.group(2).strip()
            current_lesson_qn = f"{file_path}::aula-{lesson_num}"
            current_h3_qn = None
            current_h3_kind = None
            exercise_counter = 0
            formula_counter = 0

            section_end_line = _find_section_end(lines, line_idx, 2)

            extra = {}
            # Metadata nas linhas seguintes
            for j in range(line_idx + 1, min(line_idx + 8, len(lines))):
                sl = lines[j].strip()
                dm = RE_DATE.match(sl)
                if dm:
                    extra["date"] = dm.group(1).strip()
                tm = RE_STUDY_TIME.match(sl)
                if tm:
                    extra["study_time"] = tm.group(1).strip()
                dfm = RE_DIFFICULTY.match(sl)
                if dfm:
                    difficulty = dfm.group(1).strip()

            difficulty_val = extra.get("difficulty") or (difficulty if "difficulty" in dir() else None)  # noqa: F821

            nodes.append(NodeInfo(
                kind="Lesson", name=lesson_name, file_path=file_path,
                line_start=line_num, line_end=section_end_line + 1,
                parent_name=None, difficulty=difficulty_val, extra=extra,
            ))

            # CONTAINS: Topic → Lesson
            edges.append(EdgeInfo(
                kind="CONTAINS", source=topic_qn, target=current_lesson_qn,
                file_path=file_path, line=line_num,
            ))

            # EXTENDS: Lesson anterior → Lesson atual
            if prev_lesson_qn:
                edges.append(EdgeInfo(
                    kind="EXTENDS", source=prev_lesson_qn, target=current_lesson_qn,
                    file_path=file_path, line=line_num,
                ))
            prev_lesson_qn = current_lesson_qn

            # Extrair difficulty corretamente
            for j in range(line_idx + 1, min(line_idx + 8, len(lines))):
                sl = lines[j].strip()
                dfm = RE_DIFFICULTY.match(sl)
                if dfm:
                    nodes[-1].difficulty = dfm.group(1).strip()
                    break
            continue

        # Pular seções de sumário/referências
        if in_sumario:
            continue

        # ---- H3 ----
        if RE_H3.match(stripped) and current_lesson_qn:
            current_h3_qn = None
            current_h3_kind = None

            # Skip: Objetivos, TL;DR
            if RE_H3_SKIP.match(stripped):
                continue

            h3_text = stripped[4:]  # Remove "### "
            section_end_line = _find_section_end(lines, line_idx, 3)

            # Glossário
            if RE_H3_GLOSSARY.match(stripped):
                current_h3_kind = "glossary"
                _extract_glossary_terms(
                    lines, line_idx, section_end_line, file_path,
                    current_lesson_qn, lesson_num, nodes, edges,
                )
                continue

            # Exercícios
            if RE_H3_EXERCISE.match(stripped):
                current_h3_kind = "exercise"
                current_h3_qn = f"{current_lesson_qn}.section.exercicios"
                _extract_exercises(
                    lines, line_idx, section_end_line, file_path,
                    current_lesson_qn, lesson_num, exercise_counter, nodes, edges,
                )
                # Atualizar counter
                for j in range(line_idx + 1, section_end_line + 1):
                    if RE_EXERCISE_MARKER.match(lines[j].strip()):
                        exercise_counter += 1
                continue

            # Concept
            if RE_H3_CONCEPT.match(stripped):
                slug = _slugify(h3_text)
                current_h3_qn = f"{current_lesson_qn}.concept.{slug}"
                current_h3_kind = "concept"
                nodes.append(NodeInfo(
                    kind="Concept", name=h3_text, file_path=file_path,
                    line_start=line_num, line_end=section_end_line + 1,
                    parent_name=f"aula-{lesson_num}",
                    extra={"section_type": _detect_section_type(h3_text)},
                ))
                edges.append(EdgeInfo(
                    kind="CONTAINS", source=current_lesson_qn, target=current_h3_qn,
                    file_path=file_path, line=line_num,
                ))
            else:
                # Section genérica
                slug = _slugify(h3_text)
                current_h3_qn = f"{current_lesson_qn}.section.{slug}"
                current_h3_kind = "section"
                nodes.append(NodeInfo(
                    kind="Section", name=h3_text, file_path=file_path,
                    line_start=line_num, line_end=section_end_line + 1,
                    parent_name=f"aula-{lesson_num}",
                ))
                edges.append(EdgeInfo(
                    kind="CONTAINS", source=current_lesson_qn, target=current_h3_qn,
                    file_path=file_path, line=line_num,
                ))
            continue

        # ---- H4 ----
        m_h4 = RE_H4.match(stripped)
        if m_h4 and current_h3_qn and current_lesson_qn:
            h4_text = stripped[5:]  # Remove "#### "
            section_end_line = _find_section_end(lines, line_idx, 4)

            # Exercícios em H4
            if RE_H4_EXERCISE.match(stripped):
                _extract_exercises(
                    lines, line_idx, section_end_line, file_path,
                    current_lesson_qn, lesson_num, exercise_counter, nodes, edges,
                    parent_qn=current_h3_qn,
                )
                for j in range(line_idx + 1, section_end_line + 1):
                    if RE_EXERCISE_MARKER.match(lines[j].strip()):
                        exercise_counter += 1
                continue

            # Concept em H4
            if RE_H4_CONCEPT.match(stripped):
                slug = _slugify(h4_text)
                h4_qn = f"{current_h3_qn}.concept.{slug}"
                nodes.append(NodeInfo(
                    kind="Concept", name=h4_text, file_path=file_path,
                    line_start=line_num, line_end=section_end_line + 1,
                    parent_name=current_h3_qn.split("::")[-1] if "::" in current_h3_qn else None,
                    extra={"section_type": _detect_section_type(h4_text)},
                ))
                edges.append(EdgeInfo(
                    kind="CONTAINS", source=current_h3_qn, target=h4_qn,
                    file_path=file_path, line=line_num,
                ))
                continue

            # Section genérica H4
            slug = _slugify(h4_text)
            h4_qn = f"{current_h3_qn}.section.{slug}"
            nodes.append(NodeInfo(
                kind="Section", name=h4_text, file_path=file_path,
                line_start=line_num, line_end=section_end_line + 1,
                parent_name=current_h3_qn.split("::")[-1] if "::" in current_h3_qn else None,
            ))
            edges.append(EdgeInfo(
                kind="CONTAINS", source=current_h3_qn, target=h4_qn,
                file_path=file_path, line=line_num,
            ))
            continue

        # ---- Pré-requisitos ----
        m_pre = RE_PREREQUISITE.match(stripped)
        if m_pre and topic_qn:
            target_file = m_pre.group(2).strip()
            # Resolver caminho relativo
            if not target_file.startswith("conteudos/"):
                base_dir = str(Path(file_path).parent)
                target_file = str(Path(base_dir) / target_file)
            edges.append(EdgeInfo(
                kind="PREREQUISITE", source=topic_qn, target=target_file,
                file_path=file_path, line=line_num,
                extra={"confidence": "explicit"},
            ))
            continue

    # ---- Fórmulas display math (associar ao lesson correto por range de linhas) ----
    # Coletar mapping lesson_qn -> (line_start, line_end, lesson_num)
    lesson_ranges: list[tuple[str, int, int, str]] = []
    for e in edges:
        if e.kind == "CONTAINS" and e.source == topic_qn and e.target.startswith(file_path + "::aula-"):
            for n in nodes:
                if n.kind == "Lesson" and f"{file_path}::aula-" in e.target:
                    lnum = e.target.split("::aula-")[1]
                    if n.line_start == e.line:
                        lesson_ranges.append((e.target, n.line_start, n.line_end, lnum))
                        break

    formula_counter_by_lesson: dict[str, int] = {}
    for m in RE_FORMULA.finditer(content):
        fline = content[:m.start()].count("\n") + 1
        latex = m.group(1).strip()

        owner_qn = None
        owner_num = None
        for lqn, lstart, lend, lnum in lesson_ranges:
            if lstart <= fline <= lend:
                owner_qn = lqn
                owner_num = lnum
                break

        if not owner_qn:
            continue

        formula_counter_by_lesson[owner_qn] = formula_counter_by_lesson.get(owner_qn, 0) + 1
        fc = formula_counter_by_lesson[owner_qn]
        fqn = f"{owner_qn}.formula.{fc}"
        nodes.append(NodeInfo(
            kind="Formula", name=f"Formula {fc}",
            file_path=file_path, line_start=fline, line_end=fline,
            parent_name=f"aula-{owner_num}",
            extra={"latex": latex[:200]},
        ))
        edges.append(EdgeInfo(
            kind="CONTAINS", source=owner_qn, target=fqn,
            file_path=file_path, line=fline,
        ))

    # ---- Links markdown (arestas REFERENCES) ----
    _extract_references(lines, file_path, topic_qn, nodes, edges, in_sumario_sections=True)

    return nodes, edges


def _detect_section_type(heading_text: str) -> str:
    """Detecta o tipo de seção pelo texto do heading."""
    lower = heading_text.lower()
    if any(w in lower for w in ["implementação", "código", "algoritmo"]):
        return "implementation"
    if any(w in lower for w in ["conceito", "definição", "introdução", "fundamento"]):
        return "theory"
    if any(w in lower for w in ["propriedade", "quando usar"]):
        return "analysis"
    if any(w in lower for w in ["comparação", "análise"]):
        return "comparison"
    if any(w in lower for w in ["integração", "conexão", "aplicação"]):
        return "integration"
    if any(w in lower for w in ["intuição", "dica"]):
        return "intuition"
    return "general"


def _extract_glossary_terms(
    lines: list[str], start: int, end: int, file_path: str,
    lesson_qn: str, lesson_num: str,
    nodes: list[NodeInfo], edges: list[EdgeInfo],
) -> None:
    """Extrai termos de glossário de uma seção ### 📖 Glossário."""
    term_count = 0
    for i in range(start + 1, end + 1):
        m = RE_GLOSSARY_TERM.match(lines[i].strip())
        if m:
            term_count += 1
            term_name = m.group(1).strip()
            definition = m.group(2).strip()
            slug = _slugify(term_name)
            gqn = f"{lesson_qn}.glossary.{slug}"
            nodes.append(NodeInfo(
                kind="GlossaryTerm", name=term_name, file_path=file_path,
                line_start=i + 1, line_end=i + 1,
                parent_name=f"aula-{lesson_num}",
                extra={"definition": definition},
            ))
            edges.append(EdgeInfo(
                kind="CONTAINS", source=lesson_qn, target=gqn,
                file_path=file_path, line=i + 1,
            ))


def _extract_exercises(
    lines: list[str], start: int, end: int, file_path: str,
    lesson_qn: str, lesson_num: str, counter_start: int,
    nodes: list[NodeInfo], edges: list[EdgeInfo],
    parent_qn: Optional[str] = None,
) -> None:
    """Extrai exercícios por marcadores 🟢🟡🔴."""
    counter = counter_start
    contain_source = parent_qn or lesson_qn
    difficulty_map = {"🟢": "green", "🟡": "yellow", "🔴": "red"}

    for i in range(start + 1, end + 1):
        m = RE_EXERCISE_MARKER.match(lines[i].strip())
        if m:
            counter += 1
            marker = m.group(1)
            label = m.group(2).strip().rstrip(":")
            eqn = f"{lesson_qn}.exercise.{counter}"
            nodes.append(NodeInfo(
                kind="Exercise", name=f"Exercício {counter}: {label}",
                file_path=file_path, line_start=i + 1, line_end=i + 1,
                parent_name=f"aula-{lesson_num}",
                extra={"difficulty_level": difficulty_map.get(marker, "unknown")},
            ))
            edges.append(EdgeInfo(
                kind="CONTAINS", source=contain_source, target=eqn,
                file_path=file_path, line=i + 1,
            ))

            # EVALUATES: Exercise → Concepts do mesmo scope
            # Associar aos Concepts do lesson pai
            for n in nodes:
                if (n.kind == "Concept" and n.file_path == file_path
                        and n.parent_name and f"aula-{lesson_num}" in (n.parent_name or "")):
                    edges.append(EdgeInfo(
                        kind="EVALUATES", source=eqn, target=_concept_qn(file_path, n),
                        file_path=file_path, line=i + 1,
                    ))


def _concept_qn(file_path: str, node: NodeInfo) -> str:
    """Reconstrói qualified_name de um Concept a partir de NodeInfo."""
    slug = _slugify(node.name)
    if node.parent_name:
        return f"{file_path}::{node.parent_name}.concept.{slug}"
    return f"{file_path}::concept.{slug}"


def _extract_references(
    lines: list[str], file_path: str, topic_qn: Optional[str],
    nodes: list[NodeInfo], edges: list[EdgeInfo],
    in_sumario_sections: bool = True,
) -> None:
    """Extrai links markdown como arestas REFERENCES."""
    in_sumario = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## Sumário") or stripped.startswith("## Referências"):
            in_sumario = True
            continue
        if stripped.startswith("## ") and in_sumario:
            in_sumario = False

        if in_sumario and in_sumario_sections:
            continue

        for m in RE_LINK.finditer(stripped):
            target = m.group(2).strip()
            # Ignorar links http externos e imagens
            if target.startswith("http") or target.startswith("#"):
                continue
            if target.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
                continue

            source_qn = topic_qn or file_path
            # Resolver target relativo
            if not target.startswith("conteudos/"):
                base_dir = str(Path(file_path).parent)
                resolved = str(Path(base_dir) / target)
            else:
                resolved = target

            edges.append(EdgeInfo(
                kind="REFERENCES", source=source_qn, target=resolved,
                file_path=file_path, line=i + 1,
            ))


# ---------------------------------------------------------------------------
# Index file parser
# ---------------------------------------------------------------------------

def parse_index_file(index_path: str, content: str) -> list[EdgeInfo]:
    """Extrai arestas do index.md: pré-requisitos inferidos e GENERATED_FROM."""
    lines = content.splitlines()
    edges: list[EdgeInfo] = []

    # Tabela "Estrutura de Tópicos"
    topics_ordered: list[str] = []
    in_topics_table = False

    # Tabela "Registro de Aulas"
    in_aulas_table = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if "Estrutura de Tópicos" in stripped:
            in_topics_table = True
            in_aulas_table = False
            continue

        if "Registro de Aulas" in stripped:
            in_topics_table = False
            in_aulas_table = True
            continue

        if stripped.startswith("## ") or stripped.startswith("---"):
            if in_topics_table and not stripped.startswith("---"):
                in_topics_table = False
            if in_aulas_table and not stripped.startswith("---"):
                in_aulas_table = False

        # Parse tabela de tópicos
        if in_topics_table and stripped.startswith("|") and not stripped.startswith("|-"):
            cols = [c.strip() for c in stripped.split("|")]
            cols = [c for c in cols if c]
            if len(cols) >= 3:
                # cols: [#, Tópico, Arquivo, Aulas Cobertas]
                try:
                    int(cols[0])  # Skip header
                except ValueError:
                    continue
                arquivo = cols[2].strip()
                if arquivo and arquivo != "—" and arquivo.endswith(".md"):
                    if not arquivo.startswith("conteudos/"):
                        arquivo = f"conteudos/{arquivo}"
                    topics_ordered.append(arquivo)

        # Parse tabela de registro de aulas
        if in_aulas_table and stripped.startswith("|") and not stripped.startswith("|-"):
            cols = [c.strip() for c in stripped.split("|")]
            cols = [c for c in cols if c]
            if len(cols) >= 3:
                try:
                    int(cols[0])  # Skip header
                except ValueError:
                    continue
                # Não há informação suficiente aqui para GENERATED_FROM sem o path da aula
                # GENERATED_FROM seria Lesson → aulas/aula-XX/ mas o index atual não tem esse path

    # Pré-requisitos inferidos: Tópico N depende de N-1
    for j in range(1, len(topics_ordered)):
        edges.append(EdgeInfo(
            kind="PREREQUISITE",
            source=topics_ordered[j],
            target=topics_ordered[j - 1],
            file_path=index_path,
            line=0,
            extra={"confidence": "inferred"},
        ))

    return edges


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_file(file_path: str, content: str) -> tuple[list[NodeInfo], list[EdgeInfo]]:
    """Parse um arquivo markdown. Detecta automaticamente se é index.md ou conteúdo."""
    fname = Path(file_path).name
    if fname == "index.md":
        index_edges = parse_index_file(file_path, content)
        return [], index_edges
    return parse_topic_file(file_path, content)
