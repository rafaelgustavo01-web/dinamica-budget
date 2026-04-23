# Sprint S-10 Briefing

> **Role:** Supervisor  
> **Date:** 2026-04-23  
> **Sprint:** S-10 — Importação PQ e Match Inteligente

## Objetivo

Permitir que um orçamentista faça upload de uma planilha quantitativa (Excel/CSV) para uma proposta existente, extraia os itens brutos (PqItem), e execute match fuzzy/semântico contra o catálogo de serviços (Base TCPO + Itens Próprios).

## Escopo

1. **Upload de planilha** — endpoint multipart que recebe `.xlsx` ou `.csv`
2. **Parser de PQ** — extrai colunas: código, descrição, unidade, quantidade
3. **Persistência** — cria `PqImportacao` + `PqItem` em batch
4. **Match inteligente** — reusa `busca_service` (fase 1 e 3) para sugerir serviços
5. **Status tracking** — itens passam por PENDENTE → SUGERIDO/SEM_MATCH
6. **Testes unitários** — cobertura de importação e match

## Critérios de Aceite

- Upload aceita `.xlsx` e `.csv` com pelo menos 1000 linhas sem timeout
- Cada linha vira um `PqItem` com descrição_original e descricao_tokens normalizados
- Match executa para todos os itens PENDENTES de uma proposta
- Sugestão inclui `servico_match_id`, `servico_match_tipo`, `match_confidence`
- Sem match atualiza status para SEM_MATCH
- Testes unitários cobrem parser e matcher
- Migração Alembic inclui `pq_importacoes` e `pq_itens`

## Dependências

- S-09 concluída (OK) — entidades Proposta, PqItem, PqImportacao já modeladas
- S-05 concluída (OK) — busca_service com fase1+fase3 disponível

## Riscos

- Planilhas com encoding estranho ou colunas fora do padrão
- Match batch pode ser lento para >500 itens (sem paginação de match)
- Dependência circular se busca_service precisar de alterações

## Worker Assignment

- Assigned worker: codex-5.3
- Provider: OpenAI
- Mode: BUILD

## Plano

Ver: `docs/superpowers/plans/2026-04-23-importacao-pq-match-inteligente.md`
