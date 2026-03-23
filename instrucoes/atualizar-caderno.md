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
