from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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

    def test_workflow_registry_and_merge_gate(self) -> None:
        reg = json.loads((ROOT / "workflows" / "REGISTRY.json").read_text(encoding="utf-8"))
        self.assertEqual(len(reg["workflows"]), 12)
        ids = {w["id"] for w in reg["workflows"]}
        self.assertIn("multi-model-ao-convergence", ids)
        self.assertIn("dual-workstation-orca", ids)
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


if __name__ == "__main__":
    unittest.main()
