# QA técnico — últimas 10 sprints

Data: 2026-05-15  
Escopo auditado: F3-01, F3-02, F3-04, F3-05, F4-01, F4-02, F4-03, F4-04, F4-05 e F4-DT-01.  
F3-03 foi excluída do recorte porque está ON-HOLD.

## Resumo executivo

O estado geral está estável para frontend e para os fluxos backend focados de Smart Import/PQ/CPU: lint, testes frontend, build, audit frontend e testes backend focados passaram. Ainda existem débitos técnicos relevantes antes de promover a Fase 4 para DONE ou retomar M7/Compras.

## Gates executados nesta rodada

| Gate | Resultado |
|---|---|
| git diff --check | PASS |
| app/frontend npm audit --audit-level=high | PASS — 0 vulnerabilities |
| app/frontend npm run lint | PASS |
| app/frontend npm test -- --run | PASS — 13 tests |
| app/frontend npm run build | PASS, com warning de chunk > 500 kB |
| app/backend compileall focado | PASS |
| app/backend pytest smart_import + pq_match_review + cpu_geracao + proposta_service | PASS — 90 passed, 8 warnings |

## Achados

### P1 — Fase 4 continua sem validação DB/Alembic para DONE

Evidência: docs/shared/governance/BACKLOG.md declara F4-01 a F4-05 em TESTED aguardando validação final de banco/Alembic em ambiente seguro. A checagem de migrations não encontrou revisões duplicadas nem branching direto, mas isso não substitui alembic upgrade/downgrade real com banco configurado.

Impacto: promover F4 para DONE sem validar migrations pode mascarar erro de schema ou rollback, especialmente porque F4 adicionou Smart Import, perfis, config/admin e campos de cliente.

Recomendação: criar gate técnico curto para rodar alembic upgrade head, smoke de modelos e downgrade/rollback controlado em banco seguro antes de DONE.

### P1 — Estado do match PQ ainda usa registry em memória

Evidência: app/backend/api/v1/endpoints/pq_importacao.py mantém _match_tasks em memória e status em GET /match/status depende desse dicionário local.

Impacto: em múltiplos workers, restart ou troca de processo, o frontend pode voltar a mostrar que o match não foi executado, mesmo com itens já sugeridos/confirmados no banco. Esse comportamento conversa diretamente com o erro reportado anteriormente pelo Rafael.

Recomendação: persistir o estado do match por proposta/importação no banco ou derivar o status real de pq_itens; manter _match_tasks apenas como cache opcional.

### P1 — Mojibake/encoding ainda visível em tela de itens expandidos

Evidência: app/frontend/src/features/proposals/pages/ProposalItemsExpandedPage.tsx ainda contém textos como CAT�LOGO, Cabe�alho, descri��o, Valor Unit�rio, C�digo, Bot�o e fallback "�".

Impacto: o problema de encoding não ficou restrito a Gerenciar Itens; ainda existe em uma tela de proposta/itens e causa percepção de baixa qualidade visual.

Recomendação: corrigir o arquivo inteiro para UTF-8 válido e adicionar um grep de CI simples para bloquear o caractere U+FFFD em app/frontend/src.

### P2 — F4-DT-01 ficou com documentação interna inconsistente

Evidência: BACKLOG.md mostra F4-DT-01 como TESTED, mas docs/sprints/F4-DT-01/briefing/sprint-F4-DT-01-briefing.md e docs/sprints/F4-DT-01/plans/2026-05-15-f4-dt-01-plan.md ainda indicam TODO.

Impacto: confunde Scrum Master/QA e futuras automações de pipeline. É dívida documental pequena, mas recorrente no processo.

Recomendação: padronizar briefing/plan para registrar status final ou mover status mutável para technical-review/walkthrough, deixando briefing como estado inicial apenas quando explicitamente rotulado.

### P2 — Technical feedback ausente nas sprints F4

Evidência: F4-01, F4-02, F4-03, F4-04, F4-05 e F4-DT-01 têm briefing, plano, review e walkthrough, mas não têm technical-feedback.

Impacto: o fluxo documental prometido no pipeline exige technical feedback; sem esse artefato, a rastreabilidade de aprovação/rejeição fica assimétrica em relação às sprints anteriores.

Recomendação: gerar technical-feedback sintético para F4 com status, gates e pendências residuais, ou ajustar formalmente a política documental para aceitar technical-review + walkthrough como suficiente.

### P2 — Endpoints de Proposta ainda usam body: dict em pontos críticos

Evidência: app/backend/api/v1/endpoints/propostas.py mantém body: dict em endpoints de itens/recursos expandidos e operações relacionadas.

Impacto: validação fica manual, OpenAPI perde contrato, payload inválido pode virar erro 500/KeyError em vez de 422 consistente. Esse débito já tinha sido apontado pelo agente de revisão.

Recomendação: criar schemas Pydantic pequenos para cada payload e reaproveitar validações de Decimal/UUID; cobrir 422 em testes unitários.

### P2 — Bundle frontend ainda está pesado

Evidência: npm run build passou, mas Vite alertou chunks > 500 kB: index ~684 kB e BcuUploadPage ~372 kB.

Impacto: não quebra, mas degrada carregamento inicial e confirma que o plano de refatoração/code-splitting ainda não foi totalmente executado.

Recomendação: separar chunks por domínio pesado: MUI, schemas/zod, upload XLSX/BCU e páginas administrativas.

### P3 — Warnings de pytest precisam saneamento preventivo

Evidência: pytest focado passou com 8 warnings: pytest-asyncio loop scope não definido, passlib usando crypt deprecado para Python 3.13 e jose usando datetime.utcnow.

Impacto: hoje não quebra, mas vira risco em upgrade de Python/dependências.

Recomendação: definir asyncio_default_fixture_loop_scope no pytest.ini e planejar troca/upgrade de libs quando o projeto mirar Python 3.13.

### P3 — UUID técnico ainda existe em código frontend

Evidência: app/frontend/src/features/auth/AuthProvider.tsx mantém PLACEHOLDER_CLIENT_IDS com 53ec2a1d-a949-4b2c-8caa-6ded536f0b33.

Impacto: não encontrei evidência de renderização direta após as correções, mas o ID técnico segue hardcoded no bundle do frontend.

Recomendação: mover para uma constante de configuração técnica ou, melhor, tratar cliente placeholder no backend/claim de auth para o frontend nunca precisar conhecer esse UUID.

## Recomendação de saneamento

Criar uma sprint curta F4-DT-02 com quatro entregas objetivas:

1. Persistir/derivar status do match PQ no banco.
2. Corrigir mojibake em ProposalItemsExpandedPage e adicionar bloqueio por grep de U+FFFD.
3. Trocar body: dict por schemas Pydantic nos endpoints de proposta mais usados.
4. Normalizar artefatos F4 e registrar technical-feedback sintético.

Depois disso, rodar uma sprint-gate F4-DB-01 apenas para Alembic/DB seguro antes de promover F4 para DONE.
