# ADR-0033: `v3.10.8` Orca SOTA Worker Defaults, Red-Team BugHunter, 4-Tier SkillEvaluator, `60`-Skill & `415+8`-Starred Convergence Loop

- **Status:** Accepted
- **Date:** 2026-11-19
- **Layer:** Multi-Model Orca Runtime Defaults, Red-Team & Skill Quality Gates (`L0–L13` × `P0–P5` × `T1–T5` × `H0–H7`)
- **Evidence Grade:** E4 (`ORCA_RUNTIME_WORKER_DEFAULTS`, Workflow `#21` `redteam-skilleval-convergence-loop`, `60/60` `SkillEvaluator` PASS, `415` starred + `8` beyond-starred convergence, `pytest` + `ruff` + `merge_gate.py` + `gitleaks` `0` Leaks)
- **GitHub Evidence:** https://github.com/NVIDIA/SkillEvaluator, https://github.com/elementalsouls/Claude-BugHunter, https://github.com/Tencent/LoopForge, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/stablyai/orca
- **Revisit Trigger:** Addition of new active runtime workers or changes to `21` canonical workflows / `15` dual-machine Orca automations

## Context and Problem Statement

While `v3.10.7` established the `5`-layer computer-use escalation stack (`ADR-0032`) and `10` domain lane leads (`ADR-0030`), three structural gaps remained in multi-runtime Orca operations and research convergence:
1. **Unpinned Orca Worker Defaults & Residual Retired Entries:** `cc_lead_hub.py` still carried `grok-regime`, `goose-autonomous`, and `OMC_GROK_DEFAULT_MODEL`, routed `deepseek-dsh` to `opencode` rather than native `dsh`, omitted first-class `antigravity-neon` (`gemini-4-neon-xhigh`), `claude-fable-lead`, and `pi-worker` entries, and lacked an authoritative `ORCA_RUNTIME_WORKER_DEFAULTS` table across all `9` active Orca agents (`claude`, `codex`, `antigravity`, `gemini`, `opencode`, `dsh`, `omp`, `pi`, `muse`).
2. **Untested Skill & Red-Team Loop Execution:** Canonical skills expanded to `60` (`sota-redteam-bughunter`, `sota-skill-evaluator`, `sota-loopforge-convergence`), requiring a unified schema-typed workflow (`#21`) binding `sota-harness-foundation` `ADR-0043` (`SkillEvaluator` + `Claude-BugHunter`) into the `run_workflow` and `sota-workflow run` DAG.
3. **Starred-Repo Convergence Drift (`413+6` -> `415+8`):** Newly starred frameworks (`rlaope/oh-my-hermes`, `alvinunreal/oh-my-opencode-slim`, `Tencent/LoopForge`, `NVIDIA/auto-ontology`, `NVIDIA/OpenShell`, `backnotprop/plannotator`, `Nutlope/hallmark`, `mvschwarz/openrig`, `xerj-org/xerj`, `opendatalab/MinerU`) needed formal integration into `STARRED_AND_BEYOND_SOTA_RESEARCH_STACK`.

## Decision Outcome

1. **Publish `ORCA_RUNTIME_WORKER_DEFAULTS` & Cleanse Active Roster (`src/sota_mmw/cc_lead_hub.py`):**
   - Pin all `9` active Orca agent IDs to exact frontier non-stale defaults (`claude-fable-5-2` `xhigh`, `gpt-6.2-astra` `xhigh`, `gemini-4-neon-xhigh` / `gemini-4-neon-high` + `gemini-4-carbon-high`, `anthropic/claude-sonnet-5-5`, `deepseek-flash`, `@worker`, `openai-codex/gpt-6.2-sol`, `muse-spark-1.3`).
   - Remove `grok-regime`, `goose-autonomous`, and `OMC_GROK_DEFAULT_MODEL` from active rosters/envs while tracking `RETIRED_WORKER_KEYS` explicitly; route `deepseek-dsh` natively to `orca_agent="dsh"`.
2. **Add Workflow `#21` (`redteam-skilleval-convergence-loop`) & Update `60`-Skill / `415+8`-Starred Contracts:**
   - Register `workflows/redteam_skilleval_and_convergence_loop_workflow.py` in `workflows/REGISTRY.json` (`21` workflows) and `SOTA_WORKFLOW_MANIFEST.json` (`v3.10.8`).
   - Update `research_convergence_contract.py` (`owner_starred_total_audited: 415`, `8` beyond-starred additions, Stationary Noesis Primary `S7` naming) and `native_workflow_enactor.py` (`CANONICAL_60_SOTA_SKILLS`, `21` workflows).

## Alternatives Considered

- **Leaving Orca Automations & Worker Flags Implicit via CLI Profiles Only:** Rejected — causes non-deterministic model drift and stale `dispatch_failed` runs when automations inherit legacy settings.
- **Maintaining `grok-regime`/`goose-autonomous` Inside Active Roster:** Rejected — violates `v3.10.6+` zero-retired-runtime hygiene and inflates runtime fleet failures.

## Verification Witness

- `uv run ruff check . && uv run ruff format --check .` (`0` errors).
- `uv run pytest -v` (`100%` pass including `test_v3108_adr0033_orca_worker_defaults_60_skills_and_workflow_21`).
- `uv run python scripts/architecture_catalog.py --sync-manifest && uv run python scripts/architecture_catalog.py --check` (`33` ADRs, `0` drift).
- `uv run python scripts/merge_gate.py` & `gitleaks git --staged` (`0` leaks).
