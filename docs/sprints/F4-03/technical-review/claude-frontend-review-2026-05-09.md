# Frontend Review — F4-03 — 2026-05-09

> Sprint: F4-03 — BASES/BCUs Upload Individual + CRUD
> Reviewer: Claude (post-quota review)
> Worker reviewed: Opencode (frontend/UX)
> Worktree: /tmp/db-f4-03-claude

---

## Verdict

**PASS with fixes applied.** Build clean. 6 issues found and corrected in-place.

---

## Issues Fixed

### 1. BcuPage — Stale dialog state when switching item type [HIGH]

**File:** `app/frontend/src/features/bcu/BcuPage.tsx`

**Problem:** `BcuItemDialog` uses `useState` inside conditional branches (`if (type === 'MO')`, etc.). When `type` prop changes between renders, the same React hook slot is reused — the form retains state from the previous type. Opening the EQP dialog after the MO dialog would show MO state pre-filled into EQP fields.

**Fix:** Added `key={`${dialogType}-${editingItemId ?? 'new'}`}` to `<BcuItemDialog>`. Forces a fresh mount (and fresh useState initializer) whenever type or target item changes.

---

### 2. EncargosTab — `fmtPct` formatting bug (3200% instead of 32%) [HIGH]

**File:** `app/frontend/src/features/bcu/BcuPage.tsx`

**Problem:** `fmtPct(item.taxa_percent)` was calling `Intl.NumberFormat` with `style: 'percent'`, which multiplies the value by 100. Since `taxa_percent` is stored as a raw percent (e.g., 32.5 for 32.5%), the display would show 3250.00%.

`MaoObraTab` already had the correct pattern (`encargos_percent / 100` before passing to `fmtPct`), but `EncargosTab` was missing the division.

**Fix:** Changed to `fmtPct(item.taxa_percent != null ? item.taxa_percent / 100 : null)`.

---

### 3. BcuPage — Active BCU not prioritized [MEDIUM]

**File:** `app/frontend/src/features/bcu/BcuPage.tsx`

**Problem:** `const cabecalho = cabecalhos?.[0]` was using the first result (most recently imported, by `criado_em DESC`). If there are multiple versions and the newest is inactive, the page would show data from an inactive version.

**Fix:** Changed to `cabecalhos?.find(c => c.is_ativo) ?? cabecalhos?.[0]`. Active BCU is selected first; falls back to most recent if none is active (empty state condition).

---

### 4. BcuPage — Delete without confirmation [MEDIUM]

**File:** `app/frontend/src/features/bcu/BcuPage.tsx`

**Problem:** Clicking "Excluir" on any item in any tab called `deletarMutation.mutate()` immediately, with no confirmation step. A misclick would permanently delete a row.

**Fix:**
- Added `deleteConfirm` state to hold pending `{ type, id }`.
- `onDelete` callbacks now set this state instead of calling mutate directly.
- Added `<ConfirmationDialog>` (already used in `BcuGestaoPage`) wired to `deletarMutation`.

---

### 5. BcuPage — Empty state rows missing in all tabs [LOW]

**File:** `app/frontend/src/features/bcu/BcuPage.tsx`

**Problem:** When a tab had zero items, the table rendered with just the header and no body content — visually ambiguous (loading? error? actually empty?).

**Fix:** Added `data.length === 0` guard rows with a localized "Nenhum X cadastrado" message in each of the 6 tabs.

---

### 6. BcuUploadPage — Tabela change doesn't re-validate preview [LOW]

**File:** `app/frontend/src/features/bcu/BcuUploadPage.tsx`

**Problem:** Validation errors were computed once on file load. If the user changed the `Tabela` select after loading a preview, the errors reflected the old table's required columns — potentially allowing upload of an invalid file.

**Fix:** Added `useEffect` that re-runs validation when `tabela` or `previewRows` changes. Added `useEffect` import.

---

## No-Change Items (Reviewed, Acceptable)

| Item | Assessment |
|------|-----------|
| `bcuItemApi.ts` contracts | Well-typed. Aligned with backend route shapes already in `bcu.py`. Pending endpoints (`POST /bcu/importar-individual`, `POST/PATCH/DELETE /{cabecalho_id}/{tipo}`) documented correctly. |
| `BcuGestaoPage.tsx` | Solid. Confirmation dialogs for all destructive actions. Correct `bcuApi.importarPlanilha → /importar-converter` endpoint. Empty state row present. |
| Navigation config | `Upload Individual` correctly marked `status: 'partial'`. Both new items gated behind `hasAdminPanelAccess`. |
| Router | Lazy-loaded routes for `/bcu/gestao` and `/bcu/upload` correct. Order safe (static before param). |
| `404` graceful degradation | Upload and CRUD mutations detect `404`/`Not Found` and show informative toasts instead of generic error. |
| XLSX chunk size (~340 KB) | Expected due to xlsx dependency. Already noted in Opencode review. |

---

## Remaining Risks

| Risk | Severity | Owner |
|------|----------|-------|
| Backend endpoints missing: `POST /bcu/importar-individual`, `POST/PATCH/DELETE /bcu/{id}/{tipo}` | HIGH | Kimi (backend) |
| `atualizarEquipamentoPremissa` (`PATCH /equipamentos/premissa`) not exposed in UI | LOW | Future sprint |
| No pagination/virtualisation on large BCU tables (>500 rows) | LOW | Future sprint |
| CSV parse path in `BcuUploadPage` uses XLSX library (handles it), but backend only accepts xlsx | LOW | Acceptable — backend validates |

---

## Gates

- `npm run build` → **PASS** (✓ built in ~17s, zero TS errors)
- `git diff --check` → **PASS** (whitespace only in auto-generated `package-lock.json`)
- No Alembic/migration files touched
- No backend files modified
- No push
