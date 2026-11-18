# ADR-0012: Claude Code (`cc-lead` + `OMC` v2) Central Multi-Session & Multi-Runtime Worker Orchestration

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Central Lead Orchestration, Multi-Runtime Workers & Dual-Workstation Supervision (`L1–L9` × `P0–P5` × `T0–T8`)
- **Evidence Grade:** E4 (Unit Tested, 14/14 Workflows AST-Compiled, Live `sota-cc-hub` & `run_workflow` Verified)
- **GitHub Evidence:** https://github.com/Yeachan-Heo/oh-my-claudecode, https://github.com/Yeachan-Heo/oh-my-codex, https://github.com/stablyai/orca, https://github.com/aannoo/hcom, https://github.com/native-agent-stack/sota-multi-model-workflows
- **Revisit Trigger:** `oh-my-claudecode` (`OMC`) `v6.x` release, `oh-my-codex` (`OMX`) major protocol update, or addition of a third paired Orca workstation

## Context and Problem Statement

With all `22` `native-agent-stack` repositories, the `7`-feed `sota-research-feeds.v2` point-in-time (`PIT`) DataFeed contract, and the `Mac M5 Max <-> Stationary Noesis (64c / 128 GB / RTX 4090)` Orca mesh converged, the ecosystem required a unified **Claude-Code-Central (`cc-lead`) Multi-Session & Multi-Runtime Worker Hub** so Claude Code (`claude-fable-5-2` `xhigh` + `oh-my-claudecode` `OMC v5.8.4`) remains the sovereign architectural brain (`oneModelPerConversation = True`, preserving the `600K` prompt cache) while deterministically dispatching heterogeneous runtime workers (`Codex OMX`, `Antigravity`, `OpenCode OMO`, `DeepSeek DSH`, `Pi/OMP`, `Goose`, `Muse`, `Grok`, and supervised `Orca` child worktrees).

## Decision Outcome

We introduce `src/sota_mmw/cc_lead_hub.py` (`~/.agents/bin/sota-cc-hub`), Workflow `#14` (`workflows/cc_lead_multi_runtime_workers_workflow.py`), and cross-harness skill `cc-lead-multi-runtime-orchestrator` (`v3.5.0`):

1. **Claude Code (`cc-lead`) Sovereign Central Orchestrator (`CC_LEAD_CENTRAL_CONTRACT`):**
   - Keep `claude` (`claude-fable-5-2` `xhigh`, `oh-my-claudecode@omc`) as the single central planner (`Prometheus` / `Hyperplan` / `ralplan`), `/goal` Stop-hook owner, and `Oracle` sign-off gate (`oneModelPerConversation = True`, `hephaestusForbidsGptModels = True`).
   - Inject canonical worker defaults (`OMC_RUNTIME_V2=1`, `OMC_TEAM_WORKTREE_MODE=branch`, `OMC_CODEX_DEFAULT_MODEL=gpt-6.2-astra`, `OMC_ANTIGRAVITY_DEFAULT_MODEL=gemini-4-carbon-high`, `OMC_GEMINI_DEFAULT_MODEL=gemini-4-carbon-high`, `OMC_GROK_DEFAULT_MODEL=grok-4.7`, `OMC_JEV_MAX_EFFORT=xhigh`).
2. **Five Coordinated Multi-Session & Multi-Runtime Dispatch Channels (`build_cc_lead_execution_plan`):**
   - **Channel 1 (`omc ultragoal` + Claude `/goal`):** Durable `.omc/ultragoal/plans/<plan-id>/` ledger across sessions (`G001` lease/spec preflight -> `G002` isolated worktree execution -> `G003` cross-vendor falsification).
   - **Channel 2 (`omc team` & `omc interop`):** Tmux runtime-v2 worktree swarms (`omc team "<N:agent:role,...>" --no-decompose "<brief>"`) plus interactive split-pane `Claude OMC <-> Codex OMX` (`omc interop`).
   - **Channel 3 (`omc ask` & `omx exec` / `omx mission`):** Headless cross-family specialist calls (`omc ask codex|antigravity|muse|grok`) and `oh-my-codex` (`omx exec -c model="gpt-6.2-sol"` / `omx mission`).
   - **Channel 4 (`orca orchestration worker-start`):** Supervised child-worktree DAG workers resolving `id:<uuid>` on local `Mac M5 Max` (`orca repo list --json`) or `--environment 100.110.115.22` on `Noesis 64c/RTX4090` (`NOESIS_PROVISIONED_ORCA_REPOS`), using reactive `worker_done` / `send` / `gate-create` wakeup (zero polling).
   - **Channel 5 (`OpenCode OMO` / `DSH` / `hcom` / `sota-bus`):** Non-GPT `Hephaestus` (`kimi-k3.1-pro` via `opencode`), `deepseek-v4-pro` pre-wall (`<= 2026-10-15`) batch runs via `dsh`, cross-terminal `hcom` broadcasts, and SQLite WAL `sota-bus` path-glob lease verification.
3. **Fail-Closed Safety, Pre-Wall, Non-GPT `Hephaestus` & 3-Vendor Diversity Gates (`validate_cc_lead_safety_and_invariants`):**
   - Hard-refuses (`PermissionError`) any live broker host (`paper-api.alpaca.markets` and IBKR `:4002` paper-only; live ports `4001`/`7496` refused), blocks `gpt-*` models in `Hephaestus`, enforces `study_end_date <= 2026-10-15` on pre-wall tasks, requires `>= 3` distinct `CANONICAL_MODEL_VENDORS` (`anthropic`, `openai`, `google`, `deepseek`) on Stage-3+ tasks, and blocks `--execute` worker launches when a foreign peer holds an overlapping `sota-bus` lease.

## Alternatives Considered

1. **Switch models mid-conversation inside a single Claude Code session:** Rejected — invalidates the `600K` prompt cache and creates single-context confirmation bias instead of isolated cross-vendor worker falsification.
2. **Poll worker terminals in shell sleep loops:** Rejected — consumes mail prematurely in Orca (`orca skills get orchestration`) and wastes tokens; rely strictly on reactive `worker_done` / `hcom` / `sota-bus` wakeups.

## Verification Witness

- `python3 -m unittest discover -s tests -v` (`test_cc_lead_central_orchestrator_and_workflow_14` + `14/14` workflows AST/contract verified, `PASS`).
- `python3 scripts/architecture_catalog.py --sync-manifest` + `python3 scripts/merge_gate.py` -> `PASS` (`12` GitHub-evidenced MADR 4.0 ADRs, `0` drift, `0` leaks).
- Live execution of `~/.agents/bin/sota-cc-hub status` & `run_workflow` on `cc_lead_multi_runtime_workers_workflow.py` (`PASS`).
