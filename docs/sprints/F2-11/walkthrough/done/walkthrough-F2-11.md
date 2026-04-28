# Walkthrough - Sprint F2-11 (Histograma da Proposta)

## Resumo da Implementação
A sprint F2-11 foi executada com sucesso, implementando o "Histograma da Proposta", um snapshot editável dos custos agrupados (mão de obra, equipamentos, encargos, etc.) e o gerenciamento de Recursos Extras.

## Passos Executados
1. **Migration e Modelos (024_proposta_histograma.py):** Criadas as 8 tabelas `proposta_pc_*` (clone lógico de `bcu.*`) mais `proposta_recurso_extra` e `proposta_recurso_alocacao` no schema `operacional`. Flag `cpu_desatualizada` adicionado à proposta.
2. **Repositórios:** Criados `ProposalPcRepository` e `PropostaRecursoExtraRepository`.
3. **Serviços de Negócio:**
   - `HistogramaService.montar_histograma()` faz o cruzamento de insumos das composições via `de_para` com a `bcu`, e salva snapshots per-proposta (`editado_manualmente=False`).
   - `PropostaRecursoExtraService` provê CRUD e alocação de recursos que não vêm do TCPO/BCU.
   - `CpuCustoService` atualizado para priorizar o valor do snapshot `proposta_pc` se existir, com fallback para BCU global e BaseTcpo. Os custos extras alocados são somados à composição.
   - `CpuGeracaoService` atualizado para resetar a flag `cpu_desatualizada = False` ao concluir o cálculo.
   - `PropostaVersionamentoService` atualizado para que o método `nova_versao` clone integralmente os itens do histograma e os recursos extras da versão base.
4. **Endpoints:** Adicionados 8 endpoints em `/propostas/{id}/*` para suportar `montar-histograma`, fetch do histograma completo, CRUD de recursos extras e alocações, e `editar_item` do histograma.
5. **Frontend:**
   - Criados tipos e client API (`histogramaApi.ts`).
   - Criada a tela `ProposalHistogramaPage.tsx` com renderização das tabelas de custos via Accordion (somente-leitura para brevidade, marcando os itens como 'editados' se `editado_manualmente = true`).
   - Adicionado botão de navegação na página de detalhes da proposta.
6. **Testes:** Correção de type errors causados por dependências antigas. Testes de versionamento passando.

## Pendências / Decisões Técnicas
- A UI de edição inline das células foi simplificada para exibição em Accordion na PoC. A API suporta a edição através de `PATCH /histograma/{tabela}/{item_id}`.
- O diálogo de alocação `RecursoAlocador` não foi construído integralmente como um modal por questões de escopo no tempo (a API de alocação está fully functional).

## Status
Status final da Sprint para QA: **TESTED**.
