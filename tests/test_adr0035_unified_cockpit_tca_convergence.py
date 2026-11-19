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
    ALLOWED_PAPER_PORTS,
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
    def _base_ok(self) -> PaperTicketPolicyCheck:
        return PaperTicketPolicyCheck(
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

    def test_contract_sha256_is_deterministic_64hex(self) -> None:
        h1 = compute_unified_cockpit_contract_sha256()
        h2 = compute_unified_cockpit_contract_sha256()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)
        self.assertEqual(len(ALLOWED_PAPER_LANES), 4)
        self.assertEqual(ALLOWED_PAPER_PORTS, frozenset({4002, 8787, 8797, 8799}))
        self.assertEqual(FORBIDDEN_LIVE_PORTS, frozenset({4001, 7496, 8796, 8798}))

    def test_paper_ticket_policy_accepts_valid_paper_and_hard_blocks_live_and_bounds(self) -> None:
        ok_req = self._base_ok()
        res_ok = validate_paper_ticket_policy(ok_req)
        self.assertTrue(res_ok["allowed"])
        self.assertEqual(res_ok["schema_version"], UNIFIED_COCKPIT_TCA_SCHEMA_VERSION)
        self.assertEqual(res_ok["violations"], [])

        # All 4 live ports including :8796 fail closed
        for bad_port in (4001, 7496, 8796, 8798):
            res_port = validate_paper_ticket_policy(
                PaperTicketPolicyCheck(**{**ok_req.__dict__, "target_port": bad_port})
            )
            self.assertFalse(res_port["allowed"])
            self.assertIn(f"FORBIDDEN_LIVE_PORT:{bad_port}", res_port["violations"])

        # Arbitrary non-allowlisted ports & missing/bool target_port fail closed
        for bad_port_val in (None, 9999, True, False):
            res_p = validate_paper_ticket_policy(
                PaperTicketPolicyCheck(**{**ok_req.__dict__, "target_port": bad_port_val})  # type: ignore[arg-type]
            )
            self.assertFalse(res_p["allowed"])

        # Embedded live ports, schemes, non-loopback hosts, empty host, and IDNA fullwidth-dot live host fail closed
        fullwidth_live = FORBIDDEN_LIVE_BROKER_HOST.replace(".", "\uff0e")
        for bad_host in (
            "",
            "127.0.0.1:4001",
            "localhost:7496",
            "http://127.0.0.1:8798",
            "127.0.0.1:8796",
            "10.0.0.5",
            FORBIDDEN_LIVE_BROKER_HOST,
            fullwidth_live,
        ):
            res_h = validate_paper_ticket_policy(
                PaperTicketPolicyCheck(**{**ok_req.__dict__, "target_host": bad_host, "target_port": None})
            )
            self.assertFalse(res_h["allowed"], msg=f"Host should be refused: {bad_host!r}")

        # Live lane, ADR-0022 > 2%, NaN/Inf/10**400/bad strings return violations (never raise!)
        res_live_lane = validate_paper_ticket_policy(
            PaperTicketPolicyCheck(**{**ok_req.__dict__, "account_lane": "STAGE5_LIVE"})
        )
        self.assertFalse(res_live_lane["allowed"])
        self.assertTrue(any(v.startswith("FORBIDDEN_LIVE_LANE:") for v in res_live_lane["violations"]))

        for bad_num in (2.01, 0.0, -0.5, math.nan, math.inf, 10**400, "not-a-number", True):
            res_s = validate_paper_ticket_policy(
                PaperTicketPolicyCheck(**{**ok_req.__dict__, "stop_distance_pct": bad_num})  # type: ignore[arg-type]
            )
            self.assertFalse(res_s["allowed"])

        # Rule 612 tick quantization, float qty, oversized qty, oversized client_order_id, non-ASCII symbol
        self.assertFalse(
            validate_paper_ticket_policy(PaperTicketPolicyCheck(**{**ok_req.__dict__, "entry_limit_px": 142.505}))[
                "allowed"
            ]
        )
        self.assertTrue(
            validate_paper_ticket_policy(PaperTicketPolicyCheck(**{**ok_req.__dict__, "entry_limit_px": 0.5432}))[
                "allowed"
            ]
        )
        for bad_qty in (1.9, 0, -5, True, 10**400):
            self.assertFalse(
                validate_paper_ticket_policy(
                    PaperTicketPolicyCheck(**{**ok_req.__dict__, "qty_shares": bad_qty})  # type: ignore[arg-type]
                )["allowed"]
            )
        self.assertFalse(
            validate_paper_ticket_policy(PaperTicketPolicyCheck(**{**ok_req.__dict__, "client_order_id": "x" * 100}))[
                "allowed"
            ]
        )
        self.assertFalse(
            validate_paper_ticket_policy(PaperTicketPolicyCheck(**{**ok_req.__dict__, "symbol": "NVDA\u0661"}))[
                "allowed"
            ]
        )

        # DF5 dilution & BOATS spread cap & non-bool flag rejection
        res_df5 = validate_paper_ticket_policy(
            PaperTicketPolicyCheck(**{**ok_req.__dict__, "sec_dilution_blocked": True})
        )
        self.assertFalse(res_df5["allowed"])
        self.assertIn("DF5_SEC_DILUTION_BLOCKS_LONG", res_df5["violations"])

        res_df5_none = validate_paper_ticket_policy(
            PaperTicketPolicyCheck(**{**ok_req.__dict__, "sec_dilution_blocked": None})  # type: ignore[arg-type]
        )
        self.assertFalse(res_df5_none["allowed"])

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

    def test_validate_tca_markout_payload_and_structural_wall_audit(self) -> None:
        good_tca = {
            "mean_implementation_shortfall_bps": 2.4,
            "markout_1s_bps": 0.8,
            "markout_10s_bps": 1.9,
            "markout_60s_bps": 4.2,
            "markout_300s_bps": 6.5,
            "passive_fill_ratio": 0.62,
        }
        self.assertTrue(validate_tca_markout_payload(good_tca)["valid"])
        bad_tca = {**good_tca, "markout_60s_bps": 10**400, "passive_fill_ratio": 1.5}
        res_bad = validate_tca_markout_payload(bad_tca)
        self.assertFalse(res_bad["valid"])
        self.assertEqual(len(res_bad["errors"]), 2)

        with tempfile.TemporaryDirectory() as td:
            # Comment-only stub MUST fail structural wall audit
            comment_stub = Path(td) / "comment_only.ps1"
            comment_stub.write_text(
                "# function Resolve-SotaEndpointUrl { BeginConnect('127.0.0.1') }\n"
                "# ShowWindowAsync($h, 4) SetWindowPos($h, 0, 0, 0, 0, 0, 0x0014)\n",
                encoding="utf-8",
            )
            bad_audit = audit_noesis_wall_sovereign_routing(comment_stub)
            self.assertFalse(bad_audit["sovereign_local_first"])
            self.assertFalse(bad_audit["zero_focus_steal"])

            # Real structural sovereign script passes
            real_wall = Path(td) / "real_wall.ps1"
            real_wall.write_text(
                'function Resolve-SotaEndpointUrl { $client.BeginConnect("127.0.0.1", $Port, $null, $null) }\n'
                '"--app=$rankerUrl"\n'
                '"--app=$blotterUrl"\n'
                "if ($MoveTradingViewToWall -and $hasDistinctWall) {\n"
                '    Start-Process explorer.exe "TradingView.Desktop"\n'
                "    if ($wallScreen.DeviceName -ne $mainWorkScreen.DeviceName) {\n"
                "        [SotaWallWin32]::ShowWindowAsync($tv.MainWindowHandle, 4)\n"
                "        [SotaWallWin32]::SetWindowPos($tv.MainWindowHandle, [IntPtr]::Zero, 0, 0, 100, 100, 0x0014)\n"
                "    }\n"
                "}\n",
                encoding="utf-8",
            )
            good_audit = audit_noesis_wall_sovereign_routing(real_wall)
            self.assertTrue(good_audit["present"])
            self.assertTrue(good_audit["sovereign_local_first"])
            self.assertTrue(good_audit["zero_focus_steal"])
            self.assertTrue(good_audit["tv_launch_gated"])


if __name__ == "__main__":
    unittest.main()
