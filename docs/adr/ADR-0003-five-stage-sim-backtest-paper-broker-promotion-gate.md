# ADR-0003: Deterministic Five-Stage Strategy Promotion Gate (`Sim -> Backtest -> Paper -> Fine-Tune -> Broker`)

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** Quant & Execution Governance (`L8` × `T3–T6`)
- **Evidence Grade:** E4 (Unit & Property Tested)
- **GitHub Evidence:** https://github.com/nautechsystems/nautilus_trader, https://github.com/skfolio/skfolio, https://github.com/ml4t/diagnostic
- **Revisit Trigger:** 2027-01-01

## Context and Problem Statement

Strategy candidates must pass objective statistical and simulation gates before autonomous paper allocation on Alpaca or IBKR.

## Decision Outcome

1. **Executable `evaluate_promotion_gate`:** Require `study_end_date <= 2026-10-15`, `events >= 200`, `dates >= 60`, `t_stat >= HLZ t*(N)`, `DSR >= 0.95`, `CPCV >= 70%`, `2x` impact survival, and verified simulation parity before `STAGE_4_PAPER_EXECUTION_APPROVED`.

## Alternatives Considered

1. **Manual checklist sign-off:** Rejected — non-deterministic and susceptible to multiple-testing drift.

## Verification Witness

- `python3 -m unittest discover -s tests -v` -> `PASS`
