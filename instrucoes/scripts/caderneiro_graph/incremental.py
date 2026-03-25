"""Motor incremental de build/update do grafo de conhecimento.

Baseado em hash SHA-256 (sem dependência de git). Detecta adições,
modificações e deleções via comparação disco vs DB.
"""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path

from .graph import GraphStore
from .parser import parse_file

logger = logging.getLogger(__name__)


def get_db_path(caderno_root: Path) -> Path:
    """Retorna caminho do banco de dados, criando diretório se necessário."""
    crg_dir = caderno_root / ".caderneiro-graph"
    db_path = crg_dir / "graph.db"

    crg_dir.mkdir(exist_ok=True)

    inner_gitignore = crg_dir / ".gitignore"
    if not inner_gitignore.exists():
        inner_gitignore.write_text("# Auto-generated — do not commit.\n*\n")

    return db_path


def collect_content_files(caderno_root: Path) -> list[str]:
    """Lista arquivos markdown em conteudos/ + index.md."""
    files: list[str] = []

    # index.md
    index = caderno_root / "index.md"
    if index.is_file():
        files.append("index.md")

    # conteudos/*.md
    conteudos_dir = caderno_root / "conteudos"
    if conteudos_dir.is_dir():
        for p in sorted(conteudos_dir.glob("*.md")):
            if p.is_file():
                files.append(str(p.relative_to(caderno_root)))

    return files


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_dependents(store: GraphStore, file_path: str) -> set[str]:
    """Encontra arquivos que dependem do arquivo alterado via arestas reversas."""
    dependents: set[str] = set()

    # Arestas cujo target começa com file_path
    for edge in store.get_edges_by_target_file(file_path):
        if edge.kind in ("REFERENCES", "PREREQUISITE"):
            dependents.add(edge.file_path)

    # Para cada nó do arquivo, buscar arestas que apontam para ele
    for node in store.get_nodes_by_file(file_path):
        for edge in store.get_edges_by_target(node.qualified_name):
            if edge.file_path != file_path:
                dependents.add(edge.file_path)

    dependents.discard(file_path)
    return dependents


def full_build(caderno_root: Path, store: GraphStore) -> dict:
    """Rebuild completo do grafo."""
    files = collect_content_files(caderno_root)

    # Remover dados de arquivos que não existem mais
    existing_in_db = set(store.get_all_file_paths())
    current_files = set(files)
    for stale in existing_in_db - current_files:
        store.remove_file_data(stale)

    total_nodes = 0
    total_edges = 0
    errors = []

    for rel_path in files:
        full_path = caderno_root / rel_path
        try:
            content = full_path.read_text(encoding="utf-8")
            fhash = hashlib.sha256(content.encode()).hexdigest()
            nodes, edges = parse_file(rel_path, content)
            store.store_file_nodes_edges(rel_path, nodes, edges, fhash)
            total_nodes += len(nodes)
            total_edges += len(edges)
        except Exception as e:
            logger.warning("Erro ao parsear %s: %s", rel_path, e)
            errors.append({"file": rel_path, "error": str(e)})

    store.set_metadata("last_updated", time.strftime("%Y-%m-%dT%H:%M:%S"))
    store.set_metadata("last_build_type", "full")
    store.commit()

    return {
        "files_parsed": len(files),
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "errors": errors,
    }


def incremental_update(
    caderno_root: Path,
    store: GraphStore,
    changed_files: list[str] | None = None,
) -> dict:
    """Atualização incremental: re-parseia apenas arquivos alterados + dependentes."""
    current_files = set(collect_content_files(caderno_root))

    # Detectar deleções
    existing_in_db = set(store.get_all_file_paths())
    deleted = existing_in_db - current_files
    for f in deleted:
        store.remove_file_data(f)

    # Detectar mudanças por hash
    if changed_files is None:
        changed_files = []
        for rel_path in current_files:
            full_path = caderno_root / rel_path
            if not full_path.is_file():
                continue
            fhash = hashlib.sha256(full_path.read_text(encoding="utf-8").encode()).hexdigest()
            existing_nodes = store.get_nodes_by_file(rel_path)
            if not existing_nodes or existing_nodes[0].file_hash != fhash:
                changed_files.append(rel_path)

    if not changed_files and not deleted:
        return {
            "files_updated": 0,
            "total_nodes": 0,
            "total_edges": 0,
            "changed_files": [],
            "dependent_files": [],
            "deleted_files": [],
        }

    # Encontrar dependentes
    dependent_files: set[str] = set()
    for rel_path in changed_files:
        deps = find_dependents(store, rel_path)
        dependent_files.update(deps)

    # Incluir index.md se não está na lista (arestas PREREQUISITE/GENERATED_FROM)
    if "index.md" not in set(changed_files) and "index.md" in current_files:
        dependent_files.add("index.md")

    # Combinar
    all_files = set(changed_files) | (dependent_files & current_files)

    total_nodes = 0
    total_edges = 0
    errors = []

    for rel_path in all_files:
        full_path = caderno_root / rel_path
        if not full_path.is_file():
            store.remove_file_data(rel_path)
            continue

        try:
            content = full_path.read_text(encoding="utf-8")
            fhash = hashlib.sha256(content.encode()).hexdigest()
            nodes, edges = parse_file(rel_path, content)
            store.store_file_nodes_edges(rel_path, nodes, edges, fhash)
            total_nodes += len(nodes)
            total_edges += len(edges)
        except Exception as e:
            logger.warning("Erro ao parsear %s: %s", rel_path, e)
            errors.append({"file": rel_path, "error": str(e)})

    store.set_metadata("last_updated", time.strftime("%Y-%m-%dT%H:%M:%S"))
    store.set_metadata("last_build_type", "incremental")
    store.commit()

    return {
        "files_updated": len(all_files),
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "changed_files": list(changed_files),
        "dependent_files": list(dependent_files),
        "deleted_files": list(deleted),
        "errors": errors,
    }
