# JOB DESCRIPTION - Dinamica Budget

Data: 2026-04-22
Escopo: operacao do pipeline multiagente para evolucao do sistema de orcamentos de obras.

## Objetivo Geral
Organizar o fluxo de entrega com papeis claros para garantir qualidade tecnica, seguranca de acesso on-premise, previsibilidade de sprint e governanca de artefatos.

## Papeis e Responsabilidades

### 1) Product Owner
- Prioriza backlog e define valor de negocio.
- Autoriza inicio de sprint (status `INICIADA`).
- Aprova planos do Supervisor antes de execucao.

### 2) Supervisor
- Converte sprint `INICIADA` em plano executavel.
- Define escopo tecnico, riscos e dependencias.
- Publica briefing da sprint e move para `PLAN`.

### 3) Scrum Master
- Verifica gate de artefatos (plano + briefing).
- Atribui agente executor e organiza fila de despacho.
- Move sprint para `TODO` quando pronta para execucao.

### 4) Worker
- Implementa mudancas aprovadas.
- Atualiza walkthrough tecnico e evidencia de implementacao.
- Move sprint para `TESTED`.

### 5) Tester
- Executa testes automatizados e lint.
- Compara baseline de qualidade e regressao.
- Emite relatorio tecnico para QA (aprovado/reprovado).

### 6) QA
- Faz verificacao final baseada em evidencias.
- Aceita sprint para `DONE` ou retorna para `TODO` com feedback.

### 7) Research AI
- Analisa sprints `DONE` e gera melhorias de produto/processo.
- Atualiza roadmap com novas fases, lacunas e dependencias.
- Mantem historico de atualizacao e recomendacoes futuras.

### 8) Git Controller
- Resolve incidentes de git sob demanda.
- Preserva trabalho em andamento e evita operacoes destrutivas.
- Registra incidente e orienta proximo passo.

### 9) Assistant
- Consolida status do backlog e riscos de bloqueio.
- Responde perguntas de acompanhamento do projeto.
- Nao altera status de sprint.

### 10) Log Creator (opcional)
- Registra anomalias operacionais e tecnicas.
- Mantem trilha de auditoria de eventos de processo.

## Regras Operacionais
- Fluxo canonico: `BACKLOG -> INICIADA -> PLAN -> TODO -> TESTED -> DONE`.
- Limite WIP: no maximo 4 sprints ativas (`INICIADA`, `PLAN`, `TODO`, `TESTED`).
- Uma sprint por agente ativo por vez.
- Mudanca de status somente pelo papel dono da etapa.

## Indicadores Minimos
- Lead time por sprint.
- Taxa de retrabalho (`TESTED -> TODO`).
- Cobertura de testes dos modulos alterados.
- Incidentes de seguranca/autorizacao por release.
