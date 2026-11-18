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
        self.assertEqual(reg["version"], "3.4.0")
        self.assertEqual(manifest["schemaVersion"], "3.4.0")
        self.assertEqual(len(reg["workflows"]), 13)
        self.assertEqual(manifest["workflowCount"], 13)
        ids = [w["id"] for w in reg["workflows"]]
        self.assertEqual(ids, manifest["workflows"])
        self.assertIn("multi-model-ao-convergence", ids)
        self.assertIn("dual-workstation-orca", ids)
        self.assertIn("research-convergence-landing", ids)

        expected_keys = {"id", "script_path", "skill", "agents", "args_schema", "when_to_use"}
        top_level_wf_files = sorted(p for p in (ROOT / "workflows").glob("*.py") if not p.name.startswith("_"))
        self.assertEqual(len(top_level_wf_files), 13)

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
        self.assertTrue(out["deterministic_promotion_gate"]["hard_safety_verified"])
        rec_mock.assert_called_once()

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
        with mock.patch("workflows._sota_kit.os.name", "nt"):
            argv_win = kit.agent_bin_argv(Path("C:/sota-workstation/.agents/bin/sota-workstation"), "status", "--json")
            self.assertEqual(argv_win[0], sys.executable)
            self.assertEqual(argv_win[-2:], ["status", "--json"])
            argv_exe = kit.agent_bin_argv(Path("C:/sota-workstation/orca.exe"), "status")
            self.assertEqual(argv_exe[0], str(Path("C:/sota-workstation/orca.exe")))

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


if __name__ == "__main__":
    unittest.main()
