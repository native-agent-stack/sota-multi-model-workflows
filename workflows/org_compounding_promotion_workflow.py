# ruff: noqa: E402, F704, F821, PLE1142
"""SOTA 5-Stage Quantitative Compounding & Org Promotion Workflow (`v3.0.0`).

Orchestrates Stage 1 (`meridian` Sim) -> Stage 2 (`<= 2026-10-15` Pre-Wall HLZ/CPCV/DSR) ->
Stage 3 (`200/min` Alpaca + `3,000/min` IBKR `:4002` Paper) -> Stage 4 (`sota-compounding-lab`
Empirical-Bayes Shrinkage) -> Stage 5 (`sota-dynamic-trail-c` + `sota-private-vault` SHA-256 Manifest).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = kit.get_workflow_args(globals())
candidate_id = str(cfg.get("strategy_id") or "SOTA_CANDIDATE_AUDIT")
target_lane = str(cfg.get("broker_lane") or "ALPACA_PAPER")
peer_brief = kit.load_peer_brief("sota-compounding-lab")
preflight = kit.run_preflight_summary(live_org=bool(cfg.get("live_org", False)))

log(f"{peer_brief}\nPreflight: {json.dumps(preflight)}")

STAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "stage_passed": {"type": "boolean"},
        "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
        "metrics_summary": {"type": "string"},
        "blocking_gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["stage_passed", "evidence_grade", "metrics_summary", "blocking_gaps"],
}

phase("Phase 1: Parallel 5-Stage Lifecycle & Adversarial Falsification Audit")

audits = await parallel(
    [
        (
            "Stage 1-2 Sim & Pre-Wall Statistical Auditor",
            "sota-falsifier",
            f"{peer_brief}\n\nCandidate: `{candidate_id}` | Target Lane: `{target_lane}`\n"
            "Verify Stage 1 queue-fill parity (`~/Documents/meridian`) and Stage 2 pre-wall isolation "
            "(`<= 2026-10-15`, HLZ `t*(N)`, `CPCV`, `DSR >= 0.95`, 2x square-root impact survival). "
            "Never print credentials, account IDs, or dollar balances.",
        ),
        (
            "Stage 3-5 Paper Execution, EB Shrinkage & Firewall Verifier",
            "sota-code-verifier",
            f"{peer_brief}\n\nCandidate: `{candidate_id}` | Target Lane: `{target_lane}`\n"
            "Run `uv run pytest -q` in `~/Documents/sota-compounding-lab` and verify `ADR-0022 <= 2.00%` stops, "
            "paper-only routing (`PA...` <=200/min or `DU...` `:4002` <=3,000/min), Empirical-Bayes UCB shrinkage, "
            "and 4-invariant `sota-org-doctor` compliance. Never print credentials or account IDs.",
        ),
    ],
    lambda item: agent(item[2], schema=STAGE_SCHEMA, role=item[0], type_name=item[1]),
)

PROMOTION_SCHEMA = {
    "type": "object",
    "properties": {
        "approved_for_paper_manifest": {"type": "boolean"},
        "stage_reached": {"type": "string"},
        "executive_verdict": {"type": "string"},
        "next_action": {"type": "string"},
    },
    "required": ["approved_for_paper_manifest", "stage_reached", "executive_verdict", "next_action"],
}

phase("Phase 2: Final Promotion Manifest Adjudication")

decision = await agent(
    f"{peer_brief}\n\nCandidate `{candidate_id}` ({target_lane}):\n"
    f"Stage 1-2 Falsifier: {json.dumps(audits[0])}\n"
    f"Stage 3-5 Verifier: {json.dumps(audits[1])}\n\n"
    "Approve ONLY if both Stage 1-2 and Stage 3-5 passed with zero blocking gaps.",
    schema=PROMOTION_SCHEMA,
    role="5-Stage Promotion Gate Judge",
    type_name="sota-deep-synthesizer",
)

kit.record_workflow_run(
    repo="sota-compounding-lab",
    workflow_id="org-compounding-promotion",
    done_summary=f"{candidate_id} -> approved={decision['approved_for_paper_manifest']} ({decision['stage_reached']})",
    verified_by=f"falsifier={audits[0]['stage_passed']}; verifier={audits[1]['stage_passed']}",
    open_risks="; ".join((audits[0]["blocking_gaps"] + audits[1]["blocking_gaps"])[:3]) or "none",
    next_priority=decision["next_action"],
)

out_text = json.dumps({"preflight": preflight, "audits": audits, "decision": decision}, indent=2)
log(out_text)
print(out_text)
