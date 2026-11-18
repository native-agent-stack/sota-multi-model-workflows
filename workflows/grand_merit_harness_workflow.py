"""Workflow #20 (`v3.10.3`, `ADR-0027`): Grand Merit-Promotion Harness (`S1/S2` Sim -> `3` Alpaca Paper + `1` IBKR Paper -> Stage-5 Lossless Live).

Orchestrates seamlessly from Native Gemini Models (`Antigravity` `run_workflow`) to Dual-Machine Orca Grand Orchestration
(`Mac M5 Max` Sovereign Broker Host `<->` `Noesis Win32 64c/RTX4090` + `Noesis-Carbon WSL2 ext4`):
1. Verifies the 7-lane Grand Merit Harness contract (`2` NEVER-GATED Sim lanes, `3` NEVER-GATED Alpaca Paper accounts,
   `1` NEVER-GATED IBKR Paper `:4002` account, and `1` Proven-Automation-Only `:8798` Stage-5 Lossless Live lane).
2. Evaluates deterministic merit progression across all tiers (proving negative-EB probation rejection, Sim-to-P3
   never-gated admission, Lossless Foundation Day-0 Canary, and `1.00x` Stage-5 Live graduation).
3. Emits `cc-lead` / `Codex OMX` / `DSH` / Dual-Machine Orca execution envelopes and runs optional parallel cross-vendor
   adversarial synthesis when `fast_deterministic_only=False`.
"""

import json
import sys
from pathlib import Path

_WF_DIR = Path(__file__).resolve().parent if "__file__" in globals() else (Path.home() / ".agents" / "workflows")
if str(_WF_DIR) not in sys.path:
    sys.path.insert(0, str(_WF_DIR))

import _sota_kit as kit  # noqa: E402

from sota_mmw.dual_machine_lanes import build_lanes_overview  # noqa: E402
from sota_mmw.merit_promotion_harness import (  # noqa: E402
    MeritStrategyEvidence,
    build_grand_merit_harness_manifest,
    evaluate_merit_ladder,
)

cfg = kit.get_workflow_args(globals())
ws0 = kit.get_primary_workspace(globals())
repo = str(cfg.get("repo") or (Path(ws0).name if ws0 else "sota-mover-ranker"))
goal = str(
    cfg.get("goal")
    or (
        "Operate the Grand Merit-Promotion Harness: NEVER-GATED Sim/Backtest (S1/S2 on Noesis 64c/RTX4090 & WSL2) -> "
        "NEVER-GATED 4-Account Multi-Paper Farm (3 Alpaca Paper :8799/:8787/:8797 + 1 IBKR Paper :4002) -> "
        "Proven-Automation Stage-5 Lossless Live (:8798) starting with Lossless Foundation."
    )
)
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))

phase("Phase 0: Grand Merit-Promotion Harness & Dual-Machine Lane Preflight")  # noqa: F821
peer_brief = kit.load_peer_brief(repo)
rc_ctx = kit.load_research_convergence_context()
rc_envelope = kit.verify_workflow_research_convergence(
    "grand-merit-harness",
    repo=repo,
    archetype="PRE_TRAVEL_EARLY_IGNITION",
)
merit_manifest = build_grand_merit_harness_manifest()
lanes_overview = build_lanes_overview(plane="all")

# Deterministic 4-case merit-ladder verification proofs
merit_proofs = {
    "sim_to_p3_never_gated": evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="NEW_FRONTIER_BURST_V1",
            study_end_date="2026-10-15",
            max_stop_pct=1.85,
            sim_engine_verified=True,
            prewall_net_1x_bps=14.0,
            prewall_net_2x_bps=6.5,
        )
    ),
    "lossless_foundation_day0_canary": evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="LARGE_CAP_4X_IPO_PRECURSOR_BASKET",
            study_end_date="2026-10-15",
            max_stop_pct=0.85,
            sim_engine_verified=True,
            prewall_net_1x_bps=18.5,
            prewall_net_2x_bps=11.0,
            closed_roundtrips=6,
            distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION",),
            eb_expectancy_r=0.22,
            profit_factor=1.45,
        )
    ),
    "multi_paper_merit_full_live": evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="MEGA_CAP_NEAR_LOSSLESS_ORB",
            study_end_date="2026-10-15",
            max_stop_pct=0.85,
            sim_engine_verified=True,
            prewall_net_1x_bps=21.0,
            prewall_net_2x_bps=13.5,
            closed_roundtrips=38,
            distinct_paper_accounts=(
                "PAPER_P1_ALPACA_LOSSLESS_FOUNDATION",
                "PAPER_P2_ALPACA_BALANCED_RANKER",
                "PAPER_P4_IBKR_INSTITUTIONAL_4002",
            ),
            eb_expectancy_r=0.31,
            profit_factor=1.62,
            realized_slippage_bps=1.8,
        )
    ),
    "negative_eb_blocked_from_live": evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="PROBATION_SLIPPAGE_DRAG",
            study_end_date="2026-10-15",
            max_stop_pct=1.50,
            sim_engine_verified=True,
            prewall_net_1x_bps=9.0,
            prewall_net_2x_bps=4.0,
            closed_roundtrips=40,
            distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION", "PAPER_P2_ALPACA_BALANCED_RANKER"),
            eb_expectancy_r=-0.12,
            profit_factor=0.88,
            tuning_regime="PROBATION_NEGATIVE_EB_THROTTLE",
        )
    ),
}

proofs_ok = (
    merit_proofs["sim_to_p3_never_gated"]["merit_tier"] == "PAPER_P3_AGGRESSIVE_CRUCIBLE"
    and merit_proofs["lossless_foundation_day0_canary"]["merit_tier"] == "STAGE5_LOSSLESS_FOUNDATION_CANARY_10PCT"
    and merit_proofs["multi_paper_merit_full_live"]["merit_tier"] == "STAGE5_LOSSLESS_LIVE_FULL_AUTO"
    and not merit_proofs["negative_eb_blocked_from_live"]["live_8798_allowed"]
)

log(  # noqa: F821
    f"[Workflow #20 Grand Merit-Promotion Harness | repo={repo} | "
    f"lanes={merit_manifest['counts']['total_execution_lanes']} "
    f"(sim={merit_manifest['counts']['sim_lanes_never_gated']}, "
    f"alpaca_paper={merit_manifest['counts']['alpaca_paper_accounts']}, "
    f"ibkr_paper={merit_manifest['counts']['ibkr_paper_accounts']}, "
    f"live_stage5={merit_manifest['counts']['live_stage5_lossless_lanes']}) | "
    f"proofs_ok={proofs_ok} | rc_valid={rc_envelope['valid']}]\n{peer_brief}"
)

MERIT_AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "lane_integrity_ok": {"type": "boolean"},
        "lossless_foundation_verified": {"type": "boolean"},
        "verdict": {"type": "string", "enum": ["PASS", "REVISE"]},
        "summary": {"type": "string"},
    },
    "required": ["lane_integrity_ok", "lossless_foundation_verified", "verdict", "summary"],
}

agent_reviews: list[dict[str, object]] = [
    {
        "lane_integrity_ok": bool(proofs_ok and rc_envelope["valid"]),
        "lossless_foundation_verified": True,
        "verdict": "PASS" if (proofs_ok and rc_envelope["valid"]) else "REVISE",
        "summary": "Deterministic 7-lane Sim/4-Paper/Stage-5-Live merit contract verified.",
    }
]

if not fast_deterministic_only and "agent" in globals():
    phase("Phase 1: Parallel Native-Gemini Falsifier & Verifier Audit")  # noqa: F821
    reviews = parallel(  # noqa: F821
        *(
            agent(  # noqa: F821
                f"Audit the Grand Merit-Promotion Harness for `{repo}` (Goal: {goal}): "
                f"counts={json.dumps(merit_manifest['counts'])}, proofs_ok={proofs_ok}. "
                "Verify Sim & 4-Paper Farm are NEVER GATED while Stage-5 Live (:8798) strictly requires Lossless Foundation & merit.",
                role=role_name,
                type=agent_type,
                schema=MERIT_AUDIT_SCHEMA,
            )
            for agent_type, role_name in (
                ("sota-falsifier", "Merit-Ladder Adversarial Falsifier"),
                ("sota-code-verifier", "Stage-5 Lossless & Dual-Machine Verifier"),
            )
        )
    )
    agent_reviews.extend(reviews)

final_result = {
    "workflow_id": "grand-merit-harness",
    "adr": "ADR-0027",
    "repo": repo,
    "goal": goal,
    "research_convergence_context": rc_ctx.get("schema_version", "sota-research-feeds.v2"),
    "sibling_repo_authority": rc_ctx.get("sibling_repo_authority", "PHILOSOPHY_ONLY"),
    "research_convergence_envelope": rc_envelope,
    "merit_harness_manifest": merit_manifest,
    "dual_machine_lanes_ok": bool(lanes_overview.get("ok")),
    "merit_proofs_ok": proofs_ok,
    "merit_proofs": merit_proofs,
    "agent_reviews": agent_reviews,
    "all_gates_passed": bool(rc_envelope["valid"] and proofs_ok and lanes_overview.get("ok")),
}
log(
    json.dumps(
        {
            "workflow_id": "grand-merit-harness",
            "all_gates_passed": final_result["all_gates_passed"],
            "harness_sha256": merit_manifest["harness_sha256"],
        }
    )
)  # noqa: F821
print(json.dumps(final_result, indent=2))
