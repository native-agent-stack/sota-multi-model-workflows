# ADR-0027: Grand Merit-Promotion Harness (`S1/S2` Sim -> `3` Alpaca Paper + `1` IBKR Paper -> Stage-5 Lossless Live) & Native Gemini-to-Orca Grand Orchestration

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** `L0..L13` x `T1..T5` x `H0..H7` (End-to-End Merit-Promotion Execution & Multi-Model Orca Control Plane)
- **Evidence Grade:** `E4` (Unit Suite, `20/20` Canonical Workflows AST & Runtime Verified, `3` Distinct Alpaca Paper Accounts + `1` IBKR `:4002` + `:8798` Stage-5 Lossless Live Lane Live-Probed, `merge_gate.py` & `gitleaks` `0` Leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-mover-ranker, https://github.com/native-agent-stack/sota-dynamic-trail-c, https://github.com/alpacahq/alpaca-mcp-server, https://github.com/nautechsystems/nautilus_trader, https://github.com/nkaz001/hftbacktest, https://github.com/stablyai/orca
- **Revisit Trigger:** Revisit after 45 days (`2027-01-02`), upon post-Dec-6 23/5 SIP cutover, or whenever Multi-Paper merit thresholds or Alpaca/IBKR account topologies change.

## Context and Problem Statement

Previous releases separated pre-wall backtesting (`T3`), event-driven simulation (`T2`), single-account paper trading (`T1`), and Stage-5 live execution protection (`ADR-0030` in `sota-mover-ranker`). To compound strategies cleanly from research into autonomous real-capital execution without manual bottlenecks or unverified risk, the harness must codify a deterministic **Merit-Promotion Ladder**:

1. **Simulation & Backtest Lanes (`S1`, `S2`) are NEVER GATED** — running continuously on `Noesis Win32` (`64c/128GB/RTX4090`) and `Noesis-Carbon WSL2` (`NautilusTrader v2.0.0rc9` / `hftbacktest` `RiskAdverseQueueModel`, roaming failover `Mac M5 Max`).
2. **All Four Paper Farm Accounts (`3` Distinct Alpaca Paper + `1` IBKR Paper) are NEVER GATED** — running distinct handbooks, strategy classes, and aggressiveness bands concurrently on Sovereign `portable_mac_m5_max`, all inheriting the shared **Lossless Foundation** (`ADR-0022 <= 2.00%` stop + `ADR-0024` lossless floor/runner ratchet):
   - **`PAPER_P1_ALPACA_LOSSLESS_FOUNDATION` (`Account C`, `canon-alpaca-paper-protect`, `:8799`, `sota-dynamic-trail-c`):** Conservative Lossless Foundation Anchor & Live Mirror (`1.0x–2.0x` gross, `<= 1.00%` mega-cap stop, `5–10 bps` scratch, 24x5 Guardian). Directly seeds Live Day-0 Lossless Foundation.
   - **`PAPER_P2_ALPACA_BALANCED_RANKER` (`Account B`, `canon-alpaca-paper-windows`, `:8787`, `sota-mover-ranker`):** Balanced Whole-Market Compounding Core (`2.0x–3.0x` gross, `Funnel X1/X2/IPO`, Empirical-Bayes continuous tuning, `1,000 req/min` burst).
   - **`PAPER_P3_ALPACA_AGGRESSIVE_LAB` (`Account A`, `trading-sota-alpaca`, `:8797`, `sota-mover-ranker` + `trading-sota` + `tsl`):** Aggressive High-Velocity Frontier Crucible (`3.0x–4.0x` intraday Reg-T gross, `ADR-0022 <= 2.00%` hard ceiling, newly Sim-cleared strategies, `Dual-Phase SAR`, `PEAD`/`EP`/`Burst`, rapid `Wave-2` cycling).
   - **`PAPER_P4_IBKR_INSTITUTIONAL_4002` (`Account D`, `127.0.0.1:4002`, `DU...`, `3,000 req/min`, `astrolabe` + `meridian`):** Institutional Cross-Broker Parity, native `outsideRth` stops, and `3,000 req/min` overflow routing.
3. **Stage-5 Lossless Live (`LIVE_L5_STAGE5_LOSSLESS`, `:8798`) is NEVER GATED FOR PROVEN AUTOMATION, ONLY MERIT-PROVEN & LOSSLESS-PROTECTED:**
   - Starts immediately on Day-0 with the **Lossless Foundation** (`P1` mirror + `ADR-0022 <= 2.00%` atomic stop / `:8799` guardian + `1,000 req/min` with `100/min` strict exit reserve + `ADR-0024` lossless runner floor + `-1.50%` daily drawdown breaker + zero PII/USD telemetry).
   - Automatically graduates strategies from `S1/S2 -> P3 (Aggressive) -> P2 (Balanced) -> P1/P4 (Lossless Mirror & Institutional Parity) -> L5 (1.00x Full Automated Live)` via deterministic merit thresholds (`n_closed >= 30`, `>= 2` paper accounts incl. `P1`, `eb_expectancy_r >= +0.20R`, `PF >= 1.35`, `slip <= +3.0 bps`, `0` `ADR-0022` breaches).

## Decision Outcome

- Add `src/sota_mmw/merit_promotion_harness.py` defining `GRAND_MERIT_EXECUTION_LANES` (`7` lanes: `2` Sim + `4` Paper + `1` Stage-5 Lossless Live), `MeritStrategyEvidence`, IEEE-754 fail-closed `evaluate_merit_ladder()`, and `build_grand_merit_harness_manifest()`.
- Expose `sota-lanes merit --json` in `src/sota_mmw/dual_machine_lanes.py`.
- Register **Workflow #20 (`grand-merit-harness`)** in `workflows/grand_merit_harness_workflow.py`, `workflows/REGISTRY.json`, `SOTA_WORKFLOW_MANIFEST.json`, and `src/sota_mmw/native_workflow_enactor.py` bridging Antigravity Native Gemini models directly into Dual-Machine Orca Grand Orchestration.

## Alternatives Considered

- **Single monolithic Paper account mixing aggressive experimental alpha with lossless live-mirror baselines:** Rejected because aggressive frontier experimentation contaminates the live-mirror Empirical-Bayes track record and blurs merit attribution.
- **Manual per-trade approval on Sim/Paper or on already merit-proven Live strategies:** Rejected because Sim and Paper must compound unthrottled (`NEVER_GATED`), while Live must automate cleanly once proven on the Lossless Foundation.

## Verification Witness

- `python3 scripts/architecture_catalog.py --check` (`27/27` sequential MADR 4.0 ADRs, `0` drift).
- `pytest -q` (`test_v3103_adr0027_grand_merit_promotion_harness_and_wf20` + full suite verifying `20/20` workflows, `7` merit lanes, NaN/Inf fail-closed checks, probation blocking, Day-0 Lossless Foundation canary, `1.00x` full Live graduation, and `sota-lanes merit --json`).
- `ruff check .`, `ty check`, `python3 scripts/merge_gate.py`, and `gitleaks git --no-banner` (`0` diagnostics, `0` leaks).
