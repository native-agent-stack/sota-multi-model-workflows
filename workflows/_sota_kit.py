"""Shared Self-Bootstrapping Helper (`v3.0.0`) for SOTA `run_workflow` Orchestration Scripts.

Automatically loads live cross-peer leases, handovers, compiled lessons, HLZ trial multiplicity N,
`sota-doctor` (`10/10`), `sota-org-doctor` (`4` org invariants), and `ECOSYSTEM_CONVERGENCE_LOCK.json`
before spawning workflow agents, and writes redacted workflow checkpoints back to `peer_bus.db`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

BUS_DIR = Path.home() / ".agents" / "bus"
if str(BUS_DIR) not in sys.path:
    sys.path.insert(0, str(BUS_DIR))

try:
    import sota_bus_engine as bus  # type: ignore[import-not-found]
except Exception:  # noqa: BLE001
    bus = None  # type: ignore[assignment]


def get_workflow_args(ns: dict[str, Any]) -> dict[str, Any]:
    """Safely extract `args` dict injected by `run_workflow` even when omitted."""
    raw = ns.get("args")
    return dict(raw) if isinstance(raw, dict) else {}


def get_primary_workspace(ns: dict[str, Any], default: str = "") -> str:
    """Safely extract primary workspace path injected by `run_workflow`."""
    ws = ns.get("WORKSPACES")
    if isinstance(ws, (list, tuple)) and ws:
        return str(ws[0])
    return default


def run_preflight_summary(live_org: bool = False) -> dict[str, Any]:
    """Run deterministic local + org preflight checks (`sota-doctor`, `sota-org-doctor`, umbrella lock)."""
    home = Path.home()
    out: dict[str, Any] = {
        "sota_doctor": "UNAVAILABLE",
        "sota_org_doctor": "UNAVAILABLE",
        "umbrella_lock": "UNAVAILABLE",
    }

    doc_bin = home / ".agents" / "bin" / "sota-doctor"
    if doc_bin.is_file():
        proc = subprocess.run([str(doc_bin)], capture_output=True, text=True, timeout=15, check=False)
        try:
            dj = json.loads(proc.stdout)
            out["sota_doctor"] = {
                "status": dj.get("status"),
                "checks_passed": dj.get("checks_passed"),
                "checks_total": dj.get("checks_total"),
            }
        except json.JSONDecodeError:
            out["sota_doctor"] = {"exit_code": proc.returncode}

    org_bin = home / ".agents" / "bin" / "sota-org-doctor"
    if org_bin.is_file():
        flag = "--live" if live_org else "--offline"
        proc = subprocess.run([str(org_bin), flag], capture_output=True, text=True, timeout=30, check=False)
        try:
            oj = json.loads(proc.stdout)
            out["sota_org_doctor"] = {
                "status": oj.get("status"),
                "mode": oj.get("mode"),
                "repos_total": oj.get("repos_total"),
                "violations_count": len(oj.get("violations") or []),
            }
        except json.JSONDecodeError:
            out["sota_org_doctor"] = {"exit_code": proc.returncode}

    lock_file = home / "Documents" / "native-agent-stack" / "ECOSYSTEM_CONVERGENCE_LOCK.json"
    if lock_file.is_file():
        try:
            lj = json.loads(lock_file.read_text(encoding="utf-8"))
            out["umbrella_lock"] = {
                "schemaVersion": lj.get("schemaVersion"),
                "public_repos": len(lj.get("publicUnlimitedActionsTier") or []),
                "active_private_repos": len(lj.get("privateProprietaryExecutionAndVaultTier") or []),
                "cold_archived_repos": len(lj.get("coldArchivedSupersededTier") or []),
                "single_owner_layers": len(lj.get("layerSingleOwnerMap") or {}),
            }
        except Exception:  # noqa: BLE001
            out["umbrella_lock"] = "PARSE_ERROR"

    return out


def load_peer_brief(repo: str = "") -> str:
    """Return a compact, secret-redacted live peer-bus brief (<250 tokens) for child agent prompts."""
    if bus is None:
        return "[Peer Bus: unavailable]"
    try:
        conn = bus.get_conn()
        try:
            st = bus.bus_status(conn, repo=repo)
            lessons = conn.execute(
                "SELECT domain, title, evidence_grade FROM lessons ORDER BY created_at DESC LIMIT 4"
            ).fetchall()
        finally:
            conn.close()
    except Exception:  # noqa: BLE001
        return "[Peer Bus: unavailable]"

    lines = [
        f"[Live SOTA Peer Bus @ {st['as_of_utc']} | Trials N={st['hypothesis_trials_total']} | Next HLZ t*={st['next_trial_hlz_t_hurdle']}]"
    ]
    leases: list[dict[str, Any]] = st.get("active_leases") or []
    if leases:
        lease_txt = "; ".join(
            f"{it['agent_family']}@{it['repo']}({','.join(it['paths'][:2])}: {it['intent'][:60]})" for it in leases[:4]
        )
        lines.append(f"- Active Peer Leases (DO NOT clobber): {lease_txt}")
    handovers: list[dict[str, Any]] = st.get("handovers") or []
    if handovers:
        h0 = handovers[0]
        lines.append(f"- Latest Handover ({h0['repo']}): done='{h0['done'][:110]}' | next='{h0['next_priority'][:90]}'")
    if lessons:
        l_txt = "; ".join(f"[{r['evidence_grade']}:{r['domain']}] {r['title'][:65]}" for r in lessons)
        lines.append(f"- Top Compiled Lessons: {l_txt}")
    return "\n".join(lines)


def record_workflow_run(
    *,
    repo: str,
    workflow_id: str,
    done_summary: str,
    verified_by: str,
    open_risks: str = "none",
    next_priority: str = "",
) -> None:
    """Persist a redacted workflow execution checkpoint into `peer_bus.db` and `HANDOVER.md`."""
    if bus is None:
        return
    try:
        conn = bus.get_conn()
        try:
            bus.sync_handover(
                conn,
                repo=repo or "agy-workflow",
                agent_family=f"agy-workflow:{workflow_id}",
                done=done_summary[:500],
                verified_by=verified_by[:240],
                open_risks=open_risks[:240],
                next_priority=next_priority[:240],
            )
        finally:
            conn.close()
    except Exception:  # noqa: BLE001
        return
