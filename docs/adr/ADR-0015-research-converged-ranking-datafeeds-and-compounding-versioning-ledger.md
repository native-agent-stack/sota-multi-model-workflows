# ADR-0015: Research-Converged 9-Feed Ranking System DataFeeds (`DF1–DF9`) & Two-Track Compounding Versioning Ledger (`v3.8.0`)

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Point-in-Time DataFeeds, Microstructure Hygiene & Compounding SemVer Governance (`L1–L9` × `T1–T8`)
- **Evidence Grade:** E4 (Unit Tested, 4-Hash Cryptographic Lineage Verified & Public GitHub Actions Verified)
- **GitHub Evidence:** https://github.com/alpacahq/alpaca-py, https://github.com/pola-rs/polars, https://github.com/duckdb/duckdb, https://github.com/gerrymanoim/exchange_calendars, https://github.com/dgunning/edgartools, https://github.com/ib-api-reloaded/ib_async, https://github.com/ml4t/diagnostic, https://github.com/native-agent-stack/sota-multi-model-workflows
- **Revisit Trigger:** Upstream pin bump in `~/Documents/upstream/PINS.md`, `2026-12-06` `23/5` SIP cutover activation, or new `DF10+` primary feed onboarding

## Context and Problem Statement

As the organization's pre-registered Harvey–Liu–Zhu hypothesis ledger reached `N = 90` (`t*(90) = 4.1735`, `t*(91) = 4.1760`) and `60` compiled `E1–E4` lessons across `Mac M5 Max` and `Stationary Noesis`, two governance gaps required deterministic enforcement:
1. **Granular Ranking System DataFeeds (`DF1..DF9`):** While `sota-research-feeds.v2` grouped 7 logical feeds, institutional ranking hygiene requires explicitly separating `XNYS` time-of-day `RVOL_tod` bucket normalization (`DF4`, `Canon 0173`), point-in-time SEC XBRL public float (`DF6`, `filed <= as_of`), and `T-1` FINRA `CNMSshvol` (`DF7`) vs `+8` `XNYS` business-day FINRA Rule 4560 settled short interest (`DF8`, `20260930` as-of `2026-10-15`), while preserving 100% backward compatibility with `sota-research-feeds.v2`.
2. **Two-Track Compounding Versioning (`H090` Lesson):** Structural microstructure discoveries such as `Trial #90` (`H090`: `+20.84 bps` 1x, `+15.43 bps` 2x, `5/5` `100%` positive `CPCV` folds, `+39.06 bps` in `2026`, `t = 1.2919 < 4.1735`) improve execution hygiene when applied as protective filters (`astrolabe ADR-0007`), yet must **never** bypass the HLZ/DSR/30-roundtrip bar to claim autonomous alpha-strategy elevation.

## Decision Outcome

1. **9-Feed Ranking System DataFeed Contract (`CANONICAL_RANKING_DATAFEEDS_V38`, `sota-ranking-datafeeds.v3.8`):**
   - Codifies `DF1..DF9` in `src/sota_mmw/compounding_versioning.py` as a strict, hash-locked (`compute_ranking_datafeed_contract_sha256()`) backward-compatible superset of `sota-research-feeds.v2`.
2. **4-Hash Monotonic Compounding Versioning & Two-Track Gate (`CompoundingVersionRecord` & `sota-version` CLI):**
   - `verify_compounding_version_transition()` enforces strictly monotonic SemVer (`prev_semver < next_semver`), 4 cryptographic lineage anchors (`input_lake_sha256`, `upstream_shelf_tree_sha256` across all `18` `PINS.md` commits, `ranking_datafeed_contract_sha256`, sequential `ADR-XXXX`), `trials_n >= 90` (`t*(N+1) >= 4.1760`), `lessons_count >= 59`, `<= 2026-10-15` pre-wall cutoff, `ADR-0022 <= 2.00%` stop cap, and `PHILOSOPHY_ONLY` sibling-repo authority.
   - Enforces **Two-Track Promotion**: `ALPHA_STRATEGY_MINOR` requires `DSR >= 0.95`, `CPCV >= 70%`, `t >= t*(N)`, positive `1x`/`2x` net expectancy, and `>= 30` closed roundtrips across `>= 10` sessions; `PROTECTIVE_FILTER_OR_GOVERNANCE` permits `>= 70% CPCV` non-negative-expectancy structural discoveries (`H090`) to compound strictly as protective filters / ADRs (`alpha_stage_elevated = False`).
3. **Self-Bootstrapping Workflow `#16` (`compounding-versioning-and-ranking-adr`, `v3.8.0`):**
   - Ships `workflows/compounding_versioning_and_ranking_adr_workflow.py` (`16/16` explicit Research-Convergence + `<workflow>` `__file__` guard) and standalone `~/.agents/bin/sota-version`.

## Alternatives Considered

1. **Discarding `5/5 CPCV` microstructure hygiene improvements (`H090`) completely:** Rejected — lit-only queue filtering reduces adverse selection without adding alpha degrees of freedom when explicitly locked to `PROTECTIVE_FILTER_OR_GOVERNANCE`.
2. **Allowing sub-hurdle `t < t*(N)` trials to bump `ALPHA_STRATEGY_MINOR`:** Rejected — violates Harvey–Liu–Zhu multiple-testing false-discovery control.

## Verification Witness

- `python3 scripts/architecture_catalog.py --check` -> `15 GitHub-evidenced MADR 4.0 ADRs & manifest verified (0 drift)`
- `python3 scripts/merge_gate.py` & `python3 -m unittest discover -s tests -v` -> `PASS`
