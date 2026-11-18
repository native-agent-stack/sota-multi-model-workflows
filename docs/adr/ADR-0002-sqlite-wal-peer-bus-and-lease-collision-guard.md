# ADR-0002: Portable SQLite WAL Peer Bus & Atomic Lease Collision Guard

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** Cross-Peer State (`L1` × `L7`)
- **Evidence Grade:** E4 (Concurrent 5-Session Org Convergence Proven)
- **GitHub Evidence:** https://github.com/native-agent-stack/.github, https://github.com/aannoo/hcom, https://github.com/python/cpython
- **Revisit Trigger:** 2027-01-01

## Context and Problem Statement

Concurrent CLI and IDE agents editing local clones require sub-millisecond local lease locking without external server dependencies.

## Decision Outcome

1. **SQLite WAL Mode (`PortablePeerBus`):** Persist leases, turn-boundary messages, and immutable SHA-256 hypothesis trials in a local WAL database with TTL expiration.

## Alternatives Considered

1. **Flat JSON lockfiles:** Rejected — prone to race conditions under concurrent writes.

## Verification Witness

- `python3 -m unittest discover -s tests -v` -> `PASS`
