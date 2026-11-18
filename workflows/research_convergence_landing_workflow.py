# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA `run_workflow` (`v3.3.0` #13): End-to-End Research-Convergence, 7-Feed PIT & Strategy Landing Pipeline.

Orchestrates 3-tier `ADR-0004` / `ADR-0011` Research-Convergence across:
1. Phase 1: Parallel `ADR-0004` Source-of-Truth, 18-Repo Upstream Pin & 7-Feed `sota-research-feeds.v2` PIT Recon
2. Phase 2: Converged Strategy Template Scaffolding & Pre-Wall (`<= 2026-10-15`) Sim/Backtest Execution
3. Phase 3: Parallel Adversarial Falsification (`RAW`/`ALL`, SEC `acceptanceDateTime`, FINRA `T-1`, HLZ/CPCV/DSR, 2x impact) & Code Gate
4. Phase 4: Paper-Lane Manifest Landing (`sota-mover-ranker` `:8787`, `sota-dynamic-trail-c` `:8799`, `astrolabe` `:4002`) & Peer-Bus Receipt
"""

import hashlib
import json
import re
import sys
from pathlib import Path

WF_DIR = Path.home() / ".agents" / "workflows"
LOCAL_WF_DIR = Path(__file__).resolve().parent
REPO_SRC = LOCAL_WF_DIR.parent / "src"
HOME_MMW_SRC = Path.home() / "Documents" / "sota-multi-model-workflows" / "src"
ACTIVE_WF_DIR = LOCAL_WF_DIR if (LOCAL_WF_DIR / "_sota_kit.py").is_file() else WF_DIR
ACTIVE_MMW_SRC = REPO_SRC if (REPO_SRC / "sota_mmw").is_dir() else HOME_MMW_SRC
for _p_dir in (ACTIVE_MMW_SRC, ACTIVE_WF_DIR):
    if _p_dir.is_dir() and str(_p_dir) not in sys.path:
        sys.path.insert(0, str(_p_dir))

import _sota_kit as kit

from sota_mmw.research_convergence_contract import (
    CANONICAL_DATAFEEDS,
    CANONICAL_STRATEGY_ARCHETYPES,
    PRE_WALL_MAX_DATE,
    verify_research_convergence_claim,
)

cfg = kit.get_workflow_args(globals())
strategy_id = str(cfg.get("strategy_id") or "SOTA_CONVERGED_CANDIDATE_V1")
raw_archetype = str(cfg.get("archetype") or CANONICAL_STRATEGY_ARCHETYPES[0])
archetype = raw_archetype if raw_archetype in CANONICAL_STRATEGY_ARCHETYPES else CANONICAL_STRATEGY_ARCHETYPES[0]
target_repo = str(cfg.get("repo") or "sota-compounding-lab")
broker_lane = str(cfg.get("broker_lane") or "ALPACA_PAPER")
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))

peer_brief = kit.load_peer_brief(target_repo)
rc_context = kit.load_research_convergence_context()
preflight = kit.run_preflight_summary(live_org=False)

pins_md = Path.home() / "Documents" / "upstream" / "PINS.md"
discovered_pins: dict[str, str] = {}
if pins_md.is_file():
    for m_row in re.finditer(
        r"\|\s*`([^`/]+)/?`\s*\|[^|]+\|[^|]+\|\s*`([0-9a-f]{40})`\s*\|", pins_md.read_text("utf-8")
    ):
        discovered_pins[m_row.group(1)] = m_row.group(2)
if not discovered_pins:
    discovered_pins = {
        "alpaca-py": "c42add7c0a7026e2ead3ed64e76f4def2b99fda4",
        "edgartools": "574c2bd15f6c629bceef03b6550ea8ac8abf3473",
        "nautilus_trader": "da6b57aefdd62b44f675e434ffcfefca7f4025dd",
    }

seed_input_sha256 = hashlib.sha256(
    json.dumps(
        {
            "strategy_id": strategy_id,
            "archetype": archetype,
            "repo": target_repo,
            "broker_lane": broker_lane,
            "feeds": sorted(CANONICAL_DATAFEEDS.keys()),
            "pre_wall": PRE_WALL_MAX_DATE,
        },
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()

bootstrap_bundle = {
    "strategy_id": strategy_id,
    "archetype": archetype,
    "target_repo": target_repo,
    "broker_lane": broker_lane,
    "seed_input_sha256": seed_input_sha256,
    "upstream_pin_count": len(discovered_pins),
    "research_convergence": {
        "schema_version": rc_context["schema_version"],
        "source": rc_context["source"],
        "feed_count": rc_context["feed_count"],
        "canonical_datafeeds": rc_context["canonical_datafeeds"],
        "strategy_templates": rc_context["strategy_templates"],
        "mcp_tools": rc_context["mcp_tools"],
    },
    "preflight": preflight,
}
log(f"{peer_brief}\n{json.dumps(bootstrap_bundle, indent=2)}")

if fast_deterministic_only:
    fast_violations = verify_research_convergence_claim(
        input_sha256=seed_input_sha256,
        upstream_pins=discovered_pins,
        study_max_date=PRE_WALL_MAX_DATE,
        hard_stop_pct=1.50,
        evidence_grade="E4",
    )
    fast_out = {
        "bootstrap": bootstrap_bundle,
        "convergence_claim_valid": len(fast_violations) == 0,
        "violations": fast_violations,
    }
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="research-convergence-landing-fast",
        done_summary=(
            f"{strategy_id} ({archetype}) deterministic convergence valid={len(fast_violations) == 0} "
            f"feeds={rc_context['feed_count']} pins={len(discovered_pins)}"
        ),
        verified_by="verify_research_convergence_claim + load_research_convergence_context + sota-doctor",
        open_risks="; ".join(fast_violations) or "none",
        next_priority="Run full 4-phase research-convergence-landing workflow for pre-wall study & paper manifest",
    )
    print(json.dumps(fast_out, indent=2))
else:
    RECON_SCHEMA = {
        "type": "object",
        "properties": {
            "verified_facts": {"type": "array", "items": {"type": "string"}},
            "pit_or_pin_constraints": {"type": "array", "items": {"type": "string"}},
            "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
        },
        "required": ["verified_facts", "pit_or_pin_constraints", "evidence_grade"],
    }

    phase("Phase 1: Parallel ADR-0004 Source-of-Truth, 18-Repo Upstream Pin & 7-Feed PIT DataFeed Reconnaissance")

    recon_pair = await parallel(
        [
            (
                "ADR-0004 & 18-Repo Upstream Shelf Investigator",
                "sota-deep-synthesizer",
                f"{peer_brief}\n\nBootstrap:\n{json.dumps(bootstrap_bundle, indent=2)}\n"
                "Query `sota_shelf_search` and inspect `~/Documents/upstream/PINS.md` (read-only) plus "
                "`~/Documents/sota-compounding-lab/templates/sota_converged_strategy.template.json` and "
                "`~/Documents/trading-sota/strategies/_template/manifest.json`. Verify ADR-0004 3-tier SHA-256 input "
                "+ 40-hex upstream SHA pinning for this archetype.",
            ),
            (
                "7-Feed PIT DataFeed & First-Hand Catalyst Scout",
                "self",
                f"{peer_brief}\n\nBootstrap:\n{json.dumps(bootstrap_bundle, indent=2)}\n"
                "Query `sota_get_research_feeds`, `sota_get_first_hand_incentives`, and `sota_shelf_search` to audit "
                "live/historical 7-feed `sota-research-feeds.v2` readiness (`alpaca_sip` 04:00-20:00 ET, `alpaca_boats` "
                "20:00-04:00 ET + 2026-12-06 23/5 cutover flag, `alpaca_raw_vs_all_adjustment`, "
                "`sec_edgar_acceptance_datetime` 15m half-life + `424B*`/`S-3` dilution block, "
                "`finra_regsho_cnmsshvol_t1`, `corporate_actions_split_guard`, `ibkr_paper_4002_l1`). "
                "Never print credentials, account IDs, or balances.",
            ),
        ],
        lambda item: agent(item[2], schema=RECON_SCHEMA, role=item[0], type_name=item[1]),
    )

    PREWALL_EXEC_SCHEMA = {
        "type": "object",
        "properties": {
            "strategy_id": {"type": "string"},
            "archetype": {"type": "string"},
            "input_sha256": {"type": "string"},
            "study_max_date": {"type": "string"},
            "hard_stop_pct": {"type": "number"},
            "events_count": {"type": "integer"},
            "distinct_dates": {"type": "integer"},
            "t_stat_clustered": {"type": "number"},
            "dsr": {"type": "number"},
            "cpcv_positive_fold_pct": {"type": "number"},
            "net_1x_bps": {"type": "number"},
            "net_2x_impact_bps": {"type": "number"},
            "templates_validated": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
        },
        "required": [
            "strategy_id",
            "archetype",
            "input_sha256",
            "study_max_date",
            "hard_stop_pct",
            "events_count",
            "distinct_dates",
            "t_stat_clustered",
            "dsr",
            "cpcv_positive_fold_pct",
            "net_1x_bps",
            "net_2x_impact_bps",
            "templates_validated",
            "summary",
        ],
    }

    phase("Phase 2: Converged Strategy Template Scaffolding & Pre-Wall (<= 2026-10-15) Sim/Backtest Execution")

    prewall_run = await agent(
        f"{peer_brief}\n\nCandidate: `{strategy_id}` | Archetype: `{archetype}` | Seed SHA-256: `{seed_input_sha256}`\n"
        f"Phase 1 Recon: {json.dumps(recon_pair)}\n\n"
        "Query `sota_get_converged_strategy_templates` and validate converged strategy scaffolding across "
        "`~/Documents/meridian`, `~/Documents/sota-compounding-lab`, `~/Documents/trading-sota`, and `~/Documents/astrolabe`. "
        "Execute or verify strictly pre-wall (`study_max_date <= '2026-10-15'`) simulation/backtest metrics with "
        "`0 < hard_stop_pct <= 2.00` (`ADR-0022`) and 64-char lowercase hex `input_sha256`. Never touch live brokers.",
        schema=PREWALL_EXEC_SCHEMA,
        role="Converged Strategy Scaffolder & Pre-Wall Runner",
        type_name="sota-rd-proposer",
    )
    log(json.dumps(prewall_run, indent=2))

    GATE_SCHEMA = {
        "type": "object",
        "properties": {
            "passed": {"type": "boolean"},
            "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
            "findings": {"type": "array", "items": {"type": "string"}},
            "gate_receipts": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["passed", "evidence_grade", "findings", "gate_receipts"],
    }

    phase("Phase 3: Parallel Adversarial Falsification & Deterministic Code/Template/ADR Gate")

    phase3_gates = await parallel(
        [
            (
                "7-Feed PIT, Dilution & HLZ/CPCV/DSR Falsifier",
                "sota-falsifier",
                f"{peer_brief}\n\nPre-Wall Study Output:\n{json.dumps(prewall_run, indent=2)}\n"
                "Red-team for: (1) `Adjustment.RAW` vs `ALL` split contamination & `corporate_actions_split_guard`, "
                "(2) SEC `acceptanceDateTime` (`15m` half-life + `424B*`/`S-3` dilution block) & FINRA `CNMSshvol` `T-1` "
                "lookahead leakage, and (3) HLZ `t*(N)` + `CPCV` + `DSR >= 0.95` + `2x` Almgren-Chriss square-root impact survival.",
            ),
            (
                "Deterministic Code, Template & MADR 4.0 Gate",
                "sota-code-verifier",
                f"{peer_brief}\n\nTarget Repo: `~/Documents/{target_repo}`\n"
                f"Templates Validated: {json.dumps(prewall_run['templates_validated'])}\n"
                "Run deterministic verification (`ruff`, `ty`, `pytest`, `architecture_catalog.py --check`, "
                "`merge_gate.py`, `gitleaks`) and confirm 0 secrets, account IDs, or local home path leaks.",
            ),
        ],
        lambda item: agent(item[2], schema=GATE_SCHEMA, role=item[0], type_name=item[1]),
    )

    claim_violations = verify_research_convergence_claim(
        input_sha256=str(prewall_run["input_sha256"]),
        upstream_pins=discovered_pins,
        study_max_date=str(prewall_run["study_max_date"]),
        hard_stop_pct=float(prewall_run["hard_stop_pct"]),
        evidence_grade=str(phase3_gates[1]["evidence_grade"]),
    )

    LANDING_SCHEMA = {
        "type": "object",
        "properties": {
            "ready_for_paper_lanes": {"type": "boolean"},
            "mover_ranker_8787_status": {"type": "string"},
            "dynamic_trail_8799_status": {"type": "string"},
            "astrolabe_4002_status": {"type": "string"},
            "next_priority": {"type": "string"},
        },
        "required": [
            "ready_for_paper_lanes",
            "mover_ranker_8787_status",
            "dynamic_trail_8799_status",
            "astrolabe_4002_status",
            "next_priority",
        ],
    }

    phase("Phase 4: Paper-Lane Manifest Landing (:8787, :8799, :4002) & Convergence Receipt")

    landing = await agent(
        f"{peer_brief}\n\nCandidate `{strategy_id}` (`{archetype}`, lane `{broker_lane}`):\n"
        f"Deterministic ADR-0004 Claim Violations: {json.dumps(claim_violations)}\n"
        f"Falsifier Gate: {json.dumps(phase3_gates[0])}\n"
        f"Code/ADR Gate: {json.dumps(phase3_gates[1])}\n\n"
        "Adjudicate Paper-Lane Manifest readiness across `sota-mover-ranker` (`:8787` `200 req/min` `PA...` Paper), "
        "`sota-dynamic-trail-c` (`:8799` sub-50ms dual-tranche near-lossless guardian), and `astrolabe` (`:4002` `DU...` "
        "`IBKR` Paper `outsideRth` lane; live ports `4001`/`7496` hard-refused). Set `ready_for_paper_lanes=true` ONLY "
        "if `claim_violations` is empty and both Phase 3 gates passed.",
        schema=LANDING_SCHEMA,
        role="Paper-Lane Manifest Lander (:8787 / :8799 / :4002)",
        type_name="self",
    )

    all_issues = list(claim_violations) + list(phase3_gates[0]["findings"]) + list(phase3_gates[1]["findings"])
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="research-convergence-landing",
        done_summary=(
            f"{strategy_id} ({archetype}): paper_ready={landing['ready_for_paper_lanes']} "
            f"claim_ok={len(claim_violations) == 0} t={prewall_run['t_stat_clustered']} dsr={prewall_run['dsr']}"
        ),
        verified_by="; ".join((phase3_gates[1]["gate_receipts"] + phase3_gates[0]["gate_receipts"])[:4])
        or "falsifier+code-verifier+verify_research_convergence_claim",
        open_risks="; ".join(all_issues[:3]) or "none",
        next_priority=landing["next_priority"],
    )

    final_payload = {
        "bootstrap": bootstrap_bundle,
        "recon": recon_pair,
        "prewall_execution": prewall_run,
        "falsifier_gate": phase3_gates[0],
        "code_verifier_gate": phase3_gates[1],
        "claim_violations": claim_violations,
        "paper_lane_landing": landing,
    }
    out_text = json.dumps(final_payload, indent=2)
    log(out_text)
    print(out_text)
