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
        self.assertGreaterEqual(len(reg["workflows"]), 9)
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "merge_gate.py")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr or r.stdout)


if __name__ == "__main__":
    unittest.main()
