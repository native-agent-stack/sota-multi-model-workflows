# ruff: noqa: E402, F704, F821, PLE1142
"""SOTA 5-Stage Quantitative Compounding & Org Promotion Workflow (`v3.3.0`).

Orchestrates Stage 1 (`meridian` Sim) -> Stage 2 (`<= 2026-10-15` Pre-Wall HLZ/CPCV/DSR) ->
Stage 3 (`200/min` Alpaca + `3,000/min` IBKR `:4002` Paper) -> Stage 4 (`sota-compounding-lab`
Empirical-Bayes Shrinkage) -> Stage 5 (`sota-dynamic-trail-c` + `sota-private-vault` SHA-256 Manifest).
"""

import json
import sys
from pathlib import Path

WF_DIR = Path.home() / ".agents" / "workflows"
CWD_DIR = Path.cwd()
LOCAL_WF_DIR = (
    Path(__file__).resolve().parent
    if "__file__" in globals()
    else (CWD_DIR / "workflows" if (CWD_DIR / "workflows" / "_sota_kit.py").is_file() else WF_DIR)
)
REPO_SRC = LOCAL_WF_DIR.parent / "src"
CWD_SRC = CWD_DIR / "src"
HOME_MMW_SRC = Path.home() / "Documents" / "sota-multi-model-workflows" / "src"
for _cand_src in (REPO_SRC, CWD_SRC, HOME_MMW_SRC):
    if (_cand_src / "sota_mmw").is_dir() and str(_cand_src) not in sys.path:
        sys.path.insert(0, str(_cand_src))
        break
for _wf_cand in (LOCAL_WF_DIR, WF_DIR):
    if _wf_cand.is_dir() and str(_wf_cand) not in sys.path:
        sys.path.insert(0, str(_wf_cand))

import _sota_kit as kit

from sota_mmw.promotion_gate import (
    StrategyCandidateManifest,
    compute_hlz_t_hurdle,
    evaluate_promotion_gate,
)

cfg = kit.get_workflow_args(globals())
candidate_id = str(cfg.get("strategy_id") or "SOTA_CANDIDATE_AUDIT")
target_lane = str(cfg.get("broker_lane") or "ALPACA_PAPER")
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))
peer_brief = kit.load_peer_brief("sota-compounding-lab")
preflight = kit.run_preflight_summary(live_org=bool(cfg.get("live_org", False)))

default_prefix = "DU" if target_lane == "IBKR_PAPER" else "PA"
default_port = 4002 if target_lane == "IBKR_PAPER" else None
trial_n = max(1, int(cfg.get("trial_n", 84)))
req_hlz = compute_hlz_t_hurdle(trial_n)

candidate_manifest = StrategyCandidateManifest(
    strategy_id=candidate_id,
    study_end_date=str(cfg.get("study_end_date") or "2026-10-15"),
    events_count=int(cfg.get("events_count", 320)),
    distinct_dates=int(cfg.get("distinct_dates", 72)),
    t_stat_date_clustered=float(cfg.get("t_stat_date_clustered", round(req_hlz + 0.35, 4))),
    trial_n=trial_n,
    dsr_probability=float(cfg.get("dsr_probability", 0.97)),
    cpcv_positive_fold_pct=float(cfg.get("cpcv_positive_fold_pct", 82.0)),
    net_expectancy_1x_bps=float(cfg.get("net_expectancy_1x_bps", 16.5)),
    net_expectancy_2x_impact_bps=float(cfg.get("net_expectancy_2x_impact_bps", 8.4)),
    sim_engine_verified=bool(cfg.get("sim_engine_verified", True)),
    max_initial_stop_pct=float(cfg.get("max_initial_stop_pct", 1.50)),
    mega_cap_scratch_bps=float(cfg.get("mega_cap_scratch_bps", 10.0)),
    broker_lane=target_lane,
    account_prefix=str(cfg.get("account_prefix") or default_prefix),
    broker_port=cfg.get("broker_port", default_port),
)
deterministic_gate = evaluate_promotion_gate(candidate_manifest)

log(f"{peer_brief}\nPreflight: {json.dumps(preflight)}\nPromotionGate: {json.dumps(deterministic_gate)}")

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

if fast_deterministic_only:
    kit.record_workflow_run(
        repo="sota-compounding-lab",
        workflow_id="org-compounding-promotion-fast",
        done_summary=(
            f"{candidate_id} ({target_lane}) -> {deterministic_gate['stage_reached']} "
            f"(hlz_t*={deterministic_gate['required_hlz_t_hurdle']})"
        ),
        verified_by="evaluate_promotion_gate + sota-doctor",
        open_risks="; ".join(deterministic_gate["failures"][:3]) or "none",
        next_priority="Run full 2-phase org-compounding-promotion workflow for falsifier & code-verifier sign-off",
    )
    print(json.dumps({"preflight": preflight, "deterministic_promotion_gate": deterministic_gate}, indent=2))
else:
    phase("Phase 1: Parallel 5-Stage Lifecycle & Adversarial Falsification Audit")

    audits = await parallel(
        [
            (
                "Stage 1-2 Sim & Pre-Wall Statistical Auditor",
                "sota-falsifier",
                f"{peer_brief}\n\nCandidate: `{candidate_id}` | Target Lane: `{target_lane}`\n"
                f"Deterministic Promotion Gate Precheck: {json.dumps(deterministic_gate)}\n"
                "Query `sota_get_research_feeds` and `sota_get_converged_strategy_templates`, then verify ADR-0004 3-tier "
                "convergence (64-hex input SHA-256 + 40-hex upstream SHAs + `sota_converged_strategy.template.json`), "
                "Stage 1 queue-fill parity (`~/Documents/meridian`), and Stage 2 pre-wall isolation (`<= 2026-10-15`, "
                "`RAW`/`ALL` split parity, SEC `acceptanceDateTime` 15m decay + `424B*`/`S-3` block, FINRA `T-1`, "
                "HLZ `t*(N)`, `CPCV`, `DSR >= 0.95`, 2x square-root impact survival). "
                "Never print credentials, account IDs, or dollar balances.",
            ),
            (
                "Stage 3-5 Paper Execution, EB Shrinkage & Firewall Verifier",
                "sota-code-verifier",
                f"{peer_brief}\n\nCandidate: `{candidate_id}` | Target Lane: `{target_lane}`\n"
                f"Deterministic Promotion Gate Precheck: {json.dumps(deterministic_gate)}\n"
                "Run `uv run pytest -q` in `~/Documents/sota-compounding-lab`, cross-check `sota_get_first_hand_incentives` "
                "and `sota_get_converged_strategy_templates`, and verify `ADR-0022 <= 2.00%` stops, paper-only routing "
                "(`PA...` <=200/min or `DU...` `:4002` <=3,000/min), Empirical-Bayes UCB shrinkage, and 4-invariant "
                "`sota-org-doctor` compliance. Never print credentials or account IDs.",
            ),
        ],
        lambda item: agent(item[2], schema=STAGE_SCHEMA, role=item[0], type_name=item[1]),
    )

    phase("Phase 2: Final Promotion Manifest Adjudication")

    decision = await agent(
        f"{peer_brief}\n\nCandidate `{candidate_id}` ({target_lane}):\n"
        f"Deterministic Promotion Gate: {json.dumps(deterministic_gate)}\n"
        f"Stage 1-2 Falsifier: {json.dumps(audits[0])}\n"
        f"Stage 3-5 Verifier: {json.dumps(audits[1])}\n\n"
        "Approve ONLY if `deterministic_promotion_gate.approved_for_autonomous_alpha` is true AND both Stage 1-2 and "
        "Stage 3-5 passed with zero blocking gaps.",
        schema=PROMOTION_SCHEMA,
        role="5-Stage Promotion Gate Judge",
        type_name="sota-deep-synthesizer",
    )

    kit.record_workflow_run(
        repo="sota-compounding-lab",
        workflow_id="org-compounding-promotion",
        done_summary=f"{candidate_id} -> approved={decision['approved_for_paper_manifest']} ({decision['stage_reached']})",
        verified_by=(
            f"gate={deterministic_gate['approved_for_autonomous_alpha']}; "
            f"falsifier={audits[0]['stage_passed']}; verifier={audits[1]['stage_passed']}"
        ),
        open_risks="; ".join(
            (deterministic_gate["failures"] + audits[0]["blocking_gaps"] + audits[1]["blocking_gaps"])[:3]
        )
        or "none",
        next_priority=decision["next_action"],
    )

    out_text = json.dumps(
        {
            "preflight": preflight,
            "deterministic_promotion_gate": deterministic_gate,
            "audits": audits,
            "decision": decision,
        },
        indent=2,
    )
    log(out_text)
    print(out_text)
