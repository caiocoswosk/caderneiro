"""Visualização D3.js interativa para o meta-grafo do caderneiro.

Gera HTML self-contained com force-directed layout, dark theme,
zoom, drag, collapse, busca e legenda interativa.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .graph import GraphStore, edge_to_dict, node_to_dict

# ---------------------------------------------------------------------------
# Configurações visuais por tipo de grafo
# ---------------------------------------------------------------------------

META_GRAPH_CONFIG: dict = {
    "title": "Meta-Grafo \u2014 Caderneiro",
    "aria_label": "Meta-grafo estrutural do caderneiro",
    "kind_color": {
        "SourceFile": "#58a6ff", "GeneratedArtifact": "#3fb950",
        "Script": "#d2a8ff",
    },
    "kind_radius": {
        "SourceFile": 16, "GeneratedArtifact": 8, "Script": 7,
    },
    "kind_shape": {
        "Script": "diamond",
    },
    "kind_labels": {
        "SourceFile": "Arquivo Fonte", "GeneratedArtifact": "Artefato Gerado",
        "Script": "Script",
    },
    "edge_color": {
        "GENERATES": "#3fb950", "CHECKS": "#f0883e", "COPIES": "#d2a8ff",
        "DEFINES_LEVEL": "#f778ba",
    },
    "edge_cfg": {
        "GENERATES":     {"dash": None,  "width": 2,   "opacity": 0.7, "marker": "arrow-generates"},
        "CHECKS":        {"dash": "6,3", "width": 1.5, "opacity": 0.6, "marker": "arrow-checks"},
        "COPIES":        {"dash": "3,4", "width": 1.5, "opacity": 0.6, "marker": "arrow-copies"},
        "DEFINES_LEVEL": {"dash": None,  "width": 1.5, "opacity": 0.6, "marker": "arrow-deflvl"},
    },
    "edge_labels": {
        "GENERATES": "Gera", "CHECKS": "Verifica", "COPIES": "Copia",
        "DEFINES_LEVEL": "Define N\u00edvel",
    },
    "collapse_kind": "SourceFile",
    "hierarchy_edge": "GENERATES",
    "label_visibility": {
        "SourceFile": 0, "_default": 0.4,
    },
    "label_styles": {
        "SourceFile": {"color": "#e6edf3", "size": "13px", "weight": 700},
        "_default":   {"color": "#8b949e", "size": "10px", "weight": 400},
    },
}


def export_graph_data(store: GraphStore) -> dict:
    """Exporta todos os nós e arestas como dict JSON-serializável."""
    nodes = []
    seen_qn: set[str] = set()

    for file_path in store.get_all_file_paths():
        for gnode in store.get_nodes_by_file(file_path):
            if gnode.qualified_name in seen_qn:
                continue
            seen_qn.add(gnode.qualified_name)
            nodes.append(node_to_dict(gnode))

    all_edges = [edge_to_dict(e) for e in store.get_all_edges()]

    # Filtrar arestas cujos source/target existem no grafo
    edges = []
    for e in all_edges:
        if e["source"] in seen_qn and e["target"] in seen_qn:
            edges.append(e)

    stats = store.get_stats()

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": asdict(stats),
    }


def generate_html(
    store: GraphStore,
    output_path: str | Path,
    *,
    graph_config: dict | None = None,
) -> Path:
    """Gera HTML interativo self-contained."""
    output_path = Path(output_path)
    if graph_config is None:
        graph_config = META_GRAPH_CONFIG

    data = export_graph_data(store)
    data_json = json.dumps(data, default=str, ensure_ascii=False).replace("</", "<\\/")
    config_json = json.dumps(graph_config, default=str, ensure_ascii=False).replace("</", "<\\/")

    html = _HTML_TEMPLATE
    html = html.replace("__GRAPH_DATA__", data_json)
    html = html.replace("__GRAPH_CONFIG__", config_json)
    html = html.replace("__PAGE_TITLE__", graph_config.get("title", "Grafo"))
    html = html.replace("__ARIA_LABEL__", graph_config.get("aria_label", "Grafo interativo"))

    output_path.write_text(html, encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# Template HTML D3.js
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PAGE_TITLE__</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: 100%; height: 100%; overflow: hidden; }
  body {
    background: #0d1117; color: #c9d1d9;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    font-size: 13px;
  }
  svg { display: block; width: 100%; height: 100%; }

  #legend {
    position: absolute; top: 16px; left: 16px;
    background: rgba(22,27,34,0.95); border: 1px solid #30363d;
    border-radius: 10px; padding: 16px 20px;
    font-size: 12px; line-height: 1.8;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    backdrop-filter: blur(12px); z-index: 10;
  }
  #legend h3 {
    font-size: 11px; font-weight: 700; margin-bottom: 6px;
    color: #8b949e; text-transform: uppercase; letter-spacing: 1px;
  }
  .legend-section { margin-bottom: 10px; }
  .legend-section:last-child { margin-bottom: 0; }
  .legend-item { display: flex; align-items: center; gap: 10px; padding: 2px 0; cursor: default; }
  .legend-item[data-edge-kind] { cursor: pointer; user-select: none; }
  .legend-item[data-edge-kind].dimmed { opacity: 0.3; }
  .legend-circle { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .legend-shape { width: 10px; height: 10px; flex-shrink: 0; }
  .legend-line { width: 24px; height: 0; flex-shrink: 0; }

  #stats-bar {
    position: absolute; bottom: 0; left: 0; right: 0;
    background: rgba(13,17,23,0.95); border-top: 1px solid #21262d;
    padding: 8px 24px; display: flex; gap: 32px; justify-content: center;
    font-size: 12px; color: #8b949e; backdrop-filter: blur(12px);
  }
  .stat-item { display: flex; gap: 6px; align-items: center; }
  .stat-value { color: #e6edf3; font-weight: 600; }

  #tooltip {
    position: absolute; pointer-events: none;
    background: rgba(22,27,34,0.97); color: #c9d1d9;
    border: 1px solid #30363d; border-radius: 8px;
    padding: 12px 16px; font-size: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
    max-width: 360px; line-height: 1.7;
    opacity: 0; transition: opacity 0.15s ease;
    z-index: 1000; backdrop-filter: blur(12px);
  }
  #tooltip.visible { opacity: 1; }
  .tt-name { font-weight: 700; font-size: 14px; color: #e6edf3; }
  .tt-kind {
    display: inline-block; font-size: 9px; font-weight: 700;
    padding: 2px 8px; border-radius: 10px; margin-left: 8px;
    text-transform: uppercase; letter-spacing: 0.5px;
  }
  .tt-row { margin-top: 4px; }
  .tt-label { color: #8b949e; }
  .tt-file { color: #58a6ff; font-size: 11px; }

  #controls {
    position: absolute; top: 16px; right: 16px;
    display: flex; gap: 8px; z-index: 10;
  }
  #controls button {
    background: rgba(22,27,34,0.95); color: #c9d1d9;
    border: 1px solid #30363d; border-radius: 8px;
    padding: 8px 14px; font-size: 12px; cursor: pointer;
    backdrop-filter: blur(12px); transition: all 0.15s;
  }
  #controls button:hover { background: #30363d; border-color: #8b949e; }
  #controls button.active { background: #1f6feb; border-color: #58a6ff; color: #fff; }
  #search {
    background: rgba(22,27,34,0.95); color: #c9d1d9;
    border: 1px solid #30363d; border-radius: 8px;
    padding: 8px 14px; font-size: 12px; width: 220px;
    outline: none; backdrop-filter: blur(12px);
  }
  #search:focus { border-color: #58a6ff; }
  #search::placeholder { color: #484f58; }
  marker { overflow: visible; }
</style>
</head>
<body>

<div id="legend" role="complementary" aria-label="Legenda do grafo"></div>

<div id="controls">
  <input id="search" type="text" placeholder="Buscar n&#243;s&#8230;" autocomplete="off" spellcheck="false">
  <button id="btn-fit" title="Ajustar &#224; tela">Ajustar</button>
  <button id="btn-labels" title="Alternar labels" class="active">Labels</button>
</div>

<div id="stats-bar" role="status"></div>
<div id="tooltip"></div>
<svg role="img" aria-label="__ARIA_LABEL__"></svg>

<script>
const graphData = __GRAPH_DATA__;
const CFG = __GRAPH_CONFIG__;

// -- Config from CFG --
const KIND_COLOR  = CFG.kind_color;
const KIND_RADIUS = CFG.kind_radius;
const KIND_SHAPE  = CFG.kind_shape || {};
const EDGE_COLOR  = CFG.edge_color;

// Reconstruct EDGE_CFG — marker field stores the ID string; we build url() at render time
const EDGE_CFG = {};
Object.entries(CFG.edge_cfg).forEach(([k, v]) => {
  EDGE_CFG[k] = {dash: v.dash, width: v.width, opacity: v.opacity, marker: v.marker || ""};
});

// -- Build legend dynamically --
(function buildLegend() {
  const legend = document.getElementById("legend");
  let html = '<h3>Tipos de N\u00f3</h3><div class="legend-section">';
  Object.entries(CFG.kind_labels).forEach(([kind, label]) => {
    const color = KIND_COLOR[kind] || "#8b949e";
    const shape = KIND_SHAPE[kind];
    if (shape === "diamond") {
      html += '<div class="legend-item"><span class="legend-shape" style="background:' + color + ';transform:rotate(45deg)"></span> ' + label + '</div>';
    } else if (shape === "square") {
      html += '<div class="legend-item"><span class="legend-shape" style="background:' + color + '"></span> ' + label + '</div>';
    } else {
      html += '<div class="legend-item"><span class="legend-circle" style="background:' + color + '"></span> ' + label + '</div>';
    }
  });
  html += '</div><h3>Arestas</h3><div class="legend-section">';
  Object.entries(CFG.edge_labels).forEach(([kind, label]) => {
    const color = EDGE_COLOR[kind] || "#484f58";
    const cfg = EDGE_CFG[kind] || {};
    let style = "border-top:" + (cfg.width || 1.5) + "px ";
    if (cfg.dash) style += "dashed "; else style += "solid ";
    style += color;
    html += '<div class="legend-item" data-edge-kind="' + kind + '"><span class="legend-line" style="' + style + '"></span> ' + label + '</div>';
  });
  html += '</div>';
  legend.innerHTML = html;
})();

function displayName(d) {
  return d.name;
}

// -- Prepare data --
const nodes = graphData.nodes.map(d => ({...d, _id: d.qualified_name, label: displayName(d)}));
const edges = graphData.edges.map(d => ({...d, _source: d.source, _target: d.target}));
const stats = graphData.stats;
const nodeById = new Map(nodes.map(n => [n.qualified_name, n]));

const hiddenEdgeKinds = new Set();
const collapsedTopics = new Set();
const containsChildren = new Map();
const HIERARCHY_EDGE = CFG.hierarchy_edge || "CONTAINS";
const COLLAPSE_KIND = CFG.collapse_kind || "Topic";

edges.forEach(e => {
  if (e.kind === HIERARCHY_EDGE) {
    if (!containsChildren.has(e._source)) containsChildren.set(e._source, new Set());
    containsChildren.get(e._source).add(e._target);
  }
});

function allDescendants(qn) {
  const result = new Set();
  const stack = [qn];
  while (stack.length) {
    const cur = stack.pop();
    const children = containsChildren.get(cur);
    if (!children) continue;
    for (const c of children) {
      if (!result.has(c)) { result.add(c); stack.push(c); }
    }
  }
  return result;
}

// -- Stats bar --
const statsBar = document.getElementById("stats-bar");
const si = (l,v) => '<div class="stat-item"><span class="tt-label">' + l + '</span> <span class="stat-value">' + v + '</span></div>';
statsBar.innerHTML = si("N\u00f3s", stats.total_nodes) + si("Arestas", stats.total_edges) + si("Arquivos", stats.files_count);

// -- Tooltip --
const tooltip = document.getElementById("tooltip");
function escH(s) { return !s ? "" : String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

function showTooltip(ev, d) {
  const bg = KIND_COLOR[d.kind] || "#555";
  let h = '<span class="tt-name">' + escH(d.label) + '</span>';
  h += '<span class="tt-kind" style="background:' + bg + ';color:#0d1117">' + d.kind + '</span>';
  if (d.file_path) h += '<div class="tt-row tt-file">' + escH(d.file_path) + '</div>';
  if (d.line_start != null) h += '<div class="tt-row"><span class="tt-label">Linhas: </span>' + d.line_start + ' \u2013 ' + (d.line_end || d.line_start) + '</div>';
  if (d.extra) {
    if (d.extra.condition) h += '<div class="tt-row"><span class="tt-label">Condi\u00e7\u00e3o: </span>' + escH(d.extra.condition) + '</div>';
    if (d.extra.operation) h += '<div class="tt-row"><span class="tt-label">Opera\u00e7\u00e3o: </span>' + escH(d.extra.operation) + ' (' + escH(d.extra.level) + ')</div>';
    if (d.extra.role) h += '<div class="tt-row"><span class="tt-label">Papel: </span>' + escH(d.extra.role) + '</div>';
    if (d.extra.type) h += '<div class="tt-row"><span class="tt-label">Tipo: </span>' + escH(d.extra.type) + '</div>';
  }
  tooltip.innerHTML = h;
  tooltip.classList.add("visible");
  moveTooltip(ev);
}
function moveTooltip(ev) {
  const p = 14;
  let x = ev.pageX + p, y = ev.pageY + p;
  const r = tooltip.getBoundingClientRect();
  if (x + r.width > innerWidth - p) x = ev.pageX - r.width - p;
  if (y + r.height > innerHeight - p) y = ev.pageY - r.height - p;
  tooltip.style.left = x + "px"; tooltip.style.top = y + "px";
}
function hideTooltip() { tooltip.classList.remove("visible"); }

// -- SVG setup --
const W = innerWidth, H = innerHeight;
const svg = d3.select("svg").attr("viewBox", [0, 0, W, H]);
const g = svg.append("g");
let currentTransform = d3.zoomIdentity;

const zoomBehavior = d3.zoom()
  .scaleExtent([0.05, 8])
  .on("zoom", ev => { currentTransform = ev.transform; g.attr("transform", ev.transform); updateLabelVisibility(); });
svg.call(zoomBehavior);

// Arrow markers — generated dynamically from config
const defs = svg.append("defs");
const glow = defs.append("filter").attr("id","glow").attr("x","-50%").attr("y","-50%").attr("width","200%").attr("height","200%");
glow.append("feGaussianBlur").attr("stdDeviation","3").attr("result","blur");
glow.append("feComposite").attr("in","SourceGraphic").attr("in2","blur").attr("operator","over");

Object.entries(EDGE_CFG).forEach(([kind, cfg]) => {
  if (cfg.marker) {
    const color = EDGE_COLOR[kind] || "#484f58";
    defs.append("marker").attr("id", cfg.marker)
      .attr("viewBox","0 -5 10 10").attr("refX",28).attr("refY",0)
      .attr("markerWidth",8).attr("markerHeight",8).attr("orient","auto")
      .append("path").attr("d","M0,-4L10,0L0,4Z").attr("fill", color);
  }
});

// -- Simulation --
const N = nodes.length;
const isLarge = N > 200;
const chargeCollapse = isLarge ? -300 : -500;
const chargeOther = isLarge ? -50 : -100;
const linkDist = isLarge ? 60 : 100;

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(edges).id(d => d.qualified_name)
    .distance(d => d.kind === HIERARCHY_EDGE ? 30 : linkDist)
    .strength(d => d.kind === HIERARCHY_EDGE ? 1.5 : 0.15))
  .force("charge", d3.forceManyBody().strength(d => d.kind === COLLAPSE_KIND ? chargeCollapse : chargeOther).theta(0.85).distanceMax(500))
  .force("collide", d3.forceCollide().radius(d => (KIND_RADIUS[d.kind] || 6) + 3))
  .force("center", d3.forceCenter(W/2, H/2))
  .force("x", d3.forceX(W/2).strength(0.03))
  .force("y", d3.forceY(H/2).strength(0.03))
  .alphaDecay(isLarge ? 0.04 : 0.025)
  .velocityDecay(0.4);

// -- Edge styles --
function eStyle(d) {
  const cfg = EDGE_CFG[d.kind] || {dash:null,width:1,opacity:0.3,marker:""};
  return {...cfg, markerUrl: cfg.marker ? "url(#" + cfg.marker + ")" : ""};
}
function eColor(d) { return EDGE_COLOR[d.kind] || "#484f58"; }

// -- Draw layers --
const linkGroup  = g.append("g").attr("class","links");
const nodeGroup  = g.append("g").attr("class","nodes");
const labelGroup = g.append("g").attr("class","labels");

let linkSel, labelSel;
let showLabels = true;

function updateLinks() {
  const vis = new Set(nodes.filter(n => !n._hidden).map(n => n.qualified_name));
  const visEdges = edges.filter(e => {
    if (hiddenEdgeKinds.has(e.kind)) return false;
    const s = typeof e.source === "object" ? e.source.qualified_name : e._source;
    const t = typeof e.target === "object" ? e.target.qualified_name : e._target;
    return vis.has(s) && vis.has(t);
  });
  linkSel = linkGroup.selectAll("line").data(visEdges, d => d._source+"->"+d._target+":"+d.kind);
  linkSel.exit().remove();
  const enter = linkSel.enter().append("line");
  linkSel = enter.merge(linkSel);
  linkSel
    .attr("stroke", d => eColor(d))
    .attr("stroke-width", d => eStyle(d).width)
    .attr("stroke-dasharray", d => eStyle(d).dash)
    .attr("opacity", d => eStyle(d).opacity)
    .attr("marker-end", d => eStyle(d).markerUrl);
}

// Node shape helper — driven by CFG.kind_shape
function drawNodeShape(sel) {
  // Diamonds
  sel.filter(d => KIND_SHAPE[d.kind] === "diamond")
    .append("rect").attr("class","node-shape")
    .attr("width", 10).attr("height", 10).attr("x",-5).attr("y",-5)
    .attr("transform","rotate(45)")
    .attr("fill", d => KIND_COLOR[d.kind] || "#8b949e")
    .attr("stroke","rgba(255,255,255,0.08)").attr("stroke-width",1);

  // Squares
  sel.filter(d => KIND_SHAPE[d.kind] === "square")
    .append("rect").attr("class","node-shape")
    .attr("width", 10).attr("height", 10).attr("x",-5).attr("y",-5)
    .attr("fill", d => KIND_COLOR[d.kind] || "#8b949e")
    .attr("stroke","rgba(255,255,255,0.08)").attr("stroke-width",1);

  // Circles (default)
  sel.filter(d => !KIND_SHAPE[d.kind])
    .append("circle").attr("class","node-shape")
    .attr("r", d => KIND_RADIUS[d.kind] || 6)
    .attr("fill", d => KIND_COLOR[d.kind] || "#8b949e")
    .attr("stroke", d => d.kind === COLLAPSE_KIND ? "rgba(88,166,255,0.3)" : "rgba(255,255,255,0.08)")
    .attr("stroke-width", d => d.kind === COLLAPSE_KIND ? 2 : 1);
}

function updateNodes() {
  const hiddenSet = new Set();
  for (const tqn of collapsedTopics) for (const c of allDescendants(tqn)) hiddenSet.add(c);
  nodes.forEach(n => { n._hidden = hiddenSet.has(n.qualified_name); });

  const vis = nodes.filter(n => !n._hidden);
  let nodeSel = nodeGroup.selectAll("g.node-g").data(vis, d => d.qualified_name);
  nodeSel.exit().remove();

  const enter = nodeSel.enter().append("g").attr("class","node-g");

  // Glow ring for collapsible kind
  enter.filter(d => d.kind === COLLAPSE_KIND).append("circle")
    .attr("class","glow-ring")
    .attr("r", d => (KIND_RADIUS[d.kind] || 6) + 5)
    .attr("fill","none").attr("stroke", KIND_COLOR[COLLAPSE_KIND] || "#58a6ff")
    .attr("stroke-width",1.5).attr("opacity",0.3).attr("filter","url(#glow)");

  drawNodeShape(enter);

  enter
    .attr("cursor", d => d.kind === COLLAPSE_KIND ? "pointer" : "grab")
    .on("mouseover", (ev,d) => { highlightConnected(d,true); showTooltip(ev,d); })
    .on("mousemove", ev => moveTooltip(ev))
    .on("mouseout", (ev,d) => { highlightConnected(d,false); hideTooltip(); })
    .on("click", (ev,d) => { if (d.kind === COLLAPSE_KIND) { ev.stopPropagation(); toggleCollapse(d.qualified_name); }})
    .call(d3.drag().on("start",dragS).on("drag",dragD).on("end",dragE));

  nodeSel = enter.merge(nodeSel);

  // Labels — styles from config
  const labelVis = CFG.label_visibility || {};
  const labelStyles = CFG.label_styles || {};
  const defStyle = labelStyles._default || {color:"#8b949e",size:"10px",weight:400};

  labelSel = labelGroup.selectAll("text.node-label").data(vis, d => d.qualified_name);
  labelSel.exit().remove();
  const lEnter = labelSel.enter().append("text").attr("class","node-label")
    .attr("text-anchor","start").attr("dy","0.35em")
    .text(d => d.label)
    .attr("fill", d => (labelStyles[d.kind] || defStyle).color)
    .attr("font-size", d => (labelStyles[d.kind] || defStyle).size)
    .attr("font-weight", d => (labelStyles[d.kind] || defStyle).weight);
  labelSel = lEnter.merge(labelSel);

  updateLinks();
  updateLabelVisibility();
}

function updateLabelVisibility() {
  if (!labelSel) return;
  const s = currentTransform.k;
  const vis = CFG.label_visibility || {};
  const defThreshold = vis._default !== undefined ? vis._default : 1.2;
  labelSel.attr("display", d => {
    if (!showLabels) return "none";
    const threshold = vis[d.kind] !== undefined ? vis[d.kind] : defThreshold;
    return s > threshold ? null : "none";
  });
}

function highlightConnected(d, on) {
  if (on) {
    const connected = new Set([d.qualified_name]);
    edges.forEach(e => {
      const s = typeof e.source === "object" ? e.source.qualified_name : e._source;
      const t = typeof e.target === "object" ? e.target.qualified_name : e._target;
      if (s === d.qualified_name) connected.add(t);
      if (t === d.qualified_name) connected.add(s);
    });
    nodeGroup.selectAll("g.node-g").select(".node-shape")
      .transition().duration(150).attr("opacity", n => connected.has(n.qualified_name) ? 1 : 0.15);
    linkSel.transition().duration(150)
      .attr("opacity", e => {
        const s = typeof e.source === "object" ? e.source.qualified_name : e._source;
        const t = typeof e.target === "object" ? e.target.qualified_name : e._target;
        return (s === d.qualified_name || t === d.qualified_name) ? 0.9 : 0.03;
      });
    labelSel.transition().duration(150).attr("opacity", n => connected.has(n.qualified_name) ? 1 : 0.1);
  } else {
    nodeGroup.selectAll("g.node-g").select(".node-shape").transition().duration(300).attr("opacity",1);
    linkSel.transition().duration(300).attr("opacity", e => eStyle(e).opacity);
    labelSel.transition().duration(300).attr("opacity",1);
    updateLabelVisibility();
  }
}

function toggleCollapse(qn) {
  collapsedTopics.has(qn) ? collapsedTopics.delete(qn) : collapsedTopics.add(qn);
  nodeGroup.selectAll("g.node-g").select(".glow-ring")
    .attr("stroke-dasharray", d => collapsedTopics.has(d.qualified_name) ? "4,3" : null)
    .attr("opacity", d => collapsedTopics.has(d.qualified_name) ? 0.6 : 0.3);
  updateNodes();
  simulation.alpha(0.3).restart();
}

function dragS(ev,d) { if (!ev.active) simulation.alphaTarget(0.1).restart(); d.fx=d.x; d.fy=d.y; }
function dragD(ev,d) { d.fx=ev.x; d.fy=ev.y; }
function dragE(ev,d) { if (!ev.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; }

simulation.on("tick", () => {
  if (linkSel) linkSel
    .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  nodeGroup.selectAll("g.node-g").attr("transform", d => "translate(" + d.x + "," + d.y + ")");
  if (labelSel) labelSel
    .attr("x", d => d.x + (KIND_RADIUS[d.kind] || 6) + 5)
    .attr("y", d => d.y);
});

// Start collapsed: only collapsible nodes visible
nodes.forEach(n => { if (n.kind === COLLAPSE_KIND) collapsedTopics.add(n.qualified_name); });
updateNodes();

// Auto-fit
function fitGraph() {
  const b = g.node().getBBox();
  if (b.width === 0 || b.height === 0) return;
  const pad = 0.1;
  const fw = b.width*(1+2*pad), fh = b.height*(1+2*pad);
  const s = Math.min(W/fw, H/fh, 2.5);
  const tx = W/2-(b.x+b.width/2)*s, ty = H/2-(b.y+b.height/2)*s;
  svg.transition().duration(600).call(zoomBehavior.transform, d3.zoomIdentity.translate(tx,ty).scale(s));
}
simulation.on("end", fitGraph);

// -- Controls --
document.getElementById("btn-fit").addEventListener("click", fitGraph);
document.getElementById("btn-labels").addEventListener("click", function() {
  showLabels = !showLabels;
  this.classList.toggle("active");
  updateLabelVisibility();
});

document.querySelectorAll(".legend-item[data-edge-kind]").forEach(el => {
  el.addEventListener("click", function() {
    const kind = this.dataset.edgeKind;
    if (hiddenEdgeKinds.has(kind)) { hiddenEdgeKinds.delete(kind); this.classList.remove("dimmed"); }
    else { hiddenEdgeKinds.add(kind); this.classList.add("dimmed"); }
    updateLinks();
  });
});

// -- Search --
let searchTerm = "";
document.getElementById("search").addEventListener("input", function() {
  searchTerm = this.value.trim().toLowerCase();
  applySearchFilter();
});
function applySearchFilter() {
  if (!searchTerm) {
    nodeGroup.selectAll("g.node-g").select(".node-shape").attr("opacity",1);
    if (labelSel) labelSel.attr("opacity",1);
    if (linkSel) linkSel.attr("opacity", e => eStyle(e).opacity);
    updateLabelVisibility();
    return;
  }
  const matched = new Set();
  nodes.forEach(n => {
    if (n._hidden) return;
    const hay = (n.label+" "+n.qualified_name).toLowerCase();
    if (hay.includes(searchTerm)) matched.add(n.qualified_name);
  });
  nodeGroup.selectAll("g.node-g").select(".node-shape")
    .attr("opacity", d => matched.has(d.qualified_name) ? 1 : 0.08);
  if (labelSel) labelSel
    .attr("opacity", d => matched.has(d.qualified_name) ? 1 : 0.05)
    .attr("display", d => matched.has(d.qualified_name) ? null : "none");
  if (linkSel) linkSel.attr("opacity", e => {
    const s = typeof e.source === "object" ? e.source.qualified_name : e._source;
    const t = typeof e.target === "object" ? e.target.qualified_name : e._target;
    return (matched.has(s) || matched.has(t)) ? eStyle(e).opacity : 0.02;
  });
}
</script>
</body>
</html>
"""
