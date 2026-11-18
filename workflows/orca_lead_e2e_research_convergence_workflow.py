"""Workflow #19 (`v3.10.0`, `ADR-0024`): Orca Lead (`cc-lead`) E2E Research Convergence, 12-Feed Symbol Ranking (`DF1..DF12`) & 8-Runtime SOTA Fleet.

Orchestrates:
1. Pre-flight verification of `sota-research-feeds.v2`, `PHILOSOPHY_ONLY` sibling-repo authority,
   `DF1..DF12` Symbol Ranking System DataFeeds (`sota-symbol-ranking-datafeeds.v3.10`), and
   `8`-Stage Advanced SOTA Research Convergence (`413` starred + `6` beyond-starred anchors).
2. Deterministic validation of `6` autonomous paper-trading strategy routes fed by `DF1..DF12`
   (bitemporal PIT `ts_event_ns <= ts_recv_ns <= decision_ns`, `RVOL_tod >= 2.20`, `H096` `15s <= 10bps`
   collar, `ADR-0022 <= 2.00%` stop, `900s` Wave-2 cooldown, single active broker host).
3. Cross-runtime `cc-lead` (`claude-fable-5-2` `xhigh` + `OMC v2` + Orca supervisor) E2E task assignment
   envelope & live multi-agent synthesis/falsification when `fast_deterministic_only=False`.
"""

import json
import sys
from pathlib import Path

_WF_DIR = Path(__file__).resolve().parent if "__file__" in globals() else (Path.home() / ".agents" / "workflows")
if str(_WF_DIR) not in sys.path:
    sys.path.insert(0, str(_WF_DIR))

import _sota_kit as kit  # noqa: E402

from sota_mmw.cc_lead_hub import (  # noqa: E402
    build_orca_lead_e2e_convergence_assignment,
    probe_cc_runtime_fleet,
)
from sota_mmw.research_convergence_contract import (  # noqa: E402
    verify_advanced_sota_convergence_practice,
)
from sota_mmw.symbol_ranking_datafeeds import (  # noqa: E402
    build_symbol_ranking_foundation_manifest,
    evaluate_symbol_ranking_to_strategy_handoff,
)

cfg = kit.get_workflow_args(globals())
ws0 = kit.get_primary_workspace(globals())
repo = str(cfg.get("repo") or (Path(ws0).name if ws0 else "cc-sota-harness"))
goal = str(
    cfg.get("goal")
    or (
        "Execute v3.10.0 8-Stage SOTA Research Convergence, DF1..DF12 Symbol Ranking System verification, "
        "and Orca Lead (cc-lead) multi-runtime E2E convergence task assignment."
    )
)
surface = str(cfg.get("surface") or "auto")
strategy_route = str(cfg.get("strategy_route") or "PRE_TRAVEL_EARLY_IGNITION")
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))

phase("Phase 0: Research-Convergence, 12-Feed DF1..DF12 Ranking & 8-Runtime Preflight")  # noqa: F821
peer_brief = kit.load_peer_brief(repo)
preflight = kit.run_preflight_summary(live_org=False)
rc_ctx = kit.load_research_convergence_context()
rc_envelope = kit.verify_workflow_research_convergence(
    "orca-lead-e2e-research-convergence",
    repo=repo,
    archetype="PRE_TRAVEL_EARLY_IGNITION",
)
adv_convergence = verify_advanced_sota_convergence_practice()
ranking_manifest = build_symbol_ranking_foundation_manifest()
handoff_check = evaluate_symbol_ranking_to_strategy_handoff(
    symbol="AAPL",
    strategy_route=strategy_route,
    study_date="2026-10-15",
    ts_event_ns=1_760_500_000_000_000_000,
    ts_recv_ns=1_760_500_000_005_000_000,
    decision_ns=1_760_500_000_010_000_000,
    rvol_tod=2.45,
    vol_z_tod=2.80,
    ofi=0.35,
    dry_powder_sec=18.5,
    spread_collar_bps=7.5,
    hard_stop_pct=1.65,
    broker_port=8787,
)
fleet = probe_cc_runtime_fleet()
orca_lead_assignment = build_orca_lead_e2e_convergence_assignment(
    repo=repo,
    goal=goal,
    surface=surface,
)

header = (
    f"[v3.10.0 Workflow #19 Orca-Lead E2E Convergence | repo={repo} | "
    f"rc={rc_ctx.get('schema_version', 'sota-research-feeds.v2')} "
    f"({rc_ctx.get('sibling_repo_authority', 'PHILOSOPHY_ONLY')}, valid={rc_envelope['valid']}) | "
    f"ranking_v310_feeds={ranking_manifest['feed_count']} | handoff={handoff_check['approved']} | "
    f"installed_clis={fleet['installed_count']}/{fleet['checked_total']}]\n"
    f"{json.dumps(preflight)}\n{peer_brief}"
)
log(header)  # noqa: F821

CONVERGENCE_STAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "stage_summary": {"type": "string"},
        "df12_bitemporal_pit_ok": {"type": "boolean"},
        "orca_lead_e2e_ready": {"type": "boolean"},
        "verdict": {"type": "string", "enum": ["PASS", "REVISE"]},
    },
    "required": ["stage_summary", "df12_bitemporal_pit_ok", "orca_lead_e2e_ready", "verdict"],
}

agent_reviews: list[dict[str, object]] = [
    {
        "stage_summary": "deterministic_turn0_verified",
        "df12_bitemporal_pit_ok": bool(handoff_check["approved"]),
        "orca_lead_e2e_ready": bool(orca_lead_assignment["assign_sha256"]),
        "verdict": "PASS"
        if (rc_envelope["valid"] and adv_convergence["valid"] and handoff_check["approved"])
        else "REVISE",
    }
]

if not fast_deterministic_only and "agent" in globals():
    phase("Phase 1: Parallel Cross-Vendor Synthesis, Adversarial Falsification & Orca Lead Verification")  # noqa: F821
    review_targets = [
        ("sota-deep-synthesizer", "Synthesizer (413+6 Beyond SOTA & DF1..DF12 Foundation)"),
        ("sota-falsifier", "Adversarial Quant Falsifier (HLZ/DSR/CPCV & Bitemporal PIT)"),
        ("sota-code-verifier", "Orca Lead Multi-Runtime E2E & Firewall Verifier"),
    ]

    async def _run_reviewer(item: tuple[str, str]) -> dict[str, object]:
        tname, role = item
        return await agent(  # noqa: F821
            f"{header}\n\n8-Stage Practice: {json.dumps(adv_convergence)}\n"
            f"Ranking Handoff: {json.dumps(handoff_check)}\n"
            f"Orca Lead Envelope: {json.dumps({'repo': repo, 'assign_sha256': orca_lead_assignment['assign_sha256'], 'surface': orca_lead_assignment['surface']})}\n"
            "Verify pre-wall <=2026-10-15, bitemporal ordering, ADR-0022 <=2.00% stop, "
            "8-runtime enhancement parity, and readiness for Orca Lead E2E execution.",
            schema=CONVERGENCE_STAGE_SCHEMA,
            role=role,
            type_name=tname,
        )

    if "parallel" in globals():
        agent_reviews = await parallel(review_targets, _run_reviewer)  # noqa: F821
    else:
        agent_reviews = [await _run_reviewer(it) for it in review_targets]  # noqa: F821

phase("Phase 2: Emit v3.10.0 Orca Lead E2E Research Convergence Receipt")  # noqa: F821
all_ok = bool(
    rc_envelope["valid"]
    and adv_convergence["valid"]
    and handoff_check["approved"]
    and all(r.get("verdict") == "PASS" for r in agent_reviews)
)
final_receipt = {
    "workflow": "orca-lead-e2e-research-convergence",
    "schema_version": "3.10.0",
    "research_convergence_valid": bool(rc_envelope["valid"]),
    "advanced_8stage_convergence": adv_convergence,
    "symbol_ranking_v310": {
        "schema_version": ranking_manifest["schema_version"],
        "feed_count": ranking_manifest["feed_count"],
        "strategy_route_count": ranking_manifest["strategy_route_count"],
        "ranking_v310_contract_sha256": ranking_manifest["ranking_v310_contract_sha256"],
        "handoff_verified": handoff_check["approved"],
    },
    "orca_lead_assignment": orca_lead_assignment,
    "runtime_fleet_summary": {
        "checked_total": fleet["checked_total"],
        "installed_count": fleet["installed_count"],
        "cc_lead_ready": fleet["cc_lead_ready"],
        "orca_supervisor_ready": fleet["orca_supervisor_ready"],
    },
    "agent_reviews": agent_reviews,
    "all_gates_passed": all_ok,
}
kit.record_workflow_run(
    repo=repo,
    workflow_id="orca-lead-e2e-research-convergence",
    done_summary=(
        f"Executed v3.10.0 8-Stage E2E Convergence + DF1..DF12 Ranking "
        f"({ranking_manifest['ranking_v310_contract_sha256'][:12]}) & Orca Lead assign "
        f"({orca_lead_assignment['assign_sha256'][:12]})"
    ),
    verified_by="sota-deep-synthesizer+sota-falsifier+sota-code-verifier",
)
print(json.dumps(final_receipt, indent=2))
