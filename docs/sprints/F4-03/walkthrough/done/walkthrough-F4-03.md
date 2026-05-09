# Walkthrough — F4-03 BASES/BCUs Upload Individual + CRUD

## Sprint: F4-03
## Worker: Kimi backend principal/hardening
## Data: 2026-05-08

---

## Resumo Executivo

Implementado o backend para upload individual (por tipo) e CRUD seguro de itens BCU/BASE, reutilizando 100% o schema `bcu.*` existente. Nenhuma migration foi necessária.

---

## Arquivos Alterados/Criados

### Novos
1. `app/backend/services/bcu_upload_service.py` — preview e importação individual por tipo.
2. `app/backend/services/bcu_crud_service.py` — CRUD seguro com sync base_tcpo.
3. `app/backend/tests/unit/test_bcu_upload_service.py` — 12 testes unitários.
4. `app/backend/tests/unit/test_bcu_crud_service.py` — 12 testes unitários.
5. `app/backend/tests/integration/test_bcu_upload_crud.py` — 3 testes de integração.

### Modificados
1. `app/backend/schemas/bcu.py` — adicionados schemas Create/Update e upload preview/confirm.
2. `app/backend/api/v1/endpoints/bcu.py` — novos endpoints de upload individual e CRUD.

---

## Como usar

### Upload Individual — Preview
```bash
curl -X POST "http://localhost:8000/api/v1/bcu/upload-individual/mo/preview" \
  -H "Authorization: Bearer <admin_token>" \
  -F "file=@mo.xlsx"
```

### Upload Individual — Confirmar
```bash
curl -X POST "http://localhost:8000/api/v1/bcu/upload-individual/mo/confirmar?cabecalho_id=<uuid>" \
  -H "Authorization: Bearer <admin_token>" \
  -F "file=@mo.xlsx"
```

### CRUD — Exemplo Mão de Obra
```bash
# Criar
curl -X POST "http://localhost:8000/api/v1/bcu/<cabecalho_id>/mao-obra" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"descricao_funcao": "Soldador", "salario": 4500}'

# Atualizar
curl -X PATCH "http://localhost:8000/api/v1/bcu/<cabecalho_id>/mao-obra/<item_id>" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"descricao_funcao": "Soldador Avançado"}'

# Deletar
curl -X DELETE "http://localhost:8000/api/v1/bcu/<cabecalho_id>/mao-obra/<item_id>" \
  -H "Authorization: Bearer <admin_token>"
```

---

## Estrutura dos arquivos XLSX para upload individual

Cada tipo aceita uma planilha com colunas fixas (primeira linha = header, dados a partir da segunda):

| Tipo | Colunas esperadas (ordem) |
|------|---------------------------|
| `mo` | codigo, descricao, salario, reajuste, periculosidade, refeicao, agua, vale, saude, seguro, ferias |
| `equipamentos` | codigo, equipamento, combustivel, consumo, aluguel, aluguel_mensal |
| `encargos` | (ignorada), tipo, grupo, codigo, discriminacao, taxa |
| `epi` | (ignorada), epi, unidade, custo, vida_util |
| `ferramentas` | (ignorada), descricao, unidade, preco |
| `mobilizacao` | descricao, funcao, tipo |

---

## Validação

- Preview rejeita: tipo inválido, arquivo não .xlsx, arquivo vazio.
- Confirmação rejeita: cabeçalho inexistente, linhas inválidas no arquivo.
- CRUD rejeita: cabeçalho inexistente, item inexistente, tipo inválido, campos obrigatórios em branco.

---

## Testes

```bash
cd app
export TEST_DATABASE_URL="postgresql+asyncpg://root:root@localhost:5432/dinamica_budget_test"
source .venv/bin/activate
pytest backend/tests/unit/test_bcu_upload_service.py backend/tests/unit/test_bcu_crud_service.py -xvs
pytest backend/tests/integration/test_bcu_upload_crud.py -xvs
```

Resultado: **27/27 passaram** (24 unitários + 3 integração).

---

## Próximos passos / Handoff QA

- QA deve validar os endpoints com arquivos XLSX reais de cada tipo.
- Verificar se o frontend consegue consumir os schemas de preview e confirmar.
- Testar edge cases: arquivos grandes, caracteres especiais, colunas faltantes.
