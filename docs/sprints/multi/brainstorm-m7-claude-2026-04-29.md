# Decisão Arquitetural — Milestone 7: Compras e Negociação

**Data:** 2026-04-29  
**Autor:** Claude (arquiteto produto/técnico)  
**Inputs:** BACKLOG.md, config.md, SKILL.md, brainstorm-m7-codex-2026-04-29.md, brainstorm-m7-synthesis-2026-04-29.md

---

## 1. Recomendação

**GO condicional — abrir M7-0 imediatamente.**

Não abrir outro ciclo antes. Não há fundamento de produto ou técnico para desviar para um milestone diferente. M7 é a continuação natural e direta do que foi construído em Milestone 6. A condição é estritamente operacional: a sprint M7-0 de saneamento deve ser concluída antes de qualquer sprint de Compras ser despachada.

---

## 2. Justificativa produto

O produto chegou ao ponto exato onde M7 faz sentido comercial:

- **Proposta → PQ → Match → CPU** é o fluxo de estimativa. Está completo.
- **BCU + De/Para + Histograma** entregou o mapa de recursos editável por proposta. Esse é o ponto de partida natural para compras: o histograma *é* o mapa de compras antes de receber cotações.
- **RBAC por proposta + Versionamento** garante que múltiplos atores (orçamentista, comprador, aprovador) já têm um modelo de acesso auditável.
- O usuário comprador hoje não tem nenhuma tela operacional. A lacuna entre "histograma pronto" e "seleção de fornecedor" é o gap mais visível do produto neste momento.

Abrir um ciclo diferente (infra, UX complementar, observabilidade) seria desperdício de momentum: o stakeholder está esperando o fluxo de cotação, não mais fundação.

---

## 3. Justificativa técnica

**A favor de GO:**

- Baseline verde e estável: 223 pytest PASS, 13 vitest PASS, 0 tsc errors após F2-DT-A/B/C.
- Histograma (F2-11) já expõe `custo_base` por recurso — o modelo de dados para custo ajustado é uma extensão direta, não um novo schema.
- RBAC por proposta (F2-08) e enum `proposta_papel_enum` são a fundação correta para COMPRADOR, seja como papel novo ou como permissão derivada de EDITOR.
- Árvore de composições (F2-13) entregue e testada — M7 não precisa bloquear em nada da árvore.

**Contra GO imediato (razões para M7-0 primeiro):**

- **Colisão de IDs** — `F2-13` aparece simultaneamente como DONE (Tabela Hierárquica de Composições) e como ON-HOLD (Comparativo + Recálculo original de Compras) na mesma tabela do BACKLOG. Se o pipeline for religado sem correção, há risco real de redispatch de sprint já entregue.
- **Fronteira transacional inconsistente** — services com `commit()` direto coexistindo com endpoints que tratam rollback. Em Compras, a operação "selecionar cotação → atualizar custo ajustado → marcar cpu_desatualizada" envolve pelo menos 3 tabelas em sequência. Um commit/rollback ambíguo aqui corromperia o histograma silenciosamente.
- **Contrato de permissão indefinido** — `COMPRADOR` não está mapeado contra `OWNER/EDITOR/APROVADOR`. Sem decisão explícita antes da migration, M7-2 (cotações) não pode ser entregue com garantias de segurança.
- **7 findings HIGH** da revisão multi, incluindo N+1 em exportação, upsert em lote em BCU e null checks no histograma — risco baixo em uso atual, mas crítico com usuário comprador operando cotações em volume.

---

## 4. Pré-condições antes de iniciar

As pré-condições abaixo são obrigações de M7-0, não opcionais:

1. **Resolver colisão F2-13** — marcar as sprints antigas de Compras (F2-12, F2-13, F2-14, F2-15) como `SUPERSEDED` no BACKLOG, com nota explícita dos novos IDs (`M7-01..M7-04` ou `F3-01..F3-04`). Nunca reutilizar `F2-13` como ID de sprint nova.

2. **Normalizar inboxes** — fechar ou arquivar mensagens `[PENDING]` antigas em PO, QA e Research para sprints já DONE, impedindo redispatch indevido se o pipeline for religado.

3. **Corrigir caminhos em config.md** — `docs/pipeline/...` vs `docs/shared/pipeline/...` e `docs/superpowers/plans/...` vs `docs/shared/superpowers/plans/...`. Documenta explicitamente que pipeline permanece STOPPED até M7-0 concluída.

4. **Definir contrato transacional de Compras** — decisão explícita: "selecionar cotação faz commit atômico atualizando `custo_ajustado` no histograma + flag `cpu_desatualizada` na proposta; recálculo de totais é manual/disparado por PATCH explícito". Esse contrato deve ser documentado em M7-0 e é pré-requisito de M7-2.

5. **Definir modelo de permissão de Compras** — uma das duas opções:
   - **Opção A (nova role):** adicionar `COMPRADOR` ao enum `proposta_papel_enum`, com migration + ACL antes de M7-1. Permite controle fino.
   - **Opção B (role derivada):** EDITOR pode operar cotações; nenhuma migration de enum necessária. Mais simples, menor superfície.
   - Decisão é de PO, mas deve ser tomada antes de M7-1, não durante.

6. **Tratar ou aceitar formalmente os HIGH da revisão multi** — mínimo exigido antes de Compras: (a) allowlist de campos editáveis no PATCH do histograma; (b) rollback pós-commit no BcuService; (c) null check em insumos sem De/Para. Os demais podem ser aceitos como debt documentado.

---

## 5. Sequência sugerida de sprints

### M7-0 — Saneamento e contratos (bloqueante, solo)

**Escopo mínimo:**
- Corrigir colisão de IDs e marcar sprints antigas como SUPERSEDED
- Normalizar inboxes e config.md
- Documentar contrato transacional de cotação → custo ajustado → cpu_desatualizada
- Decisão PO sobre modelo de permissão (Opção A ou B)
- Aplicar fixes HIGH mínimos (allowlist histograma, rollback BCU, null check insumo)

**Saída:** BACKLOG coerente, suite verde, contrato de Compras congelado por escrito.  
**Worker sugerido:** Claude Code (surface documental + backend cirúrgico, sem migrations complexas).  
**Duração esperada:** 1 sprint curta.

---

### M7-1 — Mapa de Compras e permissão operacional

**Escopo:**
- Derivar lista de recursos compráveis a partir do histograma (não criar novo modelo — extender `proposta_pc_recurso`)
- Aplicar decisão de permissão (migration se Opção A; ACL se Opção B)
- Endpoint `GET /propostas/{id}/compras/recursos` retornando custo_base + custo_ajustado + status_cotacao

**Saída:** API de recursos compráveis funcional; frontend ainda não necessário.  
**Worker sugerido:** Kimi (backend heavy, sem UI).

---

### M7-2 — Cotações backend

**Escopo:**
- CRUD de cotações por recurso (fornecedor, valor, prazo, validade)
- Seleção única por recurso: PATCH atualiza `custo_ajustado` no histograma + marca `cpu_desatualizada`
- Auditoria básica (quem selecionou, quando)

**Saída:** contratos transacionais do M7-0 exercitados e testados.  
**Worker sugerido:** Kimi.  
**Dependência:** M7-1 DONE.

---

### M7-3 — Tela de Compras

**Escopo:**
- `ProposalPurchasingPage` com tabela de recursos, status de cotação por recurso
- Drawer de cotações por recurso + formulário de cadastro + botão selecionar
- Edição inline de `custo_ajustado` quando sem cotação formal

**Saída:** fluxo operacional usável pelo comprador.  
**Worker sugerido:** Claude Code (UI/UX complexo, debounce, drawer, feedback visual).  
**Dependência:** M7-2 DONE.

---

### M7-4 — Comparativo e impacto na proposta

**Escopo:**
- `GET /propostas/{id}/comparativo-base-vs-ajustado` — delta por recurso, por tipo (MO/Material/Equipamento), total
- Card de comparativo no `ProposalDetailPage`
- Exportação ou integração com ExportMenu (Excel ou PDF, mesma interface de F2-05)

**Saída:** decisão comercial visível e rastreável antes da aprovação.  
**Worker sugerido:** Claude Code ou Gemini (análise + frontend).  
**Dependência:** M7-3 DONE.

---

## 6. Riscos e mitigação

| Risco | Impacto | Probabilidade | Mitigação |
|---|:---:|:---:|---|
| Reutilização de F2-13 como ID de sprint nova | Alto | Alta sem M7-0 | BACKLOG corrigido em M7-0; IDs novos com prefixo M7 |
| Cotação gravar custo ajustado sem transação atômica | Alto | Média | Contrato documentado em M7-0; teste obrigatório de rollback em M7-2 |
| COMPRADOR conflitar com EDITOR em endpoints compartilhados | Alto | Média | Decisão de Opção A ou B fechada antes de M7-1 |
| Histograma aceitar PATCH de campo indevido via Compras | Médio/Alto | Baixa pós-M7-0 | Allowlist implementada em M7-0 |
| Pipeline automatizado redispachar sprints antigas | Médio | Alta se pipeline for religado sem M7-0 | Pipeline permanece STOPPED; inboxes normalizados em M7-0 |
| Escopo de M7 crescer para cadastro sofisticado de fornecedores | Médio | Baixa | M7 mantém fornecedor como campo texto na cotação; módulo de fornecedores fica fora |
| BCU com insumos sem De/Para corrompendo custo_base no comparativo | Médio | Baixa pós-fix | Null check + fallback `INSUMO` aplicado em M7-0 |
| Histograma e custo ajustado ficarem dessincronizados após nova_versao | Médio | Baixa | nova_versao já clona histograma (F2-11); M7-1 deve garantir que cota não segue para versão clonada sem revisão |

---

## 7. Concordância e crítica em relação ao Codex

### Concordância

A recomendação do Codex é **correta no diagnóstico e na sequência**. Os cinco pontos de saneamento identificados (IDs, inboxes, RBAC, contrato transacional, findings HIGH) são todos reais e bloqueantes. A sequência M7-0 → M7-1 → M7-2 → M7-3 → M7-4 é a ordem natural de dependência e não tem atalho seguro.

O Codex acertou também em não recomendar um milestone alternativo — M7 é o próximo valor de produto e não há justificativa para desvio.

### Críticas e adições

**1. M7-0 precisa de escopo mínimo explícito, não apenas lista de pré-condições.**  
O Codex lista pré-condições mas não define o que é M7-0 como sprint despachável. Sem escopo mínimo, M7-0 pode crescer indefinidamente. A sprint deve ter critério de aceite objetivo: BACKLOG coerente sem colisão, suite verde, contrato de Compras documentado, decisão de permissão registrada.

**2. O histograma é o modelo de dados de Compras — isso não está explícito no Codex.**  
`custo_ajustado` em Compras não deve criar um novo schema paralelo. Deve ser uma coluna adicional em `proposta_pc_recurso` (ou tabela satélite direta). Qualquer divergência de modelo aqui cria duplicação estrutural equivalente ao problema `pc_tabelas` vs `bcu.*` que foi resolvido em F2-10. Esse contrato de dados precisa estar em M7-0.

**3. A Opção B de permissão (EDITOR como comprador) é subavaliada.**  
O Codex assume implicitamente que `COMPRADOR` será um papel novo (Opção A), mas a Opção B (EDITOR com permissão de cotação por contexto) evita migration de enum, é compatível com o modelo ACL atual e mantém a superfície de segurança menor. PO deve considerar explicitamente as duas antes de decidir.

**4. M7-4 (comparativo) pode ser antecipado parcialmente.**  
O endpoint `GET /comparativo-base-vs-ajustado` pode ser entregue junto com M7-2 (backend), mesmo que a UI fique para M7-4. Isso permite QA validar os cálculos antes da UI, reduzindo rework de frontend.

**5. Ausência de critério de cancelamento de M7.**  
O Codex não define quando M7 deve ser cancelada ou reduzida. Sugestão: se M7-0 revelar que o modelo de histograma precisa de refatoração substancial (não apenas fix cirúrgico), M7 deve ser pausada para uma sprint de refatoração antes de M7-1 — não ignorada.

---

## Decisão recomendada

**Abrir M7-0 agora.**  
PO aprova escopo mínimo de M7-0 conforme definido acima.  
Pipeline permanece STOPPED durante M7-0.  
Após M7-0 DONE com suite verde e contratos documentados, despachar M7-1.
