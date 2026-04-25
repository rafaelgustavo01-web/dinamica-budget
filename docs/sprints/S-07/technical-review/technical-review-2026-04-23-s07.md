# Technical Review — S-07 UX de Governança e Permissões

## Status
`TESTED`

## Escopo
- Finalização das interfaces de usuários, clientes e perfil.
- Sincronização de status de navegação no menu principal.
- Documentação de critérios UX.

## Decisões Técnicas
- **TanStack Query para Resolução de Nomes:** No componente de Perfil, optou-se por utilizar o `clientsQuery` (cacheado) para mapear UUIDs em nomes fantasia, evitando modificações complexas nos contratos de DTO do backend neste estágio.
- **Centralização de RBAC:** A decisão de manter o gerenciamento de perfis por cliente dentro da tela de Usuários (em vez de um módulo separado) visa reduzir a carga cognitiva do administrador, mantendo todo o contexto de acesso em uma única visualização.
- **Promoção de Status:** As rotas de Relatórios e Perfil foram promovidas de `partial` para `active` após validação de que os fluxos principais (download de CSV e edição de perfil) estão robustos.

## Verificação Técnica
- **Build:** O build de produção do Vite completou sem erros de tipagem (`tsc` ok).
- **Módulos:** 1167 módulos transformados no build.
- **Performance:** As queries de listagem utilizam paginação de 20 itens por padrão.

## Riscos Residuais
- A tela de Usuários pode apresentar lentidão se houver milhares de clientes vinculados a um único usuário devido à renderização de múltiplos Chips de perfil. Recomenda-se virtualização de lista em fases futuras se necessário.
