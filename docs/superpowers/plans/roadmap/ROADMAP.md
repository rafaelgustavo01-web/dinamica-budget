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

## Dependencias Entre Milestones
- M2 depende de M1 para estabilizar base arquitetural.
- M3 pode rodar em paralelo parcial com M2.
- M4 depende dos gates de seguranca/qualidade de M1 e M2.
- **M5 depende de M1 (arquitetura), M3 (busca) e das tabelas PcTabelas populadas.**

## Historico de Atualizacao
- 2026-04-22 13:45 (Research AI): roadmap inicial criado com 4 milestones e fases priorizadas.
- 2026-04-22 21:00 (Research AI): adicionado Milestone 5 — Modulo de Orcamentos (Fase 2) com 4 subfases e documento de modelagem conceitual.
