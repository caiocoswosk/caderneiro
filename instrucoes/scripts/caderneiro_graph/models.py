"""Dataclasses para nós e arestas do grafo de conhecimento acadêmico."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NodeInfo:
    """Informação de um nó extraído do parser markdown."""

    kind: str  # Topic, Lesson, Concept, Section, Exercise, GlossaryTerm, Formula
    name: str
    file_path: str
    line_start: int
    line_end: int
    parent_name: Optional[str] = None
    difficulty: Optional[str] = None  # Basica, Intermediaria, Avancada
    extra: dict = field(default_factory=dict)


@dataclass
class EdgeInfo:
    """Informação de uma aresta extraída do parser markdown."""

    kind: str  # CONTAINS, PREREQUISITE, REFERENCES, EVALUATES, EXTENDS, GENERATED_FROM
    source: str  # qualified_name do nó de origem
    target: str  # qualified_name do nó de destino
    file_path: str
    line: int = 0
    extra: dict = field(default_factory=dict)
