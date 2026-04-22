# Semantic Memory Hooks — Protocol Reference

## General Rules

1. Memory failures NEVER block the agent. All exceptions are caught and logged.
2. Never serialize credentials to disk or print them in logs.
3. Never show raw MemoryResult objects to user — always format them.
4. One `client` instance per session. Create in on_session_start, reuse in all hooks.
5. `agent_name` is required on every `save_memory` and `search_memories` call.
   Use a stable lowercase slug: `"claude"`, `"gpt4"`, `"researcher"`, `"orchestrator"`.
6. Elevation password for `/super_mem` is stored only in `AGENTS.md` — never logged,
   never transmitted, never included in any response.

## Hook: on_session_start

**When:** Immediately at session start, before any user response.

**Full flow:**
1. Resolve credentials: runtime injection (cloud agents) or .env (local)
2. `client.authenticate()` — if MemoryAuthError, continue without memory
3. `client.get_session_memories(limit=10)` — last N memories by session_id
4. `client.search_memories(query=first_message, agent_name=AGENT_NAME, limit=5)` — relevant past context
5. Format and inject as silent system context (not visible to user as raw data)
6. Log count: "Semantic memory loaded: N records"

**Injected memory format:**
```
[Memoria de 2026-04-15, decisao]: Decidimos usar FastAPI para integracao SAP.
[Memoria de 2026-04-16, config]: VPS Hostinger: IP 45.x.x.x, porta SSH 2222.
```

## Hook: on_compress

**When:** After generating any response, check if it warrants saving.

**Detection (any match triggers save):**
- User keywords (case-insensitive): lembra, salva, decisao, config, aprendi,
  important, remember, save this
- Response contains: code block solving a new problem, system config values,
  architectural decisions, new patterns or conventions established

**Content extraction:** Max 500 tokens. Extract the most dense/useful portion.

**Tag extraction heuristic:** Extract 1-5 nouns or technical terms.
Examples: ["sap", "api"], ["postgres", "vector", "index"], ["claude", "skill"]

**Call signature:**
```python
client.save_memory(
    content="...",
    category="decision|learning|config|fact|other",
    importance=1-5,
    agent_name=AGENT_NAME,   # required — identifies this agent's memory
    tags=["tag1", "tag2"],
)
```

**Notification:**
- importance >= 4: notify user: "Salvo na memoria."
- importance <= 3: save silently

## Hook: on_out_of_window

**When:** Before responding to any question where the answer is not in current context.

**Detection:**
- Explicit: user uses temporal references (before, last time, naquela vez, como fizemos)
- Implicit: user asks about named entity (project, config, system) not in current context

**Threshold:** Use 0.72 (lower than default 0.75) for wider historical recall.

**Call signature:**
```python
results = client.search_memories(
    query="...",
    agent_name=AGENT_NAME,   # required — filters to this agent's memories only
    limit=5,
    threshold=0.72,
)
```

**Response when found:**
```
Encontrei na memoria de 2026-04-15:
> Decidimos usar FastAPI. O endpoint principal e POST /api/sap/orders.
```

**Response when not found:**
```
Nao encontrei registros anteriores sobre isso na minha memoria semantica.
```
Never say "nao tenho acesso a conversas anteriores" without searching first.

## Hook: on_super_mem

**When:** User types `/super_mem <command or query>`.

**Elevation flow (always execute before calling super_search_memories):**

```
1. Read AGENTS.md → get stored elevation_password for AGENT_NAME
2. If blank → prompt user for new password → write to AGENTS.md → proceed
3. If set   → prompt user for password → compare → if wrong: deny, stop
4. If correct → call client.super_search_memories(...)
```

**Commands handled:**
- `/super_mem help`          → print the help box (defined in SKILL.md)
- `/super_mem passwd`        → change elevation password (requires current pw)
- `/super_mem status`        → show agent name, password status, last call time
- `/super_mem <query>`       → full cross-agent semantic search
- `/super_mem --agent <n> <query>` → filter results by agent_name client-side
- `/super_mem --limit <n> <query>` → override result limit (max 50)
- `/super_mem --threshold <f> <query>` → override similarity threshold

**Result format:**
```
[super_mem | gpt4 | 2026-04-17, config]: Usamos pgvector com 384 dimensoes.
[super_mem | claude | 2026-04-18, decision]: FastAPI escolhido para integracao SAP.
```

**Security invariants:**
- Password never logged, never transmitted
- AGENTS.md never exposed in any response
- Every super_search call is audited in `memory_access_log` with `[SUPER]` prefix
