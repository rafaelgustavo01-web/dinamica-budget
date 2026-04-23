# Pipeline Control — Manual de Operação

> Guia prático para ligar, desligar e ajustar o ciclo de polling da pipeline multi-agente no Windows Server.

---

## Pré-requisitos

- **Windows PowerShell 5.1+**
- **Permissão de Administrador** para criar/deletar tarefas no Task Scheduler
- Localização do script: `scripts/pipeline-control.ps1`

---

## 1. Disparar o ciclo (`start`)

Cria uma tarefa no Windows Task Scheduler para cada role ativa (`po`, `supervisor`, `worker`, `qa`, etc.) e define `status: RUNNING` no config.

```powershell
# A partir da raiz do projeto
powershell -ExecutionPolicy Bypass -File scripts\pipeline-control.ps1 -Command start
```

### O que acontece
1. Lê `docs/pipeline/config.md`
2. Extrai roles ativas do bloco `## Roles Active`
3. Cria tarefas `Dinamica-Pipeline-[role]` que executam `scripts/pipeline-agent.ps1` a cada `interval_minutes`
4. Atualiza `status: RUNNING`, `started_at` e `stopped_at: null`

### Verificar criação
```powershell
schtasks /Query /TN "Dinamica-Pipeline-*"
```

---

## 2. Parar o ciclo (`stop`)

Remove todas as tarefas do Task Scheduler e pausa o pipeline.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\pipeline-control.ps1 -Command stop
```

### O que acontece
1. Deleta todas as tarefas `Dinamica-Pipeline-*`
2. Atualiza `status: STOPPED` e `stopped_at` no config
3. Agents que acordarem leem `STOPPED` e saem silenciosamente

---

## 3. Alterar o tempo de disparo (`time_set`)

Muda o intervalo de polling. Se o pipeline estiver rodando, recria as tarefas automaticamente.

```powershell
# Exemplo: mudar para 20 minutos
powershell -ExecutionPolicy Bypass -File scripts\pipeline-control.ps1 -Command time_set -Interval 20
```

### Comportamento por estado

| Estado do Pipeline | Resultado |
|---|---|
| `STOPPED` | Apenas atualiza `interval_minutes` no config. Novo intervalo entra em vigor no próximo `start`. |
| `RUNNING` | Atualiza config → executa `stop` → executa `start` com novo intervalo. Recriação automática. |

---

## Cheat Sheet

| Ação | Comando |
|---|---|
| **Ligar** | `powershell -ExecutionPolicy Bypass -File scripts\pipeline-control.ps1 -Command start` |
| **Desligar** | `powershell -ExecutionPolicy Bypass -File scripts\pipeline-control.ps1 -Command stop` |
| **Mudar tempo** | `powershell -ExecutionPolicy Bypass -File scripts\pipeline-control.ps1 -Command time_set -Interval 15` |
| **Ver config** | `Get-Content docs\pipeline\config.md` (procurar `status:` e `interval_minutes:`) |
| **Listar tarefas** | `schtasks /Query /TN "Dinamica-Pipeline-*"` |
| **Remover tarefa manual** | `schtasks /Delete /TN "Dinamica-Pipeline-[role]" /F` |

---

## Observabilidade e Logs

### Log de Execução por Role

Cada execução do `pipeline-agent.ps1` grava em `docs/pipeline/logs/pipeline-{role}.log`:

```powershell
# Ver últimas 20 linhas do log do worker
Get-Content docs\pipeline\logs\pipeline-worker.log -Tail 20

# Ver todos os logs em tempo real (se algum agente estiver rodando)
Get-Content docs\pipeline\logs\pipeline-worker.log -Wait
```

**Formato do log:**
```
2026-04-22 21:15:00 [INFO] [worker] === AGENT CYCLE === Role:worker Interval:3min Pipeline:RUNNING
2026-04-22 21:15:00 [INFO] [worker] Total messages in inbox: 2 | PENDING: 1 | DONE: 1 | BLOCKED: 0
2026-04-22 21:15:00 [ACTION] [worker] STATUS=ACTION_REQUIRED | Pending=1
2026-04-22 21:15:00 [ACTION] [worker] CLI_TARGET=codex-5.3 CLI_COMMAND=codex "Voce esta atuando como worker..."
```

### Wake-up por CLI (Agent Dispatch)

O pipeline resolve automaticamente qual CLI invocar com base no worker atribuído (`templates/workers.json` ou briefing). O operador **não precisa saber o provider** — basta acionar a role desejada.

#### Comando único por role

```powershell
# Worker (BUILD)
powershell -ExecutionPolicy Bypass -File scripts\pipeline-agent.ps1 -Role worker -DispatchMode run

# QA (REVIEW / TEST)
powershell -ExecutionPolicy Bypass -File scripts\pipeline-agent.ps1 -Role qa -DispatchMode run

# Supervisor (PLAN / AUDIT)
powershell -ExecutionPolicy Bypass -File scripts\pipeline-agent.ps1 -Role supervisor -DispatchMode run

# SM — Scrum Master (SYNC / DISPATCH)
powershell -ExecutionPolicy Bypass -File scripts\pipeline-agent.ps1 -Role sm -DispatchMode run

# Research (MODEL / ANALYSE)
powershell -ExecutionPolicy Bypass -File scripts\pipeline-agent.ps1 -Role research -DispatchMode run

# PO (REQUIREMENTS / PRIORITIZE)
powershell -ExecutionPolicy Bypass -File scripts\pipeline-agent.ps1 -Role po -DispatchMode run
```

#### Modos de despacho

| Modo | O que faz | Quando usar |
|---|---|---|
| `emit` | Só loga o comando que *seria* executado (padrão) | Observar o ciclo normal do Task Scheduler |
| `dry-run` | Testa a resolução do worker sem rodar o CLI | Validar configuração após mudanças |
| `run` | Resolve o CLI e executa o wake-up real | Acionamento manual ou CI/CD |

```powershell
# Exemplo: testar se o QA está corretamente mapeado antes de rodar
powershell -ExecutionPolicy Bypass -File scripts\pipeline-agent.ps1 -Role qa -DispatchMode dry-run
```

#### Resolução do worker

1. Tenta `Assigned worker` / `Worker ID` no briefing da sprint
2. Senão, tenta `reserved_for_sprint` em `templates/workers.json`
3. Se nada casar, loga `CLI_TARGET: unresolved` e `CLI_STATUS: no command mapping`

#### Exemplos de prompt gerado (`<prompt>`)

O script monta o prompt automaticamente, mas o operador pode invocar manualmente com o mesmo padrão:

**Worker**
```
Você é o Worker de execução deste projeto. Leia sua introdução em docs/roles/worker-readme.md e processe apenas as mensagens [PENDING]. Sprint: S-04. Action: BUILD. Briefing: @docs/briefings/sprint-S-04-briefing.md. Plan: @docs/superpowers/plans/2026-04-22-seguranca-rbac.md. Siga o protocolo da role, execute apenas o escopo aprovado e atualize inbox/artefatos ao concluir.
```

**QA**
```
Você é o QA deste projeto. Leia sua introdução em docs/roles/qa-readme.md e processe apenas as mensagens [PENDING]. Sprint: S-02. Action: REVIEW. Briefing: @docs/briefings/sprint-S-02-briefing.md. Siga o protocolo da role, execute apenas o escopo aprovado e atualize inbox/artefatos ao concluir.
```

**Supervisor**
```
Você é o Supervisor técnico deste projeto. Leia sua introdução em docs/roles/supervisor-readme.md e processe apenas as mensagens [PENDING]. Sprint: S-04. Action: PLAN. Siga o protocolo da role, execute apenas o escopo aprovado e atualize inbox/artefatos ao concluir.
```

**SM (Scrum Master)**
```
Você é o Scrum Master deste projeto. Leia sua introdução em docs/roles/sm-readme.md e processe apenas as mensagens [PENDING]. Action: SYNC. Siga o protocolo da role, execute apenas o escopo aprovado e atualize inbox/artefatos ao concluir.
```

**Research**
```
Você é o Researcher (Analista de Dados/ML) deste projeto. Leia sua introdução em docs/roles/research-readme.md e processe apenas as mensagens [PENDING]. Sprint: S-09. Action: MODEL. Siga o protocolo da role, execute apenas o escopo aprovado e atualize inbox/artefatos ao concluir.
```

**PO**
```
Você é o Product Owner deste projeto. Leia sua introdução em docs/roles/po-readme.md e processe apenas as mensagens [PENDING]. Action: PRIORITIZE. Siga o protocolo da role, execute apenas o escopo aprovado e atualize inbox/artefatos ao concluir.
```

#### Mapeamento de provider (resolvido automaticamente)

| Worker / Provider | CLI resolvido |
|---|---|
| `codex-*` / `OpenAI` | `codex "<prompt>"` |
| `gemini-*` / `Google` | `gemini "<prompt>"` |
| `kimi-*` / `Kimi CLI` | `kimi-cli run "<prompt>"` |
| `opencode-*` / `OpenCode` | `opencode --no-interactive "<prompt>"` |

Diretório de execução: sempre a partir da raiz do projeto (`CLI_WORKDIR` logado).

### Health Check Completo

```powershell
powershell -ExecutionPolicy Bypass -File scripts\pipeline-health.ps1
```

**O que mostra:**
- Status das tasks no Task Scheduler (última execução, resultado, próxima execução)
- Resumo dos arquivos de log por role (tamanho, última escrita, IDLE vs ACTION)
- Contagem de PENDING em cada inbox
- WIP check (sprints ativas vs limite)

### Verificar se uma Task Realmente Executou

```powershell
# Último resultado do worker (0 = sucesso, qualquer outro = erro)
schtasks /Query /TN "Dinamica-Pipeline-worker" /V /FO LIST | Select-String "Last Run Time|Last Result"

# Todas as tasks do pipeline com detalhes
schtasks /Query /TN "Dinamica-Pipeline-*" /V /FO LIST
```

---

## Troubleshooting

### "No active roles found in config"
O bloco `## Roles Active` no `config.md` está vazio ou com todas as roles `false`. Defina pelo menos uma como `true`:

```markdown
## Roles Active
- worker: true
```

### "valor inválido para opção /MO"
O campo `interval_minutes` está como `0` no config. Use `time_set` com um valor ≥ 1 antes do `start`:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\pipeline-control.ps1 -Command time_set -Interval 10
```

### Acesso negado ao criar tarefas
Execute o PowerShell como **Administrador**. O comando `schtasks /Create` exige privilégios elevados (`/RL HIGHEST`).

### Tarefas antigas não foram removidas
Rode `stop` manualmente antes do `start`, ou delete via Task Scheduler GUI:

```powershell
# Abrir interface gráfica
taskschd.msc
```

### Config.md corrompido após edição manual
A skill usa regex para atualizar valores. Edições manuais fora do padrão podem quebrar o parser. Formato esperado:

```markdown
## Polling
- interval_minutes: 15
- jitter_seconds: 30

## Pipeline State
- status: STOPPED
- started_at: null
- stopped_at: null
```

---

## Arquitetura Resumida

```
┌─────────────────────────────────────────────┐
│  Windows Task Scheduler                     │
│  ├── Dinamica-Pipeline-worker    (a cada N min)
│  ├── Dinamica-Pipeline-supervisor (a cada N min)
│  ├── Dinamica-Pipeline-qa        (a cada N min)
│  └── ...                                       │
└──────────┬────────────────────────────────────┘
           │ chama
           ▼
┌─────────────────────────────────────────────┐
│  scripts/pipeline-agent.ps1 -Role [name]    │
│  1. Lê config.md → sai se STOPPED           │
│  2. Lê docs/roles/[role]-readme.md          │
│  3. Extrai ## INBOX                         │
│  4. Parseia [PENDING], [DONE], [BLOCKED]    │
│  5. Resolve CLI do worker e emite/roda wake-up │
└─────────────────────────────────────────────┘
```

---

*Gerado em: 2026-04-22*
*Versão do protocolo: Role-Inbox Broadcast v1.1*
