# ruff: noqa: E402, F704, F821, PLE1142
"""AGY & CC-Lead SOTA `run_workflow` (`v3.7.0` #15): Dual-Machine Orca Trading Lanes (`T1..T3`) & Harness Lanes (`H1..H3`).

Audits and orchestrates all 18 `native-agent-stack` repositories across:
- 3 Execution Surfaces: `portable_mac_m5_max` (`100.93.211.101`, sovereign `:8787`/`:8799`/`:4002` paper broker host),
  `stationary_noesis_win32` (`100.110.115.22`, 64c/128GB + RTX 4090 + `Z:/sota-data/prewall-lake`), and
  `stationary_noesis_carbon_wsl2` (`Noesis-Carbon` Linux `ext4` `NautilusTrader` / `RiskAdverseQueueModel` `-n 8` sim).
- 8 Converged Multi-Model Orchestration Frameworks & 17 Runtime CLI Binaries.
- `sota-research-feeds.v2` 7-Feed PIT Contract & `ADR-0004` (`PHILOSOPHY_ONLY` sibling-repo authority).
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

from sota_mmw.cc_lead_hub import _load_live_bus_and_mesh
from sota_mmw.dual_machine_lanes import (
    HARNESS_LANES,
    ORCA_LANE_HUBS,
    ORCHESTRATION_FRAMEWORKS_MATRIX,
    REPO_LANE_INDEX,
    TRADING_LANES,
    build_lanes_overview,
    resolve_dual_machine_lane_plan,
)
from sota_mmw.research_convergence_contract import resolve_ecosystem_repo_dir

cfg = kit.get_workflow_args(globals())
raw_repo = str(cfg.get("repo") or "sota-compounding-lab")
target_repo = raw_repo if raw_repo in REPO_LANE_INDEX else "sota-compounding-lab"
workload = str(cfg.get("workload") or "default")
raw_placement = str(cfg.get("placement") or "auto")
placement = raw_placement if raw_placement in ("auto", "local", "noesis") else "auto"
plane = str(cfg.get("plane") or "all")
if plane not in ("all", "trading", "harness"):
    plane = "all"
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))

peer_brief = kit.load_peer_brief(target_repo)
rc_context = kit.load_research_convergence_context()
rc_envelope = kit.verify_workflow_research_convergence("dual-machine-trading-and-harness-lanes", repo=target_repo)
preflight = kit.run_preflight_summary(live_org=False)
trials_n, next_t, live_mesh = _load_live_bus_and_mesh()

overview = build_lanes_overview(plane=plane, mesh_state=live_mesh)
target_route = resolve_dual_machine_lane_plan(
    target_repo,
    workload=workload,
    mesh_state=live_mesh,
    requested_placement=placement,
)

# Deterministically verify single-broker-host firewall refusal on Noesis
broker_firewall_verified = False
try:
    resolve_dual_machine_lane_plan(
        "sota-mover-ranker",
        workload="active_paper_broker",
        mesh_state="dual_mesh_docked",
        requested_placement="noesis",
    )
except PermissionError:
    broker_firewall_verified = True

orca_yaml_present: dict[str, bool] = {}
for repo_name in sorted(REPO_LANE_INDEX):
    rdir = resolve_ecosystem_repo_dir(repo_name)
    orca_yaml_present[repo_name] = (rdir / "orca.yaml").is_file()

deterministic_audit = {
    "target_repo": target_repo,
    "workload": workload,
    "placement": placement,
    "mesh_state": live_mesh,
    "hlz_trials_n": trials_n,
    "hlz_next_t_hurdle": next_t,
    "research_convergence": {
        "schema_version": rc_context.get("schema_version", "sota-research-feeds.v2"),
        "sibling_repo_authority": rc_context.get("sibling_repo_authority", "PHILOSOPHY_ONLY"),
        "feed_count": rc_context.get("feed_count", 7),
        "upstream_pin_count": rc_context.get("upstream_pin_count", 18),
    },
    "research_convergence_envelope": rc_envelope,
    "trading_lanes_count": len(TRADING_LANES),
    "harness_lanes_count": len(HARNESS_LANES),
    "trading_repos_count": overview["trading_repos_count"],
    "harness_repos_count": overview["harness_repos_count"],
    "total_provisioned_repos": overview["total_provisioned_repos"],
    "frameworks_count": len(ORCHESTRATION_FRAMEWORKS_MATRIX),
    "orca_lane_hubs": ORCA_LANE_HUBS,
    "runtime_fleet": overview["runtime_fleet"],
    "single_broker_host_firewall_verified": broker_firewall_verified,
    "orca_yaml_repos_count": sum(1 for v in orca_yaml_present.values() if v),
    "orca_yaml_present": orca_yaml_present,
    "target_lane_route": target_route,
    "preflight": preflight,
}
log(f"{peer_brief}\n{json.dumps(deterministic_audit, indent=2, default=list)}")

if fast_deterministic_only:
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="dual-machine-trading-and-harness-lanes-fast",
        done_summary=(
            f"Lanes 18/18 ok={overview['ok']} firewall={broker_firewall_verified} "
            f"route={target_repo}->{target_route['selected_surface']} "
            f"fleet={overview['runtime_fleet']['installed_count']}/{overview['runtime_fleet']['checked_total']}"
        ),
        verified_by="dual_machine_lanes.py + verify_workflow_research_convergence + sota-doctor",
        open_risks="none" if (overview["ok"] and broker_firewall_verified) else "lane_or_firewall_violation",
        next_priority=target_route["orca_worker_start_cmd"][:200],
    )
    print(json.dumps(deterministic_audit, indent=2, default=list))
else:
    LANE_AUDIT_SCHEMA = {
        "type": "object",
        "properties": {
            "passed": {"type": "boolean"},
            "evidence_grade": {"type": "string", "enum": ["E1", "E2", "E3", "E4"]},
            "findings": {"type": "array", "items": {"type": "string"}},
            "recommended_orca_or_omc_cmd": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": ["passed", "evidence_grade", "findings", "recommended_orca_or_omc_cmd", "summary"],
    }

    phase("Phase 1: Parallel Dual-Machine Trading Lanes (T1..T3) & Harness Lanes (H1..H3) Reconnaissance")

    lane_scouts = await parallel(
        [
            (
                "Trading Lanes (T1..T3) & 3-Surface Execution Auditor",
                "sota-deep-synthesizer",
                f"{peer_brief}\n\nDeterministic Lane Audit:\n{json.dumps(deterministic_audit, indent=2, default=list)}\n"
                "Verify T1 (`:8787`/`:8799` Mac sovereignty), T2 (`:4002` Mac IBKR Paper + `Noesis-Carbon` WSL2 `ext4` "
                "`NautilusTrader`/`RiskAdverseQueueModel` `-n 8` sim), and T3 (`Noesis` Win32/RTX 4090 `Z:/sota-data/prewall-lake` "
                "`<=2026-10-15` CPCV/DSR sweeps + roaming Mac failover) under `sota-research-feeds.v2` (`PHILOSOPHY_ONLY`).",
            ),
            (
                "Harness Lanes (H1..H3) & 8-Framework Orchestration Scout",
                "self",
                f"{peer_brief}\n\nDeterministic Lane Audit:\n{json.dumps(deterministic_audit, indent=2, default=list)}\n"
                "Verify H1..H3 alignment across all 8 SOTA orchestration frameworks (`Orca` `--on 100.110.115.22` & "
                "`--parent-worktree folder:<id>`, `CC-Lead OMC v2`, `Codex OMX`, `AGY 15-Workflow`, `OMO Hephaestus`, "
                "`Pi/OMP @worker`, `Goose/DSH`, and `sota-bus + hcom + bd + omniroute`). Never print secrets or account IDs.",
            ),
        ],
        lambda item: agent(item[2], schema=LANE_AUDIT_SCHEMA, role=item[0], type_name=item[1]),
    )

    phase("Phase 2: Adversarial Split-Brain, Pre-Wall & Multi-Vendor Falsification")

    falsifier_out = await agent(
        f"{peer_brief}\n\nTarget Route:\n{json.dumps(target_route, indent=2)}\n"
        f"Phase 1 Scouts:\n{json.dumps(lane_scouts, indent=2)}\n"
        "Red-team for: (1) dual-broker split-brain across Mac M5 Max and Noesis, (2) wrong Orca `--environment` vs "
        "`--on 100.110.115.22` or OpenCode `--effort` CLI flags, (3) post-wall (`>2026-10-15`) leakage, and "
        "(4) single-vendor review correlation (`<3` concrete vendors).",
        schema=LANE_AUDIT_SCHEMA,
        role=f"Dual-Machine Lane Falsifier ({target_repo})",
        type_name="sota-falsifier",
    )

    phase("Phase 3: Deterministic Code, orca.yaml & Zero-Leak Verification Gate")

    verifier_out = await agent(
        f"{peer_brief}\n\nTarget Repo: `{target_repo}`\n"
        f"Falsifier Output: {json.dumps(falsifier_out, indent=2)}\n"
        "Run deterministic repo checks (`ruff`, `ty`, `pytest`, `architecture_catalog.py --check`, `merge_gate.py`, "
        "`gitleaks`) and verify `orca.yaml` cross-OS readiness with 0 secret or home-path leaks.",
        schema=LANE_AUDIT_SCHEMA,
        role=f"Dual-Machine Lane Code Verifier ({target_repo})",
        type_name="sota-code-verifier",
    )

    all_findings = list(falsifier_out["findings"]) + list(verifier_out["findings"])
    final_report = {
        "deterministic_audit": deterministic_audit,
        "trading_lane_scout": lane_scouts[0],
        "harness_lane_scout": lane_scouts[1],
        "falsifier_gate": falsifier_out,
        "verifier_gate": verifier_out,
        "approved_for_dual_machine_dispatch": (
            broker_firewall_verified and falsifier_out["passed"] and verifier_out["passed"] and not all_findings
        ),
    }
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="dual-machine-trading-and-harness-lanes",
        done_summary=(
            f"{target_repo} ({target_route['lane_id']} -> {target_route['selected_surface']}) "
            f"approved={final_report['approved_for_dual_machine_dispatch']}"
        ),
        verified_by="dual_machine_lanes + synthesizer + falsifier + code-verifier",
        open_risks="; ".join(all_findings[:3]) or "none",
        next_priority=verifier_out["recommended_orca_or_omc_cmd"][:200] or target_route["orca_worker_start_cmd"][:200],
    )
    out_json = json.dumps(final_report, indent=2, default=list)
    log(out_json)
    print(out_json)
