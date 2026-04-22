# Parecer Técnico de Revisão — Sprint S-02

> **Revisor:** Supervisor (Research AI mode)  
> **Data:** 2026-04-22  
> **Artefatos revisados:**
> - `docs/briefings/sprint-S-02-briefing.md` (v1.0 → v1.1)
> - `docs/superpowers/plans/2026-04-22-arquitetura-camadas.md` (v1 → v2)

---

## Resumo da Revisão

| Item | v1 (original) | v2 (revisado) | Status |
|---|---|---|---|
| Bloqueadores técnicos | 2 (B1, B2) | 0 | ✅ Resolvido |
| Riscos altos | 4 (R1-R4) | 0 | ✅ Resolvido |
| Riscos moderados | 4 (M1-M4) | 0 | ✅ Resolvido |
| Testes unitários | AuthService (1 caso) | AuthService (3 casos) + VersaoService (4 casos) | ✅ Expandido |
| Testes de integração | Não mencionados | Task 6 obrigatória | ✅ Adicionado |
| Task 5 (servicos) | "grep -n" superficial | Inspeção de service + documentação | ✅ Aprofundado |

---

## Correções Aplicadas

### B1 — Assinatura inconsistente `ativar_versao`
- **Problema:** Service definia 3 args, endpoint chamava com 4.
- **Correção:** Service recebe apenas `versao_id` e resolve `item_proprio_id` internamente via repo.

### B2 — SQL direto no endpoint `ativar_versao`
- **Problema:** Endpoint fazia `db.execute(select(VersaoComposicao)...)`.
- **Correção:** Endpoint usa `svc.versao_repo.get_by_id()` (repository). SQL isolado na camada de dados.

### R1 — Duplicação de `db: AsyncSession`
- **Problema:** Service recebia `db` no `__init__` (via repos) E nos métodos.
- **Correção:** Padrão definido: **repo no `__init__`, sem `db` nos métodos do service**.

### R2 — `_check_perfil` no endpoint
- **Problema:** Helper de autorização com acesso a dados ficou no endpoint.
- **Correção:** Renomeado para `assert_edit_permission` e movido para `VersaoService`.

### R3 — `ativar_versao` incompleto
- **Problema:** Método no service estava como `pass`.
- **Correção:** Implementação completa incluída no plano (deactivate_all + ativação).

### R4 — Testes incompletos
- **Problema:** Apenas 1 caso de teste para AuthService.
- **Correção:** 3 casos para AuthService + 4 casos para VersaoService (happy path, erro, admin, permissão).

---

## Decisões de Arquitetura Registradas

1. **Padrão de Injeção:** Service recebe repositories no `__init__`. Não recebe `AsyncSession` nos métodos.
2. **Transação:** Mantido request-scoped. Service faz `flush`, endpoint não commita.
3. **SQL em métodos privados:** `ServicoCatalogService._explode_recursivo_*` e `_detectar_ciclo` ainda usam `db.execute`. Documentado como débito técnico aceitável fora do escopo.

---

## Recomendação

**APROVADO PARA EXECUÇÃO.**

O plano v2 está livre de bloqueadores, com riscos mitigados e critérios de aceite mensuráveis. O worker pode iniciar execução via subagent-driven ou inline.

---

## Próximos Passos

1. Handoff para Worker (BUILD)
2. Após execução, QA valida critérios de aceite
3. Se DONE, Research AI minera aprendizados para roadmap
