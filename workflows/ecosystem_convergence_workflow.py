# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA Schema-Typed `run_workflow`: Full-Ecosystem Triad & Peer-Bus Convergence Audit (`L0-L12`)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

peer_brief = kit.load_peer_brief("agy-sota-harness")
log(peer_brief)

TARGETS = [
    ("agy-sota-harness", "Run `python3 harness/run_probes.py` and verify 13/13 L0-L12 probes pass."),
    ("dsh-sota-harness", "Verify README.md L0-L9 anchors and clean `git status --short`."),
    ("sota-mover-ranker", "Run `python3 scripts/merge_gate.py` and verify 18/18 shelf pins & privacy gates pass."),
    ("peer-bus-and-skills", "Inspect `~/.agents/bin/sota-bus status`, `~/.agents/bin/sota-doctor`, and `~/.agents/bin/sota-core convergence`."),
]

TARGET_SCHEMA = {
    "type": "object",
    "properties": {
        "surface": {"type": "string"},
        "healthy": {"type": "boolean"},
        "evidence": {"type": "string"},
        "blockers": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["surface", "healthy", "evidence", "blockers"],
}

phase("Parallel Full-Ecosystem Harness & Peer-Bus Audit")

results = await parallel(
    TARGETS,
    lambda item: agent(
        f"{peer_brief}\n\n"
        f"Audit surface `{item[0]}` (strictly read-only; never print keys, PA/DU IDs, or balances): {item[1]}",
        schema=TARGET_SCHEMA,
        role=f"Audit {item[0]}",
        type_name="research",
        model="flash",
    ),
)

for r in results:
    log(f"[{r['surface']}] healthy={r['healthy']} | {r['evidence']}")

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "all_converged": {"type": "boolean"},
        "healthy_count": {"type": "integer"},
        "executive_brief": {"type": "string"},
        "next_actions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["all_converged", "healthy_count", "executive_brief", "next_actions"],
}

phase("Convergence Verdict")

verdict = await agent(
    f"{peer_brief}\n\n"
    f"Synthesize these {len(results)} harness convergence checks into a crisp executive verdict:\n{json.dumps(results)}",
    schema=SUMMARY_SCHEMA,
    role="SOTA Ecosystem Judge",
    type_name="research",
)

kit.record_workflow_run(
    repo="agy-sota-harness",
    workflow_id="ecosystem-convergence",
    done_summary=f"converged={verdict['all_converged']} ({verdict['healthy_count']}/{len(TARGETS)}): {verdict['executive_brief'][:320]}",
    verified_by="; ".join(f"{r['surface']}:{r['healthy']}" for r in results),
    next_priority=verdict["next_actions"][0] if verdict["next_actions"] else "Monitor peer convergence",
)

log(verdict["executive_brief"])
print(verdict)
