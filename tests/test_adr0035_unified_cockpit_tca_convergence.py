from __future__ import annotations

import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sota_mmw.unified_cockpit_convergence import (
    ALLOWED_PAPER_LANES,
    FORBIDDEN_LIVE_BROKER_HOST,
    FORBIDDEN_LIVE_PORTS,
    REQUIRED_PERSPECTIVE_RELPATHS,
    UNIFIED_COCKPIT_TCA_SCHEMA_VERSION,
    PaperTicketPolicyCheck,
    audit_noesis_wall_sovereign_routing,
    compute_unified_cockpit_contract_sha256,
    validate_paper_ticket_policy,
    validate_tca_markout_payload,
    verify_local_perspective_assets,
)


class TestAdr0035UnifiedCockpitTcaConvergence(unittest.TestCase):
    def test_contract_sha256_is_deterministic_64hex(self) -> None:
        h1 = compute_unified_cockpit_contract_sha256()
        h2 = compute_unified_cockpit_contract_sha256()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)
        self.assertEqual(len(ALLOWED_PAPER_LANES), 4)
        self.assertEqual(FORBIDDEN_LIVE_PORTS, frozenset({4001, 7496, 8798}))

    def test_paper_ticket_policy_accepts_valid_paper_and_hard_blocks_live_and_bounds(self) -> None:
        ok_req = PaperTicketPolicyCheck(
            account_lane="ALPACA_PAPER_P1",
            symbol="NVDA",
            side="buy",
            qty_shares=25,
            entry_limit_px=142.50,
            stop_distance_pct=1.25,
            target_port=8799,
            target_host="127.0.0.1",
            spread_bps=6.5,
            is_overnight_boats=False,
            sec_dilution_blocked=False,
            client_order_id="sota-cockpit-nvda-001",
        )
        res_ok = validate_paper_ticket_policy(ok_req)
        self.assertTrue(res_ok["allowed"])
        self.assertEqual(res_ok["schema_version"], UNIFIED_COCKPIT_TCA_SCHEMA_VERSION)
        self.assertEqual(res_ok["violations"], [])

        # Live broker host, live ports, live lane, stop > 2%, NaN, DF5 dilution, BOATS spread > 35 bps all fail closed
        for bad_port in (4001, 7496, 8798):
            res_port = validate_paper_ticket_policy(
                PaperTicketPolicyCheck(**{**ok_req.__dict__, "target_port": bad_port})
            )
            self.assertFalse(res_port["allowed"])
            self.assertIn(f"FORBIDDEN_LIVE_PORT:{bad_port}", res_port["violations"])

        res_live_host = validate_paper_ticket_policy(
            PaperTicketPolicyCheck(**{**ok_req.__dict__, "target_host": FORBIDDEN_LIVE_BROKER_HOST})
        )
        self.assertFalse(res_live_host["allowed"])
        self.assertIn("FORBIDDEN_LIVE_BROKER_HOST", res_live_host["violations"])

        res_live_lane = validate_paper_ticket_policy(
            PaperTicketPolicyCheck(**{**ok_req.__dict__, "account_lane": "STAGE5_LIVE"})
        )
        self.assertFalse(res_live_lane["allowed"])
        self.assertTrue(any(v.startswith("FORBIDDEN_LIVE_LANE:") for v in res_live_lane["violations"]))

        res_stop_cap = validate_paper_ticket_policy(
            PaperTicketPolicyCheck(**{**ok_req.__dict__, "stop_distance_pct": 2.01})
        )
        self.assertFalse(res_stop_cap["allowed"])
        self.assertTrue(any(v.startswith("ADR0022_STOP_PCT_VIOLATION") for v in res_stop_cap["violations"]))

        res_nan = validate_paper_ticket_policy(
            PaperTicketPolicyCheck(**{**ok_req.__dict__, "stop_distance_pct": math.nan})
        )
        self.assertFalse(res_nan["allowed"])

        res_df5 = validate_paper_ticket_policy(
            PaperTicketPolicyCheck(**{**ok_req.__dict__, "sec_dilution_blocked": True})
        )
        self.assertFalse(res_df5["allowed"])
        self.assertIn("DF5_SEC_DILUTION_BLOCKS_LONG", res_df5["violations"])

        res_boats = validate_paper_ticket_policy(
            PaperTicketPolicyCheck(**{**ok_req.__dict__, "is_overnight_boats": True, "spread_bps": 42.0})
        )
        self.assertFalse(res_boats["allowed"])
        self.assertTrue(any(v.startswith("BOATS_SPREAD_CAP_VIOLATION") for v in res_boats["violations"]))

    def test_verify_local_perspective_assets_handles_complete_and_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            miss = verify_local_perspective_assets(root)
            self.assertFalse(miss["ready"])
            self.assertEqual(miss["present_count"], 0)
            for rel in REQUIRED_PERSPECTIVE_RELPATHS:
                fp = root / rel
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_bytes(b"ok")
            ok = verify_local_perspective_assets(root)
            self.assertTrue(ok["ready"])
            self.assertEqual(ok["present_count"], len(REQUIRED_PERSPECTIVE_RELPATHS))

    def test_validate_tca_markout_payload_and_wall_audit(self) -> None:
        good_tca = {
            "mean_implementation_shortfall_bps": 2.4,
            "markout_1s_bps": 0.8,
            "markout_10s_bps": 1.9,
            "markout_60s_bps": 4.2,
            "markout_300s_bps": 6.5,
            "passive_fill_ratio": 0.62,
        }
        self.assertTrue(validate_tca_markout_payload(good_tca)["valid"])
        bad_tca = {**good_tca, "markout_60s_bps": math.inf, "passive_fill_ratio": 1.5}
        res_bad = validate_tca_markout_payload(bad_tca)
        self.assertFalse(res_bad["valid"])
        self.assertEqual(len(res_bad["errors"]), 2)

        with tempfile.TemporaryDirectory() as td:
            wall = Path(td) / "wall.ps1"
            wall.write_text(
                "function Resolve-SotaEndpointUrl { return 'http://127.0.0.1:8787' }\nShowWindowAsync 0x0014\n",
                encoding="utf-8",
            )
            audit = audit_noesis_wall_sovereign_routing(wall)
            self.assertTrue(audit["present"])
            self.assertTrue(audit["sovereign_local_first"])
            self.assertTrue(audit["zero_focus_steal"])


if __name__ == "__main__":
    unittest.main()
