# Guia de Organização — gedAI Docs

> Última atualização: 2026-04-18

---

## Estrutura de Diretórios

```
docs/
├── BACKLOG.md                 # Fila viva de sprints
├── ORG-GUIDE.md            # Este arquivo
├── archives/                # Arquivos antigos consolidados por data
│   ├── YYYY-MM-DD/
│   │   ├── technical-review/
│   │   ├── technical-feedback/
│   │   ├── briefings/
│   │   └── walkthrough/
├── briefings/               # Briefings vivos (última versão)
├── superpowers/
│   ├── plans/             # Planos de sprint
│   ├── specs/             # Especificações
│   └── roadmap/           # Roadmap do projeto
└── walkthrough/
    ├── done/             # Walkthroughs concluídos (worker)
    └── reviewed/          # Walkthroughs revisados (QA)
```

---

## Convenção de Nomes

| Tipo | Formato | Exemplo |
|------|--------|--------|
| Technical Review | `technical-review-YYYY-MM-DD.md` | `technical-review-2026-04-17.md` |
| Technical Feedback | `technical-feedback-YYYY-MM-DD-vN.md` | `technical-feedback-2026-04-17-v4.md` |
| Briefing | `sprint-X-briefing.md` | `sprint-i-briefing.md` |
| Plano | `YYYY-MM-DD-gedai-sprint-X-name.md` | `2026-04-17-gedai-sprint-i-b-dag-leve.md` |
| Walkthrough | `walkthrough-X.md` | `walkthrough-i-b.md` |

---

## Arquivos Consolidados

Cada dia de trabalho deve ter um arquivo consolidado em `docs/archives/YYYY-MM-DD/`:

### 16-04-2026
- `technical-review/technical-review-2026-04-16.md`
- `technical-feedback/technical-feedback-2026-04-16.md`
- `briefings/briefings-2026-04-16.md`
- `walkthrough/walkthrough-2026-04-16.md`

### 17-04-2026
- `technical-review/technical-review-2026-04-17.md`
- `technical-feedback/technical-feedback-2026-04-17.md`
- `briefings/briefings-2026-04-17.md`
- `walkthrough/walkthrough-2026-04-17.md`

---

## Regras de Organização

1. **Sem duplicação**: Arquivos antigos movidos para `archives/`, não deixar cópias
2. **Uma versão por dia**: Consolidar múltiplos arquivos (v1, v2, v3...) em um único por dia
3. **UTF-8 Only**: Todos os arquivos em UTF-8 ou ASCII
4. **Nomes consistentes**: Seguir o formato таблиa acima
5. **BACKLOG.md atualizado**: Manter o estado atual sempre visível

---

## Fluxo de Arquivos

```
Plano → Briefing → Execução → Walkthrough → Technical Review → BACKLOG
```

- **Plano**: `docs/superpowers/plans/`
- **Briefing**: `docs/briefings/`
- **Walkthrough done**: `docs/walkthrough/done/`
- **Walkthrough reviewed**: `docs/walkthrough/reviewed/`
- **Technical Review**: `docs/archives/YYYY-MM-DD/technical-review/`
- **BACKLOG**: `docs/BACKLOG.md` (sempre no root)