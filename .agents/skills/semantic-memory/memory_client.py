from __future__ import annotations

import os
import uuid
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Literal, Optional

import httpx
from supabase import create_client, Client

logger = logging.getLogger("semantic_memory")


class MemoryConfigError(Exception):
    """Raised when required credentials or config are missing."""
    pass


class MemoryAuthError(Exception):
    """Raised when authentication fails."""
    pass


class MemoryConnectionError(Exception):
    """Raised when a memory operation fails due to network/API error."""
    pass


@dataclass
class MemoryResult:
    memory_id: str
    agent_id: str
    agent_name: str
    content: str
    category: str
    tags: list
    importance: int
    session_id: Optional[str]
    created_at: str
    similarity: Optional[float] = None


class MemoryClient:
    # Class-level credential storage for runtime injection
    _email: Optional[str] = None
    _password: Optional[str] = None
    _supabase_url: Optional[str] = None
    _anon_key: Optional[str] = None

    def __init__(self) -> None:
        self._url = self._resolve("SUPABASE_URL", self.__class__._supabase_url)
        self._key = self._resolve("SUPABASE_ANON_KEY", self.__class__._anon_key)
        self._agent_email = self._resolve("AGENT_EMAIL", self.__class__._email)
        self._agent_password = self._resolve("AGENT_PASSWORD", self.__class__._password)
        self._session_id = os.getenv("AGENT_SESSION_ID", str(uuid.uuid4()))
        self._supabase: Client = create_client(self._url, self._key)
        self._access_token: Optional[str] = None

    def __repr__(self) -> str:
        email = self._agent_email
        url = self._url
        return (
            "MemoryClient(email=" + repr(email) + ", password=***, url=" + repr(url) + ")"
        )

    def __str__(self) -> str:
        return self.__repr__()

    # -- Credential injection

    @classmethod
    def set_credentials(
        cls,
        email: str,
        password: str,
        supabase_url: Optional[str] = None,
        anon_key: Optional[str] = None,
    ) -> None:
        """Inject credentials at runtime. Overrides .env values."""
        cls._email = email
        cls._password = password
        if supabase_url:
            cls._supabase_url = supabase_url
        if anon_key:
            cls._anon_key = anon_key

    @classmethod
    def set_email(cls, email: str) -> None:
        cls._email = email

    @classmethod
    def set_password(cls, password: str) -> None:
        cls._password = password

    @classmethod
    def set_supabase_url(cls, url: str) -> None:
        cls._supabase_url = url

    @classmethod
    def set_anon_key(cls, key: str) -> None:
        cls._anon_key = key

    # -- Auth

    def authenticate(self) -> None:
        """Sign in with email/password. Stores access_token in memory only."""
        try:
            response = self._supabase.auth.sign_in_with_password({
                "email": self._agent_email,
                "password": self._agent_password,
            })
            self._access_token = response.session.access_token
            logger.info("MemoryClient: authenticated as %s", self._agent_email)
        except Exception as e:
            raise MemoryAuthError(f"Authentication failed: {e}") from e

    # -- Write

    def save_memory(
        self,
        content: str,
        category: Literal["decision", "learning", "config", "fact", "other"],
        importance: int,
        agent_name: str,
        tags: list = [],
        session_id: Optional[str] = None,
        expires_at: Optional[str] = None,
        _retry: bool = True,
    ) -> str:
        """Call memory-ingest Edge Function. Returns memory_id.

        Args:
            agent_name: Logical name of the agent writing this memory.
                        Used to isolate memories per agent in normal search mode.
                        Stored as lowercase. Example: 'claude', 'gpt4', 'researcher'.
        """
        try:
            if expires_at is None and importance <= 2:
                exp = datetime.now(timezone.utc) + timedelta(days=30)
                expires_at = exp.isoformat()

            response = httpx.post(
                f"{self._url}/functions/v1/memory-ingest",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "content": content,
                    "category": category,
                    "importance": importance,
                    "agent_name": agent_name.strip().lower(),
                    "session_id": session_id or self._session_id,
                    "tags": tags,
                    "expires_at": expires_at,
                },
                timeout=30.0,
            )

            if response.status_code == 401 and _retry:
                self._reauthenticate()
                return self.save_memory(
                    content, category, importance, agent_name, tags,
                    session_id, expires_at, _retry=False,
                )

            response.raise_for_status()
            return response.json()["memory_id"]

        except MemoryAuthError:
            raise
        except Exception as e:
            ts = datetime.now(timezone.utc).isoformat()
            logger.error("save_memory failed at %s: %s", ts, e)
            raise MemoryConnectionError(f"save_memory failed: {e}") from e

    # -- Semantic search (normal mode: filtered by agent_name)

    def search_memories(
        self,
        query: str,
        agent_name: str,
        limit: int = 5,
        threshold: float = 0.75,
        _retry: bool = True,
    ) -> list:
        """Call semantic-search Edge Function. Returns [] on any failure.

        Normal mode: only returns memories belonging to `agent_name`.

        Args:
            agent_name: The calling agent's name. Filters results to this agent only.
        """
        try:
            response = httpx.post(
                f"{self._url}/functions/v1/semantic-search",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "limit": limit,
                    "threshold": threshold,
                    "agent_name": agent_name.strip().lower(),
                },
                timeout=30.0,
            )

            if response.status_code == 401 and _retry:
                self._reauthenticate()
                return self.search_memories(query, agent_name, limit, threshold, _retry=False)

            response.raise_for_status()
            return [self._parse_memory(m) for m in response.json()]

        except MemoryAuthError:
            raise
        except Exception as e:
            ts = datetime.now(timezone.utc).isoformat()
            logger.error("search_memories failed at %s: %s", ts, e)
            return []

    # -- Super search (elevation mode: reads ALL agents' memories)

    def super_search_memories(
        self,
        query: str,
        caller_agent_name: str,
        limit: int = 10,
        threshold: float = 0.70,
        _retry: bool = True,
    ) -> list:
        """Call super-search Edge Function. Returns memories across ALL agents.

        Requires /super_mem elevation password to have been validated by the
        caller before invoking this method. No password is transmitted here.

        Args:
            caller_agent_name: Name of the agent performing the super-search.
                               Stored in the audit log with [SUPER] prefix.
        """
        try:
            response = httpx.post(
                f"{self._url}/functions/v1/super-search",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "limit": limit,
                    "threshold": threshold,
                    "caller_agent_name": caller_agent_name.strip().lower(),
                },
                timeout=30.0,
            )

            if response.status_code == 401 and _retry:
                self._reauthenticate()
                return self.super_search_memories(
                    query, caller_agent_name, limit, threshold, _retry=False
                )

            response.raise_for_status()
            return [self._parse_memory(m) for m in response.json()]

        except MemoryAuthError:
            raise
        except Exception as e:
            ts = datetime.now(timezone.utc).isoformat()
            logger.error("super_search_memories failed at %s: %s", ts, e)
            return []

    # -- Direct read

    def get_session_memories(
        self,
        session_id: Optional[str] = None,
        limit: int = 20,
    ) -> list:
        """Direct supabase-py read. Returns [] on any failure."""
        try:
            sid = session_id or self._session_id
            response = (
                self._supabase
                .from_("memories")
                .select("id, agent_id, agent_name, content, category, tags, importance, session_id, created_at")
                .eq("session_id", sid)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return [self._parse_memory(m) for m in response.data]
        except Exception as e:
            ts = datetime.now(timezone.utc).isoformat()
            logger.error("get_session_memories failed at %s: %s", ts, e)
            return []

    # -- Admin

    def admin_action(self, action: str, payload: dict, _retry: bool = True) -> dict:
        """Call memory-admin Edge Function. Requires orchestrator role."""
        try:
            response = httpx.post(
                f"{self._url}/functions/v1/memory-admin",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                },
                json={"action": action, "payload": payload},
                timeout=30.0,
            )

            if response.status_code == 401 and _retry:
                self._reauthenticate()
                return self.admin_action(action, payload, _retry=False)

            response.raise_for_status()
            return response.json()

        except MemoryAuthError:
            raise
        except Exception as e:
            ts = datetime.now(timezone.utc).isoformat()
            logger.error("admin_action(%s) failed at %s: %s", action, ts, e)
            raise MemoryConnectionError(f"admin_action failed: {e}") from e

    # -- Internal helpers

    def _resolve(self, env_key: str, runtime_value: Optional[str]) -> str:
        value = runtime_value or os.getenv(env_key)
        if not value:
            raise MemoryConfigError(
                f"Missing config: '{env_key}' not set via "
                f"set_credentials() or environment variables."
            )
        return value

    def _reauthenticate(self) -> None:
        logger.warning("MemoryClient: token expired, re-authenticating")
        self.authenticate()

    @staticmethod
    def _parse_memory(data: dict) -> MemoryResult:
        return MemoryResult(
            memory_id=data.get("id") or data.get("memory_id", ""),
            agent_id=data.get("agent_id", ""),
            agent_name=data.get("agent_name", ""),
            content=data.get("content", ""),
            category=data.get("category", "other"),
            tags=data.get("tags") or [],
            importance=data.get("importance", 3),
            session_id=data.get("session_id"),
            created_at=data.get("created_at", ""),
            similarity=data.get("similarity"),
        )
