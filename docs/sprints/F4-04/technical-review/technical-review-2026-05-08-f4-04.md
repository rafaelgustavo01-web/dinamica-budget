# Technical Review — F4-04 — 2026-05-08

> Sprint: F4-04 — Cadastro de Clientes para Folha PC
> Worker: Opencode (frontend/UX substituto)
> Backlog status target on exit: TESTED

## Component Map

| File | Responsibility | Change in this sprint |
|------|----------------|-----------------------|
| `app/backend/models/cliente.py` | SQLAlchemy model — campos comerciais para Folha PC | modified (trailing whitespace cleanup; campos já presentes) |
| `app/backend/schemas/cliente.py` | Pydantic schemas — validação de entrada/saída | modified (trailing whitespace cleanup; campos já presentes) |
| `app/backend/api/v1/endpoints/clientes.py` | FastAPI routers — CRUD de clientes | modified (trailing whitespace cleanup; campos já presentes) |
| `app/backend/repositories/cliente_repository.py` | Repository pattern — persistência | modified (trailing whitespace cleanup; campos já presentes) |
| `app/alembic/versions/027_cliente_campos_pc.py` | Migration Alembic — adiciona colunas comerciais | created (já presente na worktree) |
| `app/frontend/src/shared/types/contracts/clientes.ts` | TypeScript contracts — tipagem de API | modified (trailing whitespace cleanup; campos já presentes) |
| `app/frontend/src/shared/utils/format.ts` | Utilitários de formatação | modified (adicionados `formatCnpj` e `formatCep`) |
| `app/frontend/src/features/clients/ClientsPage.tsx` | Página de gestão de clientes | modified (UI enriquecida) |

## Delivery Summary

- **Planned change:** Enriquecer cadastro de Clientes com dados empresariais/comerciais úteis à Folha PC/Proposta Comercial, com UI limpa, labels amigáveis, tips leves, validação e sem IDs técnicos expostos.
- **Delivered change:**
  - Backend: modelos, schemas, endpoints, repositório e migration Alembic 027 já continham todos os campos comerciais (trabalho prévio de Codex). Realizada limpeza de trailing whitespace para passar no gate `git diff --check`.
  - Frontend: `ClientsPage.tsx` reformulada com formulários de criação e edição completos (9 campos adicionais), organizados em seções (Dados da empresa, Contato, Endereço). Painel de detalhes exibe todos os campos formatados (CNPJ mascarado, CEP mascarado) e remove o ID técnico. Adicionados `HelpTooltip` e `helperText` descritivos como tips leves. Validação client-side via Zod (e-mail, UF 2 letras maiúsculas, CEP 8 dígitos, tamanhos máximos). Utilitários `formatCnpj` e `formatCep` adicionados em `format.ts`.
- **Known risk:** Nenhum. Não houve alteração de schema além do que já estava na migration 027. Não há dados sensíveis em fixtures.

## Validation Snapshot

```bash
# Frontend
cd app/frontend && npm ci && npm run build
# Result: PASS (tsc + vite build verdes)

cd app/frontend && npm run test
# Result: PASS (13/13 tests)

# Git hygiene
git diff --check
# Result: PASS (sem trailing whitespace)
```

- **Notes:** Build frontend verde. Testes de regressão (smoke) passaram sem falhas. Não foi possível executar testes backend nesta worktree por indisponibilidade de ambiente Python/dependências, mas as alterações backend foram puramente cosméticas (trailing whitespace).

## Follow-on Notes for QA

- Validar visualmente o painel de detalhes sem ID técnico.
- Verificar se a formatação de CNPJ/CEP na tabela e no painel está consistente.
- Testar criação/edição de cliente com campos comerciais opcionais vazios (devem ser enviados como `null` ao backend).
- Confirmar que a migration 027 está reversível (`downgrade` implementado).
- Verificar integração futura com exportação/folha de rosto (fora do escopo desta sprint).
