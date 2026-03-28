#!/usr/bin/env python3
"""CLI do caderneiro_graph — meta-grafo estrutural do caderneiro.

Uso: python3 instrucoes/scripts/caderneiro_graph/cli.py <command> [args]
"""

from __future__ import annotations

import argparse
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
from caderneiro_graph.incremental import get_meta_db_path, meta_full_build, needs_meta_rebuild
from caderneiro_graph.meta_queries import (
    check_consistency,
    impact_analysis as meta_impact_analysis,
    meta_coverage_report,
)
from caderneiro_graph.visualization import META_GRAPH_CONFIG, generate_html

logger = logging.getLogger("caderneiro_graph")


def _validate_caderneiro_root(root: Path) -> None:
    """Verifica que root é de fato a raiz de um caderneiro."""
    marker = root / "instrucoes" / "geracao.md"
    if not marker.is_file():
        print(
            f"ERRO: {root} não é a raiz do caderneiro "
            f"(instrucoes/geracao.md não encontrado).",
            file=sys.stderr,
        )
        sys.exit(1)


def _ensure_meta_store(caderneiro_root: Path, *, force_rebuild: bool = False) -> GraphStore:
    """Retorna GraphStore para o meta-grafo.

    Reconstrói apenas se os arquivos-fonte foram modificados ou se
    force_rebuild=True. Use --force-rebuild no CLI para forçar rebuild explícito
    quando o banco estiver desatualizado por razões não detectadas pelo mtime.
    """
    db_path = get_meta_db_path(caderneiro_root)
    store = GraphStore(db_path)
    if force_rebuild or needs_meta_rebuild(caderneiro_root, db_path):
        meta_full_build(caderneiro_root, store)
    return store


def cmd_meta(args: argparse.Namespace) -> None:
    caderneiro_root = Path(args.caderno).resolve()
    _validate_caderneiro_root(caderneiro_root)
    meta_cmd = args.meta_command
    force_rebuild = getattr(args, "force_rebuild", False)

    if meta_cmd == "build":
        db_path = get_meta_db_path(caderneiro_root)
        t0 = time.time()
        with GraphStore(db_path) as store:
            result = meta_full_build(caderneiro_root, store)
        elapsed = time.time() - t0
        print(f"\nMeta-build completo em {elapsed:.1f}s")
        print(f"  Fontes:   {result['files_parsed']}")
        print(f"  Nós:      {result['total_nodes']}")
        print(f"  Arestas:  {result['total_edges']}")
        if result["errors"]:
            for e in result["errors"]:
                print(f"  Erro: {e['file']}: {e['error']}")

    elif meta_cmd == "check":
        with _ensure_meta_store(caderneiro_root, force_rebuild=force_rebuild) as store:
            result = check_consistency(store)

        gaps = result["summary"]["gaps"]
        if gaps == 0:
            print("\n✅ Meta-verificação: nenhum gap encontrado.")
            s = result["summary"]
            print(f"   {s['total_artifacts']} artefatos, "
                  f"{s['total_checks']} verificações, "
                  f"{s['total_scripts']} scripts, "
                  f"{s['total_operations']} operações")
        else:
            print(f"\n⚠️  Meta-verificação: {gaps} gap(s) encontrado(s):\n")

            if result["uncovered_artifacts"]:
                print("  Artefatos sem cobertura no Mapa de Referência:")
                for a in result["uncovered_artifacts"]:
                    print(f"    ❌ {a['path']} (condição: {a['condition']})")

            if result["uncovered_scripts"]:
                print("  Scripts no filesystem sem menção em geracao.md:")
                for s in result["uncovered_scripts"]:
                    print(f"    ❌ {s['path']} ({s['type']})")

            if result["stale_map_entries"]:
                print("  Entradas do Mapa sem artefato correspondente:")
                for m in result["stale_map_entries"]:
                    print(f"    ⚠️  #{m['number']} → {m['target']}")

            if result["missing_operations"]:
                print("\n  Operações em modelos.md sem instrução em geracao.md:")
                for o in result["missing_operations"]:
                    print(f"    ℹ️  {o['operation']} ({o['level']}) → esperado: {o['expected']}")

    elif meta_cmd == "impact":
        if not args.file:
            print("Erro: --file é obrigatório para impact")
            sys.exit(1)
        with _ensure_meta_store(caderneiro_root, force_rebuild=force_rebuild) as store:
            results = meta_impact_analysis(store, args.file)

        if not results:
            print(f"\nNenhum artefato afetado por: {args.file}")
        else:
            print(f"\nArtefatos afetados por {args.file}:")
            for r in results:
                print(f"  [{r['relation']}] {r['artifact']}")

    elif meta_cmd == "status":
        with _ensure_meta_store(caderneiro_root, force_rebuild=force_rebuild) as store:
            report = meta_coverage_report(store)

        print("\nMeta-grafo — Cobertura:")
        print(f"  Artefatos:    {report['artifacts']['covered_by_map']}/{report['artifacts']['total']} cobertos pelo Mapa")
        print(f"  Scripts:      {report['scripts']['covered_by_geracao']}/{report['scripts']['total']} cobertos por geracao.md")
        print(f"  Verificações: {report['checks']['valid']}/{report['checks']['total']} válidas")
        print(f"  Operações:    {report['operations']['with_instruction']}/{report['operations']['total']} com instrução")
        print(f"  Gaps total:   {report['overall_gaps']}")

    elif meta_cmd == "visualize":
        with _ensure_meta_store(caderneiro_root, force_rebuild=force_rebuild) as store:
            output_dir = caderneiro_root / ".caderneiro-graph"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / "meta.html"
            generate_html(store, output_path, graph_config=META_GRAPH_CONFIG)

        print(f"Visualização meta gerada: {output_path}")

    elif meta_cmd == "generate":
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "meta_generate",
            _SCRIPTS_DIR / "meta_generate.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        dry_run = getattr(args, "dry_run", False)
        sys.exit(mod.generate(caderneiro_root, dry_run=dry_run, verbose=args.verbose))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meta-grafo estrutural do caderneiro",
        prog="caderneiro_graph",
    )
    parser.add_argument(
        "--caderno", default=".",
        help="Raiz do caderneiro (default: diretório atual)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Ativar logging detalhado",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # meta
    p_meta = subparsers.add_parser("meta", help="Meta-grafo do caderneiro (consistência estrutural)")
    p_meta.add_argument(
        "meta_command",
        choices=["build", "check", "impact", "status", "visualize", "generate"],
        help="Subcomando meta",
    )
    p_meta.add_argument("--file", help="Arquivo para análise de impacto (meta impact)")
    p_meta.add_argument(
        "--force-rebuild", action="store_true", dest="force_rebuild",
        help="Forçar rebuild do meta-grafo mesmo se o cache estiver atualizado",
    )
    p_meta.add_argument(
        "--dry-run", action="store_true", dest="dry_run",
        help="Mostrar diff sem modificar arquivos (meta generate)",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    cmd_meta(args)


if __name__ == "__main__":
    main()
