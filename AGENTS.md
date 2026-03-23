# Caderneiro

> Leia `caderneiro.md` para o guia completo de operações.

Operações disponíveis via comandos: `/menu`, `/criar-caderno`, `/atualizar-caderno`, `/modificar-caderno`.

## Orquestração de Modelos

Ao executar um comando, verifique se o modelo ativo é adequado para a operação:

1. **Identifique seu modelo:** declare o nome/identificador do modelo que você está usando nesta sessão (ex: `claude-sonnet-4.5`, `gpt-4.1`, `gemini-2.5-flash`). Se não souber, pergunte ao usuário.
2. **Leia o nível recomendado:** a primeira linha do arquivo de instrução contém `<!-- modelo: NIVEL -->`.
3. **Consulte `instrucoes/modelos.md`:** compare seu nível atual com o recomendado.
4. **Se o modelo for diferente do recomendado** (superior ou inferior): sugira troca via `/models` e **pare — aguarde o usuário decidir** antes de prosseguir.
5. **Se compatível**: prossiga sem comentários.
