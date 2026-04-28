# Relatório de Débitos Técnicos (Fase 1 e Fase 2) - Checkpoint 2026-04-27

Este documento apresenta o resultado da varredura arquitetural de débitos técnicos (Tech Debt) de todo o repositório, abrangendo as entregas da Fase 1 e Fase 2.

## 🔴 Alta Severidade (HIGH)

### 1. [Backend/Testes] Instabilidade de Conexão no Pytest (Connection Pool Exhaustion)
- **Local:** Suíte de Testes do Backend (`pytest`)
- **Descrição:** A execução de múltiplos arquivos de teste gera erros sistêmicos em cascata do tipo `asyncpg.exceptions.ConnectionDoesNotExistError: connection was closed in the middle of operation`. Isso indica que o ciclo de vida das fixtures do `pytest-asyncio` (`db_session`) não está isolando adequadamente as sessões assíncronas ou está esgotando o pool do SQLAlchemy.
- **Risco:** Bloqueio direto na esteira de CI/CD e falsos negativos ao validar novas features. Os testes rodam isoladamente, mas falham quando executados em batch.

### 2. [Backend/Database] Mitigação Manual de N+1 em vez de Eager Loading (SQLAlchemy)
- **Local:** `cpu_geracao_service.py`, `histograma_service.py`, entre outros.
- **Descrição:** Para evitar N+1 queries, o código atualmente faz buscas flat em batch e mapeia relacionamentos via dicionários na memória do Python (ex: `itens_map = {item.id: item for item in itens}`). O SQLAlchemy 2.0 suporta `joinedload` e `selectinload` nativamente no `select()`, que seria a abordagem arquiteturalmente correta, tipada e otimizada pelo banco.
- **Risco:** Aumento desnecessário da complexidade ciclomática nos Services, código boilerplate e maior consumo de memória RAM do container.

## 🟡 Média Severidade (MEDIUM)

### 3. [Frontend/Tipagem] Uso Explícito de Tipos Bypass (`any` / `Record<string, any>`)
- **Local:** 
  - `shared/services/api/histogramaApi.ts`
  - `features/proposals/components/HistogramaTabMaoObra.tsx`
  - `features/proposals/components/HistogramaTabGenerica.tsx`
- **Descrição:** Nas implementações recentes do Histograma, há uso explícito de payloads genéricos (`Record<string, any>`) para as requisições de mutação/edição. O ideal é que o payload seja fortemente tipado de acordo com o schema de Update DTO.
- **Risco:** Perda das garantias de segurança de tipo em tempo de compilação. Se a API mudar um nome de campo ou o desenvolvedor digitar errado, o erro passará silenciosamente pelo TS Checker e quebrará em runtime.

### 4. [Frontend/UX] TODO Aberto: Exclusão de Proposta
- **Local:** `features/proposals/pages/ProposalDetailPage.tsx` (linha 210)
- **Descrição:** O botão de exclusão de proposta ("Excluir"), visível exclusivamente para usuários `isOwner`, está renderizado na interface mas possui apenas um stub de ação: `onClick={() => { /* TODO: implementar delete */ }}`.
- **Risco:** Quebra de expectativa do usuário e impossibilidade de gerenciar o ciclo de vida completo da proposta no UI.

## 🟢 Baixa Severidade (LOW)

### 5. [Backend/Config] Credenciais Hardcoded na Configuração de Teste
- **Local:** `app/backend/tests/conftest.py`
- **Descrição:** A constante `TEST_DATABASE_URL` está fixa no código como `postgresql+asyncpg://postgres:password@localhost:5432/dinamica_budget_test`.
- **Risco:** Baixo, pois trata-se do banco efêmero de testes locais. Contudo, em pipelines de CI/CD rigorosos, essa string de conexão deve ser recuperada via variáveis de ambiente com fallback (ex: padrão `12-Factor App`).

## Conclusão da Análise
A fundação arquitetural encontra-se sólida, destacando-se a nítida separação entre Routers, Services e Repositories. O ponto **Crítico** que demanda uma **Sprint de Refatoração Imediata** é a correção do isolamento do pool de conexões do `pytest-asyncio` no backend, vital para estabilizar o CI/CD. No Frontend, os bailouts de tipagem introduzidos no F2-11 podem ser mitigados futuramente de forma orgânica.
