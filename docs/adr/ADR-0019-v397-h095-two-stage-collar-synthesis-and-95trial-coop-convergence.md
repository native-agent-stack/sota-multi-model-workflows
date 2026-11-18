# ADR-0019: v3.9.7 Pre-Registered Trial `#95` (`H095`) Two-Stage Collar Synthesis, 95-Trial (`t*(96) = 4.1882`) Ledger & 18-Repo Co-op Convergence

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Orchestration, Quantitative Falsification & Compounding SemVer Governance (`L0–L13` × `T1–T3` × `H1–H3`)
- **Evidence Grade:** E4 (`95` Pre-Registered HLZ Trials, `77` `E1–E4` Lessons, `46/46` SOTA Skills, `17/17` Workflows & `18/18` Unit Suite Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/meridian, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/sota-compounding-lab
- **Revisit Trigger:** 2027-01-02 or pre-registered Trial `#96` (`t*(96) = 4.1882`)

## Context and Problem Statement

Following `ADR-0018` (`46`-skill native workflow enactor, Workflow `#17`, and `11` Dual-Machine Orca Automations) and `H094` (`meridian 0061`, `-97.274 bps` pure-passive runaway-breakout adverse selection), our multi-session co-op partition (`6 + 7 + 1 + 1 + 3 = 18/18` active repositories) executed pre-registered Trial `#95` (`H095_TWO_STAGE_LIT_QUEUE_15S_TO_10BPS_MARKETABLE_COLLAR_ORB_CPCV`, `spec_sha256 = 5abe51a4caacf4bf6955a331b495310fae1791a8d74a76c111bc9e6a35b5f4fa`) and synchronized Two-Track Compounding Versioning across all `3` surfaces.

## Decision Outcome

1. **Advance Compounding Ledger Defaults to `v3.9.7` (`N = 95`, `t*(96) = 4.1882`, `PROTECTIVE_FILTER_OR_GOVERNANCE`):**
   - Record Trial `#95` (`189 / 319` fills across `157` dates `<= 2026-10-15`: `-1.740 bps` net `1x`, `t = -0.1089 < 4.1858 -> FAILED` on `ALPHA_STRATEGY_MINOR`, `+47.804 bps` adverse-selection improvement vs `H094`, `8/15` `C(6,2)` disjoint CPCV `> 0`) and its `E4` Stage-1 (`[0..15s]` passive `-8.736 bps` `1x`, `59.7%` `trade_through` seller sweeps) vs Stage-2 (`+15s` bid-survived `<= 10.0 bps` collar `+15.305 bps` `1x`, `+9.832 bps` `2x`) bifurcation.
   - Align `DEFAULT_ECOSYSTEM_SEMVER = "3.9.7"` across `native_workflow_enactor.py`, `REGISTRY.json`, and `SOTA_WORKFLOW_MANIFEST.json` (`19` ADRs).

## Alternatives Considered

- **Advancing minor SemVer (`3.10.0`) without `ALPHA_STRATEGY_MINOR` HLZ/DSR clearance:** Rejected; Two-Track SemVer (`ADR-0015`) reserves minor increments strictly for hypotheses clearing `t >= t*(N)`, `DSR >= 0.95`, `CPCV >= 70%`, and `Stage-3 >= 30` real paper roundtrips.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` -> `19` ADRs valid, `0` drift
- `ruff check . && ty check src scripts tests workflows/_sota_kit.py` -> `0` issues
- `pytest -q && python3 scripts/merge_gate.py && gitleaks git --staged --no-banner` -> `18 passed`, `PASS`, `0` leaks
