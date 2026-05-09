# Walkthrough — F4-02 PQ Client Profiles + Learning Loop

## Sprint
- **ID:** F4-02
- **Objetivo:** Implementar perfis de importação de PQ por cliente com preview, score de confiança e aprendizado controlado.
- **Data:** 2026-05-08
- **Worker:** Kimi (hardening/review backend)

---

## 1. Contexto

O importador de PQ já possuía `PqLayoutCliente` + `PqImportacaoMapeamento` (migration 018), mas:
- Não havia preview antes de gravar.
- Não havia score de confiança do mapeamento.
- Não respeitava `aba_nome` nem `linha_inicio` do layout.
- Não havia mecanismo de aprovação humana nem audit trail.

---

## 2. Passos de Implementação

### 2.1 Migration Alembic 027
**Arquivo:** `app/alembic/versions/027_pq_client_profile_learning.py`

```bash
# Criar migration manualmente (não usamos autogenerate para evitar race de enums)
```

- Adicionadas colunas à `pq_layout_cliente`:
  - `is_aprovado` (bool, default false)
  - `aprovado_por_id` (FK usuarios)
  - `aprovado_em` (timestamptz)
  - `aliases_json` (text)
  - `score_confianca` (numeric 5,4)
  - Índice composto `(cliente_id, is_aprovado)`
- Criada tabela `pq_layout_historico` com FKs e índices.
- **Validação:**
  ```bash
  sudo -u postgres DATABASE_URL="postgresql+psycopg2://postgres@/dinamica_budget_test_f4_02" alembic upgrade 027
  sudo -u postgres DATABASE_URL="postgresql+psycopg2://postgres@/dinamica_budget_test_f4_02" alembic downgrade 026
  ```

### 2.2 Models
**Arquivo:** `app/backend/models/pq_layout.py`

- `PqLayoutCliente` atualizado com campos de perfil.
- `PqLayoutHistorico` criada.
- Adicionada ao `models/__init__.py`.

### 2.3 Schemas
**Arquivo:** `app/backend/schemas/pq_layout.py`

- `PqLayoutResponse` expandido.
- Novos schemas: `PqPreviewResponse`, `PqPreviewItem`, `PqLayoutHistoricoResponse`, `PqLayoutAprovarRequest`.

### 2.4 Repository
**Arquivo:** `app/backend/repositories/pq_layout_repository.py`

- `aprovar(layout, usuario_id)` — atualiza flags e timestamp.
- `registrar_historico(entry)` — insere audit trail.
- `list_historico_by_layout(layout_id)` — ordenado por created_at DESC.

### 2.5 PqLayoutService
**Arquivo:** `app/backend/services/pq_layout_service.py`

- `criar_ou_substituir` agora grava histórico `CRIADO`.
- `aprovar` grava histórico `APROVADO`.
- `sugerir_mapeamento(headers)` usa aliases conhecidos para inferir colunas.
- `calcular_score(headers, layout)` — percentual de colunas do layout encontradas.

### 2.6 PqImportService
**Arquivo:** `app/backend/services/pq_import_service.py`

- Refatorado `_parse_contents`, `_parse_csv`, `_parse_xlsx` para aceitar `layout: PqLayoutCliente | None`.
- XLSX: usa `workbook[aba_nome]` e respeita `linha_inicio` na busca do cabeçalho.
- CSV: pula linhas de dados conforme `linha_inicio`.
- `preview_planilha` — parseia e retorna dict com `score_confianca`, `linhas_ok`, `linhas_com_erro`, `itens`.
- `importar_planilha` — comportamento preservado; score é calculado internamente mas não persistido na importação (pode ser evoluído futuramente).

### 2.7 Endpoints

#### PQ Layout (`app/backend/api/v1/endpoints/pq_layout.py`)
- `PUT /clientes/{id}/pq-layout` — criar/substituir (inalterado, exceto schema expandido).
- `GET /clientes/{id}/pq-layout` — obter (inalterado).
- `POST /clientes/{id}/pq-layout/aprovar` — aprova perfil.
- `POST /clientes/{id}/pq-layout/sugerir` — upload de arquivo amostra → sugestão de mapeamento.
- `GET /clientes/{id}/pq-layout/historico` — audit trail.

#### PQ Importação (`app/backend/api/v1/endpoints/pq_importacao.py`)
- `POST /propostas/{id}/pq/preview` — preview sem gravar.
- `POST /propostas/{id}/pq/importar` — importação existente (mantida).

### 2.8 Testes

#### PqLayoutService
```bash
pytest backend/tests/unit/test_pq_layout_service.py -v
# 13 passed
```

#### PqImportService
```bash
pytest backend/tests/unit/test_pq_import_service.py -v
# 7 passed
```

Total: **20 testes unitários novos**, todos passando.

---

## 3. Fluxo de Uso (Exemplo)

### 3.1 Primeira importação de um cliente
1. Usuário faz upload de uma planilha PQ.
2. Frontend chama `POST /preview` → recebe lista de itens + score.
3. Se score baixo, usuário ajusta mapeamento e salva layout via `PUT /pq-layout`.
4. Admin aprova o layout via `POST /pq-layout/aprovar`.
5. Próxima importação do mesmo cliente reaproveita o layout aprovado com score alto.

### 3.2 Correção humana vira aprendizado
1. Usuário corrige mapeamento durante importação.
2. Nova configuração é salva como layout e aprovada.
3. `pq_layout_historico` registra `CRIADO` e `APROVADO`.
4. Nenhuma atualização automática ocorre sem aprovação explícita.

---

## 4. Decisões Técnicas

| Decisão | Justificativa |
|---------|---------------|
| Preview em memória (sem tabela staging) | Menor superfície de schema; zero risco de dados órfãos |
| `aliases_json` como TEXT em vez de JSONB | Migration mais simples; parse em Python com fallback seguro |
| Score baseado apenas no cabeçalho | MVP suficiente; score de dados exigiria análise de conteúdo |
| Histórico separado (`pq_layout_historico`) | Audit trail imutável; não polui a tabela principal |
| `linha_inicio` no CSV pula linhas após header | Alinhado ao comportamento do Excel; consistente com expectativa do usuário |

---

## 5. Artefatos Entregues

- `docs/sprints/F4-02/technical-review/technical-review-2026-05-08-f4-02.md`
- `docs/sprints/F4-02/walkthrough/done/walkthrough-F4-02.md`
- Diff local na worktree (branch `f4-02-kimi`)

---

## 6. Próximos Passos (QA / PO)

1. QA valida migration 027 em ambiente de staging.
2. QA executa smoke test: preview → aprovar → importar com layout.
3. PO decide se score de confiança deve ter threshold para bloquear importação automática.
4. Após QA aceitar, mover BACKLOG → TESTED → DONE.
