"""Unit tests for ADR-0037 fail-closed upstream-map.toml and ADR-evidence enforcement."""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import merge_gate


def test_repo_passes_upstream_map_and_adr_evidence() -> None:
    assert merge_gate.verify_upstream_map(REPO_ROOT) == []
    assert merge_gate.verify_adr_evidence(REPO_ROOT) == []


def test_rejects_unmapped_file_and_banned_upstream(tmp_path: pathlib.Path) -> None:
    (tmp_path / "UPSTREAM.md").write_text(
        "| `yfinance` | 0.2 | Apache | url | 2026 | bad | upstream |\n"
        "| `orca` | 1.4 | Apache | url | 2026 | good | upstream |\n",
        encoding="utf-8",
    )
    (tmp_path / "upstream-map.toml").write_text(
        "[areas]\n"
        '"src/bad.py" = { upstream = "yfinance", how = "integrate", feature = "f", why = "w" }\n',
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "bad.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "src" / "orphan.py").write_text("y = 2\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    errs = merge_gate.verify_upstream_map(tmp_path, shelf_dir=tmp_path / "no-shelf")
    assert any("yfinance" in e for e in errs)
    assert any("orphan.py" in e for e in errs)
