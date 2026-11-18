# ADR-0016: v3.9.0 Full-Landscape SOTA Layer, Dual-Machine Orca Lane Hubs v2 (`T1–T5` × `H0–H7`), Empirical Pre-Wall Lake SHA-256 & RTH Contention Shield

- **Status:** Accepted
- **Date:** 2026-11-18
- **Layer:** Multi-Model Orchestration, Dual-Machine Orca Lanes & Quantitative Provenance (`L0–L13` × `P0–P5` × `T1–T5` × `H0–H7`)
- **Evidence Grade:** E4 (`16/16` Workflows, `8` Frameworks / `17` Binaries / `11` Workers / `7` Vendors, `64`-Thread `Noesis-Carbon` Pre-Wall Lake SHA-256 & Unit Suite Verified)
- **GitHub Evidence:** https://github.com/stablyai/orca, https://github.com/ComposioHQ/agent-orchestrator, https://github.com/Yeachan-Heo/oh-my-claudecode, https://github.com/Yeachan-Heo/oh-my-codex, https://github.com/native-agent-stack/sota-harness-foundation, https://github.com/native-agent-stack/sota-multi-model-workflows
- **Revisit Trigger:** 2027-01-02

## Context and Problem Statement

Following `ADR-0014` (`sota-dual-machine-lanes.v1`) and `ADR-0015` (`sota-ranking-datafeeds.v3.8` `DF1..DF9` and two-track compounding versioning), three cross-repo synchronization gaps remained:
1. `compounding_versioning.py` used a synthetic suffix for `DEFAULT_PREWALL_LAKE_SHA256` instead of the empirically verified `64`-hex SHA-256 (`a253421e873441740d5d4b410d993cfa7345fe34b88ec4ab7f4eecd537b3f234`) of the `1.57 GB` `<= 2026-10-15` pre-wall lake seeded onto `Z:/sota-data/prewall-lake` (`/mnt/z/sota-data/prewall-lake`).
2. `dual_machine_lanes.py` referenced `sota-research-feeds.v2` and `15` workflows rather than `sota-ranking-datafeeds.v3.8` (`DF1..DF9`) and `16` workflows, lacked the `T1..T5` × `H0..H7` stage/layer sub-lane bijection with `sota-harness-foundation`, and lacked an explicit `active_broker_host_shield` offloading heavy sweeps to `Noesis` during live `09:30–16:00 ET` RTH execution on `portable_mac_m5_max`.
3. Non-Git Orca `--kind folder` hubs (`trading-lanes` and `harness-lanes`) needed deterministic `sota-orca-lane-hub.v2` generation (`LANE_MANIFEST.json`, `orca.yaml`, `README.md`) across all 3 execution surfaces.

## Decision Outcome

1. **Anchor `DEFAULT_PREWALL_LAKE_SHA256` & Advance Ecosystem Version to `3.9.0`:**
   - Pin `DEFAULT_PREWALL_LAKE_SHA256 = "a253421e873441740d5d4b410d993cfa7345fe34b88ec4ab7f4eecd537b3f234"` in `src/sota_mmw/compounding_versioning.py` (`29,500` ORB Parquet files + `6` SEC/FINRA PIT tables + `2024–2026` universe strictly `<= 2026-10-15`) and advance `DEFAULT_ECOSYSTEM_SEMVER` to `"3.9.0"`.
2. **Upgrade `dual_machine_lanes.py` to `sota-dual-machine-lanes.v2` & `sota-orca-lane-hub.v2`:**
   - Bind `sota-ranking-datafeeds.v3.8` (`DF1..DF9`), `16` workflows, `ComposioHQ/agent-orchestrator` (`AO` 8-slot convergence), `STAGE_AND_LAYER_SUBLANES` (`T1..T5` × `H0..H7`), `7` model vendors (`11` heterogeneous workers, `17` binaries, `8` SOTA orchestration frameworks), `active_broker_host_shield`, and `sota-lanes sync-hubs --json`.

## Alternatives Considered

1. **Maintain separate `T1..T3` and `T1..T5` lane schemas without bijection:** Rejected — causes routing drift between `sota-multi-model-workflows` and `sota-harness-foundation`.
2. **Run docked `14`-thread test/pre-wall sweeps on `Mac M5 Max` during live `09:30–16:00 ET` RTH trading:** Rejected — `active_broker_host_shield` routes heavy sweeps to `56`-thread `Noesis` / `Noesis-Carbon` while preserving sub-50ms quote/trail latency on `:8787` and `:8799`.

## Verification Witness

- `python3 scripts/architecture_catalog.py --sync-manifest && python3 scripts/architecture_catalog.py --check` (`16` GitHub-evidenced MADR 4.0 ADRs, `0` drift).
- `ruff check .`, `ty check`, `python3 -m unittest discover -s tests -p "test_*.py"`, `python3 scripts/merge_gate.py`, and `gitleaks detect --no-git --no-banner` (`0` leaks).
