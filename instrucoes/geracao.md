<!-- modelo: COMPLEXO -->
# Procedimento de Geração

### 🔧 Etapas para Gerar Arquivos de Contexto + instrucoes/

Quando um usuário completar o questionário, gerar **um conjunto de arquivos** conforme a ferramenta escolhida (`CLAUDE.md`, `AGENTS.md`, `opencode.json`) + `instrucoes/`:

1. **Coletar todas as variáveis** — consultar também `instrucoes/modelos.md` para os níveis de modelo por operação
2. **Selecionar template base** (Técnico/Teórico/Híbrido) — consultar `instrucoes/templates-base.md`
3. **Aplicar módulos opcionais** (código, diagramas, exercícios, transcrição, etc.) — consultar `instrucoes/modulos.md`
4. **Aplicar adaptador de plataforma** (Notion/Nenhuma) — consultar `instrucoes/adaptadores-plataforma.md`
5. **Personalizar estilos** (tom, emojis, detalhamento)
6. **Adaptar ao público-alvo**
7. **Definir estratégia de arquivos de saída** (todos ficam em `conteudos/`):
   - Se `{{EMENTA}}` foi fornecida: um arquivo por tópico do Conteúdo Programático
     → Ao criar os arquivos, escolher um emoji representativo para cada tópico e incluir
       no título H1: `# 📊 Nome do Tópico`. O emoji deve refletir o conteúdo central
       (ex: 📊 análise/dados, 🔗 grafos/redes, ⚙️ algoritmos, 🔍 busca, 🗂️ estruturas).
   - Se não foi fornecida: um arquivo por aula
8. **Gerar os arquivos de contexto** conforme `{{FERRAMENTA}}`:

   **`CLAUDE.md` (lean, ≤ 100 linhas)** — se `{{FERRAMENTA}} == CLAUDE_CODE` ou `AMBAS`:
   - Contexto da disciplina (nome, professor, instituição, tipo, linguagens, público)
   - Estrutura de arquivos + mapeamento tópico→arquivo
   - Tabela de operações disponíveis → caminhos em `instrucoes/`
   - Referência a `instrucoes/_padroes.md`
   - Instrução on-demand: "Para cada operação, leia o arquivo correspondente em `instrucoes/`"

   **`AGENTS.md`** — se `{{FERRAMENTA}} == OPENCODE` ou `AMBAS`:
   - Conteúdo idêntico ao `CLAUDE.md` acima (mesma estrutura, mesmas instruções)

   **`opencode.json`** — se `{{FERRAMENTA}} == OPENCODE` ou `AMBAS`:
   ```json
   {
     "instructions": ["instrucoes/_padroes.md"]
   }
   ```
   > Apenas `_padroes.md` é carregado automaticamente pelo OpenCode. Os arquivos de operação permanecem on-demand via instrução no `AGENTS.md`/`CLAUDE.md`.

   **`instrucoes/_padroes.md`:**
   - Padrões de formatação (do template base selecionado)
   - Regras de consistência (nomenclatura, ordem de seções)
   - Sistema de exercícios (se módulo ativo)
   - Glossário (se módulo ativo)
   - Checklist de qualidade
   - Seção **Modelos Recomendados** — copiar a tabela de tiers de `instrucoes/modelos.md` do caderneiro, incluindo apenas as colunas relevantes à `{{FERRAMENTA}}` (Claude Code e/ou OpenCode). Incluir também as regras de comportamento do agente.

   **`instrucoes/transcrever-aula.md`** (se `{{MODULO_TRANSCRICAO}} == true`):
   - Procedimento em 3 etapas
   - Configuração de `{{TRATAMENTO_VISUAIS_MANUSCRITOS}}`

   **`instrucoes/processar-aula.md`** (sempre gerado):
   - Fluxo completo de processamento de aula
   - Usa qualquer material em `aulas/aula-XX/`: `transcricao.md`, PDFs, código, imagens ou combinação
   - Análise de código (se módulo ativo)
   - Diagramas (se módulo ativo)
   - Emoji do conteúdo: ao criar ou atualizar o título H1 de um arquivo de conteúdo, escolher
     um emoji representativo para o tema e incluir à esquerda (`# 🔍 Nome do Tópico`). Se o
     arquivo já tem emoji e um mais adequado for identificado ao longo das aulas, atualizar.
   - **Metadata por aula:** cada seção `## Aula XX` deve ter, logo abaixo do título:
     ```
     📅 Data de Adição: DD/MM/AAAA
     ⏱️ Tempo Estimado de Estudo: Xh Ymin
     📊 Dificuldade: Básica/Intermediária/Avançada
     ```
     Formato de tempo obrigatório: `Xh Ymin` (ex: `1h 30min`, `45min`, `2h`). Nunca usar decimais (`1,5 horas`) nem a palavra "horas"/"minutos" por extenso.
   - **Introdução do arquivo de conteúdo:** entre o H1 e a primeira aula, manter um bloco de introdução com tempo total e sumário:
     ```
     > ⏱️ **Tempo total de estudo:** Xh Ymin (N aulas)

     ## Sumário

     | # | Aula | Tempo | Dificuldade |
     |---|------|-------|-------------|
     | XX | [Título](#aula-xx-título) | Xh Ymin | Nível |
     ```
     - Se o arquivo é novo (primeira aula): criar a introdução com 1 linha no sumário
     - Se já existe: somar o tempo da nova aula ao total e adicionar linha ao sumário
     - Tempo total = soma dos tempos individuais de cada aula
   - **Atualizar `index.md`** ao final de cada processamento:
     1. Adicionar linha em "Registro de Aulas": `| aula-XX | YYYY-MM-DD | N. Nome do tópico |`
     2. Em "Estrutura de Tópicos", localizar o tópico e adicionar o número da aula em "Aulas Cobertas" (ex: `—` → `01`; `01` → `01, 02`)
     3. Se o tópico não existia (caderno sem ementa): inserir nova linha com emoji + nome + arquivo

   **`instrucoes/gerar-imagens.md`** (sempre gerado):
   - Regras para grafos (prompt destacado), flowcharts (Mermaid) e estruturas de dados
   - Paleta de cores, padrões visuais e estrutura de diretórios de imagens
   - Instruções para geração de imagens a partir dos prompts
   - Fontes de prompts: transcrição salva em `aulas/aula-XX/prompts/`; processamento salva em `conteudos/prompts/` — gerar-imagens lê de ambas; ambas ignoradas na exportação

   **`instrucoes/exportar-conteudo.md`** (sempre gerado):
   - Procedimento de sincronização com a plataforma de estudo e exportação como PDF

   **`instrucoes/revisar-conteudo.md`** (sempre gerado):
   - Verificação estrutural de todos os arquivos em `conteudos/` contra `instrucoes/_padroes.md`
   - **Passo 0:** listar arquivos `.md` em `conteudos/` (excluir subdiretório `prompts/`); encerrar se vazio
   - **Passo 1 — Verificação:** para cada arquivo, verificar os aspectos abaixo e registrar OK / DIVERGENTE:
     - (a) Bloco de introdução: callout `⏱️ Tempo total` + tabela Sumário `| # | Aula | Tempo | Dificuldade |` após o H1
     - (b) Metadata de aula: linhas `📅`/`⏱️`/`📊` em texto simples (não blockquote `>`); tempo no formato `Xh Ymin` (não decimal)
     - (c) Seções obrigatórias por aula: `### 📌 Objetivos`, seção de conceitos, `### 📝 TL;DR`, glossário em `<details>`
     - (d) Exercícios: 3 níveis (🟢🟡🔴) com soluções em `<details>` toggles
     - (e) Emoji no H1: título começa com emoji representativo
   - Verificar **todos** os aspectos de **todos** os arquivos antes de exibir relatório
   - **Passo 2 — Relatório:**
     ```
     🔍 Revisão de conteúdos — N arquivo(s) com divergências:
     | Arquivo | Status | Aulas divergentes | Resumo |
     ✅ OK: N | ⚠️ Divergentes: N
     ```
     Se nenhuma divergência: encerrar
   - **Passo 3 — Resolução:** avisar que re-processamento requer modelo COMPLEXO (sugerir troca antes de iniciar)
     - Se ≤ 3 arquivos divergentes → AskUserQuestion por arquivo: A) 🔄 Re-processar / B) 🔍 Ver detalhes / C) ❌ Manter
     - Se > 3 → AskUserQuestion global: A) 🔄 Re-processar todos / B) 🔍 Revisar um a um / C) ❌ Manter tudo
   - **Passo 4 — Re-processamento:** ler `index.md` → "Aulas Cobertas"; verificar materiais em `aulas/aula-XX/`; re-executar `instrucoes/processar-aula.md` para cada aula em ordem; avisar se materiais ausentes
   - **Passo 5 — Relatório final:** `🔄 Re-processados: N | ⏭️ Mantidos: N | ⚠️ Materiais ausentes: N`

   **`exportar.json`** (criado na raiz do caderno durante a geração):
   - Se `{{PLATAFORMA}} == NOTION`:
     ```json
     {
       "plataforma": "NOTION",
       "notion": {
         "page_id": "",
         "token_env": "NOTION_MD_SYNC_NOTION_TOKEN"
       }
     }
     ```
   - Se `{{PLATAFORMA}} == NENHUMA`:
     ```json
     {
       "plataforma": "NENHUMA"
     }
     ```
   `page_id` fica vazio e é preenchido no primeiro uso.
   > ⚠️ Adicionar `exportar.json` e `.env` ao `.gitignore` do caderno — podem conter tokens sensíveis.

   **`index.md` (raiz do caderno — copiar de `instrucoes/templates/index.md` e substituir variáveis):**
   - `{{CODIGO_DISCIPLINA}}`: código da disciplina se disponível; omitir a linha se não informado
   - `{{MODULOS_ATIVOS}}`: lista dos módulos habilitados (ex: código, exercícios, transcrição, diagramas)
   - `{{DATA_CRIACAO}}`: data atual no formato YYYY-MM-DD
   - `{{LINHAS_TOPICOS}}`:
     - Se `{{EMENTA}}` fornecida: uma linha por tópico — `| N | EMOJI Nome do Tópico | \`conteudos/N-nome.md\` | — |`
     - Se não fornecida: `| — | — | — | — |` (linha única indicando ausência de ementa)

   **`instrucoes/scripts/`** (copiar do caderneiro — não gerar):
   Copiar **todo o conteúdo** de `instrucoes/scripts/` do caderneiro para o caderno, recursivamente.
   Conteúdo atual:
   - `push_notion.py` — exporta `conteudos/` para o Notion (apenas se PLATAFORMA == NOTION)
   - `upload_images_notion.py` — faz upload de imagens (apenas se PLATAFORMA == NOTION)
   - `caderneiro_graph/` — pacote de grafo de conhecimento acadêmico (sempre)

   > Ao adicionar novos scripts/pacotes a `instrucoes/scripts/`, atualizar esta lista.
   > A consistência é verificada via `python3 instrucoes/scripts/caderneiro_graph/cli.py meta check`.

   **Hints de modelo em cada arquivo de operação gerado:**
   Inserir `<!-- modelo: NIVEL -->` na **primeira linha** de cada arquivo de instrução, conforme a tabela em `instrucoes/modelos.md`:
   - `transcrever-aula.md` → `<!-- modelo: MEDIO -->`
   - `processar-aula.md` → `<!-- modelo: COMPLEXO -->`
   - `gerar-imagens.md` → `<!-- modelo: SIMPLES -->`
   - `exportar-conteudo.md` → `<!-- modelo: MEDIO -->`
   - `revisar-conteudo.md` → `<!-- modelo: MEDIO -->`

9. **Criar skills individuais** — gerar comandos em `.claude/commands/` e `.opencode/commands/` (conforme `{{FERRAMENTA}}`):

   **Menu (`menu.md`)** — ambas ferramentas:

   Se `{{MODULO_TRANSCRICAO}} == true`:
   ```markdown
   Use AskUserQuestion com o texto exato abaixo (não adicione texto antes):

   Q: "Qual operação deseja realizar?"
      A) 📝 Transcrever aula → execute /transcrever-aula
      B) ⚙️ Processar aula → execute /processar-aula
      C) 🖼️ Gerar imagens → execute /gerar-imagens
      D) 📤 Exportar conteúdo → execute /exportar-conteudo
      E) 🔍 Revisar conteúdos → execute /revisar-conteudo

   Após a seleção, execute a skill correspondente.
   ```

   Se `{{MODULO_TRANSCRICAO}} == false`:
   ```markdown
   Use AskUserQuestion com o texto exato abaixo (não adicione texto antes):

   Q: "Qual operação deseja realizar?"
      A) ⚙️ Processar aula → execute /processar-aula
      B) 🖼️ Gerar imagens → execute /gerar-imagens
      C) 📤 Exportar conteúdo → execute /exportar-conteudo
      D) 🔍 Revisar conteúdos → execute /revisar-conteudo

   Após a seleção, execute a skill correspondente.
   ```

   **Skills individuais** — uma por operação:

   Claude Code (`.claude/commands/[operacao].md`):
   ```markdown
   Leia a primeira linha de `instrucoes/[operacao].md` para extrair o nível do modelo (`<!-- modelo: NIVEL -->`). Consulte `instrucoes/_padroes.md` (seção Modelos Recomendados) para verificar se o modelo ativo corresponde ao nível recomendado. Se o modelo ativo for **diferente** do recomendado, sugira a troca via `/model` e **pare — aguarde a decisão do usuário**: o usuário pode trocar o modelo ou confirmar para prosseguir com o modelo atual. Se compatível, prossiga sem comentários.

   Em seguida, leia `instrucoes/[operacao].md` por completo e execute a operação.
   ```

   OpenCode (`.opencode/commands/[operacao].md`):
   ```yaml
   ---
   description: [descrição curta da operação]
   ---
   Leia a primeira linha de `instrucoes/[operacao].md` para extrair o nível do modelo (`<!-- modelo: NIVEL -->`). Consulte `instrucoes/_padroes.md` (seção Modelos Recomendados) para verificar se o modelo ativo corresponde ao nível recomendado. Se o modelo ativo for **diferente** do recomendado, sugira a troca via `/models` e **pare — aguarde a decisão do usuário**: o usuário pode trocar o modelo ou confirmar para prosseguir com o modelo atual. Se compatível, prossiga sem comentários.

   Em seguida, leia `instrucoes/[operacao].md` por completo e execute a operação.
   ```

   Arquivos a gerar:
   - `menu.md` — menu interativo
   - `transcrever-aula.md` (se `{{MODULO_TRANSCRICAO}} == true`)
   - `processar-aula.md` (sempre)
   - `gerar-imagens.md` (sempre)
   - `exportar-conteudo.md` (sempre)
   - `revisar-conteudo.md` (sempre)

   **Fluxos interativos de cada operação do caderno:**

   **D) Transcrever aula:**
   - → Usar AskUserQuestion com o texto exato abaixo (não reformule):
     ```
     Q: "Qual aula deseja transcrever? (informe número ou nome do arquivo)"
     ```
   - Se `{{TRATAMENTO_VISUAIS_MANUSCRITOS}}` não definido → usar AskUserQuestion com o texto exato abaixo (não reformule):
     ```
     Q: "Tratamento de elementos visuais nos manuscritos:"
        A) 📝 Descrição textual detalhada
        B) 🎨 Prompt para geração de imagem por IA
        C) 📐 Diagrama/notação da área (Mermaid, UML…)
        D) 🔀 Combinação: descrição + recurso técnico
     ```
   - Ao final → usar AskUserQuestion com o texto exato abaixo (não reformule):
     ```
     Q: "Deseja fazer alguma alteração na transcrição?"
        A) ✅ Não — transcrição aprovada
        B) 🔧 Sim — informar as alterações
     ```

   **E) Processar aula:**
   - → Usar AskUserQuestion com o texto exato abaixo (não reformule):
     ```
     Q: "Qual aula deseja processar? (informe número ou nome do arquivo)"
     ```
   - Ler os materiais da aula e inferir automaticamente o tópico comparando com `conteudos/`
   - Se identificado com confiança: processar diretamente sem perguntar
   - Se não identificado (ambíguo ou novo) → usar AskUserQuestion com o texto exato abaixo (não reformule):
     ```
     Q: "Não consegui identificar o tópico. Qual arquivo recebe o conteúdo?"
        [listar arquivos em conteudos/ — até 4 opções]
        (se >4 ou tópico novo: texto livre com nome do arquivo)
     ```

   **F) Gerar imagens:**
   - → Usar AskUserQuestion com o texto exato abaixo (não reformule):
     ```
     Q: "Escopo de geração:"
        A) 🖼️ Todas as pendentes — processar todos os prompts
        B) 📄 Apenas um arquivo — informar qual
     ```

   **G) Exportar conteúdo:**
   - Se `{{PLATAFORMA}} == NENHUMA` → usar AskUserQuestion com o texto exato abaixo (não reformule):
     ```
     Q: "Como exportar?"
        A) 📄 Exportar como PDF — gerar PDFs via pandoc
     ```
   - Se `{{PLATAFORMA}} == NOTION` → usar AskUserQuestion com o texto exato abaixo (não reformule):
     ```
     Q: "Como exportar?"
        A) 📘 Sincronizar com Notion — enviar conteúdo para o Notion
        B) 📄 Exportar como PDF — gerar PDFs via pandoc
     ```

   **H) Revisar conteúdos:**
   - Verificar arquivos em `conteudos/` e reportar divergências (ver spec de `instrucoes/revisar-conteudo.md`)
   - Se o usuário optar por re-processar → sugerir troca para modelo COMPLEXO antes de iniciar

10. **Substituir todas as variáveis** em todos os arquivos gerados
11. **Validar com checklist** (ver abaixo)
12. **Apresentar ao usuário** a lista de arquivos gerados

---

## Referência: Exportar Conteúdo

Exporta o conteúdo de `conteudos/` para o Notion ou gera PDFs via pandoc.

**`exportar.json` (criado na raiz do caderno durante a geração, nunca versionado):**
```json
{
  "plataforma": "NOTION",
  "notion": {
    "page_id": "",
    "token_env": "NOTION_MD_SYNC_NOTION_TOKEN"
  }
}
```
> ⚠️ Adicionar `exportar.json` e `.env` ao `.gitignore` do caderno — contêm tokens sensíveis.

---

### Opção A — Sincronizar com Notion

> **Dependências:** `instrucoes/scripts/push_notion.py` e `instrucoes/scripts/upload_images_notion.py` (copiados do caderneiro durante a geração).

**Passo 1 — Verificar configuração**

Ler `exportar.json`. Se `notion.page_id` estiver vazio, executar o **fluxo de primeiro uso** abaixo. Caso contrário, ir direto para o Passo 2.

**Fluxo de primeiro uso:**

→ usar AskUserQuestion com o texto exato abaixo (não reformule):
```
Q: "Para configurar o Notion, você precisa de um Integration Token e de um Page ID. Como prefere prosseguir?"
   A) 📖 Ver tutorial de setup
   B) 🔑 Já tenho os dados — configurar agora
```

Se A (tutorial), exibir:
```
TUTORIAL DE SETUP DO NOTION:

1. Acesse https://www.notion.so/profile/integrations
2. Clique em "New integration" → nomeie (ex: "caderneiro")
3. Copie o "Internal Integration Token" (começa com ntn_)
4. Abra a página do Notion onde o conteúdo será publicado
5. Clique em "..." → "Connect to" → selecione sua integration
6. Copie o ID da página da URL (32 caracteres após o último "/")
```

Após o tutorial → usar AskUserQuestion com o texto exato abaixo (não reformule):
```
Q: "Pronto para informar as credenciais?"
   A) ✅ Sim — informar agora
```

Coletar credenciais (para A em qualquer caminho) — usar AskUserQuestion com o texto exato abaixo (não reformule):
```
Q: "Informe o Integration Token do Notion:"
   (começa com ntn_ — ex: ntn_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX)
```

→ usar AskUserQuestion com o texto exato abaixo (não reformule):
```
Q: "Informe o Page ID da página pai no Notion:"
   (32 caracteres após o último "/" na URL da página — ex: 3258a0cf609d80479960f7e17498cdd7)
```

Criar `.env` na raiz do caderno com o conteúdo:
```
NOTION_MD_SYNC_NOTION_TOKEN=ntn_XXXXXXXXXX
NOTION_MD_SYNC_NOTION_PARENT_PAGE_ID=page_id_aqui
```

Atualizar `exportar.json` com o page_id em `notion.page_id`.

**Passo 2 — Upload de imagens**

Verificar se `conteudos/imagens/` existe e contém arquivos.

Se sim → usar AskUserQuestion com o texto exato abaixo (não reformule):
```
Q: "Imagens detectadas em conteudos/imagens/. Como prosseguir?"
   A) ⬆️ Fazer upload das imagens (recomendado para imagens novas)
   B) ⏭️ Pular — exportar sem atualizar imagens
```

Se A, executar:
```bash
source .env && export NOTION_MD_SYNC_NOTION_TOKEN
python3 instrucoes/scripts/upload_images_notion.py
```

O script suporta `.png`, `.jpg`, `.jpeg`, `.webp` e `.gif`. Pula imagens já presentes no mapa e salva o resultado em `/tmp/img_notion_map.json` (`nome_arquivo → file_upload_id`).

**Passo 3 — Push do conteúdo**

```bash
source .env && export NOTION_MD_SYNC_NOTION_TOKEN
python3 instrucoes/scripts/push_notion.py
```

O script opera sobre **todos** os arquivos em `conteudos/` de uma vez, em ordem alfabética:

1. **Arquiva** todas as páginas existentes (`notion_id` no frontmatter) via `PATCH /pages/{id} {"archived": true}`
2. **Recria** cada página em ordem, garantindo a sequência correta no Notion
3. **Remove o `# H1`** do corpo — ele já é o título da página, não deve aparecer duplicado
4. **Extrai o emoji do título** — remove do texto e define como ícone da página. Título no Notion fica limpo.
5. Envia os blocos em chunks de 100 e salva o novo `notion_id` no frontmatter de cada arquivo

> O `notion_id` muda a cada exportação (página nova a cada vez). Isso é esperado e transparente.

---

### Opção B — Exportar como PDF

Disponível para qualquer plataforma (incluindo Nenhuma).

```bash
for f in conteudos/*.md; do
  pandoc "$f" -o "${f%.md}.pdf" --resource-path=conteudos/imagens
done
```

PDFs gerados na mesma pasta dos `.md` correspondentes.

**Tutorial de setup:**
```bash
# Ubuntu/Debian
sudo apt install pandoc

# macOS
brew install pandoc

# Verificar
pandoc --version
```

---

## Checklist de Qualidade

Ao gerar um CLAUDE.md, verificar:

#### Completude:
- [ ] Todas as seções obrigatórias presentes
- [ ] Módulos selecionados totalmente implementados
- [ ] Módulo de Consistência incluído (regras C1-C6) — ativado por padrão
- [ ] Exemplos apropriados ao tipo de curso
- [ ] Instruções claras e não ambíguas
- [ ] Hints `<!-- modelo: NIVEL -->` presentes na primeira linha de todos os arquivos de operação
- [ ] Seção "Modelos Recomendados" presente em `_padroes.md`

#### Consistência:
- [ ] Tom de linguagem uniforme
- [ ] Terminologia consistente
- [ ] Formatação da plataforma correta
- [ ] Nenhum `{{VAR}}` remanescente

#### Adequação:
- [ ] Template base apropriado
- [ ] Nível de detalhamento condiz com público
- [ ] Tipos de materiais cobertos
- [ ] Plataforma alvo com sintaxe correta

#### Usabilidade:
- [ ] Estrutura lógica e fácil navegar
- [ ] Exemplos suficientes
- [ ] Checklist de qualidade incluído
- [ ] Comandos úteis listados

#### Estrutura de Arquivos de Saída:
- [ ] Estratégia definida (por tópico se há programa, por aula se não há)
- [ ] Mapeamento tópico/aula → nome de arquivo incluído no CLAUDE.md
- [ ] Nomes de arquivo sem o conectivo "de"
