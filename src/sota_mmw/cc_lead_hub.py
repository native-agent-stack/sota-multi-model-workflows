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
import re
import shlex
import shutil
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

CC_LEAD_CENTRAL_CONTRACT: dict[str, Any] = {
    "workspace_name": "cc-lead",
    "lead_runtime": "claude",
    "orchestrator_plugin": "oh-my-claudecode@omc",
    "lead_model_id": "claude-fable-5-2",
    "lead_effort": "xhigh",
    "one_model_per_conversation": True,
    "hephaestus_forbids_gpt_models": True,
    "paper_only_trading_firewall": True,
    "prewall_study_cutoff": AO_STUDY_WALL_DATE.isoformat(),
    "omc_worker_default_env": {
        "OMC_RUNTIME_V2": "1",
        "OMC_TEAM_WORKTREE_MODE": "branch",
        "OMC_CODEX_DEFAULT_MODEL": "gpt-6.2-astra",
        "OMC_ANTIGRAVITY_DEFAULT_MODEL": "gemini-4-carbon-high",
        "OMC_GEMINI_DEFAULT_MODEL": "gemini-4-carbon-high",
        "OMC_GROK_DEFAULT_MODEL": "grok-4.7",
        "OMC_JEV_MAX_EFFORT": "xhigh",
    },
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
        "omc_spec": "1:gemini:verifier",
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
        "omc_team_spec": "1:claude:executor,1:codex:test-engineer,1:antigravity:analyst,1:gemini:verifier",
        "orca_workers": ("claude-sonnet-omc", "codex-sol-omx", "opencode-kimi-omo"),
        "hephaestus_model": "kimi-k3.1-pro",
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
        "omc_team_spec": "1:claude:scientist,1:codex:critic,1:gemini:verifier",
        "orca_workers": ("claude-opus-falsifier", "codex-astra-omx", "deepseek-dsh"),
        "hephaestus_model": "kimi-k3.1-pro",
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
        "gemini",
        "opencode",
        "oh-my-openagent",
        "pi",
        "omp",
        "goose",
        "dsh",
        "hcom",
        "wt",
        "omniroute",
    )
    extra_dirs = [
        str(Path.home() / ".local" / "bin"),
        str(Path.home() / ".local" / "share" / "mise" / "shims"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
    ]
    search_path = ":".join(extra_dirs + [shutil.os.environ.get("PATH", "")])
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
    """Query `orca repo list --json` to resolve `id:<uuid>` on local Mac M5 Max."""
    extra_path = f"{Path.home() / '.local' / 'bin'}:{shutil.os.environ.get('PATH', '')}"
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
    if (
        _LIVE_ALPACA_RE.search(req.goal)
        or _LIVE_BIN_RE.search(req.goal)
        or _LIVE_IBKR_PORT_RE.search(req.goal)
    ):
        raise PermissionError("Live-capital endpoints, binaries, and ports (4001/7496) are 100% hard-refused")

    if hephaestus_model.strip().lower().startswith("gpt-"):
        raise ValueError(
            f"Hephaestus slot forbids GPT models (got {hephaestus_model!r}); use claude-sonnet-5-5 or kimi-k3.1-pro"
        )

    eff_date = req.study_end_date or (AO_STUDY_WALL_DATE.isoformat() if requires_prewall else None)
    if eff_date is not None:
        parsed = dt.date.fromisoformat(eff_date)
        if parsed > AO_STUDY_WALL_DATE:
            raise ValueError(
                f"PREWALL_VIOLATION: study_end_date {eff_date} > {AO_STUDY_WALL_DATE.isoformat()}"
            )

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

    use_noesis = req.placement == "noesis" or (
        req.placement == "auto"
        and req.task_class == "combinatorial_gpu_sweep"
        and mesh_state in ("dual_mesh_docked", "dual_mesh_on_battery")
    )
    target_host = "noesis_64c_rtx4090" if use_noesis else "mac_m5_max_local"
    if use_noesis:
        orca_repo_uuid = NOESIS_PROVISIONED_ORCA_REPOS.get(req.repo)
        orca_selector = f"id:{orca_repo_uuid}" if orca_repo_uuid else f"name:{req.repo}"
    else:
        resolved_local = local_orca_repo_id or resolve_local_orca_repo_id(req.repo)
        orca_selector = f"id:{resolved_local}" if resolved_local else f"name:{req.repo}"

    repo_dir = (
        Path.home() / "canon"
        if req.repo == "canon"
        else Path.home() / "Documents" / ("dot-github" if req.repo == ".github" else req.repo)
    )
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
    omc_team_cmd = (
        f"{env_exports} omc team {shlex.quote(str(profile['omc_team_spec']))} "
        f"--no-decompose {quoted_brief}"
    )
    advisor_and_omx_cmds = {
        "codex_critic_ask": f"omc ask codex --agent-prompt critic --prompt {quoted_brief}",
        "antigravity_shelf_ask": f"omc ask antigravity --agent-prompt analyst --prompt {quoted_brief}",
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
            "--environment",
            "100.110.115.22" if use_noesis else "local",
            "--worktree",
            "new-child",
            "--repo",
            orca_selector,
            "--name",
            wt_name,
            "--agent",
            meta["orca_agent"],
        ]
        if meta["orca_agent"] in ("claude", "codex", "antigravity", "muse"):
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
    plan_sha256 = hashlib.sha256(
        json.dumps(plan_digest_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return {
        "schema_version": "sota-cc-lead-hub.v1",
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


def _load_live_bus_and_mesh() -> tuple[int, float, str]:
    trials_n = 88
    next_t = 4.1709
    mesh = "portable_autonomous_ac"
    bus_bin = Path.home() / ".agents" / "bin" / "sota-bus"
    ws_bin = Path.home() / ".agents" / "bin" / "sota-workstation"
    if bus_bin.is_file():
        p_bus = subprocess.run(
            [sys.executable, str(Path.home() / ".agents" / "bus" / "sota_bus_engine.py"), "status"],
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
        p_ws = subprocess.run(
            [sys.executable, str(ws_bin), "status", "--json"],
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

    p_pl = sub.add_parser("plan", help="Synthesize 5-channel Claude-Lead multi-runtime worker execution plan")
    p_pl.add_argument("--repo", default="sota-multi-model-workflows")
    p_pl.add_argument("--task-class", default="parallel_worktree_implementation", choices=sorted(TASK_CLASS_PROFILES))
    p_pl.add_argument("--goal", required=True)
    p_pl.add_argument("--placement", default="auto", choices=("auto", "local", "noesis"))
    p_pl.add_argument("--session", default="cc-lead")
    p_pl.add_argument("--paths", nargs="*", default=["*"])

    p_dp = sub.add_parser("dispatch-orca", help="Validate lease & dry-run or execute supervised Orca child-worktree workers")
    p_dp.add_argument("--repo", required=True)
    p_dp.add_argument("--task-class", default="parallel_worktree_implementation", choices=sorted(TASK_CLASS_PROFILES))
    p_dp.add_argument("--goal", required=True)
    p_dp.add_argument("--workers", default="", help="Optional comma-separated worker keys from RUNTIME_WORKER_ROSTER")
    p_dp.add_argument("--placement", default="auto", choices=("auto", "local", "noesis"))
    p_dp.add_argument("--session", default="cc-lead")
    p_dp.add_argument("--paths", nargs="*", default=["*"])
    p_dp.add_argument("--execute", action="store_true", help="Launch supervised Orca workers if lease is disjoint")

    args = parser.parse_args(argv)
    trials_n, next_t, mesh = _load_live_bus_and_mesh()

    if args.cmd == "status":
        fleet = probe_cc_runtime_fleet()
        out = {
            "ok": fleet["cc_lead_ready"] and fleet["codex_omx_ready"] and fleet["orca_supervisor_ready"],
            "schema_version": "sota-cc-lead-hub.v1",
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
    print(json.dumps({"executed": True, "ok": ok_all, "plan_sha256": plan["plan_sha256"], "results": results}, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
