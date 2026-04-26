# Walkthrough — Sprint F2-07

> **Data:** 2026-04-26
> **Sprint:** F2-07 — Tabelas Recursos + Motor 4 Camadas
> **Worker:** Gemini CLI

---

## O que foi entregue

Nesta sprint, implementamos a infraestrutura de agregação de custos por tipo de recurso e formalizamos o motor de busca em cascata de 4 camadas para garantir precisão e performance no match de itens.

### 1. Tabelas de Recursos (Agregação CPU)
- **Novo Modelo:** `PropostaResumoRecurso` para armazenar totais agregados por `TipoRecurso` (MO, Material, Equipamento, etc) por proposta.
- **Migration 020:** Criação da tabela `operacional.proposta_resumo_recursos` com índices e constraints de integridade.
- **CPU Service:** O `CpuGeracaoService` agora atualiza automaticamente o resumo de recursos sempre que uma CPU é gerada ou o BDI é recalculado.
- **Granularidade:** A agregação considera as quantidades dos itens da proposta (`PropostaItem`), fornecendo o custo total real do projeto por categoria.

### 2. Motor de Busca 4 Camadas
Formalizamos a busca em cascata no `BuscaService` para seguir a ordem de prioridade definida na modelagem:
1.  **Fase 0.1: Código Exato:** Circuit-break imediato se o texto de busca for um código de origem idêntico.
2.  **Fase 0.2: Itens Próprios:** Busca fuzzy restrita ao catálogo aprovado do cliente.
3.  **Fase 1: Associação Direta:** Lookup na tabela de associações inteligentes.
4.  **Fase 2/3: Global (Fuzzy + IA):** Fallback para o catálogo global TCPO usando similaridade de texto e vetores.

### 3. Melhorias de Repositório
- **BaseTcpoRepository:** Adicionado método `get_by_codigo`.
- **ItensPropiosRepository:** Adicionado método `get_by_codigo_scoped`.
- **PropostaItemComposicaoRepository:** Adicionado método `list_by_proposta`.

---

## Evidências de Teste

- **Total:** 133 testes PASS.
- **Novos Testes:** `app/backend/tests/unit/test_f2_07_features.py`

### Comandos de Validação
```powershell
pytest app/backend/tests/unit/test_f2_07_features.py -v
pytest app/backend/tests/unit/ -q
```

---

## Artefatos Gerados/Modificados
- `app/alembic/versions/020_add_proposta_resumo_recursos_table.py`
- `app/backend/models/proposta.py`
- `app/backend/models/enums.py`
- `app/backend/schemas/busca.py`
- `app/backend/services/busca_service.py`
- `app/backend/services/cpu_geracao_service.py`
- `app/backend/repositories/proposta_resumo_recurso_repository.py`
- `app/backend/repositories/base_tcpo_repository.py`
- `app/backend/repositories/itens_proprios_repository.py`
- `app/backend/repositories/proposta_item_composicao_repository.py`
- `app/backend/tests/unit/test_f2_07_features.py`
