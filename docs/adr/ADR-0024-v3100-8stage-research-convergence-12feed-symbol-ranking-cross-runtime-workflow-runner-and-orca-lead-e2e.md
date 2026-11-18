# ADR-0024: `v3.10.0` 8-Stage SOTA Research Convergence, Finalized 12-Feed Symbol Ranking (`DF1..DF12`), Cross-Runtime `sota-workflow run` & Orca Lead (`cc-lead`) E2E Assignment

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Research Convergence, 12-Feed Symbol Ranking DataFeeds (`DF1..DF12`), 8-Runtime SOTA Fleet & Orca Lead (`cc-lead`) E2E Orchestration (`L0..L13` x `P0..P5` x `T1..T5` x `H0..H7`)
- **Evidence Grade:** E4 (`DF1..DF12` -> `6` Auto-Trading Routes, JSON-RPC Notification Silence & Error Recovery Verified, `sota-workflow run` Across All `8` Runtimes, `sota-cc-hub assign-orca-lead` + Live Orca Automation `cc-lead` E2E, `ruff`/`ty`/Unit Suite/`merge_gate.py`/`gitleaks` `0` Leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-upstream-shelf-lock, https://github.com/stablyai/orca, https://github.com/microsoft/RD-Agent, https://github.com/databento/databento-python, https://github.com/microsoft/qlib
- **Revisit Trigger:** 2026-12-06 (`23/5` Consolidated SIP cutover) or post-wall `ALPHA_STRATEGY_MINOR` qualification (`t >= t*(N+1)`, `DSR >= 0.95`)

## Context and Problem Statement

1. **Finalizing the Symbol Ranking System DataFeeds (`DF1..DF12`) Foundation for Auto Trading Strategies:** Following `v3.8.0` `DF1..DF9` (`ADR-0015`) and `v3.9.9` own-history time-of-day abnormal-rate (`RVOL_tod >= 2.20`, `vol_z_tod >= 2.30`) + `900s` Wave-2 cooldown parity (`v3.9.9`), every autonomous paper strategy needed an explicit, fail-closed `DF1..DF12` DataFeed API and bitemporal PIT handoff contract enforcing `ts_event_ns <= ts_recv_ns <= decision_ns`, `H096` `15s <= 10.0 bps` collars, `microsoft/qlib` `RankIC` + `kappa=40` post-wall Empirical-Bayes feedback (`REAL_BROKER_ONLY`), and `ADR-0022 <= 2.00%` stop caps across `6` strategy routes under `singleActiveBrokerHostOnly = True`.
2. **8-Stage SOTA Convergence Beyond the 413-Starred Ecosystem:** Grounded in the owner's `413` GitHub starred repositories and frontier additions beyond starred (`microsoft/RD-Agent`, `databento/databento-python`, `unit8co/darts`, `Nixtla/statsforecast`, `stanfordnlp/dspy`, and `ADIA-Lab/MinTRL-MDE-PowerGate`), research convergence required an executable 8-stage contract (`S1..S8`).
3. **Resolving Noesis Multi-Runtime Execution Gaps & Enabling Orca Lead (`cc-lead`) E2E:** Prior empirical audits on Stationary Noesis identified concrete runtime friction: non-AGY runtimes (`Claude Code`, `Codex`, `OpenCode`, `Orca` automations) lacked a `sota-workflow run` subcommand capable of top-level `await` execution; dry-runs could mutate `HANDOVER.md` without `SOTA_WORKFLOW_DRY_RUN=1`; `select_workflow_and_skills` passed static default `88/4.1709` instead of live HLZ counts; `cc_lead_hub` needed explicit `assign-orca-lead` handoff plus Win32 PowerShell / `codex exec --skip-git-repo-check` headless parity and live-callable vs shim diagnostics; and MCP servers needed canonical JSON-RPC 2.0 notification silence (`0` replies when `id is None`).

## Decision Outcome

1. **Publish `src/sota_mmw/symbol_ranking_datafeeds.py` (`sota-symbol-ranking-datafeeds.v3.10`, `DF1..DF12`):**
   - Preserve `sota-ranking-datafeeds.v3.8` (`DF1..DF9`, 9 feeds) 100% backward-compatible while adding `DF10` (`Own-History ToD Normal Rate + NYSE X1/X2 U-curve`), `DF11` (`Databento Bitemporal PIT + H096 15s Collar`), and `DF12` (`Qlib RankIC + kappa=40 Post-Wall EB Feedback`), plus `sota-version ranking-feeds --v310 --json`, `evaluate_symbol_ranking_to_strategy_handoff()`, and `SYMBOL_RANKING_TO_AUTO_STRATEGY_ROUTES` (`6` autonomous routes).
2. **Enforce 8-Stage Advanced Research Convergence & Canonical JSON-RPC 2.0 MCP Server (`src/sota_mmw/peer_bus_mcp_server.py`):**
   - Add `ADVANCED_8STAGE_RESEARCH_CONVERGENCE_PRACTICE` (`S1..S8`), `STARRED_AND_BEYOND_SOTA_RESEARCH_STACK` (`413` + `6`), and `verify_advanced_sota_convergence_practice()` in `research_convergence_contract.py`, alongside a tracked `handle_jsonrpc_message` implementation enforcing strict notification silence and `isError: True` fault isolation across all 9 Protobuf-safe `sota_bus_*` tools.
3. **Ship Workflow `#19` (`orca-lead-e2e-research-convergence`), `sota-workflow run`, & `sota-cc-hub assign-orca-lead`:**
   - Add Workflow `#19` across `REGISTRY.json`, `SOTA_WORKFLOW_MANIFEST.json`, and `workflows/orca_lead_e2e_research_convergence_workflow.py` (`19` workflows total), `SOTA_WORKFLOW_DRY_RUN=1` guard in `_sota_kit.py`, live HLZ propagation in `select_workflow_and_skills()`, cross-runtime `sota-workflow run` executor (`deterministic` and `live-cli`), `ENHANCED_8_RUNTIME_SOTA_PROFILES` (`deepseek-flash`, `claude-fable-5-2`, `claude-sonnet-5-5`, `gpt-6.2-astra`, `gpt-6.2-sol`, `gemini-4-carbon-high`), Win32 `2b_win32_orca_and_codex_headless_cmds`, and `sota-cc-hub assign-orca-lead` assigning E2E convergence to Orca Lead (`cc-lead`).

## Alternatives Considered

- **Modifying frozen `CANONICAL_RANKING_DATAFEEDS_V38` (`9` feeds) or `CANONICAL_TRADING_LANE_DATAFEED_APIS` (`6` entries) in place:** Rejected — breaking frozen `v3.8.0` contract tests is avoided cleanly by additive `SYMBOL_RANKING_SYSTEM_APIS_V310` and `DF10_TO_DF12_EXTENSION`.
- **Leaving `sota-workflow` as plan-generation only (`enact`):** Rejected — non-AGY runtimes and scheduled `Orca` automations must execute any canonical `REGISTRY.json` workflow directly from CLI via `sota-workflow run`.

## Verification Witness

- `scripts/architecture_catalog.py --sync-manifest && scripts/architecture_catalog.py --check` (`24` ADRs, `0` drift)
- `ruff check . && ruff format --check . && python -m unittest discover -s tests -v && python scripts/merge_gate.py && gitleaks git --no-banner` (`PASS`, `0` leaks)
