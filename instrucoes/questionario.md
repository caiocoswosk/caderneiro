<!-- modelo: MEDIO -->
# Questionário Interativo

### 📝 Instruções para o Agente de IA

Quando um usuário solicitar **Criar caderno** (nova disciplina) ou **Modificar caderno** (caderno existente), você deve:

1. **Identificar a operação** — Criar (sem caderno existente) ou Modificar (caderno já existe)
2. **Começar pela ementa** — antes de qualquer pergunta, verificar se há arquivo de ementa disponível
3. **Copiar o texto de cada pergunta verbatim** — não reformule, não adicione introdução ou contexto antes das perguntas
4. **Usar a ementa ou configuração atual para pré-preencher e sugerir respostas** sempre que possível
5. **Confirmar entendimento antes de avançar**
6. **Documentar todas as respostas para uso posterior**

---

### 📍 Passo -1: LOCALIZAÇÃO DO CADERNO

**Apenas para "Criar caderno". Pular para Passo 0 se for Atualizar/Modificar.**

**→ Usar AskUserQuestion (Chamada 1) com o texto exato abaixo (não reformule):**
```
Q1: "Onde deseja criar o caderno?"
    A) 📁 No caderneiro — cadernos/[nome-disciplina]/ (privado, .gitignore)
    B) 📂 Em outro diretório (informar caminho completo)

Q2: "Você tem ementa ou conteúdo programático disponível?"
    A) Sim — vou fornecer agora (PDF, texto ou colar aqui)
    B) Não — vou preencher manualmente
```

Armazenar em: `{{CAMINHO_CADERNO}}`
- Se B em Q1: perguntar o caminho como texto livre após o menu.
Usar em todos os passos seguintes para montar os caminhos dos arquivos gerados.

---

### 📄 Passo 0: EMENTA / CONTEÚDO PROGRAMÁTICO

**Este passo acontece após a Chamada 1 (se Q2 = Sim).**

Se Q2 = Sim: solicitar o arquivo/conteúdo e extrair automaticamente:
  - Nome da disciplina → {{NOME_DISCIPLINA}}
  - Código → {{CODIGO_DISCIPLINA}}
  - Período → {{PERIODO}}
  - Professor(a) → {{PROFESSOR}}
  - Instituição → {{INSTITUICAO}}
  - Carga horária → {{CARGA_HORARIA}}
  - Lista de tópicos → {{TOPICOS}}
  - Tipo inferido → sugestão para Seção 2

Se Q2 = Não: continuar para Seção 1 normalmente.

Após ler a ementa, apresentar um resumo do que foi extraído e pedir confirmação usando exatamente este texto:
```
"Extraí da ementa:
  - Disciplina: [valor]
  - Código: [valor]
  - Período: [valor]
  - Professor(a): [valor]
  - Instituição: [valor]
  - Carga horária: [valor]
Está correto? Alguma correção?"
```

---

### 🎯 Seção 1: IDENTIFICAÇÃO DA DISCIPLINA

**Objetivo:** Confirmar ou completar informações básicas.
Se a ementa foi fornecida no Passo 0, pular as perguntas já preenchidas e perguntar apenas as que ficaram em branco.

**→ Usar AskUserQuestion (Chamada 1.5) com o texto exato abaixo (não reformule):**

Para cada campo ainda não preenchido pela ementa, perguntar em sequência como texto livre:

```
Q1: "Nome completo da disciplina?"
    Armazenar em: {{NOME_DISCIPLINA}} (obrigatório)

Q2: "Código da disciplina? (pode pular — ex.: DCE16376)"
    Armazenar em: {{CODIGO_DISCIPLINA}}

Q3: "Período letivo? (pode pular — ex.: 2026/1)"
    Armazenar em: {{PERIODO}}

Q4: "Nome do(a) professor(a)? (pode pular)"
    Armazenar em: {{PROFESSOR}}

Q5: "Instituição de ensino? (pode pular — ex.: UFES - Campus São Mateus)"
    Armazenar em: {{INSTITUICAO}}

Q6: "Carga horária? (pode pular — ex.: 60h totais / 4h/semana)"
    Armazenar em: {{CARGA_HORARIA}}
```

---

### 🎓 Seção 2: TIPO DE CURSO

**Objetivo:** Determinar a natureza predominante do conteúdo.

Se a ementa foi fornecida no Passo 0, inferir o tipo:
```
Inferência baseada na ementa:
  - Palavras-chave como "implementação", "programação", "algoritmos", nomes de linguagens
    → sugerir TÉCNICA
  - Palavras-chave como "teoria", "prova", "demonstração", "fundamentos", "cálculo"
    → sugerir TEÓRICA
  - Mix de ambos → sugerir HÍBRIDA
```
Se o tipo puder ser inferido, posicioná-lo **em primeiro** na lista com `(Recomendado)`.

**→ Usar AskUserQuestion (Chamada 2) com o texto exato abaixo (não reformule):**
```
Q1: "Tipo de curso?"
    A) 💻 Técnica/Prática — >60% código/implementação (Recomendado se inferido)
    B) 📚 Teórica/Conceitual — >60% teoria/conceitos
    C) ⚖️ Híbrida/Balanceada — mix equilibrado

Q2: "Plataforma de visualização?"
    A) 📘 Notion — interface visual rica, toggles, callouts
    B) ⬜ Nenhuma — manter apenas arquivos locais

Q3: "Ferramenta de IA para operar o caderno?"
    A) Claude Code — gera CLAUDE.md
    B) OpenCode — gera AGENTS.md + opencode.json
    C) Ambas — compatibilidade total (Recomendado)
```

Armazenar em: `{{TIPO_CURSO}}`, `{{PLATAFORMA}}`, `{{FERRAMENTA}}`
Valores: `TECNICA|TEORICA|HIBRIDA`, `NOTION|NENHUMA`, `CLAUDE_CODE|OPENCODE|AMBAS`

> ℹ️ Refinamentos como linguagens usadas e nível de matemática são inferidos progressivamente conforme as aulas são processadas.

#### Configurações automáticas por plataforma

Após a escolha, definir automaticamente sem perguntar:

```
NOTION:   Callout: > 💡 **Dica:** Texto  |  Diagramas: Mermaid ✅ ASCII ✅
NENHUMA:  Callout: > **Nota:**           |  Diagramas: Mermaid ✅ ASCII ✅

Armazenar em: {{FORMATO_CALLOUT}} e {{SUPORTE_DIAGRAMAS}}
```

---

### 🧩 Seção 3: MÓDULOS OPCIONAIS

**Objetivo:** Selecionar componentes adicionais para o plano.

**→ Usar AskUserQuestion (Chamada 3) com multiSelect e o texto exato abaixo (não reformule):**
```
Q1 (multiSelect): "Módulos de conteúdo — selecione os que deseja incluir:"
    A) 🔍 Análise de Código — comentários linha a linha, análise de complexidade
    B) 📊 Diagramas — Mermaid, fluxogramas, árvores, ASCII art
    C) 📝 Exercícios — por dificuldade (🟢🟡🔴) com soluções em toggles
    D) 📖 Glossário — definições técnicas por aula ou global

Q2 (multiSelect): "Módulos adicionais — selecione os que deseja incluir:"
    A) 🔢 Fórmulas Matemáticas — LaTeX inline/display, equações, demos
    B) 📚 Referências Bibliográficas — ABNT, links, material complementar
    C) 🎥 Mídia — vídeos, áudios, imagens, capturas de tela
    D) 📸 Transcrição de Manuscritos — quadro/lousa, PDFs de fotos
```

> Módulo de Consistência (regras C1–C6) é **ativado por padrão** — não aparece no menu.
> Armazenar: `{{MODULO_CODIGO}}`, `{{MODULO_DIAGRAMAS}}`, `{{MODULO_EXERCICIOS}}`, `{{MODULO_GLOSSARIO}}`, `{{MODULO_FORMULAS}}`, `{{MODULO_REFERENCIAS}}`, `{{MODULO_MIDIA}}`, `{{MODULO_TRANSCRICAO}}`

**Subperguntas condicionais (após Chamada 3):**

Se `{{MODULO_EXERCICIOS}}` = true:
```
→ Usar AskUserQuestion:
Q: "Soluções nos exercícios?"
   A) Explicação completa (Recomendado)
   B) Gabarito resumido
   C) Apenas enunciados
Armazenar em: {{EXERCICIOS_COM_SOLUCAO}}
```

Se `{{MODULO_GLOSSARIO}}` = true:
```
→ Usar AskUserQuestion:
Q: "Localização do glossário?"
   A) Por aula — ao final de cada seção
   B) Global — seção única ao final do documento
Armazenar em: {{GLOSSARIO_TIPO}}
```

**Referência dos módulos (para geração do CLAUDE.md):**

| Módulo | O que adiciona |
|--------|---------------|
| Análise de Código | Comentários linha a linha, templates para funções, entrada/saída |
| Diagramas | Mermaid, fluxogramas, árvores, grafos; ASCII art para arrays/ponteiros |
| Exercícios | 🟢🟡🔴 por subtópico; 40/40/20 básico/intermediário/avançado; soluções em toggle |
| Glossário | Definições técnicas, formato expandível, ordem alfabética |
| Fórmulas | LaTeX inline/display; sintaxe por plataforma ($$, $) |
| Referências | ABNT, links, material complementar |
| Mídia | Imagens PNG/JPG, vídeos embed, transcrição de áudios |
| Transcrição | Procedimento 3 etapas, tratamento de visuais, relatório padronizado |

#### 3.8. Módulo de CONSISTÊNCIA NA GERAÇÃO

```
✅ Módulo de Consistência na Geração (ativado por padrão)

📦 O que este módulo adiciona:
  ✓ Regras para prevenir erros recorrentes na geração de conteúdo
  ✓ Checklist de verificação antes de finalizar cada aula
  ✓ Padrões de qualidade para traces, diagramas e exercícios

🎯 Recomendado para:
  • TODOS os cursos (ativado por padrão)
  • Especialmente importante quando há código, diagramas ou exercícios

⚠️ Este módulo é ATIVADO POR PADRÃO — diferente dos demais,
   que são opcionais. Pode ser desativado explicitamente se desejado.
```

Armazenar em: `{{MODULO_CONSISTENCIA}}`
Valores: `true` (padrão) | `false`

#### 3.9. Módulo de TRANSCRIÇÃO DE MATERIAIS MANUSCRITOS

```
[ ] Incluir Módulo de Transcrição de Materiais Manuscritos

📦 O que este módulo adiciona:
  ✓ Procedimento em 3 etapas: transcrição → verificação → correção
  ✓ Regras para análise de ordem e completude de páginas
  ✓ Tratamento configurável de elementos visuais (diagramas, desenhos)
  ✓ Tabela de inconsistências com coluna de gravidade
  ✓ Relatório padronizado ao final de cada transcrição

🎯 Recomendado para:
  • Disciplinas com aulas presenciais em quadro/lousa
  • Materiais manuscritos digitalizados (PDFs de fotos)

⚡ Ativado automaticamente quando:
  • Seção 6 marcou "Fotos de quadro / materiais manuscritos"
  • Arquivo capturas.pdf encontrado em aulas/aula-XX/
```

Armazenar em: `{{MODULO_TRANSCRICAO}}`
Valores: `true | false`

**Regras que este módulo injeta no CLAUDE.md gerado:**

**Regra C1: Indexação coerente com a linguagem do curso**
```
Todos os traces de execução, exemplos e exercícios devem usar
a mesma convenção de indexação da linguagem do curso (conforme identificada nos materiais):
  • C, Java, Python → base-0 (arrays começam em 0)
  • Pascal, Lua → base-1 (arrays começam em 1)
  • Pseudocódigo puro → definir explicitamente no início do documento

Verificação: ao gerar um trace, conferir se o primeiro valor de
cada variável de laço coincide com a inicialização no código.
```

**Regra C2: Código é fonte de verdade**
```
Quando o conteúdo apresenta um algoritmo com descrição textual
E implementação em código:
  1. Escrever o código primeiro
  2. Derivar a descrição textual a partir do código
  3. Nunca descrever uma variante na prosa e implementar outra no código
  4. Terminologia da prosa deve coincidir com o código
     (ex.: não dizer "laço Enquanto" se o código usa "while")

Verificação: após escrever código + descrição, percorrer o código
mentalmente e confirmar que cada if, for, while e swap corresponde
ao que o texto descreve.
```

**Regra C3: ASCII Art com posições calculadas**
```
Ao criar representações visuais de estruturas em blocos de código
(arrays com ponteiros, pilhas, filas, etc.):
  1. Escrever a estrutura e anotar a coluna de cada elemento
  2. Posicionar ponteiros/indicadores por cálculo, não por estimativa
  3. Conferir contando caracteres da linha resultante

Nunca "chutar" alinhamento visualmente — calcular antes de escrever.
```

**Regra C4: Diagramas Mermaid — critério e sintaxe**
```
Critério de uso:
  • Usar Mermaid quando o diagrama tem RELAÇÕES entre elementos
    (setas, hierarquia, fluxo)
  • Se a informação é apenas elementos lado a lado sem conexões,
    usar texto em bloco de código

Sintaxe obrigatória:
  • Quebra de linha em labels: usar <br/>, NUNCA \n
  • Nomes de nós semânticos (Level1_L["valor"] em vez de A["valor"])
  • Subgraphs para separar fases lógicas quando aplicável
  • Estilos com cores de contraste para diferenciar estados
```

**Regra C5: Sem rascunhos no conteúdo final**
```
O conteúdo entregue NUNCA deve conter:
  • Texto de auto-correção ("espera", "opa", "na verdade")
  • Tentativas falhas seguidas da versão correta
  • Comentários internos do processo de geração
  • Parênteses com correções inline

Se perceber um erro durante a geração: apagar o trecho errado
e escrever apenas a versão correta.
```

**Regra C6: Verificar soluções de exercícios**
```
Antes de incluir a solução de um exercício:
  1. Executar mentalmente o algoritmo/procedimento com a entrada
     do enunciado, passo a passo
  2. Conferir que o resultado bate com o que a solução afirma
  3. Se o exercício pede um trace: construir a partir do código
     (não da memória), respeitando C1 (indexação) e C2 (fidelidade)
```

---

### 📊 Seção 4: ESTRUTURA DE CONTEÚDO

**Objetivo:** Definir organização interna da documentação.

**→ Usar AskUserQuestion (Chamada 4) com multiSelect e o texto exato abaixo (não reformule):**
```
Q1 (multiSelect): "Elementos de estrutura — selecione os que deseja:"
    A) 📋 Tabela de controle de progresso — status por tópico/aula
    B) 🎯 Objetivos de aprendizagem — checkboxes no início de cada aula
    C) 📌 Resumo executivo (TL;DR) — parágrafo de 3-5 linhas ao final
    D) ✅ Seções "Quando usar / Quando NÃO usar" — para algoritmos/estruturas
```

Armazenar em: `{{INCLUIR_TABELA_CONTROLE}}`, `{{INCLUIR_OBJETIVOS}}`, `{{INCLUIR_RESUMO}}`, `{{INCLUIR_QUANDO_USAR}}`

---

### 🎨 Seção 5: ESTILO E FORMATAÇÃO

**Objetivo:** Personalizar aspectos visuais e de tom.

**→ Usar AskUserQuestion (Chamada 5) com o texto exato abaixo (não reformule):**
```
Q1: "Tom de linguagem?"
    A) 📘 Formal — acadêmico ("O algoritmo Merge Sort utiliza...")
    B) 💬 Didático — conversacional ("O Merge Sort funciona dividindo...")
    C) ⚡ Direto — conciso ("Merge Sort: divisão recursiva. O(n log n).")

Q2: "Nível de detalhamento?"
    A) 🔍 Alto — explicações extensas, múltiplos exemplos (30–60 min/aula)
    B) 📊 Médio — balanceado, exemplos-chave (15–30 min/aula)
    C) 📝 Baixo — resumos, bullet points (5–15 min/aula)

Q3: "Público-alvo principal?"
    A) 👨‍🎓 Estudante acompanhando o curso — tem contexto das aulas
    B) 🎯 Autodidata (sem aulas) — documentação autocontida
    C) 🔄 Revisão para provas — resumos e exercícios
    D) 📚 Referência profissional — técnica e precisa
```

Armazenar em: `{{TOM_LINGUAGEM}}`, `{{NIVEL_DETALHAMENTO}}`, `{{PUBLICO_ALVO}}`
Valores: `FORMAL|DIDATICO|DIRETO`, `ALTO|MEDIO|BAIXO`, `ESTUDANTE_ACOMPANHANDO|AUTODIDATA|REVISAO|REFERENCIA`

> ℹ️ `USAR_EMOJIS` é definido na Chamada 7 junto com as demais configurações avançadas.

**Impacto na geração:**
- `AUTODIDATA` → Ativa explicações mais detalhadas, glossário obrigatório
- `REVISAO` → Ativa resumos executivos, foco em exercícios
- `REFERENCIA` → Tom formal, alta precisão técnica

---

### 🗂️ Seção 6: MATERIAIS DE ENTRADA

**Objetivo:** Identificar tipos de arquivos a processar.

**→ Usar AskUserQuestion (Chamada 6) com multiSelect e o texto exato abaixo (não reformule):**
```
Q1 (multiSelect): "Tipos de materiais — parte 1:"
    A) 📄 PDFs — slides, apostilas, artigos
    B) 💻 Códigos-fonte — .c, .java, .py, .cpp…
    C) 🖼️ Imagens e diagramas
    D) 📝 Textos e anotações — .md, .txt

Q2 (multiSelect): "Tipos de materiais — parte 2:"
    A) 🎥 Vídeos — aulas gravadas, tutoriais
    B) 🔊 Áudios — gravações, podcasts
    C) 🌐 Links externos — documentação, artigos web
    D) 📸 Fotos de quadro / manuscritos — capturas.pdf, pasta capturas/
```

Armazenar em: `{{TIPOS_MATERIAIS}}`

**Subperguntas condicionais (após Chamada 6):**

Se marcou PDFs:
```
→ Usar AskUserQuestion:
Q: "Os PDFs são principalmente:"
   A) Slides de aula — bullet points, figuras
   B) Apostilas/livros — texto corrido
   C) Artigos científicos — formal, referências
   D) Misto
Armazenar em: {{TIPO_PDF}}
```

Se marcou Códigos:
```
→ Usar AskUserQuestion:
Q: "Comentários nos códigos:"
   A) Linha por linha — explicação completa
   B) Partes-chave — comentários seletivos (Recomendado)
   C) Apenas transcritos — sem comentários adicionais
Armazenar em: {{NIVEL_COMENTARIO_CODIGO}}
```

Se marcou Imagens:
```
→ Usar AskUserQuestion (multiSelect):
Q: "As imagens são principalmente (selecione as que se aplicam):"
   A) Diagramas técnicos — recriar em Mermaid/ASCII
   B) Gráficos e plots — extrair dados para tabela
   C) Fotos de quadro/anotações — transcrever
   D) Screenshots de código — digitar
Armazenar em: {{TIPOS_IMAGENS}}
```

Se marcou Vídeos:
```
→ Usar AskUserQuestion:
Q: "Como processar vídeos?"
   A) Transcrever falas importantes
   B) Capturar timestamps e tópicos (Recomendado)
   C) Apenas linkar (não processar)
Armazenar em: {{PROCESSAMENTO_VIDEO}}
```

Se marcou Manuscritos:
```
→ Ativa automaticamente {{MODULO_TRANSCRICAO}} = true.
→ Usar AskUserQuestion:
Q: "Tratamento de elementos visuais nos manuscritos:"
   A) 📝 Descrição textual detalhada
   B) 🎨 Prompt para geração de imagem por IA
   C) 📐 Diagrama/notação da área (Mermaid, UML, etc.)
   D) 🔀 Combinação: descrição + recurso técnico
Armazenar em: {{TRATAMENTO_VISUAIS_MANUSCRITOS}}
Nota: vale para todas as aulas transcritas na sequência,
sem perguntar novamente — salvo instrução explícita do usuário.
```

---

### 🔧 Seção 7: CONFIGURAÇÕES AVANÇADAS

**Objetivo:** Ajustes finos e preferências especiais.

**→ Usar AskUserQuestion (Chamada 7) com o texto exato abaixo (não reformule):**
```
Q1: "Numeração das aulas?"
    A) 01, 02, 03 — dois dígitos (Recomendado)
    B) 1, 2, 3 — sem zero à esquerda
    C) Semana 1, Semana 2
    D) Por tópico (não sequencial)

Q2: "Idioma da documentação?"
    A) Português (Brasil) (Recomendado)
    B) Inglês
    C) Bilíngue — termos em inglês, explicações em PT

Q3 (multiSelect): "Elementos avançados — selecione os que deseja:"
    A) 📊 Análise de complexidade (Big-O) nos algoritmos
    B) 🔀 Comparações entre algoritmos similares (tabelas)
    C) 💡 Contexto histórico e curiosidades
    D) 😀 Emojis como marcadores visuais (✅ ❌ 💡 ⚠️ 🎯)
```

Armazenar em: `{{FORMATO_NUMERACAO}}`, `{{IDIOMA}}`, `{{INCLUIR_COMPLEXIDADE}}`, `{{INCLUIR_COMPARACOES}}`, `{{INCLUIR_CONTEXTO_HISTORICO}}`, `{{USAR_EMOJIS}}`

Se `{{INCLUIR_COMPLEXIDADE}}` = true:
```
→ Usar AskUserQuestion:
Q: "Nível da análise de complexidade?"
   A) Apenas resultado final: O(n log n)
   B) Com justificativa resumida (Recomendado)
   C) Com demonstração matemática completa
Armazenar em: {{NIVEL_COMPLEXIDADE}}
```

---

### ✅ Seção 8: CONFIRMAÇÃO FINAL

**Objetivo:** Revisar e confirmar todas as escolhas.

Apresentar o resumo de todas as variáveis coletadas em texto, depois usar AskUserQuestion:

```
📋 IDENTIFICAÇÃO:
  • Disciplina: {{NOME_DISCIPLINA}} | Código: {{CODIGO_DISCIPLINA}}
  • Período: {{PERIODO}} | Professor: {{PROFESSOR}}
  • Instituição: {{INSTITUICAO}}

🎓 CURSO: {{TIPO_CURSO}} | 🖥️ PLATAFORMA: {{PLATAFORMA}} | 🛠️ FERRAMENTA: {{FERRAMENTA}}

🧩 MÓDULOS: Código:{{MODULO_CODIGO}} Diagramas:{{MODULO_DIAGRAMAS}} Exercícios:{{MODULO_EXERCICIOS}}
            Glossário:{{MODULO_GLOSSARIO}} Fórmulas:{{MODULO_FORMULAS}} Refs:{{MODULO_REFERENCIAS}}
            Mídia:{{MODULO_MIDIA}} Transcrição:{{MODULO_TRANSCRICAO}} Consistência:✅

🎨 ESTILO: Tom:{{TOM_LINGUAGEM}} | Detalhamento:{{NIVEL_DETALHAMENTO}} | Emojis:{{USAR_EMOJIS}}
👥 PÚBLICO: {{PUBLICO_ALVO}} | 📁 MATERIAIS: {{TIPOS_MATERIAIS}}
```

**→ Usar AskUserQuestion (Chamada 8) com o texto exato abaixo (não reformule):**
```
Q: "Tudo correto?"
   A) ✅ Sim — gerar o caderno agora
   B) 🔧 Não — revisar uma seção
```

Se B: perguntar qual seção revisar (texto livre) e retornar à chamada correspondente.
