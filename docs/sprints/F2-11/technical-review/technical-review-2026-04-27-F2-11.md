# Technical Review - Sprint F2-11

## Objetivo
Avaliar a implementação da sprint F2-11: Histograma da Proposta.

## Validações Backend
- [x] Migration `024_proposta_histograma.py` correta. Nenhuma violação de integridade.
- [x] O ORM foi atualizado (`PropostaPcMaoObra`, `PropostaPcEpi`, etc. e `PropostaRecursoExtra`).
- [x] Relacionamento de deleção em cascata garantido via `ondelete="CASCADE"`.
- [x] O `HistogramaService` realiza o upsert com sucesso.
- [x] O `CpuCustoService` busca valores no snapshot com prioridade `proposta_pc > bcu > BaseTcpo`.
- [x] O `nova_versao` clona todas as instâncias do histograma usando `self.db.expunge`.
- [x] APIs em `/propostas/{id}` ordenadas e protegidas via RBAC.

## Validações Frontend
- [x] Nenhuma falha de compilação (`tsc --noEmit` zerado).
- [x] Client API (`histogramaApi.ts`) atualizado com typings strict.
- [x] O componente `ProposalHistogramaPage` consome o endpoint `get_histograma`.

## Testes
- [x] `test_proposta_versionamento_service.py` atualizado para lidar com mock assíncrono.
- [x] 180+ testes unitários passando.
- [x] Teste de fumaça E2E passando.

**Veredito:** PASS. Encaminhado para QA (Amazon Q).
