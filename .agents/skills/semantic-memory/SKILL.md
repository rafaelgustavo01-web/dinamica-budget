---
name: semantic-memory
description: Use when the user refers to prior sessions, asks to remember durable project decisions, or needs cross-session recall backed by shared semantic memory.
---

# Semantic Memory

Use this skill when memory outside the current context window would materially help, or when the user asks to persist something important for future sessions.

## When to Use

- The user says "remember this", "we did this before", or asks about a prior decision.
- A durable preference, credential location, architecture choice, or operating rule should be persisted.
- You need to search prior semantic memories before claiming there is no earlier context.

## Core Rules

- Memory access must never block the main task.
- Search first when the user references prior work.
- Save only durable, high-value information.
- Never expose secrets, tokens, or local credential files in responses.

## Save Guidance

Good candidates:
- architecture decisions
- environment or deployment rules
- stable user preferences
- validated technical learnings

Do not save:
- greetings and thanks
- temporary debugging noise
- low-value chatter
- raw secrets

## Search Guidance

When the user references earlier work:

1. Build a focused semantic query from the user's request.
2. Search the memory store for the current agent first.
3. If elevated cross-agent access is explicitly requested and configured, use the protected global search flow.
4. If no memory is found, say that no earlier record was found instead of assuming none exists.

## Safety

- Treat memory failures as non-fatal.
- Keep elevation credentials local only.
- Never print credential material, Supabase keys, or stored passwords.
