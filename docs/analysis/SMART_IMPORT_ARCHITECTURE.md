# Arquitetura de Smart Import: Dinamica Budget

## 1. Visão Geral (Princípio Central)
O objetivo principal é separar rigidamente o **Esforço de Entendimento (Flexível)** do **Esforço de Persistência (Rígido)**.

Planilhas de orçamentos (PQ), Composições (TCPO) e Bases antigas (BCUs) costumam apresentar severas variações de formato (cabeçalhos em linhas variadas, nomes de colunas diferentes, células mescladas).

**Arquitetura Pipeline Incremental:**
1. **Ingestão & Parser Flexível:** Aceita o arquivo, localiza onde os dados realmente começam (Header Detection) e lê a matriz bruta.
2. **Normalização Semântica (Smart Mapper):** Usa NLP/Embeddings e Fuzzy Matching para "adivinhar" qual coluna da planilha corresponde a qual campo do nosso modelo de banco de dados (gerando um *Confidence Score*).
3. **Validação Rígida (Pydantic Validator):** Tenta instanciar os modelos rigorosos de domínio. O que falha gera um log de erro anexado à linha.
4. **Staging / Preview:** Dados válidos e inválidos são salvos em uma área temporária (Staging).
5. **Human-in-the-loop:** O usuário visualiza o resultado, corrige o mapeamento ou ajusta linhas inválidas na interface.
6. **Efetivação Transacional (Commit):** Move os dados de Staging para as tabelas oficiais com rastreabilidade (Audit Trail) e suporte a rollback.

---

## 2. Tecnologias e Modelos (Alinhado à Stack Atual do Projeto)

A base atual em Python/FastAPI fornece o ecossistema perfeito para este modelo:

*   **Leitura de Excel/CSV:** `pandas` (para manipulação tabular robusta) combinado com `openpyxl`.
*   **Header Detection (Heurística + Estatística):** Algoritmos baseados na densidade de strings vs numéricos para encontrar a "linha de cabeçalho" real, ignorando logos e títulos soltos no topo.
*   **Mapeamento Semântico (Modelos Locais):**
    *   **Embeddings:** Usar a biblioteca atual `sentence-transformers` (ex: modelo `all-MiniLM-L6-v2` ou um finetuned em PT-BR como o `paraphrase-multilingual-MiniLM-L12-v2`).
    *   **Fuzzy Search:** O já presente `rapidfuzz` serve como uma camada rápida de *fallback* e verificação de typos (ex: "Cód." vs "Codigo").
*   **Validação de Negócio:** `pydantic` - A espinha dorsal para garantir tipos, valores não nulos e limites numéricos.
*   **OCR (Se expansão para PDFs for necessária):** `pytesseract` (Tesseract OCR) acoplado com `pdf2image`. Para tabelas complexas em PDF, bibliotecas como `Camelot` ou `Tabula-py`.
*   **Armazenamento de Staging:** Tabelas temporárias no PostgreSQL ou colunas `JSONB` na tabela de Importações (`ImportJob`).

---

## 3. Pipeline de Implementação Passo a Passo

### Fase 1: Ingestão e Detecção de Cabeçalho (Header Detection)
O script não assume que a linha 1 é o cabeçalho.
**Técnica:** Ler as primeiras 50 linhas. O cabeçalho geralmente é a primeira linha seguida por uma alta densidade de dados preenchidos (menos `NaNs` no Pandas) onde os tipos de dados da coluna (abaixo do cabeçalho) começam a ser consistentes (ex: coluna de custo tem números).

### Fase 2: Mapeamento Semântico (Smart Column Mapper)
Como mapear "Vlr. Unit" para `valor_unitario`?
1. **Dicionário de Sinônimos (Cache Local):** Antes de usar IA, verifique um dicionário de mapeamentos conhecidos aprovados anteriormente.
2. **Fuzzy Matching (`rapidfuzz`):** Compara o nome da coluna com os campos permitidos.
3. **Vector Search (Embeddings):** Transforma o cabeçalho da planilha em um vetor e compara (Cosense Similarity via `pgvector` ou cálculo local em memória com `torch`) com as descrições semânticas dos campos alvo.
   * *Exemplo:* Campo alvo `valor_unitario` (Descrição de contexto no modelo: "Preço monetário por unidade, custo unitário, R$ unit.").
4. **Confidence Score:** O sistema retorna uma taxa de confiança (0 a 100%). Se for > 85%, mapeia automaticamente. Se for entre 50-85%, mapeia com *warning* para revisão humana. Menos de 50%, deixa em branco para o usuário selecionar.

### Fase 3: Processamento Flexível e Limpeza
*   Remoção de caracteres especiais em números (R$, vírgulas).
*   Tratamento flexível de datas.
*   Preenchimento condicional de células mescladas (Forward-fill do `pandas` para hierarquias WBS/EAP onde a linha "pai" engloba as "filhas").

### Fase 4: Validador Rígido (`pydantic`)
Cada linha extraída tenta instanciar um `SchemaPydantic`.
```python
try:
    item = TabelaPrecoRowValidate(**row_dict)
    valid_rows.append(item)
except ValidationError as e:
    # Captura o erro, anexa à linha para o usuário ver O QUE precisa ser corrigido
    invalid_rows.append({"row": row_dict, "errors": e.errors()})
```

### Fase 5: Staging e Confirmação (Gravação)
Cria-se um domínio de `ImportJob` no banco:
*   `id_job`: UUID
*   `status`: PENDING, REVIEW_REQUIRED, COMPLETED, FAILED.
*   `mapping_metadata`: JSONB (Como o sistema mapeou as colunas e os scores).
*   `payload_staging`: JSONB ou tabela filha temporária (contém dados válidos e erros).

O Frontend puxa o `ImportJob`. Mostra os dados verdes (Ok) e vermelhos (Erro). O usuário pode corrigir uma célula errada no grid do frontend e mandar re-validar. Ao clicar em "Confirmar Importação", roda-se uma transaction SQL sólida.

---

## 4. Auditoria, Rollback e Versionamento

*   **Versionamento (Event Sourcing Light):** Para BASES e TCPO, a importação não dá UPDATE/DELETE destrutivo nos itens atuais. Ela insere uma nova "Revisão" de tabela ou desativa itens antigos e cria novos (Soft Delete).
*   **Transacionalidade Segura:** A efetivação do Staging para o Banco Principal (`app/backend/models/`) deve ocorrer dentro de um bloco `async with session.begin():`. Qualquer falha de integridade do PG aborta a carga inteira.
*   **Logs:** Utilizar o `structlog` existente para logar cada `ImportJob` criado, quem iniciou, e os tempos de inferência do modelo local para otimização futura.

---

## 5. Plano de Execução Incremental (Proposta Prática)

**Sprint 1: Base Flexível (Heurísticas)**
*   Criar endpoints de upload e a entidade `ImportJob`.
*   Implementar Leitura com Pandas + Header Detection heurístico (sem IA ainda).
*   Implementar mapeamento por FuzzySearch e Alias Fixo.
*   Staging via JSONB e endpoint de Preview.

**Sprint 2: Inteligência (Smart Mapper)**
*   Acoplar o modelo `sentence-transformers` (rodando no mesmo container da API ou num worker dedicado se consumir muita memória RAM).
*   Implementar a lógica de Confidence Score e sugerir colunas na UI.
*   Treinar o sistema para que mapeamentos confirmados pelo usuário sejam salvos como Sinônimos Prioritários (Feedback Loop de aprendizado sem retreinar pesos do modelo).

**Sprint 3: Endurecimento e UX**
*   Refinar os Schemas Pydantic de validação estrita.
*   Adicionar normalizadores pré-validação (regex de moeda, parser de unidade de medida).
*   Testes massivos com arquivos TCPO da PINI e PQs reais que estão no diretório root.
