# ADR-0004: Paper-Only `PA...`/`DU...` Broker Firewall & `6–14 bps` Near-Lossless Bounds

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** Execution Risk (`L9` × `T5`)
- **Evidence Grade:** E4 (Hard Firewall Tested)
- **GitHub Evidence:** https://github.com/alpacahq/alpaca-py, https://github.com/ib-api-reloaded/ib_async
- **Revisit Trigger:** 2027-01-01

## Context and Problem Statement

Execution validators must reject live broker ports (`4001`, `7496`), non-paper account prefixes, and oversized initial stops (`> 2.00%`).

## Decision Outcome

1. **Fail-Closed `HARD_BLOCKED` Verdict:** Immediately block any manifest specifying live ports, non-`PA`/`DU` prefixes, or `max_initial_stop_pct > 2.00%`.

## Alternatives Considered

1. **Warning-only validation:** Rejected — violates zero-live-capital charter.

## Verification Witness

- `python3 -m unittest discover -s tests -v` -> `PASS`
