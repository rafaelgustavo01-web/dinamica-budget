# Checkpoint Tecnico Completo — Fase 1 & Fase 2

**Data:** 2026-04-27  
**Escopo:** Backend + Frontend (todas as sprints S-01..F2-13)  
**Metodologia:** Analise estatica automatizada (grep/ast) + inspecao manual de hotspots  
**Regra:** Nenhuma linha de codigo alterada — apenas documentacao de achados.

---

## Resumo Executivo

| Categoria | Critico | Alto | Medio | Baixo |
|---|---|---|---|---|
| Arquitetura | 1 | 2 | 2 | 1 |
| Performance | 1 | 1 | 2 | 1 |
| Testes | 1 | 0 | 0 | 0 |
| Seguranca | 1 | 0 | 1 | 0 |
| Qualidade de Codigo | 0 | 2 | 2 | 2 |
| **Total** | **4** | **5** | **7** | **4** |

---

## 1. Severidade CRITICO (Acao obrigatoria antes de PROD)

### C-01: Frontend sem nenhum teste unitario
- **Arquivos:** `app/frontend/src/**/*.tsx` (95 arquivos, 13.498 linhas)
- **Problema:** Taxa de cobertura de testes no frontend = **0,0%**. Zero arquivos `.test.ts` ou `.spec.tsx`.
- **Risco:** Regressoes de UI nao detectaveis por CI; refactoring de componentes (ex: ExpandableTreeRow, HistogramaTabs) sem rede de seguranca.
- **Evidencia:** `test_ts_files = 0, test_ts_lines = 0`
- **Recomendacao:** Criar sprint de correcao para adicionar testes nos componentes criticos (Histograma, Propostas, Composicoes) usando React Testing Library + MSW.

### C-02: SQL direto em 8 arquivos de endpoint (violacao S-02)
- **Arquivos:** `bcu.py` (19 linhas SQL), `extracao.py` (4), `propostas.py` (6), `busca.py` (2), `composicoes.py` (1), `health.py` (1), `proposta_acl.py` (1), `usuarios.py` (1)
- **Problema:** A sprint S-02 consolidou arquitetura em camadas (endpoint -> service -> repository), mas `bcu.py` e outros ainda contem queries SQL diretas (`db.execute(select(...))`), regras de negocio inline e validacoes.
- **Risco:** Acoplamento entre API e schema de banco; dificuldade de testar endpoints isoladamente; quebra de contrato de camadas.
- **Exemplo:** `bcu.py:45` — `_get_cabecalho` faz `select(BcuCabecalho)` diretamente no endpoint ao inves de delegar ao `BcuRepository`.
- **Recomendacao:** Refatorar `bcu.py` para usar `BcuRepository` + `BcuService` exclusivamente. Replicar padrao dos endpoints `propostas.py` que ja usam services.

### C-03: Cache in-memory volatil no ETL Service
- **Arquivo:** `app/backend/services/etl_service.py`
- **Problema:** O singleton `etl_service` mantem `_cache: dict[str, _EtlParseResult]` em memoria RAM. Em ambiente multi-processo (uvicorn workers > 1) ou restart, o cache eh perdido e tokens ficam invalidos.
- **Risco:** Falhas intermitentes em upload -> execute em producao; nao escala horizontalmente.
- **Recomendacao:** Substituir por cache Redis/memcached ou persistir preview em tabela temporaria no PostgreSQL.

### C-04: N+1 Queries em multiplos servicos criticos
- **Arquivos:** `histograma_service.py`, `servico_catalog_service.py`, `cpu_geracao_service.py`, `proposta_versionamento_service.py`, `bcu_service.py`
- **Problema:** For-loops iterando sobre collections e disparando `await db.get()` / `await repo.get_by_id()` para cada item.
- **Impacto:** Cada composicao com N itens gera N+1 queries. Em propostas grandes (PQ com 500+ itens), isso explode para milhares de round-trips ao PostgreSQL.
- **Exemplos:**
  - `histograma_service.py:77-78` — loop sobre insumos, `await self.de_para_repo.get_by_base_tcpo_id(insumo_id)`
  - `servico_catalog_service.py:164-165` — loop sobre composicoes, `await base_repo.get_by_id(comp.insumo_filho_id)`
  - `cpu_geracao_service.py:66-71` — loop sobre itens PQ, query por item
- **Recomendacao:** Usar `selectinload` (SQLAlchemy eager loading) ou batch queries (`WHERE id IN (...)`) para carregar filhos em bulk.

---

## 2. Severidade ALTO (Acao recomendada na proxima milestone)

### A-01: God Classes / Services excessivamente grandes
- **Arquivos:**
  - `servico_catalog_service.py`: 657 linhas
  - `bcu_service.py`: 571 linhas
  - `etl_service.py`: 514 linhas
  - `histograma_service.py`: 504 linhas
  - `busca_service.py`: 461 linhas
- **Problema:** Classes com multiplas responsabilidades (SRP violado). Dificultam manutencao, review e testes.
- **Recomendacao:** Quebrar em services menores (ex: `BcuImportService`, `BcuQueryService`, `HistogramaMontagemService`, `HistogramaDivergenciaService`).

### A-02: Drift de tipos monetarios (DecimalValue vs number)
- **Arquivos frontend:** `admin.ts`, `busca.ts`, `extraction.ts`, `proposta_pc.ts`
- **Problema:** Campos monetarios (`custo_unitario`, `custo_total`, `custo_base`) declarados como `number` no frontend enquanto o backend retorna `Decimal` (serializado como string). Isso pode causar perda de precisao em aritmetica de ponto flutuante.
- **Risco:** Calculos de totais no frontend divergindo do backend por erros de arredondamento (ex: `0.1 + 0.2 !== 0.3`).
- **Recomendacao:** Criar tipo `DecimalValue = string` no frontend (ja existe em `common.ts`) e aplicar consistentemente em todos os contratos. Usar biblioteca como `decimal.js` para operacoes.

### A-03: Duplicacao de codigo nos componentes de Histograma
- **Arquivos:** `HistogramaTabMaoObra.tsx` (179 linhas) e `HistogramaTabGenerica.tsx` (170 linhas)
- **Problema:** Ambos possuem 7 imports e 6 hooks identicos; estrutura de tabela, edicao inline, badges de divergencia e logica de mutacao sao 80% iguais.
- **Risco:** Manutencao duplicada; fix em um nao propaga para o outro.
- **Recomendacao:** Extrair hook `useHistogramaEdicao` e componente base `HistogramaEditableTable` compartilhado.

### A-04: Hardcoded strings no frontend (sem i18n)
- **Volume:** ~678 ocorrencias de strings portuguesas hardcoded em 95 arquivos TSX.
- **Problema:** Textos de UI espalhados em componentes; impossibilita internacionalizacao futura; dificulta revisao de copy.
- **Recomendacao:** Consolidar em arquivos de mensagens (ja existe `FeedbackMessages.ts` mas cobre apenas toasts/erros). Expandir para todos os labels, titulos e descricoes.

### A-05: AsyncMock warnings nao resolvidos na suite de testes
- **Arquivos:** `test_bcu_de_para_service.py`, `test_explosao_recursiva.py`, `test_proposta_acl_endpoints.py`, etc.
- **Problema:** `RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited` indica mocks async incorretamente configurados.
- **Risco:** Falsos positivos em testes; comportamento nao deterministico.
- **Recomendacao:** Auditoria dos testes com alta densidade de mocks (>20 por arquivo) para corrigir `AsyncMock` vs `MagicMock`.

---

## 3. Severidade MEDIO (Debito tecnico acumulavel)

### M-01: Componentes frontend grandes (>400 linhas)
- **Arquivos:** `UsersPage.tsx` (640), `BcuPage.tsx` (506), `CompositionsPage.tsx` (487)
- **Problema:** Dificil navegacao e teste; mistura de UI, estado, logica de negocio e efeitos colaterais.
- **Recomendacao:** Extrair sub-componentes e custom hooks (ex: `useComposicoes`, `useBcuList`).

### M-02: Paginacao e limites inconsistentes
- **Problema:** Algumas queries de listagem nao possuem `LIMIT` explícito ou usam paginacao soft (offset/limit) sem cursor. Em tabelas que crescem (base_tcpo, propostas), isso pode causar timeouts.
- **Exemplo:** `bcu.py:59` — `select(BcuCabecalho).order_by(...)` sem `.limit()`.
- **Recomendacao:** Revisar todos os endpoints de listagem para garantir limites hard (max 100) e indices adequados.

### M-03: Falta de indices em FKs das migrations recentes
- **Migrations:** 021 (proposta_acl), 022 (versionamento), 023 (bcu), 024 (histograma)
- **Problema:** Migrations criam tabelas mas nem sempre criam indexes em todas as FKs e campos de busca. `ix_de_para_base_tcpo` existe, mas outras FKs (ex: `proposta_pc_mao_obra.proposta_id`) podem nao estar indexadas.
- **Risco:** Degradacao de performance em JOINs e filtros conforme volume cresce.
- **Recomendacao:** Auditoria de schema para adicionar indexes faltantes via migration de correcao.

### M-04: Coexistencia de duas abordagens de tabela
- **Problema:** O projeto usa `DataTable` (componente generico) em 8 paginas, mas `CompositionsPage` e as abas de Histograma usam `Table`/`TableRow` MUI nativo.
- **Risco:** Experiencia de usuario inconsistente; duplicacao de logica de paginacao/filtros.
- **Recomendacao:** Decidir se `DataTable` sera evoluido para suportar tree/expansible ou se todas as tabelas migrarao para MUI nativo.

### M-05: `.env` fisico presente no working tree
- **Arquivo:** `app/.env`
- **Problema:** Embora `.env` esteja no `.gitignore`, o arquivo existe no disco. Risco de commit acidental via `git add -A` ou copia para container Docker sem `.dockerignore` adequado.
- **Recomendacao:** Mover secrets para `.env.local` (gitignored) e manter apenas `.env.example` no repo. Verificar `.dockerignore`.

### M-06: Inconsistencia no tratamento de `cpu_desatualizada`
- **Arquivos:** `cpu_geracao_service.py` (seta `False`), `histograma_service.py` (seta `True`), `proposta_recurso_extra_service.py` (seta `True`), `proposta_versionamento_service.py` (nao clona flag?)
- **Problema:** A flag eh setada por multiplos services mas nao ha um unico ponto de controle. Risco de race conditions ou estados inconsistentes.
- **Recomendacao:** Centralizar logica de `cpu_desatualizada` em um `PropostaStateService` com transacao explicita.

---

## 4. Severidade BAIXO (Melhorias de polimento)

### B-01: `values_only=False` no ETL (custo de memoria)
- **Arquivo:** `etl_service.py`
- **Problema:** Leitura de Excel com `values_only=False` carrega objetos de celula completos (fonte, estilo, alinhamento). Para arquivos TCPO grandes (~60k linhas), memoria pode picar.
- **Mitigacao atual:** Aceitavel para tamanho atual; monitorar se arquivos crescerem.

### B-02: Imports nao utilizados e variaveis mortas
- **Exemplo:** `CompositionsPage.tsx` removia `setPageSize` (corrigido em F2-13); outros arquivos podem ter imports nao usados.
- **Recomendacao:** Rodar `eslint --fix` ou `tsc --noEmit` com flag `noUnusedLocals` para limpeza automatica.

### B-03: `.claude/` e `.agents/` no repositorio
- **Problema:** Diretorios de configuracao de agentes AI (`.claude/get-shit-done/`, `.agents/skills/`) estao no working tree. Nao parecem estar no `.gitignore`.
- **Risco:** Poluicao do repo; potencial vazamento de prompts internos.
- **Recomendacao:** Adicionar `.claude/` e `.agents/` ao `.gitignore` (exceto se forem intencionalmente versionados).

### B-04: Comentarios e codigo morto
- **Exemplo:** `etl_service.py` possui comentarios de debugging; `scripts/analyze_tcpo.py` eh um script ad-hoc nao integrado ao pipeline.
- **Recomendacao:** Remover scripts temporarios ou mover para `scripts/archive/`.

---

## 5. Matriz de Priorizacao para Proximas Sprints

| # | Debito | Severidade | Esforco estimado | Sprint sugerida |
|---|---|---|---|---|
| 1 | Frontend: zero testes unitarios | CRITICO | 3-4 dias | **F2-14** |
| 2 | SQL direto em endpoints (bcu.py lider) | CRITICO | 2-3 dias | **F2-15** |
| 3 | N+1 queries em servicos criticos | CRITICO | 3-4 dias | **F2-15** |
| 4 | Cache in-memory ETL | CRITICO | 1-2 dias | **F2-16** |
| 5 | God classes backend | ALTO | 3-4 dias | **F2-16** |
| 6 | Drift DecimalValue frontend | ALTO | 1-2 dias | **F2-14** |
| 7 | Duplicacao Histograma components | ALTO | 1 dia | **F2-14** |
| 8 | Hardcoded strings (i18n) | ALTO | 2-3 dias | **F2-17** |
| 9 | AsyncMock warnings em testes | ALTO | 1-2 dias | **F2-14** |
| 10 | Indices faltantes em migrations | MEDIO | 1 dia | **F2-15** |
| 11 | Paginacao inconsistente | MEDIO | 1-2 dias | **F2-15** |
| 12 | Componentes frontend grandes | MEDIO | 2-3 dias | **F2-17** |

---

## 6. Conclusao do Arquiteto

O projeto esta funcional e com arquitetura backend solida (camadas, transacoes, RBAC), mas acumulou debitos tecnicos previsiveis de uma Fase 2 acelerada:

1. **Frontend** eh o maior gargalo: zero testes + drift de tipos + strings hardcoded + componentes grandes.
2. **Backend** tem violacoes de camadas (SQL em endpoints) e N+1 que precisam de atencao antes que o volume de dados cresca.
3. **Performance** esta aceitavel para o tamanho atual (~200 testes passam, build OK), mas os N+1 e o cache in-memory sao bombas-relógio para escala.

**Recomendacao do PO:** Aprovar uma **Sprint F2-14** focada em "Frontend Testing + Type Safety" e uma **Sprint F2-15** focada em "Backend Layer Cleanup + Performance (N+1 + SQL migration)" antes de declarar o projeto pronto para go-live.
