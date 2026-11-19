# ADR-0035: Unified OSS Institutional Cockpit (`@perspective-dev@5.9.2` WASM + `Lightweight Charts` + Live Markout TCA + Paper-Only OTO/OCO Ticket)

- **Status:** Accepted
- **Date:** 2026-11-19
- **Layer:** Institutional Cockpit, Execution Telemetry, Paper-Only Order Ticket & Sovereign Wall Ergonomics (`L6` / `L9` × `T1` / `T2` / `H1`)
- **Evidence Grade:** E4 (`test_adr0035_unified_cockpit_tca_convergence.py`, `35` GitHub-Evidenced ADRs, `pytest` + `ruff` + `merge_gate.py` + `gitleaks` `0` Leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-mover-ranker, https://github.com/native-agent-stack/sota-dynamic-trail-c, https://github.com/native-agent-stack/sota-compounding-lab, https://github.com/perspective-dev/perspective, https://github.com/tradingview/lightweight-charts
- **Revisit Trigger:** Upgrade of `@perspective-dev/*` beyond `5.9.2`, cutover to Dec 6 `23/5` SIP, or addition of new paper execution venues.

## Context and Problem Statement

Prior to this decision, the trading cockpit and order-placement layer had four concrete convergence gaps:
1. `sota-mover-ranker/static/index.html` labeled its blotter as a FINOS Perspective grid while rebuilding a plain HTML `<table>` via `innerHTML`, rather than mounting local `@perspective-dev@5.9.2` WASM matching `UPSTREAM.md`.
2. Paper execution state across `:8787` (P2), `:8799` (P1), `:8797` (P3), and `:4002` (IBKR P4) lacked a single unified blotter and live Transaction Cost Analysis (TCA) markout feedback loop (`+1s/+10s/+60s/+300s` adverse-selection curves and live-vs-`hftbacktest` queue-parity reconciliation).
3. Staged presets in `:8787` were draft-only without a fail-closed paper-only 1-click OTO/OCO ticket path.
4. `sota-noesis-4k-wall.ps1` pointed Chrome wall windows at Portable Mac (`100.93.211.101`) instead of primary sovereign `127.0.0.1` on Stationary Noesis (`ADR-0041`).

## Decision Outcome

1. **Canonical Contract (`src/sota_mmw/unified_cockpit_convergence.py`, `sota.unified-cockpit-tca.v1`):** Lock the SHA-256 contract across paper-only lane allowlists (`ALPACA_PAPER_P1..P3`, `IBKR_PAPER_P4`), unconditional refusal of live ports (`4001`, `7496`, `8798`) and live broker hosts, `ADR-0022 <= 2.00%` stops, `BOATS <= 35.0 bps` overnight caps, `DF5` SEC dilution blocks, local `@perspective-dev@5.9.2` WASM asset verification, and sovereign `127.0.0.1` wall-dock auditing.
2. **Read-Only TradingView Lens:** Demote TradingView Desktop permanently to a read-only visual confirmation lens on `DISPLAY1` (zero focus steal on `120Hz` `DISPLAY2`), keeping 100% of execution, risk gating, and telemetry in the modular OSS stack.
3. **Cross-Repo Convergence:** Paired with `sota-mover-ranker` `ADR-0059`, `sota-dynamic-trail-c` `ADR-0028`, and `sota-compounding-lab` `ADR-0025`, and probed automatically by DAG `#9` (`tradingview_seamless_practice_convergence_workflow.py`).

## Alternatives Considered

- **Execute via TradingView Pine Webhooks / Chart Clicks:** Rejected — introduces webhook drops, bar-close repainting, no L2/L3 queue visibility, and fragile broker OMS state sync.
- **Commit `.wasm` Binaries Directly to Git:** Rejected — bloats git history with ~5 MB of binaries; staging into Disk `Z:` cache (`SOTA_PERSPECTIVE_CACHE_DIR`) keeps git fast while preserving 100% offline local WASM serving and graceful DOM fallback in minimal CI.

## Verification Witness

- `.venv\Scripts\python.exe scripts/architecture_catalog.py --sync-manifest` & `--check` (`35` ADRs, `0` drift), `merge_gate.py`, `ruff check`, `pytest`, and `gitleaks --staged` (`0` leaks).
