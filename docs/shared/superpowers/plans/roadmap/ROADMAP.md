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

### Fase 6.6 - RBAC por Proposta (descoplar de cliente) **[BACKLOG]**
- Nova tabela `proposta_acl(id, proposta_id, usuario_id, papel ENUM('OWNER','EDITOR','APROVADOR'), created_at, created_by)` com `UNIQUE(proposta_id, usuario_id, papel)`.
- Papel `VIEWER` é **default implicito** de qualquer usuario autenticado (nao mora em `proposta_acl`); `proposta_acl` so guarda elevacoes.
- Hierarquia: `ADMIN (global, via users.is_admin) > OWNER > EDITOR > APROVADOR > VIEWER`.
- Substituir `require_cliente_access(proposta.cliente_id, ...)` por `require_proposta_role(proposta_id, papel_minimo)` em `propostas.py`, `pq_importacao.py`, `cpu_geracao.py`, `proposta_export.py`, `proposta_recursos.py`.
- Regra de criacao: criador vira `OWNER` automaticamente.
- Regra de delete: somente `OWNER` (ou `ADMIN`).
- Migration 021: criar tabela + backfill (`OWNER` para `criado_por_id` de toda proposta existente).
- `GET /propostas` deixa de exigir `cliente_id` e retorna todas as propostas com `meu_papel` calculado.
- Endpoints de gestao de ACL: `GET /propostas/{id}/acl`, `POST /propostas/{id}/acl`, `DELETE /propostas/{id}/acl/{usuario_id}` (somente OWNER).
- Frontend: modal "Compartilhar proposta" em `ProposalDetailPage` (somente OWNER); esconder botoes de edit/delete conforme `meu_papel`.
- Sprint: `F2-08` | Dependencias: `F2-03`, `F2-04` | Worker: kimi-k2.5

### Fase 6.7 - Versionamento de Propostas + Workflow de Aprovacao **[INICIADA]**
- Tabela `propostas` ganha: `proposta_root_id UUID`, `numero_versao INT`, `versao_anterior_id UUID NULL`, `is_versao_atual BOOL`, `is_fechada BOOL`, `requer_aprovacao BOOL DEFAULT FALSE`, `aprovado_por_id UUID NULL`, `aprovado_em TIMESTAMP NULL`.
- Backfill: `proposta_root_id = id`, `numero_versao = 1`, `is_versao_atual = true`.
- Constraint: `UNIQUE(proposta_root_id, numero_versao)`.
- Novo status `AGUARDANDO_APROVACAO` no enum de status da proposta.
- ACL **herdada por root**: `require_proposta_role` resolve via `proposta.proposta_root_id`, nao via `proposta.id`.
- Endpoints: `POST /propostas/{id}/nova-versao` (clona snapshot, marca anterior como `is_versao_atual=false`), `POST /propostas/{id}/enviar-aprovacao` (so se `requer_aprovacao=true`, requer EDITOR), `POST /propostas/{id}/aprovar` + `POST /propostas/{id}/rejeitar` (requer APROVADOR), `GET /propostas/root/{root_id}/versoes`.
- Frontend: aba "Historico" em `ProposalDetailPage` listando versoes; botao "Nova versao" (EDITOR+); toggle "Esta versao precisa de aprovacao"; tela de fila de pendencias para APROVADOR.
- Migration 022.
- Sprint: `F2-09` | Dependencias: `F2-08` | Worker: claude-sonnet-4-6

## Milestone 7 - Compras e Negociacao (P1)

> **Origem:** Plano GPT (`docs/plano gpt.md`, secoes 8 e 9) — itens adiados na revisao do PO em 2026-04-26: mini modulo de Compras + custo base/ajustado + papel COMPRADOR.
> **Premissa:** suprimentos atua sobre as listas consolidadas da proposta (`PropostaResumoRecurso`) sem alterar a estrutura da CPU. Engenharia define o que e quanto; Compras define por quanto e de quem.
> **Pre-requisito:** F2-08 DONE (enum `proposta_papel_enum` existe), F2-09 DONE (versionamento — Compras opera sobre uma versao concreta).

### Fase 7.1 - Custo Base/Ajustado + Papel COMPRADOR **[BACKLOG]**
- Migration 023: alterar `proposta_resumo_recursos` adicionando `custo_unitario_base NUMERIC`, `custo_unitario_ajustado NUMERIC NULL`, `custo_total_base NUMERIC`, `custo_total_ajustado NUMERIC NULL`. Backfill: `custo_unitario_base = custo_unitario_medio`, `ajustado = NULL`.
- Migration 024: adicionar `COMPRADOR` ao enum `proposta_papel_enum` (`ALTER TYPE ... ADD VALUE 'COMPRADOR'`).
- Atualizar `PropostaPapel` (Python enum) + `PropostaAclService.HIERARQUIA` (COMPRADOR = nivel 2, abaixo de EDITOR=3 e acima de APROVADOR=2 — definir com PO).
- Service helper `custo_efetivo(recurso) -> Decimal`: retorna `ajustado ?? base`.
- Atualizar `gerar_resumo_recursos` para popular `custo_unitario_base` + `custo_total_base` (preservar valores ajustados existentes ao re-gerar — UPSERT por `(tipo_recurso, descricao_insumo, unidade)`).
- `GET /propostas/{id}/recursos` retorna ambos (base + ajustado + efetivo).
- Frontend: coluna "Custo ajustado" em `ProposalResourcesPage` (somente leitura por enquanto; edicao vem em 7.3).
- Sprint: `F2-10` | Dependencias: `F2-07`, `F2-08` | Worker: kimi-k2.5

### Fase 7.2 - Cotacoes (CRUD backend) **[BACKLOG]**
- Migration 025: tabela `operacional.proposta_compras_cotacoes(id, proposta_id, recurso_id FK proposta_resumo_recursos, fornecedor VARCHAR, valor_unitario NUMERIC, prazo_entrega_dias INT NULL, condicao_pagamento TEXT NULL, observacao TEXT NULL, selecionada BOOL DEFAULT FALSE, created_by FK usuarios, created_at, updated_at)`.
- Constraint: `UNIQUE(recurso_id) WHERE selecionada = TRUE` (so 1 cotacao selecionada por recurso).
- `PropostaCotacaoRepository` + `PropostaCotacaoService` com regras: criar (COMPRADOR+), listar por proposta/recurso, atualizar, deletar (so quem criou ou OWNER), selecionar (desmarca anteriores).
- Endpoints (todos require_proposta_role COMPRADOR ou superior):
  - `POST /propostas/{id}/cotacoes`
  - `GET /propostas/{id}/cotacoes` (com filtro opcional `recurso_id`)
  - `PATCH /propostas/{id}/cotacoes/{cotacao_id}`
  - `DELETE /propostas/{id}/cotacoes/{cotacao_id}`
  - `POST /propostas/{id}/cotacoes/{cotacao_id}/selecionar` — propaga `valor_unitario` para `recurso.custo_unitario_ajustado` (recalcula `custo_total_ajustado`)
- Sprint: `F2-11` | Dependencias: `F2-10` | Worker: kimi-k2.5

### Fase 7.3 - Frontend Tela de Compras **[BACKLOG]**
- Nova rota `/propostas/:id/compras` + entrada no menu de proposta (visivel para COMPRADOR/EDITOR/OWNER).
- Pagina `ProposalPurchasingPage`:
  - Tabela de recursos (reusa estrutura de `ProposalResourcesPage`) com colunas: descricao, qtd, custo base, custo ajustado, fornecedor selecionado, # cotacoes
  - Edicao inline de `custo_unitario_ajustado` (debounced) — escreve via PATCH no recurso
  - Botao por linha "Cotacoes" abre Drawer com lista + form de adicionar cotacao
  - Botao "Selecionar" por cotacao (chama endpoint, recarrega tabela)
- Componente `CotacaoForm`: fornecedor (text), valor_unitario (decimal), prazo_entrega_dias (int opcional), condicao_pagamento (text opcional), observacao (textarea opcional)
- Validacao client-side: `valor_unitario > 0`, fornecedor obrigatorio
- Sprint: `F2-12` | Dependencias: `F2-11` | Worker: claude-sonnet-4-6

### Fase 7.4 - Comparativo + Recalculo de Totais **[BACKLOG]**
- Endpoint `GET /propostas/{id}/comparativo-base-vs-ajustado` retorna agregado: `{ total_base, total_ajustado, diferenca_absoluta, percentual_economia, breakdown_por_tipo: [{tipo_recurso, total_base, total_ajustado, diferenca}] }`.
- Recalculo dos totais da `Proposta` (`total_geral`, `total_materiais`, `total_mao_obra`, etc.) considerando `custo_efetivo = ajustado ?? base` quando agregando.
- Trigger automatico: ao chamar `selecionar_cotacao` ou `PATCH recurso ajustado`, disparar `recalcular_totais_proposta(proposta_id)`.
- Card "Comparativo Base x Ajustado" em `ProposalDetailPage`: total base, total ajustado, % economia, com link para `/compras`.
- Coluna "Total Ajustado" em `ProposalsListPage` (ao lado de "Total").
- Sprint: `F2-13` | Dependencias: `F2-11`, `F2-12` | Worker: claude-sonnet-4-6

## Dependencias Entre Milestones
- M2 depende de M1 para estabilizar base arquitetural.
- M3 pode rodar em paralelo parcial com M2.
- M4 depende dos gates de seguranca/qualidade de M1 e M2.
- **M5 depende de M1 (arquitetura), M3 (busca) e das tabelas PcTabelas populadas.**
- **M6 depende de M5 integralmente concluido (S-09 a S-12 DONE).**
- **M7 depende de F2-08 (enum proposta_papel para acrescentar COMPRADOR) e F2-09 (versionamento — Compras opera sobre versao concreta da proposta).**

## Historico de Atualizacao
- 2026-04-22 13:45 (Research AI): roadmap inicial criado com 4 milestones e fases priorizadas.
- 2026-04-22 21:00 (Research AI): adicionado Milestone 5 — Modulo de Orcamentos (Fase 2) com 4 subfases e documento de modelagem conceitual.
- 2026-04-25 10:00 (Research AI): adicionado Milestone 6 — Proposta Completa (Fase 3) com 3 subfases: PQ Layout por Cliente (F2-01/codex), Explosao Recursiva (F2-02/kimi), Tabelas Recursos + Export Power Query (F2-03/TBD). Origem: analise de gaps pos-entrega S-09 a S-12.
- 2026-04-26 14:30 (PO/Supervisor/Scrum Master): Milestone 6 desmembrado para refletir backlog real. Fase 6.3 (TBD) renomeada para Exportacao Excel/PDF (F2-05/kimi). Adicionadas Fases 6.4 (UX complementar — F2-06/claude-sonnet-4-6) e 6.5 (Tabelas Recursos + Motor 4 Camadas — F2-07/gemini-3.1). Tres sprints INICIADAS em paralelo conforme alocacao por especialidade do worker.
- 2026-04-26 (PO apos analise critica do "plano gpt"): adicionadas Fases 6.6 (RBAC por Proposta — F2-08/kimi-k2.5) e 6.7 (Versionamento + Workflow de Aprovacao — F2-09/claude-sonnet-4-6). RBAC promovido a prioridade por gap de seguranca ativo (gating por cliente em todos os endpoints de proposta). Compras + papel COMPRADOR adiados para Milestone 7 (futuro). Custo base/ajustado tambem adiado por nao ter consumidor (Compras) nesta fase.
- 2026-04-26 (PO confirma Opcao A pos-despacho F2-08): criado Milestone 7 — Compras e Negociacao (P1) com 4 fases: 7.1 Custo Base/Ajustado + papel COMPRADOR (F2-10/kimi), 7.2 Cotacoes CRUD (F2-11/kimi), 7.3 Frontend Tela de Compras (F2-12/claude-sonnet-4-6), 7.4 Comparativo + Recalculo (F2-13/claude-sonnet-4-6). Premissa: Compras atua sobre listas consolidadas sem alterar CPU. Status BACKLOG aguardando F2-08 e F2-09 saindo de TESTED.


## Research Mining Sync — 2026-04-29

Fila `MINE_ROADMAP` acumulada foi consolidada pelo orquestrador e arquivada como DONE nos inboxes.

### Padrões promovidos para roadmap técnico

- **Autorização on-premise e RBAC por proposta:** manter `proposta_acl` como fronteira operacional e evitar acoplamento indevido a cliente quando a regra de negócio for proposta-orientada.
- **Arquitetura em camadas:** preservar endpoint enxuto → service → repository; SQL direto em endpoint deve ser considerado dívida técnica.
- **Motor de busca em cascata:** histórico confirmado → código exato → fuzzy → semântico continua sendo padrão reutilizável para match e catálogo.
- **Revisão manual de match:** fluxos de sugestão automática devem manter confirmação humana antes de impactar CPU/proposta.
- **Árvore N níveis:** composição hierárquica deve evitar flattening quando o usuário precisa de rastreabilidade visual e técnica.
- **Exportação formal:** Excel/PDF de proposta deve usar streaming, multi-aba e componentes reutilizáveis de frontend.
- **Versionamento de entidade:** padrão `root_id + numero_versao + is_versao_atual` aprovado para propostas e pode ser reutilizado em objetos versionáveis.
- **Parsing de Excel por estilo:** para TCPO/PINI, detecção robusta combina valor (`SER.*`) + `font.bold` + `alignment.indent`.
- **Histograma como snapshot operacional:** Compras deve operar sobre recursos consolidados por proposta, sem alterar a estrutura da CPU diretamente sem contrato explícito.

### Implicação para Milestone 7

Milestone 7 é desejável, mas deve iniciar por `M7-0` para sanear inbox/backlog, resolver colisão de IDs, congelar contrato de custo ajustado e definir permissão de Compras antes de implementar cotações.
