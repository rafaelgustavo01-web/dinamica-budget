# Walkthrough — Sprint F2-01: PQ Layout Cliente

**Data:** 2026-04-25
**Worker:** claude-sonnet-4-6
**Status:** TESTED

---

## O que foi entregue

Sistema de layout configuravel de importacao de PQ por cliente. Admins podem definir qual coluna da planilha do cliente corresponde a cada campo do sistema.

---

## Como usar

### 1. Configurar layout (admin)

```
PUT /api/v1/clientes/{cliente_id}/pq-layout
Authorization: Bearer <admin-token>

{
  "nome": "Layout SABESP",
  "mapeamentos": [
    {"campo_sistema": "descricao", "coluna_planilha": "Servico Executado"},
    {"campo_sistema": "quantidade", "coluna_planilha": "Coeficiente"},
    {"campo_sistema": "unidade", "coluna_planilha": "Und"},
    {"campo_sistema": "codigo", "coluna_planilha": "Item"}
  ]
}
```

### 2. Consultar layout configurado

```
GET /api/v1/clientes/{cliente_id}/pq-layout
```

Retorna `null` se nenhum layout foi configurado para o cliente.

### 3. Importar planilha

O endpoint existente `POST /propostas/{id}/pq/importar` detecta automaticamente se o cliente tem layout configurado e usa os nomes de colunas definidos. Sem layout: usa aliases padrao (descricao, servico, etc.).

---

## Estrutura de banco

```
operacional.pq_layout_cliente
  id uuid PK
  cliente_id uuid FK -> clientes.id CASCADE
  nome varchar(120)
  aba_nome varchar(120) nullable
  linha_inicio int default 2

operacional.pq_importacao_mapeamento
  id uuid PK
  layout_id uuid FK -> pq_layout_cliente.id CASCADE
  campo_sistema campo_sistema_pq_enum
  coluna_planilha varchar(120)
  UNIQUE (layout_id, campo_sistema)
```

---

## Validacoes

- `descricao` e obrigatorio nos mapeamentos (ValidationError se ausente)
- PUT substitui atomicamente o layout inteiro (delete + insert)
- Colunas sao comparadas apos normalizacao (lowercase, strip, collapse spaces)

---

## Testes

- 7 testes unitarios em `test_pq_layout_service.py` — todos PASS
- 2 testes de integracao em `test_pq_layout_endpoint.py` (auth gate) — PASS quando DB disponivel
- Suite total: 107 passed, 0 failed
