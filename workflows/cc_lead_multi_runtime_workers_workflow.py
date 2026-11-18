# ruff: noqa: E402, F704, F821, PLE1142
"""AGY & Claude-Lead SOTA `run_workflow` (`v3.5.0` #14): Claude Code Central Multi-Session & Multi-Runtime Workers.

Positions Claude Code (`cc-lead`, `claude-fable-5-2` `xhigh` + `oh-my-claudecode` `OMC` runtime v2)
as the central multi-session orchestrator commanding heterogeneous runtime workers (`Codex OMX`,
`Antigravity`, `OpenCode OMO`, `DeepSeek DSH`, `Pi/OMP`, `Goose`, `Muse`, `Grok`, and `Orca`
`Mac M5 Max <-> Noesis 64c/128GB/RTX4090` supervised child worktrees) under:
- `sota-research-feeds.v2` 7-feed PIT contract & `ADR-0004` 3-tier SHA provenance (`PHILOSOPHY_ONLY` sibling-repo authority)
- `oneModelPerConversation = True` & non-GPT `Hephaestus` invariant
- Disjoint SQLite WAL `sota-bus` path-glob leases & >= 3 `CANONICAL_MODEL_VENDORS` Stage-3 falsification
"""

import json
import sys
from pathlib import Path

WF_DIR = Path.home() / ".agents" / "workflows"
LOCAL_WF_DIR = Path(__file__).resolve().parent if "__file__" in globals() else WF_DIR
REPO_SRC = LOCAL_WF_DIR.parent / "src"
HOME_MMW_SRC = Path.home() / "Documents" / "sota-multi-model-workflows" / "src"
ACTIVE_WF_DIR = LOCAL_WF_DIR if (LOCAL_WF_DIR / "_sota_kit.py").is_file() else WF_DIR
ACTIVE_MMW_SRC = REPO_SRC if (REPO_SRC / "sota_mmw").is_dir() else HOME_MMW_SRC
for _p_dir in (ACTIVE_MMW_SRC, ACTIVE_WF_DIR):
    if _p_dir.is_dir() and str(_p_dir) not in sys.path:
        sys.path.insert(0, str(_p_dir))

import _sota_kit as kit

from sota_mmw.cc_lead_hub import (
    TASK_CLASS_PROFILES,
    CCLeadPlanRequest,
    _load_live_bus_and_mesh,
    build_cc_lead_execution_plan,
    probe_cc_runtime_fleet,
)
from sota_mmw.research_convergence_contract import SIBLING_REPO_AUTHORITY

cfg = kit.get_workflow_args(globals())
target_repo = str(cfg.get("repo") or "cc-sota-harness")
raw_class = str(cfg.get("task_class") or "parallel_worktree_implementation")
task_class = raw_class if raw_class in TASK_CLASS_PROFILES else "parallel_worktree_implementation"
placement = str(cfg.get("placement") or "auto")
if placement not in ("auto", "local", "noesis"):
    placement = "auto"
goal = str(
    cfg.get("goal")
    or f"Coordinate Claude Code (OMC v2) central multi-session & multi-runtime workers on {target_repo}."
)
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))

peer_brief = kit.load_peer_brief(target_repo)
rc_context = kit.load_research_convergence_context()
preflight = kit.run_preflight_summary(live_org=False)
fleet_status = probe_cc_runtime_fleet()
trials_n, next_t, mesh_state = _load_live_bus_and_mesh()

plan = build_cc_lead_execution_plan(
    CCLeadPlanRequest(
        repo=target_repo,
        goal=goal,
        task_class=task_class,
        placement=placement,
        session_id="cc-lead-workflow",
    ),
    mesh_state=mesh_state,
    hlz_trials_n=trials_n,
    hlz_next_t_hurdle=next_t,
    feeds_schema=str(rc_context.get("schema_version") or "sota-research-feeds.v2"),
)

bootstrap_payload = {
    "target_repo": target_repo,
    "task_class": task_class,
    "sibling_repo_authority": SIBLING_REPO_AUTHORITY,  # PHILOSOPHY_ONLY
    "research_convergence": {
        "schema_version": rc_context.get("schema_version", "sota-research-feeds.v2"),
        "feed_count": rc_context.get("feed_count", 7),
        "upstream_pin_count": rc_context.get("upstream_pin_count", 18),
    },
    "fleet": fleet_status,
    "preflight": preflight,
    "cc_lead_plan": plan,
}
log(f"{peer_brief}\n{json.dumps(bootstrap_payload, indent=2)}")

if fast_deterministic_only:
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="cc-lead-multi-runtime-workers-fast",
        done_summary=(
            f"CC-Lead plan={plan['plan_id']} sha={plan['plan_sha256'][:12]} "
            f"host={plan['target_host']} vendors={len(plan['vendors_covered'])} "
            f"lease_disjoint={plan['isolation_and_lease']['lease_disjoint']}"
        ),
        verified_by="cc_lead_hub.py + probe_cc_runtime_fleet + load_research_convergence_context + sota-doctor",
        open_risks="none" if plan["isolation_and_lease"]["lease_disjoint"] else "foreign_peer_lease_active",
        next_priority=plan["channels"]["2_omc_team_swarm_cmd"][:200],
    )
    print(json.dumps(bootstrap_payload, indent=2))
else:
    WORKER_REVIEW_SCHEMA = {
        "type": "object",
        "properties": {
            "passed": {"type": "boolean"},
            "evidence_grade": {"type": "string", "enum": ["E1", "E2", "E3", "E4"]},
            "p0_p1_findings": {"type": "array", "items": {"type": "string"}},
            "recommended_worker_adjustments": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
        },
        "required": [
            "passed",
            "evidence_grade",
            "p0_p1_findings",
            "recommended_worker_adjustments",
            "summary",
        ],
    }

    phase("Phase 1: Parallel Cross-Role Verification of Claude-Lead 5-Channel Runtime Worker Plan")

    reviews = await parallel(
        [
            (
                f"Upstream CLI & Multi-Runtime Topology Verifier ({target_repo})",
                "sota-deep-synthesizer",
                f"{peer_brief}\n\nCC-Lead Plan:\n{json.dumps(bootstrap_payload, indent=2)}\n"
                "Verify exact CLI flags for `omc ultragoal`, `omc team`, `omc ask`, `omx exec`, `orca orchestration worker-start`, "
                "and `hcom`, plus `ADR-0004` (`PHILOSOPHY_ONLY`) & `sota-research-feeds.v2` context binding.",
            ),
            (
                f"Multi-Session Correlation, Lease & Firewall Falsifier ({target_repo})",
                "sota-falsifier",
                f"{peer_brief}\n\nCC-Lead Plan:\n{json.dumps(bootstrap_payload, indent=2)}\n"
                "Red-team for single-vendor correlation, `Hephaestus` GPT violations, foreign WAL lease collisions, "
                "pre-wall (`<=2026-10-15`) leakage, or live-broker/secret exposure.",
            ),
            (
                f"Target Repo Gate & Worktree Readiness Verifier ({target_repo})",
                "sota-code-verifier",
                f"{peer_brief}\n\nCC-Lead Plan:\n{json.dumps(bootstrap_payload, indent=2)}\n"
                f"Verify `~/Documents/{target_repo}` clean status, MADR 4.0 catalog parity, and isolated worktree readiness.",
            ),
        ],
        lambda item: agent(item[2], schema=WORKER_REVIEW_SCHEMA, role=item[0], type_name=item[1]),
    )

    findings = list(reviews[1]["p0_p1_findings"]) + list(reviews[2]["p0_p1_findings"])
    final_bundle = {
        "bootstrap": bootstrap_payload,
        "topology_review": reviews[0],
        "falsifier_review": reviews[1],
        "code_verifier_review": reviews[2],
        "ready_for_cc_lead_dispatch": len(findings) == 0 and plan["isolation_and_lease"]["lease_disjoint"],
    }
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="cc-lead-multi-runtime-workers",
        done_summary=(
            f"CC-Lead {plan['plan_id']} ready={final_bundle['ready_for_cc_lead_dispatch']} "
            f"host={plan['target_host']} sha={plan['plan_sha256'][:12]}"
        ),
        verified_by="cc_lead_hub + synthesizer + falsifier + code-verifier",
        open_risks="; ".join(findings[:3]) or "none",
        next_priority=plan["channels"]["1_cc_lead_ultragoal_cmd"][:200],
    )
    out_txt = json.dumps(final_bundle, indent=2)
    log(out_txt)
    print(out_txt)
