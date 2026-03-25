"""Consultas semânticas sobre o grafo de conhecimento acadêmico.

Fornece APIs para: localização de tópicos, raio de impacto,
conceitos órfãos, ciclos, cobertura, caminho de aprendizado.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import networkx as nx

from .graph import GraphStore


def find_topic_for_content(store: GraphStore, keywords: str) -> list[dict]:
    """Busca keywords em Concepts e GlossaryTerms, agrupa por tópico (file_path)."""
    matched_nodes = store.search_nodes_extended(keywords, search_extra=True, limit=50)

    # Agrupar por file_path (tópico)
    by_file: dict[str, list] = defaultdict(list)
    for n in matched_nodes:
        if n.kind in ("Concept", "GlossaryTerm", "Section", "Exercise"):
            by_file[n.file_path].append(n)

    results = []
    for file_path, nodes in by_file.items():
        # Nome do tópico
        topic_nodes = store.get_nodes_by_file(file_path)
        topic_name = next((n.name for n in topic_nodes if n.kind == "Topic"), file_path)
        results.append({
            "file_path": file_path,
            "topic_name": topic_name,
            "match_count": len(nodes),
            "matched_concepts": [n.name for n in nodes],
        })

    results.sort(key=lambda x: x["match_count"], reverse=True)
    return results


def find_orphan_concepts(store: GraphStore) -> list[dict]:
    """Conceitos sem arestas REFERENCES/PREREQUISITE/EVALUATES de entrada."""
    concepts = store.get_nodes_by_kind("Concept")
    orphans = []

    for c in concepts:
        incoming = store.get_edges_by_target(c.qualified_name)
        has_semantic_incoming = any(
            e.kind in ("REFERENCES", "PREREQUISITE", "EVALUATES")
            for e in incoming
        )
        if not has_semantic_incoming:
            orphans.append({
                "qualified_name": c.qualified_name,
                "name": c.name,
                "file_path": c.file_path,
            })

    return orphans


def find_prerequisite_cycles(store: GraphStore) -> list[list[str]]:
    """Detecta ciclos no subgrafo de pré-requisitos explícitos."""
    g = nx.DiGraph()
    all_edges = store.get_all_edges()
    for e in all_edges:
        if e.kind == "PREREQUISITE":
            extra = e.extra or {}
            if extra.get("confidence") != "inferred":
                g.add_edge(e.source_qualified, e.target_qualified)

    cycles = list(nx.simple_cycles(g))
    return cycles


def get_coverage_report(store: GraphStore) -> dict[str, Any]:
    """Relatório de cobertura por tópico."""
    topics = store.get_nodes_by_kind("Topic")
    report: dict[str, Any] = {"topics": [], "summary": {}}

    total_concepts = 0
    total_exercises = 0
    total_glossary = 0
    exercise_distribution = {"green": 0, "yellow": 0, "red": 0}

    for topic in topics:
        file_nodes = store.get_nodes_by_file(topic.file_path)
        lessons = [n for n in file_nodes if n.kind == "Lesson"]
        concepts = [n for n in file_nodes if n.kind == "Concept"]
        exercises = [n for n in file_nodes if n.kind == "Exercise"]
        glossary_terms = [n for n in file_nodes if n.kind == "GlossaryTerm"]
        formulas = [n for n in file_nodes if n.kind == "Formula"]
        sections = [n for n in file_nodes if n.kind == "Section"]

        # Distribuição de exercícios
        dist = {"green": 0, "yellow": 0, "red": 0}
        for ex in exercises:
            level = (ex.extra or {}).get("difficulty_level", "unknown")
            if level in dist:
                dist[level] += 1

        # Flags
        flags = []
        if not exercises:
            flags.append("sem_exercicios")
        if not glossary_terms:
            flags.append("sem_glossario")
        if concepts and exercises:
            ratio = len(exercises) / len(concepts)
            if ratio < 0.5:
                flags.append("baixa_cobertura_exercicios")

        topic_data = {
            "file_path": topic.file_path,
            "name": topic.name,
            "lessons": len(lessons),
            "concepts": len(concepts),
            "exercises": len(exercises),
            "glossary_terms": len(glossary_terms),
            "formulas": len(formulas),
            "sections": len(sections),
            "exercise_distribution": dist,
            "flags": flags,
        }
        report["topics"].append(topic_data)

        total_concepts += len(concepts)
        total_exercises += len(exercises)
        total_glossary += len(glossary_terms)
        for k in dist:
            exercise_distribution[k] += dist[k]

    report["summary"] = {
        "total_topics": len(topics),
        "total_concepts": total_concepts,
        "total_exercises": total_exercises,
        "total_glossary": total_glossary,
        "exercise_distribution": exercise_distribution,
    }

    return report


def get_learning_path(store: GraphStore, topic_qn: str) -> list[str]:
    """Caminho de aprendizado: ancestrais via PREREQUISITE + topological sort."""
    g = nx.DiGraph()
    all_edges = store.get_all_edges()
    for e in all_edges:
        if e.kind == "PREREQUISITE":
            g.add_edge(e.source_qualified, e.target_qualified)

    if topic_qn not in g:
        return [topic_qn]

    # Ancestrais (pré-requisitos transitivos)
    ancestors = nx.ancestors(g, topic_qn)
    subgraph_nodes = ancestors | {topic_qn}
    subgraph = g.subgraph(subgraph_nodes)

    try:
        path = list(nx.topological_sort(subgraph))
        # Inverter: do mais básico ao mais avançado
        path.reverse()
        return path
    except nx.NetworkXUnfeasible:
        return list(subgraph_nodes)


def get_topic_dependencies(store: GraphStore) -> dict[str, Any]:
    """Todos os tópicos + arestas PREREQUISITE/REFERENCES entre eles."""
    topics = store.get_nodes_by_kind("Topic")
    topic_qns = {t.qualified_name for t in topics}

    topic_edges = []
    all_edges = store.get_all_edges()
    for e in all_edges:
        if e.kind in ("PREREQUISITE", "REFERENCES"):
            if e.source_qualified in topic_qns or e.target_qualified in topic_qns:
                topic_edges.append({
                    "kind": e.kind,
                    "source": e.source_qualified,
                    "target": e.target_qualified,
                    "extra": e.extra,
                })

    return {
        "topics": [
            {"qualified_name": t.qualified_name, "name": t.name, "file_path": t.file_path}
            for t in topics
        ],
        "edges": topic_edges,
    }
