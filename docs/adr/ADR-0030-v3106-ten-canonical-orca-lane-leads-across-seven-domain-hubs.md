# ADR-0030: `v3.10.6` Complete `10`-Lead Multi-Model Orca Coverage Across All `7/7` Ecosystem Domain Hubs & Pre-IPO `2026-11-19` Grand Run

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Orca Runtime Workers, Full-Ecosystem `7/7` Domain Lead Roster & Pre-IPO Orchestration (`L7` × `P0–P5` × `T0–T8`)
- **Evidence Grade:** E4 (`10/10` Canonical Orca Lane Leads across `7/7` Domain Hubs, `8` Live Nested Worktrees on Stationary `Noesis`, Live Multi-Model Orca Run `run_5c51382bc888`, `28/28 pytest`, `0` Leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/native-agent-stack, https://github.com/native-agent-stack/.github, https://github.com/stablyai/orca
- **Revisit Trigger:** `2026-12-06` `23/5` Consolidated SIP cutover or `v4.0.0` promotion

## Context and Problem Statement

`ADR-0029` manifested all `7` Full-Ecosystem Orca Domain Hubs (`01-sim-backtest` through `07-beyond-convergence-skillopt`) on both Stationary `Noesis` and Portable `Mac`, and commit `938decb2` added `7` canonical named leads (`T1`, `T2`, `T3`, read-only `T5`, `H1`, `H2`, `H3`) leaving Domain Hubs `04-research-all-market`, `05-non-market-incentives`, and `07-beyond-convergence-skillopt` without dedicated named leads in `CANONICAL_ORCA_LANE_LEADS` or nested worktrees on `Noesis`.

## Decision Outcome

- Extend `CANONICAL_ORCA_LANE_LEADS` from `7` to `10` named multi-model leads by adding:
  - `D4_all_market_research_lead` (`d4-all-market-research-lead`, `canon`, `claude-fable-5-2`) nested under `04-research-all-market`
  - `D5_non_market_incentives_lead` (`d5-non-market-incentives-lead`, `sota-mover-ranker`, `claude-sonnet-5-5`, strictly read-only `broker_credentials=False`, `order_write_path=False`) nested under `05-non-market-incentives`
  - `D7_beyond_skillopt_lead` (`d7-beyond-skillopt-lead`, `sota-upstream-shelf-lock`, `gpt-6.2-astra`) nested under `07-beyond-convergence-skillopt`
- Preserve strict read-only isolation on `T5_stage5_live_lane_read_only_audit` and `D5_non_market_incentives_lead`, and symmetric `SINGLE_BROKER_HOST_FIREWALL` governance.

## Alternatives Considered

- **Leaving Domains `04`, `05`, and `07` as unstaffed folder hubs without named leads in `CANONICAL_ORCA_LANE_LEADS`:** Rejected because pre-IPO `2026-11-19` readiness requires explicit multi-model ownership for All-Market `DF1..DF12` research, SEC EDGAR / `NASDAQ:ANT` `\$83.00` IPO incentives, and Upstream Shelf / SkillOpt evolution.

## Verification Witness

- `uv run python scripts/architecture_catalog.py --write && --check` (`30/30` MADR 4.0 ADRs, `0` drift).
- `uv run pytest -q && ruff check . && ty check && python3 scripts/merge_gate.py && gitleaks git --no-banner` (`PASS`, `0` leaks).
