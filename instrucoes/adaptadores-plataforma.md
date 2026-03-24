# Adaptadores de Plataforma

### 📘 Adaptador NOTION

**Quando usar:** `{{PLATAFORMA}} == "NOTION"`

#### Toggles (Expandable):

```markdown
<details>
<summary>Título do Toggle</summary>

Conteúdo que será ocultado/expandível

</details>
```

#### Callouts:

```markdown
> 💡 **Dica:** Conteúdo da dica

> ⚠️ **Atenção:** Conteúdo do aviso

> ✅ **Boas Práticas:** Conteúdo

> ❌ **Evite:** Conteúdo
```

#### Fórmulas:

```markdown
Inline: $$E = mc^2$$
```

---

### ⬜ Sem Plataforma (NENHUMA)

**Quando usar:** `{{PLATAFORMA}} == "NENHUMA"`

#### Callouts:

```markdown
> **Nota:** Conteúdo

> **Dica:** Conteúdo

> **Atenção:** Conteúdo
```

Markdown neutro — compatível com qualquer visualizador.

---

### 📄 Exportação PDF (disponível para qualquer plataforma)

PDF é gerado via `pandoc` a partir dos arquivos `.md` em `conteudos/`, independente da plataforma de estudo escolhida.

```bash
for f in conteudos/*.md; do
  pandoc "$f" -o "${f%.md}.pdf" --resource-path=conteudos/imagens
done
```

PDFs gerados na mesma pasta dos `.md` correspondentes.
