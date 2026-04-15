# Dinamica Budget — Backend API

> **Sistema de orçamentação de obras on-premise** que substitui processos manuais de copy/paste em planilhas Excel por uma API centralizada com motor de busca inteligente em cascata de 4 fases.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Stack Tecnológica](#stack-tecnológica)
- [Arquitetura](#arquitetura)
- [Modelo de Dados](#modelo-de-dados)
- [Motor de Busca em Cascata (4 Fases)](#motor-de-busca-em-cascata-4-fases)
- [Endpoints da API](#endpoints-da-api)
- [Autenticação e RBAC](#autenticação-e-rbac)
- [Fluxo de Homologação](#fluxo-de-homologação)
- [Sistema de Auditoria](#sistema-de-auditoria)
- [Módulos ML (On-Premise)](#módulos-ml-on-premise)
- [Migrations Alembic](#migrations-alembic)
- [Ferramentas de Banco de Dados](#ferramentas-de-banco-de-dados)
- [Setup e Instalação](#setup-e-instalação)
- [Deploy Automatizado — Windows Server](#deploy-automatizado--windows-server)
- [Scripts de Operação](#scripts-de-operação)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Regras de Segurança e Governança](#regras-de-segurança-e-governança)
- [Correções Sprint 1 (P0/P1)](#correções-sprint-1-p0p1)
- [Riscos Técnicos e Mitigações](#riscos-técnicos-e-mitigações)

---

## Visão Geral

O **Dinamica Budget** é uma aplicação backend on-premise para empresas de construção civil que precisam:

- **Buscar serviços TCPO** a partir de texto livre (ex: "escavação manual solo argiloso")
- **Gerenciar itens próprios** (PROPRIA) por cliente, com fluxo de homologação obrigatório
- **Aprender com confirmações** do usuário via associações inteligentes que se consolidam com o tempo
- **Explodir composições TCPO** (estrutura pai-filho com insumos, horas, materiais)
- **Registrar histórico** de buscas por cliente com rastreabilidade real (id retornado na resposta)
- **Auditar alterações** de preço e status com log rastreável por usuário e cliente
- **Isolar dados** por cliente com RBAC por vínculo (nenhum dado de um cliente vaza para outro)

A solução é totalmente **on-premise**: nenhum dado sai da rede interna. O modelo de linguagem (`all-MiniLM-L6-v2`) roda localmente via `sentence-transformers`.

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Framework Web | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async + asyncpg) |
| Banco de Dados | PostgreSQL 16 |
| Busca Vetorial | pgvector 0.8.0 (HNSW, Vector(384)) |
| Busca Fuzzy | pg_trgm + GIN index |
| Embeddings | Sentence Transformers `all-MiniLM-L6-v2` (on-premise) |
| Autenticação | JWT (access 30min + refresh 7 dias) |
| Migrações | Alembic — 11 migrations |
| Logging | structlog (JSON estruturado) |
| Validação | Pydantic v2 |
| Serviço Windows | NSSM (Non-Sucking Service Manager) |
| Servidor Web | IIS 10 + ARR 3.0 + URL Rewrite 2.1 (reverse proxy) |
| Frontend | React + Vite 6 + TypeScript (build estático servido pelo IIS) |
| Container | Docker + Docker Compose (dev/staging) |
| Deploy | `deploy-dinamica.bat` — instalador nativo Windows Server |
| Dev DB (CLI) | pgcli 4.4.0 — autocomplete, syntax highlight, aliases |
| Dev DB (GUI) | HeidiSQL — nativo Win32, leve, open-source (GPL) |

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                         FastAPI App                              │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌────────────────────┐   │
│  │  auth.py    │   │  busca.py    │   │  homologacao.py    │   │
│  │  /login     │   │  /servicos   │   │  /pendentes        │   │
│  │  /refresh   │   │  /associar   │   │  /aprovar          │   │
│  │  /me        │   │              │   │  /itens-proprios   │   │
│  └─────────────┘   └──────┬───────┘   └────────┬───────────┘   │
│                            │  RBAC check        │  RBAC check   │
│                   ┌────────▼────────┐           │               │
│                   │  busca_service  │           │               │
│                   │  (4 fases)      │           │               │
│                   └────────┬────────┘           │               │
│          ┌─────────────────┼──────────┐         │               │
│          ▼                 ▼          ▼         ▼               │
│  ┌───────────────┐ ┌────────────┐ ┌──────────────────────────┐ │
│  │ assoc_repo    │ │servico_repo│ │ homologacao_service       │ │
│  │ (fase 0+1)    │ │ (fase 2)   │ │ + auditoria_log explícita│ │
│  └───────────────┘ └────────────┘ └──────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
           │                │
           ▼                ▼
┌──────────────────────────────────────────────────────────────────┐
│                        PostgreSQL 16                             │
│  associacao_inteligente  servico_tcpo + pg_trgm  tcpo_embeddings │
│  historico_busca_cliente  auditoria_log  usuario_perfil          │
└──────────────────────────────────────────────────────────────────┘
```

### Estrutura de Pastas

```
dinamica-budget/
├── app/
│   ├── main.py
│   ├── api/v1/
│   │   ├── router.py
│   │   └── endpoints/
│   │       ├── auth.py          # login (JSON), token (OAuth2), refresh, me, create_usuario
│   │       ├── busca.py         # /servicos (4 fases), /associar, /associacoes (list/delete)
│   │       ├── servicos.py      # catálogo + composição (POST admin-only)
│   │       ├── homologacao.py   # pendentes, aprovar, itens-proprios
│   │       ├── usuarios.py      # CRUD usuários + perfis-cliente (admin)
│   │       ├── clientes.py      # list + create clientes (admin)
│   │       └── admin.py         # compute-embeddings
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── dependencies.py      # get_db, get_current_user, require_cliente_access/perfil
│   │   ├── audit_hooks.py       # stub (auditoria feita explicitamente nos services)
│   │   ├── logging.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── enums.py             # todos os enums centralizados
│   │   ├── base.py
│   │   ├── usuario.py           # + UsuarioPerfil (RBAC)
│   │   ├── cliente.py
│   │   ├── categoria_recurso.py
│   │   ├── servico_tcpo.py      # catálogo híbrido (TCPO + PROPRIA)
│   │   ├── composicao_tcpo.py
│   │   ├── tcpo_embeddings.py
│   │   ├── historico_busca_cliente.py  # usuario_id FK real
│   │   ├── associacao_inteligente.py   # substitui associacao_tcpo
│   │   └── auditoria_log.py            # usuario_id + cliente_id FK
│   ├── schemas/
│   │   ├── common.py
│   │   ├── auth.py              # + MeResponse com perfis
│   │   ├── busca.py             # BuscaMetadados tipado (não dict)
│   │   ├── servico.py
│   │   ├── homologacao.py
│   │   ├── usuario.py           # UsuarioAdminResponse, UsuarioPatch, perfis
│   │   ├── cliente.py           # ClienteCreate, ClienteResponse
│   │   └── associacao.py        # AssociacaoListItem
│   ├── services/
│   │   ├── busca_service.py     # histórico síncrono + validação de rastreabilidade
│   │   ├── auth_service.py
│   │   ├── homologacao_service.py  # ownership guard + auditoria explícita
│   │   ├── associacao_service.py
│   │   ├── servico_catalog_service.py  # list scoped + restrict create
│   │   └── embedding_sync_service.py
│   ├── repositories/
│   │   ├── base_repository.py
│   │   ├── usuario_repository.py
│   │   ├── cliente_repository.py
│   │   ├── servico_tcpo_repository.py   # + list_catalogo_visivel
│   │   ├── tcpo_embeddings_repository.py
│   │   ├── historico_repository.py      # create com usuario_id + get_by_id_and_cliente
│   │   └── associacao_repository.py
│   └── ml/
│       ├── embedder.py
│       ├── vector_search.py
│       └── fuzzy_search.py
├── alembic/versions/
│   ├── 001_create_base_tables.py
│   ├── 002_pgvector_extension.py
│   ├── 003_tcpo_embeddings_table.py
│   ├── 004_pgtrgm_and_gin_index.py
│   ├── 005_v2_governance_rbac_audit.py
│   └── 006_consolidation_fixes.py      # usuario_id FK historico + auditoria_log FKs
├── requirements.txt
├── .env.example
└── docker-compose.yml
```

---

## Modelo de Dados

### `usuarios`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | v4 |
| nome | VARCHAR(200) | NOT NULL |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| hashed_password | VARCHAR(255) | NOT NULL |
| refresh_token_hash | VARCHAR(255) | nullable, para revogação |
| external_id_ad | VARCHAR(255) | UNIQUE, nullable (AD/LDAP) |
| is_active | BOOLEAN | DEFAULT TRUE |
| is_admin | BOOLEAN | DEFAULT FALSE, bypass global |
| created_at / updated_at | TIMESTAMP | |

### `usuario_perfil` (RBAC por cliente)
| Campo | Tipo | Notas |
|---|---|---|
| usuario_id | UUID (PK, FK) | → usuarios.id |
| cliente_id | UUID (PK, FK) | → clientes.id |
| perfil | VARCHAR(50) (PK) | USUARIO / APROVADOR / ADMIN |

### `clientes`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | v4 |
| nome_fantasia | VARCHAR(255) | NOT NULL |
| cnpj | VARCHAR(14) | UNIQUE, NOT NULL |
| created_at | TIMESTAMP | |
| is_active | BOOLEAN | DEFAULT TRUE |

### `categoria_recurso`
| Campo | Tipo | Notas |
|---|---|---|
| id | INT (PK) | |
| descricao | VARCHAR(100) | NOT NULL |
| tipo_custo | ENUM | HORISTA / MENSALISTA / GLOBAL |

### `servico_tcpo` (catálogo híbrido central)
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | v4 |
| cliente_id | UUID (FK, nullable) | NULL = item global TCPO |
| codigo_origem | VARCHAR(50) | NOT NULL, INDEX |
| descricao | TEXT | NOT NULL, GIN index (pg_trgm) |
| unidade_medida | VARCHAR(20) | NOT NULL |
| custo_unitario | DECIMAL(15,4) | NOT NULL |
| categoria_id | INT (FK) | → categoria_recurso.id |
| origem | ENUM | `TCPO` / `PROPRIA` |
| status_homologacao | ENUM | `PENDENTE` / `APROVADO` / `REPROVADO` |
| aprovado_por_id | UUID (FK, nullable) | → usuarios.id |
| data_aprovacao | TIMESTAMP | nullable |
| deleted_at | TIMESTAMP | nullable, soft delete |
| created_at / updated_at | TIMESTAMP | |

> Itens TCPO globais: `cliente_id = NULL`, `origem = TCPO`, `status = APROVADO`.
> Itens do cliente: `cliente_id` obrigatório, `origem = PROPRIA`, nascem como `status = PENDENTE`.

### `composicao_tcpo` (explosão pai-filho)
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | v4 |
| servico_pai_id | UUID (FK) | → servico_tcpo.id, INDEX |
| insumo_filho_id | UUID (FK) | → servico_tcpo.id |
| quantidade_consumo | DECIMAL(10,4) | NOT NULL |

> INSERT protegido por validação DFS anti-loop. Custo pai PROPRIA recalculado automaticamente quando custo filho muda.

### `historico_busca_cliente`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | v4 |
| cliente_id | UUID (FK) | → clientes.id, INDEX |
| usuario_id | UUID (FK) | → usuarios.id, INDEX |
| texto_busca | TEXT | NOT NULL |
| criado_em | TIMESTAMP | server_default=now() |

> O `id` real desta linha é retornado em `metadados.id_historico_busca` na resposta da busca.
> Ao criar uma associação, o `id_historico_busca` é validado: deve existir e pertencer ao mesmo `cliente_id`.

### `associacao_inteligente`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | v4 |
| cliente_id | UUID (FK) | → clientes.id, INDEX |
| texto_busca_normalizado | VARCHAR(255) | INDEX composto com cliente_id |
| servico_tcpo_id | UUID (FK) | → servico_tcpo.id |
| origem_associacao | ENUM | `MANUAL_USUARIO` / `IA_CONSOLIDADA` |
| confiabilidade_score | DECIMAL(3,2) | nullable |
| frequencia_uso | INT | DEFAULT 1 |
| status_validacao | ENUM | `SUGERIDA` → `VALIDADA` → `CONSOLIDADA` |
| created_at / updated_at | TIMESTAMP | |

> Substitui `associacao_tcpo` (removido). `CONSOLIDADA` (≥3 confirmações) = circuit break na Fase 1.

### `tcpo_embeddings` (pgvector)
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (FK = PK) | = servico_tcpo.id (1:1) |
| vetor | Vector(384) | all-MiniLM-L6-v2 |
| metadata | JSONB | `{descricao, categoria_id}` |

> Índice HNSW: `m=16, ef_construction=64, vector_cosine_ops`

### `auditoria_log`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID (PK) | v4 |
| tabela | VARCHAR(100) | INDEX |
| registro_id | VARCHAR(36) | UUID como string, INDEX |
| operacao | ENUM | `CREATE` / `UPDATE` / `DELETE` / `APROVAR` / `REPROVAR` |
| campo_alterado | VARCHAR(100) | nullable |
| dados_anteriores | JSONB | snapshot antes |
| dados_novos | JSONB | snapshot depois |
| usuario_id | UUID (FK, nullable) | → usuarios.id — **quem fez** |
| cliente_id | UUID (FK, nullable) | → clientes.id — **em qual cliente** |
| criado_em | TIMESTAMP | server_default=now(), INDEX |

> Log imutável. Registros criados explicitamente nos services (não via hooks SQLAlchemy).

---

## Motor de Busca em Cascata (4 Fases)

```
POST /api/v1/busca/servicos
  ↓ RBAC: require_cliente_access(cliente_id)
  ↓ NORMALIZAÇÃO: strip → lower → NFD (remove acentos) → collapse spaces
  │
  ├─ FASE 0: Itens PROPRIOS do cliente (APROVADOS)
  │   pg_trgm em servico_tcpo WHERE origem=PROPRIA AND cliente_id=:cid AND status=APROVADO
  │   score > threshold → origem_match = "PROPRIA_CLIENTE" → RETURN
  │
  ├─ FASE 1: Associação Inteligente (circuit break em CONSOLIDADA)
  │   SELECT FROM associacao_inteligente WHERE cliente_id=:cid AND texto_busca_normalizado=:norm
  │   qualquer match → score=1.0, origem_match = "ASSOCIACAO_DIRETA"
  │   chama fortalecer() → incrementa frequencia_uso → pode elevar SUGERIDA→VALIDADA→CONSOLIDADA
  │   RETURN
  │
  ├─ FASE 2: Fuzzy Global (pg_trgm)
  │   similarity(descricao, :texto) > threshold em TCPO global (cliente_id IS NULL, APROVADO)
  │   origem_match = "FUZZY" → RETURN
  │
  └─ FASE 3: IA Semântica (pgvector)
      embedder.encode(texto) → cosine similarity em tcpo_embeddings
      threshold configurável (default 0.65) → origem_match = "IA_SEMANTICA"
      skip se embedder.ready = False
  │
  ↓ PERSISTÊNCIA SÍNCRONA do historico_busca_cliente (usuario_id, cliente_id, texto)
  ↓ id real do histórico retornado em metadados.id_historico_busca
```

### DTOs Oficiais

**Request `POST /busca/servicos`:**
```python
class BuscaServicoRequest(BaseModel):
    cliente_id: UUID
    texto_busca: str          # min=2, max=500
    limite_resultados: int = 5
    threshold_score: float = 0.65
```

**Response:**
```python
class ResultadoBusca(BaseModel):
    id_tcpo: UUID
    codigo_origem: str
    descricao: str
    unidade: str
    custo_unitario: float
    score: float
    score_confianca: float
    origem_match: Literal["PROPRIA_CLIENTE", "ASSOCIACAO_DIRETA", "FUZZY", "IA_SEMANTICA"]
    status_homologacao: str

class BuscaMetadados(BaseModel):
    tempo_processamento_ms: int   # latência total da requisição de busca
    id_historico_busca: UUID      # UUID do registro em historico_busca_cliente
                                  # usado em POST /busca/associar como chave de rastreio

class BuscaServicoResponse(BaseModel):
    texto_buscado: str
    resultados: list[ResultadoBusca]
    metadados: BuscaMetadados
```

**Request `POST /busca/associar`:**
```python
class CriarAssociacaoRequest(BaseModel):
    cliente_id: UUID
    texto_busca_original: str
    id_tcpo_selecionado: UUID
    id_historico_busca: UUID  # validado: deve existir e pertencer ao cliente
```

---

## Endpoints da API

### Auth
| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/api/v1/auth/login` | — | JSON login — frontend (email+senha → JWT) |
| POST | `/api/v1/auth/token` | — | **OAuth2 form login** — Swagger "Authorize" button |
| POST | `/api/v1/auth/refresh` | — | Renova access token |
| POST | `/api/v1/auth/logout` | JWT | Revoga refresh token |
| GET | `/api/v1/auth/me` | JWT | Usuário atual + vínculos cliente/perfil |
| POST | `/api/v1/auth/usuarios` | JWT (Admin) | Criar usuário — **admin only** |

### Busca
| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/api/v1/busca/servicos` | JWT + cliente | Motor cascata 4 fases |
| POST | `/api/v1/busca/associar` | JWT + cliente | Criar/fortalecer associação inteligente |
| GET | `/api/v1/busca/associacoes` | JWT + cliente | Listar associações do cliente (paginado) |
| DELETE | `/api/v1/busca/associacoes/{id}` | JWT (APROVADOR+) | Excluir associação |

### Catálogo de Serviços
| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/api/v1/servicos/` | JWT | Catálogo visível (TCPO global + PROPRIA aprovados) |
| GET | `/api/v1/servicos/{id}` | JWT | Detalhe — cross-tenant guard em PROPRIA |
| GET | `/api/v1/servicos/{id}/composicao` | JWT | Explosão TCPO (insumos + custos) |
| POST | `/api/v1/servicos/` | JWT (Admin) | Criar item TCPO global — **admin only** |

### Homologação
| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/api/v1/homologacao/pendentes` | JWT (APROVADOR+) | Lista PENDENTE do cliente |
| POST | `/api/v1/homologacao/aprovar` | JWT (APROVADOR+) | Aprovar ou reprovar item |
| POST | `/api/v1/homologacao/itens-proprios` | JWT + cliente | Criar item próprio (nasce PENDENTE) |

### Gestão de Usuários (Admin)
| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/api/v1/usuarios/` | JWT (Admin) | Listar usuários paginado |
| PATCH | `/api/v1/usuarios/{id}` | JWT (Admin) | Atualizar nome/email/is_active/is_admin |
| GET | `/api/v1/usuarios/{id}/perfis-cliente` | JWT (admin ou self) | Listar perfis RBAC do usuário |
| PUT | `/api/v1/usuarios/{id}/perfis-cliente` | JWT (Admin) | Substituir perfis do usuário em um cliente |

### Gestão de Clientes (Admin)
| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/api/v1/clientes/` | JWT (Admin) | Listar clientes paginado |
| POST | `/api/v1/clientes/` | JWT (Admin) | Criar cliente (CNPJ único) |
| PATCH | `/api/v1/clientes/{id}` | JWT (Admin) | Editar `nome_fantasia` e/ou `is_active` — campos opcionais, validação igual ao POST |

### Composição por Cópia
| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/api/v1/composicoes/clonar` | JWT (APROVADOR+) | Clona item TCPO/PROPRIA → novo item `PROPRIA/PENDENTE` vinculado ao cliente |
| POST | `/api/v1/composicoes/{pai_id}/componentes` | JWT (APROVADOR+) | Adiciona insumo filho a uma composição própria — anti-loop DFS |
| DELETE | `/api/v1/composicoes/{pai_id}/componentes/{componente_id}` | JWT (APROVADOR+) | Remove insumo filho; recalcula custo do pai automaticamente |

### Admin / Infra
| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/api/v1/admin/compute-embeddings` | JWT (Admin) | Batch encode embeddings |
| GET | `/health` | — | Status (embedder_ready flag) |

---

## Autenticação e RBAC

### JWT
- **Access token**: 30 minutos
- **Refresh token**: 7 dias, hash armazenado no banco para revogação explícita
- Bcrypt para hashing de senhas

### Perfis por Cliente (`usuario_perfil`)

| Perfil | Permissões |
|---|---|
| `USUARIO` | Buscar serviços, criar itens PROPRIA, confirmar associações |
| `APROVADOR` | Tudo do USUARIO + aprovar/reprovar itens PENDENTE do cliente |
| `ADMIN` | Acesso total ao cliente + operações administrativas |
| `is_admin=True` (global) | Bypass completo — acesso a todos os clientes e rotas admin |

### Funções de Autorização (`app/core/dependencies.py`)

```python
# Valida que o usuário tem qualquer vínculo com o cliente
require_cliente_access(cliente_id, current_user, db)

# Valida que o usuário tem um dos perfis exigidos para o cliente
require_cliente_perfil(cliente_id, ["APROVADOR", "ADMIN"], current_user, db)
```

> `is_admin=True` faz bypass em ambas as funções.

### `GET /auth/me` — Resposta com Perfis

```json
{
  "id": "uuid",
  "nome": "Rafael",
  "email": "rafael@empresa.com",
  "is_active": true,
  "is_admin": false,
  "perfis": [
    {"cliente_id": "uuid-cliente-a", "perfil": "APROVADOR"},
    {"cliente_id": "uuid-cliente-b", "perfil": "USUARIO"}
  ]
}
```

---

## Fluxo de Homologação

```
POST /homologacao/itens-proprios  (qualquer usuário com acesso ao cliente)
          ↓
  servico_tcpo criado:
    origem = PROPRIA | status_homologacao = PENDENTE | cliente_id = <cliente>
    auditoria_log: operacao=CREATE, usuario_id, cliente_id
          ↓
  Não aparece em buscas (filtro: status_homologacao = APROVADO)
  Não gera embedding
          ↓
GET /homologacao/pendentes?cliente_id=...  (APROVADOR ou ADMIN)
          ↓
POST /homologacao/aprovar  {servico_id, cliente_id, aprovado: true/false}
    ↓ Valida: servico.cliente_id == request.cliente_id (ownership guard)
    ↓
    ├─ aprovado=true  → status=APROVADO → EmbeddingSyncService.sync() → auditoria APROVAR
    └─ aprovado=false → status=REPROVADO → auditoria REPROVAR
```

---

## Sistema de Auditoria

A auditoria é feita **explicitamente nos services** com contexto completo do usuário.

### Eventos Auditados

| Evento | Service | Operação |
|---|---|---|
| Criação de item PROPRIA | `homologacao_service.criar_item_proprio` | `CREATE` |
| Aprovação de item | `homologacao_service.aprovar` | `APROVAR` |
| Reprovação de item | `homologacao_service.aprovar` | `REPROVAR` |
| Exclusão lógica | `servico_catalog_service.soft_delete` | `DELETE` |

Cada registro em `auditoria_log` contém:
- `usuario_id` — quem executou
- `cliente_id` — em qual cliente
- `dados_anteriores` / `dados_novos` — snapshot JSONB do que mudou

> Não utiliza SQLAlchemy event hooks (API privada `_modified` removida — frágil e sem contexto de usuário).

---

## Módulos ML (On-Premise)

### `app/ml/embedder.py`
- Singleton `Embedder`, carregado no lifespan FastAPI
- `all-MiniLM-L6-v2` — 384 dimensões, cache local via `SENTENCE_TRANSFORMERS_HOME`
- `encode(text: str) → list[float]` | `encode_batch(texts, batch_size=64)`
- Flag `ready: bool` exposta em `/health` — Fase 3 é skipada se `ready=False`

### `app/ml/fuzzy_search.py`
- Primário: `pg_trgm similarity()` — safe para múltiplos workers (Gunicorn/Uvicorn)
- Threshold padrão: **0.85** (Fase 0 e 2)
- Fallback: `rapidfuzz` in-memory (ativável por feature flag)

### `app/ml/vector_search.py`
- Stateless, query pgvector: `1 - (vetor <=> :query_vec) >= threshold`
- Índice HNSW para ANN (Approximate Nearest Neighbors)

### Sincronia de Embeddings (`embedding_sync_service`)
```
CREATE serviço aprovado → INSERT INTO tcpo_embeddings
UPDATE custo/descricao   → UPDATE tcpo_embeddings
soft DELETE              → DELETE FROM tcpo_embeddings
```

---

## Migrations Alembic

| # | Arquivo | O que faz |
|---|---|---|
| 001 | `create_base_tables` | `usuarios`, `clientes`, `categoria_recurso`, `servico_tcpo`, `composicao_tcpo`, `historico_busca_cliente`, `associacao_tcpo` (legado) |
| 002 | `pgvector_extension` | `CREATE EXTENSION IF NOT EXISTS vector` |
| 003 | `tcpo_embeddings_table` | Tabela `tcpo_embeddings` + Vector(384) + índice HNSW |
| 004 | `pgtrgm_and_gin_index` | `CREATE EXTENSION pg_trgm` + GIN index em `servico_tcpo.descricao` |
| 005 | `v2_governance_rbac_audit` | Enums V2, `external_id_ad`, `usuario_perfil`, colunas de governança em `servico_tcpo`, substitui `associacao_tcpo` → `associacao_inteligente`, cria `auditoria_log` |
| 006 | `consolidation_fixes` | `historico_busca_cliente.usuario_id FK` (substitui `usuario_origem`), `auditoria_log.usuario_id FK` + `auditoria_log.cliente_id FK`, estende enum `tipo_operacao_auditoria_enum` com `APROVAR`/`REPROVAR` |
| 007 | `fix_defaults_and_cliente_updated_at` | `servico_tcpo.status_homologacao` server_default `APROVADO → PENDENTE` (defense-in-depth), adiciona `clientes.updated_at` |
| 008 | `tipo_recurso_tokens` | Novo enum `tipo_recurso_enum` (MO/INSUMO/FERRAMENTA/EQUIPAMENTO/SERVICO), adiciona `tipo_recurso` e `descricao_tokens` (TEXT) em `servico_tcpo` |
| 009 | `versao_composicao` | Tabela `versao_composicao` (versionamento de composições), adiciona `versao_id` e `unidade_medida` em `composicao_tcpo` |
| 010 | `rename_usuario_perfil` | Renomeia tabela `usuario_perfil` → `permissao_operacional` (sem perda de dados) |
| 011 | `nullable_cliente_historico` | `historico_busca_cliente.cliente_id` nullable (suporte a busca genérica), popula `descricao_tokens` em linhas existentes via SQL |

```bash
# Aplicar todas as migrations
alembic upgrade head

# Ver status atual
alembic current

# Reverter uma migration
alembic downgrade -1
```

---

## Ferramentas de Banco de Dados

O projeto utiliza dois complementares para o dia a dia com o PostgreSQL:

| Ferramenta | Tipo | Uso |
|---|---|---|
| **pgcli** | CLI interativa | queries rápidas, scripts, automação |
| **HeidiSQL** | GUI nativa Win32 | inspeção visual, edição inline, open-source |

---

### pgcli (CLI)

pgcli já está incluído no `requirements.txt` e é instalado junto com as dependências do projeto (`pip install -r requirements.txt`). É o `psql` com autocomplete inteligente de tabelas/colunas, syntax highlighting e histórico persistente.

#### Conectar ao banco

```bash
# Windows — usa DATABASE_URL do .env automaticamente
scripts\db.bat

# Linux / Mac
./scripts/db.sh

# Conexão direta (sem script)
.venv\Scripts\pgcli.exe postgresql://postgres:postgres@localhost:5432/dinamica_budget
```

#### Comandos essenciais dentro do pgcli

```sql
\dt                        -- lista todas as tabelas
\d servico_tcpo            -- descreve estrutura da tabela
\di                        -- lista índices
\dn                        -- lista schemas
\dT                        -- lista tipos (enums)
\e                         -- abre editor externo (vim/vscode)
\o arquivo.csv             -- redireciona output para arquivo
\timing                    -- ativa/desativa cronômetro de queries
\x                         -- modo expanded (linhas → colunas)
\q                         -- sai

-- Exemplos úteis para o projeto:
SELECT * FROM usuarios;
SELECT * FROM servico_tcpo WHERE origem = 'PROPRIA' LIMIT 10;
SELECT tabela, operacao, criado_em FROM auditoria_log ORDER BY criado_em DESC LIMIT 20;
SELECT nome_fantasia, cnpj, is_active FROM clientes;
```

#### Configuração pessoal (opcional)

Copie o template de configuração para ativar syntax highlighting Monokai, expansão automática e aliases de DSN:

```bash
# Windows
copy configs\pgclirc.example %APPDATA%\pgcli\config

# Linux / Mac
cp configs/pgclirc.example ~/.config/pgcli/config
```

O arquivo `configs/pgclirc.example` define:
- `syntax_style = monokai` — destaque de sintaxe escuro
- `expand = auto` — expande resultados largos automaticamente
- `timing = True` — mostra tempo de execução
- `table_format = rounded` — bordas arredondadas nos resultados
- `alias_dsn.dinamica_dev` — atalho de conexão

---

### HeidiSQL (GUI)

HeidiSQL é uma GUI open-source (GPL) nativa para Windows — binário Win32 puro, sem Java, sem Electron, sem instalação obrigatória (versão portátil disponível). Suporta PostgreSQL, MySQL, MariaDB e SQLite. Download: **https://www.heidisql.com/download.php**

#### Instalação

Duas opções no mesmo link de download:
- **Installer** (`HeidiSQL_xx_Setup.exe`) — instalação padrão no sistema
- **Portable** (`HeidiSQL_xx_Portable.zip`) — extraia e execute `heidisql.exe` direto, sem instalar nada

#### Configuração da conexão

Ao abrir, clique em **"New"** na tela de Session Manager e preencha:

| Campo | Valor |
|---|---|
| **Network type** | `PostgreSQL (TCP/IP)` |
| **Hostname / IP** | `127.0.0.1` |
| **Port** | `5432` |
| **User** | `postgres` |
| **Password** | `postgres` _(ou o valor de `POSTGRES_PASSWORD` no `.env`)_ |
| **Database** | `dinamica_budget` |

Salve com o nome **"Dinamica Budget dev"** e clique **Open**.

> **Dicas rápidas:**
> - `F5` — atualiza a árvore de tabelas
> - `F9` / `Ctrl+Enter` — executa a query selecionada
> - `Ctrl+Shift+L` — formata SQL automaticamente
> - Clique duplo em uma célula — edição inline do valor
> - Aba **"Table data"** → filtro visual por coluna sem escrever SQL

#### Queries salvas recomendadas

Salve as queries abaixo em **HeidiSQL → Tools → User Queries** para acesso rápido:

```sql
-- Auditoria recente (últimas 50 operações)
SELECT u.nome, a.tabela, a.operacao, a.campo_alterado,
       a.dados_anteriores, a.dados_novos, a.criado_em
FROM auditoria_log a
LEFT JOIN usuarios u ON u.id = a.usuario_id
ORDER BY a.criado_em DESC LIMIT 50;

-- Itens pendentes de homologação
SELECT s.codigo_origem, s.descricao, s.origem,
       s.status_homologacao, c.nome_fantasia, s.created_at
FROM servico_tcpo s
LEFT JOIN clientes c ON c.id = s.cliente_id
WHERE s.status_homologacao = 'PENDENTE'
ORDER BY s.created_at;

-- Associações por cliente
SELECT c.nome_fantasia, a.texto_busca_normalizado,
       s.descricao, a.frequencia_uso, a.status_validacao
FROM associacao_inteligente a
JOIN clientes c ON c.id = a.cliente_id
JOIN servico_tcpo s ON s.id = a.servico_tcpo_id
ORDER BY a.frequencia_uso DESC;
```

---

## Setup e Instalação

### Pré-requisitos
- Python 3.11+
- PostgreSQL 16 com extensões `pgvector` e `pg_trgm`
- HeidiSQL (opcional, GUI open-source) — https://www.heidisql.com/download.php

> **Para deploy automatizado em Windows Server**, veja a seção [Deploy Automatizado — Windows Server](#deploy-automatizado--windows-server) abaixo.

### 1. Clone e Ambiente Virtual
```bash
git clone <repo>
cd dinamica-budget
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
# pgcli é instalado automaticamente junto com as demais dependências
```

### 2. Banco de Dados

**Opção A — PostgreSQL nativo (recomendado para Windows):**
```bash
# PostgreSQL 16 + pgvector: instale conforme docs/Manual_Instalacao_Dinamica_Budget.docx
# O serviço Windows já sobe automaticamente no boot
```

**Opção B — Docker:**
```bash
docker compose up db -d
```

### 3. Variáveis de Ambiente
```bash
cp .env.example .env
# editar .env com as credenciais
```

### 4. Migrations
```bash
alembic upgrade head
```

### 5. Conectar ao banco (verificação)
```bash
scripts\db.bat          # Windows — abre pgcli com autocomplete
./scripts/db.sh         # Linux/Mac
```

### 6. Download do Modelo ML (única vez)
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
# Definir SENTENCE_TRANSFORMERS_HOME no .env para cache local permanente
```

### 7. Iniciar API
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 8. Seed + Pré-computar Embeddings
```bash
# Após popular servico_tcpo com dados TCPO:
curl -X POST http://localhost:8000/api/v1/admin/compute-embeddings \
  -H "Authorization: Bearer <admin_token>"
```

**Swagger UI:** `http://localhost:8000/docs`

---

## Deploy Automatizado — Windows Server

Para ambientes de produção em Windows Server 2019/2022, o projeto inclui um instalador nativo completo que configura **tudo automaticamente** com uma única execução.

### Pré-requisitos do servidor

| Componente | Versão mínima | Observação |
|---|---|---|
| Windows Server | 2019 / 2022 | Build 17763+ |
| Python | 3.11+ | Adicionado ao PATH do sistema |
| Node.js | 18+ | Para build do frontend |
| PostgreSQL | 16 | Serviço `postgresql-x64-16` no Windows |
| IIS | 10 | Feature `Web-Server` habilitada |
| URL Rewrite | 2.1 | Módulo IIS |
| ARR | 3.0 | Application Request Routing (reverse proxy) |
| NSSM | qualquer | No PATH do sistema |

### Executar o deploy

```bat
REM Clique com botão direito -> "Executar como Administrador"
deploy-dinamica.bat
```

O script solicita apenas a **senha do PostgreSQL** e executa as 11 etapas automaticamente:

| Etapa | O que faz |
|---|---|
| 0 — Pré-requisitos | Valida Python, Node.js, NSSM, IIS, ARR, URL Rewrite |
| 1 — Sync de arquivos | `robocopy` da origem para `C:\DinamicaBudget` (exclui venv/logs/node_modules) |
| 2 — Python venv | Cria/atualiza venv, instala torch CPU + dependências + pgcli |
| 3 — Arquivo `.env` | Gera `.env` com `SECRET_KEY` aleatória se não existir |
| 4 — PostgreSQL | Cria banco, ativa `pgvector` e `pg_trgm`; chama `install-pgvector.ps1` |
| 5 — Alembic | `alembic upgrade head` (migrations 001–011) |
| 6 — Modelo ML | Verifica/baixa `all-MiniLM-L6-v2` para cache local |
| 7 — Frontend | `npm install` + `npm run build` para `C:\inetpub\DinamicaBudget` |
| 8 — Serviço NSSM | Cria/atualiza serviço `DinamicaBudgetAPI` (uvicorn, auto-start) |
| 9 — IIS | Cria site `DinamicaBudget` na porta 80 com Virtual Directory |
| 10 — Firewall | Abre portas 80, 443, 8000 |
| 11 — Verificação | Testa `/health`, relata status final |

### pgvector em Windows Server

Quando `pgvector` não está instalado como extensão PostgreSQL, o script `scripts/install-pgvector.ps1` é chamado automaticamente pela etapa 4. Ele:

1. Verifica se `vector.control` já existe — pula se sim
2. Localiza `vcvars64.bat` (VS Build Tools) em caminhos padrão
3. Se não encontrado: baixa o bootstrapper do VS Build Tools (~2,5 GB) e instala silenciosamente
4. Baixa o fonte de pgvector v0.8.0 do GitHub
5. Compila com `nmake /F Makefile.win` usando o compilador MSVC
6. Copia os binários para `%PG_ROOT%\lib` e `%PG_ROOT%\share\extension`
7. Executa `CREATE EXTENSION vector` no banco
8. Faz upgrade da coluna `tcpo_embeddings.vetor` de TEXT para `vector(384)` + cria índice HNSW

### Modos de execução

O deploy detecta automaticamente se é uma **instalação nova** ou uma **atualização**:

- **Nova instalação**: cria tudo do zero (venv, .env, banco, serviço NSSM, site IIS)
- **Atualização**: sincroniza arquivos, atualiza dependências, roda migrations incrementais, reinicia serviço

### Resultado esperado após deploy bem-sucedido

```
[OK] API rodando: {"status":"ok","database_connected":true,"embedder_ready":true}
[OK] Frontend acessivel em http://<servidor>/
[OK] Swagger UI em http://<servidor>:8000/docs
```

Arquivos de log gerados em `C:\Dinamica-Budget\logs\`:
- `deploy-YYYYMMDD_HHMMSS.log` — log completo do deploy
- `install-pgvector.log` — log da compilação/instalação do pgvector
- `C:\DinamicaBudget\logs\uvicorn.log` — log de runtime da API

---

## Scripts de Operação

Todos os scripts estão em `scripts/` e são executados em PowerShell.

### `scripts/status.ps1` — Painel de saúde do sistema

Exibe o estado de todos os componentes em tempo real, sem parâmetros:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\status.ps1
```

Verifica e reporta **[OK]** / **[FAIL]** / **[WARN]** para:

| Seção | O que inspeciona |
|---|---|
| Serviços Windows | PostgreSQL 16, DinamicaBudgetAPI (NSSM), IIS (W3SVC) |
| Portas | 80, 443, 8000, 5432 — estado LISTEN + processo responsável |
| API Health | `GET /health` (status, database_connected, embedder_ready) e `GET /docs` |
| PostgreSQL | Versão, existência do banco, extensões vector e pg_trgm |
| Migrations | Versões aplicadas em `alembic_version`, contagem de tabelas |
| Coluna vetor | Tipo atual de `tcpo_embeddings.vetor` e existência do índice HNSW |
| IIS Sites | Nome, estado e binding de cada site |
| Processos Python | PIDs e consumo de RAM de cada worker uvicorn |
| Disco e memória | Espaço livre em C:, RAM livre/total |
| Diretórios | Deploy dir, venv, ml_models, IIS webroot |
| Log da API | Últimas 8 linhas de `uvicorn.log` |

### `scripts/install-pgvector.ps1` — Instalação do pgvector

Usado internamente pelo deploy, mas pode ser executado manualmente com elevação:

```powershell
# Requer Administrador
Start-Process PowerShell -Verb RunAs -ArgumentList '-ExecutionPolicy Bypass -File "C:\Dinamica-Budget\scripts\install-pgvector.ps1"'
```

Parâmetros opcionais:

```powershell
-PgRoot    "C:\Program Files\PostgreSQL\16"   # caminho do PostgreSQL
-DbName    "dinamica_budget"                   # banco alvo
-EnvFile   "C:\DinamicaBudget\.env"            # arquivo .env para leitura da senha
```

### `scripts/backup-db.ps1` — Backup do banco

```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup-db.ps1
```

### `scripts/db.bat` / `scripts/db.sh` — Cliente pgcli

```bat
REM Windows — abre pgcli com autocomplete no banco de desenvolvimento
scripts\db.bat
```

---

## Variáveis de Ambiente

```env
# Banco de Dados
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dinamica_budget

# JWT
SECRET_KEY=sua_chave_secreta_muito_longa_e_aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Modelo ML
SENTENCE_TRANSFORMERS_HOME=./models/cache
ML_MODEL_NAME=all-MiniLM-L6-v2

# Busca
FUZZY_THRESHOLD=0.85
SEMANTIC_THRESHOLD=0.65
DEFAULT_SEARCH_LIMIT=5

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Regras de Segurança e Governança

### Nenhum endpoint de negócio confia só na autenticação

Todo endpoint que recebe `cliente_id` valida se o usuário tem vínculo com aquele cliente via `usuario_perfil`. O `cliente_id` enviado pelo frontend **nunca é aceito cegamente**.

### Criação de catálogo TCPO global é restrita

`POST /servicos` exige `is_admin=True`. Usuários comuns criam itens apenas via `POST /homologacao/itens-proprios`, que obrigatoriamente gera um item `PROPRIA` + `PENDENTE`.

### Item PROPRIA não aparece na busca antes da aprovação

Todas as fases da busca filtram `status_homologacao = APROVADO`. Item reprovado ou pendente nunca é retornado.

### Rastreabilidade busca → associação

A resposta de busca retorna o `id_historico_busca` real (UUID da linha no banco). Ao criar uma associação, esse id é validado: deve existir e pertencer ao mesmo `cliente_id`. Impossível criar associação "fantasma" sem histórico correspondente.

### Isolamento por cliente

Fase 0 da busca filtra `cliente_id = :cid` — impossível retornar item PROPRIA de outro cliente.
`GET /servicos?cliente_id=X` exige `require_cliente_access(X)`.
`GET /homologacao/pendentes?cliente_id=X` exige perfil APROVADOR ou ADMIN no cliente X.

### Auditoria com contexto completo

Cada registro em `auditoria_log` tem `usuario_id` e `cliente_id` reais. Logs são criados explicitamente nos services, onde o contexto do usuário está disponível (diferente de hooks SQLAlchemy, que não têm acesso à requisição HTTP).

---

## Riscos Técnicos e Mitigações

| Risco | Mitigação |
|---|---|
| Orphan IDs no banco vetorial | `EmbeddingSyncService` em toda mutação do catálogo; soft delete remove embedding imediatamente |
| Modelo ML não carregado no startup | Flag `embedder.ready=False` no `/health`; Fase 3 é skipped automaticamente |
| HNSW index build lento em tabela grande | `CREATE INDEX CONCURRENTLY` + `maintenance_work_mem=1GB` |
| Alembic não reconhece tipo Vector | Custom type hook em `alembic/env.py` |
| Histórico desconectado da associação | `id_historico_busca` validado em `criar_associacao` antes de qualquer upsert |
| Soft delete sem filtro | `WHERE deleted_at IS NULL` obrigatório em todos os SELECTs ativos |
| Loop infinito em composição TCPO | DFS com conjunto `visitados` antes de todo INSERT em `composicao_tcpo` |
| Usuário acessando cliente errado | `require_cliente_access` em todo endpoint com `cliente_id`; `is_admin` como único bypass |
| Aprovação de item de outro cliente | `servico.cliente_id == request.cliente_id` verificado em `homologacao_service.aprovar` |
| Auditoria sem contexto de usuário | Auditoria explícita nos services (não hooks); `usuario_id` + `cliente_id` sempre presentes |
| Tokens JWT não revogados | Hash do refresh token no banco; `POST /auth/logout` o invalida |
| Criação de TCPO global por usuário comum | `POST /servicos` requer `is_admin=True`; usuário comum recebe 403 |

---

---

## Correções Sprint 1 (P0/P1)

Todas as correções abaixo foram aplicadas antes do avanço para Sprint 2.

### P0 — Crítico

| # | Item | Arquivo(s) | Correção |
|---|---|---|---|
| P0.1 | Cross-tenant isolation em `GET /servicos/{id}` | `endpoints/servicos.py` | Adicionado check: itens PROPRIA retornam 404 se o usuário não tiver vínculo com o `cliente_id` do item. Admin faz bypass. TCPO global sem check. |
| P0.2 | `POST /auth/usuarios` aberto sem auth | `endpoints/auth.py` | Adicionado `Depends(get_current_admin_user)` — apenas `is_admin=True` pode criar usuários. Não-autenticado → 401. Autenticado sem admin → 403. |
| P0.3 | `SECRET_KEY` default aceita no startup | `core/config.py`, `main.py` | Função `validate_startup_config()` criada. Chamada no lifespan startup. Rejeita keys inseguras (< 32 chars, valores default conhecidos). App não sobe. |
| P0.4 | `allow_origins=["*"]` no CORS | `main.py`, `core/config.py` | Substituído por `settings.ALLOWED_ORIGINS` (lista configurável). Default: `["http://localhost:3000", "http://localhost:8080"]`. Configurável via `ALLOWED_ORIGINS` no `.env`. |

### P1 — Importante

| # | Item | Arquivo(s) | Correção |
|---|---|---|---|
| P1.5 | `historico.usuario_id` nullable mismatch ORM vs migration | `models/historico_busca_cliente.py` | Alterado `nullable=False` → `nullable=True` e `Mapped[UUID]` → `Mapped[UUID \| None]`. Alinhado com migration 006 que usa `nullable=True` por backward compat. |
| P1.6 | Senha sem validação mínima | `schemas/auth.py` | Adicionado `Field(min_length=8)` em `UsuarioCreate.password`. Senhas menores retornam 422. |
| P1.7 | N+1 na Fase 3 (busca semântica) | `services/busca_service.py`, `repositories/servico_tcpo_repository.py` | Adicionado `get_active_by_ids(ids)` ao repositório (batch SELECT com `IN`). Fase 3 agora carrega todos os candidatos em **uma única query** ao invés de N queries individuais. |
| P1.8 | Sem rate limit nos endpoints de auth | `core/rate_limit.py` (novo), `endpoints/auth.py`, `main.py`, `requirements.txt` | Adicionado `slowapi` (in-memory, sem infra externa). Login: 10 req/min por IP. Refresh: 20 req/min. Registrado no `app.state.limiter`. |

### Bug colateral corrigido

| Item | Arquivo | Correção |
|---|---|---|
| `TcpoEmbedding.metadata` conflitava com atributo reservado do SQLAlchemy Declarative API | `models/tcpo_embeddings.py`, `repositories/tcpo_embeddings_repository.py` | Renomeado atributo ORM para `embedding_metadata`; coluna no banco mantém nome `metadata` via `name="metadata"`. |

### Suite de testes

| Arquivo | Testes | Resultado |
|---|---|---|
| `tests/unit/test_busca_service.py` | 8 testes (normalize × 4, fase1 × 3, fase3 N+1) | ✅ 25/25 PASS |
| `tests/unit/test_security_p0.py` | 17 testes (SECRET_KEY, CORS, senha, cross-tenant × 4, admin dep, rate limit) | ✅ |
| `tests/integration/test_auth_access_control.py` | 5 testes (401 sem auth, 422 senha curta, health, CORS header, app.state.limiter) | Requer DB |

Para rodar os testes unitários (sem DB):
```bash
pytest app/tests/unit/ -v
```

---

*Dinamica Budget — Backend API v2.2 | On-Premise | FastAPI + PostgreSQL 16 + pgvector 0.8.0 + IIS + NSSM*
