"""
Conversation session store.

Uses Redis when REDIS_URL is set and reachable; otherwise (or if Redis fails at
runtime) transparently falls back to a bounded in-memory dict. Failures are
logged and surfaced through `status()` - never silently ignored.
"""

import json
import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional

logger = logging.getLogger("sagarvani.sessions")

MAX_MEMORY_SESSIONS = 500


class SessionStore:
    def __init__(self, redis_url: Optional[str] = None, ttl_seconds: int = 3600, redis_client: Any = None):
        self.ttl = ttl_seconds
        self._mem: "OrderedDict[str, tuple[float, Dict[str, Any]]]" = OrderedDict()
        self._lock = threading.Lock()
        self._redis = None
        self.backend = "memory"
        self.last_error: Optional[str] = None

        if redis_client is not None:
            self._redis = redis_client
            self.backend = "redis"
        elif redis_url:
            self._connect(redis_url)

    def _connect(self, url: str) -> None:
        try:
            import redis  # optional dependency

            client = redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2, decode_responses=True)
            client.ping()
            self._redis = client
            self.backend = "redis"
            logger.info("Session store: Redis connected")
        except Exception as exc:  # ImportError, ConnectionError, ...
            self.last_error = f"{type(exc).__name__}: {exc}"
            logger.warning("Redis unavailable (%s) - using in-memory sessions", self.last_error)

    # ── API ──────────────────────────────────────────────────────────────────
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self._redis is not None:
            try:
                raw = self._redis.get(self._key(session_id))
                return json.loads(raw) if raw else None
            except Exception as exc:
                self._redis_failed(exc)
        with self._lock:
            item = self._mem.get(session_id)
            if not item:
                return None
            ts, data = item
            if time.time() - ts > self.ttl:
                self._mem.pop(session_id, None)
                return None
            return json.loads(json.dumps(data))

    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        if self._redis is not None:
            try:
                self._redis.set(self._key(session_id), json.dumps(data), ex=self.ttl)
                return
            except Exception as exc:
                self._redis_failed(exc)
        with self._lock:
            self._mem[session_id] = (time.time(), json.loads(json.dumps(data)))
            self._mem.move_to_end(session_id)
            while len(self._mem) > MAX_MEMORY_SESSIONS:
                self._mem.popitem(last=False)

    def delete(self, session_id: str) -> None:
        if self._redis is not None:
            try:
                self._redis.delete(self._key(session_id))
            except Exception as exc:
                self._redis_failed(exc)
        with self._lock:
            self._mem.pop(session_id, None)

    def status(self) -> Dict[str, Any]:
        return {"backend": self.backend, "redis_error": self.last_error, "ttl_seconds": self.ttl}

    # ── internals ────────────────────────────────────────────────────────────
    @staticmethod
    def _key(session_id: str) -> str:
        return f"sagarvani:session:{session_id}"

    def _redis_failed(self, exc: Exception) -> None:
        self.last_error = f"{type(exc).__name__}: {exc}"
        logger.error("Redis operation failed (%s) - degrading to in-memory sessions", self.last_error)
        self._redis = None
        self.backend = "memory"
