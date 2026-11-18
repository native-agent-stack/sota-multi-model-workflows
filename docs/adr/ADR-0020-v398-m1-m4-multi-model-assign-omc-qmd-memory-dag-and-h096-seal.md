# ADR-0020: v3.9.8 M1-M4 1-Call Multi-Model Task Assignment, OMC v2 Stop-Callbacks, 567-Doc qmd Memory Sync, Beads+Orca DAG & H096 Seal

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Orchestration, Memory & Compounding Governance (`L3` x `L5` x `L7` x `L10` x `L11` x `L13`)
- **Evidence Grade:** E4 (Deterministic Unit Suite, 18-Workflow AST Gate, Live E2EE 3-Surface Memory Sync & Trial #96 Verified)
- **GitHub Evidence:** https://github.com/stablyai/orca, https://github.com/Yeachan-Heo/oh-my-claudecode, https://github.com/tobi/qmd, https://github.com/gastownhall/beads, https://github.com/native-agent-stack/sota-multi-model-workflows
- **Revisit Trigger:** 45 days or upon Ecosystem v4.0.0 promotion

## Context and Problem Statement

While `v3.9.7` (`ADR-0019`) unified bidirectional cross-session Orca terminal wakeups and the `95`-trial `H095` collar synthesis, four operational gaps (`M1–M4`) remained for seamless closed-loop multi-model execution across `Mac M5 Max`, `Stationary Noesis Win32`, and `Noesis-Carbon` WSL2:
1. Assigning a bounded task from Antigravity (`agy`) or `cc-lead` to any of the `7` model vendors still required manual lease claims, manual context assembly, and manual `worker-release`.
2. `oh-my-claudecode` (`OMC v2`) lacked structured JSON stop-hook callback ingestion into `sota-bus`, and `advisor_and_omx_cmds` only emitted `3` of the `7` `omc ask` providers.
3. Cross-surface `sota-workstation coop` synchronized Git SHAs and inbox messages, while `lessons`, `handovers`, and `hypotheses` (`N=96`, `H096`) + `563` MADR 4.0 ADRs were not yet unified under a local `qmd` index + 3-surface E2EE delta sync.
4. Multi-repo convergence waves lacked a first-class 3-stage `bd` (`beads@1.3.4`) + Orca (`--deps` / `gate-create`) dependency DAG and dedicated native workflow (`#18`).

## Decision Outcome

We enact `v3.9.8` (`M1–M4` + `Trial #96` `H096` governance transition):
1. **`M1` — 1-Call Multi-Model Task Assignment (`build_multi_model_assign_envelope` + `sota-cc-hub assign/release` + `sota_bus_assign_worker`):** Routes tasks across `claude`, `codex`, `omp` (`@worker`), `opencode` (`kimi-k3.1-pro`), `muse`, `grok`, `antigravity`, `cc-lead`, and `noesis-cc-lead` with automatic disjoint lease claim, `--spec-file -` `sota-bus` FTS5 + `qmd` memory brief, and `orca orchestration worker-release`.
2. **`M2` — Full 7-Provider `omc ask` & `OMC_RUNTIME_V2=1` Stop-Callback Ingestion:** Emits all `7` `omc ask` providers (`claude`, `codex`, `gemini`, `antigravity`, `grok`, `cursor`, `muse`) and ingests JSON stop callbacks into `sota-bus`.
3. **`M3` — `567`-Doc `qmd` Index & 3-Surface E2EE Memory Delta Sync:** Indexes `4` wiki files + `563` ADRs across `21` repos into `qmd` and replicates `lessons`, `handovers`, and `hypotheses` (`N=96`, `t*(97)=4.1905`) across Mac, `Noesis Win32`, and `Noesis-Carbon` WSL2.
4. **`M4` — Persistent 3-Stage Beads + Orca Wave DAG (`sota-lanes dag`) & Canonical Workflow `#18`:** Adds `build_multi_repo_beads_orca_dag()` and `workflows/multi_model_omc_memory_assign_workflow.py` (`18/18` self-bootstrapping workflows).

## Alternatives Considered

1. **Ad-hoc inline `--spec` CLI strings without stdin `--spec-file -`:** Rejected because multiline memory briefs hit Windows `ConPTY` command-line limits and leak noisy shell quoting.
2. **Polling Orca terminals instead of `OMC` stop-hook JSON callbacks + `worker_done` push wakeups:** Rejected as token-wasteful and race-prone.
3. **Promoting `H096` strict `15s` dry-powder bid-survival (`n=52`, `+16.84 bps` `1x` / `+11.37 bps` `2x`, `73.33%` CPCV) directly on `ALPHA_STRATEGY_MINOR`:** Rejected fail-closed because wide `OFI > 0` (`n=124`, `t=-0.7781`) fell below `t*(96)=4.1882`; recorded strictly on `PROTECTIVE_FILTER_OR_GOVERNANCE` (`N=96 -> t*(97)=4.1905`).

## Verification Witness

- `ruff check .` -> `All checks passed!`
- `ty check src scripts tests workflows/_sota_kit.py` -> `All checks passed!`
- `pytest -q` -> `100% PASS` (including `18/18` workflow AST + `<workflow>` execution checks, `assign`, and `dag` tests)
- `python3 scripts/architecture_catalog.py --check && python3 scripts/merge_gate.py && gitleaks git --staged --no-banner` -> `PASS` (`20` ADRs, `0` leaks)
