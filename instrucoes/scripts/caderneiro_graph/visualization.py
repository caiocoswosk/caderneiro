"""Visualização D3.js interativa para o grafo de conhecimento acadêmico.

Gera HTML self-contained com force-directed layout, dark theme,
zoom, drag, collapse, busca e legenda interativa.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .graph import GraphStore, edge_to_dict, node_to_dict


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


def generate_html(store: GraphStore, output_path: str | Path) -> Path:
    """Gera HTML interativo self-contained."""
    output_path = Path(output_path)
    data = export_graph_data(store)
    data_json = json.dumps(data, default=str, ensure_ascii=False).replace("</", "<\\/")
    html = _HTML_TEMPLATE.replace("__GRAPH_DATA__", data_json)
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
<title>Grafo de Conhecimento — Caderneiro</title>
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
  .l-prerequisite { border-top: 2.5px solid #f85149; }
  .l-references { border-top: 2px dashed #58a6ff; }
  .l-evaluates { border-top: 2px dotted #d2a8ff; }
  .l-extends { border-top: 1.5px solid #f0883e; }
  .l-contains { border-top: 1px solid rgba(139,148,158,0.3); }

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

<div id="legend" role="complementary" aria-label="Legenda do grafo">
  <h3>Tipos de N&oacute;</h3>
  <div class="legend-section">
    <div class="legend-item"><span class="legend-circle" style="background:#58a6ff"></span> T&oacute;pico</div>
    <div class="legend-item"><span class="legend-circle" style="background:#f0883e"></span> Aula</div>
    <div class="legend-item"><span class="legend-circle" style="background:#3fb950"></span> Conceito</div>
    <div class="legend-item"><span class="legend-circle" style="background:#56d364"></span> Se&ccedil;&atilde;o</div>
    <div class="legend-item"><span class="legend-shape" style="background:#d2a8ff;transform:rotate(45deg)"></span> Exerc&iacute;cio</div>
    <div class="legend-item"><span class="legend-shape" style="background:#8b949e"></span> Gloss&aacute;rio</div>
    <div class="legend-item"><span class="legend-circle" style="background:#f778ba"></span> F&oacute;rmula</div>
  </div>
  <h3>Arestas</h3>
  <div class="legend-section">
    <div class="legend-item" data-edge-kind="CONTAINS"><span class="legend-line l-contains"></span> Cont&eacute;m</div>
    <div class="legend-item" data-edge-kind="PREREQUISITE"><span class="legend-line l-prerequisite"></span> Pr&eacute;-requisito</div>
    <div class="legend-item" data-edge-kind="REFERENCES"><span class="legend-line l-references"></span> Refer&ecirc;ncia</div>
    <div class="legend-item" data-edge-kind="EVALUATES"><span class="legend-line l-evaluates"></span> Avalia</div>
    <div class="legend-item" data-edge-kind="EXTENDS"><span class="legend-line l-extends"></span> Estende</div>
  </div>
</div>

<div id="controls">
  <input id="search" type="text" placeholder="Buscar n&oacute;s&#8230;" autocomplete="off" spellcheck="false">
  <button id="btn-fit" title="Ajustar &agrave; tela">Ajustar</button>
  <button id="btn-labels" title="Alternar labels" class="active">Labels</button>
</div>

<div id="stats-bar" role="status"></div>
<div id="tooltip"></div>
<svg role="img" aria-label="Grafo de conhecimento acad&ecirc;mico interativo"></svg>

<script>
const graphData = __GRAPH_DATA__;

// -- Config --
const KIND_COLOR = {
  Topic:"#58a6ff", Lesson:"#f0883e", Concept:"#3fb950", Section:"#56d364",
  Exercise:"#d2a8ff", GlossaryTerm:"#8b949e", Formula:"#f778ba"
};
const KIND_RADIUS = {
  Topic:20, Lesson:12, Concept:8, Section:6, Exercise:6, GlossaryTerm:5, Formula:5
};
const EDGE_COLOR = {
  CONTAINS:"rgba(139,148,158,0.15)", PREREQUISITE:"#f85149",
  REFERENCES:"#58a6ff", EVALUATES:"#d2a8ff", EXTENDS:"#f0883e",
  GENERATED_FROM:"#8b949e"
};

function displayName(d) {
  if (d.kind === "Topic") {
    return d.name;
  }
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

edges.forEach(e => {
  if (e.kind === "CONTAINS") {
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
const si = (l,v) => `<div class="stat-item"><span class="tt-label">${l}</span> <span class="stat-value">${v}</span></div>`;
statsBar.innerHTML = si("N\u00f3s", stats.total_nodes) + si("Arestas", stats.total_edges) + si("Arquivos", stats.files_count);

// -- Tooltip --
const tooltip = document.getElementById("tooltip");
function escH(s) { return !s ? "" : String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

function showTooltip(ev, d) {
  const bg = KIND_COLOR[d.kind] || "#555";
  let h = `<span class="tt-name">${escH(d.label)}</span>`;
  h += `<span class="tt-kind" style="background:${bg};color:#0d1117">${d.kind}</span>`;
  if (d.file_path) h += `<div class="tt-row tt-file">${escH(d.file_path)}</div>`;
  if (d.line_start != null) h += `<div class="tt-row"><span class="tt-label">Linhas: </span>${d.line_start} \u2013 ${d.line_end || d.line_start}</div>`;
  if (d.difficulty) h += `<div class="tt-row"><span class="tt-label">Dificuldade: </span>${escH(d.difficulty)}</div>`;
  if (d.extra) {
    if (d.extra.definition) h += `<div class="tt-row"><span class="tt-label">Def: </span>${escH(d.extra.definition)}</div>`;
    if (d.extra.latex) h += `<div class="tt-row"><span class="tt-label">$$</span> ${escH(d.extra.latex.substring(0,80))}</div>`;
    if (d.extra.study_time) h += `<div class="tt-row"><span class="tt-label">Tempo: </span>${escH(d.extra.study_time)}</div>`;
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

// Arrow markers
const defs = svg.append("defs");
const glow = defs.append("filter").attr("id","glow").attr("x","-50%").attr("y","-50%").attr("width","200%").attr("height","200%");
glow.append("feGaussianBlur").attr("stdDeviation","3").attr("result","blur");
glow.append("feComposite").attr("in","SourceGraphic").attr("in2","blur").attr("operator","over");

[
  {id:"arrow-prereq",color:"#f85149"},
  {id:"arrow-ref",color:"#58a6ff"},
  {id:"arrow-eval",color:"#d2a8ff"},
  {id:"arrow-ext",color:"#f0883e"}
].forEach(mk => {
  defs.append("marker").attr("id", mk.id)
    .attr("viewBox","0 -5 10 10").attr("refX",28).attr("refY",0)
    .attr("markerWidth",8).attr("markerHeight",8).attr("orient","auto")
    .append("path").attr("d","M0,-4L10,0L0,4Z").attr("fill",mk.color);
});

// -- Simulation --
const N = nodes.length;
const isLarge = N > 200;
const chargeTopic = isLarge ? -300 : -500;
const chargeOther = isLarge ? -50 : -100;
const linkDist = isLarge ? 60 : 100;

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(edges).id(d => d.qualified_name)
    .distance(d => d.kind === "CONTAINS" ? 30 : linkDist)
    .strength(d => d.kind === "CONTAINS" ? 1.5 : 0.15))
  .force("charge", d3.forceManyBody().strength(d => d.kind === "Topic" ? chargeTopic : chargeOther).theta(0.85).distanceMax(500))
  .force("collide", d3.forceCollide().radius(d => (KIND_RADIUS[d.kind] || 6) + 3))
  .force("center", d3.forceCenter(W/2, H/2))
  .force("x", d3.forceX(W/2).strength(0.03))
  .force("y", d3.forceY(H/2).strength(0.03))
  .alphaDecay(isLarge ? 0.04 : 0.025)
  .velocityDecay(0.4);

// -- Edge styles --
const EDGE_CFG = {
  CONTAINS:       {dash:null,  width:0.8, opacity:0.08, marker:""},
  PREREQUISITE:   {dash:null,  width:2.5, opacity:0.8,  marker:"url(#arrow-prereq)"},
  REFERENCES:     {dash:"6,3", width:1.5, opacity:0.65, marker:"url(#arrow-ref)"},
  EVALUATES:      {dash:"3,4", width:1.5, opacity:0.6,  marker:"url(#arrow-eval)"},
  EXTENDS:        {dash:null,  width:1.2, opacity:0.5,  marker:"url(#arrow-ext)"},
  GENERATED_FROM: {dash:"2,2", width:1,   opacity:0.4,  marker:""},
};

function eStyle(d) { return EDGE_CFG[d.kind] || {dash:null,width:1,opacity:0.3,marker:""}; }
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
    .attr("marker-end", d => eStyle(d).marker);
}

// Node shape helper
function drawNodeShape(sel) {
  // Circles for most types
  sel.filter(d => !["Exercise","GlossaryTerm"].includes(d.kind))
    .append("circle").attr("class","node-shape")
    .attr("r", d => KIND_RADIUS[d.kind] || 6)
    .attr("fill", d => KIND_COLOR[d.kind] || "#8b949e")
    .attr("stroke", d => d.kind === "Topic" ? "rgba(88,166,255,0.3)" : "rgba(255,255,255,0.08)")
    .attr("stroke-width", d => d.kind === "Topic" ? 2 : 1);

  // Diamond for Exercise
  sel.filter(d => d.kind === "Exercise")
    .append("rect").attr("class","node-shape")
    .attr("width", 10).attr("height", 10).attr("x",-5).attr("y",-5)
    .attr("transform","rotate(45)")
    .attr("fill","#d2a8ff")
    .attr("stroke","rgba(255,255,255,0.08)").attr("stroke-width",1);

  // Square for GlossaryTerm
  sel.filter(d => d.kind === "GlossaryTerm")
    .append("rect").attr("class","node-shape")
    .attr("width", 10).attr("height", 10).attr("x",-5).attr("y",-5)
    .attr("fill","#8b949e")
    .attr("stroke","rgba(255,255,255,0.08)").attr("stroke-width",1);
}

function updateNodes() {
  const hiddenSet = new Set();
  for (const tqn of collapsedTopics) for (const c of allDescendants(tqn)) hiddenSet.add(c);
  nodes.forEach(n => { n._hidden = hiddenSet.has(n.qualified_name); });

  const vis = nodes.filter(n => !n._hidden);
  let nodeSel = nodeGroup.selectAll("g.node-g").data(vis, d => d.qualified_name);
  nodeSel.exit().remove();

  const enter = nodeSel.enter().append("g").attr("class","node-g");

  // Topic glow
  enter.filter(d => d.kind === "Topic").append("circle")
    .attr("class","glow-ring")
    .attr("r", d => KIND_RADIUS[d.kind] + 5)
    .attr("fill","none").attr("stroke","#58a6ff")
    .attr("stroke-width",1.5).attr("opacity",0.3).attr("filter","url(#glow)");

  drawNodeShape(enter);

  enter
    .attr("cursor", d => d.kind === "Topic" ? "pointer" : "grab")
    .on("mouseover", (ev,d) => { highlightConnected(d,true); showTooltip(ev,d); })
    .on("mousemove", ev => moveTooltip(ev))
    .on("mouseout", (ev,d) => { highlightConnected(d,false); hideTooltip(); })
    .on("click", (ev,d) => { if (d.kind === "Topic") { ev.stopPropagation(); toggleCollapse(d.qualified_name); }})
    .call(d3.drag().on("start",dragS).on("drag",dragD).on("end",dragE));

  nodeSel = enter.merge(nodeSel);

  // Labels
  labelSel = labelGroup.selectAll("text.node-label").data(vis, d => d.qualified_name);
  labelSel.exit().remove();
  const lEnter = labelSel.enter().append("text").attr("class","node-label")
    .attr("text-anchor","start").attr("dy","0.35em")
    .text(d => d.label)
    .attr("fill", d => {
      if (d.kind === "Topic") return "#e6edf3";
      if (d.kind === "Lesson") return "#f0883e";
      return "#8b949e";
    })
    .attr("font-size", d => d.kind === "Topic" ? "13px" : d.kind === "Lesson" ? "11px" : "10px")
    .attr("font-weight", d => d.kind === "Topic" ? 700 : d.kind === "Lesson" ? 600 : 400);
  labelSel = lEnter.merge(labelSel);

  updateLinks();
  updateLabelVisibility();
}

function updateLabelVisibility() {
  if (!labelSel) return;
  const s = currentTransform.k;
  labelSel.attr("display", d => {
    if (!showLabels) return "none";
    if (d.kind === "Topic") return null;
    if (d.kind === "Lesson") return s > 0.4 ? null : "none";
    if (d.kind === "Concept") return s > 0.8 ? null : "none";
    return s > 1.2 ? null : "none";
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
  nodeGroup.selectAll("g.node-g").attr("transform", d => `translate(${d.x},${d.y})`);
  if (labelSel) labelSel
    .attr("x", d => d.x + (KIND_RADIUS[d.kind] || 6) + 5)
    .attr("y", d => d.y);
});

// Start collapsed: only Topic nodes visible
nodes.forEach(n => { if (n.kind === "Topic") collapsedTopics.add(n.qualified_name); });
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
