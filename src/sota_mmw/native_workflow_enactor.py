"""Unified Native SOTA Workflow, 46-Skill, All-Layers (L0..L13) & 18-Repo ADR Enactment Engine (`v3.10.0`, `ADR-0018`).

Enacts SOTA Skills, 9-Feed `sota-ranking-datafeeds.v3.8` (`sota-research-feeds.v2` backward-compatible) Research
Convergence, 4-Hash Compounding Versioning, MADR 4.0 ADR Governance across all 18 active repositories, and 11
Multi-Model Runtime Workers (`17` CLI binaries, `8` orchestration frameworks, `7` model vendors) as a seamless native
workflow across Antigravity (`run_workflow`), Dual-Machine Orca (`Mac M5 Max <-> Stationary Noesis 100.110.115.22` +
`Noesis-Carbon` WSL2 `orca automations` & `worker-start`), Claude Code (`cc-lead` + `OMC v2`), Codex (`OMX`), OpenCode
(`OMO`), DeepSeek (`DSH`), Pi/OMP (`@worker`), Goose, Muse, and Grok.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
from pathlib import Path
from typing import Any

from sota_mmw.cc_lead_hub import (
    CC_LEAD_CENTRAL_CONTRACT,
    RUNTIME_WORKER_ROSTER,
    CCLeadPlanRequest,
    build_cc_lead_execution_plan,
)
from sota_mmw.compounding_versioning import (
    CANONICAL_RANKING_DATAFEEDS_V38,
    DEFAULT_ECOSYSTEM_SEMVER,
    DEFAULT_PREWALL_LAKE_SHA256,
    RANKING_DATAFEEDS_SCHEMA_VERSION,
    UPSTREAM_SHELF_PINS_18,
    build_compounding_version_status,
)
from sota_mmw.dual_machine_lanes import (
    CANONICAL_ORCA_LANE_LEADS,
    CANONICAL_SEVEN_MODEL_VENDORS,
    ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES,
    HARNESS_LANES,
    ORCA_LANE_HUBS,
    ORCHESTRATION_FRAMEWORKS_MATRIX,
    REPO_LANE_INDEX,
    TRADING_LANES,
    resolve_dual_machine_lane_plan,
)
from sota_mmw.research_convergence_contract import (
    CANONICAL_STRATEGY_ARCHETYPES,
    MAX_HARD_STOP_PCT,
    PRE_WALL_MAX_DATE,
    RESEARCH_FEEDS_SCHEMA_VERSION,
    SIBLING_REPO_AUTHORITY,
    build_workflow_research_convergence_envelope,
    detect_workstation_surface,
    resolve_ecosystem_repo_dir,
)

NATIVE_WORKFLOW_ENACTOR_SCHEMA = "sota-native-workflow-enactor.v3.10"

ACTIVE_18_REPOS: tuple[str, ...] = (
    ".github",
    "native-agent-stack",
    "sota-harness-foundation",
    "sota-multi-model-workflows",
    "agy-sota-harness",
    "dsh-sota-harness",
    "sota-compounding-lab",
    "sota-upstream-shelf-lock",
    "astrolabe",
    "canon",
    "cc-sota-harness",
    "dsh-plugin-landscape",
    "meridian",
    "sota-dynamic-trail-c",
    "sota-mover-ranker",
    "sota-private-vault",
    "trading-sota",
    "tsl",
)

SKILL_FAMILIES: dict[str, tuple[str, ...]] = {
    "CORE_HARNESS_AND_ORCHESTRATION": (
        "autoresearch-loop",
        "cc-lead-multi-runtime-orchestrator",
        "council-of-high-intelligence",
        "microstructure-and-sec-catalyst-lab",
        "orca-cli",
        "orchestration",
        "planning-with-files",
        "sota-ast-codemod",
        "sota-dimensional-and-property-invariants",
        "sota-mover-ranker",
        "sota-peer-bus-and-handover",
        "sota-quant-research-protocol",
        "sota-skillopt-self-evolution",
        "sota-spec-and-adr-gate",
        "sota-taste-anti-slop",
        "sota-tdd-superpowers",
        "sota-verification-and-security-gate",
        "sota-workflow",
    ),
    "QUANT_ALPHA_AND_CATALYST_SCREENING": (
        "backtest-expert",
        "earnings-trade-analyzer",
        "ftd-detector",
        "institutional-flow-tracker",
        "macro-regime-detector",
        "market-breadth-analyzer",
        "market-top-detector",
        "parabolic-short-trade-planner",
        "pead-screener",
        "residual-edge-analyzer",
        "stockbee-episodic-pivot-analyzer",
        "stockbee-momentum-burst-screener",
        "vcp-screener",
    ),
    "EXECUTION_DISCIPLINE_RISK_AND_POSTMORTEM": (
        "data-quality-checker",
        "drawdown-circuit-breaker",
        "early-mover-compounding-goal",
        "position-sizer",
        "pre-trade-discipline-gate",
        "signal-postmortem",
        "trader-memory-core",
    ),
    "VENDORED_SCIENTIFIC_AND_SECURITY_FOUNDATION": (
        "aeon",
        "exploratory-data-analysis",
        "hypothesis-generation",
        "polars",
        "scikit-learn",
        "security-audit",
        "statistical-analysis",
        "statsmodels",
    ),
}

CANONICAL_46_SOTA_SKILLS: tuple[str, ...] = tuple(sorted({sk for grp in SKILL_FAMILIES.values() for sk in grp}))

EXTENDED_11_SOTA_SKILLS: tuple[str, ...] = (
    "orca-computer-use",
    "orca-per-workspace-env",
    "orca-plugin-authoring",
    "sota-7feed-pit-convergence",
    "sota-ao-multi-model-convergence",
    "sota-boats-23x5-cutover",
    "sota-dual-workstation-orca",
    "sota-nautilus-queue-parity",
    "sota-prewall-compounding-gate",
    "sota-visual-diagram-craft",
    "sota-zero-leak-merge-gate",
)

CANONICAL_57_SOTA_SKILLS: tuple[str, ...] = tuple(sorted(set(CANONICAL_46_SOTA_SKILLS) | set(EXTENDED_11_SOTA_SKILLS)))

EXTENDED_3_REDTEAM_SKILLS: tuple[str, ...] = (
    "sota-loopforge-convergence",
    "sota-redteam-bughunter",
    "sota-skill-evaluator",
)

CANONICAL_60_SOTA_SKILLS: tuple[str, ...] = tuple(
    sorted(set(CANONICAL_57_SOTA_SKILLS) | set(EXTENDED_3_REDTEAM_SKILLS))
)

CANONICAL_14_LAYERS_MATRIX: dict[str, dict[str, Any]] = {
    "L0": {
        "name": "lean-global-charters-and-provisioning",
        "lane": "H1",
        "skills": ("sota-spec-and-adr-gate", "planning-with-files", "sota-workflow"),
        "workflows": ("ecosystem-convergence", "sota-skills-adr-and-orca-grand-workflow"),
        "repos": (".github", "native-agent-stack", "sota-harness-foundation", "agy-sota-harness"),
    },
    "L1": {
        "name": "lifecycle-hooks-firewall-and-lease-guard",
        "lane": "H1",
        "skills": ("sota-peer-bus-and-handover", "pre-trade-discipline-gate", "security-audit"),
        "workflows": ("security-and-release-gate", "master-sota-harness"),
        "repos": ("agy-sota-harness", "cc-sota-harness", "sota-harness-foundation"),
    },
    "L2": {
        "name": "cross-peer-46-skills-and-mcp-mesh",
        "lane": "H2",
        "skills": ("sota-workflow", "orca-cli", "cc-lead-multi-runtime-orchestrator"),
        "workflows": ("sota-skills-adr-and-orca-grand-workflow", "cc-lead-multi-runtime-workers"),
        "repos": ("agy-sota-harness", "cc-sota-harness", "dsh-sota-harness", "dsh-plugin-landscape"),
    },
    "L3": {
        "name": "ast-symbol-graph-and-18pin-shelf-fts5",
        "lane": "H1",
        "skills": ("sota-ast-codemod", "polars", "statsmodels", "scikit-learn", "aeon"),
        "workflows": ("master-sota-harness", "research-convergence-landing"),
        "repos": ("sota-upstream-shelf-lock", "agy-sota-harness"),
    },
    "L4": {
        "name": "madr40-adr-governance-and-lineage",
        "lane": "H3",
        "skills": ("sota-spec-and-adr-gate", "data-quality-checker", "council-of-high-intelligence"),
        "workflows": ("compounding-versioning-and-ranking-adr", "council-deliberation"),
        "repos": ("canon", ".github", "native-agent-stack", "meridian"),
    },
    "L5": {
        "name": "native-18-workflow-dags-and-enactor",
        "lane": "H2",
        "skills": ("sota-workflow", "orchestration", "planning-with-files"),
        "workflows": (
            "sota-skills-adr-and-orca-grand-workflow",
            "multi-model-omc-memory-assign",
            "master-sota-harness",
        ),
        "repos": ("sota-multi-model-workflows", "agy-sota-harness"),
    },
    "L6": {
        "name": "anti-slop-institutional-ui-and-blotter",
        "lane": "T3",
        "skills": ("sota-taste-anti-slop", "sota-mover-ranker"),
        "workflows": ("early-mover-compounding", "master-sota-harness"),
        "repos": ("sota-mover-ranker", "sota-dynamic-trail-c"),
    },
    "L7": {
        "name": "sqlite-wal-peer-bus-wiki-and-fts5-sandbox",
        "lane": "H3",
        "skills": ("sota-peer-bus-and-handover", "trader-memory-core", "sota-skillopt-self-evolution"),
        "workflows": ("rd-agent-hypothesis-bus", "skillopt-gepa-evolution"),
        "repos": ("sota-multi-model-workflows", "sota-private-vault"),
    },
    "L8": {
        "name": "deterministic-verification-astgrep-and-tdd",
        "lane": "H1",
        "skills": (
            "sota-verification-and-security-gate",
            "sota-tdd-superpowers",
            "sota-dimensional-and-property-invariants",
            "security-audit",
        ),
        "workflows": ("security-and-release-gate", "cross-peer-orca-review"),
        "repos": ("agy-sota-harness", "meridian", "trading-sota", "tsl"),
    },
    "L9": {
        "name": "paper-execution-24x5-guardian-and-circuit-breaker",
        "lane": "T3",
        "skills": (
            "early-mover-compounding-goal",
            "sota-mover-ranker",
            "drawdown-circuit-breaker",
            "position-sizer",
            "pre-trade-discipline-gate",
            "signal-postmortem",
        ),
        "workflows": ("early-mover-compounding", "org-compounding-promotion"),
        "repos": ("sota-mover-ranker", "sota-dynamic-trail-c", "astrolabe"),
    },
    "L10": {
        "name": "dual-machine-orca-workstation-and-automations",
        "lane": "H2",
        "skills": ("orca-cli", "orchestration", "sota-workflow"),
        "workflows": ("dual-workstation-orca", "dual-machine-trading-and-harness-lanes"),
        "repos": ("cc-sota-harness", "sota-harness-foundation", "sota-multi-model-workflows"),
    },
    "L11": {
        "name": "cc-lead-11worker-17binary-multi-model-hub",
        "lane": "H2",
        "skills": ("cc-lead-multi-runtime-orchestrator", "orchestration", "council-of-high-intelligence"),
        "workflows": ("cc-lead-multi-runtime-workers", "multi-model-ao-convergence"),
        "repos": ("cc-sota-harness", "sota-multi-model-workflows", "dsh-sota-harness"),
    },
    "L12": {
        "name": "trading-and-harness-lanes-9feed-engines",
        "lane": "T1",
        "skills": (
            "microstructure-and-sec-catalyst-lab",
            "stockbee-episodic-pivot-analyzer",
            "stockbee-momentum-burst-screener",
            "parabolic-short-trade-planner",
            "vcp-screener",
            "pead-screener",
            "earnings-trade-analyzer",
            "institutional-flow-tracker",
            "macro-regime-detector",
            "market-breadth-analyzer",
            "market-top-detector",
            "ftd-detector",
        ),
        "workflows": ("research-convergence-landing", "dual-machine-trading-and-harness-lanes"),
        "repos": ("sota-mover-ranker", "meridian", "trading-sota", "tsl", "astrolabe"),
    },
    "L13": {
        "name": "prewall-hlz-cpcv-dsr-and-4hash-compounding-versioning",
        "lane": "T2",
        "skills": (
            "sota-quant-research-protocol",
            "autoresearch-loop",
            "backtest-expert",
            "residual-edge-analyzer",
            "hypothesis-generation",
            "exploratory-data-analysis",
            "statistical-analysis",
        ),
        "workflows": (
            "compounding-versioning-and-ranking-adr",
            "autoresearch-loop",
            "org-compounding-promotion",
        ),
        "repos": ("sota-compounding-lab", "sota-upstream-shelf-lock", "canon", "sota-private-vault"),
    },
}

_EXCLUDED_ADR_DOCS = frozenset({"README.MD", "CATALOG.MD", "INDEX.MD", "TEMPLATE.MD", "0000-TEMPLATE.MD"})


def probe_installed_sota_skills(home: Path | None = None) -> dict[str, Any]:
    """Verify presence of all 46 core + 11 extended (57 canonical) SOTA skills across all 8 runtime mounts."""
    h = home or Path.home()
    agents_sk = h / ".agents" / "skills"
    peer_mounts = {
        "agents_canonical": agents_sk,
        "antigravity": h / ".gemini" / "config" / "skills",
        "claude_code": h / ".claude" / "skills",
        "codex": h / ".codex" / "skills",
    }
    all_8_runtime_mounts = {
        **peer_mounts,
        "opencode": h / ".config" / "opencode" / "skills",
        "dsh": h / ".dsh" / "skills",
        "pi": h / ".pi" / "agent" / "skills",
        "omp": h / ".omp" / "agent" / "skills",
        "muse": h / ".config" / "muse" / "skills",
    }
    present_canonical = sorted(sk for sk in CANONICAL_46_SOTA_SKILLS if (agents_sk / sk / "SKILL.md").is_file())
    missing_canonical = sorted(set(CANONICAL_46_SOTA_SKILLS) - set(present_canonical))
    present_57 = sorted(sk for sk in CANONICAL_57_SOTA_SKILLS if (agents_sk / sk / "SKILL.md").is_file())
    missing_57 = sorted(set(CANONICAL_57_SOTA_SKILLS) - set(present_57))
    present_60 = sorted(sk for sk in CANONICAL_60_SOTA_SKILLS if (agents_sk / sk / "SKILL.md").is_file())
    missing_60 = sorted(set(CANONICAL_60_SOTA_SKILLS) - set(present_60))
    mount_counts: dict[str, int] = {}
    for label, pdir in peer_mounts.items():
        if pdir.is_dir():
            mount_counts[label] = sum(1 for sk in CANONICAL_46_SOTA_SKILLS if (pdir / sk / "SKILL.md").is_file())
        else:
            mount_counts[label] = 0
    all_8_runtime_mounts_57_count: dict[str, int] = {}
    all_8_runtime_mounts_60_count: dict[str, int] = {}
    for label, pdir in all_8_runtime_mounts.items():
        if pdir.is_dir():
            all_8_runtime_mounts_57_count[label] = sum(
                1 for sk in CANONICAL_57_SOTA_SKILLS if (pdir / sk / "SKILL.md").is_file()
            )
            all_8_runtime_mounts_60_count[label] = sum(
                1 for sk in CANONICAL_60_SOTA_SKILLS if (pdir / sk / "SKILL.md").is_file()
            )
        else:
            all_8_runtime_mounts_57_count[label] = 0
            all_8_runtime_mounts_60_count[label] = 0

    return {
        "expected_count": len(CANONICAL_46_SOTA_SKILLS),
        "present_count": len(present_canonical),
        "missing_skills": missing_canonical,
        "mount_counts": mount_counts,
        "families": {k: list(v) for k, v in SKILL_FAMILIES.items()},
        "all_present_in_canonical": len(missing_canonical) == 0,
        "extended_57_expected_count": len(CANONICAL_57_SOTA_SKILLS),
        "extended_57_present_count": len(present_57),
        "extended_57_missing_skills": missing_57,
        "all_57_present_in_canonical": len(missing_57) == 0,
        "all_8_runtime_mounts_57_count": all_8_runtime_mounts_57_count,
        "canonical_60_expected_count": len(CANONICAL_60_SOTA_SKILLS),
        "canonical_60_present_count": len(present_60),
        "canonical_60_missing_skills": missing_60,
        "all_60_present_in_canonical": len(missing_60) == 0,
        "all_8_runtime_mounts_60_count": all_8_runtime_mounts_60_count,
    }


def discover_ecosystem_adr_index(home: Path | None = None) -> dict[str, Any]:
    """Scan all 18 active repositories on disk and build a deterministic MADR 4.0 ADR index & SHA-256."""
    repo_adrs: dict[str, dict[str, Any]] = {}
    total_adrs = 0
    for repo_name in ACTIVE_18_REPOS:
        rdir = resolve_ecosystem_repo_dir(repo_name, home=home)
        # Handle ~/sota-dynamic-trail-c and ~/canon primary paths on Mac
        if repo_name == "canon" and not rdir.is_dir() and ((home or Path.home()) / "canon").is_dir():
            rdir = (home or Path.home()) / "canon"
        if (
            repo_name == "sota-dynamic-trail-c"
            and not rdir.is_dir()
            and ((home or Path.home()) / "sota-dynamic-trail-c").is_dir()
        ):
            rdir = (home or Path.home()) / "sota-dynamic-trail-c"

        adr_dir = rdir / "docs" / "adr"
        files: list[str] = []
        if adr_dir.is_dir():
            files = sorted(p.name for p in adr_dir.glob("*.md") if p.name.upper() not in _EXCLUDED_ADR_DOCS)
        total_adrs += len(files)
        lane_meta = REPO_LANE_INDEX.get(repo_name, {})
        repo_adrs[repo_name] = {
            "on_disk": rdir.is_dir(),
            "lane_id": lane_meta.get("lane_id", "H3"),
            "plane": lane_meta.get("plane", "harness"),
            "adr_count": len(files),
            "latest_adr": files[-1] if files else None,
            "has_orca_yaml": (rdir / "orca.yaml").is_file(),
            "has_upstream_md": (rdir / "UPSTREAM.md").is_file(),
        }

    digest_src = json.dumps(
        {k: {"cnt": v["adr_count"], "latest": v["latest_adr"]} for k, v in sorted(repo_adrs.items())},
        sort_keys=True,
    )
    return {
        "active_repos_count": len(ACTIVE_18_REPOS),
        "repos_on_disk": sum(1 for v in repo_adrs.values() if v["on_disk"]),
        "total_adr_count": total_adrs,
        "adr_index_sha256": hashlib.sha256(digest_src.encode("utf-8")).hexdigest(),
        "repositories": repo_adrs,
    }


def select_workflow_and_skills(
    *,
    goal: str,
    repo: str = "",
    layer: str = "all",
    workflow_id: str = "auto",
) -> dict[str, Any]:
    """Deterministically bind SOTA skills, governing ADRs, 9-Feed PIT rules, and canonical workflow."""
    g_low = goal.lower()
    norm_layer = layer.upper() if layer and layer.lower() != "all" else "ALL"

    if workflow_id and workflow_id != "auto":
        chosen_wf = workflow_id
    elif any(k in g_low for k in ("redteam", "red-team", "bughunter", "skilleval", "skill-evaluator", "loopforge")):
        chosen_wf = "redteam-skilleval-convergence-loop"
    elif any(k in g_low for k in ("merit", "3 paper", "multi-paper", "lossless live", "stage-5 live", "p3")):
        chosen_wf = "grand-merit-harness"
    elif any(k in g_low for k in ("orca-lead", "orca lead", "e2e convergence", "df12", "symbol ranking")):
        chosen_wf = "orca-lead-e2e-research-convergence"
    elif any(k in g_low for k in ("grand", "all layers", "all adrs", "enact", "native workflow", "sota skills")):
        chosen_wf = "sota-skills-adr-and-orca-grand-workflow"
    elif any(k in g_low for k in ("version", "semver", "ranking", "df1", "df9")):
        chosen_wf = "compounding-versioning-and-ranking-adr"
    elif any(k in g_low for k in ("lane", "dual-machine", "noesis", "t1", "h1")):
        chosen_wf = "dual-machine-trading-and-harness-lanes"
    elif any(k in g_low for k in ("assign", "qmd", "memory-sync", "stop-callback")):
        chosen_wf = "multi-model-omc-memory-assign"
    elif any(k in g_low for k in ("cc-lead", "omc", "multi-runtime", "11 worker")):
        chosen_wf = "cc-lead-multi-runtime-workers"
    elif any(k in g_low for k in ("hypothes", "pre-wall", "cpcv", "dsr", "hlz", "autoresearch")):
        chosen_wf = "autoresearch-loop"
    elif any(k in g_low for k in ("paper", "early mover", "8787", "8799", "bracket")):
        chosen_wf = "early-mover-compounding"
    elif any(k in g_low for k in ("council", "premortem", "deliberat")):
        chosen_wf = "council-deliberation"
    elif any(k in g_low for k in ("security", "release", "merge_gate", "gitleaks")):
        chosen_wf = "security-and-release-gate"
    else:
        chosen_wf = "master-sota-harness"

    wf_script_map = {
        "master-sota-harness": "master_sota_harness_workflow.py",
        "org-compounding-promotion": "org_compounding_promotion_workflow.py",
        "ecosystem-convergence": "ecosystem_convergence_workflow.py",
        "council-deliberation": "council_deliberation_workflow.py",
        "autoresearch-loop": "autoresearch_loop_workflow.py",
        "security-and-release-gate": "security_and_release_gate_workflow.py",
        "early-mover-compounding": "early_mover_compounding_workflow.py",
        "rd-agent-hypothesis-bus": "rd_agent_hypothesis_bus_workflow.py",
        "cross-peer-orca-review": "cross_peer_orca_review_workflow.py",
        "skillopt-gepa-evolution": "skillopt_gepa_evolution_workflow.py",
        "dual-workstation-orca": "dual_workstation_orca_workflow.py",
        "multi-model-ao-convergence": "ao_multi_model_convergence_workflow.py",
        "research-convergence-landing": "research_convergence_landing_workflow.py",
        "cc-lead-multi-runtime-workers": "cc_lead_multi_runtime_workers_workflow.py",
        "dual-machine-trading-and-harness-lanes": "dual_machine_trading_and_harness_lanes_workflow.py",
        "compounding-versioning-and-ranking-adr": "compounding_versioning_and_ranking_adr_workflow.py",
        "sota-skills-adr-and-orca-grand-workflow": "sota_skills_adr_and_orca_grand_workflow.py",
        "multi-model-omc-memory-assign": "multi_model_omc_memory_assign_workflow.py",
        "orca-lead-e2e-research-convergence": "orca_lead_e2e_research_convergence_workflow.py",
        "grand-merit-harness": "grand_merit_harness_workflow.py",
        "redteam-skilleval-convergence-loop": "redteam_skilleval_and_convergence_loop_workflow.py",
    }
    script_name = wf_script_map.get(chosen_wf, "sota_skills_adr_and_orca_grand_workflow.py")

    if norm_layer in CANONICAL_14_LAYERS_MATRIX:
        active_layers = [norm_layer]
    else:
        active_layers = list(CANONICAL_14_LAYERS_MATRIX.keys())

    bound_skills: set[str] = {
        "sota-workflow",
        "sota-peer-bus-and-handover",
        "sota-spec-and-adr-gate",
        "sota-verification-and-security-gate",
        "orca-cli",
        "orchestration",
        "cc-lead-multi-runtime-orchestrator",
    }
    for lid in active_layers:
        bound_skills.update(CANONICAL_14_LAYERS_MATRIX[lid]["skills"])

    target_repo = repo if repo in REPO_LANE_INDEX else "native-agent-stack"
    cv_status = build_compounding_version_status()
    lane_plan = resolve_dual_machine_lane_plan(
        target_repo,
        workload="combinatorial_gpu_sweep" if "pre-wall" in g_low or "cpcv" in g_low else "parallel_worktree_impl",
    )
    cc_plan = build_cc_lead_execution_plan(
        CCLeadPlanRequest(
            repo=target_repo,
            goal=goal,
            task_class="parallel_worktree_implementation",
        ),
        hlz_trials_n=int(cv_status["trials_n"]),
        hlz_next_t_hurdle=float(cv_status["next_trial_hlz_t_hurdle"]),
    )
    rc_env = build_workflow_research_convergence_envelope(
        workflow_id=chosen_wf,
        repo=target_repo,
        archetype="PRE_TRAVEL_EARLY_IGNITION",
        upstream_pins=dict(UPSTREAM_SHELF_PINS_18),
    )
    adr_index = discover_ecosystem_adr_index()

    script_rel = f"~/.agents/workflows/{script_name}"
    safe_goal = shlex.quote(goal)

    runtime_enactments = {
        "antigravity_run_workflow": {
            "tool": "run_workflow",
            "ScriptPath": script_rel,
            "Args": {"goal": goal, "repo": target_repo, "layer": norm_layer.lower()},
            "Description": f"SOTA Native Workflow ({chosen_wf}) across {len(active_layers)} layers & 12-Feed DF1..DF12 PIT",
        },
        "cross_runtime_workflow_run": f"sota-workflow run {chosen_wf} --repo {target_repo} --json",
        "orca_supervised_worker": lane_plan["orca_worker_start_cmd"],
        "orca_lane_hub_worktree": lane_plan["orca_folder_worktree_cmd"],
        "cc_lead_omc_team": cc_plan["channels"]["2_omc_team_swarm_cmd"],
        "cc_lead_ultragoal": cc_plan["channels"]["1_cc_lead_ultragoal_cmd"],
        "codex_omx_exec": f"omx exec -c 'model=\"gpt-6.2-astra\"' {safe_goal}",
        "opencode_omo_hephaestus": f"opencode run {safe_goal}",
        "deepseek_dsh_prewall": f"dsh headless {safe_goal}",
        "pi_omp_role_worker": f"omp --model @worker --thinking=high -p {safe_goal}",
        "pi_worker": f"pi --model openai-codex/gpt-6.2-sol --thinking=high -p {safe_goal}",
        "muse_critic": f"omc ask muse --agent-prompt critic --prompt {safe_goal}",
    }

    receipt_payload = json.dumps(
        {
            "wf": chosen_wf,
            "repo": target_repo,
            "layers": active_layers,
            "skills": sorted(bound_skills),
            "rc_sha": rc_env["envelope_input_sha256"],
            "adr_sha": adr_index["adr_index_sha256"],
            "df_sha": cv_status["ranking_datafeed_contract_sha256"],
        },
        sort_keys=True,
    )
    enactment_sha256 = hashlib.sha256(receipt_payload.encode("utf-8")).hexdigest()

    return {
        "ok": bool(rc_env["valid"] and cv_status["ok"]),
        "schema_version": NATIVE_WORKFLOW_ENACTOR_SCHEMA,
        "ecosystem_semver": DEFAULT_ECOSYSTEM_SEMVER,
        "workstation_surface": detect_workstation_surface(),
        "workflow_id": chosen_wf,
        "script_path": script_rel,
        "target_repo": target_repo,
        "layers_enacted": active_layers,
        "layers_count": len(active_layers),
        "skills_enacted_count": len(bound_skills),
        "skills_enacted": sorted(bound_skills),
        "ranking_datafeeds_schema": RANKING_DATAFEEDS_SCHEMA_VERSION,
        "backward_compat_feeds_schema": RESEARCH_FEEDS_SCHEMA_VERSION,
        "ranking_feeds_count": len(CANONICAL_RANKING_DATAFEEDS_V38),
        "strategy_archetypes": list(CANONICAL_STRATEGY_ARCHETYPES),
        "prewall_lake_sha256": DEFAULT_PREWALL_LAKE_SHA256,
        "pre_wall_max_date": PRE_WALL_MAX_DATE,
        "max_hard_stop_pct": MAX_HARD_STOP_PCT,
        "sibling_repo_authority": SIBLING_REPO_AUTHORITY,
        "hlz_trials_n": cv_status["trials_n"],
        "next_trial_hlz_t_hurdle": cv_status["next_trial_hlz_t_hurdle"],
        "lessons_count": cv_status["lessons_count"],
        "adr_governance": {
            "active_repos_count": adr_index["active_repos_count"],
            "total_adr_count": adr_index["total_adr_count"],
            "adr_index_sha256": adr_index["adr_index_sha256"],
            "target_repo_adr": adr_index["repositories"].get(target_repo, {}),
        },
        "multi_model_fleet": {
            "lead_orchestrator": CC_LEAD_CENTRAL_CONTRACT["lead_model_id"],
            "runtime_workers_count": len(RUNTIME_WORKER_ROSTER),
            "orchestration_frameworks_count": len(ORCHESTRATION_FRAMEWORKS_MATRIX),
            "model_vendors_count": len(CANONICAL_SEVEN_MODEL_VENDORS),
            "orca_lane_hubs": ORCA_LANE_HUBS,
            "selected_lane": {
                "lane_id": lane_plan["lane_id"],
                "plane": lane_plan["plane"],
                "selected_surface": lane_plan["selected_surface"],
                "single_broker_host_enforced": True,
            },
        },
        "runtime_enactments": runtime_enactments,
        "enactment_sha256": enactment_sha256,
    }


def _read_ecosystem_lock_semver(home: Path | None = None) -> str:
    nas_dir = resolve_ecosystem_repo_dir("native-agent-stack", home=home)
    lock_path = nas_dir / "ECOSYSTEM_CONVERGENCE_LOCK.json"
    if lock_path.is_file():
        try:
            ver = str(json.loads(lock_path.read_text(encoding="utf-8")).get("schemaVersion") or "").strip()
            if ver:
                return ver
        except (OSError, ValueError, TypeError):
            pass
    return DEFAULT_ECOSYSTEM_SEMVER


def build_grand_native_workflow_status(home: Path | None = None) -> dict[str, Any]:
    """Build complete status across all 57 skills (46 core + 11 extended), 20 workflows, 14 layers, 18 ADR catalogs, & Orca."""
    skills_st = probe_installed_sota_skills(home=home)
    adr_idx = discover_ecosystem_adr_index(home=home)
    cv_st = build_compounding_version_status()
    return {
        "ok": bool(cv_st["ok"] and skills_st["present_count"] >= 17 and adr_idx["active_repos_count"] == 18),
        "schema_version": NATIVE_WORKFLOW_ENACTOR_SCHEMA,
        "ecosystem_semver": DEFAULT_ECOSYSTEM_SEMVER,
        "ecosystem_lock_semver": _read_ecosystem_lock_semver(home=home),
        "workstation_surface": detect_workstation_surface(home=home),
        "canonical_workflows_count": 21,
        "canonical_skills_total": len(CANONICAL_46_SOTA_SKILLS),
        "canonical_57_skills_total": len(CANONICAL_57_SOTA_SKILLS),
        "canonical_60_skills_total": len(CANONICAL_60_SOTA_SKILLS),
        "skills_status": skills_st,
        "layers_count": len(CANONICAL_14_LAYERS_MATRIX),
        "layers": {k: v["name"] for k, v in CANONICAL_14_LAYERS_MATRIX.items()},
        "trading_lanes_count": len(TRADING_LANES),
        "harness_lanes_count": len(HARNESS_LANES),
        "domain_lanes_count": len(ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES),
        "canonical_lane_leads_count": len(CANONICAL_ORCA_LANE_LEADS),
        "ranking_datafeeds_schema": RANKING_DATAFEEDS_SCHEMA_VERSION,
        "ranking_feeds_count": len(CANONICAL_RANKING_DATAFEEDS_V38),
        "symbol_ranking_v310_schema": cv_st["symbol_ranking_v310_schema"],
        "symbol_ranking_v310_feeds_count": cv_st["symbol_ranking_v310_feeds_count"],
        "runtime_workers_count": len(RUNTIME_WORKER_ROSTER),
        "orchestration_frameworks_count": len(ORCHESTRATION_FRAMEWORKS_MATRIX),
        "model_vendors_count": len(CANONICAL_SEVEN_MODEL_VENDORS),
        "adr_governance": {
            "active_repos_count": adr_idx["active_repos_count"],
            "repos_on_disk": adr_idx["repos_on_disk"],
            "total_adr_count": adr_idx["total_adr_count"],
            "adr_index_sha256": adr_idx["adr_index_sha256"],
        },
        "compounding_ledger": {
            "trials_n": cv_st["trials_n"],
            "next_trial_hlz_t_hurdle": cv_st["next_trial_hlz_t_hurdle"],
            "lessons_count": cv_st["lessons_count"],
            "prewall_lake_sha256": DEFAULT_PREWALL_LAKE_SHA256,
        },
    }


def _build_schema_fallback(schema: dict[str, Any], channel: str) -> dict[str, Any]:
    props = schema.get("properties") or {}
    out: dict[str, Any] = {}
    reject_tokens = {"DISCARD", "REJECT", "FAIL", "BLOCK", "BLOCKED", "REVISE"}
    for key, spec in props.items():
        if not isinstance(spec, dict):
            out[key] = channel
            continue
        enum_vals = spec.get("enum")
        if enum_vals:
            rejecting = [v for v in enum_vals if str(v).upper() in reject_tokens]
            out[key] = rejecting[0] if ("verdict" in key.lower() and rejecting) else enum_vals[0]
        elif spec.get("type") == "boolean":
            out[key] = True
        elif spec.get("type") == "integer":
            out[key] = 1
        elif spec.get("type") == "number":
            out[key] = 1.0
        elif spec.get("type") == "array":
            out[key] = [channel]
        else:
            out[key] = channel
    return out


def run_workflow_cli(
    workflow_id: str,
    *,
    repo: str = "cc-sota-harness",
    args_dict: dict[str, Any] | None = None,
    mode: str = "deterministic",
    dry_run: bool = False,
    workflows_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute any canonical REGISTRY.json workflow from CLI across all 8 runtimes (with top-level await support)."""
    import ast
    import asyncio
    import contextlib
    import io
    import os
    import shutil
    import subprocess
    import types

    reg_root = workflows_dir or (Path(__file__).resolve().parents[2] / "workflows")
    if not (reg_root / "REGISTRY.json").is_file():
        reg_root = Path.home() / ".agents" / "workflows"
    reg = json.loads((reg_root / "REGISTRY.json").read_text(encoding="utf-8"))
    match = next((w for w in reg.get("workflows", []) if w.get("id") == workflow_id), None)
    if match is None:
        raise ValueError(f"Unknown workflow_id {workflow_id!r}")

    script_path = reg_root / Path(str(match["script_path"])).name
    src = script_path.read_text(encoding="utf-8")
    merged_args: dict[str, Any] = dict(args_dict or {})
    merged_args.setdefault("repo", repo)
    if "fast_deterministic_only" not in merged_args:
        merged_args["fast_deterministic_only"] = mode == "deterministic"

    repo_dir = resolve_ecosystem_repo_dir(repo)
    logs: list[str] = []
    phases: list[str] = []
    live_calls = 0

    def _invoke_codex_sync(codex_bin: str, sys_prompt: str) -> dict[str, Any] | None:
        try:
            proc = subprocess.run(
                [codex_bin, "exec", "--skip-git-repo-check", "-c", 'model="gpt-6.2-sol"', sys_prompt],
                cwd=str(repo_dir) if repo_dir.is_dir() else None,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=45,
                check=False,
            )
            txt = proc.stdout.strip()
            start = txt.find("{")
            end = txt.rfind("}")
            if proc.returncode == 0 and start >= 0 and end > start:
                parsed = json.loads(txt[start : end + 1])
                if isinstance(parsed, dict):
                    return parsed
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            pass
        return None

    async def _cli_agent(
        prompt: str, schema: dict[str, Any], role: str = "", type_name: str = "self"
    ) -> dict[str, Any]:
        nonlocal live_calls
        if mode == "live-cli":
            codex_bin = shutil.which("codex")
            if codex_bin:
                sys_prompt = (
                    f"Role: {role or type_name}. Return ONLY raw JSON matching keys "
                    f"{sorted((schema.get('properties') or {}).keys())}.\n\n{prompt[:3500]}"
                )
                parsed = await asyncio.to_thread(_invoke_codex_sync, codex_bin, sys_prompt)
                if parsed is not None:
                    live_calls += 1
                    return parsed
        return _build_schema_fallback(schema, f"{mode}_fallback:{type_name}")

    async def _cli_parallel(items: list[Any], fn: Any) -> list[Any]:
        return [await fn(it) for it in items]

    ns: dict[str, Any] = {
        "__name__": "__main__",
        "__file__": str(script_path),
        "args": merged_args,
        "WORKSPACES": (str(repo_dir),),
        "log": lambda *a: logs.append(" ".join(str(x) for x in a)),
        "phase": lambda name: phases.append(str(name)),
        "agent": _cli_agent,
        "parallel": _cli_parallel,
    }
    code_obj = compile(src, "<workflow>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    buf = io.StringIO()
    prev_dry = os.environ.get("SOTA_WORKFLOW_DRY_RUN")
    skip_bus_writes = bool(dry_run or mode == "deterministic")
    try:
        if skip_bus_writes:
            os.environ["SOTA_WORKFLOW_DRY_RUN"] = "1"
        with contextlib.redirect_stdout(buf):
            coro = eval(code_obj, ns)
            if isinstance(coro, types.CoroutineType):
                asyncio.run(coro)
    finally:
        if prev_dry is None:
            os.environ.pop("SOTA_WORKFLOW_DRY_RUN", None)
        else:
            os.environ["SOTA_WORKFLOW_DRY_RUN"] = prev_dry

    stdout_text = buf.getvalue().strip()
    parsed_output: Any = None
    if stdout_text:
        try:
            parsed_output = json.loads(stdout_text)
        except json.JSONDecodeError:
            parsed_output = {"raw_stdout": stdout_text}

    return {
        "ok": True,
        "workflow_id": workflow_id,
        "repo": repo,
        "mode": mode,
        "dry_run": dry_run,
        "placeholder_outputs": live_calls == 0,
        "bus_writes_skipped": skip_bus_writes,
        "live_cli_calls": live_calls,
        "phases": phases,
        "logs_count": len(logs),
        "receipt": parsed_output if parsed_output is not None else ns.get("final_receipt"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sota-workflow",
        description="Unified SOTA Native Workflow, 46-Skill, 14-Layer, 18-Repo ADR & Dual-Machine Orca Enactor",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_st = sub.add_parser("status", help="Inspect 46 skills, 19 workflows, 14 layers, 18 ADR catalogs & Orca status")
    p_st.add_argument("--json", action="store_true")

    p_sk = sub.add_parser("skills", help="Audit 46 canonical SOTA skills across AGY, Claude, Codex & ~/.agents")
    p_sk.add_argument("--json", action="store_true")

    p_ly = sub.add_parser("layers", help="Show the 14-Layer (L0..L13) x Skills x Workflows x Repos matrix")
    p_ly.add_argument("--json", action="store_true")

    p_ad = sub.add_parser("adrs", help="Index MADR 4.0 ADRs across all 18 active native-agent-stack repos")
    p_ad.add_argument("--json", action="store_true")

    p_en = sub.add_parser("enact", help="Route & enact a goal across SOTA skills, ADRs, workflows & 11 runtimes")
    p_en.add_argument("--goal", required=True)
    p_en.add_argument("--repo", default="native-agent-stack")
    p_en.add_argument("--layer", default="all")
    p_en.add_argument("--workflow", default="auto")
    p_en.add_argument("--json", action="store_true")

    p_rn = sub.add_parser("run", help="Execute any canonical REGISTRY.json workflow from CLI across all 8 runtimes")
    p_rn.add_argument("workflow_id", help="Workflow ID from REGISTRY.json")
    p_rn.add_argument("--repo", default="cc-sota-harness")
    p_rn.add_argument("--args-json", default="{}")
    p_rn.add_argument("--mode", default="deterministic", choices=("deterministic", "live-cli"))
    p_rn.add_argument("--dry-run", action="store_true")
    p_rn.add_argument("--json", action="store_true")

    p_pc = sub.add_parser("precheck", help="Fast exit-0 precheck gate for scheduled Orca automations")
    p_pc.add_argument("--surface", default="auto")

    args = parser.parse_args(argv)
    if args.cmd == "status":
        st = build_grand_native_workflow_status()
        print(json.dumps(st, indent=2))
        return 0 if st["ok"] else 1
    if args.cmd == "skills":
        print(json.dumps(probe_installed_sota_skills(), indent=2))
        return 0
    if args.cmd == "layers":
        print(json.dumps(CANONICAL_14_LAYERS_MATRIX, indent=2))
        return 0
    if args.cmd == "adrs":
        print(json.dumps(discover_ecosystem_adr_index(), indent=2))
        return 0
    if args.cmd == "enact":
        res = select_workflow_and_skills(
            goal=args.goal,
            repo=args.repo,
            layer=args.layer,
            workflow_id=args.workflow,
        )
        print(json.dumps(res, indent=2))
        return 0 if res["ok"] else 1
    if args.cmd == "run":
        extra_args = json.loads(args.args_json)
        run_res = run_workflow_cli(
            args.workflow_id,
            repo=args.repo,
            args_dict=extra_args if isinstance(extra_args, dict) else {},
            mode=args.mode,
            dry_run=args.dry_run,
        )
        print(json.dumps(run_res, indent=2))
        return 0 if run_res["ok"] else 1
    if args.cmd == "precheck":
        st = build_grand_native_workflow_status()
        return 0 if st["ok"] else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
