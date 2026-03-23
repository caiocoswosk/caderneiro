<!-- modelo: COMPLEXO -->
# Procedimento de Geração

### 🔧 Etapas para Gerar Arquivos de Contexto + instrucoes/

Quando um usuário completar o questionário, gerar **um conjunto de arquivos** conforme a ferramenta escolhida (`CLAUDE.md`, `AGENTS.md`, `opencode.json`) + `instrucoes/`:

1. **Coletar todas as variáveis** — consultar também `instrucoes/modelos.md` para os níveis de modelo por operação
2. **Selecionar template base** (Técnico/Teórico/Híbrido) — consultar `instrucoes/templates-base.md`
3. **Aplicar módulos opcionais** (código, diagramas, exercícios, transcrição, etc.) — consultar `instrucoes/modulos.md`
4. **Aplicar adaptador de plataforma** (Notion/Obsidian/GitHub/LaTeX) — consultar `instrucoes/adaptadores-plataforma.md`
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

   **`instrucoes/gerar-imagens.md`** (sempre gerado):
   - Regras para grafos (prompt destacado), flowcharts (Mermaid) e estruturas de dados
   - Paleta de cores, padrões visuais e estrutura de diretórios de imagens
   - Instruções para uso do script `gerar-imagens.py`

   **`instrucoes/exportar-conteudo.md`** (sempre gerado):
   - Verificação de `exportar.json` e setup lazy por plataforma
   - Procedimento de exportação para Notion, Obsidian, PDF e GitHub

   **Hints de modelo em cada arquivo de operação gerado:**
   Inserir `<!-- modelo: NIVEL -->` na **primeira linha** de cada arquivo de instrução, conforme a tabela em `instrucoes/modelos.md`:
   - `transcrever-aula.md` → `<!-- modelo: MEDIO -->`
   - `processar-aula.md` → `<!-- modelo: COMPLEXO -->`
   - `gerar-imagens.md` → `<!-- modelo: SIMPLES -->`
   - `exportar-conteudo.md` → `<!-- modelo: MEDIO -->`

9. **Criar skills individuais** — gerar comandos em `.claude/commands/` e `.opencode/commands/` (conforme `{{FERRAMENTA}}`):

   **Menu (`menu.md`)** — ambas ferramentas:
   ```markdown
   Apresente ao usuário o menu de operações do caderno usando AskUserQuestion:

   Q: "Qual operação deseja realizar?"
      A) 📝 Transcrever aula → execute /transcrever-aula
      B) ⚙️ Processar aula → execute /processar-aula
      C) 🖼️ Gerar imagens → execute /gerar-imagens
      D) 📤 Exportar conteúdo → execute /exportar-conteudo

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

   **Fluxos interativos de cada operação do caderno:**

   **D) Transcrever aula:**
   - Perguntar qual aula (texto livre)
   - Se `{{TRATAMENTO_VISUAIS_MANUSCRITOS}}` não definido → AskUserQuestion:
     ```
     Q: "Tratamento de elementos visuais nos manuscritos:"
        A) 📝 Descrição textual detalhada
        B) 🎨 Prompt para geração de imagem por IA
        C) 📐 Diagrama/notação da área (Mermaid, UML…)
        D) 🔀 Combinação: descrição + recurso técnico
     ```
   - Ao final → AskUserQuestion:
     ```
     Q: "Deseja fazer alguma alteração na transcrição?"
        A) ✅ Não — transcrição aprovada
        B) 🔧 Sim — informar as alterações
     ```

   **E) Processar aula:**
   - Perguntar qual aula (texto livre)
   - Ler os materiais da aula e inferir automaticamente o tópico comparando com `conteudos/`
   - Se identificado com confiança: processar diretamente sem perguntar
   - Se não identificado (ambíguo ou novo) → AskUserQuestion:
     ```
     Q: "Não consegui identificar o tópico. Qual arquivo recebe o conteúdo?"
        [listar arquivos em conteudos/ — até 4 opções]
        (se >4 ou tópico novo: texto livre com nome do arquivo)
     ```

   **F) Gerar imagens:**
   - AskUserQuestion:
     ```
     Q: "Escopo de geração:"
        A) 🖼️ Todas as pendentes — processar todos os prompts
        B) 📄 Apenas um arquivo — informar qual
     ```

   **G) Exportar conteúdo:**
   - Se `exportar.json` existe → AskUserQuestion:
     ```
     Q: "Confirmar exportação para [PLATAFORMA]?"
        A) ✅ Sim — exportar agora
        B) 🔧 Mudar plataforma — reconfigurar exportar.json
     ```
   - Se `exportar.json` não existe → AskUserQuestion:
     ```
     Q: "Para qual plataforma exportar?"
        A) 📘 Notion
        B) 📝 Obsidian
        C) 📄 PDF
        D) 🐙 GitHub / GitHub Pages
     ```

10. **Substituir todas as variáveis** em todos os arquivos gerados
11. **Validar com checklist** (ver abaixo)
12. **Apresentar ao usuário** a lista de arquivos gerados

---

## Referência: Exportar Conteúdo

Sincroniza os arquivos de `conteudos/` + imagens com a plataforma de estudo escolhida. A configuração é feita uma única vez por caderno e salva em `exportar.json`.

**Passo 1 — Verificar configuração**

Checar se `exportar.json` existe na raiz do caderno. Se não existir, perguntar:

```
"Para qual plataforma deseja exportar o conteúdo?"

A) Notion
B) Obsidian
C) PDF
D) GitHub / GitHub Pages
```

Exibir o tutorial de setup da plataforma escolhida (ver abaixo) e, ao final, salvar `exportar.json`.

**`exportar.json` (salvo na raiz do caderno, nunca versionado):**
```json
{
  "plataforma": "NOTION",
  "notion": {
    "page_id": "ID_DA_PAGINA_PAI",
    "token_env": "NOTION_TOKEN"
  }
}
```
> ⚠️ Adicionar `exportar.json` e `.env` ao `.gitignore` do caderno — contêm tokens sensíveis.

---

**Passo 2 — Executar exportação**

#### A) Notion

> **Dependências:** `notion-md-sync` (go-notion-md-sync) + `instrucoes/scripts/push_notion.py` (gerado no setup).

**A.1 — Primeiro uso: setup do notion-md-sync**

Antes de rodar qualquer comando, perguntar ao usuário:

```
"Preciso de duas informações para configurar a exportação para o Notion:

1. Seu Internal Integration Token (obtido em https://www.notion.so/profile/integrations)
   Exemplo: ntn_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

2. O ID da página pai no Notion onde o conteúdo será publicado
   (são os 32 caracteres após o último "/" na URL da página)
   Exemplo: 3258a0cf609d80479960f7e17498cdd7"
```

Com os dados em mãos, pedir para o usuário rodar:

```
! cd <caminho-do-caderno> && notion-md-sync init
```

⚠️ **Atenção ao token durante o init:** O Notion gera tokens com prefixo `ntn_`, mas o `notion-md-sync` só aceita `secret_`. Durante o `init`, orientar o usuário a digitar o token com o prefixo trocado:

- Token original: `ntn_XXXXXXXXXX...`
- Token a digitar no init: `secret_XXXXXXXXXX...` ← só troca o prefixo, o resto é igual

Quando o init perguntar **"Markdown directory"**, responder: `conteudos`

Após o init, **corrigir o `.env`** trocando `secret_` de volta para `ntn_`:
```
NOTION_MD_SYNC_NOTION_TOKEN=ntn_XXXXXXXXXX...
```

**A.2 — Upload das imagens**

Para cada arquivo em `conteudos/imagens/`, fazer upload via Notion File Upload API (2 passos):

```
# Passo 1 — criar objeto de upload (headers: Authorization + Notion-Version + Content-Type: application/json):
POST https://api.notion.com/v1/file_uploads
Body: {"filename": "nome.png", "content_type": "image/png"}
Resposta: {"id": "...", "upload_url": "https://api.notion.com/v1/file_uploads/{id}/send"}

# Passo 2 — enviar o arquivo para a upload_url retornada
# Headers: Authorization + Notion-Version (sem Content-Type — requests seta multipart automaticamente)
POST <upload_url>
Form-data: file=@caminho/imagem.png;type=image/png
```

> ⚠️ **Atenção no Passo 2:** a `upload_url` é um endpoint da própria Notion (`/v1/file_uploads/{id}/send`), não S3. Exige `Authorization` e `Notion-Version`, mas **não** `Content-Type` (conflita com o multipart gerado automaticamente).

Salvar o mapeamento `nome_arquivo → file_upload_id` em `/tmp/img_notion_map.json`.

**A.3 — Push do conteúdo**

⚠️ **Não usar `notion-md-sync push` diretamente** — ele tem um bug onde envia blocos de tabela sem os filhos, causando erro 400 da API Notion. Usar o script customizado em `instrucoes/scripts/push_notion.py`.

```bash
source .env && export NOTION_MD_SYNC_NOTION_TOKEN
python3 instrucoes/scripts/push_notion.py
```

O script opera sobre **todos** os arquivos em `conteudos/` de uma vez, em ordem alfabética (= ordem numérica pelo prefixo dos arquivos), ignorando `welcome.md` (arquivo residual do `notion-md-sync`):

1. **Arquiva** todas as páginas existentes (`notion_id` no frontmatter) via `PATCH /pages/{id} {"archived": true}`
2. **Recria** cada página em ordem, garantindo a sequência correta no Notion
3. **Remove o `# H1`** do corpo antes de converter — ele já é o título da página, não deve aparecer duplicado
4. **Extrai o emoji do título** (se houver) — remove do texto do título e define como ícone da página via `"icon": {"type": "emoji", "emoji": "📊"}` na criação. O título enviado ao Notion fica limpo, sem emoji.
5. Envia os blocos em chunks de 100 e salva o novo `notion_id` no frontmatter de cada arquivo

> O emoji no início do título (ex: `# 📊 Grafos`) é automaticamente extraído: o título da página no Notion recebe apenas o texto, e o emoji vira o ícone da página.

> O `notion_id` muda a cada exportação (página nova a cada vez). Isso é esperado e transparente.

> **Raiz do bug:** A API Notion exige que blocos aninhados coloquem seus filhos **dentro do objeto do tipo**, não na raiz. Isso afeta `table` (linhas) e `toggle` (conteúdo): use `table.children` e `toggle.children`. O `notion-md-sync` coloca no nível errado em ambos os casos.

**A.4 — Atualizações subsequentes**

O mesmo comando re-exporta tudo do zero (arquiva as antigas e recria em ordem):

```bash
source .env && export NOTION_MD_SYNC_NOTION_TOKEN
python3 instrucoes/scripts/push_notion.py
```

**Tutorial de setup Notion (primeira vez):**
```
1. Acesse https://www.notion.so/profile/integrations
2. Clique em "New integration" → nomeie (ex: "caderneiro")
3. Copie o "Internal Integration Token" (começa com ntn_)
4. Abra a página do Notion onde o conteúdo será publicado
5. Clique em "..." → "Connect to" → selecione sua integration
6. Copie o ID da página da URL (32 caracteres após o último "/")
7. Instale go-notion-md-sync: https://github.com/byvfx/go-notion-md-sync
8. Informe token e page_id ao agente ANTES de rodar qualquer comando
```

---

#### B) Obsidian

```bash
cp -r conteudos/* {{CAMINHO_VAULT}}/
```

**Tutorial de setup Obsidian:**
```
1. Abra o Obsidian e vá em Configurações → Sobre
2. O caminho da vault aparece em "Vault path"
3. Informe este caminho ao agente para salvar em exportar.json
```

---

#### C) PDF (pandoc)

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

#### D) GitHub / GitHub Pages

```bash
git add conteudos/
git commit -m "conteúdo: sincronizar [$(date +%Y-%m-%d)]"
git push
```

**Tutorial de setup GitHub:**
```
1. Crie um repositório privado no GitHub para o caderno
2. Na pasta do caderno: git init && git remote add origin URL_DO_REPO
3. Configure autenticação (SSH key ou token)
4. Informe a URL do remote ao agente para salvar em exportar.json
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
