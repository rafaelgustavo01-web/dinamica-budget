# Regras de Negócio — Composição e Rebuild de Propostas

**Data:** 2026-05-12  
**Versão:** 1.0  
**Status:** Ativo

---

## 1. Fluxo de Vida de uma Proposta

```
RASCUNHO → CPU_GERADA → EM_ANALISE → APROVADA
                ↓
         REBUILD (recálculo)
                ↓
         [Totais atualizados]
```

### Estados Permitidos para Rebuild
- `RASCUNHO`: Proposta em criação
- `CPU_GERADA`: Após geração inicial da CPU
- `EM_ANALISE`: Em fase de revisão

### Estados Bloqueados para Rebuild
- `APROVADA`: Não pode ser modificada
- `ARQUIVADA`: Fechada
- `REPROVADA`: Finalizada

---

## 2. Hierarquia de Custos

### 2.1 Nível de Item (PropostaItem)

```
┌─ Composições (somatório)
│  ├─ Material
│  ├─ Mão de Obra
│  └─ Equipamento
│
├─ Recursos Extras (alocados ao item)
│
└─ Total = Composições + Extras
   ↓
   Custo Direto Unitário (CDU)
```

**Fórmula:**
```
CDU = Σ(composição.custo_total) + Σ(extra.custo × extra.quantidade)
```

### 2.2 Nível de Proposta (Totais)

```
Para cada item:
  CDU × Quantidade = Custo Direto do Item
  
Total Direto = Σ(CDU × Quantidade) para todos items

Custo Indireto Unitário = CDU × BDI_fraction
Total Indireto = Σ(Custo Indireto Unitário × Quantidade)

Preço Unitário = CDU + CIU (Custo Indireto Unitário)
Preço Total = Preço Unitário × Quantidade

Total Geral = Total Direto + Total Indireto
```

---

## 3. BDI (Benefício, Despesa Indireta)

### 3.1 Definição
- **Percentual**: 0 a 100% (ex: 28.5%)
- **Aplicação**: Multiplicador sobre custo direto
- **Proporção**: 1 BDI por proposta (mesmo para todos items)

### 3.2 Cálculo
```
BDI Fraction = BDI_Percentual / 100
              (ex: 28.5% → 0.285)

Custo Indireto = Custo Direto × BDI Fraction
Preço = Custo Direto + Custo Indireto
      = Custo Direto × (1 + BDI Fraction)
```

### 3.3 Componentes de BDI
- **Impostos**: IRPJ, CSLL, PIS, COFINS
- **Despesas**: Administrativas, comerciais, financeiras
- **Lucro**: Margem esperada

---

## 4. Composição de Valores

### 4.1 Fontes de Dados

#### A. Composições (PropostaItemComposicao)
- Vêm de: Explosão de tabela de insumos (ex: TCPO)
- Tipos: Material, MO, Equipamento
- Campos: `descricao_insumo`, `quantidade_consumo`, `custo_unitario_insumo`, `custo_total_insumo`

#### B. Recursos Extras (PropostaRecursoExtra)
- Adicionados manualmente
- Tipos: Encargos, Mobilização, Seguro, etc.
- Podem ser: **Alocados** (a composições) ou **Não-alocados** (standalone)

#### C. Cálculos Derivados
- BDI (% indireto)
- Totalizações por tipo de recurso
- Resumos consolidados

### 4.2 Busca de Valores (GET /propostas/{id}/composicoes/valores)

**Retorna:**
```json
{
  "proposta_id": "uuid",
  "codigo": "PROP-001",
  "status": "CPU_GERADA",
  "percentual_bdi": 28.5,
  "items": [
    {
      "id": "uuid",
      "codigo": "01",
      "descricao": "Escavação",
      "quantidade": 100.0,
      "custo_direto_unitario": 85.0,
      "custo_indireto_unitario": 24.225,
      "preco_unitario": 109.225,
      "preco_total": 10922.5,
      "composicoes_count": 3,
      "extras_count": 1
    }
  ],
  "totais": {
    "total_direto": 8500.0,
    "total_indireto": 2422.5,
    "total_geral": 10922.5
  },
  "resumo_por_tipo": {
    "MATERIAL": { "direto": 4000, "indireto": 1140, "total": 5140 },
    "MO": { "direto": 3000, "indireto": 855, "total": 3855 },
    "EQUIPAMENTO": { "direto": 1500, "indireto": 427.5, "total": 1927.5 }
  }
}
```

---

## 5. Validação de Composição

### 5.1 Checklist (GET /propostas/{id}/composicoes/validar)

| Validação | Tipo | Descrição |
|-----------|------|-----------|
| Items sem composição | ❌ Erro | Todos items devem ter ≥1 composição ou extra |
| BDI inconsistente | ⚠️ Aviso | BDI deve ser igual para todos items |
| Custos zerados | ⚠️ Aviso | Alguns items com CDU = 0 |
| Preço não bate | ⚠️ Aviso | Preço unitário ≠ CDU × (1 + BDI%) |
| Totais inválidos | ⚠️ Aviso | Somas não conferem |

### 5.2 Resposta
```json
{
  "proposta_id": "uuid",
  "valido": true,
  "erros": [],
  "avisos": [],
  "items_total": 42,
  "items_com_composicao": 42,
  "items_vazios": 0
}
```

---

## 6. Rebuild de Proposta

### 6.1 Quando Usar
- ✅ Após editar composições no histograma
- ✅ Após alocar/desalocar recursos extras
- ✅ Após ajustar BDI
- ✅ Antes de gerar versão para aprovação

### 6.2 Fluxo (POST /propostas/{id}/rebuild)

```
1. Carregar proposta (validar status)
2. Carregar items
3. Carregar composições (agrupadas por item)
4. Carregar recursos extras com alocações
5. Para cada item:
   a. Somar composições + extras alocadas
   b. Aplicar BDI
   c. Calcular preços
6. Somar totais
7. Regenerar resumo por tipo
8. Salvar e marcar cpu_desatualizada = false
9. Retornar novos totais
```

### 6.3 Validações Obrigatórias
- ✅ Proposta existe
- ✅ Status é permitido (RASCUNHO, CPU_GERADA, EM_ANALISE)
- ✅ Proposta tem items
- ✅ User tem permissão EDITOR+

### 6.4 Resposta (POST /propostas/{id}/rebuild)
```json
{
  "proposta_id": "uuid",
  "total_direto": 8500.0,
  "total_indireto": 2422.5,
  "total_geral": 10922.5,
  "bdi_percentual": 28.5,
  "itens_processados": 42,
  "cpu_desatualizada": false
}
```

---

## 7. Relatório de Composição

### 7.1 Finalidade
- Auditoria: Entender como cada valor foi calculado
- Debug: Encontrar discrepâncias
- Documentação: Justificar preços em propostas

### 7.2 Endpoint (GET /propostas/{id}/composicoes/relatorio)

**Estrutura:**
```json
{
  "proposta": {
    "id": "uuid",
    "codigo": "PROP-001",
    "status": "CPU_GERADA"
  },
  "items_detalhados": [
    {
      "item": {
        "codigo": "01",
        "descricao": "Escavação",
        "quantidade": 100.0
      },
      "composicoes": {
        "por_tipo": {
          "EQUIPAMENTO": { "custo": 7500 },
          "MO": { "custo": 2000 }
        },
        "total": 9500
      },
      "extras_alocadas": {
        "items": [
          {
            "descricao": "Seguro",
            "tipo": "ENCARGOS",
            "custo": 95
          }
        ],
        "total": 95
      },
      "custos": {
        "direto_unitario": 95.95,
        "indireto_unitario": 27.34,
        "bdi_percentual": 28.5,
        "preco_unitario": 123.29,
        "preco_total": 12329
      }
    }
  ],
  "totais_proposta": {
    "total_direto": 8500.0,
    "total_indireto": 2422.5,
    "total_geral": 10922.5
  }
}
```

---

## 8. Impacto no Frontend

### 8.1 Novos Endpoints Consumidos
- `GET /propostas/{id}/composicoes/valores` — Listar composição
- `GET /propostas/{id}/composicoes/validar` — Validar dados
- `GET /propostas/{id}/composicoes/relatorio` — Gerar relatório
- `POST /propostas/{id}/rebuild` — Recalcular proposta

### 8.2 Fluxo de UX
1. **Página de Proposta** → Abrir "Composição de Valores"
2. **Buscar** → `GET /propostas/{id}/composicoes/valores`
3. **Validar** → `GET /propostas/{id}/composicoes/validar`
4. **Editar** → Modificar composições/extras
5. **Rebuild** → `POST /propostas/{id}/rebuild`
6. **Relatório** → `GET /propostas/{id}/composicoes/relatorio`

---

## 9. Testes Unitários

### 9.1 Service: PropostaComposicaoService
- ✅ `test_buscar_valores_proposta_success`
- ✅ `test_buscar_valores_proposta_not_found`
- ✅ `test_buscar_valores_proposta_no_items`
- ✅ `test_validar_valores_composicao_valido`
- ✅ `test_validar_valores_composicao_items_vazios`

### 9.2 Service: PropostaMontagemService (Rebuild)
- ✅ `test_rebuild_updates_totals`
- ✅ `test_rebuild_with_extra_resources`
- ✅ `test_rebuild_rejects_invalid_status`
- ✅ `test_rebuild_rejects_no_items`

---

## 10. Casos de Uso Reais

### 10.1 Caso 1: Editar Histograma
```
1. Usuário abre ProposalHistogramaPage
2. Modifica quantidade de composições
3. Clica "Salvar Alterações"
4. Frontend chama POST /propostas/{id}/rebuild
5. Backend recalcula totais
6. Frontend recarrega valores com GET /composicoes/valores
7. Tela atualiza com novos preços
```

### 10.2 Caso 2: Alocar Recurso Extra
```
1. Usuário abre ProposalDetailPage
2. Encontra composição "Retroescavadeira"
3. Aloca extra "Seguro" a essa composição
4. Frontend chama POST /propostas/{id}/rebuild
5. Backend recalcula: CDU agora inclui seguro
6. Total geral atualizado
7. Resumo por tipo recalculado
```

### 10.3 Caso 3: Auditoria de Preços
```
1. Auditor abre proposta
2. Clica em "Relatório de Composição"
3. Frontend chama GET /propostas/{id}/composicoes/relatorio
4. Vê breakdown completo de cada item
5. Valida BDI, totalizações
6. Exporta relatório ou compartilha
```

---

## 11. Integração com Sistemas Externos

### 11.1 TCPO (Tabela de Custos)
- Fonte de composições padrão
- Cada item pode referenciar múltiplas composições TCPO
- Custos vêm de tabelas mantidas externamente

### 11.2 BCU (Base de Composição de Custos)
- Alternativa local ao TCPO
- Gerenciável no módulo Bcu
- Ambos podem ser usados na mesma proposta

---

## 12. Performance e Otimizações

### 12.1 N+1 Queries
- ❌ **Problema**: Carregar items depois composições individualmente
- ✅ **Solução**: `list_by_proposta_items_batch()` com MAP

### 12.2 Cálculos em Banco vs Aplicação
- ✅ **Regra**: Cálculos simples na aplicação (Python)
- ✅ **Razão**: Legibilidade, testabilidade, controle
- ⚠️ **Exception**: Somas agregadas podem ir em SQL se volume > 100k

### 12.3 Cache
- ⚠️ **Não cacheado**: Valores mudam com cada rebuild
- ✅ **Cacheável**: Composições TCPO (TTL: 1 dia)

---

## 13. Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| Totais não batem | BDI inconsistente | Validar com GET /composicoes/validar |
| Items vazios | Sem composições | Alocar composições ou extras |
| Rebuild falha | Status inválido | Proposta deve estar em RASCUNHO/CPU_GERADA/EM_ANALISE |
| Preços zerados | Composição sem custo | Verificar tabela TCPO/BCU |
| Extra não soma | Não alocada | Alocar ao item via composição |

---

## 14. Próximas Melhorias

- [ ] Suportar BDI diferente por tipo de recurso
- [ ] Histórico de rebuilds (auditoria)
- [ ] Exportar composição em Excel
- [ ] Comparar versões de proposta (diffs)
- [ ] API de bulk-rebuild para múltiplas propostas

---

**Última Atualização:** 2026-05-12  
**Próxima Revisão:** 2026-06-12
