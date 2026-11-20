# ADR-0036: `v3.11.1` Post-ANT Whole-Market Merit Promotion & Universal Lossless Strategy Consolidation

- **Status:** Accepted
- **Date:** 2026-11-20
- **Layer:** Multi-Model Grand Merit Harness (`L7`), `DF1..DF12` Target Admission & `ADR-0064` Strategy Quarantine (`PROTECTIVE_FILTER_OR_GOVERNANCE`, `standalone_alpha_claim = False`)
- **Evidence Grade:** E4
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-mover-ranker, https://github.com/native-agent-stack/sota-dynamic-trail-c, https://github.com/native-agent-stack/astrolabe, https://github.com/native-agent-stack/sota-compounding-lab
- **Revisit Trigger:** `2026-12-06` `21:00 ET` `23/5` Consolidated SIP cutover or pre-registration of `Trial #105` (`t*(105) = 4.2084`).

## Context and Problem Statement

With the completion of the `NASDAQ:ANT` IPO debut era, `src/sota_mmw/merit_promotion_harness.py` needed consolidation with the `v3.11.0`/`v3.11.1` lossless foundation: blocking `ADR-0064`-quarantined negative-expectancy/noisy strategies from Stage-5 Live or active Paper promotion, admitting the `6` proven SOTA strategy families, and exposing a symbol-agnostic Post-ANT whole-market target merit admission gate (`evaluate_post_ant_symbol_merit_admission`) aligned with `sota.active-market-targets.v1` and `sota.strategy-contract.v2`.

## Decision Outcome

1. **Quarantine Firewall in `evaluate_merit_ladder()`:** Unconditionally block `POST_ANT_QUARANTINED_STRATEGIES` (`SOTA_DUAL_CLIMAX_STOP_AND_REVERSE`, `POST_VIX_REVERSAL`, `SOTA_DUAL_EXTREME_BALANCE_BREAK_EARLY`, `BLIND_WAVE2_REENTRY`, `RAPID_WAVE2_REENTRY_STRESS`, `FLOW_VELOCITY_CAPITAL_RECYCLE`) from active Paper/Live promotion while admitting `POST_ANT_CONCENTRATED_SOTA_STRATEGIES` into lossless canary evaluation when pre-wall `2x` net expectancy is positive.
2. **Symbol-Agnostic Whole-Market Admission (`evaluate_post_ant_symbol_merit_admission`):** Admit ANY US symbol with `>= 3` manifested `DF1..DF12` pillars, clean 90-day SEC dilution shield, `spread_bps <= 35.0`, and `ADR-0022 <= 2.00%` uncapped lossless stop (`TP OFF`) into `MERIT_TIER_1_CORE` (`P1–P4`) or `MERIT_TIER_2_ACTIVE` (`P2–P4`) under `PROTECTIVE_FILTER_OR_GOVERNANCE` (`standalone_alpha_claim = False`).
3. **Manifest Parity (`build_grand_merit_harness_manifest`):** Publish `era = "POST_ANT_WHOLE_MARKET_MERIT"`, `ecosystem_version = "3.11.1"`, `active_market_targets_schema = "sota.active-market-targets.v1"`, and `strategy_contract_schema = "sota.strategy-contract.v2"` alongside backward-compatible `ADR-0028` lane fields.

## Alternatives Considered

- **Leaving `ADR-0064` Quarantine Local to `sota-mover-ranker`:** Rejected because the org-wide Grand Merit Harness must enforce identical quarantine & whole-market merit invariants across all 4 Paper lanes and Stage-5 Live.

## Verification Witness

- `ruff check . && ruff format --check . && ty check src tests` (`PASS`), `scripts/architecture_catalog.py --check` (`36/36` ADRs, `0` drift), `uv run pytest -q` (incl. `tests/test_v3111_post_ant_merit_mmw.py` `PASS`), `scripts/merge_gate.py` (`PASS`), `gitleaks --staged` (`0` leaks).
