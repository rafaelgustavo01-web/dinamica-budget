# Dispatch — F4-DB-01 para Kimi

Leia o briefing e o plano:
- docs/sprints/F4-DB-01/briefing/sprint-F4-DB-01-briefing.md
- docs/sprints/F4-DB-01/plans/2026-05-15-f4-db-01-alembic-db-validation.md

Execute somente na instância de deploy/staging definida pelo Rafael.

Pontos críticos:
- Não imprimir DATABASE_URL nem segredo.
- Fazer pg_dump antes de qualquer mutação.
- Não fazer downgrade em produção real sem OK explícito.
- Reportar current/head/history do Alembic.
- Rodar upgrade head, smoke SQL, testes backend focados e smoke funcional.
- Commitar/pushar relatório final; não fazer deploy/restart sem autorização.
