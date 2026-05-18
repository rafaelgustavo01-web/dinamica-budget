# Dinamica Budget — Análise Técnica do Smart Import / PQ Search

> Data: 2026-05-18
> Projeto: Dinamica Budget V2
> Módulo: Smart Import + Motor de Busca em Cascata (PQ Match)

---

## 1. Visão Geral da Arquitetura

O Smart Import e o PQ Match compartilham o mesmo motor de busca em cascata, mas atuam em momentos diferentes do fluxo:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FLUXO COMPLETO                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  1. UPLOAD PQ          → Smart Import (FileExtractor + RowClassifier)  │
│  2. DETECT HEADER      → HeaderDetector + ColumnMapper                   │
│  3. PARSE ROWS         → RowClassifier (ITEM/SECAO/TOTAL/VAZIA)         │
│  4. STAGE              → PqItem criados com status=PENDENTE              │
│  5. MATCH              → PqMatchService → BuscaService (4 camadas)       │
│  6. REVIEW             → Usuário confirma/rejeita sugestões             │
│  7. CONFIRM            → Itens vão para proposta como CONFIRMADO         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. O Motor de Busca em 4 Camadas (BuscaService)

Arquivo: `app/backend/services/busca_service.py`

### 2.1 Fase 0.1 — Código Exato (Circuit Break)

**Lógica:**
- Normaliza o texto de busca
- Procura primeiro em `operacional.itens_proprios` (item do cliente, com cliente_id + código)
- Se não encontrar, procura em `referencia.base_tcpo` (catálogo global)

**Threshold:** N/A — é match exato ou nada

**Score:** 1.0 (máxima confiança)

**Circuit break:** Sim — se encontrar, retorna imediatamente

### 2.2 Fase 0.2 — Itens Próprios do Cliente (PROPRIA + APROVADO)

**Lógica:**
- Usa `pg_trgm` (trigram similarity) em itens próprios do cliente
- Restrito a `status_homologacao = APROVADO`
- Acumula candidatos (não faz early-exit)

**Threshold:** `request.threshold_score` (default 0.65)

**Score:** O score do pg_trgm é usado diretamente como confiança

**Circuit break:** Não — acumula para competir com semântica

### 2.3 Fase 1 — Associação Direta (associacao_inteligente)

**Lógica:**
- Lookup em `associacao_inteligente` com `cliente_id + texto_normalizado`
- Se `CONSOLIDADA` (confirmada ≥ 3 vezes): score=1.0, circuit break imediato
- Se `VALIDADA` ou `SUGERIDA`: retorna com `confiabilidade_score`

**Threshold:** N/A — é lookup exato na tabela

**Score:**
- CONSOLIDADA: 1.0
- VALIDADA/SUGERIDA: `confiabilidade_score` (aprendido)

**Circuit break:** Apenas para CONSOLIDADA

### 2.4 Fase 3 — IA Semântica (pgvector)

**Lógica:**
- Gera embedding do texto de busca via `sentence-transformers` (`all-MiniLM-L6-v2`)
- Busca cosine similarity em `referencia.tcpo_embeddings`
- Batch load dos serviços encontrados

**Threshold:** `request.threshold_score` (default 0.65)

**Score:** Cosine similarity (0.0 a 1.0)

**Circuit break:** Não — sempre executa para competir

### 2.5 Fase 2 — Fuzzy Global (Fallback)

**Lógica:**
- Executa SÓ se todas as fases anteriores não retornarem resultados
- Usa `pg_trgm` em `referencia.base_tcpo` (catálogo global)

**Threshold:** `min(0.30, request.threshold_score * 0.45)`
  - Com threshold default 0.65: `min(0.30, 0.2925)` = **0.2925**
  - Com threshold 0.45 (PQ Match): `min(0.30, 0.2025)` = **0.2025**

**Score:** pg_trgm similarity

**Circuit break:** Não — é o último recurso

---

## 3. Thresholds Configurados

### 3.1 Thresholds da Busca (BuscaServicoRequest)

| Parâmetro | Default | Range | Descrição |
|-----------|---------|-------|-----------|
| `threshold_score` | 0.65 | 0.0–1.0 | Score mínimo para considerar um match válido |
| `limite_resultados` | 5 | 1–50 | Máximo de resultados retornados |

### 3.2 Thresholds do PQ Match (PqMatchService)

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `threshold_score` | 0.45 | Mais permissivo que busca normal (0.65) |
| `limite_resultados` | 10 | Mais resultados para dar opções ao usuário |
| `score_confianca` mínimo para sugerir | 0.55 | Abaixo disso, mantém PENDENTE |
| `COMMIT_CHUNK` | 50 | Commit parcial a cada 50 itens |
| `MAX_PQ_ROWS` | 3500 | Limite de itens processados por batch |

### 3.3 Thresholds das Fases

| Fase | Threshold Calculation | Valor (com 0.65) | Valor (com 0.45) |
|------|------------------------|------------------|------------------|
| Fuzzy | `min(0.30, threshold * 0.45)` | 0.2925 | 0.2025 |
| Semântica | `threshold_score` direto | 0.65 | 0.45 |
| Itens Próprios | `threshold_score` direto | 0.65 | 0.45 |

---

## 4. Tratamento de Itens Não-Serviço

### 4.1 O Problema Central

O motor de busca atual foi projetado principalmente para **serviços TCPO** (composições de obra). Quando a PQ contém:
- **Equipamentos** (tipo_recurso = EQUIPAMENTO)
- **Ferramentas** (tipo_recurso = FERRAMENTA)
- **Insumos** (tipo_recurso = INSUMO)

O comportamento é o seguinte:

### 4.2 Como Funciona Hoje

1. **Smart Import (RowClassifier):**
   - Classifica apenas em: ITEM / SECAO / TOTAL / VAZIA
   - **NÃO diferencia** se o item é serviço, equipamento, ferramenta ou insumo
   - A classificação é baseada apenas na presença de `quantidade + unidade + descricao`

2. **Busca (BuscaService):**
   - Fase 0–1 procura em catálogos de **serviços** (base_tcpo, itens_proprios)
   - Fase 3 (semântica) busca em embeddings de **serviços**
   - **NÃO existe** busca separada por tipo_recurso
   - **NÃO existe** catálogo separado para equipamentos/ferramentas/insumos

3. **PQ Match (PqMatchService):**
   - Passa a descrição do item para o BuscaService
   - Não informa o tipo_recurso na busca
   - O match é feito puramente por similaridade textual

### 4.3 Consequências

- Itens de equipamento/ferramenta/insumo que existem no catálogo de serviços podem ser encontrados **por acaso** (se a descrição for similar)
- Itens que **não** existem no catálogo de serviços ficam como `SEM_MATCH` ou `PENDENTE`
- O usuário precisa fazer match manual para esses itens
- O sistema **não aprende** que certos padrões de descrição correspondem a equipamentos vs serviços

### 4.4 Onde Estão os Dados de Não-Serviços

Arquivos relevantes:
- `bcu_service.py`: Lê abas EQUIPAMENTOS, FERRAMENTAS, INSUMOS de planilhas BCU
- `etl_service.py`: Mapeia colunas de Excel para TipoRecurso (MAT.→INSUMO, EQP.→EQUIPAMENTO, FER.→FERRAMENTA)
- `histograma_service.py`: Monta histograma separando por tipo_recurso

Porém, **esses dados não são usados no motor de busca** para PQ import.

---

## 5. Fluxo de Dados do Smart Import

### 5.1 Pipeline Completo

```
Arquivo (CSV/XLSX)
  ↓
FileExtractor.from_bytes() — detecta formato, lê aba
  ↓
HeaderDetector.detect() — encontra linha de cabeçalho
  ↓
ColumnMapper.from_headers() — mapeia colunas (código, descrição, unidade, quantidade)
  ↓
RowClassifier.classify() — classifica cada linha (ITEM/SECAO/TOTAL/VAZIA)
  ↓
Staging — cria PqItem com status=PENDENTE
  ↓
PqMatchService.executar_match_para_proposta()
  ↓
  ├── Para cada PqItem:
  │     └── BuscaService.buscar()
  │           ├── Fase 0.1: Código Exato
  │           ├── Fase 0.2: Itens Próprios
  │           ├── Fase 1: Associação Direta
  │           ├── Fase 3: Semântica
  │           └── Fase 2: Fuzzy (fallback)
  │     └── Se score_confianca ≥ 0.55: atualiza para SUGERIDO
  │     └── Se score_confianca < 0.55: mantém PENDENTE
  │     └── Se sem resultados: atualiza para SEM_MATCH
  ↓
Review — usuário confirma/rejeita
  ↓
Confirm → item vira CONFIRMADO na proposta
```

### 5.2 APIs Envolvidas

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/smart-import` | POST | Cria job de importação |
| `/api/v1/smart-import/{id}/commit` | POST | Confirma importação, cria PqItems |
| `/api/v1/propostas/{id}/pq/preview` | POST | Preview da planilha (opcional) |
| `/api/v1/propostas/{id}/pq/importar` | POST | Importação direta (legado) |
| `/api/v1/propostas/{id}/pq/match` | POST | Executa match automático |
| `/api/v1/busca` | POST | Busca genérica (também usada internamente) |

---

## 6. Problemas Identificados

### 6.1 Problema 1: Threshold PQ Match Muito Permissivo

- PQ Match usa `threshold_score=0.45` (vs 0.65 da busca normal)
- Fuzzy threshold fica em `min(0.30, 0.45*0.45) = 0.2025`
- Isso pode gerar matches de baixa qualidade para itens não-serviço

### 6.2 Problema 2: Não Diferenciação por TipoRecurso

- O motor de busca não recebe `tipo_recurso` como parâmetro
- Equipamentos, ferramentas e insumos competem no mesmo espaço de busca que serviços
- O catálogo `base_tcpo` é predominantemente serviços

### 6.3 Problema 3: RowClassifier Não Diferencia Categorias

- `RowClassifier` só vê: ITEM / SECAO / TOTAL / VAZIA
- Não identifica se um ITEM é "mão de obra", "equipamento", "material"
- Essa informação poderia melhorar a busca

### 6.4 Problema 4: Associação Inteligente Só Aprende Serviços

- A tabela `associacao_inteligente` só aponta para `base_tcpo`
- Não existe mecanismo similar para equipamentos/ferramentas/insumos
- O "aprendizado" do sistema é limitado a serviços

### 6.5 Problema 5: Fuzzy Threshold Muito Baixo para Não-Serviços

- Para itens não-serviço, o fuzzy match com threshold 0.20+ pode retornar resultados irrelevantes
- O sistema não tem como saber que "betoneira" deveria buscar em equipamentos, não em serviços

---

## 7. Recomendações Técnicas

### 7.1 Curto Prazo (Quick Wins)

1. **Aumentar threshold mínimo para sugerir:**
   - Aumentar `score_confianca` mínimo de 0.55 para 0.65 em PQ Match
   - Ou tornar configurável por cliente

2. **Adicionar tipo_recurso na busca:**
   - Incluir `tipo_recurso` no `BuscaServicoRequest`
   - Filtrar `base_tcpo` por tipo quando informado
   - Criar catálogos separados ou índices por tipo

3. **Melhorar RowClassifier:**
   - Adicionar detecção de categoria baseada em palavras-chave
   - Ex: "mão de obra", "hora" → MO; "betoneira", "compactador" → EQUIPAMENTO

### 7.2 Médio Prazo

4. **Criar associações por tipo_recurso:**
   - Extender `associacao_inteligente` para suportar múltiplos catálogos
   - Ou criar tabelas separadas: `associacao_equipamento`, `associacao_insumo`

5. **Embeddings por tipo:**
   - Gerar embeddings separados por categoria (serviço, equipamento, insumo)
   - Busca semântica filtrada por tipo_recurso

6. **Import profiles por tipo:**
   - Smart Import poderia detectar o "tipo" da PQ (serviços vs equipamentos)
   - Aplicar regras de busca diferentes por tipo

### 7.3 Longo Prazo (ML)

7. **Classificador automático de tipo_recurso:**
   - Treinar modelo para classificar descrições em MO/INSUMO/FERRAMENTA/EQUIPAMENTO/SERVICO
   - Usar como pre-processamento antes da busca

8. **Sistema de feedback ativo:**
   - Quando usuário faz match manual, perguntar o tipo_recurso
   - Usar para melhorar o classificador e o motor de busca

---

## 8. Arquivos-Chave do Sistema

| Arquivo | Responsabilidade |
|---------|------------------|
| `services/busca_service.py` | Motor de busca em 4 camadas |
| `services/pq_match_service.py` | Orquestra match para PQ items |
| `services/pq_import_service.py` | Importação de planilhas PQ |
| `services/smart_import_service.py` | Smart Import com profile learning |
| `services/smart_import/row_classifier.py` | Classificação de linhas da planilha |
| `services/smart_import/column_mapper.py` | Mapeamento de colunas |
| `services/smart_import/header_detector.py` | Detecção de cabeçalho |
| `services/smart_import/extractor.py` | Extração de arquivo |
| `schemas/busca.py` | Schema de request/response da busca |
| `models/enums.py` | Enumerações (TipoRecurso, StatusMatch, etc) |
| `repositories/base_tcpo_repository.py` | Acesso ao catálogo TCPO |
| `repositories/itens_proprios_repository.py` | Acesso a itens do cliente |
| `repositories/associacao_repository.py` | Acesso a associações inteligentes |

---

*Relatório gerado automaticamente por análise de código em 2026-05-18.*
