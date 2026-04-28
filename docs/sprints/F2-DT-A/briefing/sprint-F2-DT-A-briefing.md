# Sprint Briefing — F2-DT-A — Backend Tech Debt Cleanup

> Data: 2026-04-27
> Preparado por: Supervisor (PO + Arquiteto)
> Worker designado: claude-sonnet-4-6
> Execution mode: BUILD
> Plan: `docs/sprints/F2-DT-A/plans/2026-04-27-backend-tech-debt-cleanup.md`

## Mission

O checkpoint tecnico de 2026-04-27 (Amazon Q + Gemini + Kimi em
`docs/analysis/`) consolidou 26 achados de divida tecnica. Esta sprint
elimina **18 deles** no backend em 4 commits atomicos sequenciais,
escolhidos por **multiplicador de forca**: cada commit ou (a) desbloqueia
todos os outros (pytest), (b) fecha multiplos itens de uma vez (purga
legado), (c) padroniza um anti-pattern em 5 services (N+1), ou (d)
remove bomba-relogio para escala (cache em memoria do ETL).

A sprint paralela **F2-DT-B (Kimi, frontend)** roda em branches disjuntas
de arquivos — zero conflito git. Unica linha de acoplamento e o contrato
`codigo_origem` no schema `ComposicaoComponenteResponse`, que esta
**FROZEN no plano** (Commit 3.5).

## Delegation Envelope

| Campo | Valor |
|---|---|
| Sprint | F2-DT-A |
| Status entrada | PLAN |
| Status saida | TESTED |
| Worker | claude-sonnet-4-6 |
| Provider | Anthropic (Claude Code) |
| Mode | BUILD |
| Branch | main (regra global) |
| Auth/Quota | PASS (worker default do projeto) |

## Current Code State (hotspots validados)

### `app/backend/api/v1/endpoints/admin.py`
- L1, L161, L180: `import subprocess` + `subprocess.run` chamando
  `scripts/etl_popular_base_consulta.py` — **legado, remover** (Commit 2)
- Path traversal CWE-22 em `Path(file.filename).suffix` — sanitizar

### `app/backend/services/import_preview_service.py`
- Arquivo inteiro morto (pipeline duplicado) — **DELETE** (Commit 2)

### `app/backend/services/etl_service.py`
- L100: `self._cache: dict[str, _EtlParseResult]` — volatil em
  multi-worker (Commit 4)

### `app/backend/services/histograma_service.py`
- L77-88: loop sobre `insumos_unicos` disparando 3 queries por insumo
  (de_para + tcpo + bcu_item) — N+1 (Commit 3.1)
- `aceitar_valor_bcu`: seta `cpu_desatualizada=True` errado (Commit 3.4)

### `app/backend/services/servico_catalog_service.py`
- `listar_componentes_diretos`: loop com `get_by_id` por filho — N+1
- `ComposicaoComponenteResponse`: falta campo `codigo_origem` (Commit 3.5)

### `app/backend/core/dependencies.py`
- `require_proposta_role`: 2 queries por endpoint protegido (Commit 3.2)

### `app/backend/repositories/proposta_pc_repository.py`
- Classe `ProposalPcRepository` (ingles) — rename para
  `PropostaPcRepository` (Commit 3.3)

### `app/backend/services/proposta_export_service.py`
- BytesIO sem context manager (CWE-400/664) — Commit 3.6
- `capa["B2"] = proposta.codigo` mas label e "Cliente" — bug Commit 3.6

### `app/backend/services/proposta_versionamento_service.py`
- 8 imports locais em `nova_versao` (PEP 8) + `old_mob_id` dead code
  (Commit 3.7)

### `app/backend/core/config.py` + `app/backend/tests/conftest.py`
- Pytest em batch falha (`connection was closed`) — Commit 1

## Required Changes (resumo — detalhe no plan)

| # | Commit | Files | Itens fechados |
|---|---|---|---|
| 1 | pytest infra | config.py, conftest.py | C-03amzq, B-08, Gemini#1 |
| 2 | purge legado | admin.py, DELETE 2 arquivos | C-01amzq, C-02amzq |
| 3 | N+1 + bundle | 8 arquivos services/endpoints/repos | A-01..A-06, M-02, M-03, M-04, M-06, M-08bk, M-09, B-06, C-04kimi, Gemini#2 |
| 4 | ETL durabilidade | nova migration + etl_service.py + admin.py | C-03kimi |

## Mandatory Tests

- `app/backend/tests/` — toda a suite verde apos cada commit (197+ PASS)
- Validation commands:

```bash
python -m pytest app/backend/tests/ -q
python -m ruff check app/backend/
```

- Smoke E2E manual no Commit 4: `upload-tcpo` -> restart container ->
  `execute` com mesmo token (token sobrevive).

## Required Artifacts Before Status `TESTED`

- `docs/sprints/F2-DT-A/technical-review/technical-review-2026-04-27-f2-dt-a.md`
- `docs/sprints/F2-DT-A/walkthrough/done/walkthrough-F2-DT-A.md`
- `docs/shared/governance/BACKLOG.md` atualizado de `TODO` para `TESTED`

## Critical Warnings

1. **Branch `main` apenas.** Sem feature branches. Regra global do PO.
2. **1 commit por etapa** com mensagem `feat(f2-dt-a/N): <descricao>`.
3. **Suite verde apos cada commit.** Nao acumular debito de teste.
4. **Nao tocar `app/frontend/**`.** Sprint paralela F2-DT-B (Kimi)
   detem ownership exclusivo dessa arvore.
5. **Contrato `codigo_origem` e FROZEN** — assinatura exata no plan
   secao 3.5. F2-DT-B ja codifica frontend contra ele.
6. Nao marcar sprint como `DONE` — apenas `TESTED`.
7. Em caso de bloqueio, registrar no walkthrough e deixar status
   inalterado.
