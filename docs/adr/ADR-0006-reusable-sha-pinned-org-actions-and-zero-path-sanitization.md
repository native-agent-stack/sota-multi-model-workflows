# ADR-0006: Reusable SHA-Pinned Organization CI & Home-Path Sanitization

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** Supply-Chain & Privacy (`L9`)
- **Evidence Grade:** E4 (GitHub Actions Public Runner Verified)
- **GitHub Evidence:** https://github.com/native-agent-stack/.github, https://github.com/step-security/harden-runner, https://github.com/actions/checkout
- **Revisit Trigger:** 2027-01-01

## Context and Problem Statement

Public workflow repositories must never leak developer home paths, account identifiers, or unpinned third-party CI actions.

## Decision Outcome

1. **Automated Path & Secret Gate:** Enforce `scripts/merge_gate.py` plus `native-agent-stack/.github` reusable SHA-pinned CI on every commit.

## Alternatives Considered

1. **Manual pre-push inspection:** Rejected — error-prone across multi-agent sessions.

## Verification Witness

- `python3 scripts/merge_gate.py` -> `PASS`
