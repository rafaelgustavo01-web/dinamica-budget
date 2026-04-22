"""
Memory auto-save hook with relevance filtering.

Only content that passes the relevance gate is saved to semantic memory.
This prevents memory pollution with trivial chitchat, temporary fixes,
or low-value exchanges.
"""

import re
from typing import Tuple, Optional

# Compile once for performance
_TRIVIAL_PATTERNS = [
    re.compile(r"\b(oi|ola|hey|hi|hello|tudo bem|como vai|bom dia|boa tarde|boa noite)\b", re.I),
    re.compile(r"\b(obrigad[ao]|thanks|thx|valeu|agradeço)\b", re.I),
    re.compile(r"\b(foi isso|that's it|done|pronto|ok|okay|perfeito|perfect)\b", re.I),
    re.compile(r"^\s*(sim|não|yes|no)\s*[!?.]*\s*$", re.I),
]

_SCORE_5_KEYWORDS = [
    "arquitetura", "architecture", "decidi usar", "decided to use",
    "credencial", "credential", "senha do sistema", "system password",
    "produção", "production", "deploy", "infraestrutura", "infrastructure",
    "dockerfile", "kubernetes", "terraform", "ci/cd", "pipeline",
    "ambiente prod", "production env",
]

_SCORE_4_TECH_KEYWORDS = [
    "solucionei", "solved", "funcionou", "worked", "resolved",
    "refatorei", "refactored", "otimiz", "optimiz", "implementei", "implemented",
    "criei a função", "created the function", "novo padrão", "new pattern",
]

_SCORE_4_CONFIG_KEYWORDS = [
    "configurei", "configured", ".env", "config", "setting",
    "mudei para", "changed to", "atualizei", "updated",
    "variável de ambiente", "environment variable",
]

_SCORE_3_PREFERENCE_KEYWORDS = [
    "prefiro", "i prefer", "gosto de", "i like",
    "não gosto", "i don't like", "odeio", "i hate",
    "sempre use", "always use", "nunca use", "never use",
]

_SCORE_3_EXPLICIT_SAVE = [
    "lembra", "salva isso", "decisao", "config",
    "aprendi", "important", "remember this", "save this",
    "guarda isso", "anota", "anotar", "registrar",
]

_SCORE_2_CONTEXT_KEYWORDS = [
    "contexto", "context", "sessão anterior", "previous session",
    "referência", "reference", "última vez", "last time",
]


def should_save_memory(
    user_msg: Optional[str],
    assistant_msg: Optional[str],
) -> Tuple[int, str, str]:
    """
    Decide if a conversation turn is worth saving to semantic memory.

    Args:
        user_msg: The user's message (can be None).
        assistant_msg: The assistant's response (can be None).

    Returns:
        Tuple of (importance: int, category: str, reason: str).
        importance = 0 means "do not save".
    """
    user_msg = (user_msg or "").strip()
    assistant_msg = (assistant_msg or "").strip()

    if not user_msg and not assistant_msg:
        return (0, "other", "empty turn")

    combined = (user_msg + " " + assistant_msg).lower()
    user_lower = user_msg.lower()
    assistant_lower = assistant_msg.lower()

    # ── SCORE 3: explicit save request (check before trivial) ───
    if any(k in user_lower for k in _SCORE_3_EXPLICIT_SAVE):
        return (3, "fact", "explicit save request")

    # ── BLOCKLIST: never save trivial exchanges ──────────────────
    for pattern in _TRIVIAL_PATTERNS:
        if pattern.search(combined):
            return (0, "other", "trivial exchange")

    # ── SCORE 5: critical architectural / production decisions ────
    if any(k in combined for k in _SCORE_5_KEYWORDS):
        return (5, "decision", "architectural or production decision")

    # ── SCORE 4: new technical solution with code ─────────────────
    has_code = "```" in assistant_msg or "import " in assistant_lower or "class " in assistant_lower or "def " in assistant_lower
    if any(k in combined for k in _SCORE_4_TECH_KEYWORDS) and has_code:
        return (4, "learning", "new technical solution with code")

    # ── SCORE 4: configuration change ─────────────────────────────
    if any(k in combined for k in _SCORE_4_CONFIG_KEYWORDS):
        return (4, "config", "configuration change")

    # ── SCORE 3: user preference ──────────────────────────────────
    if any(k in combined for k in _SCORE_3_PREFERENCE_KEYWORDS):
        return (3, "fact", "user preference")

    # ── SCORE 2: useful session context ───────────────────────────
    if any(k in combined for k in _SCORE_2_CONTEXT_KEYWORDS):
        return (2, "other", "session context")

    # ── Default: do not save ─────────────────────────────────────
    return (0, "other", "not relevant enough")


def format_memory_content(
    user_msg: Optional[str],
    assistant_msg: Optional[str],
    category: str,
    max_length: int = 600,
) -> str:
    """
    Format a turn into a concise memory string.

    Keeps the most informative part (usually the assistant response),
    but includes the user question for context if relevant.
    """
    user_msg = (user_msg or "").strip()
    assistant_msg = (assistant_msg or "").strip()

    # For decisions/learning, the assistant response is usually the valuable part
    if category in ("decision", "learning", "config"):
        content = assistant_msg
    else:
        # For facts/preferences, include user context
        content = f"Q: {user_msg}\nA: {assistant_msg}"

    if len(content) > max_length:
        content = content[:max_length].rsplit(" ", 1)[0] + " …"

    return content
