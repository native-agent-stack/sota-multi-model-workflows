# ADR-0018: v3.10.0 Unified 46-Skill Cross-Harness Enactment, 17-Workflow Registry, 14-Layer × 18-Repo ADR Router & Dual-Machine Orca Automations

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Orchestration, SOTA Skills, ADR Governance & Dual-Machine Orca Enactment (`L0–L13` × `T1–T3` × `H1–H3`)
- **Evidence Grade:** E4 (`46/46` SOTA Skills Converged Across AGY+Claude+Codex+Orca, `17/17` Native Workflows, `18`-Repo ADR Index, Dual-Machine Orca Automations & `18/18` Unit Suite Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/agy-sota-harness, https://github.com/native-agent-stack/cc-sota-harness, https://github.com/stablyai/orca, https://github.com/Yeachan-Heo/oh-my-claudecode, https://github.com/Yeachan-Heo/oh-my-codex
- **Revisit Trigger:** 2027-01-02

## Context and Problem Statement

Prior to `v3.10.0`, `29` specialized SOTA quantitative, catalyst-screening, execution-discipline, and scientific skills (`sota-quant-alpha-lab`, `sota-early-mover-goal`, `sota-mover-ranker`, and vendored scientific/security skills) were isolated inside Antigravity plugin directories rather than mounted across `~/.agents/skills`, Claude Code (`cc-lead`), Codex (`OMX`), and `orca skills installed`. Furthermore, non-Antigravity runtimes and Orca workspace recipes lacked a single deterministic CLI (`~/.agents/bin/sota-workflow`) and scheduled Orca automations (`orca automations`) binding all `46` SOTA skills, `14` harness layers (`L0–L13`), `9` Ranking DataFeeds (`DF1–DF9`), and `18` repository MADR 4.0 ADR catalogs across `Mac M5 Max`, `Stationary Noesis Win32`, and `Noesis-Carbon` WSL2.

## Decision Outcome

1. **Enact `src/sota_mmw/native_workflow_enactor.py` & `~/.agents/bin/sota-workflow` (`v3.10.0`):**
   - Converge all **`46` canonical SOTA skills** (`18` Core/Orchestration + `13` Quant/Catalyst + `7` Execution/Risk/Postmortem + `8` Vendored Scientific/Security) across `~/.agents/skills`, Antigravity, Claude Code, Codex, and Orca on all 3 surfaces.
   - Map every layer (`L0–L13`) and Dual-Machine lane (`T1–T3`, `H1–H3`) to governing SOTA skills, `DF1–DF9` PIT rules, `18`-repo MADR 4.0 ADRs (`adr_index_sha256`), and `11` multi-model runtime workers (`17` binaries, `8` frameworks, `7` vendors).
2. **Add Canonical Workflow `#17` (`sota_skills_adr_and_orca_grand_workflow.py`) & Dual-Machine Orca Automations:**
   - Advance `DEFAULT_ECOSYSTEM_SEMVER` to `"3.10.0"`, upgrade `workflows/_sota_kit.py` with `bind_workflow_skills_and_adrs()`, and provision precheck-gated Orca automations across `Mac M5 Max` and `Stationary Noesis` (`100.110.115.22`) while preserving `SINGLE_BROKER_HOST_FIREWALL`.

## Alternatives Considered

- **Keeping quant/execution skills inside Antigravity-only plugin folders:** Rejected; cross-vendor Orca workers (`claude`, `codex`, `opencode`, `omp`, `dsh`, `goose`) require identical `SKILL.md` access during supervised multi-model dispatches.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` -> `18` ADRs valid, `0` drift
- `ruff check . && ty check src scripts tests workflows/_sota_kit.py` -> `0` issues
- `python3 -m unittest discover -s tests` -> `Ran 18 tests ... OK`
- `python3 scripts/merge_gate.py && gitleaks git --staged --no-banner` -> `PASS`, `0` leaks
