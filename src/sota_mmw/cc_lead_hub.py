"""Claude Code (`cc-lead` + `OMC` v2) Central Multi-Session & Multi-Runtime Worker Hub.

Positions Claude Code (`claude-fable-5-2` `xhigh` + `oh-my-claudecode` `OMC` runtime v2)
as the sovereign architectural & goal orchestrator (`oneModelPerConversation = True`)
dispatching isolated worktree and cross-session workers across:
1. `omc ultragoal` + Claude `/goal` (durable `.omc/ultragoal/` multi-session ledger)
2. `omc team` & `omc interop` (`OMC_RUNTIME_V2=1` multi-vendor tmux worktree swarms)
3. `omc ask` & `omx exec` / `omx mission` (`gpt-6.2-astra` / `gpt-6.2-sol` / `gemini-4-carbon-high` / `grok-4.7` / `muse-spark-1.3`)
4. `orca orchestration worker-start` (`Mac M5 Max <-> Noesis 64c/128GB/RTX4090` supervised DAG workers, zero polling)
5. Polyglot Open-Weights & Bus (`opencode`/`OMO` `kimi-k3.1-pro` non-GPT `Hephaestus`, `dsh` `deepseek-v4-pro`, `pi`/`omp`, `goose`, `hcom`, SQLite WAL `sota-bus`)
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sota_mmw.ao_lifecycle import (
    AO_STUDY_WALL_DATE,
    CONCRETE_VENDORS,
    derive_workstation_mesh_state,
    detect_disjoint_peer_lease,
    detect_isolated_worktree,
)


def is_running_on_noesis_host() -> bool:
    """Return True when executing directly on Stationary Noesis Win32 or Noesis-Carbon WSL2."""
    if os.name == "nt":
        return True
    if "noesis" in socket.gethostname().lower():
        return True
    return "noesis" in os.environ.get("WSL_DISTRO_NAME", "").lower()


def orca_remote_on_args(*, use_noesis: bool, flag: str = "--on") -> list[str]:
    """Emit Orca remote target flags without ever passing 100.110.115.22 to Noesis itself (#188)."""
    if is_running_on_noesis_host():
        return []
    return [flag, "100.110.115.22"] if use_noesis else []


QUALITY_DIRECTIVE_POWERHOUSE_FLEET: dict[str, dict[str, Any]] = {
    "anthropic_claude_1to1": {
        "vendor": "Anthropic",
        "benchmark_authority": "https://artificialanalysis.ai/models (Intelligence v5.0.1 #1 & Coding Agent v2.1 #1)",
        "lead_model": "claude-fable-5-2",
        "remaining_models": ("claude-opus-5-5", "claude-sonnet-5-5"),
        "target_fable_share": 0.50,
        "target_remaining_share": 0.50,
        "allowed_fable_band": (0.42, 0.58),
        "zero_haiku_sprawl": True,
    },
    "openai_codex_and_pi_omp": {
        "vendor": "OpenAI",
        "benchmark_authority": "https://artificialanalysis.ai/models (Intelligence v5.0.1 #2)",
        "reasoning_critic_model": "gpt-6.2-astra",
        "high_quality_execution_model": "gpt-6.2-sol",
        "runtimes": ("codex", "omx", "pi", "omp"),
        "default_effort": "high",
    },
    "google_deepmind_antigravity": {
        "vendor": "Google DeepMind",
        "benchmark_authority": "https://artificialanalysis.ai/models (Intelligence v5.0.1 #3 & #1 1M+ Context)",
        "model": "gemini-4-carbon-high",
        "runtimes": ("antigravity",),
        "default_effort": "high",
    },
    "deepseek_dsh_prewall": {
        "vendor": "DeepSeek",
        "benchmark_authority": "https://artificialanalysis.ai/models (Top Cost-Efficiency Pre-Wall Batch Sweep)",
        "model": "deepseek-v4-pro",
        "runtimes": ("dsh",),
        "default_effort": "high",
    },
}

CC_LEAD_CENTRAL_CONTRACT: dict[str, Any] = {
    "workspace_name": "cc-lead",
    "lead_runtime": "claude",
    "orchestrator_plugin": "oh-my-claudecode@omc",
    "lead_model_id": "claude-fable-5-2",
    "lead_effort": "xhigh",
    "claude_cli_fable_vs_remaining_target_ratio": "1:1",
    "one_model_per_conversation": True,
    "hephaestus_forbids_gpt_models": True,
    "paper_only_trading_firewall": True,
    "prewall_study_cutoff": AO_STUDY_WALL_DATE.isoformat(),
    "omc_worker_default_env": {
        "OMC_RUNTIME_V2": "1",
        "OMC_TEAM_WORKTREE_MODE": "branch",
        "OMC_MODEL_HIGH": "claude-fable-5-2",
        "OMC_MODEL_MEDIUM": "claude-sonnet-5-5",
        "OMC_MODEL_LOW": "claude-sonnet-5-5",
        "OMC_CODEX_DEFAULT_MODEL": "gpt-6.2-astra",
        "OMC_ANTIGRAVITY_DEFAULT_MODEL": "gemini-4-carbon-high",
        "OMC_GEMINI_DEFAULT_MODEL": "gemini-4-carbon-high",
        "OMC_GROK_DEFAULT_MODEL": "grok-4.7",
        "OMC_JEV_MAX_EFFORT": "xhigh",
    },
    "quality_directive_powerhouse_fleet": QUALITY_DIRECTIVE_POWERHOUSE_FLEET,
    "live_authenticated_worker_routes": ("cc-lead", "codex", "antigravity", "opencode", "dsh"),
    "binary_present_user_auth_pending_routes": ("gemini-cli", "muse", "grok", "goose", "pi", "omp-direct", "ccr"),
}

RUNTIME_WORKER_ROSTER: dict[str, dict[str, str]] = {
    "claude-sonnet-omc": {
        "binary": "claude",
        "orca_agent": "claude",
        "omc_spec": "1:claude:executor",
        "vendor": "anthropic",
        "model": "claude-sonnet-5-5",
        "effort": "high",
        "slot": "Sisyphus / Aletheia implementation & test verification",
    },
    "claude-opus-falsifier": {
        "binary": "claude",
        "orca_agent": "claude",
        "omc_spec": "1:claude:security-reviewer",
        "vendor": "anthropic",
        "model": "claude-opus-5-5",
        "effort": "high",
        "slot": "Oracle / quant-falsifier HLZ/DSR/CPCV & dimensional audit",
    },
    "codex-astra-omx": {
        "binary": "codex",
        "orca_agent": "codex",
        "omc_spec": "1:codex:critic",
        "vendor": "openai",
        "model": "gpt-6.2-astra",
        "effort": "xhigh",
        "slot": "Cross-family adversarial math/code critic (omc ask codex / omx / Orca)",
    },
    "codex-sol-omx": {
        "binary": "omx",
        "orca_agent": "codex",
        "omc_spec": "1:codex:test-engineer",
        "vendor": "openai",
        "model": "gpt-6.2-sol",
        "effort": "high",
        "slot": "High-throughput OMX mission & parallel test generation",
    },
    "antigravity-carbon": {
        "binary": "gemini",
        "orca_agent": "antigravity",
        "omc_spec": "1:antigravity:analyst",
        "vendor": "google",
        "model": "gemini-4-carbon-high",
        "effort": "high",
        "slot": "1M-context 18-clone upstream shelf, SEC EDGAR & run_workflow synthesis",
    },
    "opencode-kimi-omo": {
        "binary": "opencode",
        "orca_agent": "opencode",
        "omc_spec": "1:claude:architect",
        "vendor": "moonshot",
        "model": "kimi-k3.1-pro",
        "effort": "high",
        "slot": "Non-GPT Hephaestus structured multi-file refactoring (OMO / OpenCode)",
    },
    "deepseek-dsh": {
        "binary": "dsh",
        "orca_agent": "opencode",
        "omc_spec": "1:antigravity:verifier",
        "vendor": "deepseek",
        "model": "deepseek-v4-pro",
        "effort": "high",
        "slot": "Cost-efficient pre-wall (<=2026-10-15) batch evaluation & 10-layer DSH probes",
    },
    "grok-regime": {
        "binary": "omc",
        "orca_agent": "claude",
        "omc_spec": "1:claude:analyst",
        "vendor": "xai",
        "model": "grok-4.7",
        "effort": "high",
        "slot": "Real-time macro/catalyst regime second-opinion via omc ask grok",
    },
    "muse-critic": {
        "binary": "omc",
        "orca_agent": "muse",
        "omc_spec": "1:claude:critic",
        "vendor": "meta",
        "model": "muse-spark-1.3",
        "effort": "high",
        "slot": "5th-vendor independent critic via omc ask muse & Orca muse worker",
    },
    "pi-omp-worker": {
        "binary": "omp",
        "orca_agent": "omp",
        "omc_spec": "1:claude:executor",
        "vendor": "openai",
        "model": "@worker",
        "effort": "high",
        "slot": "Pi v1.5.2 / OMP v18.22.0 (@worker -> openai-codex/gpt-6.2-sol high) thinking runtime",
    },
    "goose-autonomous": {
        "binary": "goose",
        "orca_agent": "opencode",
        "omc_spec": "1:claude:executor",
        "vendor": "aaif-open",
        "model": "goose-1.59",
        "effort": "high",
        "slot": "AAIF Goose autonomous MCP recipe & verification worker",
    },
}

TASK_CLASS_PROFILES: dict[str, dict[str, Any]] = {
    "lead_architecture_adr_and_spec": {
        "omc_team_spec": "1:claude:architect,1:codex:critic,1:antigravity:analyst",
        "orca_workers": ("codex-astra-omx", "antigravity-carbon"),
        "hephaestus_model": "claude-sonnet-5-5",
        "requires_prewall_lock": False,
        "requires_3vendor_stage3": False,
    },
    "parallel_worktree_implementation": {
        "omc_team_spec": "1:claude:executor,1:codex:test-engineer,1:antigravity:analyst,1:antigravity:verifier",
        "orca_workers": ("claude-sonnet-omc", "codex-sol-omx", "antigravity-carbon", "pi-omp-worker"),
        "hephaestus_model": "claude-sonnet-5-5",
        "requires_prewall_lock": False,
        "requires_3vendor_stage3": True,
    },
    "cross_family_adversarial_code_and_math_audit": {
        "omc_team_spec": "1:codex:critic,1:antigravity:security-reviewer,1:claude:verifier",
        "orca_workers": ("codex-astra-omx", "antigravity-carbon", "muse-critic"),
        "hephaestus_model": "claude-sonnet-5-5",
        "requires_prewall_lock": False,
        "requires_3vendor_stage3": True,
    },
    "quant_prewall_hypothesis_falsification": {
        "omc_team_spec": "1:claude:scientist,1:codex:critic,1:antigravity:analyst",
        "orca_workers": ("claude-opus-falsifier", "codex-astra-omx", "deepseek-dsh"),
        "hephaestus_model": "claude-sonnet-5-5",
        "requires_prewall_lock": True,
        "requires_3vendor_stage3": True,
    },
    "long_horizon_1m_shelf_and_filing_synthesis": {
        "omc_team_spec": "1:antigravity:analyst,1:claude:architect,1:codex:critic",
        "orca_workers": ("antigravity-carbon", "codex-astra-omx"),
        "hephaestus_model": "claude-sonnet-5-5",
        "requires_prewall_lock": False,
        "requires_3vendor_stage3": False,
    },
    "combinatorial_gpu_sweep": {
        "omc_team_spec": "1:claude:scientist,1:codex:critic,1:antigravity:verifier",
        "orca_workers": ("claude-opus-falsifier", "codex-astra-omx", "deepseek-dsh"),
        "hephaestus_model": "claude-sonnet-5-5",
        "requires_prewall_lock": True,
        "requires_3vendor_stage3": True,
    },
}

NOESIS_PROVISIONED_ORCA_REPOS: dict[str, str] = {
    "sota-harness-foundation": "3c64b92a-ec58-4e82-b85d-42bad91048b1",
    "native-agent-stack": "a1875711-afb6-41c3-9ae2-a9e6e46af082",
    "sota-multi-model-workflows": "b2a240a3-c908-447e-8f7f-1ff9942762e7",
    "sota-compounding-lab": "46980ada-367d-4ba8-a487-a44940db96fd",
    "sota-upstream-shelf-lock": "9a888eb1-f259-4bdb-9b13-11578d4d0efb",
    "agy-sota-harness": "c30acf34-379b-4b70-88ed-2672d809bfd1",
    "dsh-sota-harness": "c81404da-bd88-4a58-9dc2-185334f85933",
    "astrolabe": "85bcd7a6-6c3d-4f82-aeac-b64ff24c74bd",
    "cc-sota-harness": "e9d7444e-7ed1-4207-b67f-6267379a5688",
    "sota-mover-ranker": "492fe9dd-cc6d-454d-98dc-e228050f04f5",
    "sota-dynamic-trail-c": "204a2a75-42c0-4678-b95f-b0f78de29cc2",
    "meridian": "29f0498e-2fb5-480c-96fe-98d7f2c5b86b",
    "sota-private-vault": "cb466c3d-99ff-4825-8e60-91943f78b28a",
    "trading-sota": "e66600d7-dd6b-4e0d-8586-95eaed3312c9",
    "tsl": "1e2193b7-a724-41ce-b92e-0c1083b6113a",
    "canon": "7ad94fb5-c149-4831-915e-ca20ef628cae",
    "dsh-plugin-landscape": "d459e8bb-8226-4274-b3f1-ee1830c8ba58",
    ".github": "46bff41f-50d5-49ac-bfca-6e0559ccb868",
}

_LIVE_ALPACA_RE = re.compile(r"(?<!paper-)(?<![A-Za-z0-9-])" + "api" + r"\." + "alpaca" + r"\.markets\b")
_LIVE_BIN_RE = re.compile(r"\." + "claude/" + "bin/" + r"(?:live|alpaca-live-mcp|key-store)\b")
_LIVE_IBKR_PORT_RE = re.compile(r"(?::|\bport\s*=\s*)(?:4001|7496)\b")
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


@dataclass(frozen=True)
class CCLeadPlanRequest:
    repo: str
    goal: str
    task_class: str = "parallel_worktree_implementation"
    placement: str = "auto"  # "auto" | "local" | "noesis"
    session_id: str = "cc-lead"
    requested_paths: tuple[str, ...] = ("*",)
    hephaestus_model_override: str | None = None
    study_end_date: str | None = None
    worker_keys_override: tuple[str, ...] | None = None


def probe_cc_runtime_fleet() -> dict[str, Any]:
    """Probe installed CLI binaries powering Claude-Lead multi-runtime orchestration."""
    binaries = (
        "claude",
        "omc",
        "codex",
        "omx",
        "orca",
        "agy",
        "gemini",
        "opencode",
        "oh-my-openagent",
        "pi",
        "omp",
        "goose",
        "dsh",
        "hcom",
        "wt",
        "bd",
        "omniroute",
    )
    extra_dirs = [
        str(Path.home() / ".agents" / "bin"),
        str(Path.home() / ".local" / "bin"),
        str(Path.home() / ".local" / "share" / "mise" / "shims"),
        "/Applications/Antigravity.app/Contents/Resources/app/bin",
        "/opt/homebrew/bin",
        "/usr/local/bin",
    ]
    search_path = os.pathsep.join([*extra_dirs, os.environ.get("PATH", "")])
    installed: list[str] = []
    missing: list[str] = []
    for b in binaries:
        if shutil.which(b, path=search_path):
            installed.append(b)
        else:
            missing.append(b)
    return {
        "checked_total": len(binaries),
        "installed_count": len(installed),
        "installed_binaries": installed,
        "missing_binaries": missing,
        "cc_lead_ready": "claude" in installed and "omc" in installed,
        "codex_omx_ready": "codex" in installed and "omx" in installed,
        "orca_supervisor_ready": "orca" in installed,
    }


def resolve_local_orca_repo_id(repo_name: str, *, timeout_sec: float = 5.0) -> str | None:
    """Query `orca repo list --json` to resolve `id:<uuid>` on local Mac M5 Max or Noesis."""
    extra_path = os.pathsep.join([str(Path.home() / ".local" / "bin"), os.environ.get("PATH", "")])
    orca_bin = shutil.which("orca", path=extra_path)
    if not orca_bin:
        return None
    try:
        proc = subprocess.run(
            [orca_bin, "repo", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    repos = ((payload.get("result") or {}).get("repos")) or []
    aliases = {repo_name, "dot-github"} if repo_name == ".github" else {repo_name}
    for entry in repos:
        rid = str(entry.get("id") or "")
        dname = str(entry.get("displayName") or "")
        rpath = Path(str(entry.get("path") or "")).name
        if (dname in aliases or rpath in aliases) and _UUID_RE.match(rid):
            return rid
    return None


def validate_cc_lead_safety_and_invariants(
    req: CCLeadPlanRequest,
    *,
    hephaestus_model: str,
    worker_keys: tuple[str, ...],
    requires_prewall: bool,
    requires_3vendor: bool,
) -> None:
    """Fail-closed trading firewall, pre-wall study lock, Hephaestus non-GPT, and vendor diversity."""
    if _LIVE_ALPACA_RE.search(req.goal) or _LIVE_BIN_RE.search(req.goal) or _LIVE_IBKR_PORT_RE.search(req.goal):
        raise PermissionError("Live-capital endpoints, binaries, and ports (4001/7496) are 100% hard-refused")

    if hephaestus_model.strip().lower().startswith("gpt-"):
        raise ValueError(
            f"Hephaestus slot forbids GPT models (got {hephaestus_model!r}); use claude-sonnet-5-5 or kimi-k3.1-pro"
        )

    eff_date = req.study_end_date or (AO_STUDY_WALL_DATE.isoformat() if requires_prewall else None)
    if eff_date is not None:
        parsed = dt.date.fromisoformat(eff_date)
        if parsed > AO_STUDY_WALL_DATE:
            raise ValueError(f"PREWALL_VIOLATION: study_end_date {eff_date} > {AO_STUDY_WALL_DATE.isoformat()}")

    for wk in worker_keys:
        if wk not in RUNTIME_WORKER_ROSTER:
            raise ValueError(f"Unknown runtime worker key {wk!r}; valid={sorted(RUNTIME_WORKER_ROSTER)}")

    if requires_3vendor:
        # Include Claude Lead ('anthropic') + concrete vendors of dispatched workers
        vendors = {"anthropic"}
        for wk in worker_keys:
            v = RUNTIME_WORKER_ROSTER[wk]["vendor"]
            if v in CONCRETE_VENDORS:
                vendors.add(v)
        if len(vendors & set(CONCRETE_VENDORS)) < 3:
            raise ValueError(
                f"Stage-3+ orchestration requires >= 3 distinct canonical vendors in {sorted(CONCRETE_VENDORS)}, "
                f"got {sorted(vendors)}"
            )


def build_cc_lead_execution_plan(
    req: CCLeadPlanRequest,
    *,
    mesh_state: str = "portable_autonomous_ac",
    local_orca_repo_id: str | None = None,
    bus_db_path: Path | None = None,
    hlz_trials_n: int = 88,
    hlz_next_t_hurdle: float = 4.1709,
    feeds_schema: str = "sota-research-feeds.v2",
) -> dict[str, Any]:
    """Synthesize a Turn-0 context-injected Claude-Code-Central 5-channel execution plan."""
    profile = TASK_CLASS_PROFILES.get(req.task_class)
    if profile is None:
        raise ValueError(f"Unsupported task_class {req.task_class!r}; valid={sorted(TASK_CLASS_PROFILES)}")

    hephaestus_model = req.hephaestus_model_override or str(profile["hephaestus_model"])
    worker_keys = req.worker_keys_override or tuple(profile["orca_workers"])
    requires_prewall = bool(profile["requires_prewall_lock"])
    requires_3vendor = bool(profile["requires_3vendor_stage3"])

    validate_cc_lead_safety_and_invariants(
        req,
        hephaestus_model=hephaestus_model,
        worker_keys=worker_keys,
        requires_prewall=requires_prewall,
        requires_3vendor=requires_3vendor,
    )

    on_noesis_self = is_running_on_noesis_host()
    use_noesis = (
        on_noesis_self
        or req.placement == "noesis"
        or (
            req.placement == "auto"
            and req.task_class == "combinatorial_gpu_sweep"
            and mesh_state in ("dual_mesh_docked", "dual_mesh_on_battery")
        )
    )
    target_host = "noesis_64c_rtx4090" if use_noesis else "mac_m5_max_local"
    if use_noesis:
        orca_repo_uuid = NOESIS_PROVISIONED_ORCA_REPOS.get(req.repo)
        orca_selector = f"id:{orca_repo_uuid}" if orca_repo_uuid else f"name:{req.repo}"
    else:
        resolved_local = local_orca_repo_id or resolve_local_orca_repo_id(req.repo)
        orca_selector = f"id:{resolved_local}" if resolved_local else f"name:{req.repo}"

    if req.repo == "canon":
        repo_dir = Path.home() / "canon"
    elif req.repo == "sota-dynamic-trail-c":
        tcc_safe = Path.home() / "sota-dynamic-trail-c"
        repo_dir = tcc_safe if tcc_safe.exists() else Path.home() / "Documents" / "sota-dynamic-trail-c"
    else:
        repo_dir = Path.home() / "Documents" / ("dot-github" if req.repo == ".github" else req.repo)
    in_isolated_wt = detect_isolated_worktree(repo_dir) if repo_dir.exists() else False
    lease_disjoint = detect_disjoint_peer_lease(
        req.repo,
        session_id=req.session_id,
        db_path=bus_db_path,
        requested_paths=list(req.requested_paths),
    )

    turn0_brief = (
        f"[CC-Lead Central SOTA Brief | repo={req.repo} | feeds={feeds_schema} | "
        f"HLZ N={hlz_trials_n} t*={hlz_next_t_hurdle:.4f} | prewall<={AO_STUDY_WALL_DATE.isoformat()} | "
        f"ADR-0022<=2.00% | host={target_host}] {req.goal}"
    )
    slug = re.sub(r"[^a-z0-9]+", "-", req.repo.lower()).strip("-") or "sota"
    plan_id = f"cc-{slug}-{req.task_class[:12].replace('_', '-')}"

    env_exports = " ".join(
        f"{k}={shlex.quote(v)}" for k, v in CC_LEAD_CENTRAL_CONTRACT["omc_worker_default_env"].items()
    )
    quoted_brief = shlex.quote(turn0_brief)

    ultragoal_cmd = (
        f"omc ultragoal create-goals --plan-id {shlex.quote(plan_id)} "
        f"--brief {quoted_brief} "
        f"--goal {shlex.quote('G001::Spec & Disjoint Lease Preflight')} "
        f"--goal {shlex.quote('G002::Isolated Worktree Multi-Runtime Execution')} "
        f"--goal {shlex.quote('G003::Cross-Vendor Falsification & Merge Gate')} --json"
    )
    omc_team_cmd = f"{env_exports} omc team {shlex.quote(str(profile['omc_team_spec']))} --no-decompose {quoted_brief}"
    advisor_and_omx_cmds = {
        "claude_architect_ask": f"omc ask claude --agent-prompt architect --prompt {quoted_brief}",
        "codex_critic_ask": f"omc ask codex --agent-prompt critic --prompt {quoted_brief}",
        "gemini_verifier_ask": f"omc ask gemini --agent-prompt verifier --prompt {quoted_brief}",
        "antigravity_shelf_ask": f"omc ask antigravity --agent-prompt analyst --prompt {quoted_brief}",
        "grok_regime_ask": f"omc ask grok --agent-prompt analyst --prompt {quoted_brief}",
        "cursor_editor_ask": f"omc ask cursor --agent-prompt executor --prompt {quoted_brief}",
        "muse_fifth_vendor_ask": f"omc ask muse --agent-prompt critic --prompt {quoted_brief}",
        "omx_exec_worker": f"omx exec -c 'model=\"gpt-6.2-sol\"' {quoted_brief}",
        "omc_omx_tmux_interop": "omc interop",
    }

    orca_dispatches: list[dict[str, Any]] = []
    for idx, wk in enumerate(worker_keys, start=1):
        meta = RUNTIME_WORKER_ROSTER[wk]
        wt_name = f"cc-{slug}-{wk.split('-')[0]}-{idx}"
        argv = [
            "orca",
            "orchestration",
            "worker-start",
            *orca_remote_on_args(use_noesis=use_noesis),
            "--worktree",
            "new-child",
            "--repo",
            orca_selector,
            "--name",
            wt_name,
            "--agent",
            meta["orca_agent"],
        ]
        if meta["orca_agent"] in ("claude", "codex", "antigravity", "grok", "muse", "omp"):
            argv.extend(["--model", meta["model"], "--effort", meta["effort"]])
        argv.extend(
            [
                "--setup",
                "run",
                "--task-title",
                f"[{wk}] {req.repo}: {req.goal[:64]}",
                "--spec",
                f"{turn0_brief}\nSlot: {meta['slot']}\nConstraints: preserve frozen assertions; run ruff, ty, pytest, merge_gate.py, gitleaks; report via worker_done.",
                "--json",
            ]
        )
        orca_dispatches.append(
            {
                "worker_key": wk,
                "vendor": meta["vendor"],
                "orca_agent": meta["orca_agent"],
                "model": meta["model"],
                "worktree_name": wt_name,
                "argv": argv,
                "shell_cmd": " ".join(shlex.quote(x) for x in argv),
            }
        )

    vendors_covered = sorted({"anthropic"} | {RUNTIME_WORKER_ROSTER[w]["vendor"] for w in worker_keys})
    plan_digest_payload = {
        "repo": req.repo,
        "task_class": req.task_class,
        "goal": req.goal,
        "target_host": target_host,
        "orca_selector": orca_selector,
        "workers": list(worker_keys),
        "hephaestus_model": hephaestus_model,
        "hlz_trials_n": hlz_trials_n,
        "feeds_schema": feeds_schema,
    }
    plan_sha256 = hashlib.sha256(json.dumps(plan_digest_payload, sort_keys=True).encode("utf-8")).hexdigest()

    return {
        "schema_version": "sota-cc-lead-hub.v2",
        "plan_id": plan_id,
        "plan_sha256": plan_sha256,
        "cc_lead_contract": CC_LEAD_CENTRAL_CONTRACT,
        "repo": req.repo,
        "task_class": req.task_class,
        "target_host": target_host,
        "mesh_state": mesh_state,
        "orca_repo_selector": orca_selector,
        "hephaestus_model": hephaestus_model,
        "vendors_covered": vendors_covered,
        "canonical_vendors_count": len(set(vendors_covered) & set(CONCRETE_VENDORS)),
        "isolation_and_lease": {
            "primary_checkout_is_linked_worktree": in_isolated_wt,
            "lease_disjoint": lease_disjoint,
            "ready_to_dispatch_mutating_workers": lease_disjoint,
        },
        "channels": {
            "1_cc_lead_ultragoal_cmd": ultragoal_cmd,
            "2_omc_team_swarm_cmd": omc_team_cmd,
            "3_advisor_and_omx_cmds": advisor_and_omx_cmds,
            "4_orca_supervised_worker_dispatches": orca_dispatches,
            "5_bus_and_hcom_cmds": {
                "claim_lease": (
                    f"~/.agents/bin/sota-bus claim --repo {shlex.quote(req.repo)} "
                    f"--agent claude --session {shlex.quote(req.session_id)} "
                    f"--paths {' '.join(shlex.quote(p) for p in req.requested_paths)} "
                    f"--intent {shlex.quote(req.goal[:120])}"
                ),
                "hcom_broadcast": f"hcom send {shlex.quote(f'[CC-Lead {plan_id}] Dispatched {len(orca_dispatches)} runtime workers on {req.repo}')}",
                "coop_sync": "~/.agents/bin/sota-workstation coop sync",
            },
        },
    }


SMART_TASK_SUITABILITY_MATRIX: dict[str, dict[str, Any]] = {
    "architecture_adr_and_spec": {
        "keywords": ("adr", "madr", "architecture", "spec", "charter", "umbrella", "governance", "manifest", "plan"),
        "primary_worker": "cc-lead",
        "primary_orca_agent": "claude",
        "primary_model": "claude-fable-5-2",
        "effort": "xhigh",
        "challenger_worker": "codex",
        "challenger_model": "gpt-6.2-astra",
        "default_surface": "local",
        "claude_best_practice": "oneModelPerConversation=True + 1h/600K cache + backnotprop/plannotator visual plan gate",
    },
    "adversarial_math_security_and_bug_hunt": {
        "keywords": (
            "audit",
            "adversarial",
            "security",
            "vulnerability",
            "bughunter",
            "red-team",
            "dimensional",
            "overflow",
            "nan",
            "falsif",
            "trailofbits",
        ),
        "primary_worker": "codex",
        "primary_orca_agent": "codex",
        "primary_model": "gpt-6.2-astra",
        "effort": "xhigh",
        "challenger_worker": "claude",
        "challenger_model": "claude-opus-5-5",
        "default_surface": "auto",
        "claude_best_practice": "Cross-family OpenAI gpt-6.2-astra + Anthropic claude-opus-5-5 (Claude-BugHunter / Trail of Bits) 2-pass P0-P3 review",
    },
    "prewall_quant_sweep_and_gpu_batch": {
        "keywords": (
            "pre-wall",
            "prewall",
            "cpcv",
            "dsr",
            "hlz",
            "duckdb",
            "polars",
            "parquet",
            "h09",
            "rvol",
            "sweep",
            "gpu",
            "cuda",
            "openvino",
            "backtest",
            "nautilus",
            "hftbacktest",
            "mintrl",
        ),
        "primary_worker": "dsh",
        "primary_orca_agent": "codex",
        "primary_model": "deepseek-v4-pro",
        "effort": "high",
        "challenger_worker": "codex",
        "challenger_model": "gpt-6.2-astra",
        "default_surface": "noesis",
        "claude_best_practice": "Offload <=2026-10-15 heavy sweeps to Noesis-Carbon 56c + RTX 4090 ext4 to shield Mac RTH :8787/:8799/:4002 latency",
    },
    "long_horizon_1m_shelf_edgar_and_search_eval": {
        "keywords": (
            "upstream",
            "shelf",
            "1m",
            "edgar",
            "8-k",
            "424b",
            "filing",
            "diagram",
            "atlas",
            "c4",
            "likec4",
            "archify",
            "graphify",
            "search-eval",
            "starred",
        ),
        "primary_worker": "antigravity",
        "primary_orca_agent": "antigravity",
        "primary_model": "gemini-4-carbon-high",
        "effort": "high",
        "challenger_worker": "cc-lead",
        "challenger_model": "claude-fable-5-2",
        "default_surface": "auto",
        "claude_best_practice": "Delegate >200K-token 18-clone shelf, SEC EDGAR, parallel-search-evals & visual/C4 synthesis to 1M-context Antigravity",
    },
    "ast_graph_multifile_codemod_refactor": {
        "keywords": (
            "ast",
            "ast-grep",
            "codemod",
            "refactor",
            "rename",
            "call-chain",
            "codebase-memory",
            "hephaestus",
            "tree-sitter",
        ),
        "primary_worker": "cc-lead",
        "primary_orca_agent": "claude",
        "primary_model": "claude-sonnet-5-5",
        "effort": "high",
        "challenger_worker": "omp",
        "challenger_model": "gpt-6.2-sol",
        "default_surface": "auto",
        "claude_best_practice": "Enforce hephaestusForbidsGptModels=True via Anthropic claude-sonnet-5-5 + codebase-memory-mcp impact graph + Pi/OMP gpt-6.2-sol challenger",
    },
    "skill_quality_eval_and_trajectory_tuning": {
        "keywords": (
            "skill.md",
            "skillopt",
            "skillevaluator",
            "promptfoo",
            "gepa",
            "trajectory",
            "lesson",
            "self-evolution",
        ),
        "primary_worker": "antigravity",
        "primary_orca_agent": "antigravity",
        "primary_model": "gemini-4-carbon-high",
        "effort": "high",
        "challenger_worker": "codex",
        "challenger_model": "gpt-6.2-astra",
        "default_surface": "local",
        "claude_best_practice": "Pair NVIDIA/SkillEvaluator + Microsoft SkillOpt + transcript friction mining before promoting SKILL.md edits",
    },
    "live_cockpit_and_paper_broker_guard": {
        "keywords": (
            "8787",
            "8799",
            "4002",
            "tradingview",
            "boats",
            "23/5",
            "wave-2",
            "blotter",
            "alpaca",
            "ibkr",
            "stop",
        ),
        "primary_worker": "cc-lead",
        "primary_orca_agent": "claude",
        "primary_model": "claude-fable-5-2",
        "effort": "xhigh",
        "challenger_worker": "codex",
        "challenger_model": "gpt-6.2-astra",
        "default_surface": "local",
        "claude_best_practice": "Enforce singleActiveBrokerHostOnly=True on portable_mac_m5_max + <=2.00% initial stop + paper-only firewall",
    },
    "parallel_worktree_feature_and_pytest": {
        "keywords": (
            "implement",
            "feature",
            "fix",
            "pytest",
            "unit test",
            "cli",
            "endpoint",
            "parser",
            "pi",
            "omp",
            "gpt-6.2-sol",
        ),
        "primary_worker": "codex",
        "primary_orca_agent": "codex",
        "primary_model": "gpt-6.2-sol",
        "effort": "high",
        "challenger_worker": "claude",
        "challenger_model": "claude-sonnet-5-5",
        "default_surface": "auto",
        "claude_best_practice": "Isolate implementation in child git worktrees with Codex / Pi / OMP gpt-6.2-sol high & disjoint peer_bus path-glob leases",
    },
}


def audit_claude_1to1_model_mix(
    model_counts: dict[str, int] | None = None,
    *,
    projects_dir: Path | None = None,
    target_fable_share: float = 0.50,
    band_half_width: float = 0.08,
) -> dict[str, Any]:
    """Audit Claude Code CLI model-turn distribution against the v3.10.0 ~1:1 (50% fable-5-2 vs 50% remaining) target."""
    counts: dict[str, int] = {}
    if model_counts is not None:
        counts = {str(k): int(v) for k, v in model_counts.items() if int(v) > 0}
    else:
        pdir = projects_dir or (Path.home() / ".claude" / "projects")
        if pdir.is_dir():
            for jf in sorted(pdir.rglob("*.jsonl")):
                try:
                    for line in jf.read_text(encoding="utf-8", errors="ignore").splitlines():
                        if '"model"' not in line:
                            continue
                        obj = json.loads(line)
                        msg = obj.get("message") if isinstance(obj, dict) else None
                        m = str((msg or {}).get("model") or obj.get("model") or "").strip()
                        if m.startswith("claude-"):
                            counts[m] = counts.get(m, 0) + 1
                except (OSError, json.JSONDecodeError):
                    continue

    fable_turns = sum(v for k, v in counts.items() if "fable-5-2" in k or "fable-5-1" in k or k == "fable")
    opus_turns = sum(v for k, v in counts.items() if "opus" in k)
    sonnet_turns = sum(v for k, v in counts.items() if "sonnet" in k)
    haiku_turns = sum(v for k, v in counts.items() if "haiku" in k)
    remaining_turns = sum(v for k, v in counts.items() if k not in {"fable"} and "fable-5-" not in k)
    total_turns = fable_turns + remaining_turns

    fable_share = round(fable_turns / total_turns, 4) if total_turns > 0 else 0.50
    remaining_share = round(remaining_turns / total_turns, 4) if total_turns > 0 else 0.50
    low_bound = round(target_fable_share - band_half_width, 4)
    high_bound = round(target_fable_share + band_half_width, 4)
    in_band = low_bound <= fable_share <= high_bound

    if total_turns == 0 or in_band:
        action = "BALANCED_1TO1_HOLD"
    elif fable_share < low_bound:
        action = "PROMOTE_HIGH_AND_ELIMINATE_HAIKU_TO_REACH_50PCT_FABLE"
    else:
        action = "DELEGATE_SUBAGENTS_TO_SONNET_OPUS_TO_REACH_50PCT_REMAINING"

    return {
        "schema_version": "sota-claude-1to1-mix.v1",
        "target_fable_share": target_fable_share,
        "allowed_band": [low_bound, high_bound],
        "total_claude_turns": total_turns,
        "fable_turns": fable_turns,
        "remaining_turns": remaining_turns,
        "opus_turns": opus_turns,
        "sonnet_turns": sonnet_turns,
        "haiku_turns": haiku_turns,
        "fable_share": fable_share,
        "remaining_share": remaining_share,
        "within_1to1_band": in_band,
        "recommended_action": action,
        "enforced_omc_tiers": {
            "OMC_MODEL_HIGH": "claude-fable-5-2",
            "OMC_MODEL_MEDIUM": "claude-sonnet-5-5",
            "OMC_MODEL_LOW": "claude-sonnet-5-5",
            "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
            "CLAUDE_CODE_WORKFLOW_SUBAGENT_MODEL": "sonnet",
        },
        "raw_model_counts": counts,
    }


def rebalance_claude_1to1_route(
    route: dict[str, Any],
    *,
    fable_share: float,
    target_fable_share: float = 0.50,
    band_half_width: float = 0.08,
) -> dict[str, Any]:
    """Deterministically steer subagent/worker tier between claude-fable-5-2 and opus/sonnet toward 1:1 balance."""
    out = dict(route)
    model = str(out.get("selected_model") or "")
    cls_name = str(out.get("suitability_class") or "")
    low_bound = target_fable_share - band_half_width
    high_bound = target_fable_share + band_half_width

    # Never downgrade live broker guard or sovereign architecture lead, and never introduce haiku sprawl.
    if model.startswith("claude-haiku"):
        out["selected_model"] = "claude-sonnet-5-5"
        out["rebalance_reason"] = "eliminated_haiku_sprawl_to_sonnet_5_5"
        return out

    if (
        fable_share < low_bound
        and model in {"claude-sonnet-5-5", "claude-opus-5-5"}
        and cls_name != "ast_graph_multifile_codemod_refactor"
    ):
        out["selected_model"] = "claude-fable-5-2"
        out["effort"] = "xhigh"
        out["selected_worker"] = "cc-lead"
        out["assign_compatible_worker"] = "cc-lead"
        out["rebalance_reason"] = f"fable_share={fable_share:.4f}<{low_bound:.2f}:promoted_to_claude_fable_5_2"
    elif (
        fable_share > high_bound
        and model == "claude-fable-5-2"
        and cls_name
        not in {
            "live_cockpit_and_paper_broker_guard",
            "architecture_adr_and_spec",
        }
    ):
        out["selected_model"] = "claude-opus-5-5"
        out["effort"] = "high"
        out["selected_worker"] = "claude-opus"
        out["assign_compatible_worker"] = "claude-opus"
        out["rebalance_reason"] = f"fable_share={fable_share:.4f}>{high_bound:.2f}:delegated_to_claude_opus_5_5"
    else:
        out["rebalance_reason"] = "within_1to1_policy"
    return out


def smart_route_task(
    goal: str,
    *,
    repo: str = "cc-sota-harness",
    surface: str = "auto",
    prefer_authenticated_only: bool = True,
) -> dict[str, Any]:
    """Deterministically classify task suitability and select optimal live-authenticated model, worker, and surface."""
    for rx, label in (
        (_LIVE_ALPACA_RE, "live Alpaca endpoint"),
        (_LIVE_BIN_RE, "live broker binary"),
        (_LIVE_IBKR_PORT_RE, "live IBKR port"),
    ):
        if rx.search(goal):
            raise PermissionError(f"Hard firewall refused {label} in goal")

    g_low = f"{repo} {goal}".lower()
    best_cls = "parallel_worktree_feature_and_pytest"
    best_hits: list[str] = []
    for cls_name, spec in SMART_TASK_SUITABILITY_MATRIX.items():
        hits = [kw for kw in spec["keywords"] if kw in g_low]
        if len(hits) > len(best_hits):
            best_cls = cls_name
            best_hits = hits

    if not best_hits:
        if repo in {"meridian", "sota-compounding-lab", "tsl", "trading-sota", "dsh-sota-harness"}:
            best_cls = "prewall_quant_sweep_and_gpu_batch"
        elif repo in {"sota-mover-ranker", "sota-dynamic-trail-c", "astrolabe"}:
            best_cls = "live_cockpit_and_paper_broker_guard"
        elif repo in {".github", "native-agent-stack", "canon"}:
            best_cls = "architecture_adr_and_spec"

    chosen = SMART_TASK_SUITABILITY_MATRIX[best_cls]
    live_routes = set(CC_LEAD_CENTRAL_CONTRACT["live_authenticated_worker_routes"])
    worker = str(chosen["primary_worker"])
    if prefer_authenticated_only and worker not in live_routes:
        worker = "codex"
    assign_worker = "claude" if worker == "dsh" else worker
    resolved_surface = str(chosen["default_surface"]) if surface == "auto" else surface
    if resolved_surface == "auto":
        resolved_surface = (
            "noesis" if repo in {"meridian", "sota-compounding-lab", "tsl", "dsh-sota-harness"} else "local"
        )

    return {
        "schema_version": "sota-smart-task-router.v1",
        "repo": repo,
        "suitability_class": best_cls,
        "matched_signals": best_hits,
        "selected_worker": worker,
        "assign_compatible_worker": assign_worker,
        "orca_agent": chosen["primary_orca_agent"],
        "selected_model": chosen["primary_model"],
        "effort": chosen["effort"],
        "challenger_worker": chosen["challenger_worker"],
        "challenger_model": chosen["challenger_model"],
        "recommended_surface": resolved_surface,
        "live_authenticated_route": worker in live_routes,
        "hephaestus_non_gpt_enforced": not str(chosen["primary_model"]).startswith("gpt-")
        if best_cls == "ast_graph_multifile_codemod_refactor"
        else True,
        "one_model_per_conversation": True,
        "claude_best_practice": chosen["claude_best_practice"],
    }


def build_multi_model_assign_envelope(
    *,
    repo: str,
    goal: str,
    worker: str = "codex",
    surface: str = "auto",
    paths: tuple[str, ...] = ("*",),
    sender_session: str = "agy",
) -> dict[str, Any]:
    """Build a deterministic 1-call multi-model task assignment & auto-release envelope (M1, ADR-0020)."""
    for rx, label in (
        (_LIVE_ALPACA_RE, "live Alpaca endpoint"),
        (_LIVE_BIN_RE, "live broker binary"),
        (_LIVE_IBKR_PORT_RE, "live IBKR port"),
    ):
        if rx.search(goal):
            raise PermissionError(f"Hard firewall refused {label} in goal")
    smart_decision: dict[str, Any] | None = None
    if worker == "auto":
        smart_decision = smart_route_task(goal, repo=repo, surface=surface)
        worker = str(smart_decision["assign_compatible_worker"])
        if surface == "auto":
            surface = str(smart_decision["recommended_surface"])
    valid_workers = (
        "claude",
        "claude-opus",
        "claude-sonnet",
        "codex",
        "codex-sol",
        "omp",
        "pi",
        "dsh",
        "opencode",
        "muse",
        "grok",
        "antigravity",
        "cc-lead",
        "noesis-cc-lead",
    )
    if worker not in valid_workers:
        raise ValueError(f"Unsupported worker '{worker}'; expected one of {valid_workers}")
    if repo not in NOESIS_PROVISIONED_ORCA_REPOS:
        raise ValueError(f"Unknown repository '{repo}'")
    on_noesis_self = is_running_on_noesis_host()
    use_noesis = on_noesis_self or surface == "noesis" or worker == "noesis-cc-lead"
    orca_repo = f"id:{NOESIS_PROVISIONED_ORCA_REPOS[repo]}" if use_noesis else repo
    assign_sha256 = hashlib.sha256(
        json.dumps(
            {"repo": repo, "goal": goal, "worker": worker, "surface": surface, "paths": list(paths)},
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    bus_cmd = [
        sys.executable,
        str(Path.home() / ".agents" / "bus" / "sota_bus_engine.py"),
        "assign",
        "--repo",
        repo,
        "--worker",
        worker,
        "--placement",
        "noesis" if use_noesis else ("local" if surface == "local" else "auto"),
        "--goal",
        goal,
        "--callback-to",
        sender_session,
        "--paths",
        *paths,
    ]
    release_cmd = [
        "orca",
        "orchestration",
        "worker-release",
        *orca_remote_on_args(use_noesis=use_noesis),
        "--dispatch",
        "<dispatch_id>",
    ]
    return {
        "schema_version": "sota-multi-model-assign.v1",
        "repo": repo,
        "worker": worker,
        "surface": "noesis" if use_noesis else surface,
        "orca_repo_selector": orca_repo,
        "stdin_spec_file_mode": True,
        "memory_sources": ("sota-bus-fts5", "qmd-567-docs"),
        "assign_sha256": assign_sha256,
        "sota_bus_assign_argv": bus_cmd,
        "orca_worker_release_template": release_cmd,
        "smart_route": smart_decision or smart_route_task(goal, repo=repo, surface=surface),
    }


def _load_live_bus_and_mesh() -> tuple[int, float, str]:
    trials_n = 96
    next_t = 4.1905
    mesh = "portable_autonomous_ac"
    bus_engine = Path.home() / ".agents" / "bus" / "sota_bus_engine.py"
    ws_bin = Path.home() / ".agents" / "bin" / "sota-workstation"
    if bus_engine.is_file():
        p_bus = subprocess.run(
            [sys.executable, str(bus_engine), "status"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if p_bus.returncode == 0:
            try:
                bj = json.loads(p_bus.stdout)
                trials_n = int(bj.get("hypothesis_trials_total") or trials_n)
                next_t = float(bj.get("next_trial_hlz_t_hurdle") or next_t)
            except (ValueError, json.JSONDecodeError):
                pass
    if ws_bin.is_file():
        ws_exe_str = f"{ws_bin}.exe"
        ws_argv = (
            [ws_exe_str, "status", "--json"]
            if os.name == "nt" and os.path.isfile(ws_exe_str)
            else [sys.executable, str(ws_bin), "status", "--json"]
        )
        p_ws = subprocess.run(
            ws_argv,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if p_ws.returncode == 0:
            try:
                mesh = derive_workstation_mesh_state(json.loads(p_ws.stdout))
            except json.JSONDecodeError:
                pass
    return trials_n, next_t, mesh


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sota-cc-hub",
        description="Claude Code (cc-lead + OMC v2) Central Multi-Session & Multi-Runtime Worker Orchestrator",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_st = sub.add_parser("status", help="Probe Claude Lead + OMC/OMX/Orca/OMO/Pi/Goose/DSH runtime worker fleet")
    p_st.add_argument("--json", action="store_true", help="Emit JSON status")

    p_ln = sub.add_parser("lanes", help="Inspect Dual-Machine Trading Lanes (T1..T3) & Harness Lanes (H1..H3)")
    p_ln.add_argument("--plane", default="all", choices=("all", "trading", "harness"))
    p_ln.add_argument("--json", action="store_true", help="Emit JSON lanes overview")

    p_pl = sub.add_parser("plan", help="Synthesize 5-channel Claude-Lead multi-runtime worker execution plan")
    p_pl.add_argument("--repo", default="sota-multi-model-workflows")
    p_pl.add_argument("--task-class", default="parallel_worktree_implementation", choices=sorted(TASK_CLASS_PROFILES))
    p_pl.add_argument("--goal", required=True)
    p_pl.add_argument("--placement", default="auto", choices=("auto", "local", "noesis"))
    p_pl.add_argument("--session", default="cc-lead")
    p_pl.add_argument("--paths", nargs="*", default=["*"])

    p_dp = sub.add_parser(
        "dispatch-orca", help="Validate lease & dry-run or execute supervised Orca child-worktree workers"
    )
    p_dp.add_argument("--repo", required=True)
    p_dp.add_argument("--task-class", default="parallel_worktree_implementation", choices=sorted(TASK_CLASS_PROFILES))
    p_dp.add_argument("--goal", required=True)
    p_dp.add_argument("--workers", default="", help="Optional comma-separated worker keys from RUNTIME_WORKER_ROSTER")
    p_dp.add_argument("--placement", default="auto", choices=("auto", "local", "noesis"))
    p_dp.add_argument("--session", default="cc-lead")
    p_dp.add_argument("--paths", nargs="*", default=["*"])
    p_dp.add_argument("--execute", action="store_true", help="Launch supervised Orca workers if lease is disjoint")

    p_as = sub.add_parser("assign", help="1-call multi-model worker assignment with FTS5+qmd memory brief & lease")
    p_as.add_argument("--repo", required=True)
    p_as.add_argument(
        "--worker",
        default="auto",
        choices=(
            "auto",
            "claude",
            "claude-opus",
            "claude-sonnet",
            "codex",
            "codex-sol",
            "omp",
            "pi",
            "dsh",
            "opencode",
            "muse",
            "grok",
            "antigravity",
            "cc-lead",
            "noesis-cc-lead",
        ),
    )
    p_as.add_argument("--surface", default="auto", choices=("auto", "local", "noesis"))
    p_as.add_argument("--goal", required=True)
    p_as.add_argument("--sender", default="cc-lead")
    p_as.add_argument("--paths", nargs="*", default=["*"])
    p_as.add_argument("--execute", action="store_true")

    p_sr = sub.add_parser(
        "smart-route", help="Classify task suitability & select optimal live-authenticated model + surface"
    )
    p_sr.add_argument("--repo", default="cc-sota-harness")
    p_sr.add_argument("--goal", required=True)
    p_sr.add_argument("--surface", default="auto", choices=("auto", "local", "noesis"))

    p_mm = sub.add_parser(
        "model-mix", help="Audit Claude Code CLI ~1:1 (50%% claude-fable-5-2 vs 50%% remaining) usage & tier balance"
    )
    p_mm.add_argument("--json", action="store_true")

    p_rl = sub.add_parser("release", help="Release a completed Orca supervised worker dispatch & sota-bus lease")
    p_rl.add_argument("--dispatch", required=True)
    p_rl.add_argument("--repo", default="")
    p_rl.add_argument("--session", default="")
    p_rl.add_argument("--surface", default="local", choices=("local", "noesis"))
    p_rl.add_argument("--execute", action="store_true")

    args = parser.parse_args(argv)
    trials_n, next_t, mesh = _load_live_bus_and_mesh()

    if args.cmd == "model-mix":
        print(json.dumps(audit_claude_1to1_model_mix(), indent=2))
        return 0

    if args.cmd == "smart-route":
        print(json.dumps(smart_route_task(args.goal, repo=args.repo, surface=args.surface), indent=2))
        return 0

    if args.cmd == "assign":
        env = build_multi_model_assign_envelope(
            repo=args.repo,
            goal=args.goal,
            worker=args.worker,
            surface=args.surface,
            paths=tuple(args.paths or ["*"]),
            sender_session=args.sender,
        )
        if not args.execute:
            print(json.dumps({"executed": False, **env}, indent=2))
            return 0
        cmd = [*env["sota_bus_assign_argv"], "--execute"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        sys.stdout.write(proc.stdout or json.dumps({"executed": True, "returncode": proc.returncode}, indent=2) + "\n")
        return 0 if proc.returncode == 0 else proc.returncode

    if args.cmd == "release":
        orca_cmd = [
            "orca",
            "orchestration",
            "worker-release",
            *orca_remote_on_args(use_noesis=(args.surface == "noesis")),
            "--dispatch",
            args.dispatch,
        ]
        if not args.execute:
            print(json.dumps({"executed": False, "orca_release_argv": orca_cmd, "repo": args.repo}, indent=2))
            return 0
        p_rel = subprocess.run(orca_cmd, capture_output=True, text=True, timeout=15, check=False)
        print(json.dumps({"executed": True, "returncode": p_rel.returncode, "stdout": p_rel.stdout.strip()}, indent=2))
        return 0 if p_rel.returncode == 0 else 1

    if args.cmd == "status":
        fleet = probe_cc_runtime_fleet()
        out = {
            "ok": fleet["cc_lead_ready"] and fleet["codex_omx_ready"] and fleet["orca_supervisor_ready"],
            "schema_version": "sota-cc-lead-hub.v2",
            "cc_lead": CC_LEAD_CENTRAL_CONTRACT,
            "fleet": fleet,
            "mesh_state": mesh,
            "hlz_trials_n": trials_n,
            "hlz_next_t_hurdle": next_t,
            "worker_roster_count": len(RUNTIME_WORKER_ROSTER),
            "task_classes": sorted(TASK_CLASS_PROFILES),
        }
        print(json.dumps(out, indent=2))
        return 0 if out["ok"] else 1

    if args.cmd == "lanes":
        from sota_mmw.dual_machine_lanes import build_lanes_overview

        lanes_out = build_lanes_overview(plane=args.plane, mesh_state=mesh)
        print(json.dumps(lanes_out, indent=2, default=list))
        return 0 if lanes_out["ok"] else 1

    w_override = tuple(x.strip() for x in getattr(args, "workers", "").split(",") if x.strip()) or None
    req = CCLeadPlanRequest(
        repo=args.repo,
        goal=args.goal,
        task_class=args.task_class,
        placement=args.placement,
        session_id=args.session,
        requested_paths=tuple(args.paths or ["*"]),
        worker_keys_override=w_override,
    )
    plan = build_cc_lead_execution_plan(
        req,
        mesh_state=mesh,
        hlz_trials_n=trials_n,
        hlz_next_t_hurdle=next_t,
    )

    if args.cmd == "plan":
        print(json.dumps(plan, indent=2))
        return 0

    # dispatch-orca
    dispatches = plan["channels"]["4_orca_supervised_worker_dispatches"]
    if not args.execute:
        print(
            json.dumps(
                {
                    "executed": False,
                    "mode": "dry_run",
                    "lease_disjoint": plan["isolation_and_lease"]["lease_disjoint"],
                    "plan_sha256": plan["plan_sha256"],
                    "dispatches": dispatches,
                },
                indent=2,
            )
        )
        return 0

    if not plan["isolation_and_lease"]["lease_disjoint"]:
        print(
            json.dumps(
                {
                    "executed": False,
                    "error": f"Blocked by overlapping foreign peer lease on {args.repo}",
                    "plan_sha256": plan["plan_sha256"],
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    results: list[dict[str, Any]] = []
    for d in dispatches:
        proc = subprocess.run(d["argv"], capture_output=True, text=True, timeout=30, check=False)
        results.append(
            {
                "worker_key": d["worker_key"],
                "returncode": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
            }
        )
    ok_all = all(r["returncode"] == 0 for r in results)
    print(
        json.dumps({"executed": True, "ok": ok_all, "plan_sha256": plan["plan_sha256"], "results": results}, indent=2)
    )
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
