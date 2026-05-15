# Briefing — F4-05 Smart Import Hardening

## Objetivo
Corrigir os riscos P0/P1 encontrados na revisão do Smart Import antes de promover a Fase 4 para DONE: autorização multi-tenant/proposta, persistência segura de staging JSONB, idempotência do commit, parsing decimal brasileiro, limites de arquivo e cobertura de testes.

## Contexto
- Origem: revisão de `app/docs/superpowers/plans/codex-review-prompt.md`.
- Área: backend FastAPI + SQLAlchemy async + PostgreSQL, com pequeno ajuste frontend se a semântica de status do staging mudar.
- Módulo afetado: `app/backend/services/smart_import*`, `app/backend/api/v1/endpoints/smart_import.py`, schemas/testes Smart Import.
- Regra do produto: PQ pode ser lida de forma flexível, mas gravação em `PqItem` deve ser validada, transacional, auditável e autorizada.

## Escopo
- Proteger todos os endpoints de Smart Import por cliente/proposta:
  - upload com `proposta_id`: exigir `EDITOR` na proposta.
  - upload sem `proposta_id`: exigir acesso ao `cliente_id`.
  - leitura de job: exigir acesso ao cliente ou papel efetivo na proposta.
  - mutações e commit: exigir `EDITOR` quando houver proposta; caso contrário exigir acesso ao cliente.
- Garantir que edições de `payload_staging["rows"]` persistam no JSONB sem depender de mutação nested invisível ao SQLAlchemy.
- Tornar `commit_job()` idempotente e protegido contra corrida, sem duplicar `PqImportacao`/`PqItem`.
- Corrigir parsing de números brasileiros (`1.234,56`, `1,5`, `1234.56`, `1.234`) em classificação e gravação.
- Validar `profile_header_row`, `sheet_name`, quantidade de linhas/colunas e payload máximo do staging.
- Ajustar score/learning loop para não promover aliases inválidos nem aceitar `HEADER_ROW_FIX` fora de faixa.
- Adicionar testes unitários focados e regressão mínima.

## Fora do escopo
- Reescrever arquitetura Smart Import.
- Adicionar Docling ou novo motor de extração.
- Criar nova UI de mapeamento.
- Alterar schema de banco salvo se o worker comprovar necessidade; preferir `mapping_metadata` para marcação de commit.
- Resolver sprints F4-01 a F4-04 pendentes de QA/Alembic fora deste módulo.

## Critérios de aceite
- Usuário sem acesso não consegue ler, editar, deletar, reclassificar ou commitar job de outro cliente/proposta.
- `patch_row`, `add_row`, `delete_row` e `reclassify_row` persistem alterações após commit em sessão SQLAlchemy real ou por reatribuição rastreável.
- Chamadas repetidas/concorrentes de commit não duplicam `PqImportacao` nem `PqItem`.
- `1.234,56` vira `Decimal("1234.56")`; `1,5` vira `Decimal("1.5")`; valores inválidos viram erro/revisão explícita, não perda silenciosa.
- Arquivos abusivos são rejeitados com `ValidationError` antes de gerar JSONB grande.
- Testes focados de Smart Import passam.

## Riscos
- Mudança de semântica de `SmartImportStatus.COMPLETED`: hoje `create_job()` pode marcar staging limpo como completed antes do commit. O worker deve separar "staged clean" de "committed" usando metadata ou ajuste frontend mínimo.
- Autorização por `cliente_id` tem histórico on-premise específico; para jobs com `proposta_id`, preferir `require_proposta_role`.
- `SELECT FOR UPDATE` deve ser usado apenas no commit para não bloquear leitura/edição desnecessariamente.

## Worker recomendado
Codex backend como executor principal; Kimi ou QA Gemini para revisão de segurança/transação.

## Plano
@docs/sprints/F4-05/plans/2026-05-15-f4-05-smart-import-hardening.md
