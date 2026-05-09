# Technical Review — F4-02 PQ Client Profiles + Learning Loop

## Data: 2026-05-08
## Worker: Kimi (hardening/review backend)
## Branch/Worktree: /tmp/db-f4-02-kimi (f4-02-kimi)

---

## 1. Resumo da Implementação

Esta sprint evolui o importador de PQ (Planilha de Quantidades) de um mapeamento estático de colunas por cliente para um **perfil de importação aprovado**, com:

- **Score de confiança** ao aplicar um layout sobre um arquivo.
- **Preview antes de gravar** — endpoint `/preview` que parseia o arquivo sem persistir dados.
- **Respeito a `aba_nome` e `linha_inicio`** do layout no parser CSV/XLSX.
- **Learning loop auditável** — tabela `pq_layout_historico` registra criação, alteração e aprovação de perfis.
- **Aprovação controlada por humano** — campo `is_aprovado` + `aprovado_por_id` + `aprovado_em`.

---

## 2. Schema Change — Migration 027

**Arquivo:** `app/alembic/versions/027_pq_client_profile_learning.py`

### Alterações
- `pq_layout_cliente`:
  - `is_aprovado` (bool, NOT NULL, default=false)
  - `aprovado_por_id` (UUID, FK → usuarios.id, ON DELETE SET NULL)
  - `aprovado_em` (timestamptz, nullable)
  - `aliases_json` (text, nullable) — aliases extras por campo
  - `score_confianca` (numeric(5,4), nullable)
  - Índice `ix_pq_layout_cliente_aprovado` (cliente_id, is_aprovado)
- Nova tabela `pq_layout_historico`:
  - FKs com CASCADE/SET NULL apropriados
  - Coluna `acao` (varchar 20) para auditoria
  - `detalhe_json` para snapshot imutável
  - Índices em `layout_id` e `cliente_id`

### Segurança da Migration
- **down_revision = "026"** — encadeamento correto.
- Todas as colunas novas são **nullable** ou têm **server_default**, preservando dados existentes.
- `upgrade` usa `op.add_column` / `op.create_table` — idempotente na ordem canônica.
- `downgrade` dropa na ordem inversa: tabela → índice → colunas.
- **Validação prática:**
  - `alembic upgrade 027` aplicada em banco PostgreSQL de teste criado do zero → sucesso.
  - `alembic downgrade 026` reverteu sem erros.
  - Conferido via `\d` que colunas e tabela foram removidas.

---

## 3. Models

**Arquivo:** `app/backend/models/pq_layout.py`

- `PqLayoutCliente` ganhou os campos de perfil aprovado e relacionamento `historico` (1:N).
- `PqLayoutHistorico` criada com `server_default=sa.func.now()` em `created_at`.
- Import de `Decimal` e `sa` adicionados; sem quebra de backward compatibility.
- `PqLayoutHistorico` registrado em `models/__init__.py` para autogenerate/metadados.

---

## 4. Services

### 4.1 PqLayoutService (`app/backend/services/pq_layout_service.py`)

- `criar_ou_substituir`: agora inicializa `is_aprovado=False` e grava histórico `CRIADO`.
- `aprovar(layout_id, usuario_id)`: marca perfil como aprovado e registra histórico `APROVADO`.
- `sugerir_mapeamento(headers)`: inferência por aliases conhecidos (reaproveitando `_HEADER_ALIASES`).
- `calcular_score(headers, layout)`: razão de colunas do layout encontradas no arquivo.
- `listar_historico`: audit trail por layout.

### 4.2 PqImportService (`app/backend/services/pq_import_service.py`)

- **Preview transacionalmente seguro**: `preview_planilha` parseia o arquivo em memória, não grava `PqImportacao` nem `PqItem`.
- **Score no preview**: calculado a partir do cabeçalho real do arquivo vs. mapeamentos do layout.
- **Respeito a layout**:
  - XLSX: usa `workbook[aba_nome]` quando configurado; senão `workbook.active`.
  - XLSX: `linha_inicio` define a partir de qual linha procurar o cabeçalho.
  - CSV: `linha_inicio` controla quantas linhas de dados pular após o header.
- **Importação existente** (`importar_planilha`) mantém a mesma assinatura pública; comportamento preservado quando não há layout.

### 4.3 Transações

- O importador continua operando dentro da sessão do request (`get_db`), que faz commit/rollback no boundary.
- Nenhum `db.commit()` foi adicionado nos novos services — o endpoint `pq_layout.py` PUT pré-existente ainda faz commit explícito (não alterado para minimizar regressão).
- O preview **nunca** chama `repo.create/update`, portanto não produz efeitos colaterais no banco mesmo se a sessão for commitada posteriormente.

---

## 5. Endpoints

**Arquivos:**
- `app/backend/api/v1/endpoints/pq_layout.py`
- `app/backend/api/v1/endpoints/pq_importacao.py`

### Novos endpoints

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/propostas/{id}/pq/preview` | Preview de importação sem gravar |
| POST | `/clientes/{id}/pq-layout/aprovar` | Aprova perfil do cliente |
| POST | `/clientes/{id}/pq-layout/sugerir` | Sugere mapeamento a partir de arquivo |
| GET | `/clientes/{id}/pq-layout/historico` | Lista audit trail do perfil |

### Segurança
- `/preview` e `/importar` requerem `PropostaPapel.EDITOR` via `require_proposta_role`.
- `/aprovar` requer `get_current_admin_user`.
- `/sugerir` e `/historico` requerem `get_current_active_user`.

---

## 6. Schemas Pydantic

**Arquivo:** `app/backend/schemas/pq_layout.py`

- `PqLayoutCriarRequest` ganhou `aliases_json` opcional.
- `PqLayoutResponse` ganhou `is_aprovado`, `aprovado_por_id`, `aprovado_em`, `aliases_json`, `score_confianca`.
- Novos schemas:
  - `PqPreviewItem` / `PqPreviewResponse` — resposta do preview.
  - `PqLayoutAprovarRequest` — body vazio (placeholder para extensão futura).
  - `PqLayoutHistoricoResponse` — audit trail.

Validações existentes preservadas:
- `campos_obrigatorios` em `PqLayoutCriarRequest` continua exigindo DESCRICAO, QUANTIDADE, UNIDADE.

---

## 7. Testes

### 7.1 Unitários — PqLayoutService
**Arquivo:** `app/backend/tests/unit/test_pq_layout_service.py`

- 13 testes cobrindo:
  - Criar/substituir layout com `is_aprovado=False`.
  - Aprovação grava histórico.
  - NotFound em layout inexistente.
  - Sugestão de mapeamento por aliases.
  - Score 100%, 0%, sem layout.

### 7.2 Unitários — PqImportService
**Arquivo:** `app/backend/tests/unit/test_pq_import_service.py`

- 7 testes cobrindo:
  - Preview retorna dados sem gravar no banco.
  - Preview com layout retorna score.
  - Importação CSV respeita `linha_inicio`.
  - Importação XLSX respeita `aba_nome`.
  - Regressão: aliases de coluna, extensão rejeitada.

### 7.3 Execução

```bash
pytest backend/tests/unit/test_pq_layout_service.py backend/tests/unit/test_pq_import_service.py -v
# 20 passed, 1 warning in 0.59s
```

Suite completa de unitários:
```bash
pytest backend/tests/unit/ -v
# 211 passed, 1 failed, 12 errors
```

A falha (`test_security_s04.py::test_list_servicos_validates_cliente_id_access_when_present`) e os erros (BCU/Histograma) são **pré-existentes** e não relacionados a esta sprint — não há alteração nos arquivos `servicos.py`, `bcu_service.py` ou `histograma_service.py`.

### 7.4 Migration
- Validado `upgrade 027` e `downgrade 026` em PostgreSQL 16 de teste.

---

## 8. Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Migration com default `false` em `is_aprovado` deixa perfis legados como não aprovados | Esperado — perfis antigos devem ser explicitamente aprovados pelo admin |
| `aliases_json` é texto livre; JSON malformado pode causar erro no parse | Service usa `try/except json.JSONDecodeError`; falha silenciosa não quebra o score |
| Preview calcula score apenas no cabeçalho, não no conteúdo das células | Aceitável para MVP — score de layout é semântico de colunas, não de dados |
| `linha_inicio` em CSV pode ser confuso (linha 1 = header, linha 2 = primeira dados) | Documentado no walkthrough; comportamento alinhado ao Excel |
| Endpoint `/sugerir` lê arquivo inteiro em memória | Aceitável para header row (primeira linha apenas) |

---

## 9. Checklist de Aceite

- [x] Migration reversível (upgrade/downgrade validados)
- [x] Dados existentes preservados (colunas nullable/default)
- [x] Preview antes de gravar
- [x] Score de confiança calculado
- [x] Aprovação humana obrigatória (`is_aprovado`)
- [x] Histórico de auditoria (`pq_layout_historico`)
- [x] Testes unitários novos passando (20/20)
- [x] Regressão unitária não introduziu novas falhas nos módulos PQ
- [x] Nenhum segredo em fixtures ou docs
- [x] Sem alteração em `docs/audits/`

---

## 10. Diff Resumido

```
app/alembic/versions/027_pq_client_profile_learning.py   (new)
app/backend/models/__init__.py                            (+PqLayoutHistorico)
app/backend/models/pq_layout.py                           (+campos perfil, +PqLayoutHistorico)
app/backend/schemas/pq_layout.py                          (+preview/historico/aliases)
app/backend/repositories/pq_layout_repository.py          (+aprovar, registrar_historico, list_historico)
app/backend/services/pq_layout_service.py                 (+aprovar, sugerir, calcular_score, historico)
app/backend/services/pq_import_service.py                 (+preview, score, aba/linha)
app/backend/api/v1/endpoints/pq_layout.py                 (+aprovar, sugerir, historico)
app/backend/api/v1/endpoints/pq_importacao.py             (+preview)
app/backend/tests/unit/test_pq_layout_service.py          (+6 testes)
app/backend/tests/unit/test_pq_import_service.py          (+4 testes)
docs/sprints/F4-02/technical-review/...                   (new)
docs/sprints/F4-02/walkthrough/done/...                   (new)
```

---

**Parecer:** Aprovado para QA. Migration segura, preview transacionalmente inofensivo, learning loop auditável.
