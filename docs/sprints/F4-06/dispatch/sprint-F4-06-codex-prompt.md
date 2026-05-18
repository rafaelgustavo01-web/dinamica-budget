# Dispatch — F4-06 Pós-deploy Import/Match Stabilization para Codex

## Contexto
Trabalhe no repositório /root/workspace/dinamica_budget na KVM2 (31.97.255.93).
Branch: main (verifique git status e HEAD antes de começar).

## Leitura obrigatória
- docs/sprints/F4-06/briefing/sprint-F4-06-briefing.md
- docs/sprints/F4-06/plans/2026-05-15-f4-06-plan.md

## Escopo
Reproduzir e corrigir bugs reais remanescentes dos fluxos:
1. Smart Import (upload, staging, commit)
2. PQ Match (executar_match_para_proposta)
3. Criação de Proposta (cliente obrigatório, numeração automática)
4. Upload individual de bases (BCU/TCPO)

## Método
1. Verifique logs/request_id recentes em /var/log/dinamica_budget/ ou stdout do app.
2. Reproduza sintomas localmente (pytest, curl, ou execução direta).
3. Corrija apenas causas confirmadas — nenhuma refatoração ampla.
4. Mantenha compatibilidade com fluxos que já funcionam.
5. Rode gates mínimos: pytest nos módulos afetados, npm run build no frontend se alterar.

## Guardrails
- Sem deploy/restart de produção sem OK explícito.
- Sem force-push/reset destrutivo.
- Sem segredos em logs/memória.
- git diff --check antes de commit.
- Commit atômico com mensagem tipo fix(f4-06): descrição.

## Entrega
- Arquivo de relatório em docs/sprints/F4-06/technical-review/technical-review-YYYY-MM-DD-f4-06.md
- git push origin main quando gates verdes (sem deploy).
