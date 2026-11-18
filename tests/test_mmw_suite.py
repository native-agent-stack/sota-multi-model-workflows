from __future__ import annotations

import ast
import asyncio
import dataclasses
import hashlib
import http.server
import io
import json
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

from sota_mmw.ao_lifecycle import (
    AO_MODEL_FAMILIES,
    AO_PLUGGABLE_SLOTS,
    AOLifecycleAttempt,
    evaluate_ao_lifecycle_gate,
    resolve_ao_multi_model_route,
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
        self.assertEqual(reg["version"], "3.3.0")
        self.assertEqual(manifest["schemaVersion"], "3.3.0")
        self.assertEqual(len(reg["workflows"]), 13)
        self.assertEqual(manifest["workflowCount"], 13)
        ids = [w["id"] for w in reg["workflows"]]
        self.assertEqual(ids, manifest["workflows"])
        self.assertIn("multi-model-ao-convergence", ids)
        self.assertIn("dual-workstation-orca", ids)
        self.assertIn("research-convergence-landing", ids)

        expected_keys = {"id", "script_path", "skill", "agents", "args_schema", "when_to_use"}
        for wf in reg["workflows"]:
            self.assertEqual(set(wf.keys()), expected_keys)
            script_name = Path(wf["script_path"]).name
            local_script = ROOT / "workflows" / script_name
            self.assertTrue(local_script.is_file(), msg=f"Missing workflow script: {script_name}")
            src = local_script.read_text(encoding="utf-8")
            self.assertIn("_sota_kit", src)
            compile(src, str(local_script), "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

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
        code = compile(wf_path.read_text(encoding="utf-8"), str(wf_path), "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        ns: dict[str, object] = {
            "__file__": str(wf_path),
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


if __name__ == "__main__":
    unittest.main()
