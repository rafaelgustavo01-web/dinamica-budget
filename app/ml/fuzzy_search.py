"""
Fuzzy search module.

Primary strategy: pg_trgm via PostgreSQL (multi-worker safe, single source of truth).

pg_trgm threshold note:
  - pg_trgm similarity() returns 0.0-1.0
  - Default threshold in settings: 0.85
  - This is DIFFERENT from the semantic threshold (0.65)
"""

from app.core.logging import get_logger

logger = get_logger(__name__)
