# ADR-0013: v3.6.0 Universal 14/14 Workflow Research-Convergence, Trading Lane DataFeed APIs, 4 Strategy Templates, 8 Engine Sources & 3-Surface Workstation Parity

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Full-Stack Workflow, DataFeed, Strategy Template, Engine Source & Dual-Workstation Governance (`L0–L12` × `P0–P5` × `T0–T8`)
- **Evidence Grade:** E4 (14/14 Workflows Verified with `verify_workflow_research_convergence`, Live `:8787` DataFeed/Template APIs & 3-Surface `Mac` / `Noesis Win32` / `Noesis-Carbon WSL2` Tested)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/native-agent-stack/astrolabe, https://github.com/native-agent-stack/sota-upstream-shelf-lock, https://github.com/nautechsystems/nautilus_trader, https://github.com/nkaz001/hftbacktest, https://github.com/alpacahq/alpaca-py, https://github.com/stablyai/orca
- **Revisit Trigger:** Addition of a 15th canonical workflow, `2026-12-06` `23/5` `SIP` overnight cutover, or engine pin bump

## Context and Problem Statement

While `ADR-0011` and `ADR-0012` introduced `research_convergence_landing_workflow.py` (`#13`) and `cc_lead_multi_runtime_workers_workflow.py` (`#14`), three concrete cross-ecosystem gaps remained:
1. Only `1/14` workflows executed deterministic `verify_research_convergence_claim(...)` validation at Turn-0 (`13/14` loaded summary context without binding the `6` Trading Lane DataFeed APIs, `4` canonical strategy templates + Pine v6, and `8` trading engine source repositories into a verified SHA-256 envelope);
2. `_sota_kit.py` read `payload.get("feeds")` before `canonical_7_feeds` on `:8787/api/research_feeds` and did not probe `/api/strategy_templates`;
3. Repo resolution inside `_sota_kit.py` and several workflows hardcoded `Path.home() / "Documents"` and `"python3"`, whereas stationary `Noesis` stores its `18` repositories at `C:/sota-workstation/*` on Windows (`Win32`) and `~/sota-workstation/*` inside the clean `Ubuntu 26.04.1` `Noesis-Carbon` WSL2 guest.

## Decision Outcome

We ship `sota-multi-model-workflows` `v3.6.0` (`src/sota_mmw/research_convergence_contract.py`, `workflows/_sota_kit.py`, and all `14/14` scripts in `workflows/`):

1. **Universal `14/14` Turn-0 Research-Convergence Envelope (`verify_workflow_research_convergence`):**
   - Every single one of the `14/14` canonical workflows invokes `kit.verify_workflow_research_convergence(workflow_id, repo=...)` (`sota-workflow-research-convergence.v3.6`), computing a deterministic `64`-hex `golang/mod` `dirhash`-style `envelope_input_sha256` and running `verify_research_convergence_claim` (`40`-hex upstream pins, `study_max_date <= 2026-10-15`, `0 < hard_stop_pct <= 2.00%`, `PHILOSOPHY_ONLY` sibling-repo authority).
2. **6 Trading Lane DataFeed APIs, 4 SOTA Strategy Templates & 8 Trading Engine Sources:**
   - Bind `CANONICAL_TRADING_LANE_DATAFEED_APIS` (`:8787/api/{research_feeds,first_hand_incentives,strategy_templates,research_convergence}`, `:8799/api/{status,tv-webhook}`, and `127.0.0.1:4002` `astrolabe` IBKR Paper `L1` with `300/min` protective-exit reserve; live ports `4001`/`7496` hard-refused).
   - Bind `CANONICAL_STRATEGY_TEMPLATES_MATRIX` (`PRE_TRAVEL_EARLY_IGNITION`, `FIRST_HAND_SEC_EPISODIC_PIVOT`, `MEGA_CAP_NEAR_LOSSLESS_ORB`, `CLIMAX_VWAP_MEAN_REVERSION` + non-repainting closed-bar `sota_pine_v6_nonrepainting.template.pine` + `tsl` and `trading-sota` `strategies/_template/manifest.json`) under `ADVERSE_STOP_FIRST` and `100x` CTA/UTP round-lot `hftbacktest::RiskAdverseQueueModel` parity.
   - Bind `CANONICAL_TRADING_ENGINE_SOURCES` across all `8` trading engine & research repositories (`meridian`, `canon`, `tsl`, `trading-sota`, `sota-mover-ranker`, `astrolabe`, `sota-compounding-lab`, `sota-dynamic-trail-c`) plus `sota-upstream-shelf-lock`.
3. **3-Surface Dual-Workstation Path & Interpreter Parity (`Mac M5 Max` + `Noesis Win32` + `Noesis-Carbon WSL2`):**
   - Introduce `resolve_ecosystem_repo_dir()` and `detect_workstation_surface()` resolving `~/Documents/<repo>` (Mac), `C:/sota-workstation/<repo>` (`Noesis` Windows), and `~/sota-workstation/<repo>` (`Noesis-Carbon` WSL2), and replace `"python3"` with `sys.executable` in workflow probes.

## Alternatives Considered

1. **Restrict full `verify_research_convergence_claim` checks to `research_convergence_landing_workflow.py` only:** Rejected — leaves `ao`, `cc-lead`, `autoresearch`, `compounding`, `early-mover`, and `dual-workstation` workflows without deterministic Turn-0 verification of strategy templates, DataFeed APIs, and engine pins.
2. **Maintain separate workflow forks for macOS, Windows, and WSL2:** Rejected — `resolve_ecosystem_repo_dir()` and `agent_bin_argv()` keep all `15` files in `workflows/` 100% byte-identical across all three surfaces.

## Verification Witness

- `python3 -m unittest discover -s tests -v`: verifies `14/14` workflows invoke `verify_workflow_research_convergence`, `3`-surface `resolve_ecosystem_repo_dir` (`Mac`, `Noesis Win32`, `Noesis-Carbon WSL2`), live/mock `:8787` `canonical_7_feeds` + `strategy_templates` parsing, and `0` claim violations (`PASS`).
- `python3 scripts/architecture_catalog.py --sync-manifest` + `python3 scripts/merge_gate.py` -> `PASS` (`13` GitHub-evidenced MADR 4.0 ADRs, `0` drift, `0` leaks).
