# ADR-0026: `v3.10.2` IEEE-754 `NaN`/`Inf` Fail-Closed Handoff Gate, Bitemporal `decision_ns` Study-Wall Enforcement & 12-Feed Key Bijection

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Quantitative Dimensional/FP Safety, Bitemporal PIT Study Wall & 12-Feed (`DF1..DF12`) Schema Integrity (`L6..L8` x `T1..T5`)
- **Evidence Grade:** E4 (`noesis-cc-lead` `#92` Adversarial Defects `A..E` 100% Remediated & Regression-Tested, `24/24` Unit Suite, `ruff`, `merge_gate.py`, `gitleaks` `0` Leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/trailofbits/skills, https://github.com/databento/databento-python
- **Revisit Trigger:** `2026-12-06` `23/5` Consolidated SIP cutover or addition of a `13th` canonical feed

## Context and Problem Statement

Adversarial source-and-call verification by `noesis-cc-lead` (`claude-fable-5-2` `xhigh`, Peer Message `#92`) uncovered five concrete defects in `ADR-0024` (`symbol_ranking_datafeeds.py`, `cc_lead_hub.py`, and Workflow `#19`):
1. **IEEE-754 `NaN`/`+-Inf` Fail-Open (`Defect A`):** Direct `<` / `>` comparisons evaluated to `False` under `float('nan')` or `+inf`, approving failed-join candidates across `rvol_tod`, `vol_z_tod`, `ofi`, `dry_powder_sec`, and `spread_collar_bps`.
2. **Label-Only Study Wall (`Defect B`):** `evaluate_symbol_ranking_to_strategy_handoff()` checked `study_date <= 2026-10-15` without deriving or checking the calendar date of `decision_ns`, and Workflow `#19`'s sample epoch (`1_760_500_000 s`) corresponded to `2025-10-15` rather than `2026-10-15`.
3. **12-Feed Key Mismatch & Unresolved Short IDs (`Defect C`):** `feed_ids` emitted `DF10..DF12` while `feeds` keyed `DF10_OWN_HISTORY_...`, raising `KeyError` on `feeds[fid]`, and `required_feeds` short IDs (`DF1..DF12`) had no resolver.
4. **CLI Flag Mismatch & Unclosed Review Schema (`Defects D & E`):** `build_orca_lead_e2e_convergence_assignment()` emitted `--mode live-cli` instead of `--backend claude`, `CONVERGENCE_STAGE_SCHEMA` lacked `additionalProperties: False`, and Workflow `#19` recorded reviewer verification even when Phase 1 was skipped.

## Decision Outcome

1. **Enforce IEEE-754 Finite & Bitemporal `decision_ns` Study-Wall Invariants (`src/sota_mmw/symbol_ranking_datafeeds.py`):**
   - Require `_is_finite_real()` (`math.isfinite`) and negated comparisons (`not (x >= floor)` / `not (x <= cap)`) on every numeric input, require UNIX epoch nanoseconds `>= 2000-01-01`, derive UTC `decision_date` from `decision_ns`, and require `decision_date <= 2026-10-15` and `decision_date == study_date`.
2. **Unify `DF1..DF12` Schema Bijection & `resolve_route_required_feeds()`:**
   - Ensure `feed_id == key` across all `12` entries in `FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS` with uniform metadata keys plus `feeds_by_short_id` (`DF1..DF12`) and `resolve_route_required_feeds()`.
3. **Align `--backend claude` & Honest Turn-0 Attribution (`cc_lead_hub.py` & `orca_lead_e2e_research_convergence_workflow.py`):**
   - Emit `--backend claude`, close `CONVERGENCE_STAGE_SCHEMA` with `additionalProperties: False`, update sample epoch to `2026-10-15T14:30:00Z` (`1_792_074_600_000_000_000` ns), and record `turn0-deterministic-sample-only (no reviewer agent ran)` whenever Phase 1 reviewers are skipped.

## Alternatives Considered

- **Allowing synthetic small integers (`100`, `200`, `300`) for `decision_ns`:** Rejected — permits unanchored timestamps to bypass bitemporal calendar-wall checks.

## Verification Witness

- `scripts/architecture_catalog.py --sync-manifest && scripts/architecture_catalog.py --check` (`26` ADRs, `0` drift)
- `ruff format --check . && ruff check . && python -m unittest discover -s tests -v && python scripts/merge_gate.py && gitleaks git --no-banner` (`PASS`, `0` leaks)
