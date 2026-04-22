# Semantic Memory Skill

Persistent semantic memory for multi-agent systems via Supabase + pgvector.

## What this skill provides

- `memory_client.py` — Python SDK to save and search memories
- `memory_hooks.py` — Auto-save intelligence hooks
- `AGENTS.md` — Per-agent local configuration (elevation passwords)

## Installation

```bash
pip install supabase>=2.4.0 httpx>=0.27.0 python-dotenv>=1.0.0
```

## Quick Start

### 1. Run `/init`

The skill includes an interactive setup script. Run it once per agent workspace:

```bash
python -m semantic_memory.init
```

Or from Python:

```python
from semantic_memory.init import run_init
run_init()
```

This will:
- Ask for your Supabase project URL and anon key
- Optionally ask for a Management Token for automatic setup
- Create or verify the shared auth user
- Generate a local `.env` file with credentials

### 2. Use in your agent

```python
from memory_client import MemoryClient

# Credentials are read from environment variables or .env
client = MemoryClient()
client.authenticate()

# Save a memory (agent_name is mandatory)
memory_id = client.save_memory(
    content="Decided to use pgvector for semantic search",
    category="decision",
    importance=4,
    agent_name="claude",
    tags=["pgvector", "supabase"],
)

# Search your own memories
results = client.search_memories(
    query="vector database architecture",
    agent_name="claude",
)
```

## Runtime injection (cloud/remote agents)

If `.env` is not available, inject credentials at runtime:

```python
MemoryClient.set_credentials(
    email="shared@domain.com",
    password="shared-password",
    supabase_url="https://project.supabase.co",
    anon_key="anon-key",
)
client = MemoryClient()
client.authenticate()
```

## Agent identity

All agents share the same Supabase credentials. Logical separation is done via
`agent_name` passed in every API call. Use a stable lowercase slug:
`"claude"`, `"gpt4"`, `"researcher"`, `"orchestrator"`.

## `/super_mem` — Elevation mode

Cross-agent memory search requires an elevation password stored locally in
`AGENTS.md`. See `SKILL.md` for full instructions.

## Tests

```bash
python -m pytest tests/test_memory_client.py -v
```
