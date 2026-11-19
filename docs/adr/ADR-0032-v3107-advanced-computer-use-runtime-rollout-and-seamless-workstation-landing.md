# ADR-0032: `v3.10.7` Dual-Machine Advanced Computer-Use Runtime Rollout & Seamless Workstation Change Landing

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Orca Runtime Rollout, Hybrid 5-Layer Computer-Use Stack (`L1–L4`) & Tiered Zero-Friction Gated-Action Landing (`L5` × `L7` × `L8` × `H1–H3`)
- **Evidence Grade:** `E4` (`sota-harness-foundation@52ce4c73` `ADR-0042` `computer_use_contract.py`, `cc-sota-harness@4590c995` `ADR-0040`, `agy-sota-harness@2f56eadf` `ADR-0033`, `32/32` MADR 4.0 ADRs, `unittest`, `ruff`, `merge_gate.py`, `gitleaks` `0` leaks)
- **GitHub Evidence:** https://github.com/native-agent-stack/sota-multi-model-workflows, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/cc-sota-harness, https://github.com/native-agent-stack/agy-sota-harness, https://github.com/stablyai/orca, https://github.com/mediar-ai/terminator, https://github.com/steipete/peekaboo, https://github.com/vercel-labs/agent-browser, https://github.com/microsoft/playwright-mcp, https://github.com/HKUDS/CLI-Anything, https://github.com/simular-ai/Agent-S, https://github.com/trycua/cua, https://github.com/microsoft/UFO
- **Revisit Trigger:** `2026-12-06` `23/5` Consolidated SIP cutover or upgrade of `orca computer` / `terminator` / `peekaboo` runtimes

## Context and Problem Statement

`sota-harness-foundation@52ce4c73` (`ADR-0042`), `cc-sota-harness@4590c995` (`ADR-0040`), and `agy-sota-harness@2f56eadf` (`ADR-0033`) established the 5-layer computer-use escalation contract and 3-tier permission model (`OWNER_ZERO_FRICTION_SEAMLESS`, `EXPLICIT_HUMAN_TRUST_GATE`, `FAIL_CLOSED_HARD_INVARIANT`). Live inspection on Stationary `Noesis` (`100.110.115.22`) confirmed that `orca-computer-use-windows` (`v1.0.0`) runs `input.background=false` and that external SOTA computer-use binaries (`mediar-ai/terminator`, `@playwright/cli`, `HKUDS/CLI-Anything`) are not yet installed on the workstation host. To land future cross-repo changes seamlessly without focus theft, terminal clutter, or manual prompt friction, multi-model Orca orchestration requires a concrete dual-machine runtime rollout specification.

## Decision Outcome

1. **Standardize Concrete Dual-Machine Runtime Rollout Across `L1–L4` (`ADR-0042` Contract):**
   - **L1 (Zero-Pixel-Tax Default):** Execute workspace sync, peer messaging, and state reconciliation via `:8792` Zero-Terminal RPC (`sota-workstation`), `orca` CLI (`--json`), `sota-bus`, `hcom`, and `HKUDS/CLI-Anything`-style stateful JSON CLI wrappers.
   - **L2 (Focus-Preserving OS Accessibility — Closing Win32 `input.background=false`):** Wire `mediar-ai/terminator` (`terminator-mcp-agent`) on Stationary `Noesis` (`win32`) alongside `orca-computer-use-windows`, and `steipete/peekaboo` on `Portable Mac M5 Max` (`darwin`) alongside `orca-computer-use-macos` (`input.background=true`). Use `trycua/cua` (Lume/gVisor) or `e2b-dev/desktop` when isolated sandbox testing is required, following `microsoft/UFO` (`UFO²`/`UFO³`) hybrid GUI+OS-API orchestration.
   - **L3 (Compact Browser CDP Refs):** Standardize `vercel-labs/agent-browser` (Rust CDP `@eN` element refs), `@playwright/cli` (`microsoft/playwright-mcp`), and Orca's built-in browser (`orca snapshot`) across both Mac and Noesis Win32/`Noesis-Carbon` WSL2.
   - **L4 (`Agent-S` S4 Distillation & VLM Fallback):** Restrict raw pixel VLM actions (`UI-TARS-2`, `OpenCUA`) strictly to unexposed UI surfaces, and distill any recurring GUI landing or configuration flow into idempotent CLI/config sync scripts (`sync-all-8-runtimes.py`, `sync_runtime_hygiene.py`).
2. **Seamless Gated-Action Landing Under Three-Tier Governance:**
   - **Zero-Friction Autonomous Landing (`OWNER_ZERO_FRICTION_SEAMLESS`):** Owner-sanctioned non-destructive dev, Orca, multi-runtime, browser, and paper-lane updates land end-to-end via documented native configs/CLIs/RPC/UIA with zero manual prompt friction.
   - **Explicit Human Trust Preservation (`EXPLICIT_HUMAN_TRUST_GATE`):** Platform trust dialogs (e.g., Orca Automations `97bd1f5e` / `6d7eba60` hook trust clicks) and OS UAC/TCC prompts surface cleanly for 1-click owner confirmation and are never bypassed.
   - **Fail-Closed Hard Invariants (`FAIL_CLOSED_HARD_INVARIANT`):** Live-capital endpoints (`:8798`, live IBKR `:4001`/`:7496`, live window opener, `PreToolUse` `ask` approval), credential/Keychain/`.env` isolation, immutable `~/Documents/upstream/` & closed repos, `singleActiveBrokerHostOnly=true`, `ADR-0022 <= 2.00%`, and untouched `sextant` remain unconditionally enforced.

## Alternatives Considered

- **Relying Solely on Foreground `orca-computer-use-windows` UIA:** Rejected — `input.background=false` steals focus on Stationary `Noesis` during concurrent human or multi-agent work; pairing with `mediar-ai/terminator` closes that gap.
- **Allowing Autonomous Bypass of Platform Hook/Trust Prompts:** Rejected — violates explicit human trust boundaries codified in `ADR-0042`.

## Verification Witness

- `uv run python scripts/architecture_catalog.py --sync-manifest && uv run python scripts/architecture_catalog.py --check` (`32` GitHub-evidenced MADR 4.0 ADRs, `0` drift).
- `uv run python -m unittest discover -s tests -v && ruff check . && uv run python scripts/merge_gate.py && gitleaks git --no-banner` (`PASS`, `0` leaks).
