# 🧪 gedAI Quality Assurance - Documentação Completa

## 📚 Índice de Documentos

Este diretório contém toda a documentação de QA do projeto gedAI-brain:

### 1. 📋 [TESTER_PROMPT.md](./TESTER_PROMPT.md)
**Prompt completo para execução do plano de testes**

Documento principal para QA Engineers executarem o plano de testes completo.

**Conteúdo:**
- Contexto do projeto e objetivos de QA
- Pré-requisitos e setup do ambiente
- Plano de testes detalhado por sprint (A até F)
- Checklist de validação final
- Template de bug report
- Template de relatório de execução

**Quando usar:** Início de qualquer ciclo de testes

---

### 2. 🎯 [TEST_CASES.md](./TEST_CASES.md)
**Matriz de casos de teste priorizados**

Casos de teste específicos organizados por prioridade e tipo.

**Conteúdo:**
- **P0 (Críticos):** 5 casos bloqueadores
- **P1 (Alta):** 5 casos de alta prioridade
- **P2 (Média):** 8 casos de média prioridade
- **P3 (Baixa):** 3 casos de baixa prioridade
- **Performance:** 3 casos de carga/latência
- **Segurança:** 3 casos de validação de segurança
- Matriz de rastreabilidade
- Ordem de execução recomendada

**Quando usar:** Para executar testes específicos ou validar correções

---

### 3. 🤖 [run_tests.py](../run_tests.py)
**Script de automação de testes**

Script Python para execução automatizada com relatórios.

**Uso:**
```bash
# Todos os testes
python run_tests.py --all

# Por sprint
python run_tests.py --sprint A

# Por prioridade
python run_tests.py --priority P0

# Com relatório HTML
python run_tests.py --all --report html
```

**Quando usar:** Para automação de testes em CI/CD ou execução local

---

### 4. 📊 [QA.md](../.amazonq/rules/QA.md)
**Relatório QA completo do projeto**

Análise detalhada de qualidade do código, testes e arquitetura.

**Conteúdo:**
- Executive Summary
- Análise de cobertura de testes
- Code smells identificados
- Vulnerabilidades de segurança
- Gargalos de performance
- Bugs críticos encontrados
- Recomendações priorizadas
- Métricas de qualidade

**Quando usar:** Para entender o estado geral de qualidade do projeto

---

## 🚀 Quick Start para QA

### Passo 1: Setup do Ambiente
```bash
# Clonar repositório
git clone <repo-url>
cd gedAI_agents

# Instalar dependências
pip install -r requirements.txt

# Verificar pytest
pytest --version
```

### Passo 2: Validar Ambiente
```bash
# Rodar smoke tests (P0)
python run_tests.py --priority P0

# Verificar Ollama
ollama list | grep gedai
```

### Passo 3: Executar Suite Completa
```bash
# Todos os testes com relatório HTML
python run_tests.py --all --report html

# Abrir relatório
open test_report.html  # macOS/Linux
start test_report.html # Windows
```

### Passo 4: Analisar Resultados
```bash
# Ver cobertura
pytest tests/ --cov=gedai --cov-report=html
open htmlcov/index.html
```

---

## 📋 Checklist de Execução

### Antes de Iniciar
- [ ] Python 3.11+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Ollama rodando (para testes de integração)
- [ ] LanceDB limpo (para testes de performance)
- [ ] Leu `TESTER_PROMPT.md` completo

### Durante Execução
- [ ] Executar P0 primeiro (smoke tests)
- [ ] Documentar falhas imediatamente
- [ ] Capturar logs de erros
- [ ] Validar cada sprint antes de prosseguir
- [ ] Atualizar matriz de rastreabilidade

### Após Execução
- [ ] Gerar relatório completo
- [ ] Documentar bugs encontrados
- [ ] Calcular métricas de qualidade
- [ ] Criar issues para correções
- [ ] Atualizar documentação de QA

---

## 🐛 Processo de Bug Report

### 1. Identificar Bug
Durante execução dos testes, documente:
- Teste que falhou
- Comportamento esperado vs atual
- Logs e stack trace
- Ambiente (Python version, OS, etc)

### 2. Classificar Severidade
- 🔴 **Crítico:** Bloqueia funcionalidade principal
- 🟡 **Médio:** Impacta funcionalidade secundária
- 🟢 **Baixo:** Cosmético ou edge case

### 3. Criar Issue
Use o template em `TESTER_PROMPT.md`:
```markdown
## 🐛 Bug: [Título]
**Severidade:** 🔴/🟡/🟢
**Localização:** `file.py:linha`
**Reprodução:** `pytest tests/test_x.py::test_y`
**Esperado:** [...]
**Atual:** [...]
**Logs:** [...]
```

### 4. Rastrear Correção
- Adicionar bug ID na matriz de rastreabilidade
- Marcar teste como ⚠️ Blocked
- Após fix, executar retest
- Atualizar status para ✅ Pass

---

## 📊 Métricas de Qualidade

### Metas do Projeto
| Métrica | Meta | Atual | Status |
|---------|------|-------|--------|
| Cobertura de Testes | 90% | ~85% | 🟡 |
| Taxa de Sucesso | 100% | TBD | ⏳ |
| Tempo de Execução | < 30s | TBD | ⏳ |
| Bugs Críticos | 0 | 3 | 🔴 |
| Complexidade Ciclomática | < 10 | 8-12 | 🟡 |

### Como Calcular
```bash
# Cobertura
pytest tests/ --cov=gedai --cov-report=term

# Complexidade
pip install radon
radon cc gedai/ -a

# Duplicação
pip install pylint
pylint gedai/ --disable=all --enable=duplicate-code
```

---

## 🔄 Integração Contínua

### GitHub Actions (Exemplo)
```yaml
name: QA Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python run_tests.py --all --report json
      - uses: actions/upload-artifact@v2
        with:
          name: test-report
          path: test_report.json
```

---

## 📈 Evolução da Qualidade

### Sprint A (Foundation)
- ✅ 15 testes implementados
- ✅ Embedder 768d validado
- ✅ Memory dual-granularity funcional

### Sprint B (Engine)
- ✅ 30 testes implementados
- ✅ RBAC Python-enforced
- ✅ Guardrails ativos

### Sprint C (Core)
- ✅ 60 testes implementados
- ✅ Orchestrator 10 passos
- ✅ CLI completa

### Sprint D (Telemetria)
- ✅ 10 testes implementados
- ✅ ExecutionMetrics funcional

### Sprint E (Planner)
- ✅ 20 testes implementados
- ✅ Clarifier interativo
- ✅ Planner baseado em dados

### Sprint F (Auditor)
- ✅ 18 testes implementados
- ✅ Schema pydantic
- ✅ Auditor 4 critérios

**Total:** 130+ testes | Cobertura: ~85%

---

## 🎯 Próximos Passos

### Curto Prazo (Sprint Atual)
1. Executar suite completa de testes
2. Corrigir bugs P0 identificados
3. Atingir 90% de cobertura
4. Implementar testes E2E faltantes

### Médio Prazo (Próximas 2 Sprints)
1. Adicionar testes de carga (1000+ cenários)
2. Implementar testes de segurança avançados
3. Configurar CI/CD completo
4. Criar dashboard de métricas

### Longo Prazo (Roadmap)
1. Testes de regressão automatizados
2. Performance benchmarking contínuo
3. Testes de penetração
4. Certificação de qualidade

---

## 📞 Contatos e Suporte

### Equipe QA
- **QA Lead:** [Nome]
- **QA Engineers:** [Nomes]
- **Slack:** #gedai-qa
- **Email:** qa@gedai.dev

### Documentação Adicional
- [README.md](../README.md) - Visão geral do projeto
- [markdown/](../markdown/) - Documentação técnica
- [docs/superpowers/plans/](../docs/superpowers/plans/) - Planos de sprint

### Issues e Bugs
- GitHub Issues: [Link]
- Bug Tracker: [Link]
- Wiki: [Link]

---

## 📝 Changelog

### 2024-01-XX - v1.0
- ✅ Criação da documentação completa de QA
- ✅ Implementação do script de automação
- ✅ Definição de 24 casos de teste priorizados
- ✅ Relatório QA inicial completo

---

## 🏆 Critérios de Aprovação

### Para Produção
- [ ] 100% dos testes P0 passando
- [ ] >= 95% dos testes P1 passando
- [ ] Cobertura >= 90%
- [ ] 0 bugs críticos abertos
- [ ] Performance dentro dos SLAs
- [ ] Documentação atualizada
- [ ] Aprovação do QA Lead

### Para Staging
- [ ] >= 90% dos testes P0+P1 passando
- [ ] Cobertura >= 85%
- [ ] Bugs críticos documentados com plano de correção
- [ ] Testes de integração passando

---

**Última atualização:** 2024-01-XX  
**Versão:** 1.0  
**Responsável:** QA Team  
**Status:** 📋 Documentação Completa
