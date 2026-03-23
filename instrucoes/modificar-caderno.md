<!-- modelo: SIMPLES -->
# Modificar Caderno

Usar quando o usuário quer alterar as configurações do caderno (não relacionado a atualizações do caderneiro).

**Passo 0 — Identificar o caderno**

→ Usar AskUserQuestion com o texto exato abaixo (não reformule):
```
Q: "Qual caderno deseja modificar?"
   [listar cadernos em cadernos/ como opções, se existirem]
   + opção: "Informar caminho externo"
```
Se "Informar caminho externo": perguntar o caminho como texto livre.

---

**Passo 1 — Leitura do caderno atual**

Ler o `CLAUDE.md` do caderno e extrair todas as configurações atuais:
- Contexto da disciplina (nome, professor, instituição, etc.)
- Módulos ativos (`instrucoes/` existentes)
- Mapeamento tópico → arquivo
- Plataforma e padrões vigentes

**Passo 2 — Questionário com respostas pré-sugeridas**

Ler `instrucoes/questionario.md` e usar as **mesmas Chamadas 1–8**, com a seguinte adaptação:
- A opção correspondente ao valor atual de cada variável é posicionada **em primeiro** na lista com o sufixo `(Atual)`
- Exemplo para tipo de curso com valor atual HIBRIDA:
  ```
  A) ⚖️ Híbrida/Balanceada (Atual)
  B) 💻 Técnica/Prática
  C) 📚 Teórica/Conceitual
  ```
- Para multiSelect: marcar previamente as opções atualmente ativas

Ao final, apresentar resumo apenas das mudanças feitas (variáveis alteradas vs. mantidas).

**Passo 3 — Verificação de conformidade (opcional)**

**→ Usar AskUserQuestion:**
```
Q: "Deseja verificar se o caderno está em conformidade com o caderneiro atual?"
   A) ✅ Sim — verificar e listar divergências
   B) ❌ Não — aplicar apenas as mudanças acima
```

Se Sim: para cada ponto divergente encontrado, **→ Usar AskUserQuestion:**
```
Q: "⚠️ [descrição]. Situação: [atual] → Esperado: [spec]. O que fazer?"
   A) ✅ Corrigir agora
   B) 🔍 Ver detalhes
   C) ❌ Manter como está
```

Relatório ao final:
```
✅ Conformidade: N/M pontos
⚠️ Corrigidos: N pontos
🔕 Aceitos com divergência: N pontos
```

**Passo 4 — Aplicar mudanças**

Reescrever o `CLAUDE.md` e os arquivos de `instrucoes/` afetados com as alterações aprovadas.
