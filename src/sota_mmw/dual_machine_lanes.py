"""Dual-Machine (`Mac M5 Max <-> Noesis 64c/128GB/RTX4090 + Noesis-Carbon WSL2`) Orca Trading & Harness Lanes (`ADR-0014`).

Converges all 8 multi-model orchestration frameworks, 3 execution surfaces across 2 paired workstations,
3 Trading Lanes (`T1..T3` covering all 8 quantitative/broker repositories), and 3 Harness Lanes (`H1..H3`
covering all 10 harness/governance repositories) under the `ADR-0020` single-broker-host firewall and
`sota-research-feeds.v2` (`ADR-0004`) provenance contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from typing import Any

from sota_mmw.ao_lifecycle import CONCRETE_VENDORS
from sota_mmw.cc_lead_hub import (
    NOESIS_PROVISIONED_ORCA_REPOS,
    RUNTIME_WORKER_ROSTER,
    _load_live_bus_and_mesh,
    probe_cc_runtime_fleet,
    resolve_local_orca_repo_id,
)
from sota_mmw.research_convergence_contract import (
    MAX_HARD_STOP_PCT,
    PRE_WALL_MAX_DATE,
    RESEARCH_FEEDS_SCHEMA_VERSION,
    SIBLING_REPO_AUTHORITY,
)

LANES_SCHEMA_VERSION = "sota-dual-machine-lanes.v1"

ORCA_LANE_HUBS: dict[str, dict[str, dict[str, str]]] = {
    "portable_mac_m5_max": {
        "trading": {
            "hub_name": "trading-lanes",
            "path": "~/.agents/orca-lanes/trading-lanes",
            "folder_id": "4cf80c7f-96aa-42f1-a25c-a55e7d5e3f3a",
            "parent_selector": "folder:4cf80c7f-96aa-42f1-a25c-a55e7d5e3f3a",
        },
        "harness": {
            "hub_name": "harness-lanes",
            "path": "~/.agents/orca-lanes/harness-lanes",
            "folder_id": "729df6dc-26e0-49e9-bad1-d4d57021c515",
            "parent_selector": "folder:729df6dc-26e0-49e9-bad1-d4d57021c515",
        },
    },
    "stationary_noesis": {
        "trading": {
            "hub_name": "trading-lanes",
            "path": "C:/sota-workstation/.orca-lanes/trading-lanes",
            "folder_id": "c4f93f9e-a710-4599-ac95-892082b03ec8",
            "parent_selector": "folder:c4f93f9e-a710-4599-ac95-892082b03ec8",
        },
        "harness": {
            "hub_name": "harness-lanes",
            "path": "C:/sota-workstation/.orca-lanes/harness-lanes",
            "folder_id": "060eb055-834e-4ef2-8198-e3e224a35fbe",
            "parent_selector": "folder:060eb055-834e-4ef2-8198-e3e224a35fbe",
        },
    },
}

ORCHESTRATION_FRAMEWORKS_MATRIX: dict[str, dict[str, Any]] = {
    "orca_cross_machine_supervisor": {
        "upstream": "stablyai/orca",
        "versions": {"mac_m5_max": "1.4.255", "noesis_win32_wsl2": "1.4.261"},
        "mesh_transport": "symmetric Tailscale :6770 (100.93.211.101 <-> 100.110.115.22)",
        "capabilities": (
            "worker-start --on 100.110.115.22 --worktree new-child --setup run",
            "worktree.lineage.crossMachine",
            "terminal.paired-parking.v1",
            "--kind folder lane hubs",
            "event-driven wakeup (zero polling)",
        ),
        "role": "Cross-machine supervised child-worktree DAG supervisor & parked-terminal continuity",
    },
    "cc_lead_omc_v2": {
        "upstream": "anthropics/claude-code + Yeachan-Heo/oh-my-claudecode",
        "versions": {"claude": "2.1.327", "oh_my_claudecode": "5.8.4"},
        "lead_model": "claude-fable-5-2 (xhigh, 600K cache, oneModelPerConversation=True, OMC_RUNTIME_V2=1)",
        "capabilities": ("omc ultragoal", "omc team", "omc interop", "omc ask"),
        "role": "Sovereign central architectural & multi-session goal orchestrator",
    },
    "codex_omx_missions": {
        "upstream": "openai/codex + Yeachan-Heo/oh-my-codex + max-sixty/worktrunk",
        "versions": {"codex": "0.169.0", "oh_my_codex": "0.22.10", "wt": "0.81.0"},
        "models": ("gpt-6.2-astra", "gpt-6.2-sol"),
        "capabilities": ("omx exec", "omx mission", "wt worktrunk isolated git branches"),
        "role": "Cross-family adversarial math/code critic & high-throughput parallel test sweeps",
    },
    "agy_typed_workflows_and_swarm": {
        "upstream": "google-antigravity/antigravity-sdk-python",
        "versions": {"agy": "1.5.10"},
        "lead_model": "gemini-4-carbon-high (1M context)",
        "capabilities": (
            "15 schema-typed run_workflow Python DAGs",
            "Native Swarm workspace:share 1:3 verifiers",
            "18-clone upstream shelf & SEC EDGAR synthesis",
        ),
        "role": "Schema-typed Python workflow orchestration & 1M-context primary-source synthesis",
    },
    "opencode_omo_hephaestus": {
        "upstream": "sst/opencode + code-yeongyu/oh-my-openagent",
        "versions": {"opencode": "2.3.0", "oh_my_openagent": "5.1.75"},
        "models": ("kimi-k3.1-pro", "claude-sonnet-5-5"),
        "capabilities": ("non-GPT Hephaestus structured multi-file graph runtime", "polyglot AST refactoring"),
        "role": "Non-GPT structured multi-file graph transformation runtime",
    },
    "pi_omp_role_thinking": {
        "upstream": "badlogic/pi-mono + can1357/oh-my-pi",
        "versions": {"pi": "1.5.2", "omp": "18.22.0"},
        "models": ("@worker", "provider/model:level"),
        "capabilities": ("OMP @worker role selector", "explicit thinking-effort (--effort) role workers in Orca & CLI"),
        "role": "Explicit thinking-effort role-selected worker runtime",
    },
    "goose_and_dsh_open_harnesses": {
        "upstream": "block/goose + native-agent-stack/dsh-sota-harness",
        "versions": {"goose": "1.59.2", "dsh": "0.2.2-rc.2"},
        "models": ("goose-1.59", "deepseek-v4-pro"),
        "capabilities": (
            "AAIF MCP autonomous recipes",
            "10-layer offline DSH probes",
            "pre-wall <=2026-10-15 batch factor evaluation",
        ),
        "role": "Open-weights pre-wall batch evaluator & AAIF autonomous MCP worker",
    },
    "peer_bus_hcom_beads_omniroute_spine": {
        "upstream": "aannoo/hcom + steveyegge/beads + native-agent-stack/sota-multi-model-workflows",
        "versions": {"sota_bus": "SQLite-WAL", "hcom": "0.7.31", "bd": "1.3.4", "omniroute": "3.8.53"},
        "capabilities": (
            "SQLite WAL BEGIN IMMEDIATE path-glob leases",
            "hcom cross-PTY push notifications",
            "sota-workstation coop @@B64: E2EE bridge",
            "Beads bd DAG issue tracker",
            "OmniRoute provider resilience router",
        ),
        "role": "Transactional cross-session lease firewall, push messaging & resilience spine",
    },
}

DUAL_MACHINE_SURFACES: dict[str, dict[str, Any]] = {
    "portable_mac_m5_max": {
        "workstation": "Apple M5 Max (18 cores, 64 GB unified memory)",
        "platform": "darwin-arm64",
        "tailscale_ip": "100.93.211.101",
        "orca_port": 6770,
        "sovereign_paper_broker_host": True,
        "paper_lanes": ("127.0.0.1:8787", "127.0.0.1:8799", "127.0.0.1:4002"),
        "workspace_roots": ("~/Documents/*", "~/sota-dynamic-trail-c", "~/canon"),
        "role": "Sovereign single-broker paper host (:8787/:8799/:4002), interactive CC-Lead/AGY cockpit & roaming failover",
    },
    "stationary_noesis_win32": {
        "workstation": "AMD Threadripper (64 logical cores, 128 GB RAM) + NVIDIA GeForce RTX 4090 (24,564 MiB)",
        "platform": "win32",
        "tailscale_ip": "100.110.115.22",
        "orca_port": 6770,
        "sovereign_paper_broker_host": False,
        "workspace_roots": ("C:/sota-workstation/* (18 repos)", "Z:/sota-data/prewall-lake (2.85 TB NVMe)"),
        "role": "56-thread / RTX 4090 pre-wall CPCV/DSR sweeps, parked-terminal workers & Win32 CI parity",
    },
    "stationary_noesis_carbon_wsl2": {
        "workstation": "Noesis-Carbon (Linux 6.18.58.1-microsoft-standard-WSL2, native ext4)",
        "platform": "linux-wsl2-ext4",
        "tailscale_ip": "100.110.115.22",
        "orca_port": 6770,
        "sovereign_paper_broker_host": False,
        "workspace_roots": ("~/sota-workstation/* (18 repos)", "/mnt/z/sota-data/prewall-lake (symlinked)"),
        "role": "NautilusTrader v2.0.0rc9 & hftbacktest RiskAdverseQueueModel POSIX simulation (-n 8) + Linux CI parity",
    },
}

TRADING_LANES: dict[str, dict[str, Any]] = {
    "T1_live_24x5_alpaca_paper_and_guardian": {
        "lane_id": "T1_live_24x5_alpaca_paper_and_guardian",
        "plane": "trading",
        "repos": ("sota-mover-ranker", "sota-dynamic-trail-c"),
        "primary_surface": "portable_mac_m5_max",
        "failover_surface": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "allows_noesis_broker_socket": False,
        "default_worker_trio": ("claude-opus-falsifier", "codex-astra-omx", "antigravity-carbon"),
        "invariants": (
            "Strictly portable_mac_m5_max (:8787/:8799); PA... <=200 req/min; "
            "ADR-0022 <=2.00% hard stop; sota-research-feeds.v2"
        ),
    },
    "T2_ibkr_paper_4002_and_event_sim_parity": {
        "lane_id": "T2_ibkr_paper_4002_and_event_sim_parity",
        "plane": "trading",
        "repos": ("astrolabe", "meridian"),
        "primary_surface": "stationary_noesis_carbon_wsl2",
        "broker_surface": "portable_mac_m5_max",
        "failover_surface": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "allows_noesis_broker_socket": False,
        "default_worker_trio": ("claude-opus-falsifier", "codex-astra-omx", "deepseek-dsh"),
        "invariants": (
            "IBKR :4002 DU... paper gateway strictly portable_mac_m5_max (4001/7496 hard-refused); "
            "NautilusTrader / RiskAdverseQueueModel -n 8 simulation on stationary_noesis_carbon_wsl2"
        ),
    },
    "T3_prewall_cpcv_gpu_and_strategy_factory": {
        "lane_id": "T3_prewall_cpcv_gpu_and_strategy_factory",
        "plane": "trading",
        "repos": ("sota-compounding-lab", "trading-sota", "tsl", "sota-private-vault"),
        "primary_surface": "stationary_noesis_win32",
        "companion_surface": "stationary_noesis_carbon_wsl2",
        "failover_surface": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "allows_noesis_broker_socket": False,
        "default_worker_trio": ("claude-opus-falsifier", "codex-astra-omx", "deepseek-dsh"),
        "invariants": (
            "Pre-wall <=2026-10-15 CPCV/DSR/RTX 4090 sweeps on Z:/sota-data/prewall-lake "
            "(stationary_noesis_win32 / stationary_noesis_carbon_wsl2, roaming failover portable_mac_m5_max)"
        ),
    },
}

HARNESS_LANES: dict[str, dict[str, Any]] = {
    "H1_sovereign_cc_lead_and_multi_runtime_hub": {
        "lane_id": "H1_sovereign_cc_lead_and_multi_runtime_hub",
        "plane": "harness",
        "repos": ("cc-sota-harness", "sota-harness-foundation", "sota-multi-model-workflows"),
        "primary_surface": "portable_mac_m5_max",
        "paired_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "default_worker_trio": ("claude-sonnet-omc", "codex-astra-omx", "antigravity-carbon"),
        "invariants": "Sovereign CC-Lead (OMC v2) + 15-workflow AGY/Orca hub + cross-OS Win32/WSL2/macOS CI parity",
    },
    "H2_cross_vendor_verifiers_and_shelf_lock": {
        "lane_id": "H2_cross_vendor_verifiers_and_shelf_lock",
        "plane": "harness",
        "repos": ("agy-sota-harness", "dsh-sota-harness", "dsh-plugin-landscape", "sota-upstream-shelf-lock"),
        "primary_surface": "portable_mac_m5_max",
        "paired_surface": "stationary_noesis_carbon_wsl2",
        "failover_surface": "portable_mac_m5_max",
        "default_worker_trio": ("antigravity-carbon", "codex-astra-omx", "deepseek-dsh"),
        "invariants": "18-repo 40-hex upstream SHA lock, 13/13 AGY probes, 10/10 DSH probes & MinTRL/QueueModel gates",
    },
    "H3_org_control_plane_and_provenance": {
        "lane_id": "H3_org_control_plane_and_provenance",
        "plane": "harness",
        "repos": ("native-agent-stack", ".github", "canon"),
        "primary_surface": "portable_mac_m5_max",
        "paired_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "default_worker_trio": ("claude-sonnet-omc", "codex-astra-omx", "antigravity-carbon"),
        "invariants": "Umbrella v3.x lock, reusable SHA-pinned Org CI, 4-invariant sota-org-doctor & Canon provenance",
    },
}


def _build_repo_lane_index() -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    for lane_map in (TRADING_LANES, HARNESS_LANES):
        for lane_id, lane in lane_map.items():
            for repo in lane["repos"]:
                if repo in idx:
                    raise RuntimeError(f"Duplicate repo {repo!r} across lanes {idx[repo]['lane_id']} and {lane_id}")
                idx[repo] = lane
    return idx


REPO_LANE_INDEX: dict[str, dict[str, Any]] = _build_repo_lane_index()


def resolve_dual_machine_lane_plan(
    repo: str,
    *,
    workload: str = "default",
    mesh_state: str = "dual_mesh_docked",
    requested_placement: str = "auto",
    local_orca_repo_id: str | None = None,
) -> dict[str, Any]:
    """Deterministically resolve surface, Orca `worker-start` command, and >=3-vendor worker trio for `repo`."""
    lane = REPO_LANE_INDEX.get(repo)
    if lane is None:
        raise ValueError(f"Unknown ecosystem repository {repo!r}; valid={sorted(REPO_LANE_INDEX)}")
    if requested_placement not in ("auto", "local", "noesis"):
        raise ValueError(f"Invalid requested_placement {requested_placement!r}; expected auto|local|noesis")

    lane_id = str(lane["lane_id"])
    plane = str(lane["plane"])

    # Hard Single-Broker-Host Firewall (ADR-0020): active paper broker sockets never run on Noesis
    is_broker_bound = workload == "active_paper_broker" or (
        lane_id == "T1_live_24x5_alpaca_paper_and_guardian" and workload == "default"
    )
    if requested_placement == "noesis" and (workload == "active_paper_broker" or is_broker_bound):
        raise PermissionError(
            f"SINGLE_BROKER_HOST_FIREWALL: active paper broker workload on {repo!r} ({lane_id}) "
            "is strictly pinned to portable_mac_m5_max (singleActiveBrokerHostOnly=True)"
        )

    mesh_online = mesh_state in ("dual_mesh_docked", "dual_mesh_on_battery")

    if (
        is_broker_bound
        or (repo == "astrolabe" and workload in ("default", "active_paper_broker"))
        or requested_placement == "local"
        or not mesh_online
    ):
        selected_surface = "portable_mac_m5_max"
        use_noesis = False
    elif requested_placement == "noesis":
        use_noesis = True
        if lane_id in ("T2_ibkr_paper_4002_and_event_sim_parity", "H2_cross_vendor_verifiers_and_shelf_lock") or (
            workload in ("event_sim_parity", "wsl2_posix_gate")
        ):
            selected_surface = "stationary_noesis_carbon_wsl2"
        else:
            selected_surface = "stationary_noesis_win32"
    else:
        # requested_placement == "auto" and mesh_online
        if lane_id == "T2_ibkr_paper_4002_and_event_sim_parity" and (
            repo == "meridian" or workload == "event_sim_parity"
        ):
            selected_surface = "stationary_noesis_carbon_wsl2"
            use_noesis = True
        elif lane_id == "T3_prewall_cpcv_gpu_and_strategy_factory" or workload in (
            "combinatorial_gpu_sweep",
            "prewall_cpcv_sweep",
        ):
            selected_surface = (
                "stationary_noesis_carbon_wsl2" if workload == "wsl2_posix_gate" else "stationary_noesis_win32"
            )
            use_noesis = True
        elif mesh_state == "dual_mesh_on_battery" and workload in ("heavy_test_sweep", "cross_os_ci_parity"):
            selected_surface = str(lane.get("paired_surface") or "stationary_noesis_win32")
            use_noesis = True
        else:
            selected_surface = "portable_mac_m5_max"
            use_noesis = False

    if use_noesis:
        remote_uuid = NOESIS_PROVISIONED_ORCA_REPOS[repo]
        orca_repo_selector = f"id:{remote_uuid}"
        lane_hub = ORCA_LANE_HUBS["stationary_noesis"][plane]
    else:
        resolved_local = local_orca_repo_id or resolve_local_orca_repo_id(repo)
        orca_repo_selector = f"id:{resolved_local}" if resolved_local else f"name:{repo}"
        lane_hub = ORCA_LANE_HUBS["portable_mac_m5_max"][plane]

    worker_trio: tuple[str, ...] = tuple(lane["default_worker_trio"])
    lead_wk = worker_trio[0]
    lead_meta = RUNTIME_WORKER_ROSTER[lead_wk]
    slug = repo.replace(".", "dot").replace("_", "-").lower()
    wt_name = f"lane-{slug}-{workload[:12].replace('_', '-')}"

    orca_folder_worktree_argv = [
        "orca",
        "worktree",
        "create",
        *(["--environment", "100.110.115.22"] if use_noesis else []),
        "--repo",
        orca_repo_selector,
        "--name",
        wt_name,
        "--parent-worktree",
        lane_hub["parent_selector"],
        "--agent",
        lead_meta["orca_agent"],
        "--json",
    ]

    orca_argv = [
        "orca",
        "orchestration",
        "worker-start",
        *(["--on", "100.110.115.22"] if use_noesis else []),
        "--worktree",
        "new-child",
        "--repo",
        orca_repo_selector,
        "--name",
        wt_name,
        "--agent",
        lead_meta["orca_agent"],
    ]
    if lead_meta["orca_agent"] in ("claude", "codex", "antigravity", "grok", "muse", "omp"):
        orca_argv.extend(["--model", lead_meta["model"], "--effort", lead_meta["effort"]])
    orca_argv.extend(
        [
            "--setup",
            "run",
            "--task-title",
            f"[{lane_id[:2]}:{repo}] {workload}",
            "--spec",
            (
                f"Execute {workload} on {repo} ({lane_id}, surface={selected_surface}). "
                f"Enforce {RESEARCH_FEEDS_SCHEMA_VERSION}, ADR-0004 ({SIBLING_REPO_AUTHORITY}), "
                f"pre-wall <={PRE_WALL_MAX_DATE}, and ADR-0022 <={MAX_HARD_STOP_PCT:.2f}% stop."
            ),
            "--json",
        ]
    )

    trio_vendors = sorted(
        {"anthropic"}
        | {
            RUNTIME_WORKER_ROSTER[w]["vendor"]
            for w in worker_trio
            if RUNTIME_WORKER_ROSTER[w]["vendor"] in CONCRETE_VENDORS
        }
    )
    receipt_sha256 = hashlib.sha256(
        json.dumps(
            {
                "repo": repo,
                "lane_id": lane_id,
                "workload": workload,
                "selected_surface": selected_surface,
                "orca_repo_selector": orca_repo_selector,
                "worker_trio": list(worker_trio),
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    return {
        "allowed": True,
        "reason": "OK",
        "schema_version": LANES_SCHEMA_VERSION,
        "repo": repo,
        "plane": plane,
        "lane_id": lane_id,
        "workload": workload,
        "mesh_state": mesh_state,
        "requested_placement": requested_placement,
        "selected_surface": selected_surface,
        "use_noesis": use_noesis,
        "single_active_broker_host_only": True,
        "orca_repo_selector": orca_repo_selector,
        "orca_lane_hub": lane_hub,
        "orca_parent_worktree_selector": lane_hub["parent_selector"],
        "orca_folder_worktree_cmd": " ".join(shlex.quote(x) for x in orca_folder_worktree_argv),
        "orca_worker_start_argv": orca_argv,
        "orca_worker_start_cmd": " ".join(shlex.quote(x) for x in orca_argv),
        "recommended_worker_trio": list(worker_trio),
        "concrete_vendors_covered": trio_vendors,
        "concrete_vendor_count": len(trio_vendors),
        "provenance_gate": {
            "feeds_schema": RESEARCH_FEEDS_SCHEMA_VERSION,
            "provenance_adr": "ADR-0004",
            "sibling_repo_authority": SIBLING_REPO_AUTHORITY,
            "prewall_max_date": PRE_WALL_MAX_DATE,
            "max_hard_stop_pct": MAX_HARD_STOP_PCT,
        },
        "lane_plan_sha256": receipt_sha256,
    }


def build_lanes_overview(*, plane: str = "all", mesh_state: str = "dual_mesh_docked") -> dict[str, Any]:
    """Summarize Dual-Machine surfaces, 8 frameworks, and T1..T3 / H1..H3 lane assignments."""
    fleet = probe_cc_runtime_fleet()
    trading_repos = [r for ln in TRADING_LANES.values() for r in ln["repos"]]
    harness_repos = [r for ln in HARNESS_LANES.values() for r in ln["repos"]]
    lanes_out: dict[str, Any] = {}
    if plane in ("all", "trading"):
        lanes_out["trading_lanes"] = TRADING_LANES
    if plane in ("all", "harness"):
        lanes_out["harness_lanes"] = HARNESS_LANES
    return {
        "ok": len(trading_repos) == 8 and len(harness_repos) == 10 and len(REPO_LANE_INDEX) == 18,
        "schema_version": LANES_SCHEMA_VERSION,
        "mesh_state": mesh_state,
        "surfaces": DUAL_MACHINE_SURFACES,
        "orca_lane_hubs": ORCA_LANE_HUBS,
        "frameworks_count": len(ORCHESTRATION_FRAMEWORKS_MATRIX),
        "trading_repos_count": len(trading_repos),
        "harness_repos_count": len(harness_repos),
        "total_provisioned_repos": len(REPO_LANE_INDEX),
        "runtime_fleet": fleet,
        **lanes_out,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sota-lanes",
        description="Dual-Machine (Mac M5 Max <-> Noesis Win32 + Noesis-Carbon WSL2) Orca Trading & Harness Lanes CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_st = sub.add_parser("status", help="Show Dual-Machine Trading (T1..T3) & Harness (H1..H3) lane status")
    p_st.add_argument("--plane", default="all", choices=("all", "trading", "harness"))
    p_st.add_argument("--json", action="store_true")

    p_mx = sub.add_parser("matrix", help="Emit the 8-framework SOTA multi-model orchestration matrix")
    p_mx.add_argument("--json", action="store_true")

    p_rt = sub.add_parser("route", help="Resolve Dual-Machine surface & Orca worker-start command for a repository")
    p_rt.add_argument("--repo", required=True, choices=sorted(REPO_LANE_INDEX))
    p_rt.add_argument("--workload", default="default")
    p_rt.add_argument("--placement", default="auto", choices=("auto", "local", "noesis"))
    p_rt.add_argument("--mesh-state", default="")

    args = parser.parse_args(argv)
    _trials_n, _next_t, live_mesh = _load_live_bus_and_mesh()

    if args.cmd == "status":
        out = build_lanes_overview(plane=args.plane, mesh_state=live_mesh)
        print(json.dumps(out, indent=2, default=list))
        return 0 if out["ok"] else 1

    if args.cmd == "matrix":
        out_mx = {
            "schema_version": LANES_SCHEMA_VERSION,
            "frameworks_count": len(ORCHESTRATION_FRAMEWORKS_MATRIX),
            "frameworks": ORCHESTRATION_FRAMEWORKS_MATRIX,
            "surfaces": DUAL_MACHINE_SURFACES,
        }
        print(json.dumps(out_mx, indent=2, default=list))
        return 0

    eff_mesh = args.mesh_state.strip() if getattr(args, "mesh_state", "") else live_mesh
    try:
        plan = resolve_dual_machine_lane_plan(
            args.repo,
            workload=args.workload,
            mesh_state=eff_mesh,
            requested_placement=args.placement,
        )
    except PermissionError as exc:
        print(
            json.dumps(
                {
                    "allowed": False,
                    "reason": "SINGLE_BROKER_HOST_FIREWALL",
                    "repo": args.repo,
                    "workload": args.workload,
                    "requested_placement": args.placement,
                    "error": str(exc),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
