# ROADMAP - Dinamica Budget

Data base: 2026-04-22
Fonte: backlog tecnico atual + analise de arquitetura do repositorio.

## Visao de Entrega
Objetivo: levar o projeto para um estado de pre-producao robusto em arquitetura, seguranca, testes e operacao on-premise.

## Milestone 1 - Seguranca e Arquitetura Base (P0)

### Fase 1.1 - Alinhamento de Autorizacao ao Modelo On-Premise **[INICIADA]**
- Revisar autorizacao em endpoints de composicao e versoes conforme regra de negocio.
- Garantir que orcamentistas tenham acesso aos clientes conforme politica operacional definida.
- Entregavel: testes de integracao cobrindo a politica nova de acesso.
- Sprint: `S-01` | Selecionada em: 2026-04-22

### Fase 1.2 - Consolidacao de Camadas (Endpoint -> Service -> Repository)
- Remover regra de negocio e SQL direto de endpoints criticos.
- Centralizar regras em services com contratos claros.
- Entregavel: endpoints enxutos e services testaveis.

### Fase 1.3 - Fronteira Transacional e Consistencia
- Revisar estrategia de commit implicito no request scope.
- Definir padrao transacional por caso de uso.
- Entregavel: documento tecnico + ajustes validados por regressao.

## Milestone 2 - Qualidade e Confiabilidade (P1)

### Fase 2.1 - Hardening de RBAC e Seguranca de API
- Expandir testes de autorizacao para rotas sensiveis.
- Executar checklist OWASP API basico.
- Entregavel: suite de seguranca com evidencias.

### Fase 2.2 - Suite de Testes e Gate de Qualidade
- Aumentar cobertura de services/endpoints criticos.
- Definir gate minimo (testes, lint, smoke).
- Entregavel: pipeline de verificacao reutilizavel.

### Fase 2.3 - Auditoria Pre-Release
- Revisar riscos residuais, lacunas e plano de mitigacao.
- Entregavel: checklist de go-live para QA.

## Milestone 3 - Performance de Busca e Operacao On-Premise (P1)

### Fase 3.1 - Benchmark de Busca (Fuzzy vs Semantica) **[INICIADA]**
- Medir latencia/precisao com carga realista.
- Reavaliar thresholds e ranking hibrido.
- Entregavel: relatorio de benchmark com recomendacoes.
- Sprint: `S-05` | Selecionada em: 2026-04-22

### Fase 3.2 - Evolucao do Pipeline de Embeddings
- Definir estrategia de re-embedding por versao de modelo.
- Planejar tuning de indice vetorial para PostgreSQL.
- Entregavel: plano operacional de embeddings em lote.

### Fase 3.3 - Runbook de Operacao e Incidentes
- Formalizar backup, restore, health-check e troubleshooting.
- Entregavel: runbook operacional para Windows Server intranet.

## Milestone 4 - Produto e Experiencia (P2)

### Fase 4.1 - Governanca de Permissoes na UI
- Decidir escopo do modulo de permissoes vs centralizacao em Usuarios.
- Eliminar placeholders criticos de governanca.
- Entregavel: criterio funcional fechado com PO.

### Fase 4.2 - UX de Fluxos Criticos
- Melhorar fluxo busca -> associacao -> homologacao.
- Priorizacao de melhorias com impacto operacional.
- Entregavel: backlog UX com criterios de aceite.

## Milestone 5 - Modulo de Orcamentos (P1)

> **Origem:** Demandada pelo PO em 2026-04-22.  
> **Documento de modelagem:** `docs/superpowers/plans/roadmap/MODELAGEM_ORCAMENTOS_FASE2.md`

### Fase 5.1 - Entidades e CRUD de Propostas
- Criar tabelas: `propostas`, `pq_importacoes`, `pq_itens`, `proposta_itens`, `proposta_item_composicoes`.
- CRUD de proposta com workflow (RASCUNHO → CPU_GERADA → APROVADA).
- Entregavel: API REST de propostas funcionando.
- Sprint: `S-09` | Dependencias: `S-02` (camadas), `S-05` (busca otimizada)

### Fase 5.2 - Importacao PQ e Match Inteligente
- Upload de planilha quantitativa (Excel/CSV) para `pq_itens`.
- Motor de match: busca fuzzy/semantica por item da PQ em BaseTcpo + ItemProprio.
- Interface de selecao/confirmacao de match pelo orcamentista.
- Entregavel: importacao + match automatico + confirmacao manual.
- Sprint: `S-10` | Dependencias: `S-09`

### Fase 5.3 - Geracao da CPU (Composicao de Precos Unitarios)
- Explosao de composicao para cada item confirmado (reutilizar logica existente).
- Custo unitario por insumo: lookup em PcTabelas (MO, equipamento, encargos, EPI).
- Aplicacao de BDI/indiretos e calculo de preco total.
- Entregavel: endpoint `/propostas/{id}/gerar-cpu` com rastreabilidade completa.
- Sprint: `S-11` | Dependencias: `S-10`

### Fase 5.4 - UX de Orcamentos (Frontend)
- Tela de criacao/edicao de proposta.
- Upload e visualizacao da PQ importada.
- Tela de match (sugestoes + selecao manual).
- Visualizacao da CPU com explosao de custos.
- Entregavel: modulo completo no React.
- Sprint: `S-12` | Dependencias: `S-11`

## Milestone 6 - Proposta Completa: Fase 3 (P1)

> **Origem:** Demandada pelo PO em 2026-04-25 apos analise de gaps do modulo de proposta entregue em S-09 a S-12.
> **Documento de referencia:** `docs/resumo_sugestoes.md` + analise de gaps Fase 3 (2026-04-25).

### Fase 6.1 - PQ Layout por Cliente **[INICIADA]**
- Entidade `PqLayoutCliente` (1:1 com cliente): configura aba, linha de inicio e mapeamento de colunas do Excel.
- Entidade `PqImportacaoMapeamento`: armazena mapeamento campo_sistema -> coluna_planilha.
- Endpoint `PUT /clientes/{id}/pq-layout` (admin) + `GET` (consulta).
- `pq_import_service.py` le layout do cliente antes de processar o arquivo; retorna `cols_detectadas` quando layout nao configurado.
- Migration Alembic `018_pq_layout_cliente.py`.
- Entregavel: importacao PQ flexivel por cliente, sem colunas fixas hardcoded.
- Sprint: `F2-01` | Dependencias: `S-09`, `S-10` | Worker: codex-5.3

### Fase 6.2 - Explosao Recursiva de Composicoes **[INICIADA]**
- Adicionar `pai_composicao_id` (self-ref FK), `nivel` (int), `e_composicao` (bool), `composicao_explodida` (bool) em `proposta_item_composicoes`.
- `cpu_explosao_service.py`: ao explodir, sinalizar insumos que tambem possuem composicao propria (`e_composicao=True`).
- Endpoint `POST /propostas/{id}/cpu/itens/{item_id}/explodir-sub`: dispara sub-explosao de insumo.
- Guard de profundidade: `nivel > 5` retorna erro 422 com mensagem clara.
- Migration Alembic `019_recursao_composicao.py`.
- Entregavel: arvore de composicao com N niveis; UI pode exibir hierarquia completa.
- Sprint: `F2-02` | Dependencias: `S-11` | Worker: kimi-k2.5

### Fase 6.3 - Exportacao Excel/PDF (folha de rosto + quadro-resumo) **[INICIADA]**
- Endpoint `GET /propostas/{id}/export/excel`: xlsx com abas Capa, Quadro-Resumo, CPU, Composicoes.
- Endpoint `GET /propostas/{id}/export/pdf`: folha de rosto com cabecalho do cliente e totais.
- Frontend: botao "Exportar" em ProposalDetailPage e ProposalCpuPage com download via Blob.
- Streaming de bytes (StreamingResponse) com headers HTTP corretos.
- Sprint: `F2-05` | Dependencias: `F2-03`, `F2-04` | Worker: kimi-k2.5

### Fase 6.4 - UX Complementar (edicao PQ, filtros, duplicacao) **[INICIADA]**
- PATCH `/propostas/{id}/pq/itens/{item_id}`: editar descricao/qtd/unidade pos-importacao.
- Filtros na lista de propostas: por status, por periodo, por busca textual.
- POST `/propostas/{id}/duplicar`: cria proposta nova como copia (sem gerar CPU).
- Frontend: tabela editavel inline em ProposalImportPage, filtros em ProposalsListPage, modal de duplicacao.
- Sprint: `F2-06` | Dependencias: `F2-03` | Worker: claude-sonnet-4-6

### Fase 6.5 - Tabelas de Recursos + Motor 4 Camadas **[INICIADA]**
- Nova entidade `PropostaResumoRecurso`: agregado por (tipo_recurso x insumo), gerado ao chamar `gerar-cpu`.
- Motor de busca 4 camadas formalizadas: (1) historico confirmado do cliente, (2) codigo exato, (3) fuzzy pg_trgm, (4) semantico pgvector.
- Refatorar `PqMatchService` para aplicar as 4 camadas em ordem com early-exit.
- Endpoint `GET /propostas/{id}/recursos`: agregado de recursos por tipo (MO, EQUIPAMENTO, INSUMO, FERRAMENTA, EPI).
- Sprint: `F2-07` | Dependencias: `F2-01`, `F2-02` | Worker: gemini-3.1

## Dependencias Entre Milestones
- M2 depende de M1 para estabilizar base arquitetural.
- M3 pode rodar em paralelo parcial com M2.
- M4 depende dos gates de seguranca/qualidade de M1 e M2.
- **M5 depende de M1 (arquitetura), M3 (busca) e das tabelas PcTabelas populadas.**
- **M6 depende de M5 integralmente concluido (S-09 a S-12 DONE).**

## Historico de Atualizacao
- 2026-04-22 13:45 (Research AI): roadmap inicial criado com 4 milestones e fases priorizadas.
- 2026-04-22 21:00 (Research AI): adicionado Milestone 5 — Modulo de Orcamentos (Fase 2) com 4 subfases e documento de modelagem conceitual.
- 2026-04-25 10:00 (Research AI): adicionado Milestone 6 — Proposta Completa (Fase 3) com 3 subfases: PQ Layout por Cliente (F2-01/codex), Explosao Recursiva (F2-02/kimi), Tabelas Recursos + Export Power Query (F2-03/TBD). Origem: analise de gaps pos-entrega S-09 a S-12.
- 2026-04-26 14:30 (PO/Supervisor/Scrum Master): Milestone 6 desmembrado para refletir backlog real. Fase 6.3 (TBD) renomeada para Exportacao Excel/PDF (F2-05/kimi). Adicionadas Fases 6.4 (UX complementar — F2-06/claude-sonnet-4-6) e 6.5 (Tabelas Recursos + Motor 4 Camadas — F2-07/gemini-3.1). Tres sprints INICIADAS em paralelo conforme alocacao por especialidade do worker.
