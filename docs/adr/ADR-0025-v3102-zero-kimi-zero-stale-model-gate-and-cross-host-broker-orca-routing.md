# ADR-0025: `v3.10.2` Zero-Stale & Zero-Kimi Model Hygiene Gate, Cross-Host Broker-Pinned Orca Routing (`100.93.211.101`), and `worker-release --environment` Parity

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Fleet Hygiene, Cross-Host Single-Broker Orca Routing & CLI Contract Parity (`L3..L7` x `T1..T5` x `H0..H7`)
- **Evidence Grade:** E4 (`FORBIDDEN_STALE_AND_REDUNDANT_MODELS` Enforced, `0` Kimi/Moonshot & `0` Retired Models, Real-Call Verified `sota-lanes route --repo sota-mover-ranker` on Noesis -> `--on 100.93.211.101` + Mac Hub `4cf80c7f`, `worker-release --environment`, `ruff`/`ty`/Unit Suite/`merge_gate.py`/`gitleaks` `0` Leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/cc-sota-harness, https://github.com/stablyai/orca, https://artificialanalysis.ai/models
- **Revisit Trigger:** Upstream frontier model release verified on `https://artificialanalysis.ai/models` or `2026-12-06` `23/5` SIP cutover

## Context and Problem Statement

1. **Owner Model-Hygiene Directives (`2026-11-18`):** All active routing tables, worker profiles, and workflow envelopes must strictly forbid superseded models (`deepseek-v4-pro`, `deepseek-v4-flash`, `deepseek-v3*`, `gemini-3.8-flash*`, `gpt-6.1-sol`, `gpt-6-astra`, `claude-fable-5-1`, `grok-4.6`, `muse-spark-1.2`) and redundant `kimi-*` / `Moonshot AI` entries, consolidating non-GPT `Hephaestus` / `OpenCode` / `OMO` onto `claude-sonnet-5-5` + `deepseek-v4.1-flash` (`deepseek-flash`).
2. **Cross-Host Broker-Pinned Orca Routing on Stationary `Noesis` (`noesis-cc-lead` `#76a`):** On `Noesis` (`100.110.115.22`), `sota-lanes route --repo sota-mover-ranker --placement local|auto` correctly selected `selected_surface = "portable_mac_m5_max"` under `SINGLE_BROKER_HOST_FIREWALL`, yet fell into `if use_noesis or on_noesis_self:` and emitted a local Orca command carrying Noesis's repo UUID (`492fe9dd`) and Noesis's trading hub (`c4f93f9e`) instead of targeting `100.93.211.101` (`portable_mac_m5_max`) with Mac's trading hub (`4cf80c7f`).
3. **`orca orchestration worker-release` Flag Contract (`F02`) & Direct HLZ Floor (`F10`):** `worker-release` accepts `--environment <host>` rather than `--on <host>`, and direct callers of `build_cc_lead_execution_plan` defaulted to `N=88 / t*=4.1709` instead of `N=96 / t*=4.1905`.

## Decision Outcome

1. **Retire `opencode-kimi-omo` / `Moonshot AI` & Enforce `FORBIDDEN_STALE_AND_REDUNDANT_MODELS`:**
   - Replace `opencode-kimi-omo` with `opencode-sonnet-omo` (`vendor="anthropic"`, `model="claude-sonnet-5-5"`, keeping `opencode-kimi-omo` rejected by `FORBIDDEN_STALE_AND_REDUNDANT_MODELS` in `validate_cc_lead_safety_and_invariants()`), update `opencode_omo_hephaestus` models to `("claude-sonnet-5-5", "deepseek-v4.1-flash")`, and trim `CANONICAL_SEVEN_MODEL_VENDORS` to the `6` active non-Moonshot vendors (`Anthropic`, `OpenAI`, `Google DeepMind`, `DeepSeek`, `xAI`, `Meta`).
2. **Pin Broker-Bound Orca Commands Executed on `Noesis` to `100.93.211.101` (`portable_mac_m5_max`):**
   - In `resolve_dual_machine_lane_plan()`, whenever a workload is broker-pinned (`T1_live_24x5_alpaca_paper_and_guardian` default/active_paper_broker or `astrolabe` default/active_paper_broker) and `is_running_on_noesis_host()` is `True`, emit `--on 100.93.211.101` (`worker-start`) and `--environment 100.93.211.101` (`worktree create`) with `name:<repo>` and `ORCA_LANE_HUBS["portable_mac_m5_max"][plane]`, ensuring broker-lane dispatches never execute on `Noesis`.
3. **Standardize `worker-release --environment` & `HLZ N=96 / t*=4.1905`:**
   - Pass `flag="--environment"` on all `worker-release` templates and raise `build_cc_lead_execution_plan()` defaults to `hlz_trials_n=96`, `hlz_next_t_hurdle=4.1905`.

## Alternatives Considered

- **Refusing `sota-lanes route --repo sota-mover-ranker --placement auto` on `Noesis`:** Rejected — `--placement noesis` already hard-refuses with `PermissionError("SINGLE_BROKER_HOST_FIREWALL")` (exit `2`), whereas `--placement auto|local` from `Noesis` should deterministically target the sovereign Mac broker host (`--on 100.93.211.101`) with Mac's hub selector.

## Verification Witness

- `scripts/architecture_catalog.py --sync-manifest && scripts/architecture_catalog.py --check` (`25` ADRs, `0` drift)
- `ruff format --check . && ruff check . && python -m unittest discover -s tests -v && python scripts/merge_gate.py && gitleaks git --no-banner` (`PASS`, `0` leaks)
