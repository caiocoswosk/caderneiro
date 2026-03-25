#!/usr/bin/env python3
"""CLI do caderneiro_graph — grafo de conhecimento para cadernos acadêmicos.

Uso: python3 instrucoes/scripts/caderneiro_graph/cli.py <command> [args]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Permitir importação direta (sem PYTHONPATH)
_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _SCRIPT_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from caderneiro_graph.graph import GraphStore
from caderneiro_graph.incremental import (
    collect_content_files,
    full_build,
    get_db_path,
    incremental_update,
)
from caderneiro_graph.queries import (
    find_orphan_concepts,
    find_prerequisite_cycles,
    find_topic_for_content,
    get_coverage_report,
    get_learning_path,
    get_topic_dependencies,
)
from caderneiro_graph.visualization import generate_html

logger = logging.getLogger("caderneiro_graph")


def _ensure_store(caderno_root: Path, auto_build: bool = True) -> GraphStore:
    """Retorna GraphStore, executando auto-build se necessário."""
    db_path = get_db_path(caderno_root)
    store = GraphStore(db_path)

    if auto_build and store.get_metadata("last_updated") is None:
        # Auto-build: DB vazio e conteudos/ tem arquivos
        content_files = collect_content_files(caderno_root)
        if content_files:
            print("Auto-build: construindo grafo pela primeira vez...")
            result = full_build(caderno_root, store)
            print(f"  {result['files_parsed']} arquivos, "
                  f"{result['total_nodes']} nós, "
                  f"{result['total_edges']} arestas")

    return store


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_build(args: argparse.Namespace) -> None:
    caderno_root = Path(args.caderno).resolve()
    db_path = get_db_path(caderno_root)
    t0 = time.time()

    with GraphStore(db_path) as store:
        result = full_build(caderno_root, store)

    elapsed = time.time() - t0
    print(f"\nBuild completo em {elapsed:.1f}s")
    print(f"  Arquivos: {result['files_parsed']}")
    print(f"  Nós:      {result['total_nodes']}")
    print(f"  Arestas:  {result['total_edges']}")
    if result["errors"]:
        print(f"  Erros:    {len(result['errors'])}")
        for e in result["errors"]:
            print(f"    - {e['file']}: {e['error']}")


def cmd_update(args: argparse.Namespace) -> None:
    caderno_root = Path(args.caderno).resolve()

    with _ensure_store(caderno_root) as store:
        changed = args.files if args.files else None
        t0 = time.time()
        result = incremental_update(caderno_root, store, changed_files=changed)
        elapsed = time.time() - t0

    print(f"\nUpdate incremental em {elapsed:.1f}s")
    print(f"  Arquivos atualizados: {result['files_updated']}")
    print(f"  Nós:    {result['total_nodes']}")
    print(f"  Arestas: {result['total_edges']}")
    if result.get("deleted_files"):
        print(f"  Deletados: {result['deleted_files']}")
    if result.get("errors"):
        for e in result["errors"]:
            print(f"  Erro: {e['file']}: {e['error']}")


def cmd_status(args: argparse.Namespace) -> None:
    caderno_root = Path(args.caderno).resolve()

    with _ensure_store(caderno_root) as store:
        stats = store.get_stats()

    print(f"\nGrafo de Conhecimento — Status")
    print(f"  Total de nós:    {stats.total_nodes}")
    print(f"  Total de arestas: {stats.total_edges}")
    print(f"  Arquivos:        {stats.files_count}")
    print(f"  Última atualização: {stats.last_updated or 'nunca'}")

    if stats.nodes_by_kind:
        print(f"\n  Nós por tipo:")
        for kind, count in sorted(stats.nodes_by_kind.items()):
            print(f"    {kind:15s} {count}")

    if stats.edges_by_kind:
        print(f"\n  Arestas por tipo:")
        for kind, count in sorted(stats.edges_by_kind.items()):
            print(f"    {kind:15s} {count}")


def cmd_query(args: argparse.Namespace) -> None:
    caderno_root = Path(args.caderno).resolve()

    with _ensure_store(caderno_root) as store:
        query_type = args.query_type

        if query_type == "find_topic":
            if not args.keywords:
                print("Erro: --keywords é obrigatório para find_topic")
                sys.exit(1)
            results = find_topic_for_content(store, args.keywords)
            if args.json:
                print(json.dumps(results, ensure_ascii=False, indent=2))
            else:
                if not results:
                    print("Nenhum tópico encontrado.")
                else:
                    print(f"\nTópicos encontrados ({len(results)}):")
                    for r in results:
                        print(f"  [{r['match_count']} matches] {r['topic_name']} ({r['file_path']})")
                        for c in r["matched_concepts"][:5]:
                            print(f"    - {c}")

        elif query_type == "impact":
            if not args.files:
                print("Erro: --files é obrigatório para impact")
                sys.exit(1)
            result = store.get_impact_radius(args.files, max_depth=args.depth)
            if args.json:
                # Serializar nós e arestas
                output = {
                    "changed_nodes": [n.qualified_name for n in result["changed_nodes"]],
                    "impacted_files": result["impacted_files"],
                    "impacted_nodes": [n.qualified_name for n in result["impacted_nodes"]],
                    "truncated": result["truncated"],
                }
                print(json.dumps(output, ensure_ascii=False, indent=2))
            else:
                print(f"\nRaio de impacto (depth={args.depth}):")
                print(f"  Nós alterados: {len(result['changed_nodes'])}")
                print(f"  Nós impactados: {result['total_impacted']}")
                print(f"  Arquivos impactados:")
                for f in result["impacted_files"]:
                    print(f"    - {f}")

        elif query_type == "orphans":
            orphans = find_orphan_concepts(store)
            if args.json:
                print(json.dumps(orphans, ensure_ascii=False, indent=2))
            else:
                print(f"\nConceitos órfãos ({len(orphans)}):")
                for o in orphans:
                    print(f"  - {o['name']} ({o['file_path']})")

        elif query_type == "cycles":
            cycles = find_prerequisite_cycles(store)
            if args.json:
                print(json.dumps(cycles, ensure_ascii=False, indent=2))
            else:
                if not cycles:
                    print("Nenhum ciclo de pré-requisitos encontrado.")
                else:
                    print(f"\nCiclos de pré-requisitos ({len(cycles)}):")
                    for i, cycle in enumerate(cycles, 1):
                        print(f"  Ciclo {i}: {' → '.join(cycle)}")

        elif query_type == "coverage":
            report = get_coverage_report(store)
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print(f"\nRelatório de Cobertura:")
                summary = report["summary"]
                print(f"  Tópicos:    {summary['total_topics']}")
                print(f"  Conceitos:  {summary['total_concepts']}")
                print(f"  Exercícios: {summary['total_exercises']}")
                print(f"  Glossário:  {summary['total_glossary']}")
                dist = summary["exercise_distribution"]
                print(f"  Exercícios: 🟢{dist['green']} 🟡{dist['yellow']} 🔴{dist['red']}")
                print()
                for t in report["topics"]:
                    flags = f" ⚠️ {', '.join(t['flags'])}" if t["flags"] else ""
                    print(f"  {t['name']}: "
                          f"{t['lessons']}L {t['concepts']}C "
                          f"{t['exercises']}E {t['glossary_terms']}G{flags}")

        elif query_type == "learning_path":
            if not args.topic:
                print("Erro: --topic é obrigatório para learning_path")
                sys.exit(1)
            path = get_learning_path(store, args.topic)
            if args.json:
                print(json.dumps(path, ensure_ascii=False, indent=2))
            else:
                print(f"\nCaminho de aprendizado ({len(path)} tópicos):")
                for i, qn in enumerate(path, 1):
                    node = store.get_node(qn)
                    name = node.name if node else qn
                    marker = " ← atual" if qn == args.topic else ""
                    print(f"  {i}. {name}{marker}")

        elif query_type == "dependencies":
            deps = get_topic_dependencies(store)
            if args.json:
                print(json.dumps(deps, ensure_ascii=False, indent=2))
            else:
                print(f"\nDependências entre tópicos:")
                for t in deps["topics"]:
                    print(f"  - {t['name']} ({t['file_path']})")
                if deps["edges"]:
                    print(f"\n  Arestas ({len(deps['edges'])}):")
                    for e in deps["edges"]:
                        print(f"    {e['source']} →[{e['kind']}]→ {e['target']}")

        else:
            print(f"Query desconhecida: {query_type}")
            sys.exit(1)


def cmd_visualize(args: argparse.Namespace) -> None:
    caderno_root = Path(args.caderno).resolve()

    with _ensure_store(caderno_root) as store:
        output_dir = caderno_root / ".caderneiro-graph"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "graph.html"
        generate_html(store, output_path)

    print(f"Visualização gerada: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Grafo de conhecimento para cadernos acadêmicos",
        prog="caderneiro_graph",
    )
    parser.add_argument(
        "--caderno", default=".",
        help="Raiz do caderno (default: diretório atual)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Ativar logging detalhado",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # build
    subparsers.add_parser("build", help="Rebuild completo do grafo")

    # update
    p_update = subparsers.add_parser("update", help="Atualização incremental")
    p_update.add_argument("--files", nargs="+", help="Arquivos alterados (relativo ao caderno)")

    # status
    subparsers.add_parser("status", help="Mostrar estatísticas do grafo")

    # query
    p_query = subparsers.add_parser("query", help="Consultar o grafo")
    p_query.add_argument(
        "query_type",
        choices=["find_topic", "impact", "orphans", "cycles", "coverage", "learning_path", "dependencies"],
        help="Tipo de consulta",
    )
    p_query.add_argument("--keywords", help="Palavras-chave (para find_topic)")
    p_query.add_argument("--files", nargs="+", help="Arquivos (para impact)")
    p_query.add_argument("--topic", help="Qualified name do tópico (para learning_path)")
    p_query.add_argument("--depth", type=int, default=2, help="Profundidade do BFS (para impact)")
    p_query.add_argument("--json", action="store_true", help="Output em JSON")

    # visualize
    subparsers.add_parser("visualize", help="Gerar visualização HTML")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    commands = {
        "build": cmd_build,
        "update": cmd_update,
        "status": cmd_status,
        "query": cmd_query,
        "visualize": cmd_visualize,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
