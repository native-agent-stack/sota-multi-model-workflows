# ADR-0017: v3.9.1 Twin Overnight Extended-Hours Stop-Whipsaw Law (`H092`+`H093`), 93-Trial / 69-Lesson HLZ Ledger & 18-Repo `UPSTREAM.md` Completion

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Orchestration, Compounding Versioning & Quantitative Falsification (`L0–L13` × `T1–T5` × `H0–H7`)
- **Evidence Grade:** E4 (`93` Pre-Registered HLZ Trials incl. `H092`+`H093` `7,473`-Event Proof, `69` `E1–E4` Lessons, `18/18` `UPSTREAM.md` & `17/17` Unit Suite Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/native-agent-stack/sota-mover-ranker, https://github.com/native-agent-stack/canon, https://github.com/stablyai/orca
- **Revisit Trigger:** 2027-01-02

## Context and Problem Statement

Following `ADR-0016` (`v3.9.0` Dual-Machine Orca Lane Hubs v2 & `a253421e8734...` pre-wall SHA-256), concurrent peer execution across `sota-compounding-lab` (`H092`+`H093`), `sota-mover-ranker` (`@ e8eebd7a0570` MCP `64 KB` `stderr=PIPE` deadlock elimination + `ADR-0017` live E2E spread/streak shield + 1-share dust-crumb filter), `dsh-sota-harness` (`@ 9e4ca13e4e62` Ubuntu 26.04 `--dump-dom` headless Chrome probe), and `canon` (`0180` `18/18` `UPSTREAM.md`) advanced the global compounding ledger to **`N = 93` pre-registered trials (`t*(94) = 4.1834`)** and **`69` compiled `E1–E4` root-cause lessons**.

## Decision Outcome

1. **Advance `DEFAULT_ECOSYSTEM_SEMVER` to `"3.9.1"` (`ADR-0016 -> ADR-0017`):**
   - Record `V391_H092_H093_OVERNIGHT_WHIPSAW_LAW_AND_93TRIAL_69LESSON_SEAL` in `src/sota_mmw/compounding_versioning.py`, `workflows/REGISTRY.json`, and `SOTA_WORKFLOW_MANIFEST.json`, preserving two-track `PROTECTIVE_FILTER_OR_GOVERNANCE` discipline (`alpha_stage_elevated = False`).
2. **Codify Twin Overnight Stop-Whipsaw Falsification (`H092` + `H093`):**
   - Bind `H092` (`5,400` events / `677` days, `t = -5.4145`) and `H093` (`2,073` events / `580` days, `t = -4.6903`) proving `18.8%–23.1%` thin-bar extended-hours `-200 bps` stop whipsaw prior to `09:30` ET, reinforcing RTH `H090` tight-spread passive-bid routing and `DF2` `BOATS` liquidity filtering.

## Alternatives Considered

- **Leaving `DEFAULT_ECOSYSTEM_SEMVER` at `3.9.0` while `.github` and `native-agent-stack` seal `3.9.1`:** Rejected; `sota-version` is the canonical source of truth for `L13` SemVer parity across all 3 workstation surfaces.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` -> `17` ADRs valid, `0` drift
- `ruff check . && ty check src scripts tests workflows/_sota_kit.py` -> `0` issues
- `python3 -m unittest discover -s tests` -> `Ran 17 tests ... OK`
- `python3 scripts/merge_gate.py && gitleaks git --staged --no-banner` -> `PASS`, `0` leaks
