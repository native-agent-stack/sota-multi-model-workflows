# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA Schema-Typed `run_workflow`: Cross-Peer Lease, Verification & Orca Second-Opinion Gate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = args if "args" in globals() and isinstance(args, dict) else {}
target_repo = str(cfg.get("repo") or "agy-sota-harness")
target_repo_dir = kit.resolve_repo_dir(target_repo)
peer_brief = kit.load_peer_brief(target_repo)
rc_ctx = kit.load_research_convergence_context()
rc_envelope = kit.verify_workflow_research_convergence("cross-peer-orca-review", repo=target_repo)
log(peer_brief)

GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "gate_passed": {"type": "boolean"},
        "p0_p1_findings": {"type": "array", "items": {"type": "string"}},
        "verification_commands_run": {"type": "array", "items": {"type": "string"}},
        "handover_ready_summary": {"type": "string"},
    },
    "required": ["gate_passed", "p0_p1_findings", "verification_commands_run", "handover_ready_summary"],
}

phase("Two-Pass Deterministic & Security Verification")

audit = await agent(
    f"{peer_brief}\n\n"
    f"Research-Convergence Contract (`{rc_ctx['schema_version']}`, `sota-research-feeds.v2`, ADR-0004 3-tier SHA "
    f"provenance, `PHILOSOPHY_ONLY` sibling-repo authority, `Mac M5 Max <-> Noesis` cross-OS parity).\n"
    f"Run the two-pass deterministic & P0-P3 self-refuting verification gate on `~/Documents/{target_repo}` "
    f"(`ruff`, `ty`, `sg scan`, `pytest`, `merge_gate.py` if present) and check `~/.agents/bin/sota-bus status --repo {target_repo}`. "
    "Never print secrets or account IDs.",
    schema=GATE_SCHEMA,
    role=f"Verify {target_repo}",
    type_name="sota-code-verifier",
)

kit.record_workflow_run(
    repo=target_repo,
    workflow_id="cross-peer-orca-review",
    done_summary=f"gate_passed={audit['gate_passed']}: {audit['handover_ready_summary'][:350]}",
    verified_by="; ".join(audit["verification_commands_run"][:4]) or "sota-code-verifier",
    open_risks="; ".join(audit["p0_p1_findings"][:3]) or "none",
    next_priority="Proceed to merge/handover" if audit["gate_passed"] else "Resolve P0/P1 findings",
)

log(f"[{target_repo}] gate_passed={audit['gate_passed']} | P0/P1={len(audit['p0_p1_findings'])}")
print(audit)
