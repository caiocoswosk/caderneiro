#!/usr/bin/env python3
"""
push_notion.py — Exporta todos os arquivos de conteudos/ para o Notion.

Estratégia:
  1. Arquiva todas as páginas existentes (notion_id no frontmatter)
  2. Recria todas em ordem (ordem alfabética = ordem numérica pelo prefixo)
  3. Envia os blocos de cada arquivo em chunks de 100

Uso:
    source .env && export NOTION_MD_SYNC_NOTION_TOKEN
    python3 instrucoes/scripts/push_notion.py [--content-dir DIRETORIO]

Dependências: requests (opcional — cai para urllib se não instalado)
"""

import argparse
import glob
import json
import os
import re
import sys
import time

# ---------------------------------------------------------------------------
# HTTP (requests com fallback para urllib)
# ---------------------------------------------------------------------------

try:
    import requests as _req

    def _http(method, url, headers, body=None):
        r = _req.request(method, url, headers=headers, json=body)
        if not r.ok:
            print(f"  HTTP {r.status_code}: {r.text[:600]}", file=sys.stderr)
            r.raise_for_status()
        return r.json()

except ImportError:
    import urllib.request
    import urllib.error

    def _http(method, url, headers, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code}: {e.read().decode()[:600]}", file=sys.stderr)
            raise


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

NOTION_VERSION = "2022-06-28"
CHUNK_SIZE = 100
MAP_PATH = "/tmp/img_notion_map.json"

LANG_MAP = {
    "c": "c", "cpp": "c++", "c++": "c++", "java": "java",
    "python": "python", "py": "python", "javascript": "javascript",
    "js": "javascript", "typescript": "typescript", "ts": "typescript",
    "bash": "shell", "sh": "shell", "shell": "shell",
    "sql": "sql", "html": "html", "css": "css",
    "json": "json", "yaml": "yaml", "markdown": "markdown",
    "md": "markdown", "go": "go", "rust": "rust", "ruby": "ruby",
    "kotlin": "kotlin", "swift": "swift", "r": "r",
    "mermaid": "mermaid", "latex": "plain text", "tex": "plain text",
}

CALLOUT_MAP = {
    "note":      ("📝", "gray_background"),
    "tip":       ("💡", "green_background"),
    "warning":   ("⚠️",  "yellow_background"),
    "important": ("❗", "red_background"),
    "caution":   ("🚧", "orange_background"),
}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _load_env_file():
    """Carrega variáveis do .env local sem sobrescrever as já definidas no ambiente."""
    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val


def get_token():
    _load_env_file()
    token = os.environ.get("NOTION_MD_SYNC_NOTION_TOKEN") or os.environ.get("NOTION_TOKEN")
    if not token:
        sys.exit(
            "Erro: NOTION_MD_SYNC_NOTION_TOKEN não encontrado.\n"
            "Execute: source .env && export NOTION_MD_SYNC_NOTION_TOKEN"
        )
    return token


def get_parent_page_id():
    _load_env_file()
    pid = os.environ.get("NOTION_MD_SYNC_NOTION_PARENT_PAGE_ID", "")
    if not pid:
        sys.exit("Erro: NOTION_MD_SYNC_NOTION_PARENT_PAGE_ID não definido.")
    return pid


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Notion API
# ---------------------------------------------------------------------------

_TOKEN = None
_HEADERS = None


def api(method, path, body=None):
    return _http(method, f"https://api.notion.com/v1/{path}", _HEADERS, body)


def archive_page(page_id):
    try:
        api("PATCH", f"pages/{page_id}", {"archived": True})
    except Exception:
        pass  # página pode já estar arquivada ou inexistente


def extract_emoji_from_title(title):
    """Se o título começa com emoji, retorna (emoji, título_limpo)."""
    if not title:
        return None, title
    first = title[0]
    if ord(first) > 127 and not first.isalpha() and not first.isdigit():
        m = re.match(r"^(\S+)\s+(.*)", title)
        if m:
            return m.group(1), m.group(2).strip()
    return None, title


def create_page(token, parent_page_id, title):
    emoji, clean_title = extract_emoji_from_title(title)
    payload = {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": clean_title}}]}
        },
    }
    if emoji:
        payload["icon"] = {"type": "emoji", "emoji": emoji}
    resp = api("POST", "pages", payload)
    return resp["id"]


def append_blocks(page_id, blocks):
    total = len(blocks)
    sent = 0
    all_results = []
    for start in range(0, total, CHUNK_SIZE):
        chunk = blocks[start:start + CHUNK_SIZE]
        resp = api("PATCH", f"blocks/{page_id}/children", {"children": chunk})
        all_results.extend(resp.get("results", []))
        sent += len(chunk)
        print(f"  Enviado: {sent}/{total} blocos")
        time.sleep(0.3)
    return all_results


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------

def parse_frontmatter(content):
    """Retorna (meta dict, body string)."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end == -1:
        return {}, content
    fm = content[3:end].strip()
    body = content[end + 4:].lstrip("\n")
    meta = {}
    for line in fm.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body


def write_frontmatter(filepath, meta, body):
    fm = "\n".join(f"{k}: {v}" for k, v in meta.items())
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"---\n{fm}\n---\n\n{body}")


# ---------------------------------------------------------------------------
# Rich text inline parser
# ---------------------------------------------------------------------------

def rich(text):
    """Converte markdown inline em lista de rich_text objects do Notion."""
    if not text:
        return [{"type": "text", "text": {"content": ""}}]

    result = []
    pattern = re.compile(
        r"\$\$(.+?)\$\$"                    # equação bloco inline
        r"|\$([^$\n]+?)\$"                  # equação inline
        r"|\*\*\*(.+?)\*\*\*"              # negrito+itálico
        r"|\*\*(.+?)\*\*"                  # negrito
        r"|__(.+?)__"                       # negrito (sublinhado)
        r"|\*([^*\n]+?)\*"                 # itálico
        r"|_([^_\n]+?)_"                   # itálico (sublinhado)
        r"|~~(.+?)~~"                       # tachado
        r"|`([^`]+?)`"                     # código inline
        r"|\[([^\]]+)\]\(([^)]+)\)"        # link
        r"|([^$*_~`\[]+)",                 # texto normal
        re.DOTALL,
    )

    for m in pattern.finditer(text):
        (eq_block, eq_inline, bold_italic, bold1, bold2,
         italic1, italic2, strike, code, link_text, link_url, plain) = m.groups()

        if eq_block or eq_inline:
            expr = (eq_block or eq_inline).strip()
            result.append({"type": "equation", "equation": {"expression": expr}})
        elif bold_italic:
            result.append({"type": "text", "text": {"content": bold_italic},
                           "annotations": {"bold": True, "italic": True}})
        elif bold1 or bold2:
            result.append({"type": "text", "text": {"content": bold1 or bold2},
                           "annotations": {"bold": True}})
        elif italic1 or italic2:
            result.append({"type": "text", "text": {"content": italic1 or italic2},
                           "annotations": {"italic": True}})
        elif strike:
            result.append({"type": "text", "text": {"content": strike},
                           "annotations": {"strikethrough": True}})
        elif code:
            result.append({"type": "text", "text": {"content": code},
                           "annotations": {"code": True}})
        elif link_text and link_url:
            result.append({"type": "text",
                           "text": {"content": link_text, "link": {"url": link_url}}})
        elif plain:
            result.append({"type": "text", "text": {"content": plain}})

    return result or [{"type": "text", "text": {"content": text}}]


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------

def heading_block(level, text):
    t = f"heading_{min(level, 3)}"
    return {"object": "block", "type": t, t: {"rich_text": rich(text)}}


def paragraph_block(text):
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": rich(text)}}


def quote_block(text):
    return {"object": "block", "type": "quote",
            "quote": {"rich_text": rich(text)}}


def callout_block(text, emoji, color):
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": rich(text),
            "icon": {"type": "emoji", "emoji": emoji},
            "color": color,
        },
    }


def divider_block():
    return {"object": "block", "type": "divider", "divider": {}}


def bullet_block(text, children=None):
    b = {"object": "block", "type": "bulleted_list_item",
         "bulleted_list_item": {"rich_text": rich(text)}}
    if children:
        b["bulleted_list_item"]["children"] = children
    return b


def numbered_block(text, children=None):
    b = {"object": "block", "type": "numbered_list_item",
         "numbered_list_item": {"rich_text": rich(text)}}
    if children:
        b["numbered_list_item"]["children"] = children
    return b


def todo_block(text, checked=False):
    return {"object": "block", "type": "to_do",
            "to_do": {"rich_text": rich(text), "checked": checked}}


def code_block(code, language="plain text"):
    lang = LANG_MAP.get(language.strip().lower(), "plain text")
    # Notion limita code block a 2000 chars — dividir se necessário
    chunks = _split_text(code, 2000)
    if len(chunks) == 1:
        return {"object": "block", "type": "code",
                "code": {"rich_text": [{"type": "text", "text": {"content": chunks[0]}}],
                         "language": lang}}
    # Retorna lista de blocos quando o código é muito longo
    return [
        {"object": "block", "type": "code",
         "code": {"rich_text": [{"type": "text", "text": {"content": c}}],
                  "language": lang}}
        for c in chunks
    ]


def equation_block(expr):
    return {"object": "block", "type": "equation",
            "equation": {"expression": expr.strip()}}


def image_block(file_upload_id):
    return {"object": "block", "type": "image",
            "image": {"type": "file_upload", "file_upload": {"id": file_upload_id}}}


def toggle_block(summary, children):
    t = {"rich_text": rich(summary)}
    if children:
        t["children"] = children
    return {"object": "block", "type": "toggle", "toggle": t}


_ANCHOR_LINK_RE = re.compile(r"\[([^\]]+)\]\(#([^)]+)\)")


def _strip_anchor_links(text):
    """Remove links de âncora (#...) mantendo apenas o texto visível.

    Links de âncora não funcionam diretamente no Notion — são resolvidos
    em pós-processamento via _resolve_toc_links(). Este strip serve de fallback.
    Ex: '[Título](#aula-01-titulo)' → 'Título'
    """
    return _ANCHOR_LINK_RE.sub(r"\1", text)


def _extract_anchor_links(text):
    """Extrai links de âncora de uma célula de tabela.

    Retorna lista de (display_text, anchor_slug).
    Ex: '[Título](#aula-01-titulo)' → [('Título', 'aula-01-titulo')]
    """
    return _ANCHOR_LINK_RE.findall(text)


def _slugify(text):
    """Converte texto de heading para slug estilo markdown (GFM).

    Ex: 'Aula 01: Motivação e Conceitos Iniciais'
      → 'aula-01-motivação-e-conceitos-iniciais'
    """
    text = text.lower()
    # Remove tudo que não é letra (unicode), dígito, espaço ou hífen
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    # Espaços e underscores → hífens
    text = re.sub(r"[\s_]+", "-", text.strip())
    # Remove hífens duplicados e nas bordas
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def table_block(rows):
    """rows: lista de listas de strings. Primeira linha = cabeçalho."""
    if not rows:
        return None
    n_cols = max(len(r) for r in rows)

    def make_row(cells):
        padded = cells + [""] * (n_cols - len(cells))
        return {
            "object": "block",
            "type": "table_row",
            "table_row": {
                "cells": [rich(_strip_anchor_links(c)) for c in padded]
            },
        }

    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": n_cols,
            "has_column_header": True,
            "has_row_header": False,
            "children": [make_row(r) for r in rows],
        },
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_text(text, max_len=2000):
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        cut = text.rfind("\n", 0, max_len)
        if cut == -1:
            cut = max_len
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    return chunks


def _is_separator_row(line):
    s = line.strip()
    return s.startswith("|") and all(
        re.fullmatch(r"[\s:\-]+", p) for p in s.strip("|").split("|")
    )


def _parse_table_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _indent_level(line):
    """Retorna o nível de indentação em múltiplos de 2 espaços."""
    return (len(line) - len(line.lstrip(" "))) // 2


# ---------------------------------------------------------------------------
# Markdown → Notion blocks
# ---------------------------------------------------------------------------

def md_to_blocks(lines, img_map):
    blocks = []
    meta = {"heading_slugs": {}, "table_anchors": []}
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Linha vazia
        if not stripped:
            i += 1
            continue

        # Frontmatter residual (segurança)
        if stripped == "---" and i == 0:
            i += 1
            while i < n and lines[i].strip() != "---":
                i += 1
            i += 1
            continue

        # Equação em bloco ($$)
        if stripped.startswith("$$"):
            expr = stripped[2:]
            if stripped.endswith("$$") and len(stripped) > 4:
                blocks.append(equation_block(stripped[2:-2]))
                i += 1
                continue
            i += 1
            while i < n and not lines[i].strip().endswith("$$"):
                expr += "\n" + lines[i]
                i += 1
            if i < n:
                expr += "\n" + lines[i].strip().rstrip("$$")
            blocks.append(equation_block(expr))
            i += 1
            continue

        # Bloco de código
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            code_lines = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i].rstrip("\n"))
                i += 1
            i += 1
            result = code_block("\n".join(code_lines), lang or "plain text")
            if isinstance(result, list):
                blocks.extend(result)
            else:
                blocks.append(result)
            continue

        # <details> → toggle
        if re.match(r"^<details\b", stripped, re.IGNORECASE):
            i += 1
            summary = ""
            if i < n:
                sm = re.match(r"<summary>(.*?)</summary>", lines[i].strip(), re.IGNORECASE)
                if sm:
                    summary = sm.group(1)
                    i += 1
            inner = []
            while i < n and not re.match(r"^</details>", lines[i].strip(), re.IGNORECASE):
                inner.append(lines[i])
                i += 1
            i += 1
            children, _ = md_to_blocks(inner, img_map)
            blocks.append(toggle_block(summary, children))
            continue

        # Tags HTML soltas (ignorar)
        if re.match(r"^</?(details|summary|div|span|p|br)[^>]*>\s*$", stripped, re.IGNORECASE):
            i += 1
            continue

        # Divisor
        if re.match(r"^[-*_]{3,}$", stripped):
            blocks.append(divider_block())
            i += 1
            continue

        # Headings
        m = re.match(r"^(#{1,4})\s+(.*)", stripped)
        if m:
            heading_text = m.group(2)
            meta["heading_slugs"][len(blocks)] = _slugify(heading_text)
            blocks.append(heading_block(len(m.group(1)), heading_text))
            i += 1
            continue

        # Imagem
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", stripped)
        if m:
            src = m.group(2)
            if not src.startswith("http"):
                fname = os.path.basename(src)
                if fname in img_map:
                    blocks.append(image_block(img_map[fname]))
                else:
                    print(f"  [aviso] imagem não encontrada no mapa: {fname}")
            i += 1
            continue

        # Callout GitHub-style: > [!NOTE], > [!TIP], etc.
        m = re.match(r"^>\s*\[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]\s*(.*)?$",
                     stripped, re.IGNORECASE)
        if m:
            kind = m.group(1).lower()
            first_line = m.group(2) or ""
            i += 1
            # Coletar linhas continuadas do callout
            cont_lines = [first_line] if first_line else []
            while i < n and lines[i].strip().startswith(">"):
                cont_lines.append(lines[i].strip().lstrip(">").strip())
                i += 1
            emoji, color = CALLOUT_MAP.get(kind, ("📝", "gray_background"))
            blocks.append(callout_block(" ".join(cont_lines), emoji, color))
            continue

        # Blockquote (simples)
        if stripped.startswith(">"):
            quote_lines = []
            while i < n and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append(quote_block("\n".join(quote_lines)))
            continue

        # Tabela markdown
        if stripped.startswith("|"):
            rows = []
            anchor_info = []
            while i < n and lines[i].strip().startswith("|"):
                if not _is_separator_row(lines[i]):
                    row_cells = _parse_table_row(lines[i])
                    row_idx = len(rows)
                    for col_idx, cell in enumerate(row_cells):
                        for display, slug in _extract_anchor_links(cell):
                            anchor_info.append((row_idx, col_idx, display, slug))
                    rows.append(row_cells)
                i += 1
            t = table_block(rows)
            if t:
                if anchor_info:
                    meta["table_anchors"].append({
                        "block_index": len(blocks),
                        "anchors": anchor_info,
                    })
                blocks.append(t)
            continue

        # Todo (checkbox)
        m = re.match(r"^[-*]\s+\[([ xX])\]\s+(.*)", stripped)
        if m:
            blocks.append(todo_block(m.group(2), m.group(1).lower() == "x"))
            i += 1
            continue

        # Lista com marcador (com suporte a aninhamento)
        m = re.match(r"^[-*]\s+(.*)", stripped)
        if m:
            text = m.group(1)
            current_indent = _indent_level(line)
            i += 1
            # Coletar sub-itens indentados
            child_lines = []
            while i < n:
                next_line = lines[i]
                if not next_line.strip():
                    break
                next_indent = _indent_level(next_line)
                if next_indent > current_indent and re.match(r"^\s+[-*\d]", next_line):
                    child_lines.append(next_line[2:])  # remove 2 espaços de indentação
                    i += 1
                else:
                    break
            children = md_to_blocks(child_lines, img_map)[0] if child_lines else None
            blocks.append(bullet_block(text, children))
            continue

        # Lista numerada (com suporte a aninhamento)
        m = re.match(r"^\d+\.\s+(.*)", stripped)
        if m:
            text = m.group(1)
            current_indent = _indent_level(line)
            i += 1
            child_lines = []
            while i < n:
                next_line = lines[i]
                if not next_line.strip():
                    break
                next_indent = _indent_level(next_line)
                if next_indent > current_indent and re.match(r"^\s+[-*\d]", next_line):
                    child_lines.append(next_line[2:])
                    i += 1
                else:
                    break
            children = md_to_blocks(child_lines, img_map)[0] if child_lines else None
            blocks.append(numbered_block(text, children))
            continue

        # Parágrafo genérico
        blocks.append(paragraph_block(stripped))
        i += 1

    return blocks, meta


# ---------------------------------------------------------------------------
# Imagem map
# ---------------------------------------------------------------------------

def load_image_map():
    if os.path.exists(MAP_PATH):
        with open(MAP_PATH) as f:
            m = json.load(f)
        print(f"Mapa de imagens carregado: {len(m)} entradas")
        return m
    return {}


# ---------------------------------------------------------------------------
# TOC link resolution (pós-processamento)
# ---------------------------------------------------------------------------

def _resolve_toc_links(page_id, results, metadata):
    """Resolve links de âncora do sumário para links internos do Notion.

    Após enviar todos os blocos, usa os IDs retornados pela API para
    atualizar as células da tabela do sumário com links clicáveis que
    navegam até o heading correspondente na página.
    """
    if not metadata.get("table_anchors"):
        return

    # 1. Mapear slug → block_id a partir dos headings criados
    slug_to_block_id = {}
    for block_idx, slug in metadata["heading_slugs"].items():
        if block_idx < len(results):
            slug_to_block_id[slug] = results[block_idx]["id"]

    if not slug_to_block_id:
        print("  [aviso] Nenhum heading encontrado para resolver links do sumário")
        return

    page_id_clean = page_id.replace("-", "")

    # 2. Para cada tabela com âncoras, buscar rows e atualizar células
    for table_info in metadata["table_anchors"]:
        block_idx = table_info["block_index"]
        if block_idx >= len(results):
            continue

        table_block_id = results[block_idx]["id"]

        # GET children da tabela (rows) — IDs não vêm no response do append
        try:
            children_resp = api("GET", f"blocks/{table_block_id}/children?page_size=100")
            time.sleep(0.3)
        except Exception as e:
            print(f"  [aviso] Falha ao buscar rows da tabela: {e}")
            continue

        row_blocks = children_resp.get("results", [])

        # Agrupar âncoras por row_idx
        anchors_by_row = {}
        for row_idx, col_idx, display, slug in table_info["anchors"]:
            anchors_by_row.setdefault(row_idx, []).append((col_idx, display, slug))

        # 3. PATCH cada row que tem âncora
        resolved = 0
        for row_idx, anchor_list in anchors_by_row.items():
            if row_idx >= len(row_blocks):
                continue

            row_block = row_blocks[row_idx]
            row_id = row_block["id"]
            cells = row_block["table_row"]["cells"]

            modified = False
            for col_idx, display, slug in anchor_list:
                target_id = slug_to_block_id.get(slug)
                if target_id is None:
                    continue  # fallback: célula fica com texto puro

                block_id_clean = target_id.replace("-", "")
                notion_url = f"https://www.notion.so/{page_id_clean}#{block_id_clean}"

                cells[col_idx] = [{
                    "type": "text",
                    "text": {
                        "content": display,
                        "link": {"url": notion_url}
                    }
                }]
                modified = True

            if modified:
                try:
                    api("PATCH", f"blocks/{row_id}", {
                        "table_row": {"cells": cells}
                    })
                    resolved += 1
                    time.sleep(0.3)
                except Exception as e:
                    print(f"  [aviso] Falha ao atualizar row {row_idx}: {e}")

        if resolved:
            print(f"  Links do sumário: {resolved} resolvidos")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Exporta conteudos/ para o Notion.")
    parser.add_argument("--content-dir", default="conteudos",
                        help="Diretório com os arquivos .md (padrão: conteudos)")
    args = parser.parse_args()

    content_dir = args.content_dir.rstrip("/")

    global _TOKEN, _HEADERS
    _TOKEN = get_token()
    parent_page_id = get_parent_page_id()
    _HEADERS = auth_headers(_TOKEN)

    img_map = load_image_map()

    IGNORE = {"welcome.md"}
    md_files = sorted(
        f for f in glob.glob(f"{content_dir}/*.md")
        if os.path.basename(f) not in IGNORE
    )
    if not md_files:
        sys.exit(f"Nenhum arquivo .md encontrado em {content_dir}/")

    print(f"Arquivos encontrados: {len(md_files)}")

    # Passo 1: arquivar páginas existentes
    print("\nArquivando páginas existentes...")
    for filepath in md_files:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        meta, _ = parse_frontmatter(content)
        nid = meta.get("notion_id", "").strip()
        if nid:
            archive_page(nid)
            print(f"  Arquivada: {os.path.basename(filepath)} ({nid})")

    # Passo 2: recriar e enviar
    print("\nCriando páginas e enviando conteúdo...")
    errors = []
    for filepath in md_files:
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            meta, body = parse_frontmatter(content)

            m = re.search(r"^#\s+(.+)", body, re.MULTILINE)
            title = m.group(1).strip() if m else os.path.splitext(os.path.basename(filepath))[0]

            notion_id = create_page(_TOKEN, parent_page_id, title)
            meta["notion_id"] = notion_id
            write_frontmatter(filepath, meta, body)
            print(f"\n[{os.path.basename(filepath)}] '{title}' → {notion_id}")

            # Remover H1 (já é o título da página)
            lines = body.split("\n")
            first_h1 = next((idx for idx, l in enumerate(lines) if re.match(r"^#\s", l)), None)
            if first_h1 is not None:
                lines = lines[:first_h1] + lines[first_h1 + 1:]

            blocks, block_meta = md_to_blocks(lines, img_map)
            print(f"  {len(blocks)} blocos")
            results = append_blocks(notion_id, blocks)

            if block_meta.get("table_anchors"):
                _resolve_toc_links(notion_id, results, block_meta)

        except Exception as e:
            errors.append((os.path.basename(filepath), str(e)))
            print(f"  [ERRO] {os.path.basename(filepath)}: {e}", file=sys.stderr)

    print("\nExportação concluída.")
    if errors:
        print(f"\n⚠️  {len(errors)} arquivo(s) com erro:")
        for name, err in errors:
            print(f"  - {name}: {err}")
    else:
        print(f"✓ {len(md_files)} arquivo(s) exportados com sucesso.")


if __name__ == "__main__":
    main()
