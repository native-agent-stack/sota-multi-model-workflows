# ADR-0014: Dual-Machine Orca Trading Lanes (`T1–T3`), Harness Lanes (`H1–H3`) & 8-Framework Orchestration Matrix

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Dual-Machine Multi-Model Orchestration, Execution Placement & Broker Firewall (`L0–L11` × `T0–T8`)
- **Evidence Grade:** E4 (Unit Tested, Live Orca `--help` / Folder-Hub Verified & Public GitHub Actions Verified)
- **GitHub Evidence:** https://github.com/stablyai/orca, https://github.com/Yeachan-Heo/oh-my-claudecode, https://github.com/Yeachan-Heo/oh-my-codex, https://github.com/code-yeongyu/oh-my-openagent, https://github.com/can1357/oh-my-pi, https://github.com/steveyegge/beads, https://github.com/native-agent-stack/sota-multi-model-workflows
- **Revisit Trigger:** Enrollment of a 3rd paired workstation surface or change to `ADR-0020` `singleActiveBrokerHostOnly` broker sovereignty

## Context and Problem Statement

Across our symmetric `:6770` Tailscale Orca mesh (`Apple M5 Max` `100.93.211.101` <-> `Stationary Noesis` `100.110.115.22` `64c`/`128GB`/`RTX 4090` Win32 + `Noesis-Carbon` WSL2 `ext4`), all 18 `native-agent-stack` repositories are provisioned on both machines alongside 8 SOTA multi-model orchestration frameworks (`Orca`, `Claude OMC v2`, `Codex OMX`, `Antigravity 15-Workflow + Swarm`, `OpenCode OMO Hephaestus`, `Pi/OMP @worker`, `Goose/DSH`, and `sota-bus + hcom + bd + omniroute`). Two concrete CLI & boundary risks required deterministic code enforcement:
1. `orca orchestration worker-start` routes remote child worktrees under a local coordinator `Run` via `--on 100.110.115.22` (never `--environment 100.110.115.22` or `--environment local`), and `omp` supports `--model @worker --effort high` whereas `opencode` forbids `--effort` and requires existing worktrees for `--model`.
2. Active paper-broker sockets (`:8787`, `:8799`, `:4002`) must remain 100% sovereign on `portable_mac_m5_max` (`singleActiveBrokerHostOnly = True`) while heavy `<= 2026-10-15` `CPCV`/`DSR`/`RTX 4090` sweeps (`T3`) and `NautilusTrader` / `RiskAdverseQueueModel` POSIX simulations (`T2`) offload to `Noesis` / `Noesis-Carbon` when docked and fail over cleanly to `Mac M5 Max` when roaming.

## Decision Outcome

1. **Dual-Machine Lanes Engine & `sota-lanes` CLI (`src/sota_mmw/dual_machine_lanes.py`):**
   - Codifies `ORCHESTRATION_FRAMEWORKS_MATRIX` (`8` frameworks), `DUAL_MACHINE_SURFACES` (`3` surfaces), `ORCA_LANE_HUBS` (live `--kind folder` UUIDs on both Mac and Noesis for `--parent-worktree folder:<id>`), `TRADING_LANES` (`T1..T3` across `8` repos), and `HARNESS_LANES` (`H1..H3` across `10` repos).
   - `resolve_dual_machine_lane_plan()` hard-refuses (`PermissionError: SINGLE_BROKER_HOST_FIREWALL`) any `noesis` placement request for `active_paper_broker` / `T1`, emits verified `orca orchestration worker-start --on 100.110.115.22 --worktree new-child --repo id:<uuid> --setup run` commands, and enforces `>= 3` concrete model vendors + `sota-research-feeds.v2` (`ADR-0004`, `PHILOSOPHY_ONLY`).
2. **`cc_lead_hub.py` (`v2.0`) & `orca.yaml` Cross-OS Recipe:**
   - Fixes `build_cc_lead_execution_plan()` to use `--on 100.110.115.22` (omitting `--on` when local), expands `RUNTIME_WORKER_ROSTER` (`9 -> 11` workers with `pi-omp-worker` `@worker` and `goose-autonomous`), expands `probe_cc_runtime_fleet()` to `17` binaries (`+agy`, `+bd`), checks TCC-safe `~/sota-dynamic-trail-c`, adds `sota-cc-hub lanes`, and ships root `orca.yaml` (`setupAgentStartupPolicy: wait-for-setup`).
3. **Self-Bootstrapping Workflow `#15` (`dual-machine-trading-and-harness-lanes`, `v3.7.0`):**
   - Adds `workflows/dual_machine_trading_and_harness_lanes_workflow.py` (`15/15` workflows verified with `verify_workflow_research_convergence()` and `<workflow>` `__file__` guards).

## Alternatives Considered

1. **Allowing active paper-broker daemons on both Mac and Noesis simultaneously:** Rejected (`ADR-0020`) — dual active writers create duplicate `sota-*` order IDs and cancel-race hazards on `PA...` / `DU... :4002`.
2. **Passing `--environment` to `orca orchestration worker-start`:** Rejected — verified against `orca orchestration worker-start --help` (`1.4.255`/`1.4.261`), which uses `--on <server>` so the `Run` remains anchored on the coordinator server.

## Verification Witness

- `python3 scripts/architecture_catalog.py --check` -> `14 GitHub-evidenced MADR 4.0 ADRs & manifest verified (0 drift)`
- `python3 scripts/merge_gate.py` & `python3 -m unittest discover -s tests -v` -> `PASS`
