"""Portable SQLite WAL Multi-Model Peer Bus (`Antigravity` + `Claude` + `Codex` + `DSH` + `Orca`)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Generator
from contextlib import closing, contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


class PortablePeerBus:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as cx:
            cx.execute("PRAGMA journal_mode=WAL")
            cx.execute(
                "CREATE TABLE IF NOT EXISTS leases ("
                "lease_key TEXT PRIMARY KEY, repo TEXT, agent TEXT, session_id TEXT, "
                "paths_json TEXT, intent TEXT, expires_utc TEXT)"
            )
            cx.execute(
                "CREATE TABLE IF NOT EXISTS messages ("
                "msg_id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, recipient TEXT, "
                "repo TEXT, body TEXT, created_utc TEXT)"
            )
            cx.execute(
                "CREATE TABLE IF NOT EXISTS hypotheses ("
                "trial_n INTEGER PRIMARY KEY AUTOINCREMENT, hypothesis_id TEXT UNIQUE, "
                "repo TEXT, spec_sha256 TEXT, created_utc TEXT)"
            )

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection]:
        with closing(sqlite3.connect(str(self.db_path), timeout=10.0)) as connection, connection:
            yield connection

    def claim_lease(
        self, repo: str, agent: str, session_id: str, paths: list[str], intent: str, ttl_m: int = 45
    ) -> dict[str, Any]:
        key = f"{repo}::{session_id}"
        exp = (datetime.now(UTC) + timedelta(minutes=ttl_m)).isoformat()
        with self._conn() as cx:
            cx.execute(
                "INSERT OR REPLACE INTO leases VALUES (?, ?, ?, ?, ?, ?, ?)",
                (key, repo, agent, session_id, json.dumps(paths), intent, exp),
            )
        return {"claimed": True, "lease_key": key, "expires_utc": exp}

    def release_lease(self, repo: str, session_id: str) -> dict[str, Any]:
        key = f"{repo}::{session_id}"
        with self._conn() as cx:
            cx.execute("DELETE FROM leases WHERE lease_key = ?", (key,))
        return {"released": True, "lease_key": key}

    def send_message(self, sender: str, recipient: str, repo: str, body: str) -> int:
        now = datetime.now(UTC).isoformat()
        with self._conn() as cx:
            cur = cx.execute(
                "INSERT INTO messages (sender, recipient, repo, body, created_utc) VALUES (?, ?, ?, ?, ?)",
                (sender, recipient, repo, body, now),
            )
            return int(cur.lastrowid or 0)

    def preregister_hypothesis(self, repo: str, hypothesis_id: str, spec: str) -> dict[str, Any]:
        digest = hashlib.sha256(spec.encode("utf-8")).hexdigest()
        now = datetime.now(UTC).isoformat()
        with self._conn() as cx:
            cur = cx.execute(
                "INSERT INTO hypotheses (hypothesis_id, repo, spec_sha256, created_utc) VALUES (?, ?, ?, ?)",
                (hypothesis_id, repo, digest, now),
            )
            n = int(cur.lastrowid or 1)
        return {"trial_n": n, "hypothesis_id": hypothesis_id, "spec_sha256": digest}
