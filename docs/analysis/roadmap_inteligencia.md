# Roadmap de Inteligência de Produto: Dinamica Budget

Este documento define a evolução da inteligência do Dinamica Budget, transformando fluxos manuais pesados em experiências "mágicas" e fluidas, mantendo governança estrita (on-premise first, RBAC, auditoria).

## 1. Visão Estratégica
**Objetivo:** Eliminar o atrito na orçamentação através de IA aplicada.
**Abordagem:** Inteligência progressiva e híbrida. Operações determinísticas e sensíveis a custo/latência rodam 100% locais (pgvector + sentence-transformers). Tarefas não-estruturadas complexas (extração de escopo de PDF/Excel, estruturação de árvores de composição) utilizam LLMs com guardrails rígidos (LLM as a Function).

## 2. Roadmap Incremental

### Fase 1: Importação de PQ (Planilha de Quantidades) & Match Inteligente (Local)
*Foco: Automação do "Copy/Paste"*
- **Importador Estruturado:** Upload de Excel (PQ). O backend faz o parsing em batch.
- **Bulk Smart Match (On-Premise):** Utilizar o motor de 4 fases (Vector -> Fuzzy -> Exact -> Assoc) em lote para sugerir o mapeamento automático de linhas da PQ para serviços TCPO/Próprios.
- **UX:** Interface de conciliação "Tinder-like" na planilha (Aceitar/Recusar/Substituir), alimentando imediatamente a tabela `associacao_inteligente` para auto-aprendizado.
- **Latência/Custo:** Custo zero. Latência baixa (batch embeddings locais).

### Fase 2: Catálogo Dinâmico & Árvore com LLM (Híbrido)
*Foco: Geração e Organização de Conteúdo*
- **Engenharia de Prompt para Composições:** Usuário descreve um serviço ("Fazer parede de drywall 2x3m"). Um LLM (Remoto/Seguro via API ou Llama 3 local se hardware permitir) decompõe em insumos TCPO conhecidos (busca RAG no catálogo).
- **Árvore de Serviços:** Classificação automática de novos serviços na taxonomia do cliente usando embeddings.
- **Anti-alucinação:** O LLM *não* cria preços nem insumos inventados; ele retorna chaves (IDs) de busca para o banco de dados. O backend faz a junção e precificação.

### Fase 3: Upload/CRUD de Bases e Clientes/Folha PC
*Foco: Gestão de Dados Próprios*
- **Ingestão Dinâmica de Bases:** Pipeline ETL para clientes fazerem upload de suas tabelas de salários (Folha PC) e materiais.
- **Indexação Vetorial Automática:** Triggers em background (via Celery/TaskIQ) que geram embeddings para novos itens do CRUD, inserindo-os no catálogo do cliente (RBAC isolado).
- **Match de RH/Folha:** Cruzamento inteligente de cargos da Folha PC do cliente com a mão de obra base do TCPO, normalizando nomenclaturas.

### Fase 4: UX Contextual (Co-piloto Orçamentário)
*Foco: Fluidez "Mágica"*
- **Agentic UX:** A interface reage ao contexto. Se o usuário importa uma PQ de "Fundações", a busca já aplica pré-filtros semânticos (boost) para serviços de terraplenagem e concreto.
- **Alertas de Anomalia:** Modelos estatísticos simples alertando sobre discrepâncias de preço ou rendimento frente ao histórico do cliente na `auditoria_log`.

## 3. Arquitetura (Motor Híbrido de IA)

```
[ Frontend (React) ] <--> [ FastAPI Backend ]
                                |
        +-----------------------+-----------------------+
        |                       |                       |
[ RAG Engine (Local) ]  [ LLM Gateway (Remote/Local) ] [ PostgreSQL 16 ]
- Sentence-Transformers - OpenAI / Azure / Ollama      - pgvector
- all-MiniLM-L6-v2      - Strict JSON Output           - pg_trgm
- Embeddings em Batch   - Guardrails (Pydantic)        - RBAC / Logs
```
* **Roteamento de IA:** Buscas e associações rodam no `RAG Engine` local. Extração de arquivos (PQ desestruturada) e decomposição de escopo passam pelo `LLM Gateway`.

## 4. Regras Endurecidas & Anti-Alucinação
1. **RAG Restrito (Grounded Generation):** O LLM nunca gera preços ou produtividade livremente. Ele recebe o catálogo (via vector search) no prompt e deve selecionar itens válidos.
2. **LLM as a Function:** O output do LLM deve ser validado via `Pydantic`. Qualquer resposta fora do schema (ex: IDs inexistentes) resulta em fallback ou recusa.
3. **Isolamento de Tenant (RBAC):** Os filtros vetoriais (HNSW) devem sempre incluir uma cláusula dura `WHERE cliente_id = X OR cliente_id IS NULL` antes do cálculo de similaridade, impossibilitando vazamento semântico.
4. **Human-in-the-loop (HITL):** Mapeamentos de PQ e novas composições geradas por IA entram no fluxo de `homologacao.py` como `PENDENTE`. Nenhuma IA escreve direto no orçamento final sem aprovação.

## 5. Observabilidade, Custo e Latência
- **Observabilidade:** Adição de metadados no `structlog` (Fase de busca, Tempo do embedding, Score de confiança, Provedor de IA). Painel de telemetria mostrando taxa de aceite das associações mágicas.
- **Custo:** Limitar chamadas externas (LLM pago) apenas para tarefas não-estruturadas. Armazenar em cache (Redis/LRU) decomposições comuns de serviços.
- **Latência:** `sentence-transformers` rodando no mesmo servidor em memória (pool de instâncias FastAPI). Importações grandes de PQ devem ser processadas em background (Async/WebSockets) com barra de progresso no front, evitando timeouts na API. Fallback para busca Fuzzy nativa (pg_trgm) caso o serviço de embeddings tenha pico de gargalo.
