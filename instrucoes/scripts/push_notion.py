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
    for start in range(0, total, CHUNK_SIZE):
        chunk = blocks[start:start + CHUNK_SIZE]
        api("PATCH", f"blocks/{page_id}/children", {"children": chunk})
        sent += len(chunk)
        print(f"  Enviado: {sent}/{total} blocos")
        time.sleep(0.3)


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
                "cells": [[{"type": "text", "text": {"content": c}}] for c in padded]
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
            children = md_to_blocks(inner, img_map)
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
            blocks.append(heading_block(len(m.group(1)), m.group(2)))
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
            while i < n and lines[i].strip().startswith("|"):
                if not _is_separator_row(lines[i]):
                    rows.append(_parse_table_row(lines[i]))
                i += 1
            t = table_block(rows)
            if t:
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
            children = md_to_blocks(child_lines, img_map) if child_lines else None
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
            children = md_to_blocks(child_lines, img_map) if child_lines else None
            blocks.append(numbered_block(text, children))
            continue

        # Parágrafo genérico
        blocks.append(paragraph_block(stripped))
        i += 1

    return blocks


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

            blocks = md_to_blocks(lines, img_map)
            print(f"  {len(blocks)} blocos")
            append_blocks(notion_id, blocks)

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
