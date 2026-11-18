# ADR-0022: `v3.9.9` Smart Task-to-Model Suitability Router (`smart-route` / `--worker auto`), Claude Code Best Practices & 413-Star Eval Convergence

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Task Suitability Routing, Auth-Aware Dispatch & Evaluation (`L3` x `L5` x `L6` x `L8` x `L10` x `L11`)
- **Evidence Grade:** E4 (`8` Task Suitability Profiles, `sota-cc-hub smart-route` + `--worker auto`, `20/20` Unit Suite & Live `413`-Star Audit Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/cc-sota-harness, https://github.com/NVIDIA/SkillEvaluator, https://github.com/elementalsouls/Claude-BugHunter, https://github.com/parallel-web/parallel-search-evals, https://github.com/stablyai/orca
- **Revisit Trigger:** Artificial Analysis v5.x frontier model rank shift or addition of new live-authenticated runtime workers

## Context and Problem Statement

Following `ADR-0021` (separating `5` live-authenticated worker routes from auth-pending binaries), operators dispatching work from `cc-lead` (`claude-fable-5-2` `xhigh`) needed deterministic **smart task-to-model suitability routing** so arbitrary goals automatically bind to the highest-leverage model, effort tier, live-authenticated runtime, and execution surface (`local` vs `noesis` `56c`/`RTX 4090`) without manual worker guesswork or mid-session `/model` switching.

## Decision Outcome

1. **Enact `SMART_TASK_SUITABILITY_MATRIX` (`8` Profiles) & `smart_route_task(...)` in `src/sota_mmw/cc_lead_hub.py`:**
   - Route architecture/ADRs to `claude-fable-5-2` (`xhigh`, `plannotator` gate), adversarial math/security to `gpt-6.2-astra` + `claude-opus-5-5` (`Claude-BugHunter` / `trailofbits`), `<= 2026-10-15` pre-wall sweeps to `deepseek-v4-pro` on `noesis` (`56c` + `RTX 4090`), `1M`-context shelf/EDGAR/diagram/search-eval tasks to `gemini-4-carbon-high` (`antigravity` + `parallel-search-evals`), AST/codemod refactors to non-GPT `kimi-k3.1-pro` (`opencode` `OMO` `Hephaestus`), skill evals to `NVIDIA/SkillEvaluator` + `SkillOpt`, and live broker guards to `cc-lead` (`local` `singleActiveBrokerHostOnly = True`).
2. **Expose `sota-cc-hub smart-route` & `--worker auto` Default in `sota-cc-hub assign` / `sota_bus_assign_worker`:**
   - Guarantees auth-aware fallback onto `live_authenticated_worker_routes` (`cc-lead`, `codex`, `antigravity`, `opencode`, `dsh`) while preserving `oneModelPerConversation = True` (`1h`/`600K` prompt cache).

## Alternatives Considered

- **Manual `--worker` selection on every `sota-cc-hub assign` call:** Rejected — error-prone and misses automatic `Noesis` `56c` RTH offload and `Hephaestus` non-GPT constraints.

## Verification Witness

- `ruff check .` + `python -m unittest discover -s tests -v` (`20/20 PASS`) + `python scripts/architecture_catalog.py --sync-manifest` + `python scripts/merge_gate.py` + `gitleaks` (`0` leaks).
