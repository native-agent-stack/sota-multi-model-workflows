# ADR-0011: End-to-End Research-Convergence, 7-Feed PIT DataFeed & Strategy Template Workflow

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Research Convergence, 7-Feed PIT DataFeed & Strategy Lifecycle (`L1–L9` × `T1–T8`)
- **Evidence Grade:** E4 (Unit Tested, 13/13 Workflows AST-Compiled & GitHub Actions Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/native-agent-stack/sota-upstream-shelf-lock, https://github.com/alpacahq/alpaca-py, https://github.com/dgunning/edgartools, https://github.com/nautechsystems/nautilus_trader
- **Revisit Trigger:** 2026-12-06 Alpaca `23/5` SIP cutover activation or schema revision beyond `sota-research-feeds.v2`

## Context and Problem Statement

Across the converged `native-agent-stack` ecosystem, quantitative factor discovery (`meridian`, `sota-compounding-lab`, `trading-sota`), point-in-time market & SEC catalyst ingestion (`sota-mover-ranker` `:8787`), sub-50ms protective trailing execution (`sota-dynamic-trail-c` `:8799`), and `IBKR` `outsideRth` paper routing (`astrolabe` `:4002`) share a strict 3-tier Research-Convergence contract (`ADR-0004` 64-hex input `SHA-256` + 18 40-hex upstream commit SHAs in `~/Documents/upstream/PINS.md` + canonical `sota_converged_strategy.template.json`). Previously, child workflow agents had to rediscover DataFeed point-in-time rules, adjustment semantics, and strategy template paths ad hoc instead of receiving them deterministically on Turn 0.

## Decision Outcome

1. **Deterministic Research-Convergence Contract (`src/sota_mmw/research_convergence_contract.py`):**
   - Codifies the 7-feed `sota-research-feeds.v2` specification (`CANONICAL_DATAFEEDS`: `alpaca_sip` `04:00–20:00 ET`, `alpaca_boats` `20:00–04:00 ET` + `2026-12-06` `23/5` cutover flag, `alpaca_raw_vs_all_adjustment`, `sec_edgar_acceptance_datetime` `15m` half-life + `424B*`/`S-3` dilution block, `finra_regsho_cnmsshvol_t1` `T-1` lag, `corporate_actions_split_guard`, and `ibkr_paper_4002_l1` `:4002` paper lane) and the 4 `CANONICAL_STRATEGY_ARCHETYPES`.
   - Provides `verify_research_convergence_claim()` enforcing 64-char hex `input_sha256`, 40-char hex `upstream_pins`, `study_max_date <= "2026-10-15"`, `0 < hard_stop_pct <= 2.00` (`ADR-0022`), and `E0..E4` evidence grading.
2. **Universal Turn-0 Injection via `workflows/_sota_kit.py` (`v3.3.0`):**
   - Adds `load_research_convergence_context()` probing live `http://127.0.0.1:8787/api/research_feeds` (`timeout=0.8`) with zero-latency offline fallback to the canonical 7-feed `sota-research-feeds.v2` specification, checking `~/Documents/upstream/PINS.md` commit pin count and canonical strategy templates (`sota_converged_strategy.template.json`, `_template/manifest.json`), and appending a 2-line `[SOTA Research-Convergence & 7-Feed PIT Contract]` header inside `load_peer_brief()` across all 13 workflows.
3. **Self-Bootstrapping Workflow `#13` (`workflows/research_convergence_landing_workflow.py`):**
   - Registers `research-convergence-landing` in `workflows/REGISTRY.json` (`v3.3.0`, 13 workflows), orchestrating Phase 1 (`ADR-0004` + 18-repo upstream pin + 7-feed PIT recon), Phase 2 (`sota_get_converged_strategy_templates` scaffolding & `<= 2026-10-15` pre-wall run), Phase 3 (parallel `sota-falsifier` + `sota-code-verifier` gates), and Phase 4 (`:8787` / `:8799` / `:4002` paper-lane manifest landing + `peer_bus.db` checkpoint).

## Alternatives Considered

1. **Prompt-only conventions without executable Python validation:** Rejected — prose reminders drift across sessions, whereas `verify_research_convergence_claim()` and Turn-0 `_sota_kit.py` injection deterministically block post-wall dates, unpinned upstreams, and `> 2.00%` stops.
2. **Hard-failing workflows when `:8787` is offline (e.g. on Ubuntu CI runners or roaming laptop):** Rejected — instant fallback (`timeout=0.8`) to the locked `CANONICAL_DATAFEEDS` contract keeps offline CI and roaming sessions 100% deterministic.

## Verification Witness

- `python3 scripts/architecture_catalog.py --check` -> `11 GitHub-evidenced MADR 4.0 ADRs & manifest verified (0 drift)`
- `python3 scripts/merge_gate.py` & `python3 -m unittest discover -s tests -v` -> `PASS`
