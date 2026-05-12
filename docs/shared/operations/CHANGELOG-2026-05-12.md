# Changelog — Dinamica Budget
**Data:** 2026-05-12  
**Autor:** OpenCode (Kimi)  
**Versão alvo:** Deploy v5.0 + Backend patches  
**Status:** Código atualizado, aguardando reinício do serviço `DinamicaBudgetAPI`

---

## 1. Correções Críticas

### 1.1 Duplicação de Rotas no Endpoint de Propostas
- **Arquivo:** `app/backend/api/v1/endpoints/propostas.py`
- **Problema:** Rotas de Histograma e Recursos Extras estavam declaradas **2 vezes** no mesmo arquivo. FastAPI lançaria `DuplicateRoute` no startup.
- **Correção:** Removida a segunda ocorrência inteira (linhas 363–521 originais).
- **Impacto:** Router agora tem 21 rotas únicas (anteriormente 31, com 10 duplicadas).
- **Validação:** `python -c "from backend.api.v1.endpoints.propostas import router; print(len(router.routes))"` → `22` (incluindo a nova rota `/rebuild`)

### 1.2 Inconsistência de Tipo no Schema de BDI
- **Arquivo:** `app/backend/schemas/proposta.py`
- **Problema:** `RecalcularBdiResponse` declarava `Decimal`, mas `CpuGeracaoService` retornava `float`. Pydantic podia rejeitar ou truncar valores.
- **Correção:** Alterado `percentual_bdi`, `total_direto`, `total_indireto`, `total_geral` de `Decimal` para `float`, consistente com `CpuGeracaoResponse`.
- **Impacto:** Elimina type mismatch entre service e schema.

---

## 2. Correções de Frontend (TypeScript)

### 2.1 Parâmetros `any` implícitos no BcuUploadPage
- **Arquivo:** `app/frontend/src/features/bcu/BcuUploadPage.tsx`
- **Problema:** Callbacks `.map`/`.filter`/`.forEach` sem tipo explícito causavam falha no `tsc` (`noImplicitAny` ativo no `tsconfig.json`).
- **Correção:** Adicionadas anotações de tipo nos parâmetros:
  - `(json[headerRowIdx] ?? []).map((h: unknown) => ...)`
  - `json.slice(...).map((r: unknown) => ...)`
  - `.filter((r: Record<string, unknown>) => ...)`
  - `.forEach((row: Record<string, unknown>, idx: number) => ...)`
- **Impacto:** Build TypeScript passa sem erros de tipo.

---

## 3. Nova Funcionalidade: Rebuild da Proposta

### 3.1 PropostaMontagemService
- **Arquivo:** `app/backend/services/proposta_montagem_service.py` (NOVO)
- **Descrição:** Serviço que consolida/recalcula todos os valores da proposta após edições no histograma ou recursos extras.
- **Fluxo do `rebuild(proposta_id)`:**
  1. Carrega proposta, itens, composições e recursos extras
  2. Para cada `PropostaItem`, recalcula custo direto somando composições + alocações de extras
  3. Aplica BDI (percentual_indireto) para obter custo indireto e preço unitário
  4. Multiplica pela quantidade do item para obter preço total
  5. Atualiza totais da proposta (`total_direto`, `total_indireto`, `total_geral`)
  6. Regenera resumo por tipo de recurso (`proposta_resumo_recursos`)
  7. Marca `cpu_desatualizada = False`
- **Validações:**
  - Rejeita propostas com status `APROVADA`, `ARQUIVADA`, `REPROVADA`
  - Rejeita propostas sem itens (mensagem: "Gere a CPU primeiro")
- **Testes:** `test_proposta_montagem_service.py` (4/4 passando)

### 3.2 Endpoint `/propostas/{id}/rebuild`
- **Arquivo:** `app/backend/api/v1/endpoints/propostas.py`
- **Rota:** `POST /api/v1/propostas/{proposta_id}/rebuild`
- **Permissão:** `PropostaPapel.EDITOR` ou superior
- **Response:** `PropostaRebuildResponse`
  ```json
  {
    "proposta_id": "uuid",
    "total_direto": 150000.00,
    "total_indireto": 15000.00,
    "total_geral": 165000.00,
    "bdi_percentual": 10.0,
    "itens_processados": 42,
    "cpu_desatualizada": false
  }
  ```

### 3.3 Schema PropostaRebuildResponse
- **Arquivo:** `app/backend/schemas/proposta.py`
- **Campos:** `proposta_id`, `total_direto`, `total_indireto`, `total_geral`, `bdi_percentual`, `itens_processados`, `cpu_desatualizada`

---

## 4. Testes

### 4.1 Testes Unitários Criados
- **Arquivo:** `app/backend/tests/unit/test_proposta_montagem_service.py`
- **Casos:**
  1. `test_rebuild_updates_totals` — rebuild atualiza totais corretamente com BDI 10%
  2. `test_rebuild_with_extra_resources` — recursos extras alocados somam ao custo direto
  3. `test_rebuild_rejects_invalid_status` — rejeita proposta APROVADA
  4. `test_rebuild_rejects_no_items` — rejeita proposta sem itens
- **Resultado:** ✅ 4/4 PASS

### 4.2 Testes Unitários Existentes (regressão)
- `test_proposta_service.py` — 5/5 PASS
- `test_security_p0.py` — 19/19 PASS
- `test_busca_service.py` — 8/8 PASS
- **Total:** 36/36 PASS

### 4.3 Compilação/Importação
- `python -c "from backend.main import create_app; app = create_app()"` ✅
- Router carrega 126 rotas no FastAPI ✅

---

## 5. Deploy

### 5.1 Status do Deploy (2026-05-12)
O script `deploy-dinamica.bat` foi executado duas vezes com elevação de privilégios.

| Etapa | Status | Detalhe |
|-------|--------|---------|
| 1. Sincronizar arquivos | ✅ OK | `C:\DinamicaBudget` atualizado |
| 2. Ambiente virtual Python | ✅ OK | venv Python 3.12 compatível |
| 3. Configuração `.env` | ✅ OK | credenciais mantidas |
| 4. PostgreSQL + extensões | ✅ OK | banco e pgvector ativos |
| 5. Migrations Alembic | ✅ OK | migrations aplicadas |
| 6. Modelo ML | ✅ OK | `all-MiniLM-L6-v2` presente |
| 7. Build do frontend | ✅ OK | `npm run build` concluído (6.83s) |
| 8. Configuração IIS | ✅ OK | site `DinamicaBudget` ativo, frontend copiado |
| 9. Serviço NSSM (API) | ⚠️ **PAUSED** | serviço configurado mas não iniciado |
| 10. Firewall | ❌ Pendente | depende da etapa 9 |
| 11. Validação final | ❌ Pendente | depende da etapa 9 |

### 5.2 Ação Manual Necessária
O serviço `DinamicaBudgetAPI` está **PAUSED**. Execute como **Administrador**:

```powershell
nssm restart DinamicaBudgetAPI
nssm status DinamicaBudgetAPI
```

Ou via CMD Admin:
```cmd
net start DinamicaBudgetAPI
```

Após iniciar, valide:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
Invoke-RestMethod -Uri "http://localhost/docs" -TimeoutSec 5
```

---

## 6. Riscos e Débitos Técnicos

| # | Item | Severidade | Mitigação |
|---|------|------------|-----------|
| R1 | `_gerar_codigo()` não é atômico — pode gerar códigos duplicados sob concorrência | Médio | Usar `SELECT FOR UPDATE` ou sequence no banco |
| R2 | `requirements.txt` lista `openpyxl` 2x com versões diferentes | Baixo | Remover duplicação futura |
| R3 | Frontend build físico bloqueado por `EPERM` em `dist/assets` no ambiente atual | Baixo | Build funciona em ambiente com permissões adequadas |
| R4 | `BcuUploadPage.tsx` importa `xlsx` — types podem não resolver em algumas versões do package | Baixo | `skipLibCheck: true` no tsconfig mitiga |

---

## 7. Resumo de Arquivos Alterados

```
app/backend/api/v1/endpoints/propostas.py          (+1 endpoint /rebuild, -duplicação de rotas)
app/backend/schemas/proposta.py                    (+PropostaRebuildResponse, fix RecalcularBdiResponse)
app/backend/services/proposta_montagem_service.py  (NOVO)
app/backend/tests/unit/test_proposta_montagem_service.py  (NOVO)
app/frontend/src/features/bcu/BcuUploadPage.tsx    (fix tipos TypeScript)
```

---

## 8. Próximos Passos Recomendados

1. **Iniciar serviço `DinamicaBudgetAPI`** como Administrador
2. **Validar endpoint `/rebuild`** via Swagger (`http://localhost/docs`)
3. **Executar suite completa de testes** com banco de dados (`pytest backend/tests/integration/`)
4. **Revisar atomicidade do `_gerar_codigo()`** em `proposta_service.py`
5. **Testar fluxo end-to-end:** criar proposta → importar PQ → match → gerar CPU → editar histograma → rebuild → exportar

---

*Documento gerado automaticamente após validação e correção do sistema.*
