#!/usr/bin/env python3
"""Fail-closed Org Merge Gate: verifies zero secrets/home-paths, live-broker firewall, SHA Actions, & MADR 4.0."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECRET_PATTERNS = (
    ("Broker Account ID", re.compile(r"\b(?:PA|DU)[0-9A-Z]*[0-9][0-9A-Z]*\b")),
    ("Alpaca Key Prefix", re.compile(r"\b(?:AK|PK)[0-9A-Z]{16,28}\b")),
    ("Private Key Header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    (
        "Live Alpaca Trading Endpoint",
        re.compile(r"(?<!paper-)(?<![A-Za-z0-9-])" + "api" + r"\." + "alpaca" + r"\.markets\b"),
    ),
    (
        "Forbidden Live Broker Binary",
        re.compile(r"\." + "claude/" + "bin/" + r"(?:live|alpaca-live-mcp|key-store)\b"),
    ),
    ("Local Home Path (macOS)", re.compile("/" + "Users/" + r"[A-Za-z0-9._-]+/")),
    ("Local Home Path (Linux)", re.compile(r"(?<![A-Za-z0-9_.-])/" + "home/" + r"[A-Za-z0-9._-]+/")),
    (
        "Local Home Path (Windows)",
        re.compile(r"\b[A-Za-z]:(?:\\|/)" + "Users" + r"(?:\\|/)[A-Za-z0-9._-]+(?:\\|/)"),
    ),
    ("Unescaped Single-Brace GH Expression", re.compile(r"\$\{\s*github\.")),
)
USES_RE = re.compile(r"^\s*-?\s*uses:\s*([^#\s]+)", re.MULTILINE)
SHA_PIN_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-f]{40}$")


def main() -> int:
    errors: list[str] = []
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
        env=clean_env,
    )
    for rel in (ln.strip() for ln in tracked.stdout.splitlines() if ln.strip()):
        fp = ROOT / rel
        if not fp.is_file():
            continue
        txt = fp.read_text(encoding="utf-8")
        for label, rx in SECRET_PATTERNS:
            if rx.search(txt):
                errors.append(f"{rel}: triggered {label}")
        if rel.startswith(".github/workflows/") and rel.endswith((".yml", ".yaml")):
            for target in USES_RE.findall(txt):
                if target.startswith(("./", "native-agent-stack/.github/")):
                    continue
                if not SHA_PIN_RE.match(target):
                    errors.append(f"{rel}: unpinned GitHub Action '{target}' (must use 40-char SHA)")

    cat = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "architecture_catalog.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
        env=clean_env,
    )
    if cat.returncode != 0:
        errors.append(f"ADR catalog gate failed: {cat.stderr or cat.stdout}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("PASS: merge_gate.py verified 0 leaks, 40-char SHA-pinned Actions, and MADR 4.0 parity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
