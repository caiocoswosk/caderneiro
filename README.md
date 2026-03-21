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
- **Como processar uma aula** — usa a transcrição, PDFs, código ou qualquer material dentro da pasta da aula para estruturar o conteúdo no arquivo de tópico correspondente
- **Como gerar imagens** — produz diagramas a partir de prompts gerados durante o processamento

Tudo a partir de uma conversa com o agente.

---

## Estrutura

```
caderneiro/
├── README.md           ← este arquivo
├── CLAUDE.md           ← ponto de entrada para Claude Code
├── AGENTS.md           ← ponto de entrada para OpenCode
├── caderneiro.md       ← guia completo de operações
└── cadernos/           ← cadernos criados aqui ficam no .gitignore
```

Cada **caderno gerado** tem a seguinte estrutura:

```
nome-da-disciplina/
├── CLAUDE.md           ← contexto lean para Claude Code
├── AGENTS.md           ← contexto lean para OpenCode  (se configurado)
├── opencode.json       ← config multi-arquivo OpenCode (se configurado)
├── instrucoes/
│   ├── _padroes.md         ← padrões compartilhados (formatação, exercícios...)
│   ├── transcrever-aula.md ← operação: fotos do quadro → transcricao.md
│   ├── processar-aula.md   ← operação: materiais da aula → conteúdo estruturado
│   └── gerar-imagens.md    ← operação: prompts → imagens
├── conteudos/
│   └── 1-topico.md         ← conteúdo gerado, um arquivo por tópico
└── aulas/
    └── aula-XX/            ← materiais brutos originais
```

---

## Ferramentas suportadas

| Ferramenta | Arquivo de contexto | Multi-arquivo |
|------------|--------------------|----|
| [Claude Code](https://claude.ai/code) | `CLAUDE.md` | via `.claude/rules/` |
| [OpenCode](https://opencode.ai) | `AGENTS.md` | via `opencode.json` |

---

## Como começar

1. Clone ou baixe este repositório
2. Abra a pasta `caderneiro/` no Claude Code ou OpenCode
3. Peça ao agente: **"Criar caderno"**
4. Responda às perguntas sobre a disciplina (ou forneça a ementa — o agente preenche o resto)
5. Comece a usar: envie fotos do quadro, peça para processar uma aula, gere imagens

---

## Operações disponíveis

| Operação | O que faz |
|----------|-----------|
| **Criar caderno** | Configura um novo caderno para uma disciplina |
| **Atualizar/Modificar caderno** | Propaga melhorias do caderneiro ou ajusta configurações |
| **Transcrever aula** | Converte fotos do quadro em transcrição revisada |
| **Processar aula** | Transforma qualquer material da pasta da aula (transcrição, PDF, código, imagens) em conteúdo estruturado |
| **Gerar imagens** | Produz imagens de diagramas a partir dos prompts e remove os indicadores de pendência nos conteúdos |

---

*Feito para quem aprende de forma não-linear, em ambientes não-padronizados, com uma cabeça que não para.*
