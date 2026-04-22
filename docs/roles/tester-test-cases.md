# 🎯 Matriz de Casos de Teste - gedAI Test Cases

## 📋 Organização

Este documento complementa o `TESTER_PROMPT.md` com casos de teste específicos organizados por:
- **Prioridade** (P0 = Crítico, P1 = Alto, P2 = Médio, P3 = Baixo)
- **Sprint** (A até L)
- **Tipo** (Unitário, Integração, E2E, Performance, Segurança)

---

## 🔴 P0 - Casos de Teste Críticos (Bloqueadores)

### TC-001: Pipeline /start Completo
**Sprint:** C  
**Tipo:** Integração  
**Pré-condição:** Ollama rodando com modelo gedai registrado

```bash
# Comando
python -m gedai.cli.main start "criar API REST em Python com autenticação JWT"

# Validações
✅ Status: completed ou partial
✅ Retorna JSON canônico com: status, data, confidence, next_action
✅ execution_id presente em data
✅ team com pelo menos 1 agente
✅ results com outputs por agente
✅ Cenário salvo no RAG se score >= 12
✅ Tempo de execução < 60s
```

**Critério de Falha:** Se não retornar JSON canônico ou crashar

---

### TC-002: RBAC Pré-Dispatch Bloqueia Agent Type Não Permitido
**Sprint:** B  
**Tipo:** Segurança  
**Pré-condição:** Subagente com 00-security.md restritivo

```python
# Setup
security_md = """
## Allowed Agent Types
- gemma:2b

## Denied Task Patterns
- DROP TABLE
"""

agent = Agent(
    name="dev", role="dev", agent_type="claude-code",  # ❌ Não permitido
    task="implementar API", soul_path="path/to/00-security.md"
)

# Execução
result = check_rbac_pre(agent, "implementar API")

# Validações
✅ result.allowed == False
✅ "claude-code" in result.reason
✅ AgentManager não despacha o agente
```

**Critério de Falha:** Se agente não permitido for executado

---

### TC-003: Memory Dual-Granularity Salva e Busca
**Sprint:** A  
**Tipo:** Integração  
**Pré-condição:** LanceDB limpo

```python
# Setup
memory = Memory()
execution_id = memory.new_execution_id()

# Salvar cenário
memory.save_scenario(
    execution_id=execution_id,
    objective="criar API REST",
    command="/start",
    team_json='[{"name":"dev","agent_type":"gemma:2b"}]',
    output_json='{"status":"completed"}',
    score=0.85,
    validation_score=16,
    tags="api"
)

# Salvar chunk
memory.save_chunk(
    execution_id=execution_id,
    agent_name="dev",
    agent_type="gemma:2b",
    role="desenvolvedor",
    task="implementar",
    agent_output="API criada com FastAPI",
    confidence=0.9,
    success=True
)

# Buscar
results = memory.search("criar API REST", k=5)

# Validações
✅ len(results) >= 1
✅ results[0]["objective"] == "criar API REST"
✅ results[0]["score"] >= 0.8
✅ "vector" not in results[0]  # Campo removido
✅ Reranker foi chamado
```

**Critério de Falha:** Se busca não retornar o cenário salvo

---

### TC-004: Guardrails Loop Detection
**Sprint:** B  
**Tipo:** Segurança  
**Pré-condição:** GuardrailsState inicializado

```python
state = GuardrailsState()

# Simular 3 ações idênticas
state.record_action("build_team")
state.record_action("build_team")
state.record_action("build_team")

# Validações
✅ state.loop_detected == True
✅ Orchestrator deve abortar execução
✅ Log de erro gerado
```

**Critério de Falha:** Se loop não for detectado

---

### TC-005: Router Delegation Chain Fallback
**Sprint:** C  
**Tipo:** Integração  
**Pré-condição:** Apenas gemma:2b disponível (CLIs externas offline)

```python
router = Router(ollama=OllamaClient(), cli_runner=CLIRunner())

# Todas as CLIs falham, gemma:2b deve ser usado
result = router.dispatch_delegated("tarefa complexa")

# Validações
✅ result.success == True
✅ result.agent_type == "gemma:2b"
✅ Tentou claude-code, codex, gemini, kimi antes
✅ Log mostra tentativas falhadas
```

**Critério de Falha:** Se não usar gemma:2b como fallback

---

## 🟡 P1 - Casos de Teste de Alta Prioridade

### TC-006: Planner RAG-First Decision
**Sprint:** E  
**Tipo:** Unitário

```python
planner = Planner(metrics=ExecutionMetrics())

# Cenário 1: Alta confiança → RAG-first
rag_results = [{"score": 0.9, "team_json": "[]"}]
assert planner.should_use_rag_first("criar API", rag_results, 0.85) == True

# Cenário 2: Baixa confiança → Não usar RAG-first
assert planner.should_use_rag_first("criar API", [], 0.4) == False

# Cenário 3: Lista vazia → Não usar RAG-first
assert planner.should_use_rag_first("criar API", [], 0.9) == False
```

---

### TC-007: Clarifier Detecta Objetivo Vago
**Sprint:** E  
**Tipo:** Unitário

```python
clarifier = Clarifier(auto_mode=False)

# Objetivo vago
result = clarifier.assess("melhorar", rag_results=[], rag_confidence=0.0)

# Validações
✅ result is not None
✅ len(result.questions) >= 1
✅ len(result.questions) <= 5
✅ "vago" in result.reason.lower() or "curto" in result.reason.lower()
```

---

### TC-008: Auditor Detecta Divergência de Confidence
**Sprint:** F  
**Tipo:** Unitário

```python
auditor = Auditor()

results = [
    {"agent": "ag1", "success": True, "output": '{"confidence": 0.9}'},
    {"agent": "ag2", "success": True, "output": '{"confidence": 0.1}'}
]

audit = auditor.evaluate("criar API", results, validation_score=14)

# Validações
✅ any("divergência" in w.lower() for w in audit.warnings)
✅ audit.score < 1.0
```

---

### TC-009: ExecutionMetrics Aggregate
**Sprint:** D  
**Tipo:** Unitário

```python
metrics = ExecutionMetrics()

# Gravar 3 execuções
for success, duration in [(True, 1000), (False, 2000), (True, 800)]:
    metrics.record(
        execution_id="exec_001",
        command="/start",
        agent_name="ag",
        agent_type="gemma:2b",
        success=success,
        duration_ms=duration,
        retry_count=0,
        used_rag=False,
        used_delegation=False,
        delegation_elo="gemma:2b",
        confidence=0.7,
        validation_score=13
    )

agg = metrics.aggregate(command="/start")

# Validações
✅ agg["total_executions"] == 3
✅ agg["success_rate"] == pytest.approx(2/3)
✅ agg["avg_duration_ms"] == pytest.approx(1266.67, abs=1)
```

---

### TC-010: Schema Validation com Pydantic
**Sprint:** F  
**Tipo:** Unitário

```python
from gedai.engine.schema import CanonicalOutput, parse_canonical_output

# Válido
out = CanonicalOutput(
    status="completed",
    data={"result": "ok"},
    confidence=0.85,
    next_action=None
)
assert out.status == "completed"

# Inválido - status
with pytest.raises(ValidationError):
    CanonicalOutput(status="unknown", data={}, confidence=0.5, next_action=None)

# Inválido - confidence > 1.0
with pytest.raises(ValidationError):
    CanonicalOutput(status="completed", data={}, confidence=1.5, next_action=None)

# Parse de string
raw = '{"status":"completed","data":{},"confidence":0.9,"next_action":null}'
parsed = parse_canonical_output(raw)
assert parsed is not None
assert parsed.confidence == 0.9
```

---

## 🟢 P2 - Casos de Teste de Média Prioridade

### TC-011: CommandParser Extrai Args Corretamente
**Sprint:** B  
**Tipo:** Unitário

```python
parser = CommandParser()

# Com aspas
result = parser.parse('/start "criar API REST com JWT"')
assert result.command == "/start"
assert "criar API REST" in result.args

# Sem aspas
result = parser.parse("/plan criar pipeline de dados")
assert result.command == "/plan"
assert result.args == "criar pipeline de dados"

# Sem args
result = parser.parse("/state")
assert result.command == "/state"
assert result.args == ""
```

---

### TC-012: MarkdownEngine Carrega Arquivos Relevantes
**Sprint:** B  
**Tipo:** Unitário

```python
engine = MarkdownEngine(markdown_dir="./markdown")

content = engine.load("/start")

# Validações
✅ "Guardrails" in content
✅ "LLM" in content or "llm" in content
✅ "===" in content  # Separador de seções
✅ len(content) > 100
```

---

### TC-013: Embedder Adiciona Prefixos Corretos
**Sprint:** A  
**Tipo:** Unitário

```python
embedder = Embedder()

# Query
query_vec = embedder.embed_query("criar API REST")
assert len(query_vec) == 768
# Internamente deve ter adicionado "query: "

# Passage
passage_vec = embedder.embed_passage("FastAPI com JWT")
assert len(passage_vec) == 768
# Internamente deve ter adicionado "passage: "

# Não duplica prefixo
query_vec2 = embedder.embed_query("query: criar API REST")
assert len(query_vec2) == 768
```

---

### TC-014: Reranker Ordena por Relevância
**Sprint:** A  
**Tipo:** Unitário

```python
reranker = Reranker()

docs = ["documento irrelevante", "documento muito relevante", "documento médio"]
result = reranker.rerank("criar API", docs, top_n=3)

# Validações
✅ len(result) == 3
✅ result[0][1] > result[1][1]  # Score decrescente
✅ result[1][1] > result[2][1]
✅ all(isinstance(idx, int) and isinstance(score, float) for idx, score in result)
```

---

### TC-015: StateMachine Transições de Estado
**Sprint:** C  
**Tipo:** Unitário

```python
sm = StateMachine()

# INITIAL → RUNNING
sm.start()
assert sm.state == AgentState.RUNNING

# RUNNING → PAUSED
sm.pause()
assert sm.state == AgentState.PAUSED

# PAUSED → RUNNING
sm.restart()
assert sm.state == AgentState.RUNNING

# RUNNING → STOPPED
sm.stop()
assert sm.state == AgentState.STOPPED
```

---

## ⚪ P3 - Casos de Teste de Baixa Prioridade

### TC-016: Animate Cria 7 Arquivos
**Sprint:** C  
**Tipo:** Integração

```python
animator = Animate(router=Router(...), subagents_dir="./subagentes")

path = animator.run("dev_backend", "desenvolvedor backend", "claude-code")

# Validações
✅ Path(path).exists()
✅ len(list(Path(path).iterdir())) == 7
✅ "00-security.md" in [f.name for f in Path(path).iterdir()]
✅ "06-lessons.md" in [f.name for f in Path(path).iterdir()]
✅ All files have content (not empty)
```

---

### TC-017: Clone Substitui Referências ao Nome
**Sprint:** C  
**Tipo:** Integração

```python
clone_cmd = CloneCommand(subagents_dir="./subagentes")

# Criar origem
# ... (setup)

# Clonar
dest_path = clone_cmd.clone_agent("dev_backend", "dev_frontend")

# Validações
✅ Path(dest_path).exists()
✅ "dev_frontend" in Path(dest_path / "01-soul.md").read_text()
✅ "dev_backend" not in Path(dest_path / "01-soul.md").read_text()
```

---

### TC-018: ContextBuilder Monta Prompt Completo
**Sprint:** B  
**Tipo:** Unitário

```python
builder = ContextBuilder()

rag_results = [{"objective": "criar API", "score": 0.9}]
markdown = "# Guardrails\nRetry: 3"

result = builder.assemble(
    objective="criar API GraphQL",
    command="/start",
    rag_results=rag_results,
    markdown_content=markdown
)

# Validações
✅ "criar API GraphQL" in result
✅ "criar API" in result  # RAG result
✅ "Guardrails" in result
✅ "/start" in result
```

---

## 🚀 Casos de Teste de Performance

### TC-P001: Busca RAG com 1000 Cenários
**Sprint:** A  
**Tipo:** Performance  
**Objetivo:** < 500ms

```python
import time

memory = Memory()

# Popular com 1000 cenários
for i in range(1000):
    memory.save_scenario(
        execution_id=f"exec_{i:04d}",
        objective=f"criar sistema {i}",
        command="/start",
        team_json="[]",
        output_json="{}",
        score=0.7,
        validation_score=14,
        tags="test"
    )

# Medir busca
start = time.perf_counter()
results = memory.search("criar API REST", k=10)
duration_ms = (time.perf_counter() - start) * 1000

# Validações
✅ duration_ms < 500
✅ len(results) <= 10
```

---

### TC-P002: Orchestrator Pipeline Completo
**Sprint:** C  
**Tipo:** Performance  
**Objetivo:** < 60s

```python
import time

gedai = GedAI()

start = time.perf_counter()
result = gedai.run("/start criar API REST em Python")
duration_s = time.perf_counter() - start

# Validações
✅ duration_s < 60
✅ result["status"] in ("completed", "partial")
```

---

### TC-P003: Parallel Executor com 5 Agentes
**Sprint:** C  
**Tipo:** Performance  
**Objetivo:** < 10s

```python
import time

executor = ParallelExecutor(router=Router(...))
agents = [Agent(f"ag{i}", "dev", "gemma:2b", "task", i) for i in range(5)]

start = time.perf_counter()
results = executor.run(agents)
duration_s = time.perf_counter() - start

# Validações
✅ duration_s < 10
✅ len(results) == 5
✅ All agents executed (not sequential)
```

---

## 🔒 Casos de Teste de Segurança

### TC-S001: RBAC Post-Output Bloqueia Senha
**Sprint:** B  
**Tipo:** Segurança

```python
security_md = """
## Output Denied Patterns
- senha
- password
- api_key
"""

agent = Agent("dev", "dev", "claude-code", "task", soul_path="path/to/security.md")

# Output com senha
result = check_rbac_post(agent, "a senha do banco é abc123")

# Validações
✅ result.allowed == False
✅ "senha" in result.reason.lower()
```

---

### TC-S002: Regex Injection Protection
**Sprint:** B  
**Tipo:** Segurança

```python
# Padrão regex malicioso (ReDoS)
malicious_pattern = "(a+)+"

security_md = f"""
## Denied Task Patterns
- {malicious_pattern}
"""

# Deve validar padrão antes de usar
policy = parse_security_md("path/to/security.md")

# Validações
✅ Não trava (timeout protection)
✅ Log de warning gerado
✅ Padrão inválido ignorado
```

---

### TC-S003: Sanitização de Logs (PII)
**Sprint:** QA Report  
**Tipo:** Segurança

```python
# Simular log com PII
log_text = "Usuário test@example.com com CPF 123.456.789-00"

sanitized = _sanitize_for_log(log_text)

# Validações
✅ "<EMAIL>" in sanitized
✅ "<CPF>" in sanitized
✅ "test@example.com" not in sanitized
✅ "123.456.789-00" not in sanitized
```

---

## 📊 Matriz de Rastreabilidade

| Test Case | Sprint | Prioridade | Tipo | Status | Bug ID |
|-----------|--------|------------|------|--------|--------|
| TC-001 | C | P0 | Integração | ⏳ Pending | - |
| TC-002 | B | P0 | Segurança | ⏳ Pending | - |
| TC-003 | A | P0 | Integração | ⏳ Pending | - |
| TC-004 | B | P0 | Segurança | ⏳ Pending | - |
| TC-005 | C | P0 | Integração | ⏳ Pending | - |
| TC-006 | E | P1 | Unitário | ⏳ Pending | - |
| TC-007 | E | P1 | Unitário | ⏳ Pending | - |
| TC-008 | F | P1 | Unitário | ⏳ Pending | - |
| TC-009 | D | P1 | Unitário | ⏳ Pending | - |
| TC-010 | F | P1 | Unitário | ⏳ Pending | - |
| TC-011 | B | P2 | Unitário | ⏳ Pending | - |
| TC-012 | B | P2 | Unitário | ⏳ Pending | - |
| TC-013 | A | P2 | Unitário | ⏳ Pending | - |
| TC-014 | A | P2 | Unitário | ⏳ Pending | - |
| TC-015 | C | P2 | Unitário | ⏳ Pending | - |
| TC-016 | C | P3 | Integração | ⏳ Pending | - |
| TC-017 | C | P3 | Integração | ⏳ Pending | - |
| TC-018 | B | P3 | Unitário | ⏳ Pending | - |
| TC-P001 | A | P1 | Performance | ⏳ Pending | - |
| TC-P002 | C | P1 | Performance | ⏳ Pending | - |
| TC-P003 | C | P2 | Performance | ⏳ Pending | - |
| TC-S001 | B | P0 | Segurança | ⏳ Pending | - |
| TC-S002 | B | P1 | Segurança | ⏳ Pending | - |
| TC-S003 | QA | P1 | Segurança | ⏳ Pending | - |

**Legenda:**
- ⏳ Pending - Aguardando execução
- ✅ Pass - Teste passou
- ❌ Fail - Teste falhou
- ⚠️ Blocked - Bloqueado por dependência
- 🔄 Retest - Aguardando reteste após fix

---

## 🎯 Ordem de Execução Recomendada

### Fase 1: Smoke Tests (P0)
Execute primeiro os casos críticos para validar que o sistema básico funciona:
1. TC-003 (Memory)
2. TC-002 (RBAC)
3. TC-004 (Guardrails)
4. TC-005 (Router)
5. TC-001 (Pipeline completo)

### Fase 2: Testes Unitários (P1 + P2)
Execute todos os testes unitários por sprint:
- Sprint A: TC-013, TC-014
- Sprint B: TC-011, TC-012
- Sprint C: TC-015
- Sprint D: TC-009
- Sprint E: TC-006, TC-007
- Sprint F: TC-008, TC-010

### Fase 3: Testes de Integração (P1 + P2 + P3)
Execute testes que dependem de múltiplos componentes:
- TC-016, TC-017, TC-018

### Fase 4: Testes de Performance (P1 + P2)
Execute testes de carga e latência:
- TC-P001, TC-P002, TC-P003

### Fase 5: Testes de Segurança (P0 + P1)
Execute validações de segurança:
- TC-S001, TC-S002, TC-S003

---

## 📝 Notas de Execução

### Ambiente Necessário
- Python 3.11+
- Ollama rodando (para testes de integração)
- LanceDB limpo (para testes de performance)
- 4GB RAM disponível

### Dados de Teste
- Cenários de teste em `tests/fixtures/`
- Subagentes mock em `tests/fixtures/subagentes/`
- Security policies em `tests/fixtures/security/`

### Limpeza Entre Testes
```bash
# Limpar banco RAG
rm -rf ./gedai_db/lancedb/*

# Limpar subagentes de teste
rm -rf ./subagentes/test_*

# Resetar métricas
# (executar antes de testes de telemetria)
```

---

**Última atualização:** 2024-01-XX  
**Versão:** 1.0  
**Responsável:** QA Team
