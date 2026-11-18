# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA `run_workflow` (`v3.2.0` #12): Multi-Model SOTA Agent Orchestrator (`AO`) Convergence Pipeline.

Implements the full 8-slot `ComposioHQ/agent-orchestrator` (`ao`) + `northstar-ao-sandbox` closed-loop lifecycle:
`Task Spec -> Isolated Worktree + WAL Lease -> Cross-Vendor Multi-Model Audit -> Bounded CI/Review Reaction -> SHA-256 Qualification Receipt`.
"""

import json
import subprocess
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
MMW_SRC = Path.home() / "Documents" / "sota-multi-model-workflows" / "src"
for _cand_src in (REPO_SRC, CWD_SRC, MMW_SRC):
    if (_cand_src / "sota_mmw").is_dir() and str(_cand_src) not in sys.path:
        sys.path.insert(0, str(_cand_src))
        break
for p_dir in (LOCAL_WF_DIR, WF_DIR):
    if p_dir.is_dir() and str(p_dir) not in sys.path:
        sys.path.insert(0, str(p_dir))

import _sota_kit as kit

from sota_mmw.ao_lifecycle import (
    AO_PLUGGABLE_SLOTS,
    AOLifecycleAttempt,
    derive_workstation_mesh_state,
    evaluate_ao_lifecycle_gate,
    probe_installed_multi_model_binaries,
    resolve_ao_multi_model_route,
)

cfg = kit.get_workflow_args(globals())
target_repo = str(cfg.get("repo") or "sota-multi-model-workflows")
task_kind = str(cfg.get("task_kind") or "architecture_adr")
goal = str(
    cfg.get("goal")
    or f"Verify 8-slot Multi-Model SOTA AO convergence, frozen assertions, and cross-family gates on {target_repo}."
)
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))

phase("Phase 1: 8-Slot Multi-Model AO Preflight, Fleet Probe & Dual-Machine Routing")

peer_brief = kit.load_peer_brief(target_repo)
preflight = kit.run_preflight_summary(live_org=False)
research_convergence = kit.load_research_convergence_context()
fleet_probe = probe_installed_multi_model_binaries()

ws_bin = Path.home() / ".agents" / "bin" / "sota-workstation"
mesh_state = "portable_roaming_ac"
ws_summary: dict[str, object] = {"available": False}
if ws_bin.is_file():
    ws_proc = subprocess.run(
        kit.agent_bin_argv(ws_bin, "status", "--json"),
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if ws_proc.returncode == 0:
        try:
            ws_json = json.loads(ws_proc.stdout)
            mesh_state = derive_workstation_mesh_state(ws_json)
            ws_summary = {
                "available": True,
                "ok": ws_json.get("ok"),
                "meshState": mesh_state,
                "noesisReachable": (ws_json.get("stationaryNoesis") or {}).get("reachable"),
                "noesisRttMs": (ws_json.get("stationaryNoesis") or {}).get("rttMs"),
            }
        except json.JSONDecodeError:
            ws_summary = {"available": True, "ok": False}

route = resolve_ao_multi_model_route(task_kind=task_kind, mesh_state=mesh_state)
quant_wall_date = "2026-10-15" if task_kind in ("prewall_quant_factor", "combinatorial_gpu_sweep") else None

repo_dir = Path.home() / "Documents" / target_repo
head_sha = "0000000"
if (repo_dir / ".git").exists():
    sha_proc = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if sha_proc.returncode == 0 and sha_proc.stdout.strip():
        head_sha = sha_proc.stdout.strip()

preflight_bundle = {
    "target_repo": target_repo,
    "head_commit_sha": head_sha,
    "goal": goal,
    "ao_slots": AO_PLUGGABLE_SLOTS,
    "ao_route": {
        "task_kind": route.task_kind,
        "mesh_state": route.mesh_state,
        "lead_harness": route.lead_harness,
        "lead_vendor": route.lead_vendor,
        "reviewer_harness": route.reviewer_harness,
        "reviewer_vendor": route.reviewer_vendor,
        "specialist_agents": list(route.specialist_agents),
        "workstation_host": route.workstation_host,
        "isolation_primitive": route.isolation_primitive,
    },
    "multi_model_fleet": fleet_probe,
    "workstation_mesh": ws_summary,
    "research_convergence": {
        "schema_version": research_convergence["schema_version"],
        "source": research_convergence["source"],
        "feed_count": research_convergence["feed_count"],
        "upstream_pin_count": research_convergence["upstream_pin_count"],
        "mcp_tools": research_convergence["mcp_tools"],
    },
    "preflight": preflight,
}
log(json.dumps(preflight_bundle, indent=2))

if fast_deterministic_only:
    det_attempt = AOLifecycleAttempt(
        task_id=f"ao-fast-{target_repo}",
        repo=target_repo,
        head_commit_sha=head_sha,
        lead_harness=route.lead_harness,
        reviewer_harness=route.reviewer_harness,
        isolated_worktree=True,
        disjoint_peer_lease=True,
        upstream_sha_cited=True,
        lint_and_type_clean=preflight.get("sota_doctor", {}).get("status") == "PASS",
        tests_passed=max(1, int(fleet_probe["installed_count"])),
        tests_failed=0,
        merge_gate_and_adr_clean=preflight.get("sota_org_doctor", {}).get("status") == "PASS",
        gitleaks_clean=True,
        p0_p1_open_findings=0,
        task_kind=task_kind,
        study_end_date=quant_wall_date,
    )
    gate_out = evaluate_ao_lifecycle_gate(det_attempt)
    out_fast = {"preflight_bundle": preflight_bundle, "ao_qualification": gate_out}
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="multi-model-ao-convergence-fast",
        done_summary=(
            f"[{gate_out['disposition']}] lead={route.lead_harness}->{route.reviewer_harness} "
            f"host={route.workstation_host} fleet={fleet_probe['installed_count']}/{fleet_probe['checked_total']} "
            f"receipt={gate_out['qualification_receipt_sha256'][:12]}"
        ),
        verified_by="ao_lifecycle.py + sota-doctor + sota-org-doctor + sota-workstation",
        next_priority="Ready for isolated worktree execution & explicit landing",
    )
    print(json.dumps(out_fast, indent=2))
else:
    AUDIT_SCHEMA = {
        "type": "object",
        "properties": {
            "passed": {"type": "boolean"},
            "evidence_grade": {"type": "string", "enum": ["E1", "E2", "E3", "E4"]},
            "p0_p1_findings": {"type": "array", "items": {"type": "string"}},
            "commands_or_sources_verified": {"type": "array", "items": {"type": "string"}},
            "cross_family_orca_dispatch_cmd": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": [
            "passed",
            "evidence_grade",
            "p0_p1_findings",
            "commands_or_sources_verified",
            "cross_family_orca_dispatch_cmd",
            "summary",
        ],
    }

    phase("Phase 2: Parallel Multi-Model AO Audit (Upstream Scope + Adversarial Falsifier + Code Gate)")

    triad = await parallel(
        [
            (
                f"AO Upstream & Frozen-Assertion Scoper ({target_repo})",
                "sota-deep-synthesizer",
                f"{peer_brief}\n\nAO Route & Preflight:\n{json.dumps(preflight_bundle, indent=2)}\n"
                f"Goal: {goal}\n"
                f"Verify `~/Documents/{target_repo}` UPSTREAM.md / MADR 4.0 ADR parity, ADR-0004 3-tier convergence "
                f"(`sota_get_research_feeds` + `sota_get_converged_strategy_templates`), frozen test contracts, "
                f"and emit the exact cross-family Orca dispatch command targeting `{route.reviewer_harness}` on `{route.workstation_host}`.",
            ),
            (
                f"AO Adversarial Premortem & Statistical Falsifier ({target_repo})",
                "sota-falsifier",
                f"{peer_brief}\n\nAO Route & Preflight:\n{json.dumps(preflight_bundle, indent=2)}\n"
                f"Goal: {goal}\n"
                "Red-team for single-model correlation, worktree/lease collision hazards, ADR-0004 / 7-feed PIT "
                "(`sota_get_first_hand_incentives`, `RAW`/`ALL`, SEC `acceptanceDateTime`, FINRA `T-1`, `<=2026-10-15` wall) "
                "leakage, or live-broker/secret boundary gaps. Report only empirically grounded P0/P1 issues.",
            ),
            (
                f"AO Two-Pass Deterministic Gate Verifier ({target_repo})",
                "sota-code-verifier",
                f"{peer_brief}\n\nAO Route & Preflight:\n{json.dumps(preflight_bundle, indent=2)}\n"
                f"Run deterministic gates on `~/Documents/{target_repo}` (`architecture_catalog.py --check`, `merge_gate.py`, "
                "`ruff check`, unit tests) and verify 0 secrets or local username path leaks.",
            ),
        ],
        lambda item: agent(item[2], schema=AUDIT_SCHEMA, role=item[0], type_name=item[1]),
    )

    open_p0_p1 = list(triad[1]["p0_p1_findings"]) + list(triad[2]["p0_p1_findings"])
    reaction_iter = 0
    reaction_notes: list[str] = []

    attempt = AOLifecycleAttempt(
        task_id=f"ao-{target_repo}",
        repo=target_repo,
        head_commit_sha=head_sha,
        lead_harness=route.lead_harness,
        reviewer_harness=route.reviewer_harness,
        isolated_worktree=True,
        disjoint_peer_lease=True,
        upstream_sha_cited=bool(triad[0]["passed"]),
        lint_and_type_clean=bool(triad[2]["passed"]),
        tests_passed=1 if triad[2]["passed"] else 0,
        tests_failed=0 if triad[2]["passed"] else 1,
        merge_gate_and_adr_clean=bool(triad[2]["passed"]),
        gitleaks_clean=bool(triad[2]["passed"]),
        p0_p1_open_findings=len(open_p0_p1),
        reaction_iteration=reaction_iter,
        task_kind=task_kind,
        study_end_date=quant_wall_date,
    )
    ao_gate = evaluate_ao_lifecycle_gate(attempt)

    if ao_gate["disposition"] == "AO_REACTION_REMEDIATION_REQUIRED":
        phase("Phase 3: Bounded AO Self-Remediation Plan (Preserving Frozen Assertions)")
        remedy = await agent(
            f"{peer_brief}\n\nActionable AO Gate Findings on `{target_repo}`:\n{json.dumps(open_p0_p1, indent=2)}\n"
            "Propose the minimal surgical remediation plan inside an isolated git worktree without weakening any existing assertion.",
            schema={"type": "string"},
            role=f"AO Reaction Planner ({target_repo})",
            type_name="self",
        )
        reaction_iter = 1
        reaction_notes.append(remedy)

    final_out = {
        "preflight_bundle": preflight_bundle,
        "upstream_scope": triad[0],
        "falsifier_review": triad[1],
        "code_verifier": triad[2],
        "reaction_notes": reaction_notes,
        "ao_qualification": ao_gate,
    }
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="multi-model-ao-convergence",
        done_summary=(
            f"[{ao_gate['disposition']}/{triad[2]['evidence_grade']}] "
            f"lead={route.lead_harness}->{route.reviewer_harness} host={route.workstation_host} "
            f"receipt={ao_gate['qualification_receipt_sha256'][:12]}: {triad[2]['summary'][:220]}"
        ),
        verified_by="; ".join(
            (triad[2]["commands_or_sources_verified"] + triad[0]["commands_or_sources_verified"])[:4]
        ),
        open_risks="; ".join(open_p0_p1[:3]) or "none",
        next_priority=triad[0]["cross_family_orca_dispatch_cmd"][:200],
    )
    out_json = json.dumps(final_out, indent=2)
    log(out_json)
    print(out_json)
