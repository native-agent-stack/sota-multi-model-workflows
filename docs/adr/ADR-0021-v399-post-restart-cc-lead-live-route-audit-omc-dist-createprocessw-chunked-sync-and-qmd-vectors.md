# ADR-0021: v3.9.9 Post-Restart CC-Lead Live-Route Audit, OMC 5.8.6 Compiled dist/ Callbacks, CreateProcessW Chunked Sync & 2,325-Vector qmd Embed

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Runtime Routing, Memory & Cross-Workstation Automation (`L3` x `L5` x `L7` x `L10` x `L11` x `L13`)
- **Evidence Grade:** E4 (Live `cc-lead` Route Smoke `#173`/`#179`/`#180`, Compiled OMC `5.8.6` `dist/` Callback `#178`, `2,325` `qmd` Vectors & `24h` Chunked E2EE Sync Verified)
- **GitHub Evidence:** https://github.com/stablyai/orca, https://github.com/Yeachan-Heo/oh-my-claudecode, https://github.com/tobi/qmd, https://github.com/can1357/oh-my-pi, https://github.com/native-agent-stack/sota-multi-model-workflows
- **Revisit Trigger:** 45 days or upon user credential provisioning for pending external CLI providers

## Context and Problem Statement

Live cross-agent execution (`cc-lead` `Msg #173`, `#179`, `#180` + `f2693e3b` `24h` sync audit) uncovered five concrete empirical gaps in `v3.9.8` (`ADR-0020`) that binary-presence probes and mocked unit tests could not catch:
1. **Binary Presence vs Live Authenticated Route Parity (`cc-lead #180`):** `5` worker routes pass live reply-OK smoke (`cc-lead`, `omc ask codex` / `omx exec gpt-6.2-astra`, `omc ask antigravity`, `opencode run`, `dsh headless`), whereas `omc ask gemini` lacks `~/.gemini/settings.json` auth (causing `omc team` specs with `1:gemini:verifier` to drop a member) and `muse`/`grok`/`goose`/`pi`/`omp-direct`/`ccr` require user credentials/billing.
2. **CLI Flag Drift in `native_workflow_enactor.py` (`cc-lead #179`):** `dsh run --profile quant-prewall --prompt` (`select a profile only once`), `omp --model @worker --effort high` (`omp` CLI uses `--thinking=high -p`), and `opencode run -m moonshot/kimi-k3.1-pro` failed verbatim on Mac; `workflows/multi_model_omc_memory_assign_workflow.py` also needed keyword-only `kit.record_workflow_run(repo=repo, ...)` parity.
3. **Uncompiled `oh-my-claudecode/5.8.6/dist/` (`cc-lead #173`):** All 16 `OMC` hook scripts silently no-oped until `bun install && npm run build` compiled `dist/hooks/session-end/callbacks.js` + `native/contained-fs-darwin-arm64.node`, and per-turn `--event Stop` receipts were added to `peer_hook_adapter.py`.
4. **`qmd` BM25 Query Truncation & Unembedded Vectors (`cc-lead #173`):** Sentence queries cut mid-word returned `No results found`; keyword tokenization + `qmd embed` (`2,325` vectors across `580` docs) enabled real hybrid retrieval.
5. **Win32 `CreateProcessW` `32,767`-Char Ceiling (`f2693e3b`):** `--since-hours 24.0` exceeded `pwsh.exe --command` limits (`~127 KB` Base64); `sota-workstation v2.4.0` chunks `>16 KB` payloads via `$env:TEMP\sota_ephem.b64`.

## Decision Outcome

We enact `v3.9.9`:
1. Separate `live_authenticated_worker_routes` (`cc-lead`, `codex`, `antigravity`, `opencode`, `dsh`) from `binary_present_user_auth_pending_routes` in `CC_LEAD_CENTRAL_CONTRACT`, route `omc_team_spec` verifier slots to `1:antigravity:verifier`, and fix `native_workflow_enactor.py` CLI invocations (`dsh headless`, `omp --model @worker --thinking=high -p`, `opencode run`).
2. Commit keyword-argument `kit.record_workflow_run(repo=repo, ...)` in `workflows/multi_model_omc_memory_assign_workflow.py` (`#18`) and bump `DEFAULT_ECOSYSTEM_SEMVER = "3.9.9"`.
3. Pair with host-level compiled `OMC 5.8.6 dist/` (`Msg #178` verified), `sota-auto-sync` (`com.sota.3surface-memory-qmd-sync` LaunchAgent), `2,325`-vector `qmd` index, and `sota-workstation v2.4.0` chunked `CreateProcessW`-safe sync.

## Alternatives Considered

- **Treating `shutil.which(bin)` as sufficient proof of live multi-model execution:** Rejected — `cc-lead #180` proved binary presence masks unauthenticated or flag-drifted routes (`E4` requires live smoke separation).

## Verification Witness

- `ruff check . && ty check src scripts tests workflows/_sota_kit.py` -> `All checks passed!`
- `uv run pytest -q` -> `19/19 PASS`
- `python3 scripts/architecture_catalog.py --check && python3 scripts/merge_gate.py && gitleaks git --staged --no-banner` -> `PASS` (`21` ADRs, `0` leaks)
