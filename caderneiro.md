# 🗒️ Caderneiro

## ⚡ Operações Disponíveis

### O que é um caderno

Um **caderno** é o repositório de conhecimento de uma disciplina. Ele centraliza tudo em um só lugar: as instruções de como o agente deve operar, os conteúdos gerados a partir das aulas e os materiais brutos de entrada.

**Objetivo:** transformar materiais de aula dispersos (PDFs, fotos de quadro, código) em documentação estruturada, navegável e autoexplicativa — para que qualquer pessoa possa aprender o conteúdo sem ter assistido às aulas.

**Estrutura de um caderno:**
```
nome-da-disciplina/
├── CLAUDE.md          ← contexto + mapa de operações (Claude Code)
├── AGENTS.md          ← idem, para OpenCode (gerado se ferramenta = OpenCode ou Ambas)
├── opencode.json      ← carrega _padroes.md automaticamente (OpenCode)
├── instrucoes/        ← procedimentos por operação, carregados sob demanda
├── conteudos/         ← conteúdo processado, um arquivo por tópico
│   └── 1-topico.md
└── aulas/             ← materiais brutos originais
    └── aula-XX/
```

---

### Operações

| Operação | Quando usar |
|----------|-------------|
| **Criar caderno** | Primeira vez em uma disciplina — pergunta onde criar e qual ferramenta; gera `CLAUDE.md` e/ou `AGENTS.md` + `instrucoes/` |
| **Atualizar caderno** | Propagar atualizações do caderneiro a um caderno existente |
| **Modificar caderno** | Ajustar configurações de um caderno existente |
| **Transcrever aula** | Converter `capturas/` ou `capturas.pdf` em `transcricao.md` |
| **Processar aula** | Integrar ao arquivo de tópico qualquer material em `aulas/aula-XX/` — transcrição, PDF, código, imagens ou combinação deles |
| **Gerar imagens** | Gerar imagens a partir dos prompts nos arquivos `.md` e remover os indicadores de pendência nos conteúdos |
| **Exportar conteúdo** | Sincronizar `conteudos/` + imagens com a plataforma de estudo (Notion, Obsidian, PDF, GitHub) |

**Onde ficam os cadernos:**
- **Dentro do caderneiro:** `caderneiro/cadernos/nome-disciplina/` — pasta `cadernos/` está no `.gitignore`; seus cadernos ficam privados
- **Fora do caderneiro:** qualquer caminho absoluto informado pelo usuário

As operações **Transcrever aula**, **Processar aula**, **Gerar imagens** e **Exportar conteúdo** são executadas a partir dos arquivos `instrucoes/` do caderno da disciplina.
> Operações adicionais podem existir conforme os módulos ativados no caderno.

---

## Instruções por Operação

Ao receber uma solicitação, identifique a operação e leia o arquivo correspondente antes de agir:

| Operação do caderneiro | Arquivo de instrução |
|------------------------|---------------------|
| Criar caderno | `instrucoes/criar-caderno.md` |
| Atualizar caderno | `instrucoes/atualizar-caderno.md` |
| Modificar caderno | `instrucoes/modificar-caderno.md` |

**Referências adicionais** (carregadas sob demanda durante a criação):

| Referência | Arquivo |
|------------|---------|
| Questionário interativo (Chamadas 1–8) | `instrucoes/questionario.md` |
| Templates base (Técnico/Teórico/Híbrido) | `instrucoes/templates-base.md` |
| Módulos opcionais (código, diagramas, etc.) | `instrucoes/modulos.md` |
| Adaptadores de plataforma (Notion, Obsidian, etc.) | `instrucoes/adaptadores-plataforma.md` |
| Procedimento de geração + checklist | `instrucoes/geracao.md` |
| Orquestração de modelos por operação | `instrucoes/modelos.md` |

---

## Papéis

**Você (Usuário):**
- Fornece materiais da aula (fotos do quadro, PDFs, código)
- Responde às perguntas do agente quando necessário
- Valida e solicita ajustes no conteúdo gerado

**Agente de IA (Claude Code ou OpenCode):**
- Conduz a criação e configuração do caderno
- Transcreve, processa e estrutura o conteúdo automaticamente
- Carrega instruções sob demanda conforme a operação solicitada

---

## Conceitos Importantes

**IMUTÁVEL vs INCREMENTAL:**

- **CLAUDE.md / AGENTS.md = IMUTÁVEL + LEAN**
  - Criado uma vez no início, nunca modificado após criação
  - Máximo ~100 linhas: apenas contexto da disciplina + mapa de operações
  - Aponta para `instrucoes/` — o agente lê o arquivo de operação sob demanda

- **instrucoes/_padroes.md = IMUTÁVEL**
  - Padrões compartilhados por todas as operações (formatação, exercícios, glossário, checklist)

- **instrucoes/[operacao].md = IMUTÁVEL**
  - Um arquivo por operação disponível (ex: `processar-aula.md`, `transcrever-aula.md`)
  - Carregado pelo agente apenas quando aquela operação é solicitada

- **Arquivos de tópico/aula = INCREMENTAIS (conteúdo)**
  - Um arquivo por tópico do Conteúdo Programático **ou** um por aula (se não houver programa)
  - Novas aulas do mesmo tópico são **acrescentadas** ao arquivo existente

**Convenção de nomenclatura:**
- Letras minúsculas, palavras separadas por hífen
- Prefixo numérico (`1-`, `2-`, etc.)
- **Sem o conectivo "de"** (ex.: `algoritmos-ordenacao`, não `algoritmos-de-ordenacao`)

---

## Orquestração de Modelos

Cada operação tem um nível de complexidade recomendado (**SIMPLES**, **MEDIO**, **COMPLEXO**) que mapeia para modelos específicos conforme o provedor em uso. A referência completa está em `instrucoes/modelos.md`.

**Como funciona:**
- Cada arquivo em `instrucoes/` contém um comentário `<!-- modelo: NIVEL -->` na primeira linha
- Ao iniciar uma operação, o agente lê o nível e consulta `instrucoes/modelos.md`
- **Modelo superior ao recomendado** (ex: opus para SIMPLES): sugere troca e **para — aguarda decisão** do usuário antes de prosseguir (evita gasto desnecessário de tokens)
- **Modelo inferior ao recomendado**: sugere troca mas prossegue normalmente
- **Modelo compatível**: prossegue sem comentários
- O agente sempre recomenda um modelo **do mesmo provedor** que o modelo ativo

---

**Versão:** 2.1
**Última Atualização:** 2026-03-23
**Licença:** Uso educacional livre
