# Walkthrough — F3-05

## Fluxos cobertos
1. Importar PQ com itens válidos.
2. Confirmar que Match Inteligente fica habilitado sem reload.
3. Reabrir proposta com PQ já importada e confirmar botão habilitado.
4. Abrir Catálogo de Serviços.
5. Expandir serviço TCPO pai.
6. Expandir filho do tipo `SERVICO` e carregar seus componentes recursivamente.

## Validações técnicas
- Build frontend concluído com sucesso.
- Backend compila com `compileall`.
- `git diff --check` sem erros.

## Observação operacional
Para TCPO já carregada, a estrutura recursiva corrigida depende de recarga da fonte TCPO para recriar `referencia.composicao_base` com as relações pai/filho corretas.
