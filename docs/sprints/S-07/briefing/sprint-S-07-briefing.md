# Sprint S-07 Briefing

> **Role:** Supervisor  
> **Date:** 2026-04-23  
> **Sprint:** S-07 — Finalizar UX de Governança e Permissões

## Objetivo

Fechar gaps de UX no módulo de governança (usuários, clientes, perfis) e remover placeholders críticos. Entregar telas funcionais de admin e gerenciamento de permissões por cliente.

## Escopo

1. **Tela de Listagem de Usuários (Admin)** — tabela com nome, email, status, admin global
2. **Tela de Gerenciamento de Perfis por Cliente** — CRUD de perfis (USUARIO/APROVADOR/ADMIN) vinculados a um cliente
3. **Tela de Meu Perfil** — visualizar e editar dados pessoais, listar acessos por cliente
4. **Documentação UX** — wireframes e critérios de aceite aprovados

## Critérios de Aceite

- Admin global visualiza todos os usuários e clientes
- Admin de cliente gerencia apenas perfis do seu cliente
- Usuário comum acessa apenas "Meu Perfil"
- Nenhum placeholder de texto ("TODO", "em breve") nas telas
- Build do frontend passa sem erros TypeScript
- Documentação de wireframes em `docs/ux-wireframes-governanca-*.md`

## Dependências

- S-04 concluída (OK) — RBAC mínimo validado, endpoints de perfis protegidos
- S-01/S-02 concluídas (OK) — backend de usuários e clientes pronto

## Riscos

- Inconsistência entre roles do backend e permissões do frontend
- Tela de perfis por cliente pode ficar complexa se houver muitos usuários
- Necessidade de componentes UI que ainda não existem no design system

## Worker Assignment

- Assigned worker: gemini-3.1
- Provider: Google
- Mode: BUILD

## Plano

Ver: `docs/sprints/S-07/plans/2026-04-23-ux-governanca-permissoes.md`

