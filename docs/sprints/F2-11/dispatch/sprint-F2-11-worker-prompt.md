# Worker Prompt — Sprint F2-11

**Para:** Gemini
**Modo:** Agent / BUILD / Always Proceed
**Sprint:** F2-11 — Histograma da Proposta
**Repo:** C:\Users\rafae\Documents\workspace\github\dinamica-budget
**Prioridade:** P1 — fecha pipeline PQ → Match → Histograma → CPU

**⚠️ PRÉ-REQUISITO:** Esta sprint depende de F2-10 estar DONE. Confirme que `bcu.*` schema existe e `cpu_custo_service` já usa De/Para antes de iniciar.

---

Você é o worker da Sprint F2-11. Implemente o plano completo em `docs/sprints/F2-11/plans/2026-04-27-histograma-proposta.md` do início ao fim sem pausas.

Use `superpowers:subagent-driven-development` ou `superpowers:executing-plans` para executar o plano task-a-task com checkboxes.

## Por que você foi escolhido

Esta sprint tem **forte componente de frontend + UX complexa**:

- **ProposalHistogramaPage**: 8 abas (7 tipos BCU + Recursos Extras), edição inline em tabelas densas, badge de divergência por item, estado vazio, estado carregando
- **4 componentes novos**: `HistogramaTabMaoObra`, `HistogramaTabGenerica` (reutilizável), `RecursosExtrasTab`, `AlocacaoRecursoDialog` (modal com seleção e quantidade)
- **CpuTable modificado**: botão "Alocar recurso extra" por composição + exibição de extras já alocados
- **ProposalDetailPage**: botão "Montar Histograma" (condicional por papel) + badge "CPU desatualizada" (amber)
- Backend: 2 services novos + 8 endpoints + extensões a 3 services existentes — estrutura bem definida no plano

## Instruções de execução

1. **VERIFICAR ANTES DE INICIAR**: `cd app && python -m pytest backend/tests/unit/test_bcu_service.py -v` deve passar. Se falhar, F2-10 não está done — aguarde.
2. **OBRIGATÓRIO antes de codar**: leia em ordem os 12 arquivos listados em "Pré-requisito de leitura" no briefing
3. Leia o briefing: `docs/sprints/F2-11/briefing/sprint-F2-11-briefing.md`
4. Leia o plano completo: `docs/sprints/F2-11/plans/2026-04-27-histograma-proposta.md`
5. Execute cada task em ordem, commitando após cada uma
6. Após cada task de backend: `cd app && python -m pytest backend/tests/ -v --tb=short`
7. Após cada task de frontend: `cd app/frontend && npx tsc --noEmit`
8. Ao concluir TODAS as tasks:
   - Crie `docs/sprints/F2-11/technical-review/technical-review-2026-04-27-f2-11.md`
   - Crie `docs/sprints/F2-11/walkthrough/done/walkthrough-F2-11.md`
   - Atualize F2-11 para **TESTED** em `docs/shared/governance/BACKLOG.md`

## Atenções especiais

- **`montar_histograma` idempotente — preservar edições manuais**:
  ```python
  # Só atualiza linhas com editado_manualmente=FALSE
  # Linhas com editado_manualmente=TRUE → mantém valores do usuário (não sobrescreve)
  existing = await repo.get_por_proposta(proposta_id, tipo)
  for row in existing:
      if not row.editado_manualmente:
          await repo.update(row.id, novo_valor_bcu=bcu_valor_atual)
  ```

- **Encargos e Mobilização INTEGRAIS** (não filtrados):
  ```python
  # Encargos: copiar TODAS as linhas de bcu.encargo_item do cabecalho ativo
  # Sem considerar quais composições usam encargo — é parâmetro global
  encargos = await bcu_repo.get_encargos(cabecalho_ativo.id)
  for enc in encargos:
      await proposta_pc_repo.upsert_encargo(proposta_id=proposta_id, bcu_item=enc)
  ```

- **Divergência calculada dinamicamente** (não persistida):
  ```python
  # GET histograma retorna por item:
  # { ..., "valor_bcu_snapshot": 125.50, "valor_bcu_atual": 130.00, "diverge_bcu": True }
  # Calculado via JOIN em tempo de consulta — não armazenar flag de divergência
  ```

- **Trigger `cpu_desatualizada`**: implementar via chamada explícita em cada método de mutação do service (não via event do SQLAlchemy — mais rastreável):
  ```python
  # Em histograma_service.editar_item, recurso_extra_service.criar, alocar_recurso:
  await proposta_repo.set_cpu_desatualizada(proposta_id=proposta_id, valor=True)
  # Em cpu_geracao_service.gerar_cpu_para_proposta (ao final):
  await proposta_repo.set_cpu_desatualizada(proposta_id=proposta_id, valor=False)
  ```

- **Clonagem em `nova_versao`**: novos UUIDs para cada linha do histograma; novo `proposta_id`; `editado_manualmente` e `valor_bcu_snapshot` são recopiados do BCU atual (não da versão anterior — a nova versão parte de uma cópia fresca).

- **HistogramaTabGenerica**: componente reutilizável para EQP, EPI, FER (mesma estrutura de tabela). Recebe props `tipo`, `proposta_id`, `cabecalho_id`. MO usa `HistogramaTabMaoObra` separada (estrutura de colunas diferente: função, quantidade, salário, encargos, custo_h).

- **AlocacaoRecursoDialog**:
  - Abre da CpuTable quando usuário clica "Alocar recurso extra" em uma composição
  - Carrega lista de `PropostaRecursoExtra` da proposta via `histogramaApi.listarRecursosExtras(propostaId)`
  - Campo `quantidade_consumo` (Numeric, obrigatório)
  - Submit via `histogramaApi.alocarRecurso(propostaId, composicaoId, { recurso_extra_id, quantidade_consumo })`
  - Após submit: invalida query `cpu-itens`

- **Badge "CPU desatualizada"**: usar `warning` (amber), consistente com `AGUARDANDO_APROVACAO`. Verificar como outros badges estão implementados em `StatusBadge.tsx`. Exibir no `ProposalDetailPage` quando `proposta.cpu_desatualizada === true`.

- **Rota `/propostas/:id/histograma`**: declarar ANTES de outras rotas parametrizadas em `routes.tsx`. Em Python (`propostas.py`), os 8 endpoints novos devem ser declarados ANTES de `/{proposta_id}` genérico.

- **Testes 245+ PASS**: base é ~200 (F2-10). Adicionar ≥ 45 testes:
  - `test_histograma_service.py`: 12+ (montar, idempotência, editar, divergências, encargos integrais)
  - `test_proposta_recurso_extra_service.py`: 8+ (CRUD, alocar, desalocar, cpu_desatualizada trigger)
  - `test_histograma_endpoints.py`: 10+ (auth, montar, get, patch, aceitar-bcu, recursos extras, alocar)
  - Modificar `test_cpu_custo_service.py`: +5 (prioridade proposta_pc_*, soma extras)
  - Modificar `test_proposta_versionamento_service.py`: +5 (clonar histograma, clonar extras)

## Critérios de conclusão

- `alembic upgrade head` sem erro; 10 novas tabelas `operacional.proposta_pc_*` criadas
- `POST /propostas/{id}/montar-histograma` → 200; encargos integrais; MO/EQP/EPI/FER filtrados por De/Para
- Edição de item preserva `editado_manualmente=TRUE`; re-montar não sobrescreve
- Divergência detectada corretamente quando `valor_bcu_snapshot != valor_bcu_atual`
- `POST /recursos-extras` → cria (não impacta CPU); `POST /alocar-recurso` → alocação criada + `cpu_desatualizada=TRUE`
- `nova_versao` clona histograma completo + recursos extras + alocações
- **245+ PASS, 0 FAIL** no pytest
- **0 erros** no `tsc --noEmit`
- Todos os 9 tasks com checkboxes marcados
- `ProposalHistogramaPage` renderiza 8 abas; edição inline funciona com debounce
- Badge "CPU desatualizada" visível no ProposalDetailPage quando flag=TRUE
- `AlocacaoRecursoDialog` abre, lista recursos extras, submete alocação
- Documentos `technical-review` e `walkthrough` criados
- BACKLOG atualizado para TESTED

## Diretório de trabalho (principais)

```
app/alembic/versions/024_proposta_histograma.py
app/backend/models/proposta_pc.py
app/backend/models/proposta_recurso_extra.py
app/backend/models/proposta.py  (cpu_desatualizada)
app/backend/repositories/proposta_pc_repository.py
app/backend/repositories/proposta_recurso_extra_repository.py
app/backend/services/histograma_service.py
app/backend/services/proposta_recurso_extra_service.py
app/backend/services/cpu_custo_service.py  (modificar)
app/backend/services/cpu_geracao_service.py  (modificar)
app/backend/services/proposta_versionamento_service.py  (modificar)
app/backend/api/v1/endpoints/propostas.py  (8 endpoints novos)
app/backend/schemas/proposta_pc.py
app/backend/tests/unit/test_histograma_service.py
app/backend/tests/unit/test_proposta_recurso_extra_service.py
app/backend/tests/unit/test_histograma_endpoints.py
app/frontend/src/shared/services/api/histogramaApi.ts
app/frontend/src/shared/services/api/proposalsApi.ts  (cpu_desatualizada)
app/frontend/src/features/proposals/pages/ProposalHistogramaPage.tsx
app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx
app/frontend/src/features/proposals/components/HistogramaTabMaoObra.tsx
app/frontend/src/features/proposals/components/HistogramaTabGenerica.tsx
app/frontend/src/features/proposals/components/RecursosExtrasTab.tsx
app/frontend/src/features/proposals/components/AlocacaoRecursoDialog.tsx
app/frontend/src/features/proposals/components/CpuTable.tsx
app/frontend/src/features/proposals/routes.tsx
```

## Commits esperados (sequência mínima)

1. `feat(f2-11): migration 024 + models proposta_pc + recurso_extra + cpu_desatualizada flag`
2. `feat(f2-11): add HistogramaService (montar, get, editar, divergencias)`
3. `feat(f2-11): add PropostaRecursoExtraService (CRUD + alocacao)`
4. `feat(f2-11): add histograma and recursos-extras endpoints`
5. `refactor(f2-11): cpu_custo_service priority proposta_pc > bcu + recurso_extra sum`
6. `feat(f2-11): nova_versao clones histograma + recursos extras + alocacoes`
7. `feat(f2-11): add histogramaApi client`
8. `feat(f2-11): add ProposalHistogramaPage, tabs, RecursosExtrasTab, AlocacaoRecursoDialog`
9. `docs(f2-11): add technical-review and walkthrough, handoff to QA`
