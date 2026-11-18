"""SOTA Council of High Intelligence (`run_workflow` Engine — Self-Bootstrapping & Schema-Typed).

Pass `Args={"question": "...", "repo": "optional-repo-name"}`.
Automatically injects live `sota-bus` peer leases/handovers/lessons, runs 3 orthogonal specialists in parallel
(`sota-deep-synthesizer`, `self`, `sota-falsifier`), adjudicates disagreements with structured JSON validation,
and writes the decision checkpoint back to `~/.agents/wiki/HANDOVER.md`.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = kit.get_workflow_args(globals())
question = str(
    cfg.get("question") or "Audit the current workspace architecture and recommend the highest-leverage next step."
)
repo_hint = str(cfg.get("repo") or "")
scope_note = f"Target repository: ~/Documents/{repo_hint}. " if repo_hint else ""
peer_brief = kit.load_peer_brief(repo_hint)
rc_ctx = kit.load_research_convergence_context()

SEAT_SCHEMA = {
    "type": "object",
    "properties": {
        "thesis": {"type": "string"},
        "evidence_citations": {"type": "array", "items": {"type": "string"}},
        "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
        "failure_modes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["thesis", "evidence_citations", "evidence_grade", "failure_modes"],
}

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "bluf_decision": {"type": "string"},
        "disagreements_resolved": {"type": "array", "items": {"type": "string"}},
        "verification_gate_commands": {"type": "array", "items": {"type": "string"}},
        "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
        "next_priority": {"type": "string"},
    },
    "required": [
        "bluf_decision",
        "disagreements_resolved",
        "verification_gate_commands",
        "evidence_grade",
        "next_priority",
    ],
}

log(peer_brief)  # noqa: F821
phase("Phase 1: Orthogonal 3-Perspective Council")  # noqa: F821

seats = [
    (
        "First-Principles & Upstream Architect",
        "sota-deep-synthesizer",
        f"{peer_brief}\n\n{scope_note}Question: {question}\n"
        f"Research-Convergence (`{rc_ctx['schema_version']}`, `sota-research-feeds.v2`, ADR-0004 3-tier SHA provenance, "
        "`PHILOSOPHY_ONLY` sibling-repo authority, `Mac M5 Max <-> Noesis` parity).\n"
        "Inspect ~/Documents/upstream/PINS.md and UPSTREAM.md first. Propose the minimal-diff, upstream-first design "
        "(Karpathy/Ponytail rule). Never print keys, account IDs, or balances.",
    ),
    (
        "Empirical Statistical & Execution Pragmatist",
        "self",
        f"{peer_brief}\n\n{scope_note}Question: {question}\n"
        "Evaluate empirical measurability, 7-feed `sota-research-feeds.v2` PIT constraints, rate-limit/latency budgets, "
        "1x & 2x transaction/compute costs, and HLZ multiple-testing / MinTRL / MDE power gates. "
        "Never print keys, account IDs, or balances.",
    ),
    (
        "Adversarial Premortem & Boundary Red-Team",
        "sota-falsifier",
        f"{peer_brief}\n\n{scope_note}Question: {question}\n"
        "Assume this design fails 30 days from now. Enumerate exact lookahead (`RAW`/`ALL`, SEC `acceptanceDateTime`, "
        "FINRA `T-1`), clock/timezone, dilution, wide-NBBO adverse selection, `Mac M5 Max <-> Noesis` split-brain, "
        "or boundary hazards.",
    ),
]

perspectives = await parallel(  # noqa: F821
    seats,
    lambda item: agent(  # noqa: F821
        item[2],
        schema=SEAT_SCHEMA,
        role=item[0],
        type_name=item[1],
    ),
)

for idx, p in enumerate(perspectives, start=1):
    log(f"--- Seat #{idx} ({seats[idx - 1][0]}) [{p['evidence_grade']}] ---\n{json.dumps(p, indent=2)}")  # noqa: F821

phase("Phase 2: Disagreement Surfacing & Adjudicated Verdict")  # noqa: F821

verdict = await agent(  # noqa: F821
    f"{peer_brief}\n\nQuestion: {question}\n\n"
    f"Seat 1 (First-Principles): {json.dumps(perspectives[0])}\n"
    f"Seat 2 (Empirical Pragmatist): {json.dumps(perspectives[1])}\n"
    f"Seat 3 (Adversarial Red-Team): {json.dumps(perspectives[2])}\n\n"
    "Adjudicate by evidence tier (one verified E2/E3 proof outweighs two E0 opinions).",
    schema=VERDICT_SCHEMA,
    role="Council Chief Adjudicator",
    type_name="sota-deep-synthesizer",
)

kit.record_workflow_run(
    repo=repo_hint or "council-deliberation",
    workflow_id="council",
    done_summary=f"[{verdict['evidence_grade']}] {verdict['bluf_decision']}",
    verified_by="; ".join(verdict["verification_gate_commands"][:3]) or "council-adjudicated",
    next_priority=verdict["next_priority"],
)

out_text = json.dumps(verdict, indent=2)
log(out_text)  # noqa: F821
print(out_text)
