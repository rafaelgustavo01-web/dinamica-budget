# Walkthrough — F4-01 Smart Import Architecture
**Autor:** Kiro  
**Data:** 2026-05-08  
**Audiência:** time de produto e engenharia

---

## O que foi revisado

A arquitetura Smart Import proposta em `docs/analysis/SMART_IMPORT_ARCHITECTURE.md` e o plano de sprint em `docs/sprints/F4-01/plans/`. A revisão cobriu o código existente relevante: `pq_import_service.py`, `etl_service.py`, `bcu_service.py`, modelos `EtlPreview`, `PqLayoutCliente`, `BcuCabecalho`, `AuditoriaLog`, e as 27 migrations existentes (001–026).

---

## O que já existe e funciona

O projeto já tem mais infraestrutura de importação do que o documento de arquitetura sugere:

- **PQ por cliente**: `PqLayoutCliente` + `PqImportacaoMapeamento` (migration 018) já permitem mapeamento de colunas por cliente. O `PqImportService` já consome esse layout.
- **Header detection**: o parser XLSX já varre linha a linha até encontrar o cabeçalho — não assume linha 1.
- **Staging TCPO**: `EtlPreview` (migration 025) já implementa o padrão token → preview → execute com TTL de 2h.
- **Soft versioning BCU**: `BcuCabecalho.is_ativo` já implementa o conceito de "nova revisão sem destruir a anterior".
- **Audit explícito**: `AuditoriaLog` com padrão de escrita explícita nos services (não via hooks SQLAlchemy).

A arquitetura proposta é uma **evolução** do que existe, não uma reescrita.

---

## O que a arquitetura adiciona de novo

1. **`ImportJob` unificado**: entidade única para PQ, BCU e TCPO com status, erros por linha, e metadados de mapeamento. Hoje cada tipo tem seu próprio mecanismo.

2. **Confidence score**: classificação automática de mapeamentos (>85% auto, 50–85% warning, <50% manual). Hoje o mapeamento é binário (encontrou ou não encontrou).

3. **Docling**: extrator flexível para PQs em formatos não-Excel (PDF, imagem). Hoje só Excel/CSV.

4. **Feedback loop**: mapeamentos confirmados pelo usuário viram sinônimos prioritários. Hoje o layout por cliente é estático (editado manualmente).

---

## Os 5 riscos identificados

**Risco 3 é o único de alta severidade**: o `bcu_service` faz inserts em batches de 500 dentro de um loop. Se a sessão SQLAlchemy não estiver envolvendo todos os batches em um único `begin()`, uma falha no meio da importação pode deixar o banco em estado parcial. Isso precisa ser verificado antes de qualquer nova implementação de importação.

Os outros 4 riscos são de severidade média/baixa e estão detalhados no technical review.

---

## Decisões de produto que precisam ser tomadas antes da implementação

**1. Docling: go ou no-go para Excel?**  
O spike deve responder: Docling agrega valor real para PQs em `.xlsx` comparado ao parser atual? Se não, Docling fica restrito a PDF/imagem. Essa decisão impacta a dependência de memória do container.

**2. Contrato de API do preview**  
O frontend precisa de 3 endpoints definidos antes de começar:
- `GET /import-jobs/{id}/preview` — lista linhas com status e erros
- `PATCH /import-jobs/{id}/preview/linha/{n}` — correção inline
- `POST /import-jobs/{id}/commit` — efetivação

Sem esse contrato, frontend e backend vão trabalhar em paralelo e divergir.

**3. Feature flag por cliente ou global?**  
O Smart Import deve ser ativado por cliente (rollout gradual) ou globalmente? Recomendo por cliente inicialmente.

---

## O que a sprint F4-01 deve entregar

Dado o escopo de "arquitetura e spike técnico" (briefing), os entregáveis concretos são:

| Entregável | Tipo | Risco |
|-----------|------|-------|
| Spike Docling (go/no-go) | Código isolado | Baixo |
| Schema `ImportJob` (Pydantic + SQLAlchemy) | Código | Baixo |
| Migration 027 com upgrade/downgrade testados | Migration | Baixo |
| Verificação de atomicidade BCU | Análise/fix | Alto se bug confirmado |
| Contrato de API preview (OpenAPI spec) | Documento | Nenhum |

O Smart Mapper com embeddings e o feedback loop são escopo de sprint subsequente.

---

## Linha do tempo sugerida

```
Dia 1: Spike Docling + verificação atomicidade BCU
Dia 2: Schema ImportJob + migration 027
Dia 3: Contrato de API preview + feature flag
Dia 4: Testes migration (upgrade/downgrade) + documentação
```

---

## Referências

- `docs/analysis/SMART_IMPORT_ARCHITECTURE.md` — documento base
- `app/backend/services/pq_import_service.py` — importador PQ atual
- `app/backend/services/etl_service.py` — importador TCPO atual
- `app/backend/services/bcu_service.py` — importador BCU atual
- `app/alembic/versions/025_etl_preview_table.py` — staging TCPO
- `app/alembic/versions/026_item_codigo_autogerado.py` — último revision (026)
- `docs/sprints/F4-01/technical-review/technical-review-kiro.md` — parecer completo
