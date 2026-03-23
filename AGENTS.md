# Caderneiro

> Leia `caderneiro.md` para o guia completo de operações.

Operações disponíveis via comandos: `/menu`, `/criar-caderno`, `/atualizar-caderno`, `/modificar-caderno`.

## Orquestração de Modelos

Ao executar um comando, verifique se o modelo ativo é adequado para a operação:

1. **Identifique seu modelo:** declare o nome/identificador do modelo que você está usando nesta sessão (ex: `claude-sonnet-4.5`, `gpt-4.1`, `gemini-2.5-flash`). Se não souber, pergunte ao usuário.
2. **Leia o nível recomendado:** a primeira linha do arquivo de instrução contém `<!-- modelo: NIVEL -->`.
3. **Consulte `instrucoes/modelos.md`:** compare seu nível atual com o recomendado.
4. **Se o modelo for superior ao recomendado** (ex: opus para tarefa SIMPLES): sugira troca via `/models` e **pare — aguarde o usuário decidir** antes de prosseguir. Isso evita gasto desnecessário de tokens.
5. **Se o modelo for inferior ao recomendado**: sugira troca mas prossiga normalmente.
6. **Se compatível**: prossiga sem comentários.
