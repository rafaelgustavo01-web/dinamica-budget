# Checkpoint Técnico — Fase 1 + Fase 2
**Data:** 2026-04-27
**Papéis:** PO + Scrum Master + Arquiteto
**QA:** Amazon Q
**Escopo:** S-01..S-12 + F2-01..F2-13
**Metodologia:** Varredura de código + análise arquitetural. Nenhuma linha alterada.

---

## Sumário Executivo

O projeto está em estado sólido. A arquitetura em camadas (endpoint → service → repository) é consistente. O RBAC por proposta (F2-08) foi bem integrado. Os débitos identificados são majoritariamente de qualidade e performance — nenhum é bloqueador de produção imediato. Há 3 itens de segurança que merecem atenção antes de go-live com dados reais.

**Distribuição:** 3 Críticos · 6 Altos · 9 Médios · 8 Baixos

---

## Pontos Positivos Confirmados

- Arquitetura em camadas (endpoint → service → repository) consistente em todos os módulos
- RBAC por proposta (F2-08) corretamente integrado com `require_proposta_role` em todos os endpoints de proposta
- Bulk loader em `GET /propostas` sem N+1 (usa `get_papeis_bulk` com lista de IDs)
- Pipeline ETL correto (`etl_service.py`) funcionando via `/admin/etl/*`
- Migrations Alembic com padrão consistente (schema explícito, autocommit_block para ALTER TYPE)
- `montar_histograma` com idempotência correta para itens mapeados (upsert com `WHERE editado_manualmente IS FALSE`)
- `nova_versao` clona histograma + recursos extras + alocações
- Parser TCPO com detecção robusta de pai via AND triplo (bold + indent + prefixo SER.)
- Tree table (F2-13) com lazy loading, recursão controlada e separação correta de clique vs expansão

---

## Débitos Técnicos

### 🔴 Críticos

#### C-01 — Pipeline legado `etl_popular_base_consulta.py` ainda ativo via subprocess

**Arquivo:** `app/backend/api/v1/endpoints/admin.py` — `POST /admin/import/execute`
**Severidade:** Crítica
**Categoria:** Segurança + Arquitetura

O endpoint ainda invoca `scripts/etl_popular_base_consulta.py` via `subprocess.run` para `source_type=TCPO`. Este script usa `psycopg2` síncrono e pode estar desatualizado com o schema atual (post-migration 023). O path traversal (CWE-22) detectado pelo scanner neste endpoint (linha 151) está exatamente neste bloco — `Path(file.filename).suffix` sem sanitização completa antes de criar o arquivo temporário em `logs/uploads/`.

**Risco:** Execução de processo externo com input de usuário + path traversal potencial + dependência de script legado que pode estar desatualizado com o schema atual.

**Recomendação:** Migrar `POST /admin/import/execute` para usar exclusivamente `etl_service.parse_tcpo_pini()` + `etl_service.execute_load()` (mesmo fluxo do `POST /admin/etl/upload-tcpo` + `POST /admin/etl/execute`). Remover o subprocess inteiramente.

**Sprint sugerida:** F2-DT-01

---

#### C-02 — `import_preview_service.py` é código morto com dois pipelines de importação paralelos

**Arquivo:** `app/backend/services/import_preview_service.py`
**Severidade:** Crítica
**Categoria:** Arquitetura + Segurança

Existe um segundo pipeline completo de importação (`generate_import_preview` + `POST /admin/import/preview` + `POST /admin/import/execute`) paralelo ao pipeline correto (`etl_service.py` + `/admin/etl/*`). O frontend (`UploadTcpoPage.tsx`) foi corrigido na F2-10 para usar o pipeline correto, mas o pipeline legado permanece no backend — endpoints ativos, service ativo, código mantido. Isso cria confusão sobre qual pipeline usar e mantém superfície de ataque desnecessária.

**Risco:** Dois caminhos de importação com comportamentos diferentes. Usuários ou integrações externas podem acionar o caminho errado.

**Recomendação:** Deprecar e remover `import_preview_service.py`, `POST /admin/import/preview` e o path TCPO de `POST /admin/import/execute` (manter apenas o 410 Gone para PC).

**Sprint sugerida:** F2-DT-01

---

#### C-03 — `DEBUG=release` no ambiente de sistema sobrescreve `.env`

**Arquivo:** Variável de ambiente do sistema operacional Windows
**Severidade:** Crítica
**Categoria:** Ambiente + CI/CD

A variável de ambiente `DEBUG=release` no sistema operacional sobrescreve `DEBUG=True` do `.env`, causando falha de validação Pydantic (`bool_parsing`) que impede o `pytest` de carregar o `conftest.py`. Isso significa que **nenhum teste pode ser executado no ambiente atual** sem intervenção manual. A suite de 199+ testes está efetivamente bloqueada para CI/CD local.

**Risco:** Regressões não detectadas. Qualquer sprint futura não pode validar testes automaticamente neste ambiente.

**Recomendação:**
- Imediato: `setx DEBUG ""` no terminal do sistema para remover a variável
- Estrutural: adicionar `env_ignore_empty=True` no `SettingsConfigDict` do `config.py` para tornar o ambiente resiliente a variáveis de sistema inválidas

**Sprint sugerida:** F2-DT-02

---

### 🟠 Altos

#### A-01 — N+1 queries em `fila_aprovacoes`

**Arquivo:** `app/backend/api/v1/endpoints/propostas.py` — `GET /propostas/aprovacoes`
**Severidade:** Alta
**Categoria:** Performance

```python
for p in candidatas:
    papeis = await acl_repo.get_papeis_bulk([root_id], current_user.id)  # 1 query por proposta
```

Para N propostas aguardando aprovação, dispara N queries de ACL sequenciais. Com 50 propostas em fila, são 50 roundtrips ao banco.

**Recomendação:** Coletar todos os `root_id`s primeiro, chamar `get_papeis_bulk` uma vez com a lista completa, depois filtrar localmente por papel.

**Sprint sugerida:** F2-DT-03

---

#### A-02 — N+1 queries em `montar_histograma` para lookup De/Para

**Arquivo:** `app/backend/services/histograma_service.py`
**Severidade:** Alta
**Categoria:** Performance

```python
for insumo_id in insumos_unicos:
    de_para = await self.de_para_repo.get_by_base_tcpo_id(insumo_id)  # 1 query por insumo
    tcpo = await self.tcpo_repo.get_by_id(insumo_id)                  # + 1 query por insumo
    bcu_item = await self.db.get(BcuMaoObraItem, de_para.bcu_item_id) # + 1 query por insumo
```

Para uma proposta com 30 insumos únicos: ~90 queries sequenciais. Para 100 insumos: ~300 queries.

**Recomendação:** Batch lookup de De/Para com `IN` query, batch lookup de `BaseTcpo`, e batch `get` dos itens BCU agrupados por tipo.

**Sprint sugerida:** F2-DT-03

---

#### A-03 — N+1 queries em `listar_componentes_diretos`

**Arquivo:** `app/backend/services/servico_catalog_service.py`
**Severidade:** Alta
**Categoria:** Performance

```python
for comp in composicoes:
    filho = await base_repo.get_by_id(comp.insumo_filho_id)  # 1 query por filho
```

Cada expansão de nó na tree table (F2-13) dispara N queries para N filhos. Para um serviço com 20 componentes: 20 queries por clique de expansão.

**Recomendação:** Substituir por `SELECT * FROM base_tcpo WHERE id IN (...)` com os IDs dos filhos coletados em batch.

**Sprint sugerida:** F2-DT-03

---

#### A-04 — Resource leak em `proposta_export_service.py` (CWE-400/664)

**Arquivo:** `app/backend/services/proposta_export_service.py` — linhas 120–121 e 131–132
**Severidade:** Alta
**Categoria:** Segurança (CWE-400, CWE-664)

`BytesIO` não é fechado se `wb.save()` ou `doc.build()` lançarem exceção. Identificado pelo scanner em F2-05 e ainda não corrigido. Em produção com muitas requisições simultâneas, acumula memória.

```python
# Atual — sem proteção contra exceção
buffer = BytesIO()
wb.save(buffer)

# Correto
with BytesIO() as buffer:
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
```

**Sprint sugerida:** F2-DT-04

---

#### A-05 — `nova_versao` usa `db.expunge` para clonar — padrão frágil

**Arquivo:** `app/backend/services/proposta_versionamento_service.py`
**Severidade:** Alta
**Categoria:** Qualidade + Confiabilidade

```python
self.db.expunge(item)
item.id = uuid.uuid4()
item.proposta_id = nova.id
self.db.add(item)
```

Expunge + mutação direta do objeto SQLAlchemy é um padrão não-idiomático que pode causar comportamento inesperado se o objeto tiver relacionamentos carregados ou se a sessão tiver estado pendente. O risco aumenta com os modelos `PropostaPcMobilizacao` que têm filhos `PropostaPcMobilizacaoQuantidade`.

**Recomendação:** Substituir por criação explícita de novos objetos com os campos copiados, sem expunge. Usar `dataclasses.asdict` ou mapeamento explícito campo a campo.

**Sprint sugerida:** F2-DT-04

---

#### A-06 — `require_proposta_role` faz 2 queries por chamada

**Arquivo:** `app/backend/core/dependencies.py`
**Severidade:** Alta
**Categoria:** Performance

```python
result = await db.execute(select(Proposta.proposta_root_id).where(...))  # query 1
papel = await svc.papel_efetivo(acl_id, current_user.id)                 # query 2
```

Cada endpoint protegido por `require_proposta_role` dispara 2 queries. Com múltiplos endpoints encadeados em um fluxo (ex: montar histograma → editar item → alocar recurso), o overhead se acumula.

**Recomendação:** Combinar em uma única query com JOIN em `proposta_acl`, ou cachear o resultado por `(proposta_id, user_id)` dentro do request lifecycle usando `request.state`.

**Sprint sugerida:** F2-DT-03

---

### 🟡 Médios

#### M-01 — `montar_histograma` duplica itens sem mapeamento De/Para em re-execuções

**Arquivo:** `app/backend/repositories/proposta_pc_repository.py` — `bulk_upsert`
**Severidade:** Média
**Categoria:** Lógica de Negócio

O `bulk_upsert` tem a cláusula `WHERE editado_manualmente IS FALSE` correta no `on_conflict_do_update`. Porém, itens com `bcu_item_id=None` (sem mapeamento De/Para) sempre geram novo `id` via `uuid.uuid4()` — nunca conflitam na constraint `(proposta_id, bcu_item_id)` quando `bcu_item_id` é NULL, pois `NULL != NULL` em SQL. Isso significa que re-executar `montar_histograma` duplica itens sem mapeamento.

**Recomendação:** Para itens sem `bcu_item_id`, usar `codigo_origem` como chave de upsert alternativa, ou filtrar itens já existentes antes de inserir usando `SELECT ... WHERE proposta_id = ? AND bcu_item_id IS NULL AND codigo_origem = ?`.

**Sprint sugerida:** F2-DT-04

---

#### M-02 — `detectar_divergencias` faz 5 queries sequenciais por chamada

**Arquivo:** `app/backend/services/histograma_service.py`
**Severidade:** Média
**Categoria:** Performance

Cada `GET /propostas/{id}/histograma` dispara 5 queries de divergência (MO, EQP, EPI, FER, ENC) além das 7 queries de listagem. Total: ~12 queries por GET do histograma.

**Recomendação:** Unificar em uma única query com `UNION ALL` ou executar em paralelo com `asyncio.gather(*[query_mo(), query_eqp(), query_epi(), query_fer(), query_enc()])`.

**Sprint sugerida:** F2-DT-03

---

#### M-03 — Aba "Capa" do Excel exportado com dado incorreto

**Arquivo:** `app/backend/services/proposta_export_service.py` — linha 52
**Severidade:** Média
**Categoria:** Bug de Dados

```python
capa["B1"] = "Cliente"
capa["B2"] = proposta.codigo   # label é "Cliente" mas valor é o código da proposta
```

A célula `B2` tem label "Cliente" mas exibe o código da proposta. O nome do cliente só aparece em `B5`. Identificado em F2-05 e não corrigido. Dado semanticamente incorreto no Excel exportado para o usuário final.

**Recomendação:** `capa["B2"] = cliente.nome_fantasia if cliente else ""`

**Sprint sugerida:** F2-DT-04

---

#### M-04 — `aceitar_valor_bcu` seta `cpu_desatualizada=True` incorretamente

**Arquivo:** `app/backend/services/histograma_service.py`
**Severidade:** Média
**Categoria:** Lógica de Negócio

`aceitar_valor_bcu` seta `editado_manualmente = False` e atualiza `valor_bcu_snapshot` — correto. Porém também seta `cpu_desatualizada = True`, o que é semanticamente incorreto: aceitar o valor BCU atual significa que o histograma está sincronizado com a BCU, não que a CPU está desatualizada.

**Recomendação:** Remover `proposta.cpu_desatualizada = True` de `aceitar_valor_bcu`. A CPU só deve ser marcada como desatualizada quando o valor do histograma diverge do que foi usado no último cálculo.

**Sprint sugerida:** F2-DT-04

---

#### M-05 — `require_cliente_access` ainda em uso em endpoints que podem precisar de revisão

**Arquivos:** `busca.py`, `extracao.py`, `homologacao.py`, `servicos.py`, `versoes.py`
**Severidade:** Média
**Categoria:** Consistência Arquitetural

Estes endpoints usam o modelo de autorização por cliente (pré-F2-08). Para endpoints de busca e catálogo isso é correto (são recursos de cliente). Para `versoes.py` e `homologacao.py` que operam sobre itens próprios do cliente, a consistência com o novo modelo RBAC por proposta deve ser avaliada.

**Recomendação:** Revisar se `versoes.py` e `homologacao.py` deveriam migrar para `require_proposta_role` ou se o modelo por cliente é intencional para esses recursos. Documentar a decisão explicitamente.

**Sprint sugerida:** F2-DT-01 (revisão de segurança)

---

#### M-06 — `proposta_versionamento_service.nova_versao` tem 8 imports locais dentro do método

**Arquivo:** `app/backend/services/proposta_versionamento_service.py`
**Severidade:** Média
**Categoria:** Qualidade de Código

```python
async def nova_versao(self, ...):
    import uuid
    from sqlalchemy import select
    from backend.models.proposta_pc import (...)
    from backend.models.proposta_recurso_extra import PropostaRecursoExtra
```

8 imports locais dentro do corpo do método. Viola PEP 8 e as guidelines do projeto. Aumenta o overhead de cada chamada e dificulta análise estática e ferramentas de linting.

**Recomendação:** Mover todos os imports para o topo do arquivo.

**Sprint sugerida:** F2-DT-04

---

#### M-07 — `ExportMenu` não trata erros de download

**Arquivo:** `app/frontend/src/features/proposals/components/ExportMenu.tsx`
**Severidade:** Média
**Categoria:** UX + Qualidade Frontend

Erros de rede em `handleExcel`/`handlePdf` são silenciados — o usuário não recebe feedback. O bloco `try/finally` garante que `busy` volta a `false`, mas a exceção é descartada silenciosamente. Identificado em F2-05 e não corrigido.

```tsx
// Atual — erro silencioso
try {
  const blob = await proposalsApi.exportExcel(propostaId);
  triggerDownload(blob, ...);
} finally {
  setBusy(false);
}

// Recomendado
const [error, setError] = useState<string | null>(null);
try {
  const blob = await proposalsApi.exportExcel(propostaId);
  triggerDownload(blob, ...);
} catch {
  setError('Falha ao exportar. Tente novamente.');
} finally {
  setBusy(false);
}
```

**Sprint sugerida:** F2-DT-05

---

#### M-08 — `ExpandableTreeRow` não exibe `codigo_origem` para filhos recursivos

**Arquivo:** `app/frontend/src/features/proposals/components/ExpandableTreeRow.tsx`
**Severidade:** Média
**Categoria:** UX + Contrato de API

```tsx
item={{
  id: child.insumo_filho_id,
  descricao: child.descricao_filho,
  codigo_origem: undefined,   // sempre undefined para filhos
  ...
}}
```

`ComposicaoComponenteResponse` não inclui `codigo_origem` do filho. A coluna "Código" exibe `—` em todos os níveis exceto o raiz, tornando a tree table menos informativa.

**Recomendação:** Adicionar `codigo_origem: str | None` ao schema `ComposicaoComponenteResponse` no backend (`servico_catalog_service.py`) e propagar para o frontend.

**Sprint sugerida:** F2-DT-05

---

#### M-09 — `ProposalPcRepository` com nome inconsistente com o padrão do projeto

**Arquivo:** `app/backend/repositories/proposta_pc_repository.py`
**Severidade:** Média
**Categoria:** Consistência de Nomenclatura

Classe nomeada `ProposalPcRepository` (inglês) enquanto todo o projeto usa português: `PropostaRepository`, `PropostaAclRepository`, `BcuRepository`, `PropostaRecursoExtraRepository`. Inconsistência que dificulta busca por padrão e onboarding de novos desenvolvedores.

**Recomendação:** Renomear para `PropostaPcRepository` e atualizar todos os imports (3 arquivos: `histograma_service.py`, `proposta_versionamento_service.py`, `test_histograma_service.py`).

**Sprint sugerida:** F2-DT-04

---

### 🟢 Baixos

#### B-01 — `bcu.py` e `bcu_service.py` usam `== True` em vez de `is_(True)`

**Arquivos:** `app/backend/api/v1/endpoints/bcu.py` linha 68; `app/backend/services/bcu_service.py` linha 568
**Severidade:** Baixa
**Categoria:** Qualidade de Código

```python
# Atual
.where(BcuCabecalho.is_ativo == True)

# Correto para SQLAlchemy
.where(BcuCabecalho.is_ativo.is_(True))
```

Para SQLAlchemy, `== True` funciona mas `is_(True)` é o idioma correto e evita warnings do linter e comportamento inesperado com valores `None`.

**Sprint sugerida:** F2-DT-04

---

#### B-02 — `proposta_export_service.gerar_excel` com 55 linhas (função grande)

**Arquivo:** `app/backend/services/proposta_export_service.py`
**Severidade:** Baixa
**Categoria:** Manutenibilidade

As 4 abas do Excel poderiam ser métodos privados `_build_capa`, `_build_resumo`, `_build_cpu`, `_build_composicoes`. Identificado pelo scanner em F2-05 e não corrigido. Dificulta testes unitários por aba.

**Sprint sugerida:** F2-DT-04

---

#### B-03 — `bcu_service.importar_bcu` com complexidade ciclomática 30

**Arquivo:** `app/backend/services/bcu_service.py`
**Severidade:** Baixa
**Categoria:** Manutenibilidade

Função de 300+ linhas com CC=30 (top 1% do dataset de referência). Candidato para extração de métodos por aba: `_importar_mao_obra`, `_importar_equipamentos`, `_importar_encargos`, `_importar_epi`, `_importar_ferramentas`, `_importar_mobilizacao`.

**Sprint sugerida:** F2-DT-04

---

#### B-04 — `histograma_service.montar_histograma` com CC=27

**Arquivo:** `app/backend/services/histograma_service.py`
**Severidade:** Baixa
**Categoria:** Manutenibilidade

Mesma estrutura que `bcu_service.importar_bcu` — loop por tipo com branches por `BcuTableType`. Candidato para extração de método `_processar_insumo(insumo_id, de_para, proposta_id) -> dict | None`.

**Sprint sugerida:** F2-DT-04

---

#### B-05 — Cobertura de testes insuficiente para módulos F2-11

**Arquivos:** `app/backend/tests/unit/`
**Severidade:** Baixa
**Categoria:** Qualidade de Testes

`test_histograma_endpoints.py` e testes de `cpu_custo_service` com prioridade `proposta_pc_*` > `bcu.*` > `BaseTcpo` não foram confirmados na varredura. O technical review de F2-11 declara "180+ testes" — abaixo da meta de 245+ do briefing.

**Recomendação:** Executar `pytest --cov=backend --cov-report=term-missing` para mapear gaps reais de cobertura.

**Sprint sugerida:** F2-DT-04

---

#### B-06 — Variável `old_mob_id` declarada mas não usada

**Arquivo:** `app/backend/services/proposta_versionamento_service.py`
**Severidade:** Baixa
**Categoria:** Dead Code

```python
old_mob_id = mob.id   # declarada mas nunca referenciada
mob.id = uuid.uuid4()
```

Dead code. Pode causar confusão sobre intenção do desenvolvedor.

**Sprint sugerida:** F2-DT-04

---

#### B-07 — Arquivo de tema duplicado no frontend

**Arquivos:** `app/frontend/src/app/theme.ts` e `app/frontend/src/app/theme/theme.ts`
**Severidade:** Baixa
**Categoria:** Organização de Código

Dois arquivos de tema no mesmo diretório com nomes similares. Risco de divergência de configuração de tema entre componentes que importam de caminhos diferentes.

**Recomendação:** Verificar qual é o arquivo canônico e remover o duplicado, atualizando os imports.

**Sprint sugerida:** F2-DT-05

---

#### B-08 — Variável de sistema `DEBUG=release` não documentada

**Arquivo:** Nenhum (ausência de documentação)
**Severidade:** Baixa
**Categoria:** Documentação + Onboarding

A variável de sistema que bloqueia os testes (C-03) não está documentada em nenhum `README`, `CONTRIBUTING.md` ou `.env.example`. Novos desenvolvedores encontrarão o mesmo problema sem diagnóstico.

**Recomendação:** Adicionar seção "Configuração do Ambiente de Desenvolvimento" no `README.md` documentando o problema e a solução.

**Sprint sugerida:** F2-DT-02

---

## Mapa de Sprints de Débito Técnico Recomendadas

| Sprint | Tipo | Itens cobertos | Esforço estimado | Prioridade |
|---|---|---|---|---|
| **F2-DT-01** | Segurança + Limpeza Arquitetural | C-01, C-02, M-05 | 4–6h | P0 |
| **F2-DT-02** | Ambiente + CI/CD | C-03, B-08 | 1–2h | P0 |
| **F2-DT-03** | Performance (N+1 + queries) | A-01, A-02, A-03, A-06, M-02 | 6–8h | P1 |
| **F2-DT-04** | Qualidade Backend | A-04, A-05, M-01, M-03, M-04, M-06, M-09, B-01, B-02, B-03, B-04, B-05, B-06 | 6–8h | P2 |
| **F2-DT-05** | Qualidade Frontend | M-07, M-08, B-07 | 2–3h | P2 |

**Total estimado:** 19–27h de trabalho técnico

---

## Tabela Consolidada de Débitos

| ID | Severidade | Categoria | Arquivo Principal | Sprint |
|---|---|---|---|---|
| C-01 | Crítico | Segurança + Arquitetura | `admin.py` | F2-DT-01 |
| C-02 | Crítico | Arquitetura + Segurança | `import_preview_service.py` | F2-DT-01 |
| C-03 | Crítico | Ambiente + CI/CD | `.env` / sistema | F2-DT-02 |
| A-01 | Alto | Performance | `propostas.py` | F2-DT-03 |
| A-02 | Alto | Performance | `histograma_service.py` | F2-DT-03 |
| A-03 | Alto | Performance | `servico_catalog_service.py` | F2-DT-03 |
| A-04 | Alto | Segurança (CWE-400/664) | `proposta_export_service.py` | F2-DT-04 |
| A-05 | Alto | Confiabilidade | `proposta_versionamento_service.py` | F2-DT-04 |
| A-06 | Alto | Performance | `dependencies.py` | F2-DT-03 |
| M-01 | Médio | Lógica de Negócio | `proposta_pc_repository.py` | F2-DT-04 |
| M-02 | Médio | Performance | `histograma_service.py` | F2-DT-03 |
| M-03 | Médio | Bug de Dados | `proposta_export_service.py` | F2-DT-04 |
| M-04 | Médio | Lógica de Negócio | `histograma_service.py` | F2-DT-04 |
| M-05 | Médio | Consistência Arquitetural | `versoes.py`, `homologacao.py` | F2-DT-01 |
| M-06 | Médio | Qualidade de Código | `proposta_versionamento_service.py` | F2-DT-04 |
| M-07 | Médio | UX + Frontend | `ExportMenu.tsx` | F2-DT-05 |
| M-08 | Médio | UX + Contrato de API | `ExpandableTreeRow.tsx` | F2-DT-05 |
| M-09 | Médio | Nomenclatura | `proposta_pc_repository.py` | F2-DT-04 |
| B-01 | Baixo | Qualidade de Código | `bcu.py`, `bcu_service.py` | F2-DT-04 |
| B-02 | Baixo | Manutenibilidade | `proposta_export_service.py` | F2-DT-04 |
| B-03 | Baixo | Manutenibilidade | `bcu_service.py` | F2-DT-04 |
| B-04 | Baixo | Manutenibilidade | `histograma_service.py` | F2-DT-04 |
| B-05 | Baixo | Cobertura de Testes | `tests/unit/` | F2-DT-04 |
| B-06 | Baixo | Dead Code | `proposta_versionamento_service.py` | F2-DT-04 |
| B-07 | Baixo | Organização | `app/theme.ts` (duplicado) | F2-DT-05 |
| B-08 | Baixo | Documentação | `README.md` (ausente) | F2-DT-02 |

---

*Gerado por Amazon Q — QA Engineer*
*Nenhuma linha de código foi alterada durante esta análise.*
