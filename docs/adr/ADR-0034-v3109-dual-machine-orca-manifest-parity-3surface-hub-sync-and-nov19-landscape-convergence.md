# ADR-0034: `v3.10.9` Dual-Machine Orca Manifest Parity, 3-Surface Lane Hubs & Nov 19 Landscape Convergence

- **Status:** Accepted
- **Date:** 2026-11-19
- **Layer:** Dual-Machine Orca Manifests (`Win32` / `Noesis-Carbon WSL2` / `Mac M5 Max`), 9 Folder Lane Hubs (`sota-orca-lane-hub.v2`) & Nov 19 Upstream Landscape Sync (`L0–L13` × `P0–P5` × `T1–T5` × `H0–H7`)
- **Evidence Grade:** E4 (`test_v3109_adr0034_post_cutover_dual_machine_orca_manifests_and_3surface_hubs`, `34` GitHub-Evidenced ADRs, `21` Canonical Workflows, `9/9` Cross-Surface Orca Lane Hubs, `pytest` + `ruff` + `merge_gate.py` + `gitleaks` `0` Leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/native-agent-stack, https://github.com/stablyai/orca, https://github.com/anthropics/claude-code, https://github.com/can1357/oh-my-pi, https://github.com/code-yeongyu/oh-my-openagent
- **Revisit Trigger:** Orca supervisor upgrade from `1.4.263` -> `1.4.264+` or changes to dual-machine broker host topology.

## Context and Problem Statement

An ecosystem-wide landscape and Orca manifest audit on `2026-11-19` surfaced four concrete drifts in `dual_machine_lanes.py` and workspace `orca.yaml` files:
1. `render_orca_lane_hub_artifacts` still emitted an obsolete `activePreCutoverBrokerSplit` pointing `:8787/:8799/:8797` to `portable_mac_m5_max` despite `ADR-0041` completing the sovereign single-host cutover onto `stationary_noesis_win32`, and omitted the `stationary_noesis_wsl_carbon` (`Noesis-Carbon (WSL)`) hub selector and RTX 4090 `:8794` CUDA sidecar.
2. Domain lanes `05-non-market-incentives` and `06-framework-and-harness` still referenced `antigravity-carbon` and `17/17 sota-doctor` instead of `antigravity-neon` and `18/18 sota-doctor`, while root `orca.yaml` tabs still labeled `57-Skill` / `20-Workflow`.
3. Upstream orchestration tools shipped new `2026-11-19` releases (`stablyai/orca v1.4.264` available vs `1.4.263` active, `claude-code v2.1.328` live, `agy 1.5.12` live, plus `oh-my-pi v19.0.0`, `oh-my-openagent v5.1.79`, `codex v0.170.0`, `oh-my-codex v0.22.11`).

## Decision Outcome

1. **Replace `activePreCutoverBrokerSplit` with `activeSovereignBrokerTopology` & Add `stationary_noesis_wsl_carbon`:** Align `ORCA_LANE_HUBS`, `render_orca_lane_hub_artifacts`, and `render_domain_lane_hub_artifacts` (`v3.10.9`) across all 3 workstation surfaces (`stationary_noesis_win32`, `stationary_noesis_wsl_carbon`, `portable_mac_m5_max`), reflecting sovereign Noesis `:8787/:8799/:8797/:4002/:8792/:8798/:8796` + `:8794` RTX 4090 CUDA sidecar and parked Mac failover (`MAC_BROKER_PORTS=0`).
2. **Converge `ORCHESTRATION_FRAMEWORKS_MATRIX`, `ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES` & `orca.yaml`:** Record live `claude 2.1.328`, `agy 1.5.12`, `orca 1.4.263` (and `1.4.264` evaluated), route Lanes `05`/`06` through `antigravity-neon`, update Lane `06` invariants to `18/18 sota-doctor`, and align `orca.yaml`, `REGISTRY.json`, and `SOTA_WORKFLOW_MANIFEST.json` to `v3.10.9`.

## Alternatives Considered

- **Leave `activePreCutoverBrokerSplit` in Generated `LANE_MANIFEST.json`:** Rejected — misrepresents active broker ownership after `ADR-0041` cutover and omits `Noesis-Carbon (WSL)` and `:8794` CUDA topology.

## Verification Witness

- `uv run python scripts/architecture_catalog.py --sync-manifest` & `--check` (`34` ADRs, `0` drift), `uv run python scripts/merge_gate.py`, `uv run ruff format --check .`, `uv run ruff check .`, `uv run pytest -v`, and `gitleaks git --staged --verbose` (`0` leaks).
