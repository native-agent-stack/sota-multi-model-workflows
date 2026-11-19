# ADR-0031: `v3.10.6` `America/New_York` Overnight `BOATS` `decision_ns` Session-Date Parity, Strict Route-to-Port Binding & `5 bps` Minimum Stop Floor

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** `L2` × `L5` × `L8` (`DF1..DF12` Bitemporal PIT Contract & Single-Broker-Lane Firewall)
- **Evidence Grade:** `E4` (`src/sota_mmw/symbol_ranking_datafeeds.py`, `tests/test_mmw_suite.py`, `31/31` MADR 4.0 ADRs, `ruff`, `merge_gate.py`, `gitleaks` `0` leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/native-agent-stack/meridian
- **Revisit Trigger:** `2026-12-06` `23/5` Consolidated SIP cutover or addition of new paper broker lanes

## Context and Problem Statement

Adversarial E2E review (`cc-lead-e2e-review` `#108`) identified four remaining precision edge cases in `evaluate_symbol_ranking_to_strategy_handoff()` (`ADR-0026`):
1. **UTC Rollover False Rejection on Overnight `BOATS` (`20:00–23:59 ET`):** Converting `decision_ns / 1_000_000_000` (float division) in `dt.UTC` caused valid `2026-10-15 21:30 EDT` (`2026-10-16T01:30:00Z`) pre-wall `BOATS_23X5_OVERNIGHT_CONTINUATION` decisions to fail as `2026-10-16 > 2026-10-15`, while huge integer inputs could trigger float conversion `OverflowError`.
2. **Unbound Route-to-Port Check:** `broker_port` checked only membership in `(8787, 8799, 4002)` without enforcing `route["paper_broker_lane"]`, allowing an IBKR `:4002` route (`BOATS_23X5_OVERNIGHT_CONTINUATION`) to approve on Alpaca port `8787` (and vice versa).
3. **Sub-Tick Zero-Stop Degeneracy:** Checking `0.0 < hard_stop_pct <= 2.00` accepted physically impossible stops like `1e-12%`.
4. **Cross-Repo `DF10..DF12` Feed Key Casing Drift:** `sota-compounding-lab` stored uppercase `DF10_OWN_HISTORY_...` while `sota-multi-model-workflows` and `meridian` used lowercase suffixes.

## Decision Outcome

1. **Exact Integer `decision_ns // 1_000_000_000` + Cross-OS `America/New_York` (`_to_ny_datetime`):** Convert epoch nanoseconds using integer floor division and evaluate session date in `America/New_York` (using IANA `ZoneInfo("America/New_York")` with an exact pure-stdlib US Energy Policy Act 2005 DST fallback so bare Windows hosts without `tzdata` never fail). Valid `20:00–23:59 ET` pre-wall `BOATS` timestamps approve cleanly; `>= 2026-10-16 00:00:00 ET` and overflowed integers (`10**400`) fail closed.
2. **Strict Route-to-Port Binding (`_allowed_ports_for_route`):** `IBKR_PAPER*` routes permit ONLY `:4002`; `ALPACA_PAPER*` routes permit ONLY `(:8787, :8799, :8797)`. Mismatches emit `ROUTE_BROKER_PORT_MISMATCH`.
3. **Realistic Minimum Stop Floor (`MIN_HARD_STOP_PCT = 0.05%` / `5.0 bps`):** Require `0.05 <= hard_stop_pct <= min(route_max, 2.00)` (matching `sota-compounding-lab` and `sota-mover-ranker` `Stage-5` parity).
4. **Cross-Repo Feed Normalization (`normalize_ranking_feed_id`):** Deterministically resolve `DF1..DF12` feed keys regardless of uppercase/lowercase suffix casing.

## Alternatives Considered

- **Keeping UTC date comparisons for US equity overnight sessions:** Rejected — breaks valid `20:00–23:59 ET` `BOATS` / `23/5` SIP study-wall boundaries.

## Verification Witness

- `python scripts/architecture_catalog.py --sync-manifest && --check` (`31/31` ADRs, `0` drift), `ruff check`, `ruff format --check`, `python -m unittest discover -s tests`, `scripts/merge_gate.py`, and `gitleaks` (`0` leaks).
