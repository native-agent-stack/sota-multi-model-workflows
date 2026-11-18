# ADR-0023: `v3.10.0` Quality-Directive `3`-Powerhouse + `DSH` + `Pi`/`OMP` (`gpt-6.2-sol` `high`) Convergence, Claude Code `~1:1` Model-Mix Rebalancer & Host-Aware Noesis Hub Parity

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Quality-Directive Multi-Model Routing, Claude Code `1:1` Tier Governance & Symmetric 3-Surface Hub Parity (`L1` x `L3` x `L4` x `L8` x `L10`)
- **Evidence Grade:** E4 (Artificial Analysis Intelligence Index `v5.0.1` & Coding Agent Index `v2.1`, `413`-Turn `~/.claude/projects` Telemetry Audit, `noesis-cc-lead` `#188`/`#190`/`#191` Empirical Verification & `21/21` Unit Suite)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/cc-sota-harness, https://github.com/Yeachan-Heo/oh-my-claudecode, https://github.com/can1357/oh-my-pi, https://github.com/stablyai/orca
- **Revisit Trigger:** Artificial Analysis `v5.x` frontier rank shift or Ecosystem `v4.0.0` promotion

## Context and Problem Statement

Empirical telemetry across `413` Claude Code CLI turns (`~/.claude/projects/**/*.jsonl`) and `noesis-cc-lead`'s live Win32 audit (`Peer Messages #188`, `#190`, `#191`) identified three concrete convergence requirements:
1. **Claude Code CLI `0.48%` `fable` vs `69.0%` `haiku` Sprawl:** Because `oh-my-claudecode` (`OMC 5.8.6` `dist/config/models.js`) defaulted `HIGH -> claude-opus-4-8`, `MEDIUM -> claude-sonnet-5`, and `LOW -> claude-haiku-4-5` when `OMC_MODEL_HIGH`, `OMC_MODEL_MEDIUM`, and `OMC_MODEL_LOW` were unset, subagents flooded turns with low-tier `haiku` instead of maintaining the owner's **`~1:1` (`50%` `claude-fable-5-2` vs `50%` remaining `claude-opus-5-5` + `claude-sonnet-5-5`)** quality directive.
2. **Quality-Directive `3`-Powerhouse + `DSH` + `Pi`/`OMP` (`gpt-6.2-sol` `high`) Focus:** Active task routing must assign tasks strictly to suitable authenticated powerhouse models grounded in `https://artificialanalysis.ai/models` (`claude-fable-5-2`/`opus-5-5`/`sonnet-5-5`, `gpt-6.2-astra`/`gpt-6.2-sol` across Codex + `Pi v1.5.2` + `OMP v18.22.0`, `gemini-4-carbon-high`, and `deepseek-v4-pro` `dsh`) rather than unauthenticated `opencode` secondary routes.
3. **Host-Aware `sota-cc-hub` / `sota-lanes` on Stationary Noesis (`#188(2)`):** Invoking `sota-cc-hub` or `sota-lanes` directly on Noesis previously emitted `--on 100.110.115.22` to itself, selected Mac's `folder:729df6dc` hub on `--placement local`, and passed `--surface`/`--sender` instead of `sota_bus_engine.py assign`'s `--placement`/`--callback-to`.

## Decision Outcome

1. **Enact `QUALITY_DIRECTIVE_POWERHOUSE_FLEET`, `OMC_MODEL_HIGH/MEDIUM/LOW`, `audit_claude_1to1_model_mix()` & `rebalance_claude_1to1_route()` (`sota-cc-hub model-mix`):**
   - Bind `OMC_MODEL_HIGH=claude-fable-5-2`, `OMC_MODEL_MEDIUM=claude-sonnet-5-5`, `OMC_MODEL_LOW=claude-sonnet-5-5` (zero `haiku` sprawl), target `50%` `claude-fable-5-2` (`[0.42, 0.58]` band) vs `50%` `claude-opus-5-5` + `claude-sonnet-5-5`, route `ast_graph_multifile_codemod_refactor` to `claude-sonnet-5-5` (`hephaestus_non_gpt_enforced = True`) with `gpt-6.2-sol` (`omp` / `pi`) challenger, and configure `Pi` (`~/.pi/agent/settings.json`) + `OMP` (`@worker`/`@default`/`@smol`) on `openai-codex/gpt-6.2-sol` (`high`).
2. **Enact Host-Aware `is_running_on_noesis_host()` & `orca_remote_on_args()` Across `cc_lead_hub.py` and `dual_machine_lanes.py`:**
   - Never pass `--on 100.110.115.22` when executing on Noesis itself, bind Noesis local hub folders (`folder:060eb055-834e-4ef2-8198-e3e224a35fbe` / `folder:c4f93f9e-a710-4599-ac95-892082b03ec8`), read live `sota_bus_engine.py` HLZ multiplicity (`N = 96`, `t*(97) = 4.1905`) directly on Win32/POSIX, and align `--placement` / `--callback-to` CLI flags with `sota_bus_engine.py assign`.

## Alternatives Considered

- **Leaving `OMC_MODEL_LOW` at `haiku`:** Rejected — empirically caused `69.0%` `haiku` turn share and degraded code-search/verification quality.
- **Routing AST refactors to unauthenticated `opencode` on Noesis:** Rejected — `noesis-cc-lead` `#188(3)` proved `opencode` lacks live auth on Noesis, whereas `claude-sonnet-5-5` (`Hephaestus`-safe non-GPT) + `gpt-6.2-sol` (`codex` / `omp`) are high-quality powerhouses.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` (`23` ADRs, `0` drift)
- `uv run ruff check . && uv run ty check && uv run pytest -q && python3 scripts/merge_gate.py && gitleaks git --no-banner`
