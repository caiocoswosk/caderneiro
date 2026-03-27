<!-- modelo: MEDIO -->
# Atualizar Caderno

Usar quando o caderneiro evoluiu (novos módulos, procedimentos revisados, padrões atualizados) e o usuário quer que o caderno existente reflita essas melhorias.

**Passo 0 — Identificar o caderno**

→ Usar AskUserQuestion com o texto exato abaixo (não reformule):
```
Q: "Qual caderno deseja atualizar?"
   [listar cadernos em cadernos/ como opções, se existirem]
   + opção: "Informar caminho externo"
```
Se "Informar caminho externo": perguntar o caminho como texto livre.

---

**Passo 1 — Inventariar o caderno**

Antes de comparar, extrair a configuração do caderno:

1. Ler `index.md` (seção "Configuração") — ou, se ausente, ler `CLAUDE.md` / `AGENTS.md`
2. Identificar:
   - **FERRAMENTA:** inferir pela presença de `CLAUDE.md` (CLAUDE_CODE), `AGENTS.md` (OPENCODE), ou ambos (AMBAS)
   - **PLATAFORMA:** ler `exportar.json` → campo `plataforma` (NOTION / NENHUMA)
   - **Módulos ativos:** ler `index.md` campo "Módulos ativos", ou inferir pela presença de `instrucoes/transcrever-aula.md` (transcrição)
   - **Tipo de disciplina:** inferir do campo "Tipo" em `index.md` ou `CLAUDE.md` (Técnico / Teórico / Híbrido)

---

**Passo 2 — Verificação completa**

Iterar cada linha do **Mapa de Referência** abaixo. Para cada linha cuja **Condição** é atendida:

1. Verificar se o arquivo **existe** no caderno
   - Se ausente → registrar como `AUSENTE`
2. Se existe, **ler a referência indicada** no caderneiro (`instrucoes/` do caderneiro, não do caderno)
3. **Ler o arquivo do caderno** e comparar cada aspecto listado
   - Se algum aspecto diverge → registrar como `DIVERGENTE` com resumo
   - Se todos os aspectos estão alinhados → registrar como `OK`

> **Regra:** comparar **todos** os aspectos de **todas** as linhas antes de apresentar resultados. Não perguntar nada ao usuário neste passo.

### Mapa de Referência

| # | Arquivo no caderno | Condição | Referência no caderneiro | Aspectos a verificar |
|---|-------------------|----------|--------------------------|---------------------|
| 1 | `CLAUDE.md` | FERRAMENTA == CLAUDE_CODE ou AMBAS | `geracao.md` Etapa 8, seção "CLAUDE.md" | (a) Tabela de operações com caminhos corretos para `instrucoes/`; (b) Referência a `instrucoes/_padroes.md`; (c) Instrução on-demand presente |
| 2 | `AGENTS.md` | FERRAMENTA == OPENCODE ou AMBAS | `geracao.md` Etapa 8, seção "AGENTS.md" | Conteúdo idêntico ao CLAUDE.md |
| 3 | `opencode.json` | FERRAMENTA == OPENCODE ou AMBAS | `geracao.md` Etapa 8, seção "opencode.json" | (a) Estrutura JSON válida; (b) Campo `instructions` contém `_padroes.md` |
| 4 | `index.md` | sempre | `instrucoes/templates/index.md` do caderneiro | (a) Seções obrigatórias: Configuração, Estrutura de Tópicos, Registro de Aulas; (b) Tabela de tópicos coerente com arquivos em `conteudos/` |
| 5 | `instrucoes/_padroes.md` | sempre | `geracao.md` Etapa 8 "_padroes.md" + `templates-base.md` (template do tipo da disciplina) | (a) Seções do template base correspondentes ao tipo; (b) Módulos ativos refletidos; (c) Seção "Modelos Recomendados" presente; (d) Checklist de qualidade presente |
| 6 | `instrucoes/processar-aula.md` | sempre | `geracao.md` Etapa 8 "processar-aula.md" | (a) `<!-- modelo: COMPLEXO -->` na 1ª linha; (b) Metadata por aula (📅 Data, ⏱️ Tempo, 📊 Dificuldade); (c) Introdução do arquivo de conteúdo (tempo total + sumário); (d) Atualização de `index.md` ao final; (e) Módulos ativos refletidos |
| 7 | `instrucoes/gerar-imagens.md` | sempre | `geracao.md` Etapa 8 "gerar-imagens.md" | (a) `<!-- modelo: SIMPLES -->` na 1ª linha; (b) Fontes de prompts: `aulas/aula-XX/prompts/` e `conteudos/prompts/`; (c) Regras por tipo de diagrama (grafos, flowcharts, estruturas) |
| 8 | `instrucoes/exportar-conteudo.md` | sempre | `geracao.md` Etapa 8 "exportar-conteudo.md" + seção "Referência: Exportar Conteúdo" | (a) `<!-- modelo: MEDIO -->` na 1ª linha; (b) Opções corretas para a PLATAFORMA; (c) Fluxo Notion completo se aplicável (setup, upload imagens, push via script) |
| 9 | `instrucoes/transcrever-aula.md` | módulo transcrição ativo | `geracao.md` Etapa 8 "transcrever-aula.md" | (a) `<!-- modelo: MEDIO -->` na 1ª linha; (b) 3 etapas presentes (transcrever → verificar → corrigir); (c) Configuração de tratamento de visuais |
| 10 | `.claude/commands/*.md` | FERRAMENTA == CLAUDE_CODE ou AMBAS | `geracao.md` Etapa 9, seção "Skills individuais" | (a) Todos os commands esperados existem (menu + um por operação ativa); (b) Conteúdo de cada command segue template (verificação de modelo usa "diferente", leitura do arquivo de operação); (c) Menu lista todas as operações ativas |
| 11 | `.opencode/commands/*.md` | FERRAMENTA == OPENCODE ou AMBAS | `geracao.md` Etapa 9, seção "Skills individuais" | Idem linha 10, com frontmatter `description` e `/models` em vez de `/model` |
| 12 | `instrucoes/scripts/` | sempre | `instrucoes/scripts/` do caderneiro (comparar recursivamente) | (a) Listar recursivamente `instrucoes/scripts/` do caderneiro; (b) Para cada arquivo/subdiretório: verificar existência no caderno e conteúdo idêntico (hash); (c) Arquivos exclusivos do Notion (`push_notion.py`, `upload_images_notion.py`): ausência OK se PLATAFORMA != NOTION; (d) Demais arquivos/pacotes: ausência = AUSENTE |
| 13 | `exportar.json` | sempre | `geracao.md` Etapa 8 "exportar.json" | (a) Existe; (b) Estrutura corresponde à PLATAFORMA configurada |
| 14 | `instrucoes/revisar-conteudo.md` | sempre | `geracao.md` Etapa 8 "revisar-conteudo.md" | (a) `<!-- modelo: MEDIO -->` na 1ª linha; (b) 5 aspectos de verificação presentes (intro, metadata, seções, exercícios, emoji); (c) fluxo de resolução com AskUserQuestion; (d) nota sobre troca para COMPLEXO no re-processamento |
| 15 | — (meta-verificação) | sempre | `caderneiro_graph meta check` | Executar `python3 instrucoes/scripts/caderneiro_graph/cli.py --caderno . meta check` na raiz do caderneiro. Se reportar gaps (artefatos sem cobertura no Mapa, scripts não listados em geracao.md), registrar como `AVISO: Mapa de Referência desatualizado` com detalhes do gap |

---

**Passo 2.5 — Detecção de arquivos obsoletos**

Identificar arquivos presentes no caderno que não pertencem à estrutura esperada.

**Conjunto de arquivos esperados** (baseado na configuração do Passo 1):

- Raiz: `CLAUDE.md`, `AGENTS.md`, `opencode.json`, `index.md`, `exportar.json`, `.gitignore`, `README.md`
- Se PLATAFORMA == NOTION: adicionar `.env`, `.env.example`
- Diretórios a ignorar: `aulas/`, `conteudos/`, `.git/`, `.claude/`, `.opencode/`
- `instrucoes/`: conjunto do Mapa de Referência (Passo 2) + `scripts/`

**Procedimento de listagem:**

1. Listar **todos** os arquivos e diretórios na raiz do caderno, **incluindo ocultos** (prefixo `.`)
2. Listar **todos** os arquivos dentro de `instrucoes/` (exceto `scripts/`)
3. Subtrair do resultado: arquivos esperados (acima), diretórios a ignorar (acima), e arquivos do Mapa de Referência dentro de `instrucoes/`
4. O que restar são candidatos a "extra" — avaliar cada um abaixo

**Para cada arquivo ou diretório extra encontrado:**

1. Buscar referências nos arquivos de instrução do caderno: `CLAUDE.md`, `AGENTS.md`, `instrucoes/*.md`, `exportar.json`, `index.md`
2. Classificar:
   - **Não referenciado em nenhum arquivo** → `OBSOLETO`
   - **Referenciado apenas em arquivo(s) marcado(s) como DIVERGENTE no Passo 2** → `POTENCIALMENTE OBSOLETO` — registrar nota: "referenciado em [arquivo], pendente de atualização"
   - **Referenciado em arquivo OK** → em uso legítimo, ignorar
3. Registrar apenas OBSOLETO e POTENCIALMENTE OBSOLETO para o relatório

**Padrões conhecidos para contextualizar** (incluir no resumo quando identificado):
- `config.yaml` → configuração do notion-md-sync (substituído pelos scripts Python em `instrucoes/scripts/`)
- `.notion-sync/` → diretório de cache do notion-md-sync (gerado automaticamente, não versionável)
- `requirements.txt` fora de `instrucoes/scripts/` → dependências pip soltas
- `conteudos/welcome.md` → arquivo residual do notion-md-sync (gerado automaticamente na primeira sincronização)

> **Regra:** não perguntar nada ao usuário neste passo.

---

**Passo 3 — Relatório de divergências**

Apresentar **todas** as divergências encontradas em uma única tabela, seguida dos arquivos obsoletos:

```
🔍 Verificação concluída — N divergência(s) encontrada(s):

| # | Arquivo | Status | Resumo |
|---|---------|--------|--------|
| 1 | instrucoes/processar-aula.md | DIVERGENTE | Falta metadata por aula e sumário |
| 4 | index.md | OK | — |
| 12 | instrucoes/scripts/*.py | AUSENTE | Scripts de exportação não encontrados |
[...]

✅ Arquivos OK: N
⚠️ Divergentes: N
❌ Ausentes: N

❗ Arquivos obsoletos: N
| Arquivo | Status | Resumo |
|---------|--------|--------|
| config.yaml | POTENCIALMENTE OBSOLETO | Referenciado em instrucoes/exportar-conteudo.md (DIVERGENTE); notion-md-sync substituído por scripts Python |
| .notion-sync/ | OBSOLETO | Diretório de cache do notion-md-sync; não referenciado em nenhum arquivo de instrução |
```

Se **nenhuma divergência e nenhum obsoleto**: exibir relatório final e encerrar.

---

**Passo 4 — Aplicar atualizações**

**Se ≤ 5 divergências**, perguntar por arquivo — → Usar AskUserQuestion:
```
Q: "[arquivo] — [status]: [resumo]. O que fazer?"
   A) ✅ Atualizar — reescrever preservando personalizações da disciplina
   B) 🔍 Ver detalhes — mostrar divergências antes de decidir
   C) ❌ Manter — preservar versão atual
```

- Se **Ver detalhes**: exibir detalhes em texto e usar AskUserQuestion novamente com A) Atualizar / C) Manter

**Se > 5 divergências**, → Usar AskUserQuestion:
```
Q: "N divergências encontradas. Como deseja prosseguir?"
   A) ✅ Atualizar todas — reescrever preservando personalizações
   B) 🔍 Revisar uma a uma — decidir por arquivo
   C) ❌ Manter tudo — preservar versão atual
```

- Se **Revisar uma a uma**: seguir o fluxo de ≤ 5 para cada divergência

**Ao atualizar um arquivo:** ler a referência indicada no Mapa de Referência e reescrever o arquivo do caderno conforme a especificação atual, preservando personalizações da disciplina (nome, professor, variáveis, módulos, paleta de cores, etc.).

**Arquivos obsoletos** (após resolver as divergências dos 14 arquivos):

Para cada arquivo `OBSOLETO` ou `POTENCIALMENTE OBSOLETO`, → Usar AskUserQuestion:
```
Q: "[arquivo] — [status]: [resumo]. O que fazer?"
   A) 🗑️ Remover — deletar o arquivo/diretório
   B) ❌ Manter — preservar (pode ter uso não mapeado)
```

---

**Passo 5 — Relatório final**

```
✅ Atualização concluída
📄 Arquivos atualizados: N
⏭️ Arquivos mantidos: N
❌ Arquivos ausentes não criados: N
🗑️ Arquivos obsoletos removidos: N
```
