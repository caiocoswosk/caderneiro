# 🗒️ Caderneiro

> Sistema de documentação acadêmica assistida por IA — do caos de materiais dispersos a um caderno estruturado, navegável e autoexplicativo.

---

## Por que isso existe

Sempre tive dificuldade de organizar minhas sessões de estudo de forma que fossem fluidas e consistentes. Na faculdade federal isso se complica ainda mais: não existe nenhum padrão entre livros, aulas e materiais fornecidos pelos professores. O resultado era muito tempo gasto em esforços paralelos e redundantes sem chegar a lugar nenhum.

Por ter TDAH, prestar atenção na aula e ao mesmo tempo copiar o conteúdo do quadro sempre foi uma batalha. Isso se intensificava por um problema de coordenação motora que tornava a experiência de copiar literalmente dolorosa. Quanto mais complexo o conteúdo, pior ficava o dilema: acompanhar o raciocínio ou registrar o que estava sendo escrito.

Com o aumento de responsabilidades — estágio, atividades extracurriculares, projetos — a pergunta ficou inevitável:

> *Como posso organizar e estruturar meu estudo de forma fácil, rápida, com baixa carga cognitiva — e ao mesmo tempo só enviar fotos do quadro ou os materiais do professor e ter todo o conteúdo de estudo gerado automaticamente?*

O Caderneiro é a resposta que construí para isso.

---

## O que é

O **Caderneiro** é um sistema baseado em IA para criar e operar **cadernos acadêmicos** — repositórios de conhecimento por disciplina, gerados a partir dos materiais brutos das aulas.

Um **caderno** transforma isso:

```
aulas/aula-03/
├── capturas/          ← fotos do quadro tiradas na aula
├── slides.pdf         ← material do professor
└── codigo-exemplo.c   ← implementação vista em aula
```

Em isso:

```
conteudos/
└── 1-introducao-grafos.md   ← conteúdo estruturado, navegável,
                                com teoria, código comentado,
                                exercícios por nível e glossário
```

Sem precisar digitar nada durante a aula. Sem perder o fio do raciocínio. Sem dor.

---

## Como funciona

O Caderneiro é um conjunto de instruções para agentes de IA (Claude Code ou OpenCode). Ele define:

- **Como criar um caderno** para uma disciplina — a partir da ementa, gera a estrutura completa automaticamente
- **Como transcrever uma aula** — converte fotos do quadro (`capturas/`) em `transcricao.md` com verificação de inconsistências e correção automática
- **Como processar uma aula** — usa a transcrição, PDFs, código ou qualquer material dentro da pasta da aula para estruturar o conteúdo no arquivo de tópico correspondente; identifica automaticamente o tópico pelo conteúdo
- **Como gerar imagens** — produz diagramas a partir de prompts gerados durante o processamento
- **Como exportar o conteúdo** — sincroniza os arquivos gerados com a plataforma de estudo escolhida: Notion (com upload automático de imagens via API e emoji como ícone da página), Obsidian, PDF ou GitHub

Toda interação acontece via **menus interativos** ou **skills diretas**: o agente apresenta opções usando o recurso nativo de menus do Claude Code / OpenCode, e cada operação tem sua própria skill invocável diretamente.

---

## Estrutura

```
caderneiro/
├── README.md
├── CLAUDE.md                         ← ponto de entrada para Claude Code
├── AGENTS.md                         ← ponto de entrada para OpenCode
├── caderneiro.md                     ← visão geral + tabela de dispatch
├── instrucoes/                       ← procedimentos por operação (carregados sob demanda)
│   ├── criar-caderno.md
│   ├── atualizar-caderno.md
│   ├── modificar-caderno.md
│   ├── questionario.md
│   ├── geracao.md
│   ├── templates-base.md
│   ├── modulos.md
│   ├── adaptadores-plataforma.md
│   └── modelos.md                    ← orquestração de modelos por operação
├── .claude/commands/                 ← skills Claude Code
│   ├── menu.md                       ← /menu
│   ├── criar-caderno.md              ← /criar-caderno
│   ├── atualizar-caderno.md          ← /atualizar-caderno
│   └── modificar-caderno.md         ← /modificar-caderno
├── .opencode/commands/               ← skills OpenCode
│   ├── menu.md                       ← /menu
│   ├── criar-caderno.md              ← /criar-caderno
│   ├── atualizar-caderno.md          ← /atualizar-caderno
│   └── modificar-caderno.md         ← /modificar-caderno
└── cadernos/                         ← cadernos criados aqui ficam no .gitignore
```

Cada **caderno gerado** tem a seguinte estrutura:

```
nome-da-disciplina/
├── CLAUDE.md                         ← contexto lean para Claude Code
├── AGENTS.md                         ← contexto lean para OpenCode (se configurado)
├── opencode.json                     ← config multi-arquivo OpenCode (se configurado)
├── .claude/commands/                 ← skills Claude Code
│   ├── menu.md                       ← /menu
│   ├── transcrever-aula.md           ← /transcrever-aula
│   ├── processar-aula.md             ← /processar-aula
│   ├── gerar-imagens.md              ← /gerar-imagens
│   └── exportar-conteudo.md          ← /exportar-conteudo
├── .opencode/commands/               ← skills OpenCode (se configurado)
│   └── [mesmas skills com frontmatter description:]
├── instrucoes/
│   ├── _padroes.md                   ← padrões compartilhados (formatação, exercícios...)
│   ├── transcrever-aula.md
│   ├── processar-aula.md
│   ├── gerar-imagens.md
│   ├── exportar-conteudo.md
│   └── scripts/
│       └── push_notion.py            ← script customizado de export para o Notion
├── conteudos/
│   └── 🔗 1-topico.md                ← conteúdo gerado com emoji, um arquivo por tópico
└── aulas/
    └── aula-XX/                      ← materiais brutos originais
```

---

## Ferramentas suportadas

| Ferramenta | Arquivo de contexto | Skills |
|------------|--------------------|----|
| [Claude Code](https://claude.ai/code) | `CLAUDE.md` | `.claude/commands/` |
| [OpenCode](https://opencode.ai) | `AGENTS.md` + `opencode.json` | `.opencode/commands/` |

---

## Como começar

1. Clone ou baixe este repositório
2. Abra a pasta `caderneiro/` no Claude Code ou OpenCode
3. Use **`/menu`** para ver as operações disponíveis
4. Selecione **A) Criar caderno** e responda às perguntas (ou forneça a ementa — o agente preenche o resto)
5. Abra a pasta do caderno criado e use **`/menu`** para acessar as operações do dia a dia

---

## Operações disponíveis

### Operações do caderneiro

| Comando | Operação | O que faz |
|---------|----------|-----------|
| `/menu` | Menu principal | Apresenta as opções abaixo |
| `/criar-caderno` | Criar caderno | Configura um novo caderno para uma disciplina a partir da ementa |
| `/atualizar-caderno` | Atualizar caderno | Propaga melhorias do caderneiro para um caderno existente |
| `/modificar-caderno` | Modificar caderno | Ajusta configurações de um caderno existente |

### Operações do caderno (dia a dia)

| Comando | Operação | O que faz |
|---------|----------|-----------|
| `/menu` | Menu principal | Apresenta as opções abaixo |
| `/transcrever-aula` | Transcrever aula | Converte fotos do quadro em transcrição revisada |
| `/processar-aula` | Processar aula | Transforma qualquer material da pasta da aula em conteúdo estruturado; identifica o tópico automaticamente |
| `/gerar-imagens` | Gerar imagens | Produz imagens de diagramas a partir dos prompts pendentes |
| `/exportar-conteudo` | Exportar conteúdo | Sincroniza `conteudos/` + imagens com Notion, Obsidian, PDF ou GitHub |

---

## Orquestração de modelos

O caderneiro recomenda automaticamente o modelo mais adequado para cada operação com base na complexidade da tarefa:

| Nível | Operações | Exemplos (Anthropic) |
|-------|-----------|---------------------|
| **SIMPLES** | criar-caderno, modificar-caderno, gerar-imagens | haiku |
| **MEDIO** | questionario, atualizar-caderno, transcrever-aula, exportar-conteudo | sonnet |
| **COMPLEXO** | geracao, processar-aula | opus |

Ao iniciar uma operação, o agente identifica o modelo ativo e compara com o nível recomendado. Se diferente, sugere troca e **para — aguarda a decisão do usuário** antes de prosseguir. Detalhes em `instrucoes/modelos.md`.

---

## ⚠️ Uso Responsável

Este projeto tem **foco pessoal e estudantil**. Os cadernos gerados são para uso próprio como ferramenta de estudo.

**Não compartilhe cadernos** que contenham transcrições, slides ou qualquer material de terceiros (professores, livros, apostilas) sem autorização explícita dos detentores dos direitos. O fato de o conteúdo ter sido processado por IA não altera a titularidade do material original.

---

*Feito para quem aprende de forma não-linear, em ambientes não-padronizados, com uma cabeça que não para.*
