#!/usr/bin/env python3
"""
upload_images_notion.py — Faz upload de imagens para a Notion File Upload API.
Salva o mapeamento nome_arquivo → file_upload_id em /tmp/img_notion_map.json.

Formatos suportados: .png, .jpg, .jpeg, .webp, .gif

Uso:
    source .env && export NOTION_MD_SYNC_NOTION_TOKEN
    python3 instrucoes/scripts/upload_images_notion.py [--images-dir DIRETORIO]

Dependências: requests
"""

import argparse
import glob
import json
import os
import sys

import requests

NOTION_VERSION = "2022-06-28"
MAP_PATH = "/tmp/img_notion_map.json"

MIME_TYPES = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif":  "image/gif",
}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _load_env_file():
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


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def upload_image(filepath, token):
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()
    mime = MIME_TYPES.get(ext, "image/png")

    # Passo 1: criar objeto de upload
    r = requests.post(
        "https://api.notion.com/v1/file_uploads",
        headers=auth_headers(token),
        json={"filename": filename, "content_type": mime},
    )
    r.raise_for_status()
    data = r.json()
    upload_id = data["id"]
    upload_url = data["upload_url"]

    # Passo 2: enviar o arquivo (sem Content-Type — requests seta multipart automaticamente)
    with open(filepath, "rb") as f:
        r2 = requests.post(
            upload_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
            },
            files={"file": (filename, f, mime)},
        )
    r2.raise_for_status()

    return upload_id


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Faz upload de imagens para o Notion e salva o mapa em /tmp/img_notion_map.json."
    )
    parser.add_argument("--images-dir", default="conteudos/imagens",
                        help="Diretório raiz das imagens (padrão: conteudos/imagens)")
    args = parser.parse_args()

    token = get_token()
    images_dir = args.images_dir.rstrip("/")

    # Carregar mapa existente
    img_map = {}
    if os.path.exists(MAP_PATH):
        with open(MAP_PATH) as f:
            img_map = json.load(f)
        print(f"Mapa existente: {len(img_map)} entradas")

    # Listar todas as imagens suportadas
    patterns = [f"{images_dir}/**/*{ext}" for ext in MIME_TYPES]
    images = sorted(
        path for pat in patterns for path in glob.glob(pat, recursive=True)
    )
    print(f"Imagens encontradas: {len(images)}")

    uploaded = 0
    skipped = 0
    errors = []

    for img_path in images:
        name = os.path.basename(img_path)
        if name in img_map:
            skipped += 1
            continue
        try:
            file_id = upload_image(img_path, token)
            img_map[name] = file_id
            print(f"  ✓ {name} → {file_id}")
            uploaded += 1
        except Exception as e:
            errors.append((name, str(e)))
            print(f"  ✗ {name} — erro: {e}")

    # Salvar mapeamento
    with open(MAP_PATH, "w") as f:
        json.dump(img_map, f, indent=2)

    print(f"\nMapeamento salvo em {MAP_PATH}")
    print(f"  {uploaded} novas, {skipped} já existentes, {len(errors)} erros")
    if errors:
        print("  Erros:")
        for name, err in errors:
            print(f"    - {name}: {err}")


if __name__ == "__main__":
    main()
