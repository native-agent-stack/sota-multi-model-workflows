# ADR-0029: `v3.10.5` Full-Ecosystem 7-Domain Orca Lane Hub Manifestation (`Sim`, `Paper`, `Live`, `All-Market Research`, `Non-Market Incentives`, `Framework/Harness` & `Beyond/SkillOpt`)

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** `L0..L13` x `T1..T5` x `H0..H7` (Full-Ecosystem Orca Folder-Hub Manifestation & Lead-Agent Topology)
- **Evidence Grade:** `E4` (`29/29` ADRs, `pytest`, `ruff`, `merge_gate.py`, `sota-lanes domains --json`, `sota-lanes sync-hubs --all-domains`, live Orca `--kind folder` registration across Mac + Noesis `100.110.115.22`, `gitleaks` `0` Leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/sota-mover-ranker, https://github.com/stablyai/orca
- **Revisit Trigger:** `2026-12-06` `23/5` Consolidated SIP cutover or addition of new asset-class / non-market catalyst domains.

## Context and Problem Statement

Earlier releases manifested only two coarse Orca folder hubs (`trading-lanes` and `harness-lanes`). Operating a full multi-market, non-market-incentive, simulation, 4-account paper, Stage-5 lossless live, main-framework, and SkillOpt convergence ecosystem cleanly inside Orca Desktop (`Noesis 100.110.115.22` primary + `Mac` portable cockpit) requires each operational domain to be materialized as its own clickable, supervised Orca `--kind folder` hub with dedicated `orca.yaml`, `LANE_MANIFEST.json`, `README.md`, Lead Agent, Worker Trio, and Gating Policy.

## Decision Outcome

1. **Define `ECOSYSTEM_SEVEN_ORCA_DOMAIN_LANES` in `src/sota_mmw/dual_machine_lanes.py`:**
   - `01-sim-backtest` (`NEVER_GATED`, `S1` Win32 64c/RTX4090 + `S2` WSL2 `Nautilus`/`hftbacktest`)
   - `02-paper-4acct-farm` (`NEVER_GATED`, `P1:8799`, `P2:8787`, `P3:8797` Alpaca + `P4:4002` IBKR)
   - `03-stage5-lossless-live` (`PROVEN_AUTOMATION_ONLY_STARTING_WITH_LOSSLESS_FOUNDATION`, `:8798` RTH Atomic + `:8796` Dedicated Live Guardian)
   - `04-research-all-market` (`NEVER_GATED`, Equities/ETFs/Options/VIX/FX/Crypto/Futures/IPOs + `DF1..DF12` PIT Lake)
   - `05-non-market-incentives` (`NEVER_GATED`, SEC EDGAR `8-K`/`S-1`/`424B4`/`424B5`/`13F`/`Form 4`, FDA/PDUFA, Patents, Gov/DoD, Fed/Macro)
   - `06-framework-and-harness` (`CONTINUOUS_CI_GATED`, Stationary `Noesis` Primary Framework Foundation & `20`-workflow hub)
   - `07-beyond-convergence-skillopt` (`NEVER_GATED_RESEARCH_TO_CI_PROMOTION`, 18-repo upstream shelf, SkillOpt/GEPA self-evolution & 7-vendor AO)
2. **Add `render_domain_lane_hub_artifacts()`, `sync_seven_domain_orca_lanes()`, `sota-lanes domains --json`, and `sota-lanes sync-hubs --all-domains`:** preserves backward compatibility for `trading-lanes` + `harness-lanes` (`6` files) while materializing all `7` Domain Lane Hubs (`21` files) ready for `orca repo add --kind folder` on both Stationary `Noesis` and Portable `Mac`.

## Alternatives Considered

- **Keeping all trading, research, non-market incentives, and live protection crammed inside two folders:** Rejected — loses clear Lead Agent ownership, gating isolation (`NEVER_GATED` vs `PROVEN_AUTOMATION_ONLY`), and Source Control clarity in Orca Desktop.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && --check` (`29/29` ADRs, `0` drift), `ruff check .`, `pytest -q`, `scripts/merge_gate.py`, and `gitleaks` (`0` leaks).
