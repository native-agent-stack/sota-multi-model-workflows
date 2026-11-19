# ADR-0028: `v3.10.4` Stationary Workstation (`Noesis`) Primary Always-On `24/5` Host for Main Framework Foundation & Trading Engine; Portable Mac Cockpit & Hot Failover

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** `L0..L13` x `T1..T5` x `H0..H7` (Stationary Workstation Primary Hosting & Symmetric Single-Broker-Host Firewall)
- **Evidence Grade:** `E4` (`28/28` ADRs, `pytest`, `ruff`, `ty`, `merge_gate.py`, `sota-lanes merit --json` & `WF20` verified, `gitleaks` `0` Leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/sota-mover-ranker, https://github.com/native-agent-stack/sota-dynamic-trail-c, https://github.com/stablyai/orca
- **Revisit Trigger:** `2026-12-06` `23/5` Consolidated SIP cutover or addition of a dedicated cloud colocation host.

## Context and Problem Statement

`ADR-0020` and `ADR-0027` pinned the `4`-account Paper Farm (`:8799/:8787/:8797/:4002`), Stage-5 Live Lane (`:8798`), and `H1`–`H3` Framework Hub to `portable_mac_m5_max`. Because the MacBook Pro M5 Max is a portable laptop (lid sleep, Wi-Fi handoffs, travel), anchoring the always-on `24/5` Main Framework Foundation and Trading Engine on a portable machine degrades uptime and causes IBKR `COMPETE` session collisions with stationary `Noesis`.

## Decision Outcome

1. **Promote Stationary Workstation `Noesis` (`stationary_noesis_win32`, `100.110.115.22`, 64c/128GB/RTX4090 + `Noesis-Carbon` WSL2) as Primary `24/5` Host:**
   - All `7` merit execution lanes (`S1`, `S2`, `P1:8799`, `P2:8787`, `P3:8797`, `P4:4002`, `L5:8798`) and Main Framework Foundation lanes (`H1`–`H3`) set `primary_surface = "stationary_noesis_win32"` (or `stationary_noesis_carbon_wsl2` for POSIX simulation/verifiers) and `failover_surface = "portable_mac_m5_max"`.
2. **Symmetric `SINGLE_BROKER_HOST_FIREWALL` (`<= 1` Active Broker Host):**
   - `resolve_dual_machine_lane_plan(..., active_broker_host="stationary_noesis_win32")` routes active broker workloads to `Noesis` while mesh is online and blocks simultaneous local Mac broker routing (`PermissionError`).
   - Explicit failover (`active_broker_host="portable_mac_m5_max"`, or offline roaming mesh) routes seamlessly to `portable_mac_m5_max` while blocking simultaneous Noesis broker routing.

## Alternatives Considered

- **Allowing active broker daemons on both Mac and Noesis simultaneously:** Rejected — violates `singleActiveBrokerHostOnly=True`, causes duplicate orders, and triggers IBKR `COMPETE` disconnects.

## Verification Witness

- `python3 scripts/architecture_catalog.py --write && python3 scripts/architecture_catalog.py --check` (`28/28` ADRs, `0` drift).
- `pytest -q`, `ruff check .`, `ty check`, `python3 scripts/merge_gate.py`, and `gitleaks detect --source . --no-git --no-banner` (`PASS`, `0` leaks).
