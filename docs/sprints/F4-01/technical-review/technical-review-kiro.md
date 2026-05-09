# Technical Review — F4-01 Smart Import Architecture
**Revisor:** Kiro (design/spec reviewer)  
**Data:** 2026-05-08  
**Sprint:** F4-01 — Smart Import Architecture  
**Documento base:** `docs/analysis/SMART_IMPORT_ARCHITECTURE.md`

---

## 1. Resumo Executivo

A arquitetura proposta é sólida no princípio central — **entrada tolerante, núcleo rigoroso, banco protegido** — e está bem alinhada com a stack existente. O pipeline de 6 etapas (ingestão → normalização semântica → validação Pydantic → staging → revisão humana → commit transacional) é o padrão correto para este domínio.

Este parecer identifica **5 riscos materiais** e propõe ajustes pontuais sem alterar a arquitetura central.

---

## 2. Análise por Dimensão

### 2.1 Fluxo Adaptativo por Cliente (PQ)

**O que existe hoje:**  
`PqLayoutCliente` + `PqImportacaoMapeamento` já implementam mapeamento por cliente (migration 018). O `PqImportService` já consome esse layout via `_resolver_mapa_colunas`. O header detection no XLSX já faz varredura linha a linha até encontrar o cabeçalho.

**O que a arquitetura propõe adicionar:**  
Docling como extrator flexível + embeddings para mapeamento semântico com confidence score.

**Avaliação:**  
✅ A base de mapeamento por cliente está correta e deve ser preservada.  
✅ O confidence score (>85% auto, 50–85% warning, <50% manual) é um contrato de UX razoável.  
⚠️ **Risco 1 — Docling como dependência primária:** Docling é uma biblioteca pesada (modelos de layout de documento, OCR). Para PQs que são planilhas Excel estruturadas (não PDFs escaneados), o ganho sobre `openpyxl` + header detection heurístico é marginal e o custo de memória/latência é alto. Recomendo: Docling como **caminho alternativo** para PQs em PDF/imagem, não como substituto do parser Excel atual.  
⚠️ **Risco 2 — Feedback loop de sinônimos:** O documento propõe salvar mapeamentos confirmados como sinônimos prioritários. Isso é correto, mas precisa de um mecanismo de **invalidação**: se um cliente muda o layout da planilha, o sinônimo antigo pode mapear errado silenciosamente. O `PqLayoutCliente` já tem `updated_at` (via `TimestampMixin`) — o sistema deve comparar a data do layout com a data do último mapeamento confirmado.

**Recomendação:**  
Manter `PqLayoutCliente`/`PqImportacaoMapeamento` como camada de mapeamento persistente. Adicionar campo `confidence_score: float` e `origem_mapeamento: enum(ALIAS_FIXO, FUZZY, EMBEDDING, MANUAL)` em `PqImportacaoMapeamento` para rastreabilidade.

---

### 2.2 BASE/BCU — Importação Rígida

**O que existe hoje:**  
`bcu_service.py` já implementa parser rígido com `_find_col` por keyword, header detection nas primeiras 10 linhas, e upsert via `pg_insert(...).on_conflict_do_update`. O `BcuCabecalho` com `is_ativo` implementa soft-versioning.

**Avaliação:**  
✅ A rigidez está correta. BCU tem estrutura conhecida e controlada — não precisa de IA.  
✅ O padrão `is_ativo` + novo `BcuCabecalho` por importação é o equivalente ao "soft delete + nova revisão" proposto.  
⚠️ **Risco 3 — Ausência de staging para BCU:** O `bcu_service` grava diretamente nas tabelas `bcu.*` sem staging intermediário. Se uma importação BCU falhar no meio (ex: aba de equipamentos corrompida), as abas anteriores já foram gravadas. O `async with session.begin()` envolve toda a operação, mas o `_BATCH_SIZE = 500` com `pg_insert` em loop pode quebrar a atomicidade se houver exceção entre batches.

**Recomendação:**  
Verificar que todos os inserts BCU estão dentro de um único `session.begin()` (não múltiplos `begin` aninhados). Se não estiver, é um bug de atomicidade a corrigir antes de F4-01 avançar. Não é necessário staging completo para BCU — a transação única é suficiente, mas precisa ser garantida.

---

### 2.3 TCPO — Tolerância Controlada

**O que existe hoje:**  
`etl_service.py` implementa parser TCPO com header detection, mapeamento por keyword (`_CLASS_TO_TIPO`), e staging via `EtlPreview` (migration 025, token com TTL de 2h). O fluxo upload → preview → execute já existe.

**Avaliação:**  
✅ O modelo de staging com token é correto e já está implementado.  
✅ A separação parse (síncrono) / execute (assíncrono) é adequada.  
⚠️ **Risco 4 — TTL de 2h pode expirar durante revisão humana:** Se o usuário demora para revisar o preview (ex: planilha grande, múltiplas abas), o token expira e ele perde o trabalho. O TTL deve ser configurável por tipo de importação ou estendido automaticamente quando o usuário está ativo na tela de preview.  
⚠️ **Risco 5 — `EtlPreview.payload` como JSON sem schema:** O campo `payload: JSONB` armazena `{itens: [...], relacoes: [...], avisos: [...]}` sem validação de schema. Se o formato interno mudar entre versões, tokens antigos podem quebrar o execute. Recomendo versionar o payload: `{version: "1", itens: [...]}`.

**Recomendação:**  
Adicionar `ttl_horas: int` configurável no `EtlPreview` (ou via settings). Adicionar campo `payload_version: str` para compatibilidade futura.

---

### 2.4 Proteção do Banco — Validação Rígida

**O que existe hoje:**  
Pydantic valida schemas de entrada nas rotas. `bcu_service` usa `_to_decimal` com fallback `None`. `pq_import_service` usa `_parse_decimal` com `ValidationError` explícito.

**Avaliação:**  
✅ O princípio "LLM/Docling não grava no banco" está correto e deve ser contrato explícito.  
✅ A validação Pydantic por linha com captura de `ValidationError` e log de erros por linha é o padrão correto.  
⚠️ **Gap:** O `pq_import_service` atual grava itens com erro de quantidade como `linhas_com_erro` mas **não persiste o motivo do erro por linha**. O usuário vê "3 linhas com erro" mas não sabe quais linhas nem por quê. A arquitetura proposta corrige isso com `payload_staging: JSONB` — isso é uma melhoria necessária.

**Recomendação:**  
O modelo `ImportJob` proposto deve incluir `erros_por_linha: JSONB` com estrutura `[{linha: int, campo: str, motivo: str}]`. Isso é o mínimo para UX de preview útil.

---

### 2.5 Staging e Preview

**O que existe hoje:**  
`EtlPreview` para TCPO (token-based, TTL 2h). Para PQ, não há staging — a importação é direta.

**Avaliação:**  
✅ A proposta de unificar em `ImportJob` com status `PENDING → REVIEW_REQUIRED → COMPLETED/FAILED` é a evolução correta.  
⚠️ **Risco de migração:** Adicionar `ImportJob` requer migration 027. O `PqImportacao` existente (em `proposta.py`) tem estrutura similar mas sem staging. A migração deve ser aditiva — não alterar `PqImportacao` existente, criar `ImportJob` como entidade nova no schema `operacional`.

---

### 2.6 Auditoria e Rollback

**O que existe hoje:**  
`AuditoriaLog` com `tabela`, `registro_id`, `operacao`, `dados_anteriores`, `dados_novos`. Audit explícito nos services (não via hooks SQLAlchemy — decisão correta documentada em `audit_hooks.py`).

**Avaliação:**  
✅ O padrão de audit explícito é correto e deve ser mantido para importações.  
✅ O soft-delete via `is_ativo` em BCU e versioning em TCPO são os mecanismos de rollback corretos.  
⚠️ **Gap de auditoria em importações PQ:** `PqImportacao` não gera entrada em `AuditoriaLog`. Para rastreabilidade completa, o commit de uma importação PQ deve registrar `operacao=CREATE` com `dados_novos={importacao_id, arquivo, linhas, usuario_id}`.

**Recomendação:**  
Adicionar chamada explícita a `AuditoriaLog` no momento do commit de qualquer importação (PQ, BCU, TCPO). Não é necessário logar cada linha — apenas o evento de commit com metadados do job.

---

### 2.7 UX de Preview

**Avaliação:**  
✅ O fluxo proposto (grid com linhas verdes/vermelhas, edição inline, re-validação, confirmação) é o padrão correto para este tipo de importação.  
⚠️ **Gap de especificação:** O documento não especifica o contrato de API para o preview. O frontend precisa de:
- `GET /import-jobs/{id}/preview` → lista de linhas com status e erros
- `PATCH /import-jobs/{id}/preview/linha/{n}` → correção inline
- `POST /import-jobs/{id}/commit` → efetivação transacional

Esses endpoints precisam ser especificados antes da implementação para evitar retrabalho de contrato.

---

## 3. Riscos Consolidados

| # | Risco | Severidade | Mitigação |
|---|-------|-----------|-----------|
| 1 | Docling como dependência primária para Excel | Médio | Usar como caminho alternativo (PDF/imagem), não substituto |
| 2 | Feedback loop de sinônimos sem invalidação | Médio | Comparar `updated_at` do layout com data do mapeamento |
| 3 | Atomicidade BCU entre batches | Alto | Garantir único `session.begin()` envolvendo todos os batches |
| 4 | TTL de 2h expira durante revisão | Baixo | TTL configurável ou extensão automática |
| 5 | `EtlPreview.payload` sem versionamento | Baixo | Adicionar campo `payload_version` |

---

## 4. Riscos de Migração

A arquitetura proposta requer as seguintes migrations novas (após 026):

**Migration 027 — `import_job`**
```sql
-- Schema: operacional
-- Tabela: import_job
-- Campos mínimos:
--   id UUID PK
--   tipo_importacao ENUM(PQ, BCU, TCPO)
--   status ENUM(PENDING, REVIEW_REQUIRED, COMPLETED, FAILED)
--   cliente_id UUID FK → operacional.clientes
--   usuario_id UUID FK → operacional.usuarios
--   nome_arquivo VARCHAR(260)
--   mapping_metadata JSONB  -- scores e origem de cada coluna
--   erros_por_linha JSONB   -- [{linha, campo, motivo}]
--   criado_em TIMESTAMPTZ
--   atualizado_em TIMESTAMPTZ
--   expira_em TIMESTAMPTZ   -- para limpeza de jobs abandonados
```

**Requisitos de segurança da migration:**
- `down_revision` deve apontar para `026` (último revision confirmado)
- `downgrade()` deve fazer `DROP TABLE` limpo (sem dados de produção em risco — tabela nova)
- Não alterar tabelas existentes (`pq_importacao`, `etl_preview`, `bcu.*`) nesta migration
- Dados existentes em `etl_preview` não são afetados

**Não há migration de schema change em tabelas existentes nesta sprint** — apenas criação de tabela nova. Risco de rollback: baixo.

---

## 5. Recomendações de Implementação

### Ordem de execução sugerida

1. **Spike Docling** (isolado, sem tocar código de produção): validar se Docling agrega valor real para PQs em Excel vs. o parser atual. Resultado esperado: decisão go/no-go em 1 dia.

2. **Contrato `ImportJob`**: definir schema Pydantic e modelo SQLAlchemy antes de qualquer endpoint. Isso desbloqueia frontend e backend em paralelo.

3. **Migration 027**: criar tabela `import_job` com `down_revision = "026"`. Testar upgrade/downgrade em banco limpo.

4. **Adaptar `PqImportService`**: adicionar staging via `ImportJob` mantendo o fluxo atual como fallback (feature flag `SMART_IMPORT_ENABLED`).

5. **Confidence score**: implementar após o contrato estar estável. Não bloqueia o pipeline básico.

### Feature flag recomendada

```python
# app/backend/core/config.py
SMART_IMPORT_ENABLED: bool = False  # ativar por cliente via settings
```

Isso permite rollout gradual sem risco para importações existentes.

---

## 6. O que está correto e não deve ser alterado

- Princípio "LLM não grava no banco" — manter como contrato inviolável
- `PqLayoutCliente`/`PqImportacaoMapeamento` — base sólida, não refatorar
- Audit explícito nos services (não via hooks) — padrão correto
- `async with session.begin()` para commit transacional — manter
- `EtlPreview` com TTL — padrão correto, apenas tornar TTL configurável
- Separação de schemas (`referencia.*`, `bcu.*`, `operacional.*`) — preservar

---

## 7. Parecer Final

A arquitetura está **aprovada com ressalvas**. Os 5 riscos identificados são mitigáveis sem alterar o design central. O maior risco operacional é o **Risco 3** (atomicidade BCU) — deve ser verificado antes de qualquer nova implementação de importação. Os demais são riscos de produto/UX que podem ser endereçados incrementalmente.

A sprint F4-01 deve focar em:
1. Spike Docling (go/no-go)
2. Contrato `ImportJob` + migration 027
3. Verificação de atomicidade BCU

Implementação completa do Smart Mapper com embeddings é escopo de sprint subsequente (F4-02 ou F4-03).
