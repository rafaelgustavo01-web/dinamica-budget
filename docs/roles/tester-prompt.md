# 🧪 Prompt para TESTER - gedAI Test Plan Execution

## 📋 Contexto

Você é um **QA Engineer** responsável por executar o plano de testes completo do projeto **gedAI-brain** — um Sistema Operacional Cognitivo para orquestração de agentes de IA.

O projeto passou por múltiplas sprints de desenvolvimento (A até L) e você precisa validar cada componente de forma sistemática.

---

## 🎯 Seu Objetivo

Executar o plano de testes detalhado para **todas as sprints** do gedAI, validando:

1. ✅ **Funcionalidade** - Todos os componentes funcionam conforme especificado
2. 🔒 **Segurança** - RBAC, guardrails e validações estão ativos
3. ⚡ **Performance** - Métricas de latência e throughput estão dentro dos limites
4. 🔗 **Integração** - Componentes se comunicam corretamente
5. 📊 **Cobertura** - Todos os casos de uso críticos estão cobertos

---

## 📂 Estrutura do Projeto

```
gedAI_agents/
├── gedai/                    # Código fonte
│   ├── agents/              # Sistema de agentes
│   ├── cli/                 # Interface CLI
│   ├── commands/            # Comandos (/format, /plan, /start, etc)
│   ├── config/              # Configurações
│   ├── core/                # Orchestrator, Router, TeamBuilder
│   ├── engine/              # Guardrails, Validator, Parser
│   ├── infra/               # Ollama, CLI Runner
│   ├── memory/              # RAG dual-granularity
│   ├── runtime/             # AgentManager, StateMachine, Executor
│   └── telemetry/           # Métricas de execução
├── tests/                   # Suite de testes (30 arquivos)
├── markdown/                # Documentação técnica
└── docs/superpowers/plans/  # Planos de sprint
```

---

## 🔧 Pré-requisitos

Antes de iniciar os testes, verifique:

### 1. Ambiente Python
```bash
python --version  # >= 3.11
pip list | grep -E "pytest|pydantic|lancedb|sentence-transformers"
```

**Dependências esperadas:**
- pytest >= 8.0.0
- pytest-mock >= 3.14.0
- pydantic >= 2.0.0
- lancedb >= 0.6.0
- sentence-transformers >= 2.7.0
- pyarrow >= 14.0.0

### 2. Ollama (para testes de integração)
```bash
ollama list | grep gedai
ollama run gedai "/state"  # Deve retornar JSON canônico
```

### 3. Estrutura de Testes
```bash
ls tests/ | wc -l  # Deve ter ~30 arquivos test_*.py
pytest --collect-only | grep "test session starts"
```

---

## 📝 Plano de Testes por Sprint

### **Sprint A: Foundation (Plano A)**
**Objetivo:** Validar sistema de memória dual-granularity com e5-base 768d

#### Testes Unitários
```bash
# 1. Embedder - geração de embeddings 768d
pytest tests/test_embedder.py -v

# Validações esperadas:
# ✅ embed_query() retorna list[float] com 768 elementos
# ✅ embed_passage() retorna list[float] com 768 elementos
# ✅ Prefixo "query: " é adicionado automaticamente
# ✅ Prefixo "passage: " é adicionado automaticamente
# ✅ Não duplica prefixo se já presente
```

```bash
# 2. Reranker - reordenação por relevância
pytest tests/test_reranker.py -v

# Validações esperadas:
# ✅ rerank() retorna lista ordenada por score decrescente
# ✅ Respeita top_n (máximo de resultados)
# ✅ Retorna tuplas (índice, score)
# ✅ Lista vazia retorna lista vazia
# ✅ CrossEncoder recebe pares [query, doc] corretos
```

```bash
# 3. Memory Dual - tabelas scenarios + agent_chunks
pytest tests/test_memory_dual.py -v

# Validações esperadas:
# ✅ save_scenario() adiciona registro na tabela scenarios
# ✅ save_chunk() adiciona registro na tabela agent_chunks
# ✅ search() retorna lista vazia quando não há dados
# ✅ search() combina resultados de ambas as tabelas
# ✅ Reranker é chamado para ordenar resultados
# ✅ Campo 'vector' é removido dos resultados
# ✅ count() retorna soma de ambas as tabelas
# ✅ embed_passage() usado para indexação
# ✅ embed_query() usado para busca
# ✅ save_case() ignora cenários com score < 0.3
# ✅ Cenários arquivados não aparecem em buscas
```

#### Testes de Integração
```bash
# Validar que 384d foi completamente removido
grep -r "384" gedai/ --include="*.py"
# Esperado: NENHUM resultado

grep -r "all-MiniLM" gedai/ --include="*.py"
# Esperado: NENHUM resultado
```

#### Critérios de Aceitação Sprint A
- [ ] Todos os testes unitários PASS (15+ testes)
- [ ] Nenhuma referência a 384d ou all-MiniLM no código
- [ ] Tabelas LanceDB criadas com schema correto (768d)
- [ ] Busca dual retorna resultados rerankeados

---

### **Sprint B: Engine Layer (Plano B)**
**Objetivo:** Validar parsing, markdown, contexto, guardrails e validação

#### Testes Unitários
```bash
# 1. CommandParser - parsing de comandos
pytest tests/test_command_parser.py -v

# Validações esperadas:
# ✅ parse() extrai comando e args corretamente
# ✅ Suporta aspas duplas e simples
# ✅ Comando sem args funciona
# ✅ Múltiplos args são capturados
# ✅ Comando desconhecido levanta ValueError
# ✅ String vazia levanta ValueError
# ✅ Whitespace é removido
# ✅ ParsedCommand é dataclass com command, args, raw
```

```bash
# 2. MarkdownEngine - carregamento dinâmico
pytest tests/test_markdown_engine.py -v

# Validações esperadas:
# ✅ load() retorna arquivos relevantes para o comando
# ✅ Seções são separadas por "==="
# ✅ Arquivo faltando não causa exceção
# ✅ Comando desconhecido retorna arquivos base
# ✅ Retorna string não-vazia
```

```bash
# 3. ContextBuilder - montagem de prompt
pytest tests/test_context_builder.py -v

# Validações esperadas:
# ✅ assemble() retorna string
# ✅ Objetivo está incluído no contexto
# ✅ Resultados RAG estão incluídos
# ✅ Markdown está incluído
# ✅ check_rag_confidence() retorna 0.0 para lista vazia
# ✅ check_rag_confidence() calcula média corretamente
# ✅ Confidence >= 0.75 indica skip gemma:2b
# ✅ Chunks de agent_output aparecem no contexto
# ✅ Comando está incluído
```

```bash
# 4. Guardrails - RBAC + retry + timeout
pytest tests/test_guardrails.py -v

# Validações esperadas:
# ✅ GuardrailsState inicia com retry_count=0
# ✅ increment_retry() incrementa contador
# ✅ retry_exceeded() retorna True após RETRY_MAX
# ✅ check_confidence() retorna "pending" se < CONFIDENCE_MIN
# ✅ check_confidence() retorna "ok" se >= CONFIDENCE_MIN
# ✅ Loop detection: 3 ações idênticas → loop_detected=True
# ✅ parse_security_md() extrai allowed_agent_types
# ✅ parse_security_md() extrai denied_task_patterns
# ✅ Arquivo faltando retorna política permissiva
# ✅ check_rbac_pre() bloqueia agent_type não permitido
# ✅ check_rbac_pre() permite agent_type permitido
# ✅ check_rbac_pre() bloqueia padrão negado na task
# ✅ Sem soul_path permite tudo
# ✅ check_rbac_post() bloqueia output com padrão negado
# ✅ check_rbac_post() permite output limpo
```

```bash
# 5. ScenarioValidator - 17 critérios
pytest tests/test_scenario_validator.py -v

# Validações esperadas:
# ✅ Cenário completo retorna score >= 15
# ✅ Cenário incompleto retorna score < 12
# ✅ Retorna 17 critérios
# ✅ passed=True quando score >= 15
# ✅ passed=False quando score < 15
# ✅ Critérios têm name e passed
# ✅ Detecta objetivo
# ✅ Detecta output JSON
```

#### Critérios de Aceitação Sprint B
- [ ] Todos os testes unitários PASS (30+ testes)
- [ ] RBAC enforçado em Python (não via prompt)
- [ ] Guardrails detectam loop, timeout e retry
- [ ] Validator identifica 17 critérios estruturais

---

### **Sprint C: Core + Commands + CLI (Plano C)**
**Objetivo:** Validar runtime, router, comandos e orchestrator completo

#### Testes Unitários
```bash
# 1. StateMachine - ciclo de vida de agentes
pytest tests/test_state_machine.py -v

# Validações esperadas:
# ✅ Estado inicial é INITIAL
# ✅ start() transiciona para RUNNING
# ✅ pause() de RUNNING vai para PAUSED
# ✅ stop() de RUNNING vai para STOPPED
# ✅ restart() de PAUSED volta para RUNNING
# ✅ reinforce() adiciona instrução
# ✅ alter() só funciona de PAUSED ou INITIAL
# ✅ alter() atualiza current_task
# ✅ get_state() retorna snapshot completo
# ✅ pause() de INITIAL levanta erro
```

```bash
# 2. AgentManager - execução com RBAC
pytest tests/test_agent_manager.py -v

# Validações esperadas:
# ✅ execute_all() retorna lista de resultados
# ✅ Resultado tem campos: agent, success, output, error
# ✅ Agente falhado é capturado
# ✅ RBAC pré-dispatch bloqueia agent_type não permitido
# ✅ Output do agente 1 é passado ao agente 2 (context passing)
# ✅ save_chunk() é chamado para cada agente
# ✅ Métricas são gravadas por agente
```

```bash
# 3. Router - delegation chain
pytest tests/test_router.py -v

# Validações esperadas:
# ✅ dispatch("gemma:2b") usa Ollama
# ✅ dispatch("claude-code") usa CLI
# ✅ dispatch_delegated() tenta chain em ordem
# ✅ Fallback para gemma:2b se toda chain falhar
# ✅ Agent_type desconhecido retorna erro
```

```bash
# 4. Commands - todos os comandos
pytest tests/test_commands.py -v

# Validações esperadas:
# ✅ /format retorna JSON canônico
# ✅ /format com router falhado retorna status=failed
# ✅ /plan retorna JSON canônico
# ✅ /simulate retorna risks em data
# ✅ /debug retorna JSON canônico
# ✅ /optimize retorna JSON canônico
```

```bash
# 5. Animate - criação de subagentes
pytest tests/test_animate.py -v

# Validações esperadas:
# ✅ Cria diretório com 7 arquivos
# ✅ Arquivos têm conteúdo não-vazio
# ✅ Retorna path string
```

```bash
# 6. Clone - replicação de estrutura
pytest tests/test_clone.py -v

# Validações esperadas:
# ✅ clone_agent() cria destino
# ✅ Substitui nome nos arquivos
# ✅ Origem não encontrada levanta FileNotFoundError
# ✅ Retorna path do destino
```

```bash
# 7. Orchestrator - pipeline /start completo
pytest tests/test_orchestrator.py -v

# Validações esperadas:
# ✅ run() retorna dict canônico
# ✅ Status é completed/partial/failed
# ✅ Salva no RAG quando validação passa
# ✅ RAG-first skip gemma:2b quando confidence >= 0.75
# ✅ Inclui execution_id em data
# ✅ Usa ExecutorFactory.for_mode
# ✅ Passa execution_mode para factory
# ✅ Delega para pipeline steps
# ✅ _build_result() retorna dict completo
```

#### Testes de Integração
```bash
# Testar CLI end-to-end (requer Ollama rodando)
python -m gedai.cli.main status
# Esperado: Tabela com status de componentes

python -m gedai.cli.main memory "criar API"
# Esperado: Resultados da busca RAG ou "Nenhum resultado"
```

#### Critérios de Aceitação Sprint C
- [ ] Todos os testes unitários PASS (60+ testes)
- [ ] StateMachine gerencia estados corretamente
- [ ] Router delegation chain funciona
- [ ] Orchestrator executa 10 passos do /start
- [ ] CLI expõe todos os comandos

---

### **Sprint D: Telemetria (Plano D)**
**Objetivo:** Validar sistema de métricas ExecutionMetrics

#### Testes Unitários
```bash
pytest tests/test_metrics.py -v

# Validações esperadas:
# ✅ record() armazena entrada na tabela
# ✅ get_by_execution() retorna todos os agentes de uma execução
# ✅ get_by_execution() vazio para execution_id desconhecido
# ✅ aggregate() retorna summary com métricas
# ✅ aggregate() calcula success_rate corretamente
# ✅ aggregate() calcula rag_hit_rate
# ✅ aggregate() vazio retorna zeros
# ✅ get_recent() retorna últimos N registros
# ✅ delegation_rate calculado por tipo
```

#### Testes de Integração
```bash
# Validar que AgentManager grava métricas
pytest tests/test_agent_manager.py::test_agent_manager_records_metrics_on_success -v
pytest tests/test_agent_manager.py::test_agent_manager_records_metrics_on_failure -v

# Validações esperadas:
# ✅ Métricas gravadas em sucesso
# ✅ Métricas gravadas em falha
# ✅ execution_id correto
# ✅ agent_name correto
```

#### Critérios de Aceitação Sprint D
- [ ] Todos os testes PASS (10+ testes)
- [ ] Tabela execution_metrics criada no LanceDB
- [ ] AgentManager grava métricas por agente
- [ ] aggregate() fornece dados para Planner

---

### **Sprint E: Planner + Clarifier (Plano E)**
**Objetivo:** Validar decisões estratégicas e coleta de informações

#### Testes Unitários
```bash
# 1. Clarifier - detecção de ambiguidade
pytest tests/test_clarifier.py -v

# Validações esperadas:
# ✅ Detecta objetivo vago
# ✅ Não faz perguntas para objetivo detalhado
# ✅ Pergunta quando não há RAG results
# ✅ Máximo 5 perguntas
# ✅ Modo auto usa defaults
# ✅ collect() interativo funciona
# ✅ Input vazio usa default
# ✅ enrich_objective() adiciona contexto
```

```bash
# 2. Planner - decisões baseadas em dados
pytest tests/test_planner.py -v

# Validações esperadas:
# ✅ RAG-first quando confidence >= 0.75
# ✅ Não usa RAG-first quando confidence baixa
# ✅ Não usa RAG-first quando lista vazia
# ✅ select_mode() retorna "sequential" por padrão
# ✅ select_mode() retorna "rag_only" quando hit_rate >= 0.85
# ✅ select_mode() retorna "delegated" para /enhance
# ✅ should_delegate() True para /enhance
# ✅ should_delegate() False para /start com RAG
# ✅ decide() retorna dict com todas as chaves
# ✅ Usa metrics.aggregate()
# ✅ reason não-vazio
```

#### Testes de Integração
```bash
# Validar integração com Orchestrator
pytest tests/test_orchestrator.py::test_orchestrator_uses_planner_for_rag_first -v
pytest tests/test_orchestrator.py::test_orchestrator_clarifier_enriches_objective_in_auto_mode -v
```

#### Critérios de Aceitação Sprint E
- [ ] Todos os testes PASS (20+ testes)
- [ ] Clarifier detecta ambiguidade corretamente
- [ ] Planner usa telemetria quando disponível
- [ ] Orchestrator integra ambos no pipeline

---

### **Sprint F: Auditor + Schema (Plano F)**
**Objetivo:** Validar governança de output e schema formal

#### Testes Unitários
```bash
# 1. Schema - validação pydantic
pytest tests/test_schema.py -v

# Validações esperadas:
# ✅ CanonicalOutput válido aceito
# ✅ Status inválido levanta ValidationError
# ✅ Confidence > 1.0 levanta ValidationError
# ✅ Confidence < 0.0 levanta ValidationError
# ✅ parse_canonical_output() válido retorna objeto
# ✅ parse_canonical_output() inválido retorna None
# ✅ Campo faltando retorna None
# ✅ model_dump() retorna dict
```

```bash
# 2. Auditor - coerência operacional
pytest tests/test_auditor.py -v

# Validações esperadas:
# ✅ Resultados consistentes passam
# ✅ Todos os agentes falhados não passa
# ✅ Detecta divergência de confidence
# ✅ Sinaliza alta taxa de falha
# ✅ Recomenda retry quando recuperável
# ✅ Score entre 0.0 e 1.0
# ✅ Avisa sobre validation_score baixo
# ✅ Sem warnings para alta qualidade
```

#### Testes de Integração
```bash
# Validar integração com Orchestrator
pytest tests/test_orchestrator.py::test_orchestrator_includes_audit_result_in_output -v
pytest tests/test_orchestrator.py::test_orchestrator_audit_recommendation_in_output -v

# Validar schema no AgentManager
pytest tests/test_agent_manager.py::test_agent_manager_flags_invalid_schema_in_result -v
pytest tests/test_agent_manager.py::test_agent_manager_schema_valid_true_for_canonical_output -v
```

#### Critérios de Aceitação Sprint F
- [ ] Todos os testes PASS (18+ testes)
- [ ] Schema pydantic valida outputs
- [ ] Auditor avalia 4 critérios operacionais
- [ ] Orchestrator só salva no RAG se audit aceitar

---

## 🚀 Execução Completa da Suite

### Rodar Todos os Testes
```bash
# Suite completa
pytest tests/ -v --tb=short

# Com cobertura
pytest tests/ --cov=gedai --cov-report=html

# Apenas testes rápidos (sem integração)
pytest tests/ -v -m "not integration"

# Apenas testes de integração
pytest tests/ -v -m integration
```

### Métricas Esperadas
```
Total de testes: 130+
Tempo de execução: < 30 segundos
Cobertura de código: >= 85%
Falhas: 0
```

---

## 📊 Checklist de Validação Final

### Funcionalidade
- [ ] Todos os comandos (/format, /plan, /start, etc) funcionam
- [ ] Pipeline TAO (Think-Act-Observe) completo
- [ ] Multi-agent orchestration operacional
- [ ] RAG memory dual-granularity persistente
- [ ] Testes end-to-end passam

### Segurança
- [ ] RBAC implementado em Python (não via prompt)
- [ ] Guardrails anti-hallucination ativos
- [ ] Validação de regex patterns (sem ReDoS)
- [ ] Logs não vazam PII

### Performance
- [ ] Lazy loading de dependências pesadas funciona
- [ ] Parallel execution para agentes independentes
- [ ] Busca RAG retorna em < 500ms (com 1000 cenários)
- [ ] Embeddings são gerados corretamente (768d)

### Manutenibilidade
- [ ] Documentação inline completa
- [ ] Type hints em todos os módulos
- [ ] Testes unitários abrangentes
- [ ] Padrões de código consistentes

---

## 🐛 Reportando Bugs

Quando encontrar um bug, documente:

### Template de Bug Report
```markdown
## 🐛 Bug: [Título curto]

**Severidade:** 🔴 Crítico / 🟡 Médio / 🟢 Baixo

**Localização:** `gedai/module/file.py:linha`

**Descrição:**
[O que aconteceu]

**Reprodução:**
```bash
pytest tests/test_file.py::test_name -v
```

**Comportamento Esperado:**
[O que deveria acontecer]

**Comportamento Atual:**
[O que está acontecendo]

**Logs/Output:**
```
[Cole o output do teste]
```

**Impacto:**
[Quais funcionalidades são afetadas]

**Sugestão de Fix:**
[Se tiver, sugira uma correção]
```

---

## 📈 Relatório de Execução

Ao final dos testes, gere um relatório:

### Template de Relatório
```markdown
# 📊 Relatório de Testes - gedAI Sprint [X]

**Data:** YYYY-MM-DD
**Executor:** [Seu nome]
**Ambiente:** Python 3.11 / Ollama [versão]

## Resumo Executivo
- Total de testes: XXX
- Passou: XXX
- Falhou: XXX
- Pulados: XXX
- Cobertura: XX%
- Tempo: XXs

## Testes por Sprint

### Sprint A: Foundation
- ✅ test_embedder.py: 5/5 PASS
- ✅ test_reranker.py: 5/5 PASS
- ✅ test_memory_dual.py: 11/11 PASS

### Sprint B: Engine
- ✅ test_command_parser.py: 9/9 PASS
- ✅ test_markdown_engine.py: 6/6 PASS
- ✅ test_context_builder.py: 9/9 PASS
- ✅ test_guardrails.py: 15/15 PASS
- ✅ test_scenario_validator.py: 8/8 PASS

[... continuar para todas as sprints ...]

## Bugs Encontrados
[Lista de bugs com severidade]

## Recomendações
[Sugestões de melhorias]

## Conclusão
[Status geral: APROVADO / APROVADO COM RESSALVAS / REPROVADO]
```

---

## 🎯 Próximos Passos

Após completar todos os testes:

1. **Gerar relatório completo** usando o template acima
2. **Documentar todos os bugs** encontrados
3. **Validar fixes** após correções
4. **Executar testes de regressão** completos
5. **Aprovar para produção** se todos os critérios forem atendidos

---

## 📞 Suporte

Se encontrar dificuldades:

1. Consulte a documentação em `markdown/`
2. Revise os planos de sprint em `docs/superpowers/plans/`
3. Verifique o QA Report em `.amazonq/rules/QA.md`
4. Execute testes individuais com `-vv` para mais detalhes

---

**Boa sorte com os testes! 🚀**
