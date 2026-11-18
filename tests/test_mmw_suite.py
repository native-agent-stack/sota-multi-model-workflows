from __future__ import annotations

import ast
import asyncio
import dataclasses
import hashlib
import http.server
import io
import json
import statistics
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts import merge_gate
from sota_mmw.ao_lifecycle import (
    AO_MODEL_FAMILIES,
    AO_PLUGGABLE_SLOTS,
    CONCRETE_VENDORS,
    AOLifecycleAttempt,
    count_python_test_assertions,
    derive_workstation_mesh_state,
    detect_disjoint_peer_lease,
    detect_isolated_worktree,
    evaluate_ao_lifecycle_gate,
    qualify_ao_lifecycle_attempt,
    resolve_ao_multi_model_route,
)
from sota_mmw.cc_lead_hub import (
    CC_LEAD_CENTRAL_CONTRACT,
    NOESIS_PROVISIONED_ORCA_REPOS,
    RUNTIME_WORKER_ROSTER,
    TASK_CLASS_PROFILES,
    CCLeadPlanRequest,
    build_cc_lead_execution_plan,
)
from sota_mmw.compounding_versioning import (
    CANONICAL_RANKING_DATAFEEDS_V38,
    DEFAULT_PREWALL_LAKE_SHA256,
    RANKING_DATAFEEDS_SCHEMA_VERSION,
    UPSTREAM_SHELF_PINS_18,
    CompoundingVersionRecord,
    build_compounding_version_status,
    compute_ranking_datafeed_contract_sha256,
    compute_upstream_shelf_tree_sha256,
    verify_compounding_version_transition,
)
from sota_mmw.dual_machine_lanes import (
    DUAL_MACHINE_SURFACES,
    HARNESS_LANES,
    ORCA_LANE_HUBS,
    ORCHESTRATION_FRAMEWORKS_MATRIX,
    REPO_LANE_INDEX,
    TRADING_LANES,
    build_lanes_overview,
    resolve_dual_machine_lane_plan,
)
from sota_mmw.peer_bus_schema import PortablePeerBus
from sota_mmw.promotion_gate import (
    StrategyCandidateManifest,
    compute_hlz_t_hurdle,
    evaluate_promotion_gate,
)
from sota_mmw.research_convergence_contract import (
    CANONICAL_DATAFEEDS,
    CANONICAL_RESEARCH_MCP_TOOLS,
    CANONICAL_STRATEGY_ARCHETYPES,
    RESEARCH_FEEDS_SCHEMA_VERSION,
    verify_research_convergence_claim,
)
from workflows import _sota_kit as kit

sys.modules.setdefault("_sota_kit", kit)


class TestMultiModelWorkflows(unittest.TestCase):
    def test_promotion_gate_approves_valid_and_blocks_live_or_postwall(self) -> None:
        self.assertGreaterEqual(compute_hlz_t_hurdle(82), 4.10)
        good = StrategyCandidateManifest(
            strategy_id="SOTA_EARLY_IGNITION_V6",
            study_end_date="2026-10-15",
            events_count=420,
            distinct_dates=75,
            t_stat_date_clustered=4.65,
            trial_n=82,
            dsr_probability=0.98,
            cpcv_positive_fold_pct=86.7,
            net_expectancy_1x_bps=18.4,
            net_expectancy_2x_impact_bps=9.2,
            sim_engine_verified=True,
            max_initial_stop_pct=1.50,
            mega_cap_scratch_bps=9.5,
            broker_lane="ALPACA_PAPER",
            account_prefix="PA",
        )
        res = evaluate_promotion_gate(good)
        self.assertTrue(res["approved_for_autonomous_alpha"])
        self.assertEqual(res["stage_reached"], "STAGE_4_PAPER_EXECUTION_APPROVED")

        live_port = dataclasses.replace(good, broker_lane="IBKR_PAPER", account_prefix="DU", broker_port=7496)
        r_bad = evaluate_promotion_gate(live_port)
        self.assertFalse(r_bad["hard_safety_verified"])
        self.assertEqual(r_bad["stage_reached"], "HARD_BLOCKED")

        post_wall = dataclasses.replace(good, study_end_date="2026-11-01")
        self.assertEqual(evaluate_promotion_gate(post_wall)["stage_reached"], "HARD_BLOCKED")

    def test_portable_peer_bus_wal_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bus = PortablePeerBus(Path(td) / "peer_bus.db")
            c = bus.claim_lease("sota-mmw", "agy", "s1", ["src/*"], "unit test")
            self.assertTrue(c["claimed"])
            mid = bus.send_message("agy:s1", "*", "sota-mmw", "hello peers")
            self.assertGreaterEqual(mid, 1)
            h = bus.preregister_hypothesis("sota-mmw", "H01", "locked spec <=2026-10-15")
            self.assertEqual(h["trial_n"], 1)
            self.assertTrue(bus.release_lease("sota-mmw", "s1")["released"])

    def test_workflow_registry_ast_and_merge_gate(self) -> None:
        reg = json.loads((ROOT / "workflows" / "REGISTRY.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "SOTA_WORKFLOW_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(reg["version"], "3.10.0")
        self.assertEqual(manifest["schemaVersion"], "3.10.0")
        self.assertEqual(len(reg["workflows"]), 20)
        self.assertEqual(manifest["workflowCount"], 20)
        ids = [w["id"] for w in reg["workflows"]]
        self.assertEqual(ids, manifest["workflows"])
        self.assertIn("multi-model-ao-convergence", ids)
        self.assertIn("dual-workstation-orca", ids)
        self.assertIn("research-convergence-landing", ids)
        self.assertIn("cc-lead-multi-runtime-workers", ids)
        self.assertIn("dual-machine-trading-and-harness-lanes", ids)
        self.assertIn("compounding-versioning-and-ranking-adr", ids)
        self.assertIn("sota-skills-adr-and-orca-grand-workflow", ids)
        self.assertIn("multi-model-omc-memory-assign", ids)
        self.assertIn("orca-lead-e2e-research-convergence", ids)
        self.assertIn("grand-merit-harness", ids)

        expected_keys = {"id", "script_path", "skill", "agents", "args_schema", "when_to_use"}
        top_level_wf_files = sorted(p for p in (ROOT / "workflows").glob("*.py") if not p.name.startswith("_"))
        self.assertEqual(len(top_level_wf_files), 20)

        for wf in reg["workflows"]:
            self.assertEqual(set(wf.keys()), expected_keys)
            script_name = Path(wf["script_path"]).name
            local_script = ROOT / "workflows" / script_name
            self.assertTrue(local_script.is_file(), msg=f"Missing workflow script: {script_name}")
            src = local_script.read_text(encoding="utf-8")
            self.assertIn("_sota_kit", src)
            self.assertIn(
                "load_research_convergence_context",
                src,
                msg=f"{script_name} missing explicit load_research_convergence_context() call",
            )
            self.assertIn(
                "sota-research-feeds.v2",
                src,
                msg=f"{script_name} missing explicit sota-research-feeds.v2 contract reference",
            )
            self.assertIn(
                "PHILOSOPHY_ONLY",
                src,
                msg=f"{script_name} missing explicit PHILOSOPHY_ONLY sibling-repo authority",
            )
            compile(src, "<workflow>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
            tree = ast.parse(src)
            uses_dunder_file = any(isinstance(node, ast.Name) and node.id == "__file__" for node in ast.walk(tree))
            if uses_dunder_file:
                self.assertIn(
                    '"__file__" in globals()',
                    src,
                    msg=f"{script_name} uses __file__ without guarding '__file__' in globals() for <workflow> runtime",
                )

        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "merge_gate.py")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr or r.stdout)

    def test_multi_model_ao_lifecycle_routing_and_frozen_assertion_gate(self) -> None:
        self.assertEqual(len(AO_PLUGGABLE_SLOTS), 8)
        self.assertEqual(len(AO_MODEL_FAMILIES), 7)

        r_gpu = resolve_ao_multi_model_route("combinatorial_gpu_sweep", "dual_mesh_docked")
        self.assertEqual(r_gpu.workstation_host, "noesis_64c_rtx4090")
        self.assertNotEqual(r_gpu.lead_vendor, r_gpu.reviewer_vendor)

        r_offline = resolve_ao_multi_model_route("combinatorial_gpu_sweep", "portable_autonomous_battery")
        self.assertEqual(r_offline.workstation_host, "mac_m5_max_local")

        valid_ao = AOLifecycleAttempt(
            task_id="ao-001",
            repo="sota-multi-model-workflows",
            head_commit_sha="82f31a4ce67da77f6c243f8b0c2e61f643bd44f5",
            lead_harness="antigravity",
            reviewer_harness="claude-code-omc",
            isolated_worktree=True,
            disjoint_peer_lease=True,
            upstream_sha_cited=True,
            tests_passed=14,
            tests_failed=0,
        )
        out_ok = evaluate_ao_lifecycle_gate(valid_ao)
        self.assertTrue(out_ok["ready_for_explicit_landing"])
        self.assertEqual(out_ok["disposition"], "AO_READY_FOR_EXPLICIT_LANDING")
        self.assertEqual(len(out_ok["qualification_receipt_sha256"]), 64)

        # Weakening frozen assertions or same-vendor self-review must hard-block
        weakened = dataclasses.replace(valid_ao, frozen_assertions_deleted_or_weakened=1)
        self.assertEqual(evaluate_ao_lifecycle_gate(weakened)["disposition"], "AO_HARD_BLOCKED")
        same_vendor = dataclasses.replace(valid_ao, reviewer_harness="antigravity")
        self.assertEqual(evaluate_ao_lifecycle_gate(same_vendor)["disposition"], "AO_HARD_BLOCKED")

        # Actionable P0/P1 finding triggers bounded reaction loop, then escalates after max iterations
        remediable = dataclasses.replace(valid_ao, p0_p1_open_findings=1, reaction_iteration=1)
        self.assertEqual(evaluate_ao_lifecycle_gate(remediable)["disposition"], "AO_REACTION_REMEDIATION_REQUIRED")
        exhausted = dataclasses.replace(valid_ao, p0_p1_open_findings=1, reaction_iteration=3)
        self.assertEqual(evaluate_ao_lifecycle_gate(exhausted)["disposition"], "AO_EXHAUSTED_ESCALATE_TO_OWNER")

    def test_research_convergence_contract_and_claim_verifier(self) -> None:
        self.assertEqual(len(CANONICAL_DATAFEEDS), 7)
        self.assertEqual(
            set(CANONICAL_DATAFEEDS.keys()),
            {
                "alpaca_sip",
                "alpaca_boats",
                "alpaca_raw_vs_all_adjustment",
                "sec_edgar_acceptance_datetime",
                "finra_regsho_cnmsshvol_t1",
                "corporate_actions_split_guard",
                "ibkr_paper_4002_l1",
            },
        )
        self.assertEqual(CANONICAL_DATAFEEDS["alpaca_boats"]["cutover_date"], "2026-12-06")
        self.assertEqual(CANONICAL_DATAFEEDS["sec_edgar_acceptance_datetime"]["half_life_minutes"], 15)
        self.assertEqual(CANONICAL_DATAFEEDS["finra_regsho_cnmsshvol_t1"]["lag_trading_days"], 1)
        self.assertEqual(CANONICAL_DATAFEEDS["ibkr_paper_4002_l1"]["paper_port"], 4002)
        self.assertEqual(
            CANONICAL_STRATEGY_ARCHETYPES,
            (
                "PRE_TRAVEL_EARLY_IGNITION",
                "FIRST_HAND_SEC_EPISODIC_PIVOT",
                "MEGA_CAP_NEAR_LOSSLESS_ORB",
                "CLIMAX_VWAP_MEAN_REVERSION",
            ),
        )
        self.assertEqual(len(CANONICAL_RESEARCH_MCP_TOOLS), 3)

        valid_input_sha = hashlib.sha256(b"sota-research-convergence-spec").hexdigest()
        valid_pins = {
            "alpaca-py": "c42add7c0a7026e2ead3ed64e76f4def2b99fda4",
            "edgartools": "574c2bd15f6c629bceef03b6550ea8ac8abf3473",
        }
        self.assertEqual(
            verify_research_convergence_claim(
                input_sha256=valid_input_sha,
                upstream_pins=valid_pins,
                study_max_date="2026-10-15",
                hard_stop_pct=2.0,
                evidence_grade="E4",
            ),
            [],
        )

        bad_violations = verify_research_convergence_claim(
            input_sha256="short-sha",
            upstream_pins={"alpaca-py": "main"},
            study_max_date="2026-10-16",
            hard_stop_pct=2.5,
            evidence_grade="E9",
        )
        self.assertEqual(len(bad_violations), 5)
        self.assertTrue(any(v.startswith("ADR0004_INVALID_INPUT_SHA256") for v in bad_violations))
        self.assertTrue(any(v.startswith("ADR0004_INVALID_UPSTREAM_SHA") for v in bad_violations))
        self.assertTrue(any(v.startswith("PREWALL_VIOLATION") for v in bad_violations))
        self.assertTrue(any(v.startswith("ADR0022_HARD_STOP_VIOLATION") for v in bad_violations))
        self.assertTrue(any(v.startswith("INVALID_EVIDENCE_GRADE") for v in bad_violations))

        nan_stop = verify_research_convergence_claim(
            input_sha256=valid_input_sha,
            upstream_pins=valid_pins,
            study_max_date="2026-10-15",
            hard_stop_pct=float("nan"),
            evidence_grade="E3",
        )
        self.assertEqual(len(nan_stop), 1)
        self.assertTrue(nan_stop[0].startswith("ADR0022_HARD_STOP_VIOLATION"))

    def test_sota_kit_research_convergence_context_and_peer_brief_injection(self) -> None:
        offline_ctx = kit.load_research_convergence_context(
            feed_url="http://127.0.0.1:1/api/research_feeds", timeout=0.1
        )
        self.assertEqual(offline_ctx["source"], "offline_canonical_contract")
        self.assertEqual(offline_ctx["schema_version"], RESEARCH_FEEDS_SCHEMA_VERSION)
        self.assertEqual(offline_ctx["feed_count"], 7)
        self.assertGreaterEqual(offline_ctx["upstream_pin_count"], 18)

        class _FeedHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                body = json.dumps(
                    {
                        "schema_version": "sota-research-feeds.v2",
                        "feeds": [{"feed_id": k} for k in CANONICAL_DATAFEEDS],
                        "dec6_235_sip_enabled": False,
                        "live_session_segment": "OVERNIGHT_BOATS",
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        srv = http.server.HTTPServer(("127.0.0.1", 0), _FeedHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.handle_request, daemon=True)
        t.start()
        try:
            live_ctx = kit.load_research_convergence_context(
                feed_url=f"http://127.0.0.1:{port}/api/research_feeds",
                timeout=0.8,
            )
        finally:
            srv.server_close()
            t.join(timeout=1.0)

        self.assertEqual(live_ctx["source"], "live_8787_api")
        self.assertEqual(len(live_ctx["live_feed_ids"]), 7)
        self.assertEqual(live_ctx["live_session_segment"], "OVERNIGHT_BOATS")

        brief = kit.load_peer_brief("sota-multi-model-workflows")
        self.assertIn("[SOTA Research-Convergence & 7-Feed PIT Contract", brief)
        self.assertIn("sota_converged_strategy.template.json", brief)
        self.assertIn("sota_get_research_feeds", brief)
        self.assertIn("ADR-0022<=2.00%", brief)

    def test_research_convergence_landing_workflow_fast_execution(self) -> None:
        wf_path = ROOT / "workflows" / "research_convergence_landing_workflow.py"
        code = compile(wf_path.read_text(encoding="utf-8"), "<workflow>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        ns: dict[str, object] = {
            "__name__": "__main__",
            "args": {
                "strategy_id": "SOTA_TEST_RC_01",
                "archetype": "FIRST_HAND_SEC_EPISODIC_PIVOT",
                "repo": "sota-compounding-lab",
                "broker_lane": "ALPACA_PAPER",
                "fast_deterministic_only": True,
            },
            "log": lambda *_a: None,
            "phase": lambda *_a: None,
        }
        self.assertNotIn("__file__", ns)
        buf = io.StringIO()
        with (
            mock.patch.object(kit, "run_preflight_summary", return_value={"sota_doctor": {"status": "PASS"}}),
            mock.patch.object(kit, "record_workflow_run") as rec_mock,
            redirect_stdout(buf),
        ):
            res = eval(code, ns)
            if isinstance(res, types.CoroutineType):
                asyncio.run(res)
        out = json.loads(buf.getvalue())
        self.assertTrue(out["convergence_claim_valid"])
        self.assertEqual(out["violations"], [])
        self.assertEqual(out["bootstrap"]["archetype"], "FIRST_HAND_SEC_EPISODIC_PIVOT")
        rec_mock.assert_called_once()

    def test_e4_promotion_gate_nan_inf_ibkr_port_and_normaldist_hlz(self) -> None:
        self.assertEqual(compute_hlz_t_hurdle(1), 3.0)
        exp_84 = round(max(3.0, statistics.NormalDist(0.0, 1.0).inv_cdf(1.0 - 0.00135 / 84.0)), 4)
        self.assertEqual(compute_hlz_t_hurdle(84), exp_84)

        base = StrategyCandidateManifest(
            strategy_id="SOTA_E4_CHECK",
            study_end_date="2026-10-15",
            events_count=300,
            distinct_dates=70,
            t_stat_date_clustered=4.50,
            trial_n=84,
            dsr_probability=0.97,
            cpcv_positive_fold_pct=80.0,
            net_expectancy_1x_bps=15.0,
            net_expectancy_2x_impact_bps=8.0,
            sim_engine_verified=True,
            max_initial_stop_pct=1.50,
            mega_cap_scratch_bps=10.0,
            broker_lane="IBKR_PAPER",
            account_prefix="DU",
            broker_port=4002,
        )
        self.assertTrue(evaluate_promotion_gate(base)["approved_for_autonomous_alpha"])

        # Stage-3 paper shadow (<30 closed roundtrips or <10 distinct sessions) blocks Stage-4 approval
        stage3_pending = evaluate_promotion_gate(dataclasses.replace(base, closed_roundtrips=12, distinct_sessions=5))
        self.assertFalse(stage3_pending["approved_for_autonomous_alpha"])
        self.assertTrue(stage3_pending["hard_safety_verified"])
        self.assertEqual(stage3_pending["stage_reached"], "STAGE_3_PAPER_SHADOW_ACCUMULATING")
        self.assertTrue(any(f.startswith("STAGE3_PAPER_SHADOW_INSUFFICIENT") for f in stage3_pending["failures"]))

        # IBKR_PAPER with broker_port=None must fail closed
        ibkr_none_port = dataclasses.replace(base, broker_port=None)
        res_none_port = evaluate_promotion_gate(ibkr_none_port)
        self.assertFalse(res_none_port["hard_safety_verified"])
        self.assertEqual(res_none_port["stage_reached"], "HARD_BLOCKED")
        self.assertIn("HARD_FIREWALL_NON_DU_OR_PORT_IBKR", res_none_port["failures"])

        # NaN/Inf on stop, scratch, and statistical floats must fail closed
        nan_stop = evaluate_promotion_gate(dataclasses.replace(base, max_initial_stop_pct=float("nan")))
        self.assertEqual(nan_stop["stage_reached"], "HARD_BLOCKED")
        self.assertTrue(any(f.startswith("ADR0022_STOP_VIOLATION") for f in nan_stop["failures"]))

        inf_scratch = evaluate_promotion_gate(dataclasses.replace(base, mega_cap_scratch_bps=float("inf")))
        self.assertFalse(inf_scratch["approved_for_autonomous_alpha"])
        self.assertTrue(any(f.startswith("NEAR_LOSSLESS_SCRATCH_BOUNDS") for f in inf_scratch["failures"]))

        for field_name in (
            "t_stat_date_clustered",
            "dsr_probability",
            "cpcv_positive_fold_pct",
            "net_expectancy_1x_bps",
            "net_expectancy_2x_impact_bps",
        ):
            for bad_val in (float("nan"), float("inf"), float("-inf")):
                mutated = dataclasses.replace(base, **{field_name: bad_val})
                res_bad = evaluate_promotion_gate(mutated)
                self.assertFalse(res_bad["approved_for_autonomous_alpha"], msg=f"{field_name}={bad_val}")
                self.assertTrue(any(f.startswith("STATISTICAL_GATE_REJECTED") for f in res_bad["failures"]))

    def test_e4_ao_mesh_failover_concrete_vendors_and_prewall(self) -> None:
        self.assertEqual(CONCRETE_VENDORS, frozenset({"google", "anthropic", "openai", "deepseek"}))

        ws_offline_batt = {"stationaryNoesis": {"reachable": False}, "portableMac": {"onAcPower": False}}
        self.assertEqual(derive_workstation_mesh_state(ws_offline_batt), "portable_roaming_battery")
        r_failover = resolve_ao_multi_model_route(
            "combinatorial_gpu_sweep", derive_workstation_mesh_state(ws_offline_batt)
        )
        self.assertEqual(r_failover.workstation_host, "mac_m5_max_local")

        ws_offline_ac = {"stationaryNoesis": {"reachable": False}, "portableMac": {"onAcPower": True}}
        self.assertEqual(derive_workstation_mesh_state(ws_offline_ac), "portable_roaming_ac")

        ws_online = {"stationaryNoesis": {"reachable": True}, "portableMac": {"onAcPower": True}}
        self.assertEqual(derive_workstation_mesh_state(ws_online), "dual_mesh_docked")
        self.assertEqual(
            resolve_ao_multi_model_route(
                "combinatorial_gpu_sweep", derive_workstation_mesh_state(ws_online)
            ).workstation_host,
            "noesis_64c_rtx4090",
        )

        # Multi-router harness without resolved concrete vendor must hard-block
        router_unresolved = AOLifecycleAttempt(
            task_id="ao-router-1",
            repo="sota-multi-model-workflows",
            head_commit_sha="8a29338c70778565379aacccf308a2c9fea14de8",
            lead_harness="opencode-omo",
            reviewer_harness="claude-code-omc",
            isolated_worktree=True,
            disjoint_peer_lease=True,
            upstream_sha_cited=True,
        )
        self.assertEqual(qualify_ao_lifecycle_attempt(router_unresolved)["disposition"], "AO_HARD_BLOCKED")

        # Multi-router harness resolving to same concrete vendor as reviewer must hard-block
        router_same = dataclasses.replace(router_unresolved, resolved_lead_vendor="anthropic")
        self.assertEqual(qualify_ao_lifecycle_attempt(router_same)["disposition"], "AO_HARD_BLOCKED")

        # Multi-router harness resolving to distinct concrete vendor + valid pre-wall date succeeds
        router_distinct = dataclasses.replace(
            router_unresolved,
            resolved_lead_vendor="openai",
            task_kind="prewall_quant_factor",
            study_end_date="2026-10-15",
        )
        self.assertEqual(
            qualify_ao_lifecycle_attempt(router_distinct)["disposition"],
            "AO_READY_FOR_EXPLICIT_LANDING",
        )

        # Post-wall study_end_date on quant task must hard-block
        router_postwall = dataclasses.replace(router_distinct, study_end_date="2026-10-16")
        self.assertEqual(qualify_ao_lifecycle_attempt(router_postwall)["disposition"], "AO_HARD_BLOCKED")

    def test_e4_peer_bus_foreign_lease_collision_guard(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bus = PortablePeerBus(Path(td) / "peer_bus.db")
            c1 = bus.claim_lease("sota-mmw", "agy", "session-a", ["src/*"], "owning src")
            self.assertTrue(c1["claimed"])

            # Foreign session with overlapping path must be rejected without clobbering session-a
            c_conflict = bus.claim_lease(
                "sota-mmw", "claude", "session-b", ["src/sota_mmw/promotion_gate.py"], "overlapping edit"
            )
            self.assertFalse(c_conflict["claimed"])
            self.assertEqual(c_conflict["conflict_lease_key"], "sota-mmw::session-a")
            self.assertIn("src/sota_mmw/promotion_gate.py", c_conflict["conflict_paths"])

            # Wildcard foreign claim also collides
            c_wild = bus.claim_lease("sota-mmw", "codex", "session-c", ["*"], "whole repo")
            self.assertFalse(c_wild["claimed"])

            # Disjoint directory claim by foreign session succeeds
            c_disjoint = bus.claim_lease("sota-mmw", "claude", "session-b", ["docs/adr/*"], "disjoint docs")
            self.assertTrue(c_disjoint["claimed"])

            # Same session renewing its own lease succeeds
            c_renew = bus.claim_lease("sota-mmw", "agy", "session-a", ["src/*"], "renew")
            self.assertTrue(c_renew["claimed"])

            # Expired foreign lease does not block
            bus.claim_lease("sota-mmw", "dsh", "session-exp", ["scripts/*"], "already expired", ttl_m=-5)
            c_take_expired = bus.claim_lease("sota-mmw", "agy", "session-new", ["scripts/merge_gate.py"], "fresh")
            self.assertTrue(c_take_expired["claimed"])

    def test_e4_org_compounding_workflow_invokes_promotion_gate_and_merge_gate_patterns(self) -> None:
        wf_path = ROOT / "workflows" / "org_compounding_promotion_workflow.py"
        src = wf_path.read_text(encoding="utf-8")
        self.assertIn("evaluate_promotion_gate", src)
        code = compile(src, "<workflow>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        ns: dict[str, object] = {
            "__name__": "__main__",
            "args": {
                "strategy_id": "SOTA_PROMO_FAST_01",
                "broker_lane": "IBKR_PAPER",
                "fast_deterministic_only": True,
            },
            "log": lambda *_a: None,
            "phase": lambda *_a: None,
        }
        self.assertNotIn("__file__", ns)
        buf = io.StringIO()
        with (
            mock.patch.object(kit, "run_preflight_summary", return_value={"sota_doctor": {"status": "PASS"}}),
            mock.patch.object(kit, "record_workflow_run") as rec_mock,
            redirect_stdout(buf),
        ):
            res = eval(code, ns)
            if isinstance(res, types.CoroutineType):
                asyncio.run(res)
        out = json.loads(buf.getvalue())
        # Omitted empirical candidate_metrics must fail closed to STAGE_1_PROTECTIVE_OVERLAY_ONLY (never synthesize passing defaults)
        self.assertTrue(out["deterministic_promotion_gate"]["hard_safety_verified"])
        self.assertFalse(out["deterministic_promotion_gate"]["approved_for_autonomous_alpha"])
        self.assertEqual(out["deterministic_promotion_gate"]["stage_reached"], "STAGE_1_PROTECTIVE_OVERLAY_ONLY")
        self.assertGreaterEqual(out["deterministic_promotion_gate"]["required_hlz_t_hurdle"], compute_hlz_t_hurdle(87))
        rec_mock.assert_called_once()

        # Explicit passing Stage-2 + Stage-3 candidate_metrics reach STAGE_4_PAPER_EXECUTION_APPROVED
        ns_explicit = {
            **ns,
            "args": {
                "strategy_id": "SOTA_PROMO_EXPLICIT_02",
                "broker_lane": "IBKR_PAPER",
                "fast_deterministic_only": True,
                "candidate_metrics": {
                    "events_count": 340,
                    "distinct_dates": 80,
                    "t_stat_date_clustered": 4.85,
                    "trial_n": 90,
                    "dsr_probability": 0.98,
                    "cpcv_positive_fold_pct": 85.0,
                    "net_expectancy_1x_bps": 19.0,
                    "net_expectancy_2x_impact_bps": 9.5,
                    "sim_engine_verified": True,
                    "closed_roundtrips": 35,
                    "distinct_sessions": 14,
                },
            },
        }
        buf2 = io.StringIO()
        with (
            mock.patch.object(kit, "run_preflight_summary", return_value={"sota_doctor": {"status": "PASS"}}),
            mock.patch.object(kit, "record_workflow_run"),
            redirect_stdout(buf2),
        ):
            res2 = eval(code, ns_explicit)
            if isinstance(res2, types.CoroutineType):
                asyncio.run(res2)
        out2 = json.loads(buf2.getvalue())
        self.assertTrue(out2["deterministic_promotion_gate"]["approved_for_autonomous_alpha"])
        self.assertEqual(out2["deterministic_promotion_gate"]["stage_reached"], "STAGE_4_PAPER_EXECUTION_APPROVED")

        def _triggers(sample: str) -> list[str]:
            return [label for label, rx in merge_gate.SECRET_PATTERNS if rx.search(sample)]

        self.assertTrue(_triggers("https://api." + "alpaca.markets/v2/orders"))
        self.assertEqual(_triggers("https://paper-api.alpaca.markets/v2/orders"), [])
        self.assertTrue(_triggers("~/." + "claude/bin/live"))
        self.assertTrue(_triggers("~/." + "claude/bin/alpaca-live-mcp"))
        self.assertTrue(_triggers("~/." + "claude/bin/key-store"))
        self.assertTrue(_triggers("/" + "home/ubuntu/workspace/"))
        self.assertTrue(_triggers("C:\\" + "Users\\runner\\repo\\"))
        self.assertTrue(_triggers("C:/" + "Users/runner/repo/"))

    def test_cross_os_agent_bin_argv_parity_and_ao_dynamic_detectors(self) -> None:
        argv_posix = kit.agent_bin_argv(Path("~/.agents/bin/sota-workstation"), "status", "--json")
        self.assertEqual(argv_posix[-2:], ["status", "--json"])
        with tempfile.TemporaryDirectory() as td_pe:
            pe_shim = Path(td_pe) / "sota-doctor"
            pe_shim.write_bytes(b"MZ\x90\x00")
            sibling_base = Path(td_pe) / "sota-org-doctor"
            sibling_exe = Path(td_pe) / "sota-org-doctor.exe"
            sibling_exe.write_bytes(b"MZ\x90\x00")
            win_script = Path("C:/sota-workstation/.agents/bin/sota-workstation")
            win_exe = Path("C:/sota-workstation/orca.exe")
            with mock.patch("workflows._sota_kit.os.name", "nt"):
                argv_win = kit.agent_bin_argv(win_script, "status", "--json")
                self.assertEqual(argv_win[0], sys.executable)
                self.assertEqual(argv_win[-2:], ["status", "--json"])
                argv_exe = kit.agent_bin_argv(win_exe, "status")
                self.assertEqual(argv_exe[0], str(win_exe))
                argv_mz = kit.agent_bin_argv(pe_shim, "--json")
                self.assertEqual(argv_mz, [str(pe_shim), "--json"])
                argv_sib = kit.agent_bin_argv(sibling_base, "--live")
                self.assertEqual(argv_sib, [str(sibling_exe), "--live"])

        # Count AST assertions in this repository's tests/
        assertion_cnt = count_python_test_assertions(ROOT)
        self.assertGreaterEqual(assertion_cnt, 50)

        # Verify detect_isolated_worktree against temporary primary repo + linked worktree
        with tempfile.TemporaryDirectory() as td:
            primary_repo = Path(td) / "primary"
            linked_wt = Path(td) / "linked-wt"
            primary_repo.mkdir()
            subprocess.run(["git", "-C", str(primary_repo), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(primary_repo), "config", "user.email", "t@example.com"], check=True)
            subprocess.run(["git", "-C", str(primary_repo), "config", "user.name", "t"], check=True)
            (primary_repo / "README.md").write_text("init\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(primary_repo), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(primary_repo), "commit", "-q", "-m", "init"], check=True)
            subprocess.run(
                ["git", "-C", str(primary_repo), "worktree", "add", "-q", "-b", "wt-b", str(linked_wt)],
                check=True,
            )
            self.assertFalse(detect_isolated_worktree(primary_repo))
            self.assertTrue(detect_isolated_worktree(linked_wt))

            # Verify detect_disjoint_peer_lease against PortablePeerBus SQLite WAL
            db_file = Path(td) / "peer_bus.db"
            bus = PortablePeerBus(db_file)
            self.assertTrue(detect_disjoint_peer_lease("sota-mmw", session_id="s1", db_path=db_file))
            bus.claim_lease("sota-mmw", "agy", "s1", ["src/*"], "s1 work")
            self.assertTrue(detect_disjoint_peer_lease("sota-mmw", session_id="s1", db_path=db_file))
            self.assertFalse(
                detect_disjoint_peer_lease("sota-mmw", session_id="s2", db_path=db_file, requested_paths=["src/a.py"])
            )
            self.assertTrue(
                detect_disjoint_peer_lease("sota-mmw", session_id="s2", db_path=db_file, requested_paths=["docs/*"])
            )

    def test_cc_lead_central_orchestrator_and_workflow_14(self) -> None:
        self.assertEqual(CC_LEAD_CENTRAL_CONTRACT["lead_runtime"], "claude")
        self.assertEqual(CC_LEAD_CENTRAL_CONTRACT["lead_model_id"], "claude-fable-5-2")
        self.assertTrue(CC_LEAD_CENTRAL_CONTRACT["one_model_per_conversation"])
        self.assertEqual(len(RUNTIME_WORKER_ROSTER), 11)
        self.assertIn("pi-omp-worker", RUNTIME_WORKER_ROSTER)
        self.assertIn("goose-autonomous", RUNTIME_WORKER_ROSTER)

        with tempfile.TemporaryDirectory() as td:
            db_file = Path(td) / "peer_bus.db"
            bus = PortablePeerBus(db_file)

            # 1. Valid Noesis GPU sweep routes to noesis_64c_rtx4090 with >=3 canonical vendors and --on 100.110.115.22
            with mock.patch("sota_mmw.cc_lead_hub.is_running_on_noesis_host", return_value=False):
                plan = build_cc_lead_execution_plan(
                    CCLeadPlanRequest(
                        repo="sota-compounding-lab",
                        goal="Run pre-wall CPCV sweep with Claude OMC lead, Codex OMX critic & DeepSeek DSH batch",
                        task_class="combinatorial_gpu_sweep",
                        placement="auto",
                        session_id="cc-lead-1",
                    ),
                    mesh_state="dual_mesh_docked",
                    bus_db_path=db_file,
                )
                self.assertEqual(plan["target_host"], "noesis_64c_rtx4090")
                self.assertEqual(plan["orca_repo_selector"], "id:46980ada-367d-4ba8-a487-a44940db96fd")
                self.assertGreaterEqual(plan["canonical_vendors_count"], 3)
                self.assertTrue(plan["isolation_and_lease"]["lease_disjoint"])
                self.assertIn("OMC_RUNTIME_V2=1", plan["channels"]["2_omc_team_swarm_cmd"])
                self.assertIn("omc ultragoal create-goals", plan["channels"]["1_cc_lead_ultragoal_cmd"])
                dispatches = plan["channels"]["4_orca_supervised_worker_dispatches"]
                self.assertEqual(len(dispatches), 3)
                for d in dispatches:
                    self.assertIn("--on", d["argv"])
                    self.assertIn("100.110.115.22", d["argv"])
                    self.assertNotIn("--environment", d["argv"])

            # Local placement omits --on; pi-omp-worker passes --model @worker --effort high; opencode omits --effort
            plan_local_omp = build_cc_lead_execution_plan(
                CCLeadPlanRequest(
                    repo="cc-sota-harness",
                    goal="Test OMP and OpenCode worker flags",
                    task_class="parallel_worktree_implementation",
                    placement="local",
                    worker_keys_override=(
                        "codex-sol-omx",
                        "antigravity-carbon",
                        "pi-omp-worker",
                        "opencode-sonnet-omo",
                    ),
                    session_id="cc-lead-1",
                ),
                mesh_state="dual_mesh_docked",
                bus_db_path=db_file,
            )
            local_dispatches = {
                d["worker_key"]: d["argv"] for d in plan_local_omp["channels"]["4_orca_supervised_worker_dispatches"]
            }
            for argv in local_dispatches.values():
                self.assertNotIn("--on", argv)
                self.assertNotIn("--environment", argv)
            omp_argv = local_dispatches["pi-omp-worker"]
            self.assertIn("--model", omp_argv)
            self.assertIn("@worker", omp_argv)
            self.assertIn("--effort", omp_argv)
            opencode_argv = local_dispatches["opencode-sonnet-omo"]
            self.assertNotIn("--effort", opencode_argv)
            self.assertNotIn("--model", opencode_argv)

            # Verify every registered task_class builds cleanly without vendor-diversity errors
            for tc_name in TASK_CLASS_PROFILES:
                p_tc = build_cc_lead_execution_plan(
                    CCLeadPlanRequest(
                        repo="cc-sota-harness",
                        goal=f"Verify {tc_name}",
                        task_class=tc_name,
                        session_id="cc-lead-1",
                    ),
                    mesh_state="dual_mesh_docked",
                    bus_db_path=db_file,
                )
                self.assertEqual(p_tc["task_class"], tc_name)

            # 2. Foreign overlapping lease flips lease_disjoint=False
            bus.claim_lease("sota-compounding-lab", "agy", "foreign-peer", ["src/*"], "active edit")
            plan_blocked = build_cc_lead_execution_plan(
                CCLeadPlanRequest(
                    repo="sota-compounding-lab",
                    goal="Edit src/sota_compounding",
                    task_class="lead_architecture_adr_and_spec",
                    session_id="cc-lead-1",
                    requested_paths=("src/sota_compounding/engine.py",),
                ),
                bus_db_path=db_file,
            )
            self.assertFalse(plan_blocked["isolation_and_lease"]["lease_disjoint"])

            # 3. Hephaestus GPT model, post-wall prewall date, and live broker endpoints fail closed
            with self.assertRaises(ValueError):
                build_cc_lead_execution_plan(
                    CCLeadPlanRequest(
                        repo="cc-sota-harness",
                        goal="Refactor modules",
                        hephaestus_model_override="gpt-6.2-astra",
                    ),
                    bus_db_path=db_file,
                )
            with self.assertRaises(ValueError):
                build_cc_lead_execution_plan(
                    CCLeadPlanRequest(
                        repo="sota-compounding-lab",
                        goal="Test factor",
                        task_class="quant_prewall_hypothesis_falsification",
                        study_end_date="2026-11-01",
                    ),
                    bus_db_path=db_file,
                )
            with self.assertRaises(PermissionError):
                build_cc_lead_execution_plan(
                    CCLeadPlanRequest(
                        repo="astrolabe",
                        goal="Connect IBKR port=4001",
                    ),
                    bus_db_path=db_file,
                )

        # 4. Execute Workflow #14 in <workflow> namespace without __file__
        wf14 = ROOT / "workflows" / "cc_lead_multi_runtime_workers_workflow.py"
        src14 = wf14.read_text(encoding="utf-8")
        code14 = compile(src14, "<workflow>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        ns14: dict[str, object] = {
            "__name__": "__main__",
            "args": {
                "repo": "cc-sota-harness",
                "task_class": "cross_family_adversarial_code_and_math_audit",
                "fast_deterministic_only": True,
            },
            "log": lambda *_a: None,
            "phase": lambda *_a: None,
        }
        buf14 = io.StringIO()
        with (
            mock.patch.object(kit, "run_preflight_summary", return_value={"sota_doctor": {"status": "PASS"}}),
            mock.patch.object(kit, "record_workflow_run") as rec14,
            redirect_stdout(buf14),
        ):
            r14 = eval(code14, ns14)
            if isinstance(r14, types.CoroutineType):
                asyncio.run(r14)
        out14 = json.loads(buf14.getvalue())
        self.assertEqual(out14["cc_lead_plan"]["schema_version"], "sota-cc-lead-hub.v2")
        self.assertEqual(len(out14["cc_lead_plan"]["plan_sha256"]), 64)
        rec14.assert_called_once()

        # 5. Cross-OS os.pathsep parity for probe_cc_runtime_fleet (Windows ';' vs POSIX ':')
        from sota_mmw import cc_lead_hub as cch

        captured_paths: list[str] = []

        def _fake_which(_bin: str, path: str | None = None) -> str | None:
            if path is not None:
                captured_paths.append(path)
            return "/mock/bin"

        with (
            mock.patch.object(cch.os, "pathsep", ";"),
            mock.patch.dict(cch.os.environ, {"PATH": "C:\\Tools;C:\\Bin"}, clear=False),
            mock.patch.object(cch.shutil, "which", side_effect=_fake_which),
        ):
            fleet_win = cch.probe_cc_runtime_fleet()
        self.assertEqual(fleet_win["installed_count"], 17)
        self.assertTrue(captured_paths and ";C:\\Tools;C:\\Bin" in captured_paths[0])

    def test_v360_all_14_workflows_enforce_full_stack_datafeed_template_engine_and_workstation_convergence(
        self,
    ) -> None:
        from sota_mmw.research_convergence_contract import (
            CANONICAL_STRATEGY_TEMPLATES_MATRIX,
            CANONICAL_TRADING_ENGINE_SOURCES,
            CANONICAL_TRADING_LANE_DATAFEED_APIS,
            build_workflow_research_convergence_envelope,
            resolve_ecosystem_repo_dir,
        )

        # 1. Every single one of the 20 canonical workflows must call kit.verify_workflow_research_convergence
        wf_files = sorted((ROOT / "workflows").glob("*_workflow.py"))
        self.assertEqual(len(wf_files), 20)
        for wf_path in wf_files:
            txt = wf_path.read_text(encoding="utf-8")
            self.assertIn(
                "verify_workflow_research_convergence(",
                txt,
                msg=f"{wf_path.name} missing kit.verify_workflow_research_convergence(...)",
            )

        # 2. Verify 6 Trading Lane DataFeed APIs, 4 Strategy Templates, and 8 Trading Engine Sources
        self.assertEqual(len(CANONICAL_TRADING_LANE_DATAFEED_APIS), 6)
        self.assertEqual(len(CANONICAL_STRATEGY_TEMPLATES_MATRIX), 4)
        self.assertEqual(len(CANONICAL_TRADING_ENGINE_SOURCES), 8)

        # 3. Verify 3-surface repo resolution (Mac ~/Documents, Noesis Win32, Noesis-Carbon WSL2)
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            wsl_home = base / "wsl_home"
            win_root = base / "win_sota_ws"
            (wsl_home / "sota-workstation" / "meridian").mkdir(parents=True)
            (win_root / "astrolabe").mkdir(parents=True)

            self.assertEqual(
                resolve_ecosystem_repo_dir("meridian", home=wsl_home, win_root=win_root),
                wsl_home / "sota-workstation" / "meridian",
            )
            self.assertEqual(
                resolve_ecosystem_repo_dir("astrolabe", home=wsl_home, win_root=win_root),
                win_root / "astrolabe",
            )

            env = build_workflow_research_convergence_envelope(
                workflow_id="research-convergence-landing",
                repo="meridian",
                archetype="FIRST_HAND_SEC_EPISODIC_PIVOT",
                home=wsl_home,
                win_root=win_root,
            )
            self.assertTrue(env["valid"], msg=env["violations"])
            self.assertEqual(env["violations"], [])
            self.assertEqual(env["datafeed_api_count"], 6)
            self.assertEqual(env["trading_engine_source_count"], 8)
            self.assertEqual(len(env["envelope_input_sha256"]), 64)
            self.assertTrue(env["trading_engine_repos_present"]["meridian"])
            self.assertTrue(env["trading_engine_repos_present"]["astrolabe"])

    def test_v370_dual_machine_trading_and_harness_lanes_and_workflow_15(self) -> None:
        from sota_mmw import cc_lead_hub as cch
        from sota_mmw import dual_machine_lanes as dml

        # 1. Verify 8 orchestration frameworks, 3 surfaces, 4 Orca folder hubs, and 18-repo lane bijection
        self.assertEqual(len(ORCHESTRATION_FRAMEWORKS_MATRIX), 8)
        self.assertEqual(len(DUAL_MACHINE_SURFACES), 3)
        self.assertEqual(len(TRADING_LANES), 3)
        self.assertEqual(len(HARNESS_LANES), 3)
        self.assertEqual(set(REPO_LANE_INDEX.keys()), set(NOESIS_PROVISIONED_ORCA_REPOS.keys()))
        self.assertEqual(len(REPO_LANE_INDEX), 18)
        self.assertEqual(
            ORCA_LANE_HUBS["portable_mac_m5_max"]["trading"]["parent_selector"],
            "folder:4cf80c7f-96aa-42f1-a25c-a55e7d5e3f3a",
        )
        self.assertEqual(
            ORCA_LANE_HUBS["stationary_noesis"]["harness"]["parent_selector"],
            "folder:060eb055-834e-4ef2-8198-e3e224a35fbe",
        )

        overview = build_lanes_overview(plane="all", mesh_state="dual_mesh_docked")
        self.assertTrue(overview["ok"])
        self.assertEqual(overview["trading_repos_count"], 8)
        self.assertEqual(overview["harness_repos_count"], 10)
        self.assertEqual(overview["total_provisioned_repos"], 18)

        # 2. T3 pre-wall GPU/CPCV routes to stationary_noesis_win32 with --on 100.110.115.22 & roaming failover
        with (
            mock.patch.object(dml, "is_running_on_noesis_host", return_value=False),
            mock.patch("sota_mmw.cc_lead_hub.is_running_on_noesis_host", return_value=False),
        ):
            t3_docked = resolve_dual_machine_lane_plan(
                "sota-compounding-lab",
                workload="combinatorial_gpu_sweep",
                mesh_state="dual_mesh_docked",
            )
            self.assertEqual(t3_docked["selected_surface"], "stationary_noesis_win32")
            self.assertTrue(t3_docked["use_noesis"])
            self.assertIn("--on", t3_docked["orca_worker_start_argv"])
            self.assertIn("100.110.115.22", t3_docked["orca_worker_start_argv"])
            self.assertEqual(
                t3_docked["orca_parent_worktree_selector"],
                "folder:c4f93f9e-a710-4599-ac95-892082b03ec8",
            )
            self.assertGreaterEqual(t3_docked["concrete_vendor_count"], 3)

        t3_roaming = resolve_dual_machine_lane_plan(
            "sota-compounding-lab",
            workload="combinatorial_gpu_sweep",
            mesh_state="portable_roaming_battery",
            local_orca_repo_id="00000000-0000-0000-0000-000000000001",
        )
        self.assertEqual(t3_roaming["selected_surface"], "portable_mac_m5_max")
        self.assertFalse(t3_roaming["use_noesis"])
        self.assertNotIn("--on", t3_roaming["orca_worker_start_argv"])

        # 3. T2 meridian event-sim routes to stationary_noesis_carbon_wsl2; astrolabe default stays on Mac
        t2_meridian = resolve_dual_machine_lane_plan("meridian", mesh_state="dual_mesh_docked")
        self.assertEqual(t2_meridian["selected_surface"], "stationary_noesis_carbon_wsl2")
        t2_astrolabe = resolve_dual_machine_lane_plan(
            "astrolabe",
            mesh_state="dual_mesh_docked",
            local_orca_repo_id="00000000-0000-0000-0000-000000000002",
        )
        self.assertEqual(t2_astrolabe["selected_surface"], "portable_mac_m5_max")

        # 4. Single-Broker-Host Firewall (ADR-0020) hard-blocks active paper broker sockets on Noesis
        with self.assertRaises(PermissionError):
            resolve_dual_machine_lane_plan(
                "sota-mover-ranker",
                workload="active_paper_broker",
                requested_placement="noesis",
            )

        err_buf = io.StringIO()
        with mock.patch("sys.stderr", err_buf):
            rc_blocked = dml.main(
                ["route", "--repo", "sota-mover-ranker", "--workload", "active_paper_broker", "--placement", "noesis"]
            )
        self.assertEqual(rc_blocked, 2)
        self.assertEqual(json.loads(err_buf.getvalue())["reason"], "SINGLE_BROKER_HOST_FIREWALL")

        out_buf = io.StringIO()
        with redirect_stdout(out_buf):
            self.assertEqual(dml.main(["matrix", "--json"]), 0)
        self.assertEqual(json.loads(out_buf.getvalue())["frameworks_count"], 8)

        hub_lanes_buf = io.StringIO()
        with redirect_stdout(hub_lanes_buf):
            self.assertEqual(cch.main(["lanes", "--plane", "trading", "--json"]), 0)
        self.assertEqual(json.loads(hub_lanes_buf.getvalue())["trading_repos_count"], 8)

        # 5. Verify canonical orca.yaml in repository root
        orca_yaml = (ROOT / "orca.yaml").read_text(encoding="utf-8")
        self.assertIn("setupAgentStartupPolicy: wait-for-setup", orca_yaml)
        self.assertIn("CC-Lead & Lanes Hub", orca_yaml)

        # 6. Execute Workflow #15 in <workflow> namespace without __file__
        wf15 = ROOT / "workflows" / "dual_machine_trading_and_harness_lanes_workflow.py"
        src15 = wf15.read_text(encoding="utf-8")
        code15 = compile(src15, "<workflow>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        ns15: dict[str, object] = {
            "__name__": "__main__",
            "args": {
                "repo": "sota-compounding-lab",
                "plane": "all",
                "workload": "combinatorial_gpu_sweep",
                "placement": "auto",
                "fast_deterministic_only": True,
            },
            "log": lambda *_a: None,
            "phase": lambda *_a: None,
        }
        buf15 = io.StringIO()
        with (
            mock.patch.object(cch, "_load_live_bus_and_mesh", return_value=(90, 4.18, "dual_mesh_docked")),
            mock.patch.object(kit, "run_preflight_summary", return_value={"sota_doctor": {"status": "PASS"}}),
            mock.patch.object(kit, "record_workflow_run") as rec15,
            redirect_stdout(buf15),
        ):
            r15 = eval(code15, ns15)
            if isinstance(r15, types.CoroutineType):
                asyncio.run(r15)
        out15 = json.loads(buf15.getvalue())
        self.assertTrue(out15["single_broker_host_firewall_verified"])
        self.assertEqual(out15["total_provisioned_repos"], 18)
        self.assertEqual(out15["frameworks_count"], 8)
        self.assertEqual(out15["target_lane_route"]["selected_surface"], "stationary_noesis_win32")
        rec15.assert_called_once()

    def test_v380_ranking_datafeeds_compounding_versioning_and_workflow_16(self) -> None:
        from sota_mmw import compounding_versioning as cv

        # 1. Verify 9 DF1..DF9 Ranking DataFeeds, v2 backward-compat coverage, and 64-hex digests
        self.assertEqual(RANKING_DATAFEEDS_SCHEMA_VERSION, "sota-ranking-datafeeds.v3.8")
        self.assertEqual(len(CANONICAL_RANKING_DATAFEEDS_V38), 9)
        expected_df_ids = [
            "DF1_alpaca_sip_lit_and_dark_tape",
            "DF2_alpaca_boats_overnight_and_dec6_23x5",
            "DF3_raw_vs_all_split_and_corporate_actions_guard",
            "DF4_xnys_tod_rvol_bucket_normalizer",
            "DF5_sec_edgar_acceptance_datetime_catalyst_and_dilution_shield",
            "DF6_sec_xbrl_point_in_time_public_float",
            "DF7_finra_regsho_cnmsshvol_intraday_t1",
            "DF8_finra_rule4560_settled_short_interest_t8",
            "DF9_vix_majors_regime_and_ibkr_4002_l1_locate",
        ]
        self.assertEqual(list(CANONICAL_RANKING_DATAFEEDS_V38.keys()), expected_df_ids)
        covered_v2 = {v2 for df in CANONICAL_RANKING_DATAFEEDS_V38.values() for v2 in df["v2_compat_feeds"]}
        self.assertEqual(covered_v2, set(CANONICAL_DATAFEEDS.keys()))

        self.assertEqual(len(UPSTREAM_SHELF_PINS_18), 18)
        shelf_sha = compute_upstream_shelf_tree_sha256()
        df_sha = compute_ranking_datafeed_contract_sha256()
        self.assertEqual(len(shelf_sha), 64)
        self.assertEqual(len(df_sha), 64)

        # 2. Two-track promotion: H090 compounds ONLY on PROTECTIVE_FILTER_OR_GOVERNANCE, refused on ALPHA_STRATEGY_MINOR
        h090_protective = CompoundingVersionRecord(
            prev_semver="3.7.0",
            next_semver="3.8.0",
            promotion_kind="PROTECTIVE_FILTER_OR_GOVERNANCE",
            adr_id="ADR-0015",
            input_lake_sha256=DEFAULT_PREWALL_LAKE_SHA256,
            upstream_shelf_tree_sha256=shelf_sha,
            ranking_datafeed_contract_sha256=df_sha,
            trials_n=90,
            lessons_count=60,
            candidate_id="H090_LIT_ONLY_PROTECTIVE_FILTER",
            dsr_probability=0.42,
            cpcv_positive_fold_pct=100.0,
            t_stat_date_clustered=1.2919,
            net_1x_bps=20.84,
            net_2x_bps=15.43,
            closed_roundtrips=0,
            distinct_sessions=0,
            hard_stop_pct=1.80,
        )
        res_prot = verify_compounding_version_transition(h090_protective, prev_adr_id="ADR-0014")
        self.assertTrue(res_prot["approved"], msg=res_prot["violations"])
        self.assertFalse(res_prot["alpha_stage_elevated"])
        self.assertEqual(res_prot["track_disposition"], "PROTECTIVE_FILTER_OR_ADR_COMPOUNDED")
        self.assertEqual(res_prot["required_hlz_t_hurdle"], 4.1735)
        self.assertGreaterEqual(res_prot["next_trial_hlz_t_hurdle"], 4.1760)
        self.assertEqual(len(res_prot["transition_receipt_sha256"]), 64)

        h090_alpha_attempt = dataclasses.replace(h090_protective, promotion_kind="ALPHA_STRATEGY_MINOR")
        res_alpha_rej = verify_compounding_version_transition(h090_alpha_attempt, prev_adr_id="ADR-0014")
        self.assertFalse(res_alpha_rej["approved"])
        self.assertFalse(res_alpha_rej["alpha_stage_elevated"])
        self.assertTrue(any(v.startswith("ALPHA_T_STAT_BELOW_HLZ:") for v in res_alpha_rej["violations"]))

        # Full alpha candidate clears ALPHA_STRATEGY_MINOR
        full_alpha = dataclasses.replace(
            h090_protective,
            promotion_kind="ALPHA_STRATEGY_MINOR",
            candidate_id="H091_FULL_STAGE4_CANDIDATE",
            dsr_probability=0.98,
            cpcv_positive_fold_pct=86.7,
            t_stat_date_clustered=4.65,
            net_1x_bps=18.4,
            net_2x_bps=9.2,
            closed_roundtrips=35,
            distinct_sessions=12,
            hard_stop_pct=1.60,
        )
        res_alpha_ok = verify_compounding_version_transition(full_alpha, prev_adr_id="ADR-0014")
        self.assertTrue(res_alpha_ok["approved"], msg=res_alpha_ok["violations"])
        self.assertTrue(res_alpha_ok["alpha_stage_elevated"])
        self.assertEqual(res_alpha_ok["track_disposition"], "ALPHA_STAGE_ELEVATED")

        # 3. Monotonic SemVer, sequential ADR, pre-wall, ADR-0022 stop & hash tampering all fail closed
        for bad_rec, expected_prefix in (
            (dataclasses.replace(h090_protective, next_semver="3.7.0"), "NON_MONOTONIC_SEMVER"),
            (dataclasses.replace(h090_protective, next_semver="3.6.9"), "NON_MONOTONIC_SEMVER"),
            (dataclasses.replace(h090_protective, adr_id="ADR-0014"), "NON_SEQUENTIAL_ADR_ID"),
            (dataclasses.replace(h090_protective, study_end_date="2026-11-01"), "PREWALL_VIOLATION"),
            (dataclasses.replace(h090_protective, hard_stop_pct=2.50), "ADR0022_STOP_VIOLATION"),
            (dataclasses.replace(h090_protective, trials_n=85), "HLZ_TRIALS_BELOW_FLOOR"),
            (dataclasses.replace(h090_protective, sibling_repo_authority="COPY"), "SIBLING_REPO_AUTHORITY_VIOLATION"),
            (
                dataclasses.replace(h090_protective, ranking_datafeed_contract_sha256="0" * 64),
                "RANKING_DATAFEED_CONTRACT_SHA256_MISMATCH",
            ),
        ):
            r_bad = verify_compounding_version_transition(bad_rec, prev_adr_id="ADR-0014")
            self.assertFalse(r_bad["approved"])
            self.assertTrue(
                any(v.startswith(expected_prefix) for v in r_bad["violations"]),
                msg=f"Expected {expected_prefix} in {r_bad['violations']}",
            )

        # 4. Verify CLI status, ranking-feeds, and verify exit codes
        st_snap = build_compounding_version_status()
        self.assertTrue(st_snap["ok"])
        out_rf = io.StringIO()
        with redirect_stdout(out_rf):
            self.assertEqual(cv.main(["ranking-feeds", "--json"]), 0)
        self.assertEqual(json.loads(out_rf.getvalue())["feed_count"], 9)

        err_vf = io.StringIO()
        with mock.patch("sys.stderr", err_vf):
            rc_rej = cv.main(["verify", "--promotion-kind", "ALPHA_STRATEGY_MINOR", "--t-stat", "1.2919"])
        self.assertEqual(rc_rej, 2)

        # 5. Execute Workflow #16 in <workflow> namespace without __file__
        wf16 = ROOT / "workflows" / "compounding_versioning_and_ranking_adr_workflow.py"
        src16 = wf16.read_text(encoding="utf-8")
        code16 = compile(src16, "<workflow>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        ns16: dict[str, object] = {
            "__name__": "__main__",
            "args": {
                "repo": "sota-multi-model-workflows",
                "prev_semver": "3.7.0",
                "next_semver": "3.8.0",
                "promotion_kind": "PROTECTIVE_FILTER_OR_GOVERNANCE",
                "adr_id": "ADR-0015",
                "prev_adr_id": "ADR-0014",
                "fast_deterministic_only": True,
            },
            "log": lambda *_a: None,
            "phase": lambda *_a: None,
        }
        buf16 = io.StringIO()
        with (
            mock.patch.object(kit, "run_preflight_summary", return_value={"sota_doctor": {"status": "PASS"}}),
            mock.patch.object(kit, "record_workflow_run") as rec16,
            redirect_stdout(buf16),
        ):
            r16 = eval(code16, ns16)
            if isinstance(r16, types.CoroutineType):
                asyncio.run(r16)
        out16 = json.loads(buf16.getvalue())
        self.assertEqual(out16["canonical_ranking_feeds_count"], 9)
        self.assertTrue(out16["transition_verdict"]["approved"])
        self.assertTrue(out16["two_track_subhurdle_alpha_rejection_verified"])
        rec16.assert_called_once()

    def test_v390_full_landscape_lanes_v2_rth_shield_and_hub_sync(self) -> None:
        from sota_mmw import compounding_versioning as cv
        from sota_mmw import dual_machine_lanes as dml

        # 1. Empirical 64-hex pre-wall lake SHA-256 & v3.9.0 status
        self.assertEqual(
            cv.DEFAULT_PREWALL_LAKE_SHA256,
            "a253421e873441740d5d4b410d993cfa7345fe34b88ec4ab7f4eecd537b3f234",
        )
        self.assertEqual(cv.DEFAULT_ECOSYSTEM_SEMVER, "3.10.0")
        st_v390 = cv.build_compounding_version_status()
        self.assertTrue(st_v390["ok"])
        self.assertEqual(st_v390["ecosystem_version"], "3.10.0")
        self.assertEqual(st_v390["latest_verified_transition"]["adr_id"], "ADR-0024")

        # 2. T1..T5 x H0..H7 bijection (13 sub-lanes covering all 18 active repos) & 9-feed DF1..DF9 gate
        self.assertEqual(len(dml.STAGE_AND_LAYER_SUBLANES), 13)
        sublane_repos = {r for s in dml.STAGE_AND_LAYER_SUBLANES.values() for r in s["repos"]}
        self.assertEqual(sublane_repos, set(dml.REPO_LANE_INDEX.keys()))
        self.assertEqual(len(dml.CANONICAL_SEVEN_MODEL_VENDORS), 6)

        # 3. Live RTH active_broker_host_shield offloads docked heavy sweeps to Noesis
        unshielded = dml.resolve_dual_machine_lane_plan(
            "agy-sota-harness",
            workload="heavy_test_sweep",
            mesh_state="dual_mesh_docked",
            active_broker_host_shield=False,
        )
        self.assertEqual(unshielded["selected_surface"], "portable_mac_m5_max")
        shielded = dml.resolve_dual_machine_lane_plan(
            "agy-sota-harness",
            workload="heavy_test_sweep",
            mesh_state="dual_mesh_docked",
            active_broker_host_shield=True,
        )
        self.assertEqual(shielded["selected_surface"], "stationary_noesis_carbon_wsl2")
        self.assertTrue(shielded["use_noesis"])
        self.assertEqual(shielded["provenance_gate"]["ranking_datafeeds_schema"], "sota-ranking-datafeeds.v3.8")
        self.assertEqual(shielded["provenance_gate"]["ranking_feeds_count"], 9)

        # 4. Deterministic sota-orca-lane-hub.v2 generation (LANE_MANIFEST.json + orca.yaml + README.md)
        with tempfile.TemporaryDirectory() as td_hubs:
            hub_res = dml.sync_orca_lane_hubs(Path(td_hubs))
            self.assertTrue(hub_res["ok"])
            self.assertEqual(hub_res["files_written"], 6)
            tr_mf = json.loads((Path(td_hubs) / "trading-lanes" / "LANE_MANIFEST.json").read_text(encoding="utf-8"))
            hr_mf = json.loads((Path(td_hubs) / "harness-lanes" / "LANE_MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(tr_mf["schemaVersion"], "sota-orca-lane-hub.v2")
            self.assertEqual(hr_mf["schemaVersion"], "sota-orca-lane-hub.v2")
            self.assertEqual(tr_mf["rankingDatafeedsCount"], 9)
            self.assertEqual(hr_mf["orchestrationFrameworksCount"], 8)

    def test_v3100_native_workflow_enactor_46skills_14layers_18repo_adrs(self) -> None:
        from sota_mmw import native_workflow_enactor as nwe

        self.assertEqual(len(nwe.CANONICAL_46_SOTA_SKILLS), 46)
        self.assertEqual(len(nwe.CANONICAL_14_LAYERS_MATRIX), 14)
        self.assertEqual(len(nwe.ACTIVE_18_REPOS), 18)

        enacted = nwe.select_workflow_and_skills(
            goal="Enact all SOTA skills and ADRs across grand Orca multi-model ecosystem",
            repo="sota-multi-model-workflows",
            layer="all",
        )
        self.assertTrue(enacted["ok"])
        self.assertEqual(enacted["workflow_id"], "sota-skills-adr-and-orca-grand-workflow")
        self.assertEqual(enacted["layers_count"], 14)
        self.assertEqual(enacted["ranking_feeds_count"], 9)
        self.assertEqual(len(enacted["enactment_sha256"]), 64)
        self.assertIn("antigravity_run_workflow", enacted["runtime_enactments"])
        self.assertIn("orca_supervised_worker", enacted["runtime_enactments"])
        self.assertIn("cc_lead_omc_team", enacted["runtime_enactments"])
        self.assertIn("codex_omx_exec", enacted["runtime_enactments"])
        self.assertEqual(enacted["multi_model_fleet"]["runtime_workers_count"], 11)
        self.assertEqual(enacted["multi_model_fleet"]["orchestration_frameworks_count"], 8)
        self.assertEqual(enacted["multi_model_fleet"]["model_vendors_count"], 6)

        # Execute Grand Workflow #17 deterministically with mocked workflow primitives
        wf17_src = (ROOT / "workflows" / "sota_skills_adr_and_orca_grand_workflow.py").read_text(encoding="utf-8")
        logs_captured: list[str] = []

        async def _fake_agent(prompt: str, schema: dict, role: str = "", type_name: str = "self") -> dict:
            if "skills_verified_count" in schema.get("properties", {}):
                return {
                    "surface_and_doctor_status": "14/14 PASS",
                    "skills_verified_count": 46,
                    "layers_verified": [f"L{i}" for i in range(14)],
                    "adr_catalog_highlights": ["ADR-0018"],
                    "ranking_and_prewall_gates_ok": True,
                    "evidence_grade": "E4",
                }
            return {
                "dual_machine_mesh_status": "Mac M5 Max <-> Noesis 100.110.115.22 ONLINE",
                "orca_automations_and_hubs": ["trading-lanes", "harness-lanes"],
                "runtime_worker_routes": ["cc-lead", "codex-omx", "orca"],
                "single_broker_firewall_intact": True,
                "verdict": "PASS",
            }

        async def _fake_parallel(items: list, fn):
            return [await fn(it) for it in items]

        ns: dict[str, object] = {
            "args": {
                "goal": "Verify v3.10.0 Grand SOTA Workflow",
                "repo": "sota-multi-model-workflows",
                "layer": "all",
            },
            "WORKSPACES": (str(ROOT),),
            "log": lambda *a: logs_captured.append(" ".join(str(x) for x in a)),
            "phase": lambda _name: None,
            "agent": _fake_agent,
            "parallel": _fake_parallel,
        }
        code_obj = compile(wf17_src, "<workflow>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        with mock.patch("workflows._sota_kit.record_workflow_run") as rec17:
            coro = eval(code_obj, ns)
            if coro is not None:
                import asyncio

                asyncio.run(coro)
            rec17.assert_called_once()
        fr = ns.get("final_receipt")
        self.assertIsInstance(fr, dict)
        assert isinstance(fr, dict)
        self.assertTrue(fr["all_gates_passed"])

    def test_v398_m1_m4_multi_model_assign_beads_orca_dag_and_workflow_18(self) -> None:
        from sota_mmw import cc_lead_hub as cch
        from sota_mmw import dual_machine_lanes as dml
        from sota_mmw import native_workflow_enactor as nwe

        with mock.patch.object(cch, "is_running_on_noesis_host", return_value=False):
            env_noesis = cch.build_multi_model_assign_envelope(
                repo="sota-compounding-lab",
                goal="Verify H096 15s dry-powder bid-survival protective filter",
                worker="codex",
                surface="noesis",
            )
            self.assertEqual(env_noesis["schema_version"], "sota-multi-model-assign.v1")
            self.assertEqual(env_noesis["surface"], "noesis")
            self.assertTrue(env_noesis["stdin_spec_file_mode"])
            self.assertEqual(len(env_noesis["assign_sha256"]), 64)
            self.assertIn("--environment", env_noesis["orca_worker_release_template"])

        with self.assertRaises(PermissionError):
            cch.build_multi_model_assign_envelope(
                repo="astrolabe",
                goal="Connect IBKR port=4001",
                worker="codex",
            )

        dag = dml.build_multi_repo_beads_orca_dag(goal="Seal v3.9.8 across 3 stages")
        self.assertEqual(dag["schema_version"], "sota-beads-orca-dag.v1")
        self.assertEqual(dag["stages_count"], 3)
        self.assertGreaterEqual(dag["nodes_count"], 10)
        self.assertEqual(len(dag["dag_sha256"]), 64)
        stage3_nodes = [n for n in dag["nodes"] if n["stage"] == "stage3_org_umbrella_seal"]
        self.assertTrue(all(len(n["depends_on"]) > 0 for n in stage3_nodes))

        st18 = nwe.build_grand_native_workflow_status()
        self.assertEqual(st18["canonical_workflows_count"], 20)

        wf18_src = (ROOT / "workflows" / "multi_model_omc_memory_assign_workflow.py").read_text(encoding="utf-8")
        ns18: dict[str, object] = {
            "__name__": "__main__",
            "args": {"repo": "cc-sota-harness", "worker": "codex", "surface": "local", "fast_deterministic_only": True},
            "log": lambda *_a: None,
            "phase": lambda *_a: None,
        }
        buf18 = io.StringIO()
        code18 = compile(wf18_src, "<workflow>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        with (
            mock.patch.object(kit, "run_preflight_summary", return_value={"sota_doctor": {"status": "PASS"}}),
            mock.patch.object(kit, "record_workflow_run") as rec18,
            redirect_stdout(buf18),
        ):
            r18 = eval(code18, ns18)
            if isinstance(r18, types.CoroutineType):
                asyncio.run(r18)
        out18 = json.loads(buf18.getvalue())
        self.assertTrue(out18["all_gates_passed"])
        self.assertEqual(out18["schema_version"], "3.10.0")
        rec18.assert_called_once()
        self.assertEqual(rec18.call_args.args, ())
        self.assertIn("repo", rec18.call_args.kwargs)
        self.assertIn("workflow_id", rec18.call_args.kwargs)
        self.assertEqual(
            cch.CC_LEAD_CENTRAL_CONTRACT["live_authenticated_worker_routes"],
            ("cc-lead", "codex", "antigravity", "opencode", "dsh"),
        )
        en_rt = nwe.select_workflow_and_skills(goal="Audit pre-wall DSH route", repo="cc-sota-harness")[
            "runtime_enactments"
        ]
        self.assertTrue(en_rt["deepseek_dsh_prewall"].startswith("dsh headless "))
        self.assertIn("--thinking=high -p", en_rt["pi_omp_role_worker"])

    def test_v399_smart_task_model_suitability_router_and_auto_assign(self) -> None:
        from sota_mmw import cc_lead_hub as cch

        self.assertEqual(len(cch.SMART_TASK_SUITABILITY_MATRIX), 8)
        r_quant = cch.smart_route_task(
            "Run CPCV DSR pre-wall DuckDB sweep on H096 collar",
            repo="sota-compounding-lab",
        )
        self.assertEqual(r_quant["suitability_class"], "prewall_quant_sweep_and_gpu_batch")
        self.assertEqual(r_quant["recommended_surface"], "noesis")
        self.assertTrue(r_quant["live_authenticated_route"])

        r_ast = cch.smart_route_task(
            "Run ast-grep multi-file codemod refactor with codebase-memory",
            repo="sota-multi-model-workflows",
        )
        self.assertEqual(r_ast["suitability_class"], "ast_graph_multifile_codemod_refactor")
        self.assertEqual(r_ast["selected_worker"], "cc-lead")
        self.assertEqual(r_ast["selected_model"], "claude-sonnet-5-5")
        self.assertEqual(r_ast["challenger_model"], "gpt-6.2-sol")
        self.assertTrue(r_ast["hephaestus_non_gpt_enforced"])

        r_sec = cch.smart_route_task(
            "Adversarial dimensional stop-loss math & Claude-BugHunter security audit",
            repo="astrolabe",
        )
        self.assertEqual(r_sec["suitability_class"], "adversarial_math_security_and_bug_hunt")
        self.assertEqual(r_sec["selected_worker"], "codex")
        self.assertEqual(r_sec["selected_model"], "gpt-6.2-astra")

        auto_env = cch.build_multi_model_assign_envelope(
            repo="agy-sota-harness",
            goal="Synthesize 18-clone upstream shelf EDGAR filings and parallel-search-evals diagram atlas",
            worker="auto",
        )
        self.assertEqual(auto_env["worker"], "antigravity")
        self.assertEqual(auto_env["smart_route"]["selected_model"], "gemini-4-carbon-high")
        self.assertIn("--placement", auto_env["sota_bus_assign_argv"])
        self.assertIn("--callback-to", auto_env["sota_bus_assign_argv"])

    def test_v3100_quality_directive_claude_1to1_mix_and_noesis_self_routing(self) -> None:
        from sota_mmw import cc_lead_hub as cch
        from sota_mmw import dual_machine_lanes as dml

        # 1. Verify 3 frontier powerhouses + DSH + OMC 1:1 tier env
        env_cfg = cch.CC_LEAD_CENTRAL_CONTRACT["omc_worker_default_env"]
        self.assertEqual(env_cfg["OMC_MODEL_HIGH"], "claude-fable-5-2")
        self.assertEqual(env_cfg["OMC_MODEL_MEDIUM"], "claude-sonnet-5-5")
        self.assertEqual(env_cfg["OMC_MODEL_LOW"], "claude-sonnet-5-5")
        self.assertEqual(len(cch.QUALITY_DIRECTIVE_POWERHOUSE_FLEET), 4)

        # 2. Verify Claude 1:1 telemetry & rebalancer (0.48% historical fable -> promote; 50% -> hold; 80% -> delegate)
        skew_low = cch.audit_claude_1to1_model_mix(
            {"claude-fable-5-2": 2, "claude-opus-5-5": 126, "claude-haiku-5-5": 285}
        )
        self.assertFalse(skew_low["within_1to1_band"])
        self.assertEqual(skew_low["recommended_action"], "PROMOTE_HIGH_AND_ELIMINATE_HAIKU_TO_REACH_50PCT_FABLE")

        bal = cch.audit_claude_1to1_model_mix({"claude-fable-5-2": 50, "claude-opus-5-5": 20, "claude-sonnet-5-5": 30})
        self.assertTrue(bal["within_1to1_band"])
        self.assertEqual(bal["fable_share"], 0.50)
        self.assertEqual(bal["haiku_turns"], 0)

        promoted = cch.rebalance_claude_1to1_route(
            {"suitability_class": "parallel_worktree_feature_and_pytest", "selected_model": "claude-sonnet-5-5"},
            fable_share=0.20,
        )
        self.assertEqual(promoted["selected_model"], "claude-fable-5-2")

        delegated = cch.rebalance_claude_1to1_route(
            {"suitability_class": "general_analysis", "selected_model": "claude-fable-5-2"},
            fable_share=0.75,
        )
        self.assertEqual(delegated["selected_model"], "claude-opus-5-5")

        # 3. Verify host-aware Noesis self-routing (#188(2): never pass --on 100.110.115.22 to Noesis itself)
        with (
            mock.patch.object(cch, "is_running_on_noesis_host", return_value=True),
            mock.patch.object(dml, "is_running_on_noesis_host", return_value=True),
        ):
            self.assertEqual(cch.orca_remote_on_args(use_noesis=True), [])
            env_self = cch.build_multi_model_assign_envelope(
                repo="cc-sota-harness",
                goal="Implement pytest gate",
                worker="codex-sol",
                surface="noesis",
            )
            self.assertNotIn("100.110.115.22", env_self["orca_worker_release_template"])
            lane_self = dml.resolve_dual_machine_lane_plan(
                "cc-sota-harness",
                workload="parallel_worktree_implementation",
                requested_placement="local",
            )
            self.assertEqual(
                lane_self["orca_parent_worktree_selector"],
                "folder:060eb055-834e-4ef2-8198-e3e224a35fbe",
            )
            self.assertNotIn("100.110.115.22", lane_self["orca_worker_start_argv"])

    def test_v3100_adr0024_df12_symbol_ranking_mcp_silence_workflow_run_and_orca_lead_e2e(self) -> None:
        from sota_mmw import cc_lead_hub as cch
        from sota_mmw import compounding_versioning as cv
        from sota_mmw import native_workflow_enactor as nwe
        from sota_mmw import peer_bus_mcp_server as pbm
        from sota_mmw import research_convergence_contract as rcc
        from sota_mmw import symbol_ranking_datafeeds as srd

        # 1. Finalized DF1..DF12 Symbol Ranking DataFeeds & 6 auto-trading strategy routes
        mf = srd.build_symbol_ranking_foundation_manifest()
        self.assertEqual(mf["schema_version"], "sota-symbol-ranking-datafeeds.v3.10")
        self.assertEqual(mf["feed_count"], 12)
        self.assertEqual(mf["strategy_route_count"], 6)
        ok_handoff = srd.evaluate_symbol_ranking_to_strategy_handoff(
            symbol="NVDA",
            strategy_route="HYBRID_50_50_CORE_AND_WAVE2_REENTRY",
            study_date="2026-10-15",
            ts_event_ns=1_792_074_600_000_000_000,
            ts_recv_ns=1_792_074_600_005_000_000,
            decision_ns=1_792_074_600_010_000_000,
            rvol_tod=2.5,
            vol_z_tod=2.7,
            ofi=0.35,
            dry_powder_sec=16.0,
            spread_collar_bps=6.5,
            hard_stop_pct=1.75,
            is_wave2_reentry=True,
            cooldown_elapsed_sec=920.0,
            pullback_held_zero_loss_floor=True,
            broker_port=8787,
        )
        self.assertTrue(ok_handoff["approved"])

        bad_bitemporal = srd.evaluate_symbol_ranking_to_strategy_handoff(
            symbol="NVDA",
            strategy_route="PRE_TRAVEL_EARLY_IGNITION",
            study_date="2026-10-15",
            ts_event_ns=1_792_074_600_030_000_000,
            ts_recv_ns=1_792_074_600_020_000_000,
            decision_ns=1_792_074_600_025_000_000,
            rvol_tod=2.5,
            vol_z_tod=2.7,
            ofi=0.35,
            dry_powder_sec=16.0,
            spread_collar_bps=6.5,
            hard_stop_pct=1.75,
            broker_port=8787,
        )
        self.assertFalse(bad_bitemporal["approved"])
        self.assertTrue(any("BITEMPORAL_PIT_VIOLATION" in v for v in bad_bitemporal["violations"]))

        # 2. 8-Stage Advanced Research Convergence & Live Version status
        adv = rcc.verify_advanced_sota_convergence_practice()
        self.assertTrue(adv["valid"])
        self.assertEqual(adv["stages_count"], 8)
        self.assertEqual(adv["owner_starred_total_audited"], 413)
        self.assertEqual(adv["beyond_starred_sota_count"], 6)
        cv_st = cv.build_compounding_version_status()
        self.assertEqual(cv_st["symbol_ranking_v310_feeds_count"], 12)

        # 3. Canonical Peer-Bus MCP JSON-RPC 2.0 notification silence + isError recovery
        self.assertEqual(len(pbm.TOOLS), 9)
        self.assertIsNone(pbm.handle_jsonrpc_message({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertIsNone(pbm.handle_jsonrpc_message({"jsonrpc": "2.0", "id": None, "method": "ping"}))
        init_resp = pbm.handle_jsonrpc_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertIsNotNone(init_resp)
        assert init_resp is not None
        self.assertEqual(init_resp["id"], 1)

        def _boom(_name: str, _args: dict) -> dict:
            raise RuntimeError("simulated tool failure")

        err_resp = pbm.handle_jsonrpc_message(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "sota_bus_status", "arguments": {}}},
            tool_dispatcher=_boom,
        )
        self.assertIsNotNone(err_resp)
        assert err_resp is not None
        self.assertTrue(err_resp["result"]["isError"])

        # 4. Dry-run guard in _sota_kit + sota-workflow run + sota-cc-hub assign-orca-lead + live HLZ propagation
        with (
            mock.patch.dict("os.environ", {"SOTA_WORKFLOW_DRY_RUN": "1"}),
            mock.patch.object(kit, "bus") as mocked_bus,
        ):
            kit.record_workflow_run(
                repo="cc-sota-harness",
                workflow_id="orca-lead-e2e-research-convergence",
                done_summary="dry",
                verified_by="test",
            )
            mocked_bus.get_conn.assert_not_called()

        enacted = nwe.select_workflow_and_skills(
            goal="Assign orca lead e2e convergence with df12 symbol ranking",
            repo="cc-sota-harness",
        )
        self.assertEqual(enacted["workflow_id"], "orca-lead-e2e-research-convergence")
        self.assertGreaterEqual(enacted["hlz_trials_n"], 90)
        self.assertIn("cross_runtime_workflow_run", enacted["runtime_enactments"])

        with mock.patch.dict("os.environ", {"SOTA_WORKFLOW_DRY_RUN": "1"}):
            run_out = nwe.run_workflow_cli(
                "orca-lead-e2e-research-convergence",
                repo="cc-sota-harness",
                mode="deterministic",
                dry_run=True,
                workflows_dir=ROOT / "workflows",
            )
        self.assertTrue(run_out["ok"])
        self.assertTrue(run_out["receipt"]["all_gates_passed"])

        fleet = cch.probe_cc_runtime_fleet()
        self.assertEqual(fleet["enhanced_runtimes_count"], 8)
        orca_assign = cch.build_orca_lead_e2e_convergence_assignment(repo="cc-sota-harness")
        self.assertEqual(orca_assign["target_lead"], "cc-lead")
        self.assertTrue(orca_assign["non_colliding_message_handoff"])
        self.assertEqual(len(orca_assign["assign_sha256"]), 64)

    def test_v3102_adr0025_zero_kimi_worker_release_env_and_broker_mac_pinning(self) -> None:
        from unittest import mock

        from sota_mmw import cc_lead_hub as cch
        from sota_mmw import dual_machine_lanes as dml

        # 1. Zero Kimi / Moonshot & zero retired models across roster and vendors
        self.assertNotIn("Moonshot AI", dml.CANONICAL_SEVEN_MODEL_VENDORS)
        for wk, meta in cch.RUNTIME_WORKER_ROSTER.items():
            hay = f"{wk} {meta.get('model', '')} {meta.get('vendor', '')}".lower()
            for bad in cch.FORBIDDEN_STALE_AND_REDUNDANT_MODELS:
                self.assertNotIn(bad, hay)

        with self.assertRaises(ValueError):
            cch.build_cc_lead_execution_plan(
                cch.CCLeadPlanRequest(
                    repo="cc-sota-harness",
                    goal="Verify forbidden model rejection",
                    hephaestus_model_override="kimi-" + "k3.1-pro",
                )
            )

        # 2. worker-release uses --environment (never --on) when targeting remote Noesis from Mac
        with mock.patch.object(cch, "is_running_on_noesis_host", return_value=False):
            env_mac = cch.build_multi_model_assign_envelope(
                repo="cc-sota-harness",
                goal="Verify worker-release flag",
                worker="codex-sol",
                surface="noesis",
            )
            self.assertIn("--environment", env_mac["orca_worker_release_template"])
            self.assertNotIn("--on", env_mac["orca_worker_release_template"])

        # 3. Broker-pinned repo (sota-mover-ranker) invoked ON Noesis emits --on 100.93.211.101 + Mac hub 4cf80c7f
        with mock.patch.object(dml, "is_running_on_noesis_host", return_value=True):
            for pl_mode in ("local", "auto"):
                broker_plan = dml.resolve_dual_machine_lane_plan(
                    "sota-mover-ranker",
                    requested_placement=pl_mode,
                )
                self.assertEqual(broker_plan["selected_surface"], "portable_mac_m5_max")
                self.assertEqual(broker_plan["orca_repo_selector"], "name:sota-mover-ranker")
                self.assertEqual(
                    broker_plan["orca_parent_worktree_selector"],
                    "folder:4cf80c7f-96aa-42f1-a25c-a55e7d5e3f3a",
                )
                self.assertIn("100.93.211.101", broker_plan["orca_worker_start_argv"])
                self.assertIn("100.93.211.101", broker_plan["orca_folder_worktree_cmd"])

    def test_v3102_adr0026_nan_inf_fail_closed_decision_ns_wall_and_feed_key_bijection(self) -> None:
        from sota_mmw import cc_lead_hub as cch
        from sota_mmw import symbol_ranking_datafeeds as srd

        base_kw = {
            "symbol": "AAPL",
            "strategy_route": "PRE_TRAVEL_EARLY_IGNITION",
            "study_date": "2026-10-15",
            "ts_event_ns": 1_792_074_600_000_000_000,
            "ts_recv_ns": 1_792_074_600_005_000_000,
            "decision_ns": 1_792_074_600_010_000_000,
            "rvol_tod": 2.45,
            "vol_z_tod": 2.80,
            "ofi": 0.35,
            "dry_powder_sec": 18.5,
            "spread_collar_bps": 7.5,
            "hard_stop_pct": 1.65,
            "broker_port": 8787,
        }
        self.assertTrue(srd.evaluate_symbol_ranking_to_strategy_handoff(**base_kw)["approved"])

        # Defect A: NaN or +-Inf on ANY numeric input must fail closed
        for field_name in ("rvol_tod", "vol_z_tod", "ofi", "dry_powder_sec", "spread_collar_bps", "hard_stop_pct"):
            for bad_val in (float("nan"), float("inf"), float("-inf")):
                res_bad = srd.evaluate_symbol_ranking_to_strategy_handoff(**{**base_kw, field_name: bad_val})
                self.assertFalse(res_bad["approved"], f"{field_name}={bad_val} must fail closed")

        # Defect B: January 2027 decision_ns with study_date='2026-10-15' must fail closed
        jan_2027_ns = 1_800_000_000_000_000_000  # 2027-01-15T08:00:00Z
        res_wall_bypass = srd.evaluate_symbol_ranking_to_strategy_handoff(
            **{
                **base_kw,
                "ts_event_ns": jan_2027_ns - 20,
                "ts_recv_ns": jan_2027_ns - 10,
                "decision_ns": jan_2027_ns,
            }
        )
        self.assertFalse(res_wall_bypass["approved"])
        self.assertTrue(any("PREWALL_DECISION_NS_VIOLATION" in v for v in res_wall_bypass["violations"]))

        # Defect C: Bijective feed_ids == feeds.keys() & all 6 routes resolve required_feeds
        mf = srd.build_symbol_ranking_foundation_manifest()
        for fid in mf["feed_ids"]:
            self.assertIn(fid, mf["feeds"])
            for req_key in (
                "feed_id",
                "short_id",
                "v2_compat_feeds",
                "window_et",
                "upstream",
                "pit_and_microstructure_rules",
            ):
                self.assertIn(req_key, mf["feeds"][fid])
        for r_id in mf["strategy_routes"]:
            resolved_feeds = srd.resolve_route_required_feeds(r_id)
            self.assertGreaterEqual(len(resolved_feeds), 5)

        # Defect D: sota_workflow_run_argv uses --backend claude (never --mode live-cli)
        assign = cch.build_orca_lead_e2e_convergence_assignment(repo="cc-sota-harness")
        self.assertIn("--backend", assign["sota_workflow_run_argv"])
        self.assertNotIn("--mode", assign["sota_workflow_run_argv"])

    def test_v3103_adr0027_grand_merit_promotion_harness_and_wf20(self) -> None:
        from sota_mmw import dual_machine_lanes as dml
        from sota_mmw import merit_promotion_harness as mph

        mf = mph.build_grand_merit_harness_manifest()
        self.assertTrue(mf["ok"])
        self.assertEqual(mf["counts"]["total_execution_lanes"], 7)
        self.assertEqual(mf["counts"]["sim_lanes_never_gated"], 2)
        self.assertEqual(mf["counts"]["paper_accounts_never_gated"], 4)
        self.assertEqual(mf["counts"]["alpaca_paper_accounts"], 3)
        self.assertEqual(mf["counts"]["ibkr_paper_accounts"], 1)
        self.assertEqual(mf["counts"]["live_stage5_lossless_lanes"], 1)
        self.assertEqual(len(mf["harness_sha256"]), 64)
        self.assertEqual(mf["gating_charter"]["sim_lanes"], "NEVER_GATED")
        self.assertEqual(mf["gating_charter"]["paper_farm_4_accounts"], "NEVER_GATED")

        # 1. Fail-closed on NaN/Inf, >2.00% stop, or post-wall study date
        bad_nan = mph.evaluate_merit_ladder(
            mph.MeritStrategyEvidence(
                strategy_id="BAD_NAN",
                study_end_date="2026-10-15",
                max_stop_pct=1.0,
                sim_engine_verified=True,
                prewall_net_1x_bps=float("nan"),
                prewall_net_2x_bps=5.0,
            )
        )
        self.assertEqual(bad_nan["merit_tier"], "HARD_REJECTED_SAFETY_OR_PREWALL")
        self.assertFalse(bad_nan["live_8798_allowed"])

        # 2. Sim-cleared enters P3 Aggressive Crucible NEVER GATED (not Live yet)
        p3 = mph.evaluate_merit_ladder(
            mph.MeritStrategyEvidence(
                strategy_id="FRONTIER_ALPHA_V1",
                study_end_date="2026-10-15",
                max_stop_pct=1.80,
                sim_engine_verified=True,
                prewall_net_1x_bps=12.0,
                prewall_net_2x_bps=4.0,
            )
        )
        self.assertEqual(p3["merit_tier"], "PAPER_P3_AGGRESSIVE_CRUCIBLE")
        self.assertEqual(p3["assigned_lanes"], ["PAPER_P3_ALPACA_AGGRESSIVE_LAB"])
        self.assertFalse(p3["live_8798_allowed"])

        # 3. Negative EB stays on probation in P3 and is hard-blocked from Live
        neg = mph.evaluate_merit_ladder(
            mph.MeritStrategyEvidence(
                strategy_id="MEGA_CAP_NEAR_LOSSLESS_ORB",
                study_end_date="2026-10-15",
                max_stop_pct=0.85,
                sim_engine_verified=True,
                prewall_net_1x_bps=15.0,
                prewall_net_2x_bps=10.0,
                closed_roundtrips=50,
                distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION", "PAPER_P2_ALPACA_BALANCED_RANKER"),
                eb_expectancy_r=-0.05,
                tuning_regime="PROBATION_NEGATIVE_EB_THROTTLE",
            )
        )
        self.assertFalse(neg["live_8798_allowed"])

        # 4. Lossless Foundation Seed enters Stage-5 Live Canary 10%
        canary = mph.evaluate_merit_ladder(
            mph.MeritStrategyEvidence(
                strategy_id="LARGE_CAP_4X_IPO_PRECURSOR_BASKET",
                study_end_date="2026-10-15",
                max_stop_pct=0.85,
                sim_engine_verified=True,
                prewall_net_1x_bps=18.0,
                prewall_net_2x_bps=10.5,
            )
        )
        self.assertEqual(canary["merit_tier"], "STAGE5_LOSSLESS_FOUNDATION_CANARY_10PCT")
        self.assertTrue(canary["live_8798_allowed"])
        self.assertEqual(canary["live_notional_scale"], 0.10)

        # 5. Multi-paper certified (n>=30, >=2 accounts incl. P1, EB>=0.20, PF>=1.35, slip<=3bps) -> 1.00x Full Live
        full = mph.evaluate_merit_ladder(
            mph.MeritStrategyEvidence(
                strategy_id="MEGA_CAP_NEAR_LOSSLESS_ORB",
                study_end_date="2026-10-15",
                max_stop_pct=0.85,
                sim_engine_verified=True,
                prewall_net_1x_bps=22.0,
                prewall_net_2x_bps=14.0,
                closed_roundtrips=36,
                distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION", "PAPER_P2_ALPACA_BALANCED_RANKER"),
                eb_expectancy_r=0.28,
                profit_factor=1.55,
                realized_slippage_bps=1.9,
            )
        )
        self.assertEqual(full["merit_tier"], "STAGE5_LOSSLESS_LIVE_FULL_AUTO")
        self.assertTrue(full["live_8798_allowed"])
        self.assertEqual(full["live_notional_scale"], 1.00)

        # 6. CLI `sota-lanes merit --json` and WF20 deterministic execution both pass
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc_m = dml.main(["merit", "--json"])
        self.assertEqual(rc_m, 0)
        cli_out = json.loads(buf.getvalue())
        self.assertEqual(cli_out["adr"], "ADR-0027")

        wf20_src = (ROOT / "workflows" / "grand_merit_harness_workflow.py").read_text(encoding="utf-8")
        ns20: dict[str, object] = {
            "__name__": "__main__",
            "args": {"repo": "sota-mover-ranker", "fast_deterministic_only": True},
            "log": lambda *_a: None,
            "phase": lambda *_a: None,
        }
        buf20 = io.StringIO()
        with redirect_stdout(buf20):
            exec(compile(wf20_src, "grand_merit_harness_workflow.py", "exec"), ns20)  # noqa: S102
        out20 = json.loads(buf20.getvalue())
        self.assertTrue(out20["all_gates_passed"])
        self.assertEqual(out20["workflow_id"], "grand-merit-harness")

    def test_workflow_handovers_fail_closed_no_unconditional_none_risks(self) -> None:
        import re

        targets = (
            "ecosystem_convergence_workflow.py",
            "orca_lead_e2e_research_convergence_workflow.py",
            "skillopt_gepa_evolution_workflow.py",
        )
        unconditional_re = re.compile(r'^\s*open_risks\s*=\s*["\']none["\']\s*,', re.MULTILINE)
        for wf_name in targets:
            wf_src = (ROOT / "workflows" / wf_name).read_text(encoding="utf-8")
            self.assertIsNone(
                unconditional_re.search(wf_src),
                f"{wf_name} must not pass unconditional open_risks='none'",
            )
            norm = " ".join(wf_src.split())
            self.assertTrue(
                'open_risks="none" if' in norm or 'open_risks=( "none" if' in norm,
                f"{wf_name} must guard open_risks='none' with a conditional expression",
            )


if __name__ == "__main__":
    unittest.main()
