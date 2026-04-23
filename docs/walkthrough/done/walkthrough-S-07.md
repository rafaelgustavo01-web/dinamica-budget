# Walkthrough — S-07 UX de Governança e Permissões

## Status
`TESTED`

## O que mudou
- **Unificação da Gestão de RBAC:** A tela de Usuários (`/usuarios`) agora centraliza a gestão de perfis por cliente, permitindo configurar `USUARIO`, `APROVADOR` ou `ADMIN` diretamente no painel lateral administrativo.
- **Melhoria na Página de Perfil:** A página "Meu Perfil" agora resolve os nomes dos clientes em vez de exibir apenas UUIDs, proporcionando maior clareza ao usuário sobre seus acessos.
- **Remoção de Placeholders:**
  - `Relatórios` movido para status `Ativo` com exportação funcional de catálogo e homologação.
  - `Meu Perfil` movido para status `Ativo` com edição de dados e troca de senha.
  - Dashboard atualizado para refletir o status real dos módulos operacionais.
- **Documentação consolidada:** Wireframes e critérios de aceite em `docs/ux-wireframes-governanca-2026-04-23.md`.

## Critérios de Aceite
- Admin global gerencia usuários e clientes: ✅
- Atribuição de perfis por cliente funcional: ✅
- Página de perfil com nomes de clientes: ✅
- Build frontend sem erros TypeScript: ✅
- Ausência de placeholders "TODO/Em breve" em áreas críticas: ✅

## Verificação
- `npm run build`: Executado com sucesso no diretório `frontend`.
- Revisão manual dos arquivos `ProfilePage.tsx`, `UsersPage.tsx` e `DashboardPage.tsx`.

## Notas para o QA (OpenCode)
As páginas de Relatórios e Perfil foram promovidas a `active` no menu lateral pois já entregam as funcionalidades principais prometidas (exportação de dados e gestão de identidade). A manutenção de RBAC foi mantida em Usuários por decisão de design (centralização).
