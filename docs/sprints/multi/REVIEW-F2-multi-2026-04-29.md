# Code Review — F2 Multi-Sprint
**Date:** 2026-04-29
**Sprints reviewed:** F2-DT-A, F2-DT-B, F2-DT-C, F2-10, F2-11, F2-13
**Reviewer:** Claude (standard depth)
**Baseline:** 223 pytest PASS, 13 vitest PASS, 0 tsc errors

---

## Summary Table

| Sprint | Scope | CRITICAL | HIGH | MEDIUM | LOW |
|--------|-------|----------|------|--------|-----|
| F2-DT-A | etl_service, proposta_export_service, proposta_versionamento_service | 0 | 2 | 2 | 2 |
| F2-DT-B | ExpandableTreeRow, ExportMenu, ProposalDetailPage | 0 | 1 | 1 | 1 |
| F2-DT-C | 4 test files | 0 | 0 | 2 | 1 |
| F2-10 | bcu_service, bcu.py endpoint, bcu_de_para_service | 0 | 2 | 2 | 2 |
| F2-11 | histograma_service, ProposalHistogramaPage | 0 | 1 | 3 | 1 |
| F2-13 | servico_catalog_service | 0 | 1 | 1 | 0 |
| **Total** | | **0** | **7** | **11** | **7** |

---

## F2-DT-A — ETL Durability, Export, Versioning

### DTA-01 — HIGH
**File:** `app/backend/services/proposta_export_service.py:79`
**Issue: N+1 query in `gerar_excel`.**
`list_by_proposta` fetches all proposal items, then inside the loop `composicao_repo.list_by_proposta_item(item.id)` is called once per item. For a proposal with N items this fires N+1 queries. The result is stored in `composicoes_por_item` and reused later (tabs CPU / Composicoes are fine), but the fetch loop itself is the problem — it's a per-item await inside a for loop.
**Recommendation:** Add a `list_by_proposta_items_batch(proposta_id)` method to `PropostaItemComposicaoRepository` that fetches all compositions for the proposal in a single query keyed by `proposta_item_id`, replacing the loop. Same pattern already used in `proposta_versionamento_service.py` for mobilizacao.

---

### DTA-02 — HIGH
**File:** `app/backend/services/proposta_export_service.py:119-121`
**Issue: `BytesIO` used as a context manager but `buffer.getvalue()` is called inside the `with` block.**
`openpyxl.Workbook.save()` writes to the buffer and `buffer.getvalue()` is called at line 121 while the context manager is still open — this works because `close()` on a `BytesIO` only marks it closed without freeing memory before `getvalue()` can be called. However, the PDF path (lines 129-158) calls `doc.build(story)` and then `return buffer.getvalue()` inside the `with` block on the same `BytesIO`. `doc.build()` calls `buffer.close()` internally in some ReportLab versions, making `buffer.getvalue()` raise `ValueError: I/O operation on closed file` at runtime. The correct pattern is to call `getvalue()` before the context manager closes, or use the buffer without a `with` block.
**Recommendation:**
```python
# Excel — safe as-is, but make it explicit:
buffer = BytesIO()
wb.save(buffer)
return buffer.getvalue()

# PDF — replace with:
buffer = BytesIO()
doc = SimpleDocTemplate(buffer, ...)
doc.build(story)
return buffer.getvalue()
```

---

### DTA-03 — MEDIUM
**File:** `app/backend/services/etl_service.py:364-376`
**Issue: REPLACE mode deletes `referencia.composicao_base` before validating that tokens hold any data.**
The `DELETE FROM referencia.composicao_base` at line 365 fires unconditionally at the start of `REPLACE` mode. If the subsequent upsert fails (e.g., a malformed token payload passes the `if not all_itens` check but contains corrupt data), the BOM is lost with no rollback guard. The `await db.commit()` only runs at line 477 on success; SQLAlchemy async does not auto-rollback on exception unless the caller's context manager does so. If the endpoint catches the error and the session is reused, the in-progress deletes could be committed by a later flush.
**Recommendation:** Wrap the REPLACE section in a try/except that calls `await db.rollback()` on any error, or confirm that the calling endpoint owns a transaction boundary that rolls back on exception before re-raising.

---

### DTA-04 — MEDIUM
**File:** `app/backend/services/proposta_versionamento_service.py:103-107`
**Issue: Mutating detached ORM objects (`expunge` + direct attribute set) is fragile.**
After `self.db.expunge(item)`, the code mutates `item.id` and `item.proposta_id` and then calls `self.db.add(item)`. This pattern works today because the fields are plain columns, but it bypasses SQLAlchemy's identity map and can silently corrupt session state if a relationship attribute was already loaded (it will still reference the old FK). The safe pattern for cloning is to build a new object from scalar values.
**Recommendation:** Replace the expunge-mutate-add cycle with explicit object construction:
```python
new_item = model.__class__(
    **{c.key: getattr(item, c.key) for c in inspect(item).mapper.column_attrs
       if c.key not in ("id", "proposta_id")},
    id=uuid.uuid4(),
    proposta_id=nova.id,
)
self.db.add(new_item)
```

---

### DTA-05 — LOW
**File:** `app/backend/services/etl_service.py:590-595`
**Issue: Bare `except Exception: pass` suppresses all DB errors during token expiry purge.**
The expired-token cleanup at lines 591-595 silently swallows any DB error (connection loss, schema error). A failed purge means the `etl_preview` table can grow unboundedly. At minimum the exception should be logged at debug/warning level.
**Recommendation:**
```python
except Exception as exc:  # noqa: BLE001
    logger.debug("etl.token_purge_failed", error=str(exc))
```

---

### DTA-06 — LOW
**File:** `app/backend/services/proposta_export_service.py:56`
**Issue: `cliente` can be `None` if the FK lookup fails, but `cliente.nome_fantasia` is accessed without guard at line 56.**
Line 56: `capa["B2"] = cliente.nome_fantasia if cliente else ""` is correctly guarded. But `gerar_pdf` line 136 also has `cliente.nome_fantasia if cliente else '-'` which is safe. The one gap is lines 63-64 where `cliente.nome_fantasia` is used inside a conditional `if cliente`. No actual bug — this is fine — but `cliente.cnpj` (line 63) uses `getattr` guard while `nome_fantasia` (line 56 and 136) does not; inconsistent pattern increases future risk.
**Recommendation:** Use `getattr(cliente, "nome_fantasia", "")` consistently or document that `nome_fantasia` is a guaranteed non-nullable column.

---

## F2-DT-B — ExpandableTreeRow, ExportMenu, ProposalDetailPage

### DTB-01 — HIGH
**File:** `app/frontend/src/features/compositions/components/ExpandableTreeRow.tsx:123`
**Issue: Recursive child rows receive no `isExpandable` prop, so expandability is inferred solely from `tipo_recurso === 'SERVICO'`.**
When a child row is rendered at line 120-131, it does not pass `isExpandable`. The child component falls back to `item.tipo_recurso === 'SERVICO'` (line 36). If the API returns a child with `tipo_recurso: 'SERVICO'` that has no actual children in the DB, the user sees a chevron that expands to "Sem componentes." — a confusing but non-crashing experience. More critically: there is no depth cap. A cyclic BOM (even if unlikely for TCPO data) or a very deep BOM would generate an unbounded query cascade — one network request per expand click at each level. The UI has no depth limit or cycle guard.
**Recommendation:** Add a `maxDepth` prop (e.g., default 5) and render a non-expandable row when `depth >= maxDepth`. Also pass `isExpandable={child.tipo_recurso === 'SERVICO'}` explicitly from the parent to allow the parent to override based on server knowledge (e.g., a `has_children` flag).

---

### DTB-02 — MEDIUM
**File:** `app/frontend/src/features/proposals/components/ExportMenu.tsx:46-50` and `53-57`
**Issue: A second export can be triggered while the first is still in-flight.**
`busy` is set to `true` only for the active export type, but the `Menu` is opened by clicking the button, and both `handleExcel` and `handlePdf` are accessible via the open menu. If the user opens the menu while `busy=true`, the button is disabled but the menu items are not. Both menu items are rendered without a `disabled` prop. The user can trigger Excel while PDF is downloading, resulting in two concurrent downloads and two `setBusy(true)/setBusy(false)` races that can leave `busy` stuck at `false` prematurely.
**Recommendation:** Disable menu items while `busy` is true:
```tsx
<MenuItem onClick={handleExcel} disabled={busy}>
<MenuItem onClick={handlePdf} disabled={busy}>
```

---

### DTB-03 — LOW
**File:** `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx:34`
**Issue: `ExportMenu` import path resolves to `../components/ExportMenu` (relative path from `pages/`).**
The actual file is at `app/frontend/src/features/proposals/components/ExportMenu.tsx` — import works correctly. The issue noted in the spec (`app/frontend/src/shared/components/ExportMenu.tsx`) does not exist; the component lives under `features/proposals/components/`, not `shared/`. The `ProposalDetailPage.tsx` import at line 34 references the correct path. No action required, but the sprint description references the wrong path — update sprint docs.

---

## F2-DT-C — Smoke Tests

### DTC-01 — MEDIUM
**File:** `app/frontend/src/features/proposals/pages/__tests__/ProposalHistogramaPage.test.tsx:139-165`
**Issue: Test "edicao inline de uma celula dispara mutation com payload correto" asserts inside an MSW handler.**
Line 148: `expect(body.salario).toBe(4000)` is placed inside the MSW `http.patch` handler. If the handler is never called (e.g., the mutation does not fire), the `expect` is silently skipped and `patched` remains `false`. The `await waitFor(() => expect(patched).toBe(true))` at line 163 correctly catches this. However if the MSW handler throws (from the inner `expect`), MSW swallows the error and the handler returns `undefined`, causing the mutation to see a network error rather than the assertion failure. This means a wrong payload would surface as an "Erro ao exportar" Snackbar rather than a test failure pointing at the payload check.
**Recommendation:** Move payload validation outside the handler:
```ts
let capturedBody: Record<string, unknown> | null = null;
http.patch('...', async ({ request }) => {
  capturedBody = await request.json();
  return HttpResponse.json({ ok: true });
});
// ...after waitFor:
expect(capturedBody?.salario).toBe(4000);
```

---

### DTC-02 — MEDIUM
**File:** `app/frontend/src/features/compositions/components/__tests__/ExpandableTreeRow.test.tsx:150-151`
**Issue: Level-2 expand uses `screen.getAllByRole('button')` and clicks the last button.**
`chevrons[chevrons.length - 1]` assumes the newly rendered child row's chevron is always the last button in the DOM. This is coincidentally true now (only one `SERVICO`-type child is rendered at level 1) but will break silently if additional rows with chevrons are added to the mock data, causing the test to click the wrong element.
**Recommendation:** Use a more specific selector — e.g., query by the child row's description text's closest ancestor row, or assign `data-testid` to the toggle button with the item ID.

---

### DTC-03 — LOW
**File:** `app/frontend/src/features/proposals/pages/__tests__/ProposalHistogramaPage.test.tsx:83-96`
**Issue: The first test uses `findByText` for async elements but then immediately checks synchronous elements with `getByText` on line 95.**
`screen.getByText('CPU Desatualizada')` at line 95 will throw if the component is still loading. Since `findByText('Pedreiro')` at line 93-94 awaits data, the subsequent `getByText` is safe in practice. However this is a subtle temporal dependency — a future refactor that defers the `cpu_desatualizada` chip could silently break the synchronous assertion. No immediate bug, but worth converting to `findByText` or `waitFor` for robustness.

---

## F2-10 — BCU Unificada + De/Para

### F210-01 — HIGH
**File:** `app/backend/services/bcu_service.py:520-538`
**Issue: N+1 upserts for `base_tcpo` synchronization — one `EXECUTE` per item.**
In `importar_bcu` (line 520) and `importar_converter` (line 781), the `all_base_tcpo` list is iterated one item at a time, each executing a separate `pg_insert(...).on_conflict_do_update(...)`. For a BCU file with hundreds of items this fires hundreds of individual statements inside a single transaction, which is a significant performance and locking concern. The ETL service (`etl_service.py`) already demonstrates the correct pattern: chunked batch upsert with `_BATCH_SIZE = 500`.
**Recommendation:** Replace the per-item loop with batched `pg_insert` using `.values(list_of_dicts)` and `.on_conflict_do_update()`, identical to the pattern in `etl_service.py` lines 391-415.

---

### F210-02 — HIGH
**File:** `app/backend/api/v1/endpoints/bcu.py:134-144`
**Issue: Broad `except Exception` in `importar_converter` calls `await db.rollback()` after the service's `await self.db.commit()` may already have been called.**
The `BcuService.importar_converter` method commits at line 814 of `bcu_service.py`. If any exception is raised *after* that commit (e.g., during `db.refresh(cab)`), the endpoint catches it, calls `await db.rollback()`, and re-raises a `ValidationError`. Rolling back after a commit is a no-op in PostgreSQL (the committed data persists), but the endpoint still returns HTTP 422 to the client — reporting failure for a partially successful import. The client will retry, creating a duplicate `BcuCabecalho` (the idempotency delete at lines 570-575 should handle this for same filename, but the state is inconsistent between what the DB holds and what the client believes).
**Recommendation:** Move `await db.commit()` and `await db.refresh(cab)` inside the try block in the *service*, not after it. Alternatively restructure so the endpoint owns the commit and the service only flushes. At minimum, log a warning when rollback is called post-commit.

---

### F210-03 — MEDIUM
**File:** `app/backend/services/bcu_service.py:416-417`
**Issue: `BcuService.importar_bcu` deletes existing rows by filename *before* parsing the file.**
Lines 416-420: existing `BcuCabecalho` rows with the same `nome_arquivo` are deleted and flushed before the file is parsed. If parsing then fails (e.g., `openpyxl` raises on a corrupt file), the old data has been flushed out of the session but not yet committed. Since the exception will propagate and (assuming the caller rolls back) the delete will be rolled back too, this is not a data-loss bug — but only if the calling endpoint reliably rolls back. Given finding F210-02 above, rollback is not guaranteed. Consider reversing the order: parse first, then delete-and-replace.

---

### F210-04 — MEDIUM
**File:** `app/backend/services/bcu_de_para_service.py:43-45`
**Issue: Double subquery in `listar` when `only_unmapped=True` is unnecessarily complex.**
```python
subq = select(DeParaTcpoBcu.base_tcpo_id).subquery()
q = select(BaseTcpo).where(BaseTcpo.id.notin_(select(subq.c.base_tcpo_id)))
```
This wraps a subquery inside another `select()` — a double-nested subquery. The outer `select(subq.c.base_tcpo_id)` is redundant; `BaseTcpo.id.notin_(select(DeParaTcpoBcu.base_tcpo_id))` achieves the same result with one level of nesting. Not a correctness bug but generates more complex SQL than needed.
**Recommendation:**
```python
q = select(BaseTcpo).where(
    BaseTcpo.id.notin_(select(DeParaTcpoBcu.base_tcpo_id))
)
```

---

### F210-05 — LOW
**File:** `app/backend/services/bcu_de_para_service.py:186-189`
**Issue: `atualizar` fetches `BaseTcpo` without a null check.**
Line 186: `bt = await self.db.get(BaseTcpo, de_para.base_tcpo_id)`. If `de_para.base_tcpo_id` is somehow orphaned (referential integrity violated), `bt` will be `None` and line 188 (`bt.tipo_recurso`) will raise `AttributeError` — surfacing as a 500 rather than a 404/422. The `criar` path correctly checks `if not bt` (line 154).
**Recommendation:**
```python
if not bt:
    raise NotFoundError("BaseTcpo", str(de_para.base_tcpo_id))
```

---

### F210-06 — LOW
**File:** `app/backend/services/bcu_de_para_service.py:220-221`
**Issue: `_validar_bcu_item_existe` for `BcuTableType.MOB` validates against `BcuCabecalho` instead of a mobilizacao item.**
When `bcu_table_type == BcuTableType.MOB`, the validation fetches `BcuCabecalho.id` (line 220) — checking for a header record, not a mobilizacao item. If the intent is to allow mapping to a mobilizacao item, the correct model is `BcuMobilizacaoItem`. If MOB means "mapped to the cabecalho level" that should be documented. Either way the validation is inconsistent with the other types.

---

## F2-11 — Histograma da Proposta

### F211-01 — HIGH
**File:** `app/backend/services/histograma_service.py:476-477`
**Issue: `editar_item` calls `await self.proposta_repo.get_by_id(item.proposta_id)` without null check, then dereferences `proposta.cpu_desatualizada`.**
Line 476: `proposta = await self.proposta_repo.get_by_id(item.proposta_id)`. If the proposal was deleted between the item fetch and this call (unlikely but possible under concurrency), `proposta` is `None` and line 477 (`proposta.cpu_desatualizada = True`) raises `AttributeError`, which propagates as an unhandled 500.
**Recommendation:**
```python
proposta = await self.proposta_repo.get_by_id(item.proposta_id)
if not proposta:
    raise NotFoundError("Proposta", str(item.proposta_id))
proposta.cpu_desatualizada = True
```
Same pattern applies to `aceitar_valor_bcu` at line 515.

---

### F211-02 — MEDIUM
**File:** `app/backend/services/histograma_service.py:452-474`
**Issue: `editar_item` allows setting any attribute via `setattr(item, k, v)` with no field allowlist.**
Lines 470-471: any key present in `payload` that matches an attribute name on the ORM model is set without restriction. This means a caller could send `{"proposta_id": "<other_uuid>"}` or `{"bcu_item_id": "<tampered_uuid>"}` in the patch payload and silently reassign FK columns. The endpoint that calls `editar_item` should validate the payload shape using a Pydantic schema with an explicit field allowlist before passing it here, but the service itself has no defense.
**Recommendation:** Maintain an explicit set of editable fields per `tabela` and filter `payload` against it:
```python
EDITABLE_FIELDS = {
    "mao-obra": {"salario", "encargos_percent", "quantidade", ...},
    ...
}
allowed = EDITABLE_FIELDS.get(tabela, set())
for k, v in payload.items():
    if k in allowed and hasattr(item, k):
        setattr(item, k, v)
```

---

### F211-03 — MEDIUM
**File:** `app/backend/services/histograma_service.py:219-230`
**Issue: Unmapped `INSUMO` type is silently classified as EPI.**
Lines 219-230: when a `BaseTcpo` item has `tipo_recurso == "INSUMO"` and no De/Para mapping exists, it is appended to `epi_items`. The comment acknowledges this is a guess. This means ferramentas and other insumos without a mapping appear in the EPI tab of the histograma, which is incorrect cost classification and can corrupt cost reporting.
**Recommendation:** Log a warning and skip unmapped INSUMO items rather than silently misclassifying them, or extend the fallback to check the `codigo_origem` prefix (e.g., `FER-` → ferramenta).

---

### F211-04 — MEDIUM
**File:** `app/backend/services/histograma_service.py:255-271`
**Issue: `montar_histograma` calls `clear_encargos` and `bulk_insert(PropostaPcEncargo, ...)` without wrapping in an error handler.**
If `bulk_insert` for encargos fails after `clear_encargos` has already removed the existing rows (line 255), the proposal is left with zero encargos in the DB — data loss within the transaction. The service has no explicit rollback or savepoint around this destructive-then-insert pair. The `await db.flush()` at line 320 and commit would not be reached, but the caller's error handler must roll back for this to be safe.
**Recommendation:** Document clearly that the caller endpoint must own a transaction boundary that rolls back on any exception, or wrap the clear+insert in an explicit savepoint using `async with db.begin_nested()`.

---

### F211-05 — LOW
**File:** `app/frontend/src/features/proposals/pages/ProposalHistogramaPage.tsx:56`
**Issue: `Object.values(counts).reduce((a, b) => a + b, 0)` does not guard against `counts` being undefined.**
`montarMutation.onSuccess` receives the response from `histogramaApi.montarHistograma`, typed as the server's return dict. If the API returns an unexpected shape (e.g., an error body that passes HTTP 200), `.reduce` on a non-iterable will throw a runtime error. The reduce has a valid initial value (`0`), which protects against empty arrays, but not against `counts` being non-iterable.
**Recommendation:** Add a runtime guard: `Object.values(counts ?? {}).reduce(...)`.

---

## F2-13 — Tabela Hierárquica de Composições

### F213-01 — HIGH
**File:** `app/backend/services/servico_catalog_service.py:213`
**Issue: N+1 query for `insumo_proprio_id` children in `listar_componentes_diretos`.**
When the item is a PROPRIA composition, the code iterates over `versao.itens` at line 212. For children with `insumo_proprio_id`, each child fires an individual `await propria_repo.get_active_by_id(comp.insumo_proprio_id)` query at line 213 — one query per PROPRIA child. For a composition with many PROPRIA children this is a classic N+1. The `insumo_base_id` path immediately above (lines 189-191) correctly batch-fetches all BaseTcpo children in one query.
**Recommendation:** Apply the same batch-fetch pattern for PROPRIA children:
```python
proprio_ids = [c.insumo_proprio_id for c in versao.itens if c.insumo_proprio_id is not None]
proprio_map = await propria_repo.get_active_by_ids(proprio_ids)  # add this method
for comp in versao.itens:
    if comp.insumo_proprio_id is not None:
        filho = proprio_map.get(comp.insumo_proprio_id)
        ...
```

---

### F213-02 — MEDIUM
**File:** `app/backend/services/servico_catalog_service.py:233-290`
**Issue: `_explode_recursivo_tcpo` performs one DB query per BOM node (N+1 in DFS).**
Each recursive call fetches `ComposicaoBase` rows for a single `item_id` and then fetches each `filho` individually via `base_repo.get_by_id(comp.insumo_filho_id)`. A deep or wide TCPO BOM tree generates O(nodes) queries. For the tree view (F2-13) this is acceptable for single-level direct children (handled via batch in `listar_componentes_diretos`), but `explode_composicao` — which uses this recursive DFS — is exposed via an API endpoint and could be called on a root service with hundreds of nested components.
**Note:** This is an existing pattern predating these sprints and represents a known architectural limitation rather than a sprint regression. Flagged for visibility.
**Recommendation:** For the immediate term, add a `max_depth` guard (e.g., 10 levels) to `_explode_recursivo_tcpo` to bound worst-case query count.

---

## Cross-Sprint Observations

1. **Transaction boundary ownership is unclear.** Several services (`bcu_service`, `histograma_service`, `etl_service`) call `await db.commit()` directly while also being invoked inside FastAPI endpoints that inject the session via `Depends(get_db)`. If the `get_db` dependency uses a session-per-request that auto-commits on exit, this creates double-commit risk. If it uses a transaction-per-request that rolls back on exception, then the service-level commits happen *inside* the outer transaction, which is correct in PostgreSQL (they become sub-commits within the same connection) but can confuse error recovery when the service commits successfully but an exception occurs afterward. A consistent pattern — either all services flush and the endpoint commits, or services own commits and endpoints are stateless — would eliminate several of the medium findings above.

2. **`BcuTableType.MOB` in De/Para is unused but partially wired.** `_validar_bcu_item_existe` handles `MOB` but `criar`, `atualizar`, and `TIPO_COERENCIA` do not include it as a valid mapping target for any `tipo_recurso`. This dead-code path should either be completed or removed to avoid confusion.

3. **Test divergence detection test uses a wrong field name.** In `ProposalHistogramaPage.test.tsx` line 72, the divergence mock uses `campo: 'salario'` but the `detectar_divergencias` service generates `campo: 'custo_unitario_h'` for MO rows (line 373 of histograma_service.py). The test currently passes because the badge display does not depend on the `campo` value, but any future test that validates `campo` content will fail against production data.

---

## Overall Verdict

**PASS WITH NOTES**

The baseline test suite passes and no critical (data-corruption, authentication-bypass, or injection) issues were found. The codebase is well-structured with clear separation of concerns. Seven HIGH findings should be addressed before the next production deploy:

- DTA-01, DTA-02: Fix export N+1 and BytesIO misuse (production correctness risk)
- F210-01, F210-02: Fix BCU upsert N+1 and post-commit rollback confusion
- F210-05: Add null check in `atualizar` to prevent 500 errors
- F211-01: Add null check on `proposta` in `editar_item` / `aceitar_valor_bcu`
- F213-01: Fix N+1 for PROPRIA children in `listar_componentes_diretos`

The MEDIUM findings (field-allowlist in `editar_item`, INSUMO misclassification, concurrent export trigger) should be tracked and addressed in the next sprint cycle.
