# Caderneiro

> Leia `caderneiro.md` para o guia completo de operações.

Operações disponíveis via comandos: `/menu`, `/criar-caderno`, `/atualizar-caderno`, `/modificar-caderno`.

## Orquestração de Modelos

Ao executar um comando, verifique se o modelo ativo é adequado para a operação:

1. **Identifique seu modelo:** declare o nome/identificador do modelo que você está usando nesta sessão (ex: `claude-sonnet-4.5`, `gpt-4.1`, `gemini-2.5-flash`). Se não souber, pergunte ao usuário.
2. **Leia o nível recomendado:** a primeira linha do arquivo de instrução contém `<!-- modelo: NIVEL -->`.
3. **Consulte `instrucoes/modelos.md`:** compare seu nível atual com o recomendado.
4. **Se o modelo for diferente do recomendado** (superior ou inferior): sugira troca via `/model` e **pare — aguarde o usuário decidir**: o usuário pode trocar o modelo ou confirmar para prosseguir com o modelo atual.
5. **Se compatível**: prossiga sem comentários.

## Consistência Estrutural

Ao planejar ou implementar alterações em `instrucoes/` (scripts, templates, geracao.md, atualizar-caderno.md, modelos.md):

1. **Verificar estado atual:** execute a partir da raiz do caderneiro:
   ```
   python3 instrucoes/scripts/caderneiro_graph/cli.py --caderno . meta check
   ```
2. **Interpretar resultado:**
   - "nenhum gap encontrado" → consistência OK, prossiga
   - Gaps listados → resolver antes de commitar:
     - "Artefatos sem cobertura no Mapa" → adicionar entrada em `instrucoes/atualizar-caderno.md`
     - "Scripts sem menção em geracao.md" → adicionar na Etapa 8 de `instrucoes/geracao.md`
     - "Entradas do Mapa sem artefato" → remover entrada obsoleta do Mapa
3. **Após implementar:** re-execute o comando e confirme "nenhum gap encontrado"
4. Se adicionou novos scripts/pacotes em `instrucoes/scripts/`, atualize `geracao.md` Etapa 8

O usuário também pode solicitar a verificação a qualquer momento.

## Workflow de Atualização Estrutural (SSoT)

Ao adicionar ou remover operações do caderno (que afetam `modelos.md`,
`atualizar-caderno.md` e `geracao.md`):

1. **Criar branch:**
   ```
   git checkout -b meta/add-{nome-operacao}
   ```
2. **Editar `instrucoes/meta-schema.yaml`** — adicionar/remover entrada da operação
3. **Executar geração (A3 embutido):**
   ```
   python3 instrucoes/scripts/caderneiro_graph/cli.py --caderno . meta generate
   ```
   Se falhar: corrigir o schema e repetir. Não commitar com gaps.
4. **Atualizar `instrucoes/geracao.md` manualmente** — adicionar entrada
   `` **`instrucoes/{nome}.md`** `` na Etapa 8 se for operação nova
5. **Commit atômico** (apenas se `meta check` passar):
   ```
   git add instrucoes/meta-schema.yaml instrucoes/modelos.md \
           instrucoes/atualizar-caderno.md instrucoes/geracao.md
   git commit -m "meta: add operacao {nome}"
   ```
6. **Rollback** se qualquer etapa falhar:
   ```
   git checkout master && git branch -D meta/add-{nome-operacao}
   ```
