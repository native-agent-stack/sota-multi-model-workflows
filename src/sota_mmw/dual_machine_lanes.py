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
import pathlib
import shlex
import sys
from typing import Any

from sota_mmw.ao_lifecycle import CONCRETE_VENDORS
from sota_mmw.cc_lead_hub import (
    NOESIS_PROVISIONED_ORCA_REPOS,
    RUNTIME_WORKER_ROSTER,
    _load_live_bus_and_mesh,
    is_running_on_noesis_host,
    orca_remote_on_args,
    probe_cc_runtime_fleet,
    resolve_local_orca_repo_id,
)
from sota_mmw.compounding_versioning import (
    CANONICAL_RANKING_DATAFEEDS_V38,
    DEFAULT_PREWALL_LAKE_SHA256,
    RANKING_DATAFEEDS_SCHEMA_VERSION,
)
from sota_mmw.research_convergence_contract import (
    MAX_HARD_STOP_PCT,
    PRE_WALL_MAX_DATE,
    RESEARCH_FEEDS_SCHEMA_VERSION,
    SIBLING_REPO_AUTHORITY,
)

LANES_SCHEMA_VERSION = "sota-dual-machine-lanes.v2"
ORCA_LANE_HUB_SCHEMA_VERSION = "sota-orca-lane-hub.v2"
CANONICAL_SEVEN_MODEL_VENDORS: tuple[str, ...] = (
    "Anthropic",
    "OpenAI",
    "Google DeepMind",
    "DeepSeek",
    "xAI",
    "Meta",
)

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
            "16 schema-typed run_workflow Python DAGs (v3.9.0)",
            "Native Swarm workspace:share 1:3 verifiers",
            "18-clone upstream shelf & SEC EDGAR synthesis",
        ),
        "role": "Schema-typed Python workflow orchestration & 1M-context primary-source synthesis",
    },
    "opencode_omo_hephaestus": {
        "upstream": "sst/opencode + code-yeongyu/oh-my-openagent",
        "versions": {"opencode": "2.3.0", "oh_my_openagent": "5.1.75"},
        "models": ("claude-sonnet-5-5", "deepseek-v4.1-flash"),
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
        "upstream": "native-agent-stack/dsh-sota-harness (goose retired v3.10.5)",
        "versions": {"dsh": "0.2.2-rc.2"},
        "models": ("deepseek-flash",),
        "capabilities": (
            "10-layer offline DSH probes",
            "pre-wall <=2026-10-15 batch factor evaluation",
            "DeepSeek-V4.1-Flash 1M-context synthesis",
        ),
        "role": "Open-weights pre-wall batch evaluator & DeepSeek-V4.1-Flash DSH harness (goose retired)",
    },
    "peer_bus_hcom_beads_omniroute_spine": {
        "upstream": (
            "ComposioHQ/agent-orchestrator + aannoo/hcom + steveyegge/beads + "
            "native-agent-stack/sota-multi-model-workflows"
        ),
        "versions": {
            "agent_orchestrator_ao": "8-slot-v3.9",
            "sota_bus": "SQLite-WAL",
            "hcom": "0.7.31",
            "bd": "1.3.4",
            "omniroute": "3.8.53",
        },
        "capabilities": (
            "8-slot Multi-Model AO cross-vendor convergence gate (ADR-0008)",
            "SQLite WAL BEGIN IMMEDIATE path-glob leases",
            "hcom cross-PTY push notifications",
            "sota-workstation coop @@B64: E2EE bridge",
            "Beads bd DAG issue tracker",
            "OmniRoute provider resilience router",
        ),
        "role": "8-slot AO convergence, transactional cross-session lease firewall, push messaging & resilience spine",
    },
}

DUAL_MACHINE_SURFACES: dict[str, dict[str, Any]] = {
    "portable_mac_m5_max": {
        "workstation": "Apple M5 Max (18 cores, 64 GB unified memory)",
        "platform": "darwin-arm64",
        "tailscale_ip": "100.93.211.101",
        "orca_port": 6770,
        "sovereign_paper_broker_host": False,
        "portable_command_cockpit_and_failover": True,
        "failover_paper_lanes": (
            "127.0.0.1:8787",
            "127.0.0.1:8799",
            "127.0.0.1:8797",
            "127.0.0.1:4002",
            "127.0.0.1:8798",
        ),
        "workspace_roots": ("~/Documents/*", "~/sota-dynamic-trail-c", "~/canon"),
        "role": "Portable command cockpit, interactive CC-Lead/AGY lead, read-only mirror of Noesis (100.110.115.22) & explicit single-host hot failover",
    },
    "stationary_noesis_win32": {
        "workstation": "AMD Threadripper (64 logical cores, 128 GB RAM) + NVIDIA GeForce RTX 4090 (24,564 MiB)",
        "platform": "win32",
        "tailscale_ip": "100.110.115.22",
        "orca_port": 6770,
        "sovereign_paper_broker_host": True,
        "primary_framework_and_trading_engine": True,
        "paper_lanes": ("127.0.0.1:8787", "127.0.0.1:8799", "127.0.0.1:8797", "127.0.0.1:4002", "127.0.0.1:8798"),
        "workspace_roots": ("C:/sota-workstation/* (18 repos)", "Z:/sota-data/prewall-lake (2.85 TB NVMe)"),
        "role": "Primary always-on 24/5 Sovereign Host for Main Framework Foundation, 4-Account Paper Farm + Stage-5 Live Trading Engine (:8787/:8799/:8797/:4002/:8798), 4K TradingView & 56c/RTX4090 CPCV sweeps",
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
        "primary_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "allows_noesis_broker_socket": True,
        "default_worker_trio": ("claude-opus-falsifier", "codex-astra-omx", "antigravity-carbon"),
        "invariants": (
            "Primary always-on stationary_noesis_win32 (:8787/:8799/:8797/:8798) with explicit single-host failover "
            "portable_mac_m5_max; PA... 1,000 req/min; ADR-0022 <=2.00% hard stop; DF1..DF12 PIT"
        ),
    },
    "T2_ibkr_paper_4002_and_event_sim_parity": {
        "lane_id": "T2_ibkr_paper_4002_and_event_sim_parity",
        "plane": "trading",
        "repos": ("astrolabe", "meridian"),
        "primary_surface": "stationary_noesis_carbon_wsl2",
        "broker_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "allows_noesis_broker_socket": True,
        "default_worker_trio": ("claude-opus-falsifier", "codex-astra-omx", "deepseek-dsh"),
        "invariants": (
            "IBKR :4002 DU... paper gateway primary on stationary_noesis_win32 (4001/7496 gated); "
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
        "allows_noesis_broker_socket": True,
        "default_worker_trio": ("claude-opus-falsifier", "codex-astra-omx", "deepseek-dsh"),
        "invariants": (
            "Pre-wall <=2026-10-15 CPCV/DSR/RTX 4090 sweeps on Z:/sota-data/prewall-lake "
            "(sha256=a253421e8734..., stationary_noesis_win32 / stationary_noesis_carbon_wsl2, roaming failover portable_mac_m5_max)"
        ),
    },
}

HARNESS_LANES: dict[str, dict[str, Any]] = {
    "H1_sovereign_cc_lead_and_multi_runtime_hub": {
        "lane_id": "H1_sovereign_cc_lead_and_multi_runtime_hub",
        "plane": "harness",
        "repos": ("cc-sota-harness", "sota-harness-foundation", "sota-multi-model-workflows"),
        "primary_surface": "stationary_noesis_win32",
        "paired_surface": "portable_mac_m5_max",
        "failover_surface": "portable_mac_m5_max",
        "default_worker_trio": ("claude-sonnet-omc", "codex-astra-omx", "antigravity-carbon"),
        "invariants": "Stationary Noesis Main Framework Foundation + 20-workflow v3.10.4 AGY/Orca hub + Portable Mac cockpit parity",
    },
    "H2_cross_vendor_verifiers_and_shelf_lock": {
        "lane_id": "H2_cross_vendor_verifiers_and_shelf_lock",
        "plane": "harness",
        "repos": ("agy-sota-harness", "dsh-sota-harness", "dsh-plugin-landscape", "sota-upstream-shelf-lock"),
        "primary_surface": "stationary_noesis_carbon_wsl2",
        "paired_surface": "portable_mac_m5_max",
        "failover_surface": "portable_mac_m5_max",
        "default_worker_trio": ("antigravity-carbon", "codex-astra-omx", "deepseek-dsh"),
        "invariants": "18-repo 40-hex upstream SHA lock, 13/13 AGY probes, 10/10 DSH probes & MinTRL/QueueModel gates",
    },
    "H3_org_control_plane_and_provenance": {
        "lane_id": "H3_org_control_plane_and_provenance",
        "plane": "harness",
        "repos": ("native-agent-stack", ".github", "canon"),
        "primary_surface": "stationary_noesis_win32",
        "paired_surface": "portable_mac_m5_max",
        "failover_surface": "portable_mac_m5_max",
        "default_worker_trio": ("claude-sonnet-omc", "codex-astra-omx", "antigravity-carbon"),
        "invariants": "Umbrella v3.x lock, reusable SHA-pinned Org CI, 4-invariant sota-org-doctor & Canon provenance",
    },
}


STAGE_AND_LAYER_SUBLANES: dict[str, dict[str, Any]] = {
    "T1_MERIDIAN_NAUTILUS_QUEUE_SIM": {
        "macro_hub_lane": "T2_ibkr_paper_4002_and_event_sim_parity",
        "stage": "Stage1_Simulation",
        "repos": ("meridian",),
    },
    "T2_PREWALL_CAUSAL_ALPHA_LAB": {
        "macro_hub_lane": "T3_prewall_cpcv_gpu_and_strategy_factory",
        "stage": "Stage2_PreWall_Research",
        "repos": ("canon", "trading-sota", "tsl"),
    },
    "T3A_ALPACA_200RPM_SIP_PAPER": {
        "macro_hub_lane": "T1_live_24x5_alpaca_paper_and_guardian",
        "stage": "Stage3A_Alpaca_Paper",
        "repos": ("sota-mover-ranker",),
    },
    "T3B_IBKR_4002_NAUTILUS_PAPER": {
        "macro_hub_lane": "T2_ibkr_paper_4002_and_event_sim_parity",
        "stage": "Stage3B_IBKR_Paper",
        "repos": ("astrolabe",),
    },
    "T4_T5_COMPOUNDING_GUARDIAN_VAULT": {
        "macro_hub_lane": "T1_live_24x5_alpaca_paper_and_guardian+T3_prewall_cpcv_gpu_and_strategy_factory",
        "stage": "Stage4_5_Compounding_And_Guardian",
        "repos": ("sota-compounding-lab", "sota-dynamic-trail-c", "sota-private-vault"),
    },
    "H0_ORG_GOVERNANCE_CI": {
        "macro_hub_lane": "H3_org_control_plane_and_provenance",
        "layer": "L0",
        "repos": (".github",),
    },
    "H1_ECOSYSTEM_UMBRELLA_LOCK": {
        "macro_hub_lane": "H3_org_control_plane_and_provenance",
        "layer": "L1",
        "repos": ("native-agent-stack",),
    },
    "H2_UPSTREAM_40SHA_SHELF_LOCK": {
        "macro_hub_lane": "H2_cross_vendor_verifiers_and_shelf_lock",
        "layer": "L2",
        "repos": ("sota-upstream-shelf-lock",),
    },
    "H3_OPEN_CORE_MULTI_RUNTIME_FOUNDATION": {
        "macro_hub_lane": "H1_sovereign_cc_lead_and_multi_runtime_hub",
        "layer": "L3",
        "repos": ("sota-harness-foundation",),
    },
    "H4_ANTIGRAVITY_L0_L13_HARNESS": {
        "macro_hub_lane": "H2_cross_vendor_verifiers_and_shelf_lock",
        "layer": "L4",
        "repos": ("agy-sota-harness",),
    },
    "H5_CLAUDE_LEAD_28RUNTIME_HARNESS": {
        "macro_hub_lane": "H1_sovereign_cc_lead_and_multi_runtime_hub",
        "layer": "L5",
        "repos": ("cc-sota-harness",),
    },
    "H6_DEEPSEEK_10LAYER_HARNESS": {
        "macro_hub_lane": "H2_cross_vendor_verifiers_and_shelf_lock",
        "layer": "L6",
        "repos": ("dsh-sota-harness", "dsh-plugin-landscape"),
    },
    "H7_MULTI_MODEL_WORKFLOWS_WAL_BUS": {
        "macro_hub_lane": "H1_sovereign_cc_lead_and_multi_runtime_hub",
        "layer": "L7",
        "repos": ("sota-multi-model-workflows",),
    },
}


# Canonical named Orca Lane Leads across trading-lanes & harness-lanes (Mac <-> Noesis Co-Op Consensus v3.10.4).
# T5_stage5_live_lane_read_only_audit is explicitly declared read-only with zero broker credentials or order write path.
CANONICAL_ORCA_LANE_LEADS: dict[str, dict[str, Any]] = {
    "T1_paper_guardian_lead": {
        "lead_id": "T1_paper_guardian_lead",
        "worktree_name": "t1-paper-guardian-lead",
        "plane": "trading",
        "macro_hub_lane": "T1_live_24x5_alpaca_paper_and_guardian",
        "primary_repo": "sota-dynamic-trail-c",
        "repos": ("sota-dynamic-trail-c", "sota-mover-ranker"),
        "active_host_policy": "FOLLOW_ACTIVE_ALPACA_BROKER_HOST",
        "active_host_pre_cutover": "portable_mac_m5_max",
        "target_host_post_cutover": "stationary_noesis_win32",
        "default_agent": "claude",
        "default_model": "claude-opus-5-5",
        "mode": "paper_audit_and_guardian_ops",
        "ports_observed": (8799, 8787, 8797),
        "charter": (
            "Own P1 (:8799) Lossless Foundation guardian, P2 (:8787) Balanced Ranker, P3 (:8797) Aggressive Lab, "
            "Dec-6 23/5 SIP readiness, and P0 ADR-0017/ADR-0019 shield wiring fixes (single-broker-host firewall)."
        ),
    },
    "T2_ibkr_and_sim_lead": {
        "lead_id": "T2_ibkr_and_sim_lead",
        "worktree_name": "t2-ibkr-sim-lead",
        "plane": "trading",
        "macro_hub_lane": "T2_ibkr_paper_4002_and_event_sim_parity",
        "primary_repo": "meridian",
        "repos": ("meridian", "astrolabe"),
        "active_host_policy": "STATIONARY_NOESIS_PRIMARY",
        "active_host_pre_cutover": "stationary_noesis_carbon_wsl2",
        "target_host_post_cutover": "stationary_noesis_carbon_wsl2",
        "default_agent": "codex",
        "default_model": "gpt-6.2-astra",
        "mode": "event_sim_and_ibkr_paper_4002",
        "ports_observed": (4002,),
        "charter": (
            "Own S2 NautilusTrader v2rc9 / hftbacktest RiskAdverseQueueModel (-n 8) queue-fill simulation on "
            "Noesis-Carbon WSL2 ext4 and IBKR Paper :4002 parity (4001/7496 hard-gated)."
        ),
    },
    "T3_prewall_factory_lead": {
        "lead_id": "T3_prewall_factory_lead",
        "worktree_name": "t3-prewall-factory-lead",
        "plane": "trading",
        "macro_hub_lane": "T3_prewall_cpcv_gpu_and_strategy_factory",
        "primary_repo": "sota-compounding-lab",
        "repos": ("sota-compounding-lab", "trading-sota", "tsl", "sota-private-vault"),
        "active_host_policy": "STATIONARY_NOESIS_PRIMARY",
        "active_host_pre_cutover": "stationary_noesis_win32",
        "target_host_post_cutover": "stationary_noesis_win32",
        "default_agent": "codex",
        "default_model": "gpt-6.2-sol",
        "mode": "prewall_cpcv_dsr_hlz_factory",
        "ports_observed": (),
        "charter": (
            "Own S1 64c/RTX4090 pre-wall (<=2026-10-15) alpha factory on Z:/sota-data/prewall-lake enforcing "
            "ADIA #19 MinTRL, HLZ t*(N), C(6,2)=15 CPCV, DSR >= 0.95, and 1x/2x Almgren-Chriss stress."
        ),
    },
    "T5_stage5_live_lane_read_only_audit": {
        "lead_id": "T5_stage5_live_lane_read_only_audit",
        "worktree_name": "t5-stage5-live-lane-lead",
        "plane": "trading",
        "macro_hub_lane": "T1_live_24x5_alpaca_paper_and_guardian",
        "merit_lane_id": "LIVE_L5_STAGE5_LOSSLESS",
        "primary_repo": "sota-mover-ranker",
        "repos": ("sota-mover-ranker", "sota-dynamic-trail-c"),
        "active_host_policy": "READ_ONLY_DUAL_HOST_AUDIT",
        "active_host_pre_cutover": "stationary_noesis_win32",
        "target_host_post_cutover": "stationary_noesis_win32",
        "default_agent": "claude",
        "default_model": "claude-fable-5-2",
        "mode": "read_only_audit_and_merit_qualification",
        "broker_credentials": False,
        "order_write_path": False,
        "live_window_state": "CLOSED_BY_DEFAULT",
        "owner_manual_open_only": True,
        "ports_observed": (8798, 8796),
        "p0_blockers_required_before_arming": (
            "P0-1_ADR0017_COOLDOWN_STREAK_AND_ELAPSED_UNCAP",
            "P0-2_ADR0017_PROBATION_INPUTS_WIRED",
            "P0-3_ADR0017_EXTENDED_HOURS_AND_SAR_GATE",
            "P0-4_UNIFIED_SHIELD_ON_VIX_8797_8798_AND_OPEN5M",
            "P0-5_DRAWDOWN_BREAKER_AND_CLEAN_PAPER_COHORT",
            "P0-6_SUPERVISOR_KEEPALIVE_AND_8796_LIVE_GUARDIAN",
        ),
        "charter": (
            "Strictly READ-ONLY Stage-5 (:8798) Live Lane Lead: holds ZERO broker credentials and ZERO order write path; "
            "tracks P0-1..6 closure, 5 Lossless Foundation invariants, clean paper merit qualification, and "
            "draft-only readiness. Owner manual act exclusively controls the live window."
        ),
    },
    "H1_cc_lead_orchestrator": {
        "lead_id": "H1_cc_lead_orchestrator",
        "worktree_name": "h1-cc-lead-orchestrator",
        "plane": "harness",
        "macro_hub_lane": "H1_sovereign_cc_lead_and_multi_runtime_hub",
        "primary_repo": "cc-sota-harness",
        "repos": ("cc-sota-harness", "sota-harness-foundation", "sota-multi-model-workflows"),
        "active_host_policy": "PAIRED_DUAL_HOST_COCKPIT",
        "active_host_pre_cutover": "stationary_noesis_win32",
        "target_host_post_cutover": "stationary_noesis_win32",
        "default_agent": "claude",
        "default_model": "claude-fable-5-2",
        "mode": "sovereign_orchestration_and_wf20",
        "ports_observed": (8792, 6770),
        "charter": (
            "Sovereign Claude Code (cc-lead) orchestrator commanding 57 skills, 20 canonical workflows, "
            "4 MCP servers (50 tools), SQLite WAL peer-bus, and symmetric Mac <-> Noesis Orca mesh."
        ),
    },
    "H2_cross_vendor_verifier_lead": {
        "lead_id": "H2_cross_vendor_verifier_lead",
        "worktree_name": "h2-cross-vendor-verifier-lead",
        "plane": "harness",
        "macro_hub_lane": "H2_cross_vendor_verifiers_and_shelf_lock",
        "primary_repo": "agy-sota-harness",
        "repos": ("agy-sota-harness", "dsh-sota-harness", "dsh-plugin-landscape", "sota-upstream-shelf-lock"),
        "active_host_policy": "STATIONARY_NOESIS_PRIMARY",
        "active_host_pre_cutover": "stationary_noesis_carbon_wsl2",
        "target_host_post_cutover": "stationary_noesis_carbon_wsl2",
        "default_agent": "codex",
        "default_model": "gpt-6.2-astra",
        "mode": "cross_vendor_probes_and_shelf_lock",
        "ports_observed": (),
        "charter": (
            "Own 13/13 AGY probes, 10/10 DSH probes, 18-repo 40-hex upstream SHA shelf lock, and "
            "cross-vendor Codex/Gemini/DeepSeek verification gates."
        ),
    },
    "H3_org_control_and_provenance_lead": {
        "lead_id": "H3_org_control_and_provenance_lead",
        "worktree_name": "h3-org-control-lead",
        "plane": "harness",
        "macro_hub_lane": "H3_org_control_plane_and_provenance",
        "primary_repo": ".github",
        "repos": ("native-agent-stack", ".github", "canon"),
        "active_host_policy": "STATIONARY_NOESIS_PRIMARY",
        "active_host_pre_cutover": "stationary_noesis_win32",
        "target_host_post_cutover": "stationary_noesis_win32",
        "default_agent": "claude",
        "default_model": "claude-sonnet-5-5",
        "mode": "org_manifest_ci_and_canon_provenance",
        "ports_observed": (),
        "charter": (
            "Own .github/ECOSYSTEM_ORG_MANIFEST.json 22/22 SHA seals, 9-PUBLIC SHA-pinned Actions vs "
            "9-PRIVATE zero-burn firewall, and Canon MADR 4.0 provenance."
        ),
    },
    "D4_all_market_research_lead": {
        "lead_id": "D4_all_market_research_lead",
        "worktree_name": "d4-all-market-research-lead",
        "plane": "trading",
        "macro_hub_lane": "T3_prewall_cpcv_gpu_and_strategy_factory",
        "domain_hub_slug": "04-research-all-market",
        "primary_repo": "canon",
        "repos": ("canon", "sota-compounding-lab", "sota-mover-ranker", "trading-sota", "tsl"),
        "active_host_policy": "STATIONARY_NOESIS_PRIMARY",
        "active_host_pre_cutover": "stationary_noesis_win32",
        "target_host_post_cutover": "stationary_noesis_win32",
        "default_agent": "claude",
        "default_model": "claude-fable-5-2",
        "mode": "all_market_bitemporal_research",
        "ports_observed": (),
        "charter": (
            "Own Lane 04 All-Market Quantitative Research across DF1..DF12 bitemporal PIT feeds, "
            "equities/VIX/FX/crypto/futures/IPO cross-asset regimes, and SHA-256 pre-registered trials (H099+)."
        ),
    },
    "D5_non_market_incentives_lead": {
        "lead_id": "D5_non_market_incentives_lead",
        "worktree_name": "d5-non-market-incentives-lead",
        "plane": "trading",
        "macro_hub_lane": "T1_live_24x5_alpaca_paper_and_guardian",
        "domain_hub_slug": "05-non-market-incentives",
        "primary_repo": "sota-mover-ranker",
        "repos": ("sota-mover-ranker", "canon", "sota-compounding-lab", "sota-private-vault"),
        "active_host_policy": "STATIONARY_NOESIS_PRIMARY",
        "active_host_pre_cutover": "stationary_noesis_win32",
        "target_host_post_cutover": "stationary_noesis_win32",
        "default_agent": "claude",
        "default_model": "claude-sonnet-5-5",
        "mode": "read_only_sec_edgar_and_ipo_catalysts",
        "broker_credentials": False,
        "order_write_path": False,
        "ports_observed": (),
        "charter": (
            "Own Lane 05 Non-Market Incentives & Catalysts: SEC EDGAR acceptanceDateTime PIT filings "
            "(S-1/424B4/424B5/S-3 dilution shields, 8-K, 13F/Form-4), NASDAQ:ANT $83 IPO terms, FDA/Gov/Macro."
        ),
    },
    "D7_beyond_skillopt_lead": {
        "lead_id": "D7_beyond_skillopt_lead",
        "worktree_name": "d7-beyond-skillopt-lead",
        "plane": "harness",
        "macro_hub_lane": "H2_cross_vendor_verifiers_and_shelf_lock",
        "domain_hub_slug": "07-beyond-convergence-skillopt",
        "primary_repo": "sota-upstream-shelf-lock",
        "repos": (
            "sota-upstream-shelf-lock",
            "dsh-plugin-landscape",
            "native-agent-stack",
            "sota-multi-model-workflows",
        ),
        "active_host_policy": "STATIONARY_NOESIS_PRIMARY",
        "active_host_pre_cutover": "stationary_noesis_win32",
        "target_host_post_cutover": "stationary_noesis_win32",
        "default_agent": "codex",
        "default_model": "gpt-6.2-astra",
        "mode": "upstream_shelf_and_skillopt_gepa_evolution",
        "ports_observed": (),
        "charter": (
            "Own Lane 07 Beyond Convergence: 18 immutable 40-char upstream shelf pins, 413+6 frontier stars, "
            "SkillOpt/GEPA trajectory mining into LESSONS.md, and 7-vendor cross-family adversarial convergence."
        ),
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
    active_broker_host_shield: bool = False,
    active_broker_host: str = "stationary_noesis_win32",
) -> dict[str, Any]:
    """Deterministically resolve surface, Orca `worker-start` command, and >=3-vendor worker trio for `repo`."""
    lane = REPO_LANE_INDEX.get(repo)
    if lane is None:
        raise ValueError(f"Unknown ecosystem repository {repo!r}; valid={sorted(REPO_LANE_INDEX)}")
    if requested_placement not in ("auto", "local", "noesis"):
        raise ValueError(f"Invalid requested_placement {requested_placement!r}; expected auto|local|noesis")
    if active_broker_host not in ("stationary_noesis_win32", "portable_mac_m5_max"):
        raise ValueError(
            f"Invalid active_broker_host {active_broker_host!r}; expected stationary_noesis_win32|portable_mac_m5_max"
        )

    lane_id = str(lane["lane_id"])
    plane = str(lane["plane"])
    mesh_online = mesh_state in ("dual_mesh_docked", "dual_mesh_on_battery")
    is_broker_bound = workload == "active_paper_broker" or (
        lane_id == "T1_live_24x5_alpaca_paper_and_guardian" and workload == "default"
    )
    is_ibkr_broker = repo == "astrolabe" and workload in ("default", "active_paper_broker")

    # Symmetric Single-Broker-Host Firewall (ADR-0028): <=1 active broker host at any instant!
    # Default primary: stationary_noesis_win32 (100.110.115.22); explicit failover: portable_mac_m5_max.
    if is_broker_bound or is_ibkr_broker:
        if active_broker_host == "stationary_noesis_win32" and mesh_online:
            if requested_placement == "local":
                raise PermissionError(
                    f"SINGLE_BROKER_HOST_FIREWALL: active broker workload on {repo!r} ({lane_id}) "
                    "is pinned to primary stationary_noesis_win32 while mesh is online (singleActiveBrokerHostOnly=True)"
                )
            selected_surface = "stationary_noesis_win32"
            use_noesis = True
        elif active_broker_host == "portable_mac_m5_max":
            if requested_placement == "noesis":
                raise PermissionError(
                    f"SINGLE_BROKER_HOST_FIREWALL: active broker workload on {repo!r} ({lane_id}) "
                    "is pinned to failover portable_mac_m5_max while Mac holds active lease (singleActiveBrokerHostOnly=True)"
                )
            selected_surface = "portable_mac_m5_max"
            use_noesis = False
        else:
            # Workstation unreachable -> seamless portable Mac failover
            selected_surface = "portable_mac_m5_max"
            use_noesis = False
    elif requested_placement == "local" or not mesh_online:
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
        # requested_placement == "auto" and mesh_online -> Workstation hosts Main Framework Foundation & Sim
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
        elif plane == "harness" and workload == "default":
            selected_surface = str(lane.get("primary_surface") or "stationary_noesis_win32")
            use_noesis = selected_surface != "portable_mac_m5_max"
        elif (mesh_state == "dual_mesh_on_battery" or active_broker_host_shield) and workload in (
            "heavy_test_sweep",
            "cross_os_ci_parity",
        ):
            selected_surface = str(lane.get("primary_surface") or "stationary_noesis_carbon_wsl2")
            use_noesis = True
        else:
            selected_surface = "portable_mac_m5_max"
            use_noesis = False

    is_mac_pinned = (is_broker_bound or is_ibkr_broker) and selected_surface == "portable_mac_m5_max"
    on_noesis_self = is_running_on_noesis_host()
    if is_mac_pinned:
        if on_noesis_self:
            orca_repo_selector = f"id:{local_orca_repo_id}" if local_orca_repo_id else f"name:{repo}"
            remote_wt_args = ["--environment", "100.93.211.101"]
            remote_start_args = ["--on", "100.93.211.101"]
        else:
            resolved_local = local_orca_repo_id or resolve_local_orca_repo_id(repo)
            orca_repo_selector = f"id:{resolved_local}" if resolved_local else f"name:{repo}"
            remote_wt_args = []
            remote_start_args = []
        lane_hub = ORCA_LANE_HUBS["portable_mac_m5_max"][plane]
    elif use_noesis or on_noesis_self:
        remote_uuid = NOESIS_PROVISIONED_ORCA_REPOS[repo]
        orca_repo_selector = f"id:{remote_uuid}"
        lane_hub = ORCA_LANE_HUBS["stationary_noesis"][plane]
        remote_wt_args = orca_remote_on_args(use_noesis=use_noesis, flag="--environment", on_noesis_self=on_noesis_self)
        remote_start_args = orca_remote_on_args(use_noesis=use_noesis, flag="--on", on_noesis_self=on_noesis_self)
    else:
        resolved_local = local_orca_repo_id or resolve_local_orca_repo_id(repo)
        orca_repo_selector = f"id:{resolved_local}" if resolved_local else f"name:{repo}"
        lane_hub = ORCA_LANE_HUBS["portable_mac_m5_max"][plane]
        remote_wt_args = []
        remote_start_args = []

    worker_trio: tuple[str, ...] = tuple(lane["default_worker_trio"])
    lead_wk = worker_trio[0]
    lead_meta = RUNTIME_WORKER_ROSTER[lead_wk]
    slug = repo.replace(".", "dot").replace("_", "-").lower()
    wt_name = f"lane-{slug}-{workload[:12].replace('_', '-')}"

    orca_folder_worktree_argv = [
        "orca",
        "worktree",
        "create",
        *remote_wt_args,
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
        *remote_start_args,
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
                f"Enforce {RANKING_DATAFEEDS_SCHEMA_VERSION} (DF1..DF9, compat {RESEARCH_FEEDS_SCHEMA_VERSION}), "
                f"ADR-0004/ADR-0016 ({SIBLING_REPO_AUTHORITY}), pre-wall <={PRE_WALL_MAX_DATE}, "
                f"and ADR-0022 <={MAX_HARD_STOP_PCT:.2f}% stop."
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
                "active_broker_host_shield": active_broker_host_shield,
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
        "active_broker_host_shield": active_broker_host_shield,
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
            "ranking_datafeeds_schema": RANKING_DATAFEEDS_SCHEMA_VERSION,
            "ranking_feeds_count": len(CANONICAL_RANKING_DATAFEEDS_V38),
            "prewall_lake_sha256": DEFAULT_PREWALL_LAKE_SHA256,
            "provenance_adr": "ADR-0004",
            "sibling_repo_authority": SIBLING_REPO_AUTHORITY,
            "prewall_max_date": PRE_WALL_MAX_DATE,
            "max_hard_stop_pct": MAX_HARD_STOP_PCT,
        },
        "lane_plan_sha256": receipt_sha256,
    }


def render_orca_lane_hub_artifacts(plane: str) -> dict[str, str]:
    """Render deterministic `sota-orca-lane-hub.v2` `LANE_MANIFEST.json`, `orca.yaml`, and `README.md`."""
    if plane not in ("trading", "harness"):
        raise ValueError(f"Invalid plane {plane!r}; expected 'trading' or 'harness'")

    is_trading = plane == "trading"
    lane_map = TRADING_LANES if is_trading else HARNESS_LANES
    sublanes = {
        k: v for k, v in STAGE_AND_LAYER_SUBLANES.items() if (k.startswith("T") if is_trading else k.startswith("H"))
    }
    lane_leads = {k: v for k, v in CANONICAL_ORCA_LANE_LEADS.items() if v["plane"] == plane}
    manifest_obj: dict[str, Any] = {
        "schemaVersion": ORCA_LANE_HUB_SCHEMA_VERSION,
        "ecosystemVersion": "3.10.5",
        "plane": "TRADING_LANES" if is_trading else "HARNESS_LANES",
        "adrAuthority": [
            "ADR-0004 (Research-Convergence & 4-Hash Provenance)",
            "ADR-0014 (Dual-Machine Orca Trading & Harness Lanes + 8-Framework Matrix)",
            "ADR-0015 (9-Feed DF1..DF9 Compat / 12-Feed DF1..DF12 Bitemporal Ranking DataFeeds)",
            "ADR-0016 (Full-Landscape SOTA Layer, 18/18 UPSTREAM.md & Orca Lane Hub v2 Seal)",
            "ADR-0020 (Symmetric :6770 Dual-Workstation Orca & Single-Broker-Host Firewall)",
            "ADR-0022 (<= 2.00% Reg NMS Rule 612 Protective Stop-Limit)",
            "ADR-0027 (7-Lane Grand Merit-Promotion Harness & Stage-5 Read-Only Gate)",
            "ADR-0028 (v3.10.4 Stationary Noesis Primary 24/5 Host & Portable Mac Hot Failover)",
            "ADR-0029 (v3.10.5 Full-Ecosystem 7-Domain Orca Lane Hubs & Lead Topology)",
        ],
        "singleActiveBrokerHostOnly": True,
        "rthBrokerContentionShield": True,
        "sovereignPaperBrokerHost": "stationary_noesis_win32 (100.110.115.22; failover portable_mac_m5_max 100.93.211.101)",
        "activePreCutoverBrokerSplit": {
            "alpaca_paper_ports_8787_8799_8797": "portable_mac_m5_max",
            "ibkr_paper_port_4002": "stationary_noesis_win32",
            "stage5_live_port_8798": "STANDBY_OWNER_LIVE_WINDOW_CLOSED",
            "cutover_prerequisites": [
                "P0-1..6 sota-mover-ranker ADR-0017/ADR-0019 shield & supervisor fixes",
                "Owner Windows Credential Manager seeding on stationary_noesis_win32",
                "Owner-called zero-overlap v3.10.4 single-host cutover",
            ],
        },
        "pairedWorkstationSurfaces": DUAL_MACHINE_SURFACES,
        "orcaHubSelectors": {
            "portable_mac_m5_max": ORCA_LANE_HUBS["portable_mac_m5_max"][plane],
            "stationary_noesis": ORCA_LANE_HUBS["stationary_noesis"][plane],
        },
        "rankingDatafeedsSchema": RANKING_DATAFEEDS_SCHEMA_VERSION,
        "rankingDatafeedsCount": len(CANONICAL_RANKING_DATAFEEDS_V38),
        "bitemporalRankingFeedsCount": 12,
        "prewallLakeSha256": DEFAULT_PREWALL_LAKE_SHA256,
        "orchestrationFrameworksCount": len(ORCHESTRATION_FRAMEWORKS_MATRIX),
        "runtimeWorkersCount": len(RUNTIME_WORKER_ROSTER),
        "modelVendors": list(CANONICAL_SEVEN_MODEL_VENDORS),
        "macroLanes": lane_map,
        "stageAndLayerSubLanes": sublanes,
        "laneLeads": lane_leads,
    }
    hub_title = (
        "Trading Lanes (`T1–T3` + `T5` Read-Only Stage-5 Audit)" if is_trading else "Harness Lanes (`H1–H3` / `H0–H7`)"
    )
    orca_yaml = (
        f"# SOTA Dual-Machine Orca Folder Hub Recipe — {hub_title} (v3.10.7, Cross-OS Win32/macOS/Linux)\n"
        "setupAgentStartupPolicy: wait-for-setup\n"
        "scripts:\n"
        "  setup: |\n"
        f'    echo "[SOTA Orca Hub] {plane}-lanes ready"\n'
        "defaultTabs:\n"
        "  - title: Lead Agent\n"
        f"  - title: {plane}-lanes Status\n"
        f"    command: sota-lanes status --plane {plane} --json\n"
    )
    readme_lines = [
        f"# SOTA Dual-Machine Orca Hub — {hub_title} (`v3.10.7`)",
        "",
        (
            f"Schema: `{ORCA_LANE_HUB_SCHEMA_VERSION}` · DataFeeds: `DF1..DF12` (`{RANKING_DATAFEEDS_SCHEMA_VERSION}` `DF1..DF9` compat) · "
            f"Pre-Wall Lake SHA-256: `{DEFAULT_PREWALL_LAKE_SHA256}` (`<= {PRE_WALL_MAX_DATE}`)."
        ),
        "",
        "- **Symmetric Orca Mesh:** `stationary_noesis` (`100.110.115.22:6770` Win32 + `Noesis-Carbon` WSL2 `ext4`, `ADR-0028`/`ADR-0041` primary sovereign 24/5 host) <-> `portable_mac_m5_max` (`100.93.211.101:6768`, portable cockpit & hot failover).",
        "- **Single-Broker-Host Firewall (`singleActiveBrokerHostOnly = true`):** Active 4 Paper accounts (`:8799`, `:8787`, `:8797`, IBKR `:4002`) + Stage-5 (`:8798`, `draft_only=true`) run on `stationary_noesis`; `portable_mac_m5_max` stays parked (`MAC_BROKER_PORTS=0`) for zero dual-host routing.",
        "- **Stage-5 Live Lane Lead (`T5_stage5_live_lane_read_only_audit`):** Strictly `read_only_audit_and_merit_qualification` (`broker_credentials=false`, `order_write_path=false`, `live_window_state=CLOSED_BY_DEFAULT`); owner manual act exclusively governs the live window.",
        f"- **Multi-Model Fleet:** `{len(ORCHESTRATION_FRAMEWORKS_MATRIX)}` SOTA orchestration frameworks, `57` canonical skills, `{len(RUNTIME_WORKER_ROSTER)}` workers across `{len(CANONICAL_SEVEN_MODEL_VENDORS)}` model vendors.",
        "",
        "## Macro Hub Groups",
    ]
    for lid, lmeta in lane_map.items():
        readme_lines.append(f"- **`{lid}`:** `{', '.join(lmeta['repos'])}` — {lmeta['invariants']}")
    readme_lines.append("")
    readme_lines.append("## Canonical Named Lane Leads")
    for lead_id, lead_meta in lane_leads.items():
        readme_lines.append(
            f"- **`{lead_id}`** (`{lead_meta['worktree_name']}`, `{lead_meta['mode']}`, `{lead_meta['default_agent']}/{lead_meta['default_model']}`): {lead_meta['charter']}"
        )
    readme_lines.append("")
    return {
        "LANE_MANIFEST.json": json.dumps(manifest_obj, indent=2, default=list) + "\n",
        "orca.yaml": orca_yaml,
        "README.md": "\n".join(readme_lines),
    }


ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES: dict[str, dict[str, Any]] = {
    "01-sim-backtest": {
        "order": 1,
        "slug": "01-sim-backtest",
        "title": "Lane 01 — Sim & Pre-Wall Backtest Factory (S1 Win32 64c/RTX4090 + S2 WSL2 Nautilus/Queue)",
        "domain": "SIM_AND_PREWALL_BACKTEST",
        "gating_policy": "NEVER_GATED",
        "primary_surface": "stationary_noesis_win32",
        "companion_surface": "stationary_noesis_carbon_wsl2",
        "failover_surface": "portable_mac_m5_max",
        "lead_agent": "codex-astra-omx",
        "worker_trio": ("codex-astra-omx", "deepseek-dsh", "claude-opus-falsifier"),
        "repos": ("sota-compounding-lab", "meridian", "trading-sota", "tsl", "sota-private-vault"),
        "upstream_platforms": (
            "polars",
            "duckdb",
            "vectorbt",
            "skfolio",
            "ml4t-diagnostic",
            "nautilus_trader",
            "hftbacktest",
        ),
        "invariants": "Strictly <= 2026-10-15 pre-wall; ADIA #19 MinTRL; HLZ t*(N); RiskAdverseQueueModel -n 8; 1x/2x Almgren-Chriss.",
        "default_command": "sota-lanes status --plane trading --json",
    },
    "02-paper-4acct-farm": {
        "order": 2,
        "slug": "02-paper-4acct-farm",
        "title": "Lane 02 — 4-Account Multi-Paper Farm (P1:8799, P2:8787, P3:8797 Alpaca + P4:4002 IBKR)",
        "domain": "MULTI_PAPER_FARM",
        "gating_policy": "NEVER_GATED",
        "primary_surface": "stationary_noesis_win32",
        "companion_surface": "stationary_noesis_carbon_wsl2",
        "failover_surface": "portable_mac_m5_max",
        "lead_agent": "antigravity-carbon",
        "worker_trio": ("antigravity-carbon", "claude-sonnet-omc", "codex-astra-omx"),
        "repos": ("sota-mover-ranker", "sota-dynamic-trail-c", "astrolabe"),
        "upstream_platforms": (
            "alpaca-mcp-server==2.4.1",
            "alpaca-py",
            "ib_async",
            "perspective",
            "lightweight-charts",
        ),
        "invariants": "3 distinct Alpaca Paper + 1 IBKR Paper NEVER GATED; ADR-0022 <= 2.00% stop; symmetric Single-Broker-Host Firewall (singleActiveBrokerHostOnly=true).",
        "default_command": "sota-lanes merit --json",
    },
    "03-stage5-lossless-live": {
        "order": 3,
        "slug": "03-stage5-lossless-live",
        "title": "Lane 03 — Stage-5 Lossless Live & Protection (:8798 RTH Atomic + :8796 Dedicated Live Guardian)",
        "domain": "STAGE5_LOSSLESS_LIVE",
        "gating_policy": "PROVEN_AUTOMATION_ONLY_STARTING_WITH_LOSSLESS_FOUNDATION",
        "primary_surface": "stationary_noesis_win32",
        "companion_surface": "stationary_noesis_carbon_wsl2",
        "failover_surface": "portable_mac_m5_max",
        "lead_agent": "claude-opus-falsifier",
        "worker_trio": ("claude-opus-falsifier", "antigravity-carbon", "codex-astra-omx"),
        "repos": ("sota-mover-ranker", "sota-dynamic-trail-c", "sota-harness-foundation"),
        "upstream_platforms": ("alpaca-mcp-server==2.4.1", "ib_async", "exchange_calendars"),
        "invariants": (
            "5 Stage-5 Lossless Invariants (ADR-0045): Paper-merit provenance, zero naked orders "
            "(RTH atomic OCO / EXT dedicated :8796 LIVE guardian), ADR-0022 <= 2.00% hard stop, "
            "LULD +/-10% pre-halt & Reg M Rule 104 floors, 1,000 req/min with 100/min exit reserve, "
            "-1.50% breaker, singleActiveBrokerHostOnly=true, Credential-Manager window + 0 PII/USD leaks."
        ),
        "default_command": "sota-lanes merit --json",
    },
    "04-research-all-market": {
        "order": 4,
        "slug": "04-research-all-market",
        "title": "Lane 04 — All-Market Quantitative Research (Equities, ETFs, Options/VIX, FX, Crypto, Futures, IPOs)",
        "domain": "ALL_MARKET_RESEARCH",
        "gating_policy": "NEVER_GATED",
        "primary_surface": "stationary_noesis_win32",
        "companion_surface": "stationary_noesis_carbon_wsl2",
        "failover_surface": "portable_mac_m5_max",
        "lead_agent": "antigravity-carbon",
        "worker_trio": ("antigravity-carbon", "deepseek-dsh", "codex-sol"),
        "repos": ("sota-compounding-lab", "canon", "trading-sota", "tsl", "sota-mover-ranker"),
        "upstream_platforms": (
            "polars",
            "duckdb",
            "pandera",
            "statsmodels",
            "quantstats",
            "alpaca-py",
            "ib_async",
        ),
        "invariants": "Bitemporal DF1..DF12 PIT ordering (ts_event <= ts_recv <= decision); cross-asset volatility/VIX/IPO/4x precursor calibration; SHA-256 pre-registered trials (H099+).",
        "default_command": "sota-workflow status --json",
    },
    "05-non-market-incentives": {
        "order": 5,
        "slug": "05-non-market-incentives",
        "title": "Lane 05 — Non-Market Incentives & Catalysts (SEC EDGAR, FDA/PDUFA, Patents, Gov/DoD, Fed/Macro)",
        "domain": "NON_MARKET_INCENTIVES_AND_CATALYSTS",
        "gating_policy": "NEVER_GATED",
        "primary_surface": "stationary_noesis_win32",
        "companion_surface": "portable_mac_m5_max",
        "failover_surface": "portable_mac_m5_max",
        "lead_agent": "antigravity-carbon",
        "worker_trio": ("antigravity-carbon", "claude-sonnet-omc", "deepseek-dsh"),
        "repos": ("sota-mover-ranker", "sota-compounding-lab", "canon", "sota-private-vault"),
        "upstream_platforms": ("edgartools", "polars", "duckdb", "qmd"),
        "invariants": "Point-in-time acceptanceDateTime timestamps ONLY (zero filing-date look-ahead); SEC S-1/424B4/424B5/S-3 dilution shields, 8-K catalysts, 13F/Form-4 insider incentives, FDA/PDUFA, Gov/DoD awards & macro prints.",
        "default_command": "sota-workflow status --json",
    },
    "06-framework-and-harness": {
        "order": 6,
        "slug": "06-framework-and-harness",
        "title": "Lane 06 — Main Framework Foundation & Multi-Runtime Harness (Stationary Noesis Primary)",
        "domain": "MAIN_FRAMEWORK_AND_HARNESS",
        "gating_policy": "CONTINUOUS_CI_GATED",
        "primary_surface": "stationary_noesis_win32",
        "companion_surface": "portable_mac_m5_max",
        "failover_surface": "portable_mac_m5_max",
        "lead_agent": "claude-sonnet-omc",
        "worker_trio": ("claude-sonnet-omc", "codex-astra-omx", "antigravity-carbon"),
        "repos": (
            "sota-harness-foundation",
            "sota-multi-model-workflows",
            "cc-sota-harness",
            "agy-sota-harness",
            "dsh-sota-harness",
            "native-agent-stack",
            ".github",
        ),
        "upstream_platforms": ("stablyai/orca", "oh-my-claudecode", "oh-my-codex", "hcom", "beads", "qmd"),
        "invariants": "20/20 self-bootstrapping workflows; 14/14 sota-doctor; 22/22 SHA-pinned org manifest; zero-drift MADR 4.0 ADRs; cross-OS Win32/WSL2/Darwin parity.",
        "default_command": "sota-lanes status --plane harness --json",
    },
    "07-beyond-convergence-skillopt": {
        "order": 7,
        "slug": "07-beyond-convergence-skillopt",
        "title": "Lane 07 — Beyond: 18-Repo Upstream Shelf, SkillOpt/GEPA Self-Evolution & 7-Vendor AO Convergence",
        "domain": "BEYOND_CONVERGENCE_AND_SKILLOPT",
        "gating_policy": "NEVER_GATED_RESEARCH_TO_CI_PROMOTION",
        "primary_surface": "stationary_noesis_carbon_wsl2",
        "companion_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "lead_agent": "antigravity-carbon",
        "worker_trio": ("antigravity-carbon", "claude-opus-falsifier", "codex-astra-omx"),
        "repos": (
            "sota-upstream-shelf-lock",
            "dsh-plugin-landscape",
            "native-agent-stack",
            "sota-multi-model-workflows",
        ),
        "upstream_platforms": ("18-pinned-upstream-shelf", "SkillOpt/GEPA", "8-slot-Multi-Model-AO"),
        "invariants": "Immutable ~/Documents/upstream/ pins (PINS.md); zero reinvention; trajectory friction mining into ~/.agents/wiki/LESSONS.md; 7-vendor cross-family adversarial review.",
        "default_command": "sota-lanes matrix --json",
    },
}


def render_domain_lane_hub_artifacts(slug: str) -> dict[str, str]:
    """Render `LANE_MANIFEST.json`, cross-OS `orca.yaml`, and `README.md` for one of the 7 Ecosystem Domain Lanes."""
    lane = ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES.get(slug)
    if lane is None:
        raise ValueError(f"Unknown domain lane slug {slug!r}; valid={sorted(ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES)}")
    manifest = {
        "schemaVersion": "sota-ecosystem-domain-lane.v1",
        "adrAuthority": ["ADR-0027", "ADR-0028", "ADR-0029"],
        "ecosystemSemver": "3.10.7",
        "singleActiveBrokerHostOnly": True,
        "rthBrokerContentionShield": True,
        "primarySovereignWorkstation": "stationary_noesis_win32 (100.110.115.22)",
        "portableCockpitAndFailover": "portable_mac_m5_max (100.93.211.101)",
        "lane": lane,
        "orcaRegisterCommands": {
            "noesis": f"orca repo add --environment 100.110.115.22 --path C:/sota-workstation/.orca-lanes/{slug} --kind folder --json",
            "mac": f"orca repo add --path ~/.agents/orca-lanes/{slug} --kind folder --json",
        },
    }
    orca_yaml = (
        f"# SOTA 7-Domain Ecosystem Orca Lane Hub — {slug} (v3.10.5, ADR-0029)\n"
        "setupAgentStartupPolicy: wait-for-setup\n"
        "scripts:\n"
        "  setup: |\n"
        f'    echo "[SOTA Orca Lane] {lane["title"]} | gating={lane["gating_policy"]} | lead={lane["lead_agent"]}"\n'
        "defaultTabs:\n"
        "  - title: Lead Agent\n"
        f"  - title: {slug} Status\n"
        f"    command: {lane['default_command']}\n"
    )
    readme = "\n".join(
        [
            f"# {lane['title']}",
            "",
            f"- **Domain:** `{lane['domain']}` | **Gating:** `{lane['gating_policy']}`",
            f"- **Primary Surface:** `{lane['primary_surface']}` | **Failover:** `{lane['failover_surface']}`",
            f"- **Lead Agent:** `{lane['lead_agent']}` | **Worker Trio:** `{', '.join(lane['worker_trio'])}`",
            f"- **Owned Repos:** `{', '.join(lane['repos'])}`",
            f"- **Upstream Platforms:** `{', '.join(lane['upstream_platforms'])}`",
            f"- **Invariants:** {lane['invariants']}",
            "",
        ]
    )
    return {
        "LANE_MANIFEST.json": json.dumps(manifest, indent=2, default=list) + "\n",
        "orca.yaml": orca_yaml,
        "README.md": readme,
    }


def sync_seven_domain_orca_lanes(hub_root: pathlib.Path | None = None) -> dict[str, Any]:
    """Materialize all 7 Full-Ecosystem Domain Lane Hubs (`01-sim-backtest` .. `07-beyond-convergence-skillopt`)."""
    target_root = hub_root or (pathlib.Path.home() / ".agents" / "orca-lanes")
    written: list[str] = []
    created_dirs: dict[str, str] = {}
    for slug in sorted(ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES):
        dest_dir = target_root / slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        created_dirs[slug] = str(dest_dir)
        for fname, content in render_domain_lane_hub_artifacts(slug).items():
            fp = dest_dir / fname
            fp.write_text(content, encoding="utf-8")
            written.append(str(fp))
    return {
        "ok": True,
        "schema_version": "sota-ecosystem-domain-lane.v1",
        "adr": "ADR-0029",
        "hub_root": str(target_root),
        "domain_lanes_count": len(ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES),
        "files_written": len(written),
        "lane_dirs": created_dirs,
    }


def sync_orca_lane_hubs(hub_root: pathlib.Path | None = None, *, include_domain_lanes: bool = False) -> dict[str, Any]:
    """Write `sota-orca-lane-hub.v2` artifacts into `<hub_root>/{trading-lanes,harness-lanes}` (+ optional 7 Domain Lanes)."""
    target_root = hub_root or (pathlib.Path.home() / ".agents" / "orca-lanes")
    written: list[str] = []
    for plane, folder_name in (("trading", "trading-lanes"), ("harness", "harness-lanes")):
        dest_dir = target_root / folder_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        for fname, content in render_orca_lane_hub_artifacts(plane).items():
            fp = dest_dir / fname
            fp.write_text(content, encoding="utf-8")
            written.append(str(fp))
    out: dict[str, Any] = {
        "ok": True,
        "hub_schema_version": ORCA_LANE_HUB_SCHEMA_VERSION,
        "hub_root": str(target_root),
        "files_written": len(written),
    }
    if include_domain_lanes:
        dom = sync_seven_domain_orca_lanes(target_root)
        out["domain_lanes_count"] = dom["domain_lanes_count"]
        out["domain_files_written"] = dom["files_written"]
        out["domain_lane_dirs"] = dom["lane_dirs"]
        out["total_files_written"] = len(written) + int(dom["files_written"])
    return out


def build_multi_repo_beads_orca_dag(
    *,
    goal: str,
    leaf_repos: tuple[str, ...] = ("meridian", "tsl", "trading-sota", "sota-mover-ranker"),
    mid_repos: tuple[str, ...] = ("cc-sota-harness", "agy-sota-harness", "sota-multi-model-workflows"),
    seal_repos: tuple[str, ...] = ("sota-private-vault", "native-agent-stack", ".github"),
    surface: str = "dual_mesh_docked",
) -> dict[str, Any]:
    """Synthesize a persistent 3-stage Beads (bd) + Orca (--deps / gate-create) multi-repo DAG (M4, ADR-0020)."""
    stages = (
        ("stage1_leaf_repos", leaf_repos, ()),
        ("stage2_harness_mid_repos", mid_repos, ("stage1_leaf_repos",)),
        ("stage3_org_umbrella_seal", seal_repos, ("stage1_leaf_repos", "stage2_harness_mid_repos")),
    )
    nodes: list[dict[str, Any]] = []
    for stage_id, repos, deps in stages:
        for repo in repos:
            if repo not in REPO_LANE_INDEX:
                raise ValueError(f"Unknown repository '{repo}' in DAG")
            route = resolve_dual_machine_lane_plan(repo, mesh_state=surface)
            task_id = f"dag-{stage_id.split('_')[0]}-{repo.replace('.', 'dot')}"
            dep_tasks = [
                f"dag-{d.split('_')[0]}-{r.replace('.', 'dot')}"
                for d in deps
                for s_id, s_repos, _ in stages
                if s_id == d
                for r in s_repos
            ]
            bd_cmd = f"bd create --title {shlex.quote(f'[{stage_id}] {repo}: {goal[:64]}')} --type task"
            orca_argv = [*route["orca_worker_start_argv"]]
            if dep_tasks:
                orca_argv.extend(["--deps", ",".join(dep_tasks)])
            nodes.append(
                {
                    "task_id": task_id,
                    "stage": stage_id,
                    "repo": repo,
                    "surface": route["selected_surface"],
                    "depends_on": dep_tasks,
                    "beads_create_cmd": bd_cmd,
                    "orca_dag_worker_argv": orca_argv,
                }
            )
    gate_cmd = [
        "orca",
        "orchestration",
        "gate-create",
        "--title",
        f"22/22 Zero-Drift Seal Gate: {goal[:48]}",
        "--deps",
        ",".join(n["task_id"] for n in nodes if n["stage"] != "stage3_org_umbrella_seal"),
    ]
    dag_sha256 = hashlib.sha256(
        json.dumps({"goal": goal, "nodes": [n["task_id"] for n in nodes]}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "sota-beads-orca-dag.v1",
        "goal": goal,
        "stages_count": 3,
        "nodes_count": len(nodes),
        "dag_sha256": dag_sha256,
        "orca_seal_gate_argv": gate_cmd,
        "nodes": nodes,
    }


def build_lanes_overview(*, plane: str = "all", mesh_state: str = "dual_mesh_docked") -> dict[str, Any]:
    """Summarize Dual-Machine surfaces, 8 frameworks, and T1..T3 / H1..H3 (+ T1..T5 / H0..H7) lane assignments."""
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
        "hub_schema_version": ORCA_LANE_HUB_SCHEMA_VERSION,
        "ranking_datafeeds_schema": RANKING_DATAFEEDS_SCHEMA_VERSION,
        "ranking_feeds_count": len(CANONICAL_RANKING_DATAFEEDS_V38),
        "prewall_lake_sha256": DEFAULT_PREWALL_LAKE_SHA256,
        "mesh_state": mesh_state,
        "surfaces": DUAL_MACHINE_SURFACES,
        "orca_lane_hubs": ORCA_LANE_HUBS,
        "frameworks_count": len(ORCHESTRATION_FRAMEWORKS_MATRIX),
        "workers_count": len(RUNTIME_WORKER_ROSTER),
        "model_vendors_count": len(CANONICAL_SEVEN_MODEL_VENDORS),
        "stage_and_layer_sublanes_count": len(STAGE_AND_LAYER_SUBLANES),
        "lane_leads_count": len(CANONICAL_ORCA_LANE_LEADS),
        "lane_leads": {k: v for k, v in CANONICAL_ORCA_LANE_LEADS.items() if plane == "all" or v["plane"] == plane},
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

    p_sh = sub.add_parser("sync-hubs", help="Materialize sota-orca-lane-hub.v2 manifests & orca.yaml in folder hubs")
    p_sh.add_argument("--root", default="", help="Override hub root directory (default: ~/.agents/orca-lanes)")
    p_sh.add_argument("--all-domains", action="store_true", help="Also materialize all 7 Ecosystem Domain Lane Hubs")
    p_sh.add_argument("--json", action="store_true")

    p_dm = sub.add_parser(
        "domains",
        help="List all 7 Full-Ecosystem Orca Domain Lanes (Sim/Paper/Live/All-Market/Incentives/Framework/Beyond)",
    )
    p_dm.add_argument("--json", action="store_true")

    p_rt = sub.add_parser("route", help="Resolve Dual-Machine surface & Orca worker-start command for a repository")
    p_rt.add_argument("--repo", required=True, choices=sorted(REPO_LANE_INDEX))
    p_rt.add_argument("--workload", default="default")
    p_rt.add_argument("--placement", default="auto", choices=("auto", "local", "noesis"))
    p_rt.add_argument("--mesh-state", default="")
    p_rt.add_argument("--active-broker-shield", action="store_true")
    p_rt.add_argument(
        "--active-broker-host",
        default="stationary_noesis_win32",
        choices=("stationary_noesis_win32", "portable_mac_m5_max"),
    )

    p_dg = sub.add_parser("dag", help="Build a 3-stage persistent Beads (bd) + Orca (--deps / gate-create) wave DAG")
    p_dg.add_argument("--goal", default="Land v3.9.8 co-op convergence wave across leaf -> harness -> umbrella seal")
    p_dg.add_argument("--json", action="store_true")

    p_mr = sub.add_parser(
        "merit",
        help="Show the 7-lane Grand Merit-Promotion Harness (2 Sim + 3 Alpaca Paper + 1 IBKR Paper + Stage-5 Live)",
    )
    p_mr.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    _trials_n, _next_t, live_mesh = _load_live_bus_and_mesh()

    if args.cmd == "merit":
        from sota_mmw.merit_promotion_harness import build_grand_merit_harness_manifest

        merit_out = build_grand_merit_harness_manifest()
        print(json.dumps(merit_out, indent=2, default=list))
        return 0 if merit_out["ok"] else 1

    if args.cmd == "dag":
        dag_out = build_multi_repo_beads_orca_dag(goal=args.goal, surface=live_mesh)
        print(json.dumps(dag_out, indent=2))
        return 0

    if args.cmd == "status":
        out = build_lanes_overview(plane=args.plane, mesh_state=live_mesh)
        print(json.dumps(out, indent=2, default=list))
        return 0 if out["ok"] else 1

    if args.cmd == "matrix":
        out_mx = {
            "schema_version": LANES_SCHEMA_VERSION,
            "frameworks_count": len(ORCHESTRATION_FRAMEWORKS_MATRIX),
            "workers_count": len(RUNTIME_WORKER_ROSTER),
            "model_vendors": list(CANONICAL_SEVEN_MODEL_VENDORS),
            "frameworks": ORCHESTRATION_FRAMEWORKS_MATRIX,
            "runtime_workers": RUNTIME_WORKER_ROSTER,
            "stage_and_layer_sublanes": STAGE_AND_LAYER_SUBLANES,
            "surfaces": DUAL_MACHINE_SURFACES,
        }
        print(json.dumps(out_mx, indent=2, default=list))
        return 0

    if args.cmd == "domains":
        dom_out = {
            "ok": True,
            "schema_version": "sota-ecosystem-domain-lane.v1",
            "adr": "ADR-0029",
            "domain_lanes_count": len(ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES),
            "primary_sovereign_host": "stationary_noesis_win32",
            "portable_cockpit_and_failover": "portable_mac_m5_max",
            "lanes": ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES,
        }
        print(json.dumps(dom_out, indent=2, default=list))
        return 0

    if args.cmd == "sync-hubs":
        root_p = pathlib.Path(args.root).expanduser() if args.root.strip() else None
        res_sh = sync_orca_lane_hubs(root_p, include_domain_lanes=bool(getattr(args, "all_domains", False)))
        print(json.dumps(res_sh, indent=2))
        return 0

    eff_mesh = args.mesh_state.strip() if getattr(args, "mesh_state", "") else live_mesh
    try:
        plan = resolve_dual_machine_lane_plan(
            args.repo,
            workload=args.workload,
            mesh_state=eff_mesh,
            requested_placement=args.placement,
            active_broker_host_shield=bool(getattr(args, "active_broker_shield", False)),
            active_broker_host=str(getattr(args, "active_broker_host", "stationary_noesis_win32")),
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
