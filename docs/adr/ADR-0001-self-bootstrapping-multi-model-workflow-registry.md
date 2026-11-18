# ADR-0001: Self-Bootstrapping Multi-Model Workflow Registry (`REGISTRY.json` + `_sota_kit.py`)

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** Workflow Orchestration (`L5` × `P0–P5`)
- **Evidence Grade:** E4 (9 Workflows Runtime Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/google-antigravity/antigravity-sdk-python, https://github.com/stablyai/orca
- **Revisit Trigger:** 2027-01-01

## Context and Problem Statement

Ad-hoc multi-agent prompts forget active peer leases, duplicate trial numbers, and lose handover state across Antigravity, Claude Code, Codex, and DeepSeek sessions.

## Decision Outcome

1. **Typed JSON-Schema Registry (`workflows/REGISTRY.json`):** Register all 9 multi-model workflows with explicit `args_schema` contracts and automatic peer-bus context injection via `_sota_kit.py`.
2. **Cross-Vendor Fan-Out:** Combine native `parallel()`/`pipeline()` subagent orchestration with `orca` isolated worktrees for heterogeneous model review.

## Alternatives Considered

1. **Untyped prose subagent prompts:** Rejected — drops structured schema guarantees and peer lease awareness.

## Verification Witness

- `python3 -m unittest discover -s tests -v` -> `PASS`
