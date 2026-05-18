# Technical Review — F4-06 Pós-deploy Import/Match Stabilization

Data: 2026-05-18
Branch: main
Base inicial: 5e2570b

## Diagnóstico

- Repositório em `/root/workspace/dinamica_budget`, branch `main`.
- `/var/log/dinamica_budget/` não tinha arquivos úteis no momento da análise.
- `journalctl` para serviços prováveis (`dinamica-budget`, `dinamica_budget`, `uvicorn`, `gunicorn`) não retornou entradas recentes.
- Worktree já tinha arquivos não rastreados de documentação/scripts antes do início; eles foram preservados fora do commit.

## Causas confirmadas

1. Smart Import alterava `payload_staging` em JSON mutável sem marcar o atributo como sujo no SQLAlchemy.
   - Impacto: edições/add/delete/reclassificação no staging podiam não persistir após commit da sessão.

2. Smart Import aceitava `proposta_id` sem validar se a proposta pertencia ao `cliente_id` informado e sem exigir papel na proposta.
   - Impacto: risco de associar importação a proposta errada/cross-client.

3. PQ Match mantinha estado em memória por proposta depois de nova importação PQ.
   - Impacto: status concluído antigo podia mascarar a necessidade real de novo match após upload de nova planilha.

4. Upload individual BCU no frontend aceitava CSV e bloqueava layouts válidos por exigir nomes de coluna mais restritos que o backend.
   - Impacto: usuário podia selecionar formato que o backend rejeita e, ao mesmo tempo, ser bloqueado em planilhas XLSX aceitas pelo parser.

5. Gate local de testes BCU falhava no teardown por objetos antigos em schemas de teste não gerenciados pelo metadata.
   - Impacto: testes afetados não ficavam verdes em KVM2 mesmo com lógica de serviço passando.

## Correções aplicadas

- `app/backend/services/smart_import_service.py`
  - Adicionado `flag_modified(job, "payload_staging")` nas mutações de staging.

- `app/backend/api/v1/endpoints/smart_import.py`
  - Upload com `proposta_id` agora valida existência, vínculo com `cliente_id` e papel `EDITOR`.

- `app/backend/api/v1/endpoints/pq_importacao.py`
  - Novo upload PQ limpa o estado de match em memória da proposta.

- `app/frontend/src/features/bcu/BcuUploadPage.tsx`
  - Upload individual limitado a `.xlsx`, compatível com backend.
  - Validação de preview aceita aliases de coluna usados pelo parser (`descricao_funcao` ou `descricao`, `discriminacao_encargo` ou `discriminacao`).

- `app/backend/tests/conftest.py`
  - Fixture recria schemas customizados do banco de teste para evitar teardown bloqueado por objetos legados.

- `app/backend/tests/unit/smart_import/test_smart_import_service.py`
  - Cobertura adicionada para garantir marcação dirty das mutações de staging.

## Validação

- `venv/bin/python -m pytest -q backend/tests/unit/smart_import backend/tests/unit/test_pq_match_service.py backend/tests/unit/test_proposta_service.py backend/tests/unit/test_bcu_upload_service.py`
  - Resultado: 98 passed, 8 warnings.

- `npm run build` em `app/frontend`
  - Resultado: sucesso.
  - Observação: Vite manteve aviso existente de chunks acima de 500 kB.

- `git diff --check`
  - Resultado: sucesso.

## Observações

- Não houve deploy nem restart de produção.
- Arquivos não rastreados preexistentes foram mantidos fora do commit.
