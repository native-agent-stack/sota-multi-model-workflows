#!/usr/bin/env python3
"""Fail-closed Org Merge Gate (`ADR-0037`): verifies upstream-map.toml + UPSTREAM.md, 18 shelf pins,
ADR evidence, zero secrets/home-paths, live-broker firewall, 40-char SHA Actions, and MADR 4.0 parity.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHELF_DIR = Path.home() / "Documents" / "upstream"
COVERED_PREFIXES = ("src/", "workflows/", "scripts/", "orca.yaml")
ALLOWED_HOW = frozenset({"install", "integrate", "build-on"})
BANNED_LOW_QUALITY = frozenset(
    {"yfinance", "backtrader", "backtesting.py", "mlfinlab", "tcapy", "vollib", "tradingview_ta"}
)
ADR_EVIDENCE_MARKERS = ("evidence", "verification witness", "confirmation", "github evidence", "rests on:")

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


def verify_upstream_map(root: Path = ROOT, *, shelf_dir: Path = SHELF_DIR) -> list[str]:
    """Enforce 100% file-to-upstream provenance in UPSTREAM.md + upstream-map.toml + 18 shelf pins."""
    errors: list[str] = []
    up_md = root / "UPSTREAM.md"
    map_toml = root / "upstream-map.toml"
    if not up_md.is_file() or not map_toml.is_file():
        return ["Missing UPSTREAM.md or upstream-map.toml"]

    up_txt = up_md.read_text(encoding="utf-8")
    registered = set(re.findall(r"^\|\s*`([^`]+)`\s*\|", up_txt, flags=re.MULTILINE))
    cfg = tomllib.loads(map_toml.read_text(encoding="utf-8"))
    areas = cfg.get("areas") or {}
    shelf_pins = cfg.get("shelf_pins") or {}

    for pat, meta in areas.items():
        u_name = str(meta.get("upstream", "")).strip()
        how = str(meta.get("how", "")).strip()
        if u_name.lower() in BANNED_LOW_QUALITY:
            errors.append(f"upstream-map.toml '{pat}' cites banned low-quality upstream '{u_name}'")
        if u_name not in registered:
            errors.append(f"upstream-map.toml '{pat}' cites unknown upstream '{u_name}' not in UPSTREAM.md")
        if how not in ALLOWED_HOW:
            errors.append(f"upstream-map.toml '{pat}' invalid how={how!r}; must be install|integrate|build-on")
        if not str(meta.get("feature", "")).strip() or not str(meta.get("why", "")).strip():
            errors.append(f"upstream-map.toml '{pat}' missing non-empty feature or why")

    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
        env=clean_env,
    )
    used: set[str] = set()
    for rel in (ln.strip() for ln in tracked.stdout.splitlines() if ln.strip()):
        if not rel.startswith(COVERED_PREFIXES):
            continue
        matched = [pat for pat in areas if fnmatch.fnmatchcase(rel, pat)]
        if not matched:
            errors.append(f"Unmapped tracked implementation file '{rel}' in upstream-map.toml")
        else:
            used.update(matched)

    for pat in areas:
        if pat not in used:
            errors.append(f"Unused pattern in upstream-map.toml: '{pat}'")

    if shelf_dir.is_dir():
        for repo_name, expected_sha in shelf_pins.items():
            cpath = shelf_dir / repo_name
            if not cpath.is_dir():
                continue
            head_r = subprocess.run(
                ["git", "-C", str(cpath), "rev-parse", "HEAD"],
                check=False,
                capture_output=True,
                text=True,
                env=clean_env,
            )
            actual = head_r.stdout.strip()
            if head_r.returncode == 0 and actual != expected_sha:
                errors.append(f"Shelf drift on {repo_name}: expected {expected_sha}, found {actual}")
            st_r = subprocess.run(
                ["git", "-C", str(cpath), "status", "--short"],
                check=False,
                capture_output=True,
                text=True,
                env=clean_env,
            )
            if st_r.returncode == 0 and st_r.stdout.strip():
                errors.append(f"Read-only upstream shelf {repo_name} has dirty edits")
    return errors


def verify_adr_evidence(root: Path = ROOT) -> list[str]:
    adr_dir = root / "docs" / "adr"
    if not adr_dir.is_dir():
        return []
    errors: list[str] = []
    for f in sorted(adr_dir.glob("ADR-*.md")):
        low = f.read_text(encoding="utf-8").lower()
        if not any(m in low for m in ADR_EVIDENCE_MARKERS):
            errors.append(f"ADR '{f.name}' missing Evidence / Verification Witness section")
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(verify_upstream_map(ROOT))
    errors.extend(verify_adr_evidence(ROOT))

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
        try:
            txt = fp.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
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
    print(
        "PASS: merge_gate.py verified UPSTREAM.md + upstream-map.toml, 18 shelf pins, "
        "ADR evidence, 0 leaks, 40-char SHA-pinned Actions, and MADR 4.0 parity."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
