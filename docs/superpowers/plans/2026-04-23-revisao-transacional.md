# Revisão Transacional — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduzir o uso de commits implícitos e garantir que operações de leitura sejam puras (sem efeitos colaterais no banco). Consolidar o uso de `db.flush()` nos services e deixar o commit para o final do request via middleware/dependência FastAPI.

**Architecture:** Transações gerenciadas no escopo do request. Services executam `flush` para garantir que as constraints de banco sejam validadas e os IDs gerados, mas sem persistência definitiva até o final do sucesso da rota.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async

---

## Task 1: Revisar Configuração de Sessão e Idempotência

**Files:**
- Modify: `app/core/dependencies.py`
- Test: `app/tests/unit/test_transactional_purity.py`

### Step 1: Verificar autocommit e autoflush

Garantir que a `async_sessionmaker` não está fazendo commit automático.

```python
# app/core/dependencies.py
# Verificar se bind está correto
async_sessionmaker(..., autocommit=False, autoflush=False)
```

### Step 2: Implementar teste de idempotência de leitura

Criar um teste que verifica se um GET não incrementa versões ou altera timestamps de forma inesperada.

---

## Task 2: Refatorar Services para usar Flush em vez de Commit

**Files:**
- Modify: `app/services/auth_service.py`
- Modify: `app/services/versao_service.py`
- Modify: `app/services/servico_catalog_service.py`

### Step 1: Substituir `db.commit()` por `db.flush()`

Nos métodos de criação/atualização dos services, garantir que o estado é enviado ao banco (`flush`) mas não finalizado (`commit`).

```python
# Exemplo em VersaoService.criar_versao
db.add(nova_versao)
await db.flush()  # Garante que nova_versao.id esteja disponível
# ... lógica de clone ...
await db.flush()
# NÃO chamar db.commit() aqui
```

### Step 2: Commit parcial

```bash
git add app/services/
git commit -m "refactor(services): replace commit with flush for transactional safety"
```

---

## Task 3: Validar Rollback em Caso de Erro

**Files:**
- Modify: `app/api/v1/endpoints/versoes.py` (ou criar rota de teste)
- Test: `app/tests/integration/test_transaction_rollback.py`

### Step 1: Teste de falha após sucesso parcial

Simular um cenário onde uma versão é criada (`flush` OK) mas uma exceção ocorre antes do retorno do endpoint. Verificar que a versão **NÃO** existe no banco após a falha.

---

## Task 4: Documentar Estratégia Transacional

**Files:**
- Modify: `app/models/base.py` (docstring)
- Create: `docs/TRANSACTION_STRATEGY.md`

### Step 1: Registrar padrões

Documentar quando usar `flush`, quando usar `commit` (ex: background tasks) e como o rollback é tratado.

---

## Task 5: Regressão Geral e Walkthrough

**Files:**
- Test: full unit suite (pytest app/tests/unit)
- Create: `docs/walkthrough/done/walkthrough-S-03.md`

### Step 1: Executar e Documentar

Garantir que S-01, S-02 e S-04 (se concluída) continuam funcionando com a nova estratégia de commits centralizada.

---

## Plan Review Checklist

- [x] Spec coverage: services refactored to flush
- [x] Placeholder scan: none
- [x] Type consistency: async handled
- [x] Risco mitigado: rollback test included

## Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-23-revisao-transacional.md`.**
 Sprint moved to PLAN state.
