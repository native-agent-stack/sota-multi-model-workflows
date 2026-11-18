"""Portable SQLite WAL Multi-Model Peer Bus (`Antigravity` + `Claude` + `Codex` + `DSH` + `Orca`)."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import sqlite3
from collections.abc import Generator
from contextlib import closing, contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def _normalize_lease_path(raw: str) -> str:
    p = raw.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p.removeprefix("./")
    p = p.strip("/")
    return "*" if p in ("", ".", "*", "**") else p


def _paths_overlap(raw_a: str, raw_b: str) -> bool:
    a = _normalize_lease_path(raw_a)
    b = _normalize_lease_path(raw_b)
    if a == "*" or b == "*" or a == b:
        return True
    if fnmatch.fnmatchcase(a, b) or fnmatch.fnmatchcase(b, a):
        return True
    a_stem = a.removesuffix("/**").removesuffix("/*")
    b_stem = b.removesuffix("/**").removesuffix("/*")
    if a_stem == b_stem:
        return True
    return (
        a.startswith((b + "/", b_stem + "/"))
        or b.startswith((a + "/", a_stem + "/"))
        or a_stem.startswith(b_stem + "/")
        or b_stem.startswith(a_stem + "/")
    )


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
        now_dt = datetime.now(UTC)
        now_iso = now_dt.isoformat()
        exp = (now_dt + timedelta(minutes=ttl_m)).isoformat()
        req_paths = list(paths) if paths else ["*"]

        with closing(sqlite3.connect(str(self.db_path), timeout=10.0, isolation_level=None)) as cx:
            cx.execute("BEGIN IMMEDIATE")
            try:
                rows = cx.execute(
                    "SELECT lease_key, session_id, paths_json, expires_utc FROM leases "
                    "WHERE repo = ? AND session_id != ? AND expires_utc > ?",
                    (repo, session_id, now_iso),
                ).fetchall()
                for foreign_key, _foreign_sid, foreign_paths_json, foreign_exp in rows:
                    try:
                        if datetime.fromisoformat(str(foreign_exp)) <= now_dt:
                            continue
                    except ValueError:
                        pass
                    foreign_paths = json.loads(foreign_paths_json or '["*"]')
                    overlapping = [rp for rp in req_paths if any(_paths_overlap(rp, str(fp)) for fp in foreign_paths)]
                    if overlapping:
                        cx.execute("COMMIT")
                        return {
                            "claimed": False,
                            "lease_key": key,
                            "conflict_lease_key": str(foreign_key),
                            "conflict_paths": overlapping,
                        }

                cx.execute("DELETE FROM leases WHERE repo = ? AND expires_utc <= ?", (repo, now_iso))
                cx.execute(
                    "INSERT OR REPLACE INTO leases VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (key, repo, agent, session_id, json.dumps(req_paths), intent, exp),
                )
                cx.execute("COMMIT")
            except BaseException:
                if cx.in_transaction:
                    cx.execute("ROLLBACK")
                raise
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
