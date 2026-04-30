# Brainstorm M7 — Compras e Negociacao

**Data:** 2026-04-29  
**Autor:** Codex  
**Recomendacao:** **GO condicional**

## 1. Recomendacao clara

**GO condicional:** seguir com Milestone 7, mas **nao reativar imediatamente as sprints originais de Compras** no estado atual.

Abrir antes um ciclo curto de saneamento (`M7-0`) para fechar desalinhamentos de backlog/inboxes, resolver ou formalmente aceitar os findings HIGH da revisao multi e recriar M7 com IDs novos. Depois disso, M7 deve seguir.

## 2. Justificativa produto

- O produto ja tem a base necessaria para Compras: Proposta, PQ, Match, CPU, RBAC por proposta, versionamento/aprovacao, BCU, De/Para, histograma editavel e arvore de composicoes.
- Compras agora tem valor claro: transformar o histograma em fluxo operacional de cotacao, negociacao e custo ajustado por proposta.
- Reativar M7 sem saneamento cria risco de confundir o escopo: `F2-13` aparece como M7.2/Cotacoes `ON-HOLD` na tabela principal, mas tambem consta como DONE para Tabela Hierarquica de Composicoes.
- O melhor produto a entregar em seguida nao e uma feature isolada de cotacao; e um fluxo coerente: histograma -> mapa de compras -> cotacoes -> selecao -> comparativo -> recalc da proposta.

## 3. Justificativa tecnica

- F2-10, F2-11, F2-12, F2-13 e F2-DT-A/B/C estao aprovadas, com baseline verde: 223 pytest PASS, 13 vitest PASS, 0 tsc errors.
- A revisao multi nao encontrou CRITICAL, mas levantou 7 HIGH e 11 MEDIUM. Alguns itens afetam exatamente as fundacoes de M7: BCU, histograma, exportacao, transacoes e arvore de composicoes.
- A fronteira transacional ainda esta inconsistente em services que fazem `commit()` diretamente e endpoints que tambem tratam rollback. Isso fica mais arriscado em Compras, onde selecao de cotacao deve atualizar custo ajustado e disparar recalculo de totais.
- A autorizacao para M7 ainda precisa ser redecidida: o papel `COMPRADOR` foi citado no plano original, mas as regras atuais de histograma usam OWNER/EDITOR para edicao e VIEWER/APROVADOR para leitura.
- Inboxes e backlog estao desalinhados: ha mensagens `PENDING` antigas em PO/QA/Research mesmo para sprints ja DONE, e o config ainda referencia caminhos legados em `docs/...` enquanto o fluxo canonico atual usa `docs/shared/...` e `docs/sprints/...`.

## 4. Pre-condicoes antes de iniciar

1. Atualizar `docs/shared/governance/BACKLOG.md` para remover a colisao de `F2-13` e marcar claramente as antigas sprints de Compras como superseded/on-hold, nao como IDs reutilizaveis.
2. Criar IDs novos para M7, por exemplo `M7-01..M7-04` ou `F2-14..F2-17`, sem reaproveitar `F2-13`.
3. Fechar ou registrar como accepted debt os findings HIGH da revisao multi, com foco minimo em:
   - exportacao: N+1 e BytesIO;
   - BCU: upsert em lote e rollback pos-commit;
   - histograma: null checks e allowlist de campos editaveis;
   - composicoes: N+1 em filhos PROPRIA e limite de profundidade/ciclo.
4. Normalizar inboxes `PENDING` antigos para nao disparar fluxo automatico incorreto se o pipeline for religado.
5. Atualizar `docs/shared/pipeline/config.md` para caminhos canonicos ou documentar explicitamente que o pipeline automatico permanece STOPPED.
6. Definir contrato de permissao de Compras: se `COMPRADOR` volta, mapear acesso contra OWNER/EDITOR/APROVADOR e ajustar enum/ACL antes dos endpoints.
7. Especificar a regra de custo ajustado: onde vive, quando recalcula, se altera CPU imediatamente ou apenas marca `cpu_desatualizada`.

## 5. Sequencia sugerida de sprints se GO

### M7-0 — Saneamento e alinhamento operacional

Escopo: corrigir backlog/inboxes/config, resolver findings HIGH bloqueantes e congelar contratos de permissao/custo ajustado.  
Saida esperada: pipeline documental coerente, suite verde, M7 replanejada com IDs novos.

### M7-1 — Mapa de Compras e papel operacional

Escopo: derivar lista de recursos compraveis a partir do histograma, definir papel `COMPRADOR` ou regra equivalente, adicionar custo base/custo ajustado por recurso da proposta.  
Saida esperada: backend e API de recursos compraveis, sem cotacao ainda.

### M7-2 — Cotacoes backend

Escopo: CRUD de cotacoes por recurso, fornecedor, prazo, validade, anexos/metadados se necessario; selecao unica por recurso; auditoria basica.  
Saida esperada: selecao de cotacao atualiza custo ajustado e marca/recalcula conforme contrato definido em M7-0.

### M7-3 — Tela de Compras

Escopo: tela por proposta com recursos, status de cotacao, edicao de ajustado, drawer/form de cotacoes e selecao.  
Saida esperada: fluxo usavel pelo comprador sem depender de admin/BCU.

### M7-4 — Comparativo e impacto na proposta

Escopo: base vs ajustado, delta por recurso/tipo/total, integracao com detalhe da proposta, exportacao ou card executivo.  
Saida esperada: decisao comercial visivel e rastreavel antes da aprovacao.

## 6. Riscos e mitigacao

| Risco | Impacto | Mitigacao |
|---|---:|---|
| Reusar IDs antigos (`F2-13`) | Alto | Criar IDs novos e marcar sprints antigas como superseded |
| Cotacao escrever custo ajustado sem contrato transacional claro | Alto | M7-0 define ownership de commit/rollback e teste de selecao + recalc |
| Permissao `COMPRADOR` conflitar com OWNER/EDITOR/APROVADOR | Alto | Decisao explicita de RBAC antes de migration/endpoints |
| Histograma aceitar campos indevidos no PATCH | Medio/Alto | Allowlist por tabela antes de abrir Compras para usuarios operacionais |
| BCU/histograma com classificacao incorreta de insumos | Medio | Tratar fallback de `INSUMO` sem De/Para antes de comparativos |
| Inboxes antigas reativarem trabalho obsoleto | Medio | Normalizar estados antes de religar pipeline |
| Escopo de M7 crescer para fornecedores/contratos completos | Medio | Manter M7 em cotacao por recurso da proposta; cadastro sofisticado de fornecedores fica fora |

## Decisao pratica

Abrir **M7-0 agora**.  
Reativar Compras apenas depois de M7-0 concluida e backlog reemitido com IDs novos.
