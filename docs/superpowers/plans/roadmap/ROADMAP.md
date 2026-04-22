# ROADMAP - Dinamica Budget

Data base: 2026-04-22
Fonte: backlog tecnico atual + analise de arquitetura do repositorio.

## Visao de Entrega
Objetivo: levar o projeto para um estado de pre-producao robusto em arquitetura, seguranca, testes e operacao on-premise.

## Milestone 1 - Seguranca e Arquitetura Base (P0)

### Fase 1.1 - Isolamento Multi-tenant em Composicoes e Versoes
- Corrigir autorizacao em endpoints de composicao e versoes.
- Garantir retorno 404/403 para acesso cross-tenant.
- Entregavel: testes de integracao cobrindo permissoes por perfil.

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

### Fase 3.1 - Benchmark de Busca (Fuzzy vs Semantica)
- Medir latencia/precisao com carga realista.
- Reavaliar thresholds e ranking hibrido.
- Entregavel: relatorio de benchmark com recomendacoes.

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

## Dependencias Entre Milestones
- M2 depende de M1 para estabilizar base arquitetural.
- M3 pode rodar em paralelo parcial com M2.
- M4 depende dos gates de seguranca/qualidade de M1 e M2.

## Historico de Atualizacao
- 2026-04-22 13:45 (Research AI): roadmap inicial criado com 4 milestones e fases priorizadas.
