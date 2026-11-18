"""Multi-Model SOTA Agent Orchestrator (`AO`) Convergence & Lifecycle Qualification Engine (`ADR-0008`).

Converges `ComposioHQ/agent-orchestrator` (`ao` 8-slot pluggable lifecycle), the harvested `northstar-ao-sandbox`
frozen-assertion & explicit-landing qualification line (`issue -> isolated-worktree-worker -> PR/gate -> cross-model
review -> bounded-reaction -> explicit-merge-receipt`), the 7-family multi-model CLI fabric (`ADR-0014`), and the
Dual-Machine `Mac M5 Max <-> Noesis 64c/RTX4090` Orca Workstation Lane (`ADR-0020`).
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import os
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

CONCRETE_VENDORS: frozenset[str] = frozenset({"google", "anthropic", "openai", "deepseek"})
AO_STUDY_WALL_DATE = dt.date(2026, 10, 15)

AO_PLUGGABLE_SLOTS: dict[str, str] = {
    "runtime": "7-family heterogeneous harnesses (antigravity, claude-code-omc, openai-codex-omx, opencode-omo, pi-omp, goose, deepseek-dsh)",
    "orchestrator": "antigravity run_workflow DAGs + stablyai/orca cross-runtime supervisor",
    "workspace": "isolated git worktree per worker (git worktree / worktrunk / orca --worktree new-child)",
    "lease_bus": "transactional SQLite WAL peer_bus.db + hcom real-time push notifications",
    "acceptance_contract": "frozen existing assertions (append-only tests) + ruff + ty + pytest + merge_gate + gitleaks + architecture_catalog",
    "adversarial_review": "strictly cross-vendor reviewer diversity + sota-falsifier + sota-code-verifier",
    "ci_reaction_loop": "bounded autonomous in-worktree remediation (max_reactions <= 3) without assertion weakening",
    "merge_disposition": "explicit SHA-256 qualification receipt (0 blind force-merge, 0 live-broker/secret touch, 0 private Actions burn)",
}

AO_MODEL_FAMILIES: dict[str, dict[str, str]] = {
    "antigravity": {"vendor": "google", "lead_model": "gemini-4-carbon-high", "cli": "agy"},
    "claude-code-omc": {"vendor": "anthropic", "lead_model": "claude-fable-5-2", "cli": "claude"},
    "openai-codex-omx": {"vendor": "openai", "lead_model": "gpt-6.2-astra", "cli": "codex"},
    "opencode-omo": {"vendor": "multi-router", "lead_model": "oh-my-openagent-graph", "cli": "opencode"},
    "pi-omp": {"vendor": "pi-multi", "lead_model": "oh-my-pi-runtime", "cli": "pi"},
    "goose": {"vendor": "aaif-open", "lead_model": "goose-autonomous", "cli": "goose"},
    "deepseek-dsh": {"vendor": "deepseek", "lead_model": "deepseek-v3-r1-harness", "cli": "dsh"},
}

AO_FLEET_BINARIES: tuple[str, ...] = (
    "orca",
    "claude",
    "codex",
    "gemini",
    "opencode",
    "pi",
    "goose",
    "dsh",
    "hcom",
    "wt",
    "omniroute",
)


@dataclasses.dataclass(frozen=True)
class AOMultiModelRoute:
    task_kind: str
    mesh_state: str
    lead_harness: str
    lead_vendor: str
    reviewer_harness: str
    reviewer_vendor: str
    specialist_agents: tuple[str, ...]
    workstation_host: str
    isolation_primitive: str


@dataclasses.dataclass(frozen=True)
class AOLifecycleAttempt:
    task_id: str
    repo: str
    head_commit_sha: str
    lead_harness: str
    reviewer_harness: str
    isolated_worktree: bool
    disjoint_peer_lease: bool
    upstream_sha_cited: bool
    frozen_assertions_deleted_or_weakened: int = 0
    lint_and_type_clean: bool = True
    tests_passed: int = 1
    tests_failed: int = 0
    merge_gate_and_adr_clean: bool = True
    gitleaks_clean: bool = True
    p0_p1_open_findings: int = 0
    reaction_iteration: int = 0
    max_reaction_iterations: int = 3
    repo_visibility: str = "PUBLIC"
    private_repo_actions_enabled: bool = False
    touches_live_broker: bool = False
    reads_raw_secrets: bool = False
    resolved_lead_vendor: str | None = None
    resolved_reviewer_vendor: str | None = None
    task_kind: str = "execution_risk_code"
    study_end_date: str | None = None


def derive_workstation_mesh_state(ws_json: Mapping[str, Any]) -> str:
    """Derive canonical mesh_state from `sota-workstation status --json` with safe offline Noesis failover."""
    noesis = ws_json.get("stationaryNoesis")
    mac = ws_json.get("portableMac")
    noesis_reachable = bool(noesis.get("reachable")) if isinstance(noesis, Mapping) else False
    on_ac = mac.get("onAcPower") if isinstance(mac, Mapping) else None

    raw_mesh = ws_json.get("meshState")
    if isinstance(raw_mesh, str) and raw_mesh.strip():
        if isinstance(noesis, Mapping) and noesis.get("reachable") is False and raw_mesh.startswith("dual_mesh"):
            return "portable_roaming_battery" if on_ac is False else "portable_roaming_ac"
        return raw_mesh.strip()

    if noesis_reachable:
        return "dual_mesh_docked"
    if on_ac is False:
        return "portable_roaming_battery"
    return "portable_roaming_ac"


def resolve_ao_multi_model_route(
    task_kind: str = "execution_risk_code",
    mesh_state: str = "dual_mesh_docked",
) -> AOMultiModelRoute:
    """Deterministically assign cross-vendor lead + reviewer harnesses & Dual-Machine Orca host placement."""
    routing_table: dict[str, tuple[str, str, tuple[str, ...]]] = {
        "architecture_adr": (
            "antigravity",
            "claude-code-omc",
            ("sota-deep-synthesizer", "sota-falsifier", "sota-code-verifier"),
        ),
        "prewall_quant_factor": (
            "claude-code-omc",
            "openai-codex-omx",
            ("sota-rd-proposer", "sota-falsifier", "sota-code-verifier"),
        ),
        "execution_risk_code": (
            "antigravity",
            "openai-codex-omx",
            ("sota-falsifier", "sota-code-verifier"),
        ),
        "cross_repo_refactor": (
            "openai-codex-omx",
            "claude-code-omc",
            ("sota-code-verifier",),
        ),
        "combinatorial_gpu_sweep": (
            "claude-code-omc",
            "antigravity",
            ("sota-rd-proposer", "sota-falsifier"),
        ),
    }
    lead_h, rev_h, specialists = routing_table.get(task_kind, routing_table["execution_risk_code"])
    lead_v = AO_MODEL_FAMILIES[lead_h]["vendor"]
    rev_v = AO_MODEL_FAMILIES[rev_h]["vendor"]

    noesis_eligible = mesh_state in ("dual_mesh_docked", "dual_mesh_on_battery")
    if noesis_eligible and (
        task_kind == "combinatorial_gpu_sweep"
        or (mesh_state == "dual_mesh_on_battery" and task_kind == "prewall_quant_factor")
    ):
        host = "noesis_64c_rtx4090"
    else:
        host = "mac_m5_max_local"

    return AOMultiModelRoute(
        task_kind=task_kind,
        mesh_state=mesh_state,
        lead_harness=lead_h,
        lead_vendor=lead_v,
        reviewer_harness=rev_h,
        reviewer_vendor=rev_v,
        specialist_agents=specialists,
        workstation_host=host,
        isolation_primitive="git_worktree_plus_sqlite_wal_lease",
    )


def _resolve_concrete_vendor(
    role_label: str,
    harness: str,
    harness_vendor: str,
    override: str | None,
    hard_blocks: list[str],
) -> str | None:
    if harness_vendor in CONCRETE_VENDORS:
        if override is not None and override.strip().lower() != harness_vendor:
            hard_blocks.append(
                f"{role_label} vendor override '{override}' conflicts with fixed harness '{harness}' ({harness_vendor})"
            )
            return None
        return harness_vendor
    if override is None or override.strip().lower() not in CONCRETE_VENDORS:
        hard_blocks.append(
            f"Multi-router {role_label} harness '{harness}' requires resolved_{role_label}_vendor in {sorted(CONCRETE_VENDORS)}"
        )
        return None
    return override.strip().lower()


def evaluate_ao_lifecycle_gate(attempt: AOLifecycleAttempt) -> dict[str, Any]:
    """Evaluate `northstar-ao-sandbox` + `ComposioHQ/agent-orchestrator` closed-loop qualification rules."""
    hard_blocks: list[str] = []
    remediable_failures: list[str] = []

    if not attempt.isolated_worktree:
        hard_blocks.append("AO worker must execute inside an isolated git worktree")
    if not attempt.disjoint_peer_lease:
        hard_blocks.append("Disjoint SQLite WAL peer lease required before editing")
    if attempt.frozen_assertions_deleted_or_weakened > 0:
        hard_blocks.append("Frozen acceptance assertions must never be deleted or weakened")
    if attempt.touches_live_broker:
        hard_blocks.append("Live-money broker endpoints and live ports are 100% hard-refused")
    if attempt.reads_raw_secrets:
        hard_blocks.append("Keyless/secret-isolated boundary violated")
    if attempt.repo_visibility.upper() == "PRIVATE" and attempt.private_repo_actions_enabled:
        hard_blocks.append("PRIVATE org repos must keep GitHub Actions disabled (0 quota burn)")

    if attempt.study_end_date is not None:
        try:
            parsed_end = dt.date.fromisoformat(attempt.study_end_date)
            if parsed_end > AO_STUDY_WALL_DATE:
                hard_blocks.append(
                    f"PREWALL_VIOLATION: study_end_date {attempt.study_end_date} > {AO_STUDY_WALL_DATE.isoformat()}"
                )
        except ValueError:
            hard_blocks.append(f"Invalid study_end_date '{attempt.study_end_date}' (expected YYYY-MM-DD)")

    lead_meta = AO_MODEL_FAMILIES.get(attempt.lead_harness)
    rev_meta = AO_MODEL_FAMILIES.get(attempt.reviewer_harness)
    if lead_meta is None or rev_meta is None:
        hard_blocks.append(f"Unregistered AO harness pair: {attempt.lead_harness} / {attempt.reviewer_harness}")
        cross_vendor_ok = False
    else:
        eff_lead = _resolve_concrete_vendor(
            "lead", attempt.lead_harness, lead_meta["vendor"], attempt.resolved_lead_vendor, hard_blocks
        )
        eff_rev = _resolve_concrete_vendor(
            "reviewer", attempt.reviewer_harness, rev_meta["vendor"], attempt.resolved_reviewer_vendor, hard_blocks
        )
        if eff_lead is not None and eff_rev is not None:
            cross_vendor_ok = eff_lead != eff_rev
            if not cross_vendor_ok:
                hard_blocks.append(
                    f"Same-vendor review prohibited ({eff_lead}); AO requires cross-family falsification"
                )
        else:
            cross_vendor_ok = False

    if len(attempt.head_commit_sha.strip()) < 7:
        remediable_failures.append("Missing valid Git commit SHA witness")
    if not attempt.upstream_sha_cited:
        remediable_failures.append("Missing pinned upstream reference citation")
    if not attempt.lint_and_type_clean:
        remediable_failures.append("Deterministic linter or static type-checker diagnostics present")
    if attempt.tests_passed <= 0 or attempt.tests_failed > 0:
        remediable_failures.append(f"Test gate failed (passed={attempt.tests_passed}, failed={attempt.tests_failed})")
    if not attempt.merge_gate_and_adr_clean:
        remediable_failures.append("merge_gate.py or MADR 4.0 catalog parity failed")
    if not attempt.gitleaks_clean:
        remediable_failures.append("gitleaks secret/path scan failed")
    if attempt.p0_p1_open_findings > 0:
        remediable_failures.append(f"{attempt.p0_p1_open_findings} open P0/P1 adversarial review finding(s)")

    if hard_blocks:
        disposition = "AO_HARD_BLOCKED"
        ready = False
    elif remediable_failures:
        if attempt.reaction_iteration < attempt.max_reaction_iterations:
            disposition = "AO_REACTION_REMEDIATION_REQUIRED"
        else:
            disposition = "AO_EXHAUSTED_ESCALATE_TO_OWNER"
        ready = False
    else:
        disposition = "AO_READY_FOR_EXPLICIT_LANDING"
        ready = True

    canonical_payload = json.dumps(
        {
            "task_id": attempt.task_id,
            "repo": attempt.repo,
            "head": attempt.head_commit_sha,
            "lead": attempt.lead_harness,
            "reviewer": attempt.reviewer_harness,
            "tests_passed": attempt.tests_passed,
            "disposition": disposition,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    receipt_sha256 = hashlib.sha256(canonical_payload).hexdigest()

    return {
        "task_id": attempt.task_id,
        "repo": attempt.repo,
        "head_commit_sha": attempt.head_commit_sha,
        "disposition": disposition,
        "ready_for_explicit_landing": ready,
        "cross_vendor_diversity_verified": cross_vendor_ok,
        "reaction_iteration": attempt.reaction_iteration,
        "max_reaction_iterations": attempt.max_reaction_iterations,
        "hard_blocks": hard_blocks,
        "remediable_failures": remediable_failures,
        "qualification_receipt_sha256": receipt_sha256,
    }


qualify_ao_lifecycle_attempt = evaluate_ao_lifecycle_gate


def probe_installed_multi_model_binaries(extra_dirs: Sequence[Path] | None = None) -> dict[str, Any]:
    """Probe installed multi-model CLI binaries without leaking local username paths."""
    home = Path.home()
    search_dirs = list(
        extra_dirs
        or (
            home / ".local" / "bin",
            home / ".local" / "share" / "mise" / "shims",
            home / ".agents" / "bin",
        )
    )
    path_env = os.environ.get("PATH", "")
    augmented_path = os.pathsep.join([*(str(d) for d in search_dirs if d.is_dir()), path_env])

    present: list[str] = []
    missing: list[str] = []
    for binary in AO_FLEET_BINARIES:
        if shutil.which(binary, path=augmented_path):
            present.append(binary)
        else:
            missing.append(binary)
    return {
        "checked_total": len(AO_FLEET_BINARIES),
        "installed_count": len(present),
        "installed_binaries": present,
        "missing_binaries": missing,
    }
