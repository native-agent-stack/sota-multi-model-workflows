# ADR-0007: Ten-Workflow v3.0.0 Convergence, Deterministic Preflight & 5-Stage Org Promotion

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Workflow Orchestration & Org Governance (`L5` × `L8` × `T1–T8`)
- **Evidence Grade:** E4 (10 Workflows & Live `run_workflow` Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/native-agent-stack/native-agent-stack
- **Revisit Trigger:** Addition of a new broker execution lane or major Antigravity `run_workflow` SDK release

## Context and Problem Statement
Earlier `v1.1.0` workflow scripts accessed `args`/`WORKSPACES` without fallback helpers, delegated shell probe execution to read-only `research` subagents lacking `run_command`, referenced the superseded `edge` prototype, and lacked a dedicated 5-stage `sota-compounding-lab` + 22-repo `sota-org-doctor` workflow.

## Decision Outcome
Upgrade `workflows/_sota_kit.py` and `workflows/REGISTRY.json` to `v3.0.0`:
1. Provide crash-proof `get_workflow_args()`, `get_primary_workspace()`, and deterministic Python `run_preflight_summary()` (`sota-doctor` + `sota-org-doctor` + `ECOSYSTEM_CONVERGENCE_LOCK.json`).
2. Execute deterministic harness probes directly in Python inside `ecosystem_convergence_workflow.py` (supporting sub-2s `fast_deterministic_only` execution) and route shell verification strictly to `sota-code-verifier`.
3. Add `org_compounding_promotion_workflow.py` (`10` canonical workflows total) and keep `~/.agents/workflows/` byte-for-byte synchronized with `native-agent-stack/sota-multi-model-workflows`.

## Alternatives Considered
- Keeping separate local `~/.agents/workflows/` vs GitHub `workflows/` copies: rejected due to path and version drift.
- Running shell probes inside `type_name="research"`: rejected because `research` runs in a read-only sandbox without `run_command`.

## Verification Witness
- `python3 scripts/merge_gate.py` (`0` leaks, `7/7` MADR 4.0 ADRs, `40`-char SHA-pinned CI)
- `python3 -m unittest discover -s tests -v` (`PASS`)
- Live Antigravity `run_workflow` execution receipt
