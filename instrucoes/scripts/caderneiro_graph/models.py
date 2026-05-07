"""Dataclasses para nós e arestas do meta-grafo do caderneiro."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NodeInfo:
    """Informação de um nó do grafo."""

    kind: str  # SourceFile, GeneratedArtifact, Script
    name: str
    file_path: str
    line_start: int
    line_end: int
    parent_name: Optional[str] = None
    difficulty: Optional[str] = None
    extra: dict = field(default_factory=dict)


@dataclass
class EdgeInfo:
    """Informação de uma aresta do grafo."""

    kind: str  # GENERATES, CHECKS, COPIES, DEFINES_LEVEL
    source: str  # qualified_name do nó de origem
    target: str  # qualified_name do nó de destino
    file_path: str
    line: int = 0
    extra: dict = field(default_factory=dict)
