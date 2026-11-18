"""Grand SOTA Native Workflow (`v3.10.0`, `ADR-0018`): 46 Skills x 14 Layers x 18-Repo ADRs x 11 Runtime Workers x Dual-Machine Orca.

Enacts SOTA Skills (`46` skills converged across Antigravity, Claude Code `cc-lead`, Codex `OMX`, `~/.agents`, and `Orca`),
`9`-Feed `sota-ranking-datafeeds.v3.8` (`sota-research-feeds.v2` backward-compatible) PIT Research Convergence,
`4`-Hash Compounding Versioning (`HLZ N>=93`, `t*(94)>=4.1834`, `ADR-0022 <= 2.00%` stop, `PHILOSOPHY_ONLY` sibling repos),
live `18`-Repository MADR 4.0 ADR Governance, and `11` Multi-Model Runtime Workers (`17` binaries, `8` orchestration
frameworks, `7` model vendors) across `Mac M5 Max`, `Stationary Noesis Win32` (`100.110.115.22`), and `Noesis-Carbon` WSL2.

Pass `Args={"goal": "...", "repo": "native-agent-stack", "layer": "all"}`.
"""

import json
import sys
from pathlib import Path

_WF_DIR = Path(__file__).resolve().parent if "__file__" in globals() else (Path.home() / ".agents" / "workflows")
if str(_WF_DIR) not in sys.path:
    sys.path.insert(0, str(_WF_DIR))

import _sota_kit as kit  # noqa: E402

cfg = kit.get_workflow_args(globals())
goal = str(
    cfg.get("goal")
    or "Audit and enact all 46 SOTA skills, 9-Feed PIT Research-Convergence, 14 layers (L0-L13), 18-repo MADR 4.0 ADRs, and Dual-Machine Orca multi-model workers."
)
ws0 = kit.get_primary_workspace(globals())
repo = str(cfg.get("repo") or (Path(ws0).name if ws0 else "native-agent-stack"))
layer = str(cfg.get("layer") or "all")

# Phase 0: Deterministic Self-Bootstrap (Peer Bus + 9-Feed/7-Feed RC + 46-Skill & 18-Repo ADR Binding)
peer_brief = kit.load_peer_brief(repo)
preflight = kit.run_preflight_summary(live_org=False)
rc_ctx = kit.load_research_convergence_context()
rc_envelope = kit.verify_workflow_research_convergence(
    "sota-skills-adr-and-orca-grand-workflow",
    repo=repo,
)
enactment = kit.bind_workflow_skills_and_adrs(
    goal=goal,
    repo=repo,
    layer=layer,
    workflow_id="sota-skills-adr-and-orca-grand-workflow",
)

header = (
    f"[v3.10.0 Grand Native Enactor | rc={rc_ctx['schema_version']}+sota-ranking-datafeeds.v3.8 "
    f"({rc_ctx.get('sibling_repo_authority', 'PHILOSOPHY_ONLY')}, rc_valid={rc_envelope['valid']}) | "
    f"skills={enactment.get('skills_enacted_count', 46)} | layers={enactment.get('layers_count', 14)} | "
    f"enactment_sha256={str(enactment.get('enactment_sha256', ''))[:16]}]\n"
    f"{json.dumps(preflight)}\n{peer_brief}"
)
log(header)  # noqa: F821

LAYER_SKILL_ADR_SCHEMA = {
    "type": "object",
    "properties": {
        "surface_and_doctor_status": {"type": "string"},
        "skills_verified_count": {"type": "integer"},
        "layers_verified": {"type": "array", "items": {"type": "string"}},
        "adr_catalog_highlights": {"type": "array", "items": {"type": "string"}},
        "ranking_and_prewall_gates_ok": {"type": "boolean"},
        "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
    },
    "required": [
        "surface_and_doctor_status",
        "skills_verified_count",
        "layers_verified",
        "adr_catalog_highlights",
        "ranking_and_prewall_gates_ok",
        "evidence_grade",
    ],
}

ORCA_RUNTIME_SCHEMA = {
    "type": "object",
    "properties": {
        "dual_machine_mesh_status": {"type": "string"},
        "orca_automations_and_hubs": {"type": "array", "items": {"type": "string"}},
        "runtime_worker_routes": {"type": "array", "items": {"type": "string"}},
        "single_broker_firewall_intact": {"type": "boolean"},
        "verdict": {"type": "string", "enum": ["PASS", "BLOCKED"]},
    },
    "required": [
        "dual_machine_mesh_status",
        "orca_automations_and_hubs",
        "runtime_worker_routes",
        "single_broker_firewall_intact",
        "verdict",
    ],
}

phase("Phase 1: Parallel 46-Skill, 14-Layer, 18-Repo ADR & Dual-Machine Orca Reconnaissance")  # noqa: F821

fanout_results = await parallel(  # noqa: F821
    [
        (
            "SOTA 46-Skill, 9-Feed PIT & 18-Repo ADR Auditor",
            "sota-deep-synthesizer",
            LAYER_SKILL_ADR_SCHEMA,
            f"{header}\n\nGoal: {goal} | Repo: {repo} | Layer: {layer}\n"
            f"Deterministic Enactment Receipt: {json.dumps(enactment.get('adr_governance', {}))}\n"
            "Run `~/.agents/bin/sota-workflow status --json` (or inspect `sota_mmw.native_workflow_enactor`) "
            "to verify all 46 canonical SOTA skills across AGY/Claude/Codex/Orca, 9-Feed `DF1..DF9` "
            "(`sota-ranking-datafeeds.v3.8` / `sota-research-feeds.v2`), `<= 2026-10-15` pre-wall + `HLZ N>=93`, "
            "`ADR-0022 <= 2.00%` stop, `PHILOSOPHY_ONLY` sibling-repo rule, and MADR 4.0 ADR catalogs. "
            "Never print secrets, account IDs, or balances.",
        ),
        (
            "Dual-Machine Orca & 11-Worker Multi-Model Fleet Verifier",
            "sota-code-verifier",
            ORCA_RUNTIME_SCHEMA,
            f"{header}\n\nGoal: {goal} | Repo: {repo}\n"
            f"Multi-Model Fleet Spec: {json.dumps(enactment.get('multi_model_fleet', {}))}\n"
            "Verify `orca automations list --json`, `~/.agents/bin/sota-lanes status --json`, and "
            "`~/.agents/bin/sota-cc-hub status` across `portable_mac_m5_max` and `stationary_noesis` (`100.110.115.22`), "
            "confirming `SINGLE_BROKER_HOST_FIREWALL` (`:8787`/`:8799`/`:4002` paper-only on Mac M5 Max, live ports "
            "`4001`/`7496` hard-refused) and 0 secret/path leaks.",
        ),
    ],
    lambda item: agent(  # noqa: F821
        item[3],
        schema=item[2],
        role=item[0],
        type_name=item[1],
    ),
)

phase("Phase 2: Unified Synthesis & Peer-Bus Handover Checkpoint")  # noqa: F821

final_receipt = {
    "workflow_id": "sota-skills-adr-and-orca-grand-workflow",
    "ecosystem_semver": enactment.get("ecosystem_semver", "3.10.0"),
    "enactment_sha256": enactment.get("enactment_sha256", ""),
    "skill_layer_adr_audit": fanout_results[0],
    "orca_multimodel_audit": fanout_results[1],
    "all_gates_passed": bool(
        rc_envelope["valid"]
        and fanout_results[0]["ranking_and_prewall_gates_ok"]
        and fanout_results[1]["single_broker_firewall_intact"]
        and fanout_results[1]["verdict"] == "PASS"
    ),
}
log(json.dumps(final_receipt, indent=2))  # noqa: F821

kit.record_workflow_run(
    repo=repo,
    workflow_id="sota-skills-adr-and-orca-grand-workflow",
    done_summary=(
        f"Enacted v3.10.0 Grand SOTA Workflow ({goal[:140]}): "
        f"skills={fanout_results[0]['skills_verified_count']}, "
        f"orca={fanout_results[1]['verdict']}, sha={str(enactment.get('enactment_sha256', ''))[:16]}"
    ),
    verified_by=f"rc_valid={rc_envelope['valid']}, grade={fanout_results[0]['evidence_grade']}",
    open_risks="none" if final_receipt["all_gates_passed"] else "review_audit_findings",
    next_priority="Operate 17 native workflows + Dual-Machine Orca automations across all 3 surfaces",
)
print(json.dumps(final_receipt, indent=2))
