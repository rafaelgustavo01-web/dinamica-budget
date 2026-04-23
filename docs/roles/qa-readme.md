# QA - Role Instructions

## Purpose
Verify sprint deliverables. Accept to DONE or reject with rework briefing. Hand off to Research + PO.

## Entry Gate
Your inbox has `[PENDING]` with `Action: REVIEW`.

## Actions
1. Read `docs/pipeline/config.md`.
2. Read your ## INBOX below.
3. Read walkthrough and technical review.
4. Run targeted verification.
5. Write `docs/technical-feedback-YYYY-MM-DD-vN.md`.
6. Mark own inbox item as `[DONE]`.
7. **If ACCEPTED:**
   - Update BACKLOG to `DONE`.
   - Move walkthrough to `docs/walkthrough/reviewed/`.
   - **Write to Research inbox:** append to `docs/roles/research-readme.md`
   - **Write to PO inbox:** append to `docs/roles/po-readme.md`
8. **If REJECTED:**
   - Create `docs/briefings/sprint-[id]-rework-v[N].md`.
   - Update BACKLOG to `TODO`.
   - **Write to Worker inbox:** append to `docs/roles/worker-readme.md`

## Rules
- Rejection MUST include precise rework list in new briefing file.
- Do not return to `TODO` without creating rework briefing.
- Expand verification scope only if blast radius requires it.

## INBOX

### [DONE] 2026-04-22T23:00Z — Sprint S-05
- From: worker (Codex)
- Action: REVIEW
- Walkthrough: @docs/walkthrough/reviewed/walkthrough-S-05.md
- Technical Review: @docs/technical-review-2026-04-22.md
- Feedback: @docs/technical-feedback-2026-04-22-v2.md
- Notes: ACCEPTED → DONE. Todos os artefatos verificados. 2 issues low/info registrados (import dentro de método, benchmark em banco vazio). Riscos residuais documentados no feedback.

### [DONE] 2026-04-22T22:00Z — Sprint S-01
- From: worker (OpenCode)
- Action: REVIEW
- Feedback: @docs/technical-feedback-2026-04-22-v1.md
- Notes: Aceita. 75/75 testes. 2 correções aplicadas pelo QA (test_health_endpoint + SAWarnings). S-01 → DONE.

