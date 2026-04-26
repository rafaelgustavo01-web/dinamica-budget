# Technical Review — Sprint F2-07

> **Data:** 2026-04-26
> **Sprint:** F2-07 — Tabelas Recursos + Motor 4 Camadas
> **Worker:** Gemini CLI
> **Status:** TESTED

---

## Resumo das Mudanças

### 1. Modelo de Agregação de Recursos
- **Tabela:** `operacional.proposta_resumo_recursos`.
- **Objetivo:** Fornecer uma visão consolidada dos custos totais da proposta por categoria (MO, Insumo, etc) sem a necessidade de varrer toda a árvore de composições em tempo de leitura.
- **Trigger:** Atualizado no `CpuGeracaoService` durante `gerar_cpu` e `recalcular_bdi`.

### 2. Motor de Busca 4 Camadas
- **Cascade:** 
    - Nível 1: Código Exato (Circuit Break).
    - Nível 2: Itens Próprios do Cliente (Fuzzy).
    - Nível 3: Associações Consolidadas (Inteligente).
    - Nível 4: Catálogo Global (Fuzzy/Semântico).
- **Performance:** A busca por código exato evita custos de processamento de string e IA quando o código é fornecido diretamente.

### 3. Integridade de Dados
- Adicionada constraint `uq_proposta_recurso` para evitar duplicidade de categorias por proposta.
- BDI é aplicado proporcionalmente a cada linha de resumo para garantir que a soma dos gerais no resumo bata com o total geral da proposta.

## Checklist de Validação
- [x] Migration 020 aplicada com sucesso.
- [x] PropostaResumoRecurso atualiza no recalcular BDI.
- [x] Busca por código exato prioriza item próprio.
- [x] 133 testes PASS (0 regressions).
- [x] Agregação de custos considera quantidade do PropostaItem.

## Riscos e Observações
- A heurística de BDI (fração vs porcentagem) foi mantida para compatibilidade, mas recomenda-se padronizar para porcentagem literal (ex: 25.0) em todas as futuras sprints de UI.
