"""Shared Self-Bootstrapping Helper for SOTA `run_workflow` Orchestration Scripts.

Automatically loads live cross-peer leases, handovers, compiled lessons, and HLZ trial multiplicity N
from `~/.agents/bus/peer_bus.db` before spawning workflow agents, and writes redacted workflow
checkpoints back to the shared peer bus upon completion.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

BUS_DIR = Path.home() / ".agents" / "bus"
if str(BUS_DIR) not in sys.path:
    sys.path.insert(0, str(BUS_DIR))

import sota_bus_engine as bus


def load_peer_brief(repo: str = "") -> str:
    """Return a compact, secret-redacted live peer-bus brief (<250 tokens) for child agent prompts."""
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
            f"{it['agent_family']}@{it['repo']}({','.join(it['paths'][:2])}: {it['intent'][:60]})"
            for it in leases[:4]
        )
        lines.append(f"- Active Peer Leases (DO NOT clobber): {lease_txt}")
    handovers: list[dict[str, Any]] = st.get("handovers") or []
    if handovers:
        h0 = handovers[0]
        lines.append(
            f"- Latest Handover ({h0['repo']}): done='{h0['done'][:110]}' | next='{h0['next_priority'][:90]}'"
        )
    if lessons:
        l_txt = "; ".join(
            f"[{r['evidence_grade']}:{r['domain']}] {r['title'][:65]}" for r in lessons
        )
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
