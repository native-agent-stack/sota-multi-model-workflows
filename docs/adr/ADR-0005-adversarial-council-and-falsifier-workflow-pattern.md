# ADR-0005: Three-Seat Deliberation Council & Adversarial Falsifier Workflow Pattern

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** Epistemic Falsification (`L5` × `L12`)
- **Evidence Grade:** E3 (Empirical Workflow Audits)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/.github
- **Revisit Trigger:** 2027-01-01

## Context and Problem Statement

Single-agent trajectories exhibit confirmation bias when evaluating alpha factors or architectural trade-offs.

## Decision Outcome

1. **Parallel Synthesis + Red-Team Falsification:** Pair `sota-deep-synthesizer` and `sota-rd-proposer` with an independent `sota-falsifier` red-team stage prior to code verification (`sota-code-verifier`).

## Alternatives Considered

1. **Single-pass self-review:** Rejected — misses subtle lookahead, fee-tier, and macOS TCC edge cases.

## Verification Witness

- `python3 -m unittest discover -s tests -v` -> `PASS`
