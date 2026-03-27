"""Consultas semânticas sobre o meta-grafo do caderneiro.

Detecta inconsistências entre geracao.md, atualizar-caderno.md,
modelos.md e o filesystem de instrucoes/scripts/.
"""

from __future__ import annotations

from .graph import GraphStore


def check_consistency(store: GraphStore) -> dict:
    """Verifica consistência do meta-grafo.

    Retorna dict com listas de gaps:
    - uncovered_artifacts: artefatos em geracao.md sem cobertura no Mapa
    - uncovered_scripts: scripts no filesystem sem menção em geracao.md
    - stale_map_entries: entradas CHECKS que apontam para artefatos inexistentes
    - missing_operations: arestas DEFINES_LEVEL que apontam para artefatos inexistentes
    """
    # Coletar nós por tipo
    artifacts = {n.name: n for n in store.get_nodes_by_kind("GeneratedArtifact")}
    scripts = store.get_nodes_by_kind("Script")

    generated_paths: set[str] = set(artifacts.keys())

    # Coletar artefatos cobertos por CHECKS (arestas diretas de atualizar-caderno.md)
    checked_artifacts: set[str] = set()
    checks_edges = []
    for edge in store.get_all_edges():
        if edge.kind == "CHECKS":
            target = edge.target_qualified
            if "::" in target:
                artifact_name = target.split("::", 1)[1]
                checked_artifacts.add(artifact_name)
            checks_edges.append(edge)

    # Coletar operações (arestas DEFINES_LEVEL de modelos.md)
    defines_level_edges = []
    operations_count = 0
    for edge in store.get_all_edges():
        if edge.kind == "DEFINES_LEVEL":
            operations_count += 1
            defines_level_edges.append(edge)

    # 1. Artefatos gerados mas não verificados pelo Mapa
    uncovered_artifacts = []
    for name, node in artifacts.items():
        if name not in checked_artifacts:
            # Verificar se está coberto indiretamente
            covered = False
            for checked in checked_artifacts:
                # Diretório genérico cobre subpaths
                if checked.endswith("/") and name.startswith(checked):
                    covered = True
                    break
                # Reverso: artefato é diretório que cobre o checked
                if name.endswith("/") and checked.startswith(name):
                    covered = True
                    break
            if not covered:
                uncovered_artifacts.append({
                    "path": name,
                    "condition": node.extra.get("condition", "?"),
                    "source": node.extra.get("source_section", "?"),
                })

    # 2. Scripts no filesystem sem menção em geracao.md
    uncovered_scripts = []
    for script in scripts:
        script_name = script.name
        covered = False
        for gen_path in generated_paths:
            if gen_path.endswith("/"):
                if script.file_path.startswith(gen_path.rstrip("/")):
                    covered = True
                    break
                if script_name.rstrip("/") in gen_path:
                    covered = True
                    break
            if script_name == gen_path or script.file_path == gen_path:
                covered = True
                break
            if gen_path.endswith(script_name) or gen_path.endswith(script_name.rstrip("/")):
                covered = True
                break
        if not covered:
            uncovered_scripts.append({
                "path": script.file_path,
                "name": script_name,
                "type": script.extra.get("type", "?"),
            })

    # 3. Arestas CHECKS que apontam para artefatos inexistentes
    artifact_qns = {n.qualified_name for n in artifacts.values()}
    stale_map_entries = []
    for edge in checks_edges:
        target_qn = edge.target_qualified
        if target_qn not in artifact_qns:
            # Verificar cobertura por prefixo (ex: scripts/ cobre scripts/*.py)
            found = False
            for aqn in artifact_qns:
                art_name = aqn.split("::", 1)[1] if "::" in aqn else aqn
                tgt_name = target_qn.split("::", 1)[1] if "::" in target_qn else target_qn
                if art_name.endswith("/") and tgt_name.startswith(art_name):
                    found = True
                    break
                if tgt_name.endswith("/") and art_name.startswith(tgt_name):
                    found = True
                    break
            if not found:
                extra = edge.extra or {}
                stale_map_entries.append({
                    "number": extra.get("map_number", "?"),
                    "target": extra.get("map_target", "?"),
                    "condition": extra.get("condition", "?"),
                })

    # 4. Arestas DEFINES_LEVEL que apontam para artefatos inexistentes
    missing_operations = []
    operations_with_instruction = 0
    for edge in defines_level_edges:
        target_qn = edge.target_qualified
        if target_qn in artifact_qns:
            operations_with_instruction += 1
        else:
            extra = edge.extra or {}
            missing_operations.append({
                "operation": extra.get("operation", "?"),
                "level": extra.get("level", "?"),
                "expected": f"instrucoes/{extra.get('operation', '?')}.md",
            })

    return {
        "uncovered_artifacts": uncovered_artifacts,
        "uncovered_scripts": uncovered_scripts,
        "stale_map_entries": stale_map_entries,
        "missing_operations": missing_operations,
        "summary": {
            "total_artifacts": len(artifacts),
            "total_checks": len(checks_edges),
            "total_scripts": len(scripts),
            "total_operations": operations_count,
            "gaps": (
                len(uncovered_artifacts)
                + len(uncovered_scripts)
                + len(stale_map_entries)
            ),
        },
    }


def impact_analysis(store: GraphStore, file_path: str) -> list[dict]:
    """Dado um arquivo do caderneiro, retorna artefatos de caderno afetados.

    Percorre arestas GENERATES e DERIVES_FROM para encontrar
    quais artefatos dependem do arquivo alterado.
    """
    affected: list[dict] = []

    # Nós neste arquivo
    file_nodes = store.get_nodes_by_file(file_path)
    if not file_nodes:
        return []

    for node in file_nodes:
        # Arestas de saída deste nó
        for edge in store.get_edges_by_source(node.qualified_name):
            target_node = store.get_node(edge.target_qualified)
            if target_node:
                affected.append({
                    "artifact": target_node.name,
                    "relation": edge.kind,
                    "source_node": node.name,
                })

    return affected


def meta_coverage_report(store: GraphStore) -> dict:
    """Relatório resumido de cobertura do meta-grafo."""
    scripts = store.get_nodes_by_kind("Script")
    consistency = check_consistency(store)
    s = consistency["summary"]

    return {
        "artifacts": {
            "total": s["total_artifacts"],
            "covered_by_map": s["total_artifacts"] - len(consistency["uncovered_artifacts"]),
            "uncovered": len(consistency["uncovered_artifacts"]),
        },
        "scripts": {
            "total": len(scripts),
            "covered_by_geracao": len(scripts) - len(consistency["uncovered_scripts"]),
            "uncovered": len(consistency["uncovered_scripts"]),
        },
        "checks": {
            "total": s["total_checks"],
            "valid": s["total_checks"] - len(consistency["stale_map_entries"]),
            "stale": len(consistency["stale_map_entries"]),
        },
        "operations": {
            "total": s["total_operations"],
            "with_instruction": s["total_operations"] - len(consistency["missing_operations"]),
            "missing": len(consistency["missing_operations"]),
        },
        "overall_gaps": s["gaps"],
    }
