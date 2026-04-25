# Technical Review — S-12 UX Frontend do Módulo de Orçamentos

## Status
`TESTED`

## Escopo
- Novas telas para o Módulo de Orçamentos.
- API Service para Propostas e Importação.
- Configuração de rotas e menu lateral.

## Decisões Técnicas
- **Feature-Based Module:** Concentração de toda a lógica em `src/features/proposals/` para facilitar a manutenção futura, quando a S-11 for integrada.
- **Zod + React Hook Form:** Padronização da criação de propostas com validação no client-side.
- **Consumo de Multi-Part Form Data:** Implementado suporte para upload de arquivos reais integrando com o endpoint do FastAPI via Axios.
- **Status Badges Personalizados:** Extensão do componente `StatusBadge` para suportar o ciclo de vida da proposta (`RASCUNHO`, `EM_ANALISE`, etc).

## Verificação Técnica
- Build de produção completo: 1182 módulos transformados.
- Tipagem TypeScript verificada e livre de erros nas novas telas.
- Axios interceptors configurados no `proposalsApi` para herdar autenticação global.

## Riscos e Observações
- **Dependência de Backend (S-11):** A visualização de CPU é um esqueleto ("Ghost UI") com `ContractNotice`. A integração real exigirá atualização do `proposalsApi` e da `CpuTable` assim que o backend liberar os novos endpoints.
- **Navegação:** O item "Orçamentos" foi posicionado como prioridade máxima no grupo de Operação por ser o core da Fase 2.
