# Módulos Opcionais

### 💻 Módulo 1: ANÁLISE DE CÓDIGO

**Quando ativar:** `{{MODULO_CODIGO}} == true`

#### Instruções para o Agente:

**Etapas de Análise:**

1. **Extração:**
   - Ler arquivo completo
   - Identificar linguagem
   - Verificar compilação/sintaxe

2. **Comentário Linha por Linha:**
   - Para cada linha significativa:
     * O que faz (ação)
     * Por que faz (razão)
     * Complexidade (se relevante)

3. **Análise de Estrutura:**
   - Identificar funções/métodos
   - Mapear dependências
   - Destacar padrões de design

4. **Geração de Exemplos:**
   - Criar entrada de exemplo
   - Traçar execução passo a passo
   - Mostrar saída esperada

#### Template de Saída:

```[linguagem]
// ========================================
// FUNÇÃO: [nome]
// PROPÓSITO: [o que faz]
// COMPLEXIDADE: O(?)
// ========================================

[linha 1 do código]  // [comentário explicativo]
[linha 2 do código]  // [comentário explicativo]
...
```

**Exemplo de Execução:**

```
Entrada: [valor]
Passo 1: [estado]
Passo 2: [estado]
...
Saída: [resultado]
```

---

### 📊 Módulo 2: DIAGRAMAS

**Quando ativar:** `{{MODULO_DIAGRAMAS}} == true`

#### Decisão: Mermaid vs ASCII vs Tabela

**✅ USE MERMAID para:**
- Fluxogramas de algoritmos
- Árvores (binárias, B-tree, etc.)
- Grafos e relações
- Diagramas de sequência
- Mapas mentais

**❌ NÃO use Mermaid para:**
- Arrays com índices e valores lado a lado
- Representações de memória (ponteiros)
- Estruturas de baixo nível (stack frames)
- Matrizes com valores específicos

**✅ USE ASCII ART para:**
- Arrays e vetores
- Pilhas e filas visuais
- Ponteiros e referências
- Estruturas de memória

**✅ USE TABELAS para:**
- Comparações de características
- Análise de complexidade múltipla
- Estados passo-a-passo

#### Exemplos por Tipo:

**ARRAY/VETOR → ASCII Art**

```
Array após inserção:
Índice:  0   1   2   3   4
       +---+---+---+---+---+
Valor: | 5 | 2 | 8 | 1 | 9 |
       +---+---+---+---+---+
         ↑
         |
       início
```

**LISTA ENCADEADA → ASCII Art**

```
Lista Encadeada:
   head
    |
    v
  +---+---+    +---+---+    +---+---+
  | 5 | *----> | 2 | *----> | 8 |NULL|
  +---+---+    +---+---+    +---+---+
```

---

### ✏️ Módulo 3: EXERCÍCIOS

**Quando ativar:** `{{MODULO_EXERCICIOS}} == true`

#### Sistema de Geração:

**Quantidade Adaptativa:**
- Tópico Simples: 5-8 exercícios
- Tópico Médio: 9-12 exercícios
- Tópico Complexo: 13-20 exercícios

**Distribuição por Dificuldade:**
- 40% Básico 🟢 (aplicação direta)
- 40% Intermediário 🟡 (combina 2+ conceitos)
- 20% Avançado 🔴 (desafio, generalização)

#### Template de Exercício:

**Para Cursos Técnicos:**

```markdown
🟢 **Básico:** [Enunciado claro e direto]

**Entrada:** [exemplo]
**Saída esperada:** [exemplo]

<details>
<summary>💡 Ver Solução</summary>

**Solução:**

```[linguagem]
[código completo]
```

**Explicação:** ...

</details>
```

---

### 📖 Módulo 4: GLOSSÁRIO

**Quando ativar:** `{{MODULO_GLOSSARIO}} == true`

#### Template por Aula:

```markdown
### 📖 Glossário

<details>
<summary>Termos Técnicos desta Aula</summary>

- **[Termo 1]:** Definição clara e concisa.
- **[Termo 2]:** Definição.

</details>
```

---

### 🧮 Módulo 5: FÓRMULAS MATEMÁTICAS

**Quando ativar:** `{{MODULO_FORMULAS}} == true`

#### Sintaxe por Plataforma:

**Notion:**
```markdown
$$E = mc^2$$
```

**Obsidian:**
```markdown
$E = mc^2$
```

**GitHub:**
```markdown
$E = mc^2$
```

**LaTeX:**
```latex
$E = mc^2$
```

---

### 📚 Módulo 6: REFERÊNCIAS

**Quando ativar:** `{{MODULO_REFERENCIAS}} == true`

#### Template de Seção:

```markdown
## 📚 REFERÊNCIAS

[1] SOBRENOME, Nome. **Título**. Edição. Cidade: Editora, Ano.

[2] AUTOR, N. et al. Título do artigo. **Nome da Conferência**, v. X, n. Y, p. Z-W, Ano.

### Recursos Online

- 📹 [Nome do Vídeo](URL)
- 💻 [Nome do Repositório](URL)
```

---

### 🎥 Módulo 7: MÍDIA

**Quando ativar:** `{{MODULO_MIDIA}} == true`

#### Processamento de Imagens:

1. Se for **diagrama técnico**: recriar em Mermaid ou ASCII
2. Se for **foto de quadro**: transcrever conteúdo
3. Se for **gráfico**: extrair dados e recriar em tabela
4. Se for **screenshot de código**: digitar código

#### Processamento de Vídeos:

- Transcrever pontos-chave
- Capturar timestamps
- Linkar para recurso original

---

### 📸 Módulo 8: TRANSCRIÇÃO DE MATERIAIS MANUSCRITOS

**Quando ativar:** `{{MODULO_TRANSCRICAO}} == true`

**Arquivo de saída:** `aulas/aula-XX/{{ARQUIVO_TRANSCRICAO}}` (padrão: `transcricao.md`)

**Regras de execução obrigatórias:**
- O agente **deve saber qual aula transcrever** antes de iniciar. Se o usuário não informou, perguntar: *"Qual aula você deseja transcrever?"*
- **Apenas uma aula por execução.** Se múltiplas forem solicitadas, processar somente a primeira e avisar.

**Identificação da fonte** (buscar na pasta `aulas/aula-XX/` nesta ordem de prioridade):
1. Pasta `capturas/` — transcrever todos os arquivos de imagem (`.png`, `.jpg`, `.jpeg`, `.webp`) e PDF (`.pdf`) dentro dela, em ordem alfabética/numérica
2. Arquivo `capturas.pdf` — se não houver pasta `capturas/`
3. Nenhum encontrado → informar o usuário e encerrar

---

#### Tratamento de Elementos Visuais

Ao encontrar diagramas, desenhos ou qualquer elemento visual em materiais manuscritos, verificar se o `CLAUDE.md` da disciplina define como tratá-los. Se **não houver instrução específica**, perguntar ao usuário **uma única vez** e armazenar em `{{TRATAMENTO_VISUAIS_MANUSCRITOS}}`:

```
"Como devo tratar diagramas, desenhos e outros elementos visuais
encontrados nos materiais manuscritos?"

A) 📝 Descrição textual detalhada
      Descrevo o conteúdo visual em itálico no corpo do texto.

B) 🎨 Prompt para geração de imagem por IA
      Gero um bloco de prompt detalhado em `conteudos/prompts/N-nome-topico.md`
      para geração posterior. No ponto do texto, uso referência:
      ![descrição](caminho/para/imagem.png)

C) 📐 Diagrama/notação da área de conhecimento
      Uso a ferramenta padrão da área quando aplicável
      (ex: Mermaid para fluxos, notação musical, circuito elétrico,
      estrutura química, diagrama UML, etc.)

D) 🔀 Combinação: descrição + recurso técnico
      Descrevo textualmente E gero o prompt/diagrama correspondente.

Esta configuração vale para todas as aulas transcritas na sequência,
sem perguntar novamente — salvo instrução explícita do usuário.
```

---

#### ETAPA 1 — Transcrição

**Passo 1 — Leitura do material**

Ler todos os arquivos identificados (PDF página a página, imagens uma a uma). Cada página/imagem é tratada como uma foto ou digitalização de um segmento do quadro/documento.

**Passo 2 — Análise de ordem e completude**

Antes de transcrever, avaliar criticamente a sequência:

| Situação | Ação |
|----------|------|
| Ordem das páginas inconsistente | Reordenar + avisar: `⚠️ Reordenação: páginas X e Y foram invertidas` |
| Página ilegível ou cortada de forma essencial | Ignorar + avisar: `⚠️ Página X não transcrita: [motivo]` |
| Duas páginas com o mesmo conteúdo (duplicata) | Usar a com mais informação + avisar: `ℹ️ Página X ignorada: duplicata de Y` |
| Duas páginas com partes complementares do mesmo quadro | Fundir em uma seção + avisar: `ℹ️ Páginas X e Y fundidas: complementares` |
| Texto cortado entre páginas | Marcar `[continua...]` no final e `[...continuação]` no início da seguinte |

**Passo 3 — Transcrição página a página**

- Reproduzir fielmente o texto manuscrito
- Converter sublinhados para **negrito**
- Fórmulas e notações matemáticas: usar LaTeX inline `$...$` ou display `$$...$$`
- Preservar a notação original; corrigir apenas na Etapa 3

Para cada elemento visual encontrado, aplicar `{{TRATAMENTO_VISUAIS_MANUSCRITOS}}`:
- No ponto do corpo, inserir descrição e/ou referência de imagem
- Se opção B ou D: salvar os prompts em `conteudos/prompts/N-nome-topico.md` (arquivo separado, **nunca** no arquivo de conteúdo), numerados de 01 em diante — a pasta `conteudos/prompts/` é ignorada na exportação para o Notion

**Passo 4 — Geração do arquivo**

Criar (ou sobrescrever) `aulas/aula-XX/{{ARQUIVO_TRANSCRICAO}}` com a estrutura:

```markdown
# Transcrição — Aula XX

> 📅 **Data de transcrição:** DD/MM/AAAA
> 📄 **Fonte:** [capturas.pdf (N páginas) | pasta capturas/ (N arquivos: lista dos nomes)]
> ⚠️ **Avisos:** [reordenações / páginas ignoradas / fusões — ou "Nenhum"]

---

## Página 1

[transcrição]

---

## Página 2

[transcrição]

---

[...]

---

```

**Arquivo separado de prompts** (apenas se `{{TRATAMENTO_VISUAIS_MANUSCRITOS}}` == B ou D):

Criar `conteudos/prompts/N-nome-topico.md`:
```markdown
## 🎨 Prompts para Geração de Imagens

[prompts numerados de 01 em diante]
```

---

#### ETAPA 2 — Verificação de Inconsistências

Após transcrever, analisar o conteúdo e verificar:

1. **Inconsistências lógicas/matemáticas** — definições contraditórias, afirmações falsas
2. **Inconsistências de nomenclatura** — mesmo símbolo usado para objetos diferentes sem aviso
3. **Inconsistências nos exemplos** — valores, contagens ou resultados que não fecham
4. **Erros de escrita** — negações trocadas, palavras que invertem o sentido correto

Apresentar resultados em tabela:

| # | Página | Problema encontrado | Gravidade |
|---|--------|---------------------|-----------|
| 1 | X | [descrição] | Alta / Média / Baixa |

---

#### ETAPA 3 — Versão Corrigida

Reescrever o conteúdo com correções aplicadas:

- Marcar cada correção com ✏️ e nota explicativa
- Usar ~~tachado~~ para mostrar o que foi removido/corrigido
- Renomear objetos conflitantes (ex: segundo G → G') com nota
- Manter estilo e estrutura do original — apenas corrigir, não reescrever

---

#### Relatório e Revisão

Reportar ao usuário:

```
✅ Transcrição concluída: aulas/aula-XX/{{ARQUIVO_TRANSCRICAO}}
📄 Páginas processadas: N de M
⚠️ Avisos: [reordenações / páginas ignoradas / fusões — ou "Nenhum"]
🔍 Inconsistências encontradas: N
✏️ Correções aplicadas: N
```

Em seguida, perguntar: *"Deseja fazer alguma alteração na transcrição?"*
- Se **sim**: aplicar as alterações e perguntar novamente até o usuário confirmar.
- Se **não**: encerrar o procedimento.
