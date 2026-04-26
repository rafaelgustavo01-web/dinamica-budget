# Technical Feedback — Sprint F2-04 — v1

> **Data:** 2026-04-25
> **Sprint:** F2-04 — CPU Detalhada + BDI Dinâmico
> **QA:** Gemini CLI
> **Status:** ACCEPTED

---

## Análise Técnica

A sprint foi entregue com alta qualidade, cumprindo todos os requisitos funcionais e técnicos estabelecidos.

### Pontos Positivos
1. **Breakdown Detalhado:** A implementação do accordion no frontend permite visualizar os insumos por item com clareza, incluindo chips para identificação do tipo de recurso (MAT/MO/EQUIP).
2. **BDI Dinâmico:** O endpoint de recálculo de BDI é eficiente, pois atualiza os totais da proposta e dos itens sem necessidade de re-explodir as composições, o que preserva a integridade dos dados e melhora a performance.
3. **UX/UI:** A `ProposalCpuPage` está bem estruturada, fornecendo feedback imediato ao usuário através de alertas e atualizações via TanStack Query. Os totais no cabeçalho facilitam a conferência dos valores.
4. **Qualidade de Código:** 
    - Schemas Pydantic bem definidos com validações adequadas.
    - Repositório seguindo o padrão do projeto com ordenação hierárquica.
    - Cobertura de testes unitários sólida (114+ testes passando).
    - TypeScript no frontend sem erros de tipagem.

### Observações
- A reutilização da coluna `percentual_indireto` para o BDI foi uma decisão inteligente que evitou migrations desnecessárias, mantendo a compatibilidade com a modelagem anterior.
- O carregamento lazy (on demand) das composições ao expandir o accordion otimiza o tráfego de dados.

---

## Veredito

**ACCEPTED → DONE.** Sprint aprovada para merge.

Próximos passos recomendados:
- Iniciar F2-05 (Exportação) aproveitando os novos schemas de detalhamento.
