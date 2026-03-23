<!-- modelo: MEDIO -->
# Atualizar Caderno

Usar quando o caderneiro evoluiu (novos módulos, procedimentos revisados, padrões atualizados) e o usuário quer que o caderno existente reflita essas melhorias.

**Passo 0 — Identificar o caderno**

Perguntar ao usuário qual caderno deseja atualizar (texto livre):
```
"Qual caderno deseja atualizar?"
- Listar cadernos em cadernos/ (se existirem)
- Ou informar caminho externo
```

---

**Passo 1a — Arquivos de contexto**

Verificar os arquivos de contexto do caderno conforme a ferramenta configurada (`{{FERRAMENTA}}`):
- `CLAUDE.md`: deve existir se `{{FERRAMENTA}} == CLAUDE_CODE` ou `AMBAS`
- `AGENTS.md`: deve existir se `{{FERRAMENTA}} == OPENCODE` ou `AMBAS`
- `opencode.json`: deve existir se `{{FERRAMENTA}} == OPENCODE` ou `AMBAS`

Para cada arquivo ausente, **→ Usar AskUserQuestion:**
```
Q: "[arquivo].md está ausente. Deseja criar?"
   A) ✅ Sim — criar com base na especificação atual do caderneiro
   B) ❌ Não — manter ausente
```

> Se múltiplos arquivos estiverem ausentes simultaneamente, agrupar em até 4 perguntas por chamada.

---

**Passo 1b — Operações ausentes**

Comparar os arquivos presentes em `instrucoes/` com o conjunto de operações padrão que todo caderno deve ter:

| Arquivo | Condição |
|---------|----------|
| `instrucoes/_padroes.md` | sempre |
| `instrucoes/processar-aula.md` | sempre |
| `instrucoes/gerar-imagens.md` | sempre |
| `instrucoes/exportar-conteudo.md` | sempre |
| `instrucoes/transcrever-aula.md` | se módulo de transcrição ativo |

Para cada arquivo ausente, **→ Usar AskUserQuestion:**
```
Q: "instrucoes/[arquivo].md — ausente (adicionado ao caderneiro após criação deste caderno). Deseja criar?"
   A) ✅ Sim — criar agora
   B) ❌ Não — manter ausente
```

**Passo 1b.1 — Hints de modelo**

Para cada arquivo de operação presente em `instrucoes/`, verificar se contém `<!-- modelo: NIVEL -->` na primeira linha. Verificar também se `instrucoes/_padroes.md` contém a seção "Modelos Recomendados".

Se ausentes, **→ Usar AskUserQuestion:**
```
Q: "Hints de orquestração de modelos não encontrados neste caderno. Deseja adicionar?"
   A) ✅ Sim — adicionar hints e seção de modelos conforme especificação atual
   B) ❌ Não — manter sem orquestração de modelos
```

Se **Sim**: inserir `<!-- modelo: NIVEL -->` na primeira linha de cada arquivo de operação (conforme tabela em `instrucoes/modelos.md` do caderneiro) e adicionar seção "Modelos Recomendados" em `_padroes.md`.

---

**Passo 1b.2 — Commands com verificação de modelo**

Para cada command file em `.claude/commands/` e/ou `.opencode/commands/` (conforme `{{FERRAMENTA}}`), verificar se contém a instrução de verificação de modelo (buscar por "modelo ativo" ou "nível do modelo" no conteúdo do arquivo).

Se ausente, **→ Usar AskUserQuestion:**
```
Q: "Os commands deste caderno não verificam o modelo antes de executar. Deseja atualizar?"
   A) ✅ Sim — atualizar commands com verificação de modelo
   B) ❌ Não — manter commands atuais
```

Se **Sim**: reescrever cada command conforme o template atualizado em `instrucoes/geracao.md` do caderneiro (Etapa 9, seção "Skills individuais").

---

**Passo 1c — Alinhamento de conteúdo**

Para cada arquivo presente em `instrucoes/`, ler seu conteúdo e compará-lo com a especificação correspondente no caderneiro. Identificar divergências conceituais: funcionalidades novas, regras alteradas, seções ausentes — não diff literal de texto.

Para cada arquivo que divergir, **→ Usar AskUserQuestion:**
```
Q: "instrucoes/[arquivo].md diverge da especificação atual. Principais diferenças: [resumo]. O que fazer?"
   A) ✅ Atualizar — reescrever preservando personalizações da disciplina
   B) 🔍 Ver detalhes — mostrar divergências antes de decidir
   C) ❌ Manter — preservar versão atual
```

- Se **Ver detalhes**: exibir detalhes em texto e usar AskUserQuestion novamente com A) Atualizar / B) Manter

**Passo 2 — Relatório de atualização**

```
✅ Atualização concluída
📄 Arquivos atualizados: N
⏭️ Arquivos mantidos: N
```
