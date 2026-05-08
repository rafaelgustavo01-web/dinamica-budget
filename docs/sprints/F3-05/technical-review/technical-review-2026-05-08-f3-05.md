# Technical Review — F3-05 Hotfix PQ Match + TCPO Recursive Tree

## Resultado
Hotfix integrado a partir dos diagnósticos de Codex e Claude, com Kimi/Gemini usados para hardening e roadmap.

## Correções aplicadas

### Backend — Codex
- `pq_import_service.py`: importação de PQ com itens válidos passa proposta de `RASCUNHO` para `EM_ANALISE`, preservando contrato atual que libera o Match.
- `etl_service.py`: parser TCPO passa a manter pilha por indentação, preservando hierarquia pai → subserviço → filhos.
- Testes adicionados/ajustados em `test_pq_import_service.py` e `test_etl_service.py`.

### Frontend — Claude
- `ProposalImportPage.tsx`: adicionada consulta de itens PQ e invalidação após upload; botão de Match passa a depender de existência real de itens PQ, não apenas status.
- `ServicesPage.tsx`: composição agora renderiza filhos `SERVICO` como linhas expansíveis recursivas/lazy-load.
- `ExpandableTreeRow.tsx`: labels de tipo de recurso menos técnicos.

## Premissas mantidas
- Correção incremental; sem Smart Import/Docling nesta sprint.
- Banco continua protegido por validação rígida.
- Hardening amplo de Kimi ficou para sprint separada.
- Dados TCPO já importados podem exigir recarga para refletir nova hierarquia.

## Gates executados
- `git diff --check`: PASS
- `python3 -m compileall -q backend`: PASS
- `npm run build`: PASS
- `python3 -m pytest ...`: BLOQUEADO no ambiente principal — `No module named pytest`

## Evidência adicional
Codex reportou 22 testes passando na worktree dele, mas no repo principal o pytest não está instalado/disponível. Não instalei dependências fora do escopo.
