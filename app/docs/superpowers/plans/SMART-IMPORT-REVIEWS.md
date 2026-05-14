---
phases: A, B, C, D
feature: Smart Import Engine
reviewers: [opencode, codex]
reviewed_at: 2026-05-14T00:00:00Z
plans_reviewed:
  - 2026-05-14-smart-import-phase-c.md
  - 2026-05-14-smart-import-phase-d.md
  - (phases A and B: reviewed from implementation files)
skipped: gemini (DNS authentication failure), claude (self-review excluded — running inside Claude Code)
---

# Cross-AI Plan Review — Smart Import Engine (Phases A–D)

---

## OpenCode Review

### Summary

The Smart Import Engine is a well-architected 4-phase feature with a clean pipeline design (Extract → Detect → Map → Classify → Stage), atomic commit semantics, and a pragmatic profile learning loop. The separation of concerns across extractor, detector, mapper, classifier, and learner modules is sound, and the frontend staging UI provides good interactive feedback. However, there are several correctness issues (one critical), transactional inconsistencies, a fundamentally flawed confidence score formula, missing edge-case handling in data transformation, and significant test coverage gaps that must be addressed before production deployment.

### Strengths

- **Clean pipeline architecture** — Each stage is isolated, stateless, and easily testable.
- **Atomic commit design** — `_write_pq_items()` runs inside the same transaction as `commit_job`, ensuring PqImportacao and PqItem records are all-or-nothing.
- **Profile learning loop** — The correction → profile update → score recalculation flow is a good foundation for improving future imports.
- **Frontend UX** — Staging page with inline reclassification, editing, deletion, and visual warnings for missing quantities is intuitive.
- **Defensive file extraction** — Magic byte validation, multi-encoding CSV fallback, and trailing-None column stripping prevent common malformed file issues.

### Concerns

#### 🔴 HIGH

- **`RowClassifier` fallthrough bug — everything becomes `SECAO`**
  The final `return RowClass.SECAO` means any row that doesn't explicitly match `VAZIA`, `TOTAL`, or `ITEM` criteria is classified as a section. Rows like `"Concreto usinado"` (> 5 chars, not ALL_CAPS, no keyword, no quantity) become `SECAO` instead of `ITEM`, misclassifying legitimate budget items.

- **Score formula uses only *current-batch* corrections, not historical cumulative total**
  `_compute_score(uso_count, len(corrections))` passes the batch correction count, not cumulative. A profile with 10 successful uses drops from ~1.0 to ~0.5 on one bad import, then instantly returns to ~1.0 on the next clean run. The score oscillates wildly and is not a reliable maturity indicator.

- **Triple-commit anti-pattern**
  `create_job()` commits. The edit/add/delete/reclassify endpoints each commit. `commit_job()` commits a third time. Services owning commits makes them non-composable and creates partial-commit risk during refactors.

- **No row-level locking on JSONB mutations**
  Multiple concurrent users editing the same job's `payload_staging` will cause last-write-wins data loss. No optimistic locking (`version` column) exists.

#### 🟡 MEDIUM

- **Alias definitions duplicated** across `header_detector.py` and `column_mapper.py` — divergence is guaranteed over time. Extract to `aliases.py`.

- **`_write_pq_items` hardcodes `linhas_com_erro=0`** — When quantity parsing fails, row is still added with `quantidade=None` but error counter stays 0, misrepresenting import quality.

- **No ownership/authorization checks on row mutations** — Any authenticated user can mutate any job by ID. Missing tenant isolation check.

- **Decimal parsing for Brazilian formats** — `1.234,56` → `replace(",",".")` → `"1.234.56"` (invalid). Thousand-separator dot must be removed before replacing decimal comma.

- **`SmartImportStatus` type in frontend is incomplete** — Missing `'PROCESSANDO'` and `'FAILED'` values from backend enum.

- **`committed` state check is racy** — `job.status === 'COMPLETED' && commitMutation.isSuccess` may show inconsistent UI between mutation success and query refetch.

- **`norm_aliases` rebuilt inside loop** — Alias normalization recomputed per row in `_score_row()`. Easy to hoist.

#### 🟢 LOW

- `_MAX_SCAN_ROWS = 30` is a magic number — should be a configurable constant.
- `RowClassifier._to_decimal` silently swallows `InvalidOperation` — acceptable in classifier, but not in `_write_pq_items` where it silently corrupts quantity.
- No rate limiting on `/smart-import` upload endpoint — 10MB × unlimited = DoS vector.
- `openpyxl.load_workbook` blocks the async event loop — should use `asyncio.to_thread`.

### Suggestions

**1. Fix `RowClassifier` fallthrough:**
```python
if first_word in _SECTION_KEYWORDS:
    return RowClass.SECAO

# If there's any meaningful content, treat as ITEM (not SECAO)
if descricao:
    return RowClass.ITEM

return RowClass.VAZIA
```

**2. Fix confidence score to use cumulative corrections:**
```python
def _compute_score(uso_count: int, total_corrections_ever: int) -> float:
    if uso_count == 0:
        return 0.0
    raw = uso_count / (uso_count + total_corrections_ever * 2)
    return min(round(raw, 4), 1.0)
```
Query cumulative correction count from DB in `commit_job` before calling `ProfileLearner.apply()`.

**3. Move commits out of service layer** — Services should `flush()` only; endpoints own `commit()`.

**4. Handle thousand separators:**
```python
def _parse_brazilian_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    s = str(value).strip()
    if re.search(r"\.\d{3}", s):  # thousand separator dot
        s = s.replace(".", "")
    s = s.replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None
```

**5. Fix `linhas_com_erro` tracking:**
```python
linhas_com_erro = 0
for row in item_rows:
    if qtd_raw and quantidade is None:
        linhas_com_erro += 1
```

**6. Use `asyncio.to_thread` for file parsing:**
```python
sheet = await asyncio.to_thread(FileExtractor.from_bytes, filename, content, sheet_name)
```

### Risk Assessment: **HIGH**

Critical: RowClassifier bug + score formula volatility + triple-commit pattern + missing test coverage + no auth checks on mutations.

---

## Codex Review

### Summary

Overall well-structured and pragmatic for Brazilian PQ spreadsheet imports. The separation between staging, profile learning, and final PqItem creation is a strong design choice. Main risks are around data correctness at commit time, tenant/authorization boundaries, duplicate commits, locale-sensitive numeric parsing, and that the current learning loop only meaningfully learns header/sheet/column corrections while the frontend only exposes row reclassification.

### Strengths

- Clear backend pipeline with focused responsibilities per module.
- JSONB staging is appropriate for review/edit workflows before committing normalized records.
- `ImportProfile` learning model is simple and understandable.
- Atomic commit design is correct; `await db.flush()` before FK assignment is the right pattern.
- Use of `normalize_text()` before creating `PqItem` supports downstream FTS/matching.
- Frontend flow is coherent: upload → staging review → commit → match page.

### Concerns

#### 🔴 HIGH

- **Commit idempotency risk** — If `commit_job` can be called multiple times for the same job, it creates duplicate `PqImportacao` and `PqItem` records. No committed-state guard exists.

- **Tenant/security boundary risk** — `clienteId` and `propostaId` are frontend-supplied. Backend does not verify the authenticated user can access these resources. Cross-tenant import is possible.

- **Invalid ITEM rows still reach `_write_pq_items`** — `create_job` marks `REVIEW_REQUIRED` when items miss quantity/description, but `commit_job` has no server-side guard. Frontend button alone cannot be trusted.

- **Decimal parsing is fragile for Brazilian formats** — `1.234,56`, `1,234.56`, `12,5`, blank cells need deterministic handling. Naive replace can silently corrupt quantities.

- **XLSX zip-bomb risk** — XLSX is a ZIP container. A small file can expand to a massive sheet. Row/cell limits are needed.

#### 🟡 MEDIUM

- **Profile score overconfident after one use** — `uso_count=1, correction_count=0` → score `1.0` immediately.

- **Frontend only captures `ROW_RECLASSIFY` corrections** — Since `ROW_RECLASSIFY` does not structurally improve the profile (it's logged only), the current UI provides limited real learning benefit. `COLUMN_REMAP` and `HEADER_ROW_FIX` require additional UI.

- **Row corrections can become stale** — If user reclassifies then deletes/adds rows before commit, accumulated corrections may reference wrong rows.

- **Minimum header score of 2 is weak** — Rows containing domain words like "total" or "valor" outside the header could score 2 and be selected as the header row.

- **Profile alias poisoning** — User-supplied `header_text` blindly appended to aliases can degrade future imports if corrections are incorrect.

- **Zero-item import not blocked** — A file can parse successfully with zero valid ITEM rows.

#### 🟢 LOW

- CSV delimiter detection not tested with Brazilian exports.
- Large JSONB staging rows become expensive to patch/fetch.
- Frontend commit button lacks double-click prevention.
- TOTAL rows with quantities, section rows with numeric prefixes, and accented ALL_CAPS Portuguese may need additional classifier fixtures.

### Suggestions

**1. Add committed-state guard:**
```python
if job.status == SmartImportStatus.COMPLETED:
    raise ValidationError("Importação já foi commitada")
```

**2. Validate ITEM rows before writing:**
```python
item_rows = [r for r in rows if r.get("row_class") == "ITEM" and r.get("descricao")]
if not item_rows:
    raise ValidationError("Nenhum item válido para importar")
```

**3. Centralize Brazilian decimal parsing:**
```python
def parse_br_decimal(value: str) -> Decimal | None:
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(".", "").replace(",", ".")  # works for 1.234,56
    try:
        return Decimal(text)
    except InvalidOperation:
        return None
```

**4. Harden XLSX extraction:**
- Enforce max rows, max columns, max total cells.
- Reject suspicious ZIPs with excessive uncompressed size.

**5. Dampen confidence score:**
```python
score = uso_count / (uso_count + correction_count * 2 + 3)  # avoids 1.0 after one use
```

**6. Make row corrections stable** — Use a stable row ID (not index) in correction entries:
```ts
type CorrectionEntry = {
  row_id: string;  // stable ID assigned at staging creation
  correction_type: "ROW_RECLASSIFY";
  old_class: RowClass;
  new_class: RowClass;
};
```

**7. Backend authorization on every endpoint:**
- Job belongs to authenticated tenant
- `proposta_id` belongs to `cliente_id`
- Profile belongs to same cliente
- Commit cannot write to another tenant's proposal

### Test Coverage Gaps

- XLSX/CSV extraction limits, malformed files, wrong extension, wrong magic bytes.
- Header detection with preambles, merged cells, headers after row 30.
- Column mapping with profile-specific aliases, accents, duplicates.
- Row classification edge cases (ITEM/SECAO/TOTAL/VAZIA).
- Decimal parsing: `1.234,56`, `1234,56`, `1.234`, `12,5`, blanks, invalid strings.
- `commit_job` idempotency.
- `_write_pq_items` verifies `normalize_text()` called per item.
- Authorization tests for cross-tenant access.

### Risk Assessment: **MEDIUM-HIGH**

Architecture is sound but production correctness depends on commit-time validation, tenant authorization, duplicate prevention, and robust locale parsing.

---

## Consensus Summary

### Agreed Strengths (mentioned by both reviewers)

- Clean, isolated pipeline architecture (Extractor → Detector → Mapper → Classifier → Learner).
- Atomic transactional commit (`_write_pq_items` inside same `db.commit`).
- Appropriate use of `normalize_text()` for downstream matching.
- Frontend staging flow (upload → review → reclassify → commit → match) is well-designed.
- Defensive file handling (magic byte validation, multi-encoding fallback, size cap).

### Agreed Concerns (HIGH priority — both reviewers flagged)

1. **Brazilian decimal parsing is broken** — `1.234,56` case will corrupt quantities silently. Fix before any production imports.

2. **No tenant authorization on job mutations** — Any authenticated user can edit/commit any job. Must be fixed before multi-tenant use.

3. **Commit is not idempotent** — Double-clicking or API retry creates duplicate PqImportacao/PqItem records. Needs committed-state guard.

4. **Score formula is unreliable** — Either oscillates with batch corrections (OpenCode) or reaches 1.0 after a single import (Codex). Both reviewers want a more conservative formula and cumulative correction tracking.

5. **`RowClassifier` fallthrough to SECAO** — (OpenCode HIGH) Legitimate items without quantity are misclassified as sections. High-impact correctness bug.

### Additional Agreed Concerns (MEDIUM priority)

- Missing test coverage on pure pipeline modules (extractor, header_detector, column_mapper, row_classifier, profile_learner).
- Frontend-only captures ROW_RECLASSIFY corrections, which provide no structural profile improvement — the learning loop is effectively passive.
- Row correction indexes can become stale after delete/add operations.

### Divergent Views

- **Commit ownership**: OpenCode frames as "triple-commit anti-pattern" (service should never commit); Codex is more pragmatic about idempotency guarding. Both are valid; the architectural fix is larger scope.
- **XLSX zip-bomb**: Only Codex flagged this explicitly. Valid concern for untrusted uploads.
- **`RowClassifier` fallthrough**: Only OpenCode called this HIGH. Codex implicitly covered via edge-case test recommendations.

---

## Action Items (Priority Order)

| # | Severity | Issue | File |
|---|----------|-------|------|
| 1 | 🔴 | Fix `RowClassifier` fallthrough — ITEM rows becoming SECAO | `row_classifier.py` |
| 2 | 🔴 | Fix Brazilian decimal parsing (`1.234,56`) | `row_classifier.py`, `smart_import_service.py` |
| 3 | 🔴 | Add committed-state guard to `commit_job` | `smart_import_service.py` |
| 4 | 🔴 | Add tenant authorization checks on job endpoints | `api/v1/endpoints/smart_import.py` |
| 5 | 🟡 | Fix confidence score (cumulative corrections or dampened formula) | `profile_learner.py` |
| 6 | 🟡 | Fix `linhas_com_erro` counter in `_write_pq_items` | `smart_import_service.py` |
| 7 | 🟡 | Deduplicate aliases into shared `aliases.py` module | `header_detector.py`, `column_mapper.py` |
| 8 | 🟡 | Add unit tests for pure pipeline modules | `tests/unit/smart_import/` |
| 9 | 🟡 | Use `asyncio.to_thread` for file parsing | `smart_import_service.py` |
| 10 | 🟡 | Add XLSX row/cell limits to prevent zip-bomb | `extractor.py` |
| 11 | 🟢 | Complete `SmartImportStatus` type in frontend | `smartImportApi.ts` |
| 12 | 🟢 | Add rate limiting on upload endpoint | `api/v1/endpoints/smart_import.py` |

---

## How to Incorporate Feedback

Incorporate these findings into the next planning cycle:

```
/gsd-plan-phase <next> --reviews app/docs/superpowers/plans/SMART-IMPORT-REVIEWS.md
```

Or address items directly:

- Items 1–2: Fix in a targeted bugfix commit (no schema changes needed).
- Items 3–4: Fix before enabling multi-tenant access to smart-import.
- Items 5–8: Schedule as a separate hardening phase.
