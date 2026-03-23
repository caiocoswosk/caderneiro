# Orquestração de Modelos

Cada operação do caderneiro e do caderno tem um nível de complexidade (SIMPLES, MEDIO, COMPLEXO) que mapeia para modelos de diferentes capacidades. O agente identifica o nível do modelo ativo e sugere troca quando necessário.

---

## Claude Code

| Nível | Modelo |
|-------|--------|
| SIMPLES | haiku |
| MEDIO | sonnet |
| COMPLEXO | opus |

Sugestão de troca: `/model`

---

## OpenCode — Identificação por Família

O agente identifica o nível do modelo ativo pela **substring** no nome do modelo. Para sugerir troca, indica a família-alvo e o comando `/models`.

### Anthropic (Claude)

| Substring no modelo | Nível |
|---------------------|-------|
| `haiku` | SIMPLES |
| `sonnet` | MEDIO |
| `opus` | COMPLEXO |

> Exemplo: modelo ativo `anthropic/claude-sonnet-4-20250514` → nível MEDIO.
> Sugestão para COMPLEXO: "Esta operação recomenda nível COMPLEXO. Troque para um modelo **Claude Opus** via `/models`."

### OpenAI

| Substring no modelo | Nível |
|---------------------|-------|
| `nano` | SIMPLES |
| `mini` (gpt-*-mini, o*-mini) | SIMPLES ou MEDIO ¹ |
| `gpt-4.1` (sem mini/nano) | MEDIO |
| `gpt-5` (sem mini/nano) | COMPLEXO |
| `o3` (sem mini) | COMPLEXO |

> ¹ `gpt-4.1-mini` e `gpt-5-mini` = SIMPLES. `o3-mini` e `o4-mini` = MEDIO (modelos de raciocínio compactos).

### Google (Gemini)

| Substring no modelo | Nível |
|---------------------|-------|
| `flash` | SIMPLES |
| `pro` | MEDIO/COMPLEXO ² |

> ² Usar a geração mais recente de `pro` como COMPLEXO. Ex: se `gemini-2.5-pro` e `gemini-3.1-pro` estão disponíveis, 2.5 = MEDIO, 3.1 = COMPLEXO.

### xAI (Grok)

| Substring no modelo | Nível |
|---------------------|-------|
| `grok-*-mini` | SIMPLES/MEDIO |
| `grok-*` (sem mini) | COMPLEXO |

### DeepSeek

| Substring no modelo | Nível |
|---------------------|-------|
| `deepseek-v*` | SIMPLES/MEDIO |
| `deepseek-r*` | COMPLEXO |

> Modelos `v*` são generalistas; modelos `r*` são de raciocínio (mais capazes, mais lentos).

### Mistral

| Substring no modelo | Nível |
|---------------------|-------|
| `ministral` | SIMPLES |
| `mistral-medium` | MEDIO |
| `codestral`, `mistral-large` | COMPLEXO |

### Meta (Llama) / Modelos Open-Source

| Substring no modelo | Nível |
|---------------------|-------|
| `8b`, `11b` ou menor | SIMPLES |
| `70b` | MEDIO |
| `405b` ou maior | COMPLEXO |

> Aplica-se a Llama, Qwen e outros modelos open-source. O tamanho (parâmetros) indica a capacidade.

### Outros / Modelos Locais

Se o modelo ativo não se encaixa em nenhuma família acima:
1. Perguntar ao usuário: "Qual a capacidade relativa do seu modelo? (leve, médio, pesado)"
2. Mapear a resposta para SIMPLES/MEDIO/COMPLEXO

---

## Atribuição por Operação

### Operações do Caderneiro

| Operação | Nível | Justificativa |
|----------|-------|---------------|
| criar-caderno | SIMPLES | Apenas roteia para questionário e geração |
| questionario | MEDIO | Lógica condicional, decisões interativas |
| geracao | COMPLEXO | 12 etapas, substituição de variáveis, checklist |
| atualizar-caderno | MEDIO | Comparação conceitual entre versões |
| modificar-caderno | SIMPLES | Re-executa questionário com pre-fills |

### Operações do Caderno (defaults)

| Operação | Nível | Justificativa |
|----------|-------|---------------|
| transcrever-aula | MEDIO | OCR/leitura de imagens, estruturação |
| processar-aula | COMPLEXO | Integra múltiplos materiais, cria conteúdo educacional |
| gerar-imagens | SIMPLES | Gera prompts a partir de templates |
| exportar-conteudo | MEDIO | Conversão de plataforma, chamadas API |

---

## Regras do Agente

### Detecção do modelo ativo

- **Claude Code:** o modelo ativo é visível pela sessão — usar tabela "Claude Code"
- **OpenCode:** ler o campo `"model"` do `opencode.json` ou identificar pelo contexto da sessão

### Identificação de família e nível

1. Extrair o nome do modelo ativo
2. Procurar a substring nas tabelas acima para determinar a **família** e o **nível atual**
3. Se nenhuma família corresponder → perguntar ao usuário

### Regra de mesma família

Ao sugerir troca, **nunca** trocar de família (ex: de Claude para GPT). Apenas subir/descer dentro da mesma família:
- Claude: haiku ↔ sonnet ↔ opus
- OpenAI: nano ↔ mini ↔ gpt-4.1 ↔ gpt-5
- Gemini: flash ↔ pro

### Comportamento ao iniciar uma operação

1. Ler o comentário `<!-- modelo: NIVEL -->` na primeira linha do arquivo de instrução
2. Identificar o nível do modelo ativo pela tabela de família correspondente
3. Comparar o nível atual com o recomendado:
   - **Modelo diferente do recomendado** (superior ou inferior): sugerir troca e **parar — aguardar a decisão do usuário** antes de prosseguir.
     > "Esta operação recomenda nível **X**. Troque para **[modelo-alvo]** via `/models` (OpenCode) ou `/model` (Claude Code), ou confirme para continuar com o modelo atual."
   - **Modelo compatível**: prosseguir sem comentários.

### Manutenção

Atualizar as tabelas de substring quando novas famílias de modelo surgirem. Não é necessário atualizar para novas versões dentro da mesma família — a detecção por substring já cobre.
