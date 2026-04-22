#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
STACK="${2:-polyglot-monorepo}"
shift 2 || true
PERSONAS=("$@")

TPL="$ROOT/_agentic_foundation/templates"
STACK_DIR="$ROOT/_agentic_foundation/stacks"
PERSONA_DIR="$ROOT/_agentic_foundation/personas"

required=("CLAUDE.md" "AGENTS.md" "GEMINI.md" "OBJECTIVE.md" "STACK_PROFILE.md" "PERSONA_PROFILE.md" "ORCHESTRATION.md")
for f in "${required[@]}"; do
  [ -f "$ROOT/$f" ] || cp "$TPL/$f" "$ROOT/$f"
done

[ -f "$STACK_DIR/$STACK.md" ] || { echo "Unknown stack: $STACK" >&2; exit 1; }
cp "$STACK_DIR/$STACK.md" "$ROOT/STACK_PROFILE.md"

tmp="$(mktemp)"
echo "# PERSONA_PROFILE.md" > "$tmp"
echo "" >> "$tmp"
for persona in "${PERSONAS[@]}"; do
  [ -f "$PERSONA_DIR/$persona.md" ] || { echo "Unknown persona: $persona" >&2; rm -f "$tmp"; exit 1; }
  cat "$PERSONA_DIR/$persona.md" >> "$tmp"
  echo "" >> "$tmp"
done
cp "$tmp" "$ROOT/PERSONA_PROFILE.md"
rm -f "$tmp"

echo "Bootstrap complete. Update OBJECTIVE.md if needed."
