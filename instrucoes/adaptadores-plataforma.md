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

### 📝 Adaptador OBSIDIAN

**Quando usar:** `{{PLATAFORMA}} == "OBSIDIAN"`

#### Callouts:

```markdown
> [!note] Nota
> Conteúdo

> [!tip] Dica
> Conteúdo

> [!warning] Atenção
> Conteúdo
```

#### Wikilinks:

```markdown
[[Aula 02 - Quick Sort]]
```

#### Tags:

```markdown
#estrutura-de-dados #ordenação
```

---

### 🐙 Adaptador GITHUB

**Quando usar:** `{{PLATAFORMA}} == "GITHUB"`

#### Callouts:

```markdown
> **Note**
> Conteúdo
```

#### Details/Summary:

```markdown
<details>
<summary>Clique para expandir</summary>

Conteúdo oculto

</details>
```

---

### 📄 Adaptador LATEX

**Quando usar:** `{{PLATAFORMA}} == "LATEX"`

#### Estrutura:

```latex
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath, amssymb}

\title{{{NOME_DISCIPLINA}}}
\author{{{INSTITUICAO}}}

\begin{document}
\maketitle
[CONTEÚDO]
\end{document}
```

#### Callouts:

```latex
\begin{tcolorbox}[colback=blue!5,title=Nota]
Conteúdo
\end{tcolorbox}
```
