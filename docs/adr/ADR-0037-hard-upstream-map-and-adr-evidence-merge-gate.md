# ADR-0037: Fail-Closed `upstream-map.toml`, 18-Pin Shelf Parity & ADR-Evidence Enforcement in `scripts/merge_gate.py`

- **Status:** Accepted
- **Date:** 2026-11-20
- **Layer:** Workflow Repository Provenance & Hard Upstream-Source Firewall (`PROTECTIVE_FILTER_OR_GOVERNANCE`, `standalone_alpha_claim = False`)
- **Evidence Grade:** E4 (`scripts/merge_gate.py`, `upstream-map.toml`, `tests/test_upstream_map_gate.py`, `pytest`, `ruff`, `architecture_catalog.py --check`, `merge_gate.py`, `gitleaks 0`)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-upstream-shelf-lock
- **Revisit Trigger:** Addition of any new module under `src/sota_mmw/`, `workflows/`, or `scripts/`.

## Context and Problem Statement

An ecosystem-wide provenance audit (`2026-11-20`) found that although `sota-multi-model-workflows` tracked an `upstream-map.toml`, `scripts/merge_gate.py` did not mechanically validate it. As a result, six modules added under `src/sota_mmw/` (`boats_23x5_cutover_drill.py`, `merit_promotion_harness.py`, `native_workflow_enactor.py`, `peer_bus_mcp_server.py`, `symbol_ranking_datafeeds.py`, `unified_cockpit_convergence.py`) drifted unmapped without failing CI or pre-push checks.

## Decision Outcome

1. **Upgrade `scripts/merge_gate.py` (`verify_upstream_map` + `verify_adr_evidence`):**
   - Mechanically verify every tracked file under `src/`, `workflows/`, `scripts/`, and `orca.yaml` maps to an entry in `upstream-map.toml` (`how in {"install", "integrate", "build-on"}`, non-empty `feature` & `why`) referencing `UPSTREAM.md`, rejecting unused patterns and banned low-quality libraries.
   - Verify exact 40-char SHA parity & clean tree on all 18 read-only shelf clones in `~/Documents/upstream/` when present.
   - Verify every MADR 4.0 ADR in `docs/adr/ADR-*.md` includes verifiable evidence (`Evidence` / `Verification Witness` / `Confirmation`).
2. **Synchronize `upstream-map.toml`** across 100% of tracked implementation files and pin `[shelf_pins]` to the 18 canonical `PINS_LOCK.json` SHAs.

## Alternatives Considered

- **Keep `upstream-map.toml` as an unchecked documentation artifact:** Rejected — six modules drifted unmapped under unchecked prose rules; fail-closed mechanical gating in `scripts/merge_gate.py` closes the loophole permanently.

## Verification Witness

- `pytest -q` (including `tests/test_upstream_map_gate.py` testing real repo pass + orphan/banned/missing-ADR-evidence failure cases).
- `python scripts/merge_gate.py` -> `PASS`.
- `python scripts/architecture_catalog.py --check` -> `37/37` ADRs, `0` drift.
- `ruff check .` & `gitleaks protect --staged --no-banner` (`0` leaks).
