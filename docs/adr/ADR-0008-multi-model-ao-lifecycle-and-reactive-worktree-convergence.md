# ADR-0008: Multi-Model Agent Orchestrator (`AO`) 8-Slot Lifecycle & Reactive Worktree Convergence

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Agent Orchestration, Worktree Isolation & CI Reaction (`L3–L9` × `T0–T8`)
- **Evidence Grade:** E4 (Unit Tested, GitHub Actions Verified & Live `run_workflow` Probed)
- **GitHub Evidence:** https://github.com/ComposioHQ/agent-orchestrator, https://github.com/stablyai/orca, https://github.com/google-antigravity/antigravity-sdk-python, https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/cc-sota-harness, https://github.com/native-agent-stack/agy-sota-harness
- **Revisit Trigger:** Enrollment of a new frontier model vendor into `AO_MODEL_FAMILIES` or major `Orca` / `Antigravity` workflow protocol revision

## Context and Problem Statement

Earlier Agent Orchestrator (`AO`) practice in `northstar-ao-sandbox` (`issue -> isolated worker -> PR -> review -> explicit merge`) proved the value of frozen acceptance assertions and keyless worktree sandboxes, while `ComposioHQ/agent-orchestrator` established the 8-slot pluggable control-plane pattern (`runtime`, `orchestrator`, `workspace`, `tracker/lease`, `acceptance`, `review`, `CI reaction`, `merge`). Across our converged 22-repository `native-agent-stack` Organization and Dual-Machine `Mac M5 Max <-> Noesis 64c/RTX4090` mesh, we needed one canonical executable `AO` convergence engine (`src/sota_mmw/ao_lifecycle.py`) and workflow (`workflows/ao_multi_model_convergence_workflow.py`, `#12`) uniting all 7 installed model runtime families without installing unverified global daemon wrappers or violating single-model review correlation.

## Decision Outcome

1. **8-Slot Multi-Model `AO` Convergence Engine (`src/sota_mmw/ao_lifecycle.py`):**
   - Formalizes all 7 installed runtime families (`antigravity`, `claude-code-omc`, `openai-codex-omx`, `opencode-omo`, `pi-omp`, `goose`, `deepseek-dsh`) and enforces **strict cross-vendor reviewer diversity** (`lead_vendor != reviewer_vendor`) in `resolve_ao_multi_model_route()` and `evaluate_ao_lifecycle_gate()`.
   - Integrates Dual-Machine Orca host placement (`mac_m5_max_local` vs `noesis_64c_rtx4090` over Tailscale `100.110.115.22`) with automatic offline laptop failover.
2. **Harvested `northstar-ao-sandbox` Frozen-Assertion & Explicit-Landing Contract:**
   - Hard-blocks (`AO_HARD_BLOCKED`) any attempt that runs outside an isolated git worktree, lacks a disjoint SQLite WAL peer lease, weakens or deletes frozen acceptance assertions (`frozen_assertions_deleted_or_weakened > 0`), touches live broker endpoints, reads raw secrets, or enables paid GitHub Actions on `PRIVATE` repositories.
   - Implements bounded in-worktree reaction states (`AO_REACTION_REMEDIATION_REQUIRED` up to `max_reaction_iterations = 3`, escalating via `AO_EXHAUSTED_ESCALATE_TO_OWNER`) and emits a cryptographic `SHA-256` `qualification_receipt_sha256` (`AO_READY_FOR_EXPLICIT_LANDING`) rather than performing blind auto-merges.
3. **Self-Bootstrapping Workflow `#12` (`multi-model-ao-convergence`):**
   - Adds `workflows/ao_multi_model_convergence_workflow.py` (`REGISTRY.json` `v3.2.0`, 12 workflows), running deterministic 8-slot fleet/mesh preflight (`< 3s` in `fast_deterministic_only=True` mode) or full parallel `sota-deep-synthesizer` + `sota-falsifier` + `sota-code-verifier` audit with bounded reaction planning and `peer_bus.db` checkpointing.

## Alternatives Considered

1. **Installing standalone global `ao` npm daemon alongside Orca + Antigravity `run_workflow`:** Rejected per One-Owner-Per-Layer discipline (`ECOSYSTEM_CONVERGENCE_LOCK.json`) — duplicating worktree/process supervisors creates split-brain state against `stablyai/orca` and `peer_bus.db`; encoding the 8-slot `AO` state machine natively inside `sota-multi-model-workflows` achieves zero-daemon, deterministic parity.
2. **Same-model self-review (`lead_vendor == reviewer_vendor`):** Rejected — correlated training blind spots miss subtle lookahead, unit, and boundary bugs that cross-family review (`Google` <-> `Anthropic` <-> `OpenAI`) catches.

## Verification Witness

- `python3 scripts/architecture_catalog.py --check` -> `8 GitHub-evidenced MADR 4.0 ADRs & manifest verified (0 drift)`
- `python3 scripts/merge_gate.py` & `python3 -m unittest discover -s tests -v` -> `PASS`
