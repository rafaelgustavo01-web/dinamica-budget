# Sprint F2-11 — Briefing

**Sprint:** F2-11
**Titulo:** Histograma da Proposta
**Worker:** gemini (a despachar quando F2-10 for DONE)
**Status:** PLAN (aguarda F2-10 DONE para ir a TODO)
**Data:** 2026-04-27
**Prioridade:** P1

---

## Contexto

F2-10 entregará o schema `bcu.*` + De/Para + `cpu_custo_service` refatorado. Com isso desbloqueado, F2-11 implementa o **Histograma da Proposta** — o snapshot editável per-proposta que separa custos globais (BCU) dos custos contratuais específicos da proposta.

O fluxo canônico passa a ser: **PQ → Match → Montar Histograma → CPU**. Ao montar o histograma, os valores BCU são copiados para tabelas `operacional.proposta_pc_*` com `valor_bcu_snapshot` gravado. O usuário pode editar esses valores per-proposta. A CPU usa o histograma (prioridade) em vez da BCU global.

## Objetivo

1. **Migration 024**: 8 tabelas `operacional.proposta_pc_*` (MO, EQP, ENC-Horista, ENC-Mensalista, EPI, FER, MOB, distribuição EPI por função) + `proposta_recurso_extra` + `proposta_recurso_alocacao` + flag `propostas.cpu_desatualizada`
2. **HistogramaService**: `montar_histograma` (explode composições → lookup De/Para → copia BCU), `get_histograma`, `editar_item`, `detectar_divergencias`
3. **PropostaRecursoExtraService**: CRUD recurso extra (livre) + alocar/desalocar em composição
4. **8 endpoints novos** em `propostas.py`: montar histograma, GET histograma, PATCH item, aceitar-bcu, recursos extras CRUD, alocar recurso
5. **cpu_custo_service**: adicionar resolução prioritária `proposta_pc_*` > `bcu.*` > `BaseTcpo.custo_base`; soma recursos extras alocados
6. **proposta_versionamento_service**: `nova_versao` clona histograma + recursos extras + alocações
7. **Frontend**: `ProposalHistogramaPage` (7 abas editáveis + Recursos Extras), 4 componentes novos (`HistogramaTabMaoObra`, `HistogramaTabGenerica`, `RecursosExtrasTab`, `AlocacaoRecursoDialog`), botão "Montar Histograma" + badge "CPU desatualizada" no `ProposalDetailPage`

## Decisões de produto (NÃO rediscutir)

| Decisão | Valor |
|---|---|
| Trigger do histograma | **Explícito** — botão "Montar Histograma" (não automático após match) |
| Snapshot | **Sincronizado com aviso** — valor snapshot gravado + badge divergência em tempo real |
| Recurso extra | **2 passos** — criar (sem impacto CPU) → alocar a composição (com `quantidade_consumo`) |
| Versionamento + histograma | **Clonar** — nova versão copia histograma + extras + alocações |
| CPU desatualizada | **Flag `cpu_desatualizada=TRUE`** em qualquer mutação de `proposta_pc_*`, `recurso_extra` ou `alocacao` |
| Encargos/Mobilização | **Integrais** — cópia completa do BCU ativo (não filtrados pela composição) |
| MO/EQP/EPI/FER | **Filtrados** — apenas itens cujo TCPO está presente nas composições E mapeado em De/Para |
| Sem mapeamento De/Para | Warning "Sem vínculo BCU" + `BaseTcpo.custo_base` como padrão; usuário pode editar |
| Permissões | EDITOR/OWNER monta e edita; VIEWER/APROVADOR apenas lê |

## Critérios de Aceite

- Migration 024 aplicada sem erro; 10 tabelas `operacional.proposta_pc_*` criadas + recurso_extra + alocacao
- `POST /propostas/{id}/montar-histograma` → cria/atualiza snapshot das composições filtrando por De/Para
- Encargos e Mobilização copiados integralmente do cabecalho BCU ativo
- `PATCH /propostas/{id}/histograma/mao-obra/{item_id}` → atualiza valor + seta `editado_manualmente=TRUE` + seta `cpu_desatualizada=TRUE`
- `POST /propostas/{id}/recursos-extras` → cria recurso livre (não impacta CPU ainda)
- `POST /propostas/{id}/composicoes/{composicao_id}/alocar-recurso` → cria alocação + seta `cpu_desatualizada=TRUE`
- `cpu_custo_service`: usa `proposta_pc_*` primeiro, fallback para `bcu.*`, depois `BaseTcpo.custo_base`; soma extras alocados
- `nova_versao` clona todo o histograma + extras + alocações da versão anterior
- `ProposalHistogramaPage`: 7 abas (MO, EQP, Encargos Horista, Encargos Mensalista, EPI, FER, MOB) + aba Recursos Extras
- Edição inline funcional com debounce; badge "⚠️ Divergência BCU" por item divergente
- Botão "Montar Histograma" em `ProposalDetailPage` (EDITOR/OWNER); badge "CPU desatualizada" visível
- `AlocacaoRecursoDialog`: abre da CpuTable; lista recursos extras da proposta; submete com `quantidade_consumo`
- **245+ pytest PASS, 0 FAIL**
- **0 erros `npx tsc --noEmit`**

## Plano

Arquivo: `docs/sprints/F2-11/plans/2026-04-27-histograma-proposta.md`

9 tasks:
1. Migration 024 + models
2. `HistogramaService` (montar, get, editar, divergências)
3. `PropostaRecursoExtraService` (CRUD + alocação)
4. Schemas + 8 endpoints em `propostas.py`
5. `cpu_custo_service`: prioridade proposta_pc_* + soma extras
6. `proposta_versionamento_service`: clonar histograma
7. Frontend API client (`histogramaApi.ts`)
8. Frontend UI (ProposalHistogramaPage + 4 componentes + detail page)
9. Validação final + walkthrough + technical-review + BACKLOG TESTED

## Pré-requisito de leitura (CRÍTICO — nesta ordem)

1. `docs/shared/governance/BACKLOG.md` — sprint F2-11 (escopo + critérios de aceite)
2. `docs/sprints/F2-10/technical-review/technical-review-2026-04-27-f2-10.md` — o que F2-10 entregou
3. `app/backend/models/bcu.py` — schema BCU global (referência para snapshot)
4. `app/backend/models/proposta.py` — campos atuais + `bcu_cabecalho_id`
5. `app/backend/services/cpu_custo_service.py` — lookup via De/Para (a estender)
6. `app/backend/services/cpu_geracao_service.py` — fluxo gerar_cpu
7. `app/backend/services/cpu_explosao_service.py` — explosão de composições
8. `app/backend/services/proposta_versionamento_service.py` — nova_versao (a estender)
9. `app/backend/services/bcu_de_para_service.py` — lookup BCU para BaseTcpo
10. `app/alembic/versions/023_bcu_unificada.py` — padrão de migration
11. `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` — onde entrar botão
12. `app/frontend/src/features/bcu/BcuPage.tsx` — referência visual para abas

## Atenções especiais (Gemini)

- **`montar_histograma` idempotente**: re-executar preserva linhas com `editado_manualmente=TRUE` (não sobrescreve edições do usuário). Apenas linhas não editadas são atualizadas com valores BCU frescos.
- **Encargos integrais**: copiar TODAS as linhas de `bcu.encargo_item` + `bcu.mobilizacao_item` do cabecalho ativo, independentemente das composições. Não filtrar.
- **`cpu_desatualizada` trigger**: implementar via evento SQLAlchemy (after_update/after_insert/after_delete) nos models `PropostaPcMaoObraItem`, `PropostaRecursoExtra`, `PropostaRecursoAlocacao` — ou via service explícito em cada mutação. O service é mais rastreável.
- **Divergência**: `GET /propostas/{id}/histograma` retorna flag `diverge_bcu: bool` por item — calculado via JOIN comparando `proposta_pc_*.valor_bcu_snapshot` com valor atual em `bcu.*` (por `bcu_item_id`). Não armazenar a divergência; calcular dinamicamente.
- **Clonagem em nova_versao**: clonar histograma como NOVA versão (novos UUIDs, novo `proposta_id`, `editado_manualmente` preservado, mas `valor_bcu_snapshot` recopiado do BCU atual — não da versão anterior).
- **AlocacaoRecursoDialog**: componente modal que abre da linha de composição em `CpuTable`. Carrega lista de `recurso_extra` da proposta; usuário digita `quantidade_consumo`; submit via `POST /propostas/{id}/composicoes/{composicao_id}/alocar-recurso`.
- **7 abas na ProposalHistogramaPage**: MO, EQP, Encargos Horista, Encargos Mensalista, EPI, FER, MOB. A aba "Recursos Extras" é a 8ª. Usar `HistogramaTabMaoObra` para MO (estrutura diferente) e `HistogramaTabGenerica` para EQP, EPI, FER (estrutura similar — reutilizar).
- **Testes 245+ PASS**: base é ~200 (F2-10). Adicionar ≥ 45:
  - `test_histograma_service.py`: 12+ testes
  - `test_proposta_recurso_extra_service.py`: 8+ testes
  - `test_histograma_endpoints.py`: 10+ testes
  - `test_cpu_custo_service.py`: +5 testes de prioridade
  - `test_proposta_versionamento_service.py`: +5 testes de clonagem

## Dependências

- **F2-10 DONE** ✅ (BCU schema, De/Para, cpu_custo_service refatorado — requerido)
- F2-09 DONE ✅ (versionamento — `nova_versao` a estender)
- F2-02 DONE ✅ (explosão de composições — `cpu_explosao_service`)
