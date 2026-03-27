"""Motor de build do meta-grafo do caderneiro."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from .graph import GraphStore
from .meta_parser import parse_meta

logger = logging.getLogger(__name__)

# Arquivos-fonte do meta-grafo cujo mtime é verificado para rebuild condicional.
_META_SOURCE_FILES = [
    "instrucoes/geracao.md",
    "instrucoes/atualizar-caderno.md",
    "instrucoes/modelos.md",
]


def needs_meta_rebuild(caderneiro_root: Path, db_path: Path) -> bool:
    """Retorna True se o meta-grafo precisar de rebuild.

    Compara mtime do banco com mtime dos arquivos-fonte e do diretório scripts/.
    Um rebuild é necessário quando:
    - O banco não existe (primeira execução)
    - Qualquer arquivo-fonte é mais recente que o banco
    - O diretório instrucoes/scripts/ é mais recente (cobre adição/remoção de scripts)
    """
    if not db_path.exists():
        return True

    db_mtime = db_path.stat().st_mtime

    for rel in _META_SOURCE_FILES:
        source = caderneiro_root / rel
        if source.exists() and source.stat().st_mtime > db_mtime:
            return True

    scripts_dir = caderneiro_root / "instrucoes" / "scripts"
    if scripts_dir.exists() and scripts_dir.stat().st_mtime > db_mtime:
        return True

    return False


def get_meta_db_path(caderneiro_root: Path) -> Path:
    """Retorna caminho do banco de dados meta, criando diretório se necessário."""
    crg_dir = caderneiro_root / ".caderneiro-graph"
    crg_dir.mkdir(exist_ok=True)

    inner_gitignore = crg_dir / ".gitignore"
    if not inner_gitignore.exists():
        inner_gitignore.write_text("# Auto-generated — do not commit.\n*\n")

    return crg_dir / "meta.db"


def meta_full_build(caderneiro_root: Path, store: GraphStore) -> dict:
    """Rebuild completo do meta-grafo."""
    # Limpar dados antigos
    existing = store.get_all_file_paths()
    for fp in existing:
        store.remove_file_data(fp)

    nodes, edges = parse_meta(caderneiro_root)

    total_nodes = 0
    total_edges = 0
    errors = []

    # Agrupar nós por file_path para usar store_file_nodes_edges
    by_file: dict[str, tuple[list, list]] = {}
    for node in nodes:
        fp = node.file_path
        if fp not in by_file:
            by_file[fp] = ([], [])
        by_file[fp][0].append(node)

    for edge in edges:
        fp = edge.file_path
        if fp not in by_file:
            by_file[fp] = ([], [])
        by_file[fp][1].append(edge)

    for fp, (file_nodes, file_edges) in by_file.items():
        try:
            store.store_file_nodes_edges(fp, file_nodes, file_edges, fhash="meta")
            total_nodes += len(file_nodes)
            total_edges += len(file_edges)
        except Exception as e:
            logger.warning("Erro no meta-build para %s: %s", fp, e)
            errors.append({"file": fp, "error": str(e)})

    store.set_metadata("last_updated", time.strftime("%Y-%m-%dT%H:%M:%S"))
    store.set_metadata("last_build_type", "meta_full")
    store.commit()

    return {
        "files_parsed": len(by_file),
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "errors": errors,
    }
