"""SOTA Early-Mover & 200/min Paper Attribution Adversarial Workflow (`run_workflow` Engine — Self-Bootstrapping).

Run with `Cwd="~/Documents/sota-mover-ranker"` (or defaults dynamically to `~/Documents/sota-mover-ranker`).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

peer_brief = kit.load_peer_brief("sota-mover-ranker")
log(peer_brief)  # noqa: F821

SYNTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "paper_fill_and_slippage_health": {"type": "string"},
        "verified_pre_travel_edge": {"type": "string"},
        "top_ucb_alpha_leaders": {"type": "string"},
        "falsifier_warnings_and_tightened_gates": {"type": "string"},
        "next_preregistered_prewall_hypothesis": {"type": "string"},
        "firewall_status": {"type": "string"},
    },
    "required": [
        "paper_fill_and_slippage_health",
        "verified_pre_travel_edge",
        "top_ucb_alpha_leaders",
        "falsifier_warnings_and_tightened_gates",
        "next_preregistered_prewall_hypothesis",
        "firewall_status",
    ],
}

phase("Parallel Bull/Attribution Specialists + Adversarial Red-Team Falsifier")  # noqa: F821

seats = [
    (
        "Pre-Travel Early-Mover Factor Specialist",
        "sota-deep-synthesizer",
        f"{peer_brief}\n\nRead cache/goal_loop/GOAL_LOOP_REPORT.md and project only top 8 movers + "
        "ranked_lists.strict_pre_travel_early from cache/latest_scan.json in ~/Documents/sota-mover-ranker. "
        "Summarize in <=5 concise bullets: (1) Active Pre-Wall Champion & OOS +8%/3d Lift (strictly <=2026-10-15), "
        "(2) Live Pre-Travel Early-Stage common-stock candidates catching volume breaks before price extension, and "
        "(3) Concrete microstructure factor threshold insight (vol_z, Pocket Pivot, close_pos, BJZZ dark-pool, OFI). "
        "Never print account IDs, keys, or dollar balances.",
    ),
    (
        "200/min Paper Execution & Slippage Attribution Analyst",
        "sota-deep-synthesizer",
        f"{peer_brief}\n\nRead cache/paper_broker_e2e/REAL_PAPER_PERFORMANCE_MANIFEST.md and "
        "cache/goal_loop/PAPER_FACTOR_GOAL_MANIFEST.md in ~/Documents/sota-mover-ranker. Summarize in <=5 concise bullets: "
        "(1) Total reconciled sota-* orders, fills, and realized limit slippage (bps), "
        "(2) Top Promoted Alpha Leaders by Empirical-Bayes UCB weight & Open MTM% / Closed Mean R across all 10 strategies, and "
        "(3) Which noisy strategies had close_pos / OFI / stop_atr_mult tightened (confirming ADR-0022 <=2.00% cap and Never-Gated >=0.40x). "
        "Never print account IDs, keys, or dollar balances.",
    ),
    (
        "Adversarial Microstructure & Overfitting Falsifier",
        "sota-falsifier",
        f"{peer_brief}\n\nInspect cache/goal_loop/GOAL_LOOP_REPORT.md, cache/goal_loop/PAPER_FACTOR_GOAL_MANIFEST.md, "
        "cache/paper_broker_e2e/REAL_PAPER_PERFORMANCE_MANIFEST.md, and ranked_lists.strict_pre_travel_early in cache/latest_scan.json "
        "in ~/Documents/sota-mover-ranker. Challenge every optimistic claim in <=5 bullets: "
        "(1) Sample-size & date-clustering fragility (flag any promoted strategy with <30 closed fills or single-day concentration), "
        "(2) Multiple-testing DSR/PBO & 2x-slippage survival risk, "
        "(3) Wide-NBBO spread / adverse-selection / after-hours liquidity traps on current candidates, and "
        "(4) Any residual ETF/ADR/$10 SPAC/SEC S-3 or 424B5 dilution exposure. "
        "Never print account IDs, keys, or dollar balances.",
    ),
]

audits = await parallel(  # noqa: F821
    seats,
    lambda item: agent(  # noqa: F821
        item[2],
        schema={"type": "string"},
        role=item[0],
        type_name=item[1],
    ),
)

for idx, report in enumerate(audits, start=1):
    log(f"--- Specialist Report #{idx} ---\n{report}")  # noqa: F821

phase("Adversarial Adjudication & Compounding Goal Synthesis")  # noqa: F821

synthesis = await agent(  # noqa: F821
    f"{peer_brief}\n\nAdjudicate the Bull Factor Specialist and Paper Attribution reports against the Adversarial Falsifier "
    "for Goal `G_SOTA_200RPM_PAPER_FACTOR_COMPOUNDING` into an evidence-graded (E0-E4) executive action brief:\n\n"
    f"Report 1 (Early-Mover Factors):\n{audits[0]}\n\n"
    f"Report 2 (Real Paper Attribution):\n{audits[1]}\n\n"
    f"Report 3 (Adversarial Red-Team Falsifier):\n{audits[2]}",
    schema=SYNTHESIS_SCHEMA,
    role="Early-Mover Paper Goal Adjudicator",
    type_name="sota-deep-synthesizer",
)

kit.record_workflow_run(
    repo="sota-mover-ranker",
    workflow_id="early-mover-compounding",
    done_summary=f"{synthesis['paper_fill_and_slippage_health']} | {synthesis['top_ucb_alpha_leaders']}",
    verified_by="3-agent adversarial workflow (sota-deep-synthesizer + sota-falsifier)",
    open_risks=synthesis["falsifier_warnings_and_tightened_gates"],
    next_priority=synthesis["next_preregistered_prewall_hypothesis"],
)

out_text = json.dumps(synthesis, indent=2)
log(out_text)  # noqa: F821
print(out_text)
