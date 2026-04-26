# Technical Feedback — Sprint F2-01: PQ Layout Cliente

**Data:** 2026-04-25
**QA:** claude-sonnet-4-6 (auto-review)
**Veredicto:** APROVADO — Sprint pode avançar para DONE

---

## Checklist de Revisao

### Modelos e Migracao

- [x] `PqLayoutCliente` usa `Mapped`/`mapped_column` (SQLAlchemy 2.0)
- [x] `UniqueConstraint` em `cliente_id` — relacao 1:1 com cliente garantida
- [x] `PqImportacaoMapeamento` com `UniqueConstraint(layout_id, campo_sistema)` — sem duplicatas por campo
- [x] FK com `ondelete="CASCADE"` em ambas as tabelas
- [x] `lazy="noload"` nas relationships — sem N+1 silencioso
- [x] Migration 018 com `down_revision = "017"` — chain correto
- [x] Enum PostgreSQL criado com padrao idempotente `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN NULL; END $$`
- [x] `downgrade()` limpo: drop indexes -> drop tables -> drop type

### Schemas e Validacao

- [x] `PqLayoutCriarRequest.campos_obrigatorios` valida presenca de DESCRICAO, QUANTIDADE, UNIDADE
- [x] `@field_validator` com `@classmethod` — Pydantic v2 correto
- [x] `PqLayoutResponse` com `from_attributes = True`
- [x] `MapeamentoItemResponse` expoe `id` para rastreabilidade

### Service e Repositorio

- [x] `criar_ou_substituir` faz delete atomico antes de insert — sem layouts orfaos
- [x] `get_by_cliente_id` usa `selectinload(mapeamentos)` — evita lazy load em contexto async
- [x] `delete_by_cliente_id` usa SQLAlchemy `delete()` — nao carrega objetos na memoria
- [x] `build_coluna_map` retorna `{campo_sistema.value: coluna_planilha}` — interface limpa

### Integracao com PqImportService

- [x] `pq_layout_repo=None` — retrocompativel, sem breaking change
- [x] `_resolver_mapa_colunas` retorna `None` quando repo e None ou layout nao existe
- [x] `_find_column_map_from_layout` normaliza headers — robusto a espacos/case
- [x] Fallback para `_find_column_map` quando sem layout — clientes existentes nao sao afetados

### Endpoint e Autenticacao

- [x] PUT usa `get_current_admin_user` — somente admins configuram layouts
- [x] GET usa `get_current_active_user` — usuarios comuns podem consultar
- [x] Router registrado em `v1/router.py`

### Testes

- [x] 7 unit tests em `test_pq_layout_service.py` — criar, obter, fallback None, build_coluna_map, validacao
- [x] 2 integration auth tests em `test_pq_layout_endpoint.py`
- [x] Suite: **107 PASS, 0 FAIL**

---

## Observacoes nao bloqueantes

1. `ColunasDetectadasResponse` no schema nao esta exposta por nenhum endpoint ainda — candidato a sprint futura.
2. `aba_nome` e `linha_inicio` existem no model mas nao sao usados na logica de parse atual — incremento futuro.

---

## Veredicto Final

**APROVADO.** Criterios de aceite satisfeitos:
- PUT /clientes/{id}/pq-layout com payload valido -> 200
- PUT sem descricao -> 422 (unit test `test_request_valida_campos_obrigatorios_faltando_descricao`)
- GET sem config -> null (unit test `test_obter_por_cliente_retorna_none_quando_nao_existe`)
- 107 PASS >= 93 PASS (criterio do plano)

Sprint F2-01 avanca para **DONE**.
