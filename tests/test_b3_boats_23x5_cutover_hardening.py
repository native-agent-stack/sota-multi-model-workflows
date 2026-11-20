"""Offline broker and market-clock witnesses for the December 2026 cutover."""

import datetime as dt
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sota_mmw import boats_23x5_cutover_drill as drill
from sota_mmw import unified_cockpit_convergence as cockpit


def evaluate(timestamp: Any, **overrides: Any) -> dict[str, Any]:
    ticket: dict[str, Any] = {
        "dec6_235_sip_enabled": True,
        "spread_bps": 10.0,
        "stop_pct": 1.5,
        "broker_port": 8799,
        "order_type": "LMT",
        "limit_price": 101.25,
        "active_guardian": True,
    }
    return drill.evaluate_session_boundary_policy(timestamp, **(ticket | overrides))


class TestCutover(unittest.TestCase):
    def test_seat_e4_boundaries(self):
        # Each row specifies the selected paper feed, separately from order eligibility.
        cases = [
            ("11-26T10:00", "CLOSED", "BLOCKED", False),
            ("11-27T14:00", "AFTER_HOURS", "SIP", True),
            ("12-04T20:00", "CLOSED", "BLOCKED", False),
            ("12-05T12:00", "CLOSED", "BLOCKED", False),
            ("12-06T00:00", "CLOSED", "BLOCKED", False),
            ("12-06T19:59", "CLOSED", "BLOCKED", False),
            ("12-06T20:00", "OVERNIGHT_BOATS", "BOATS", True),
            ("12-06T20:59", "OVERNIGHT_BOATS", "BOATS", True),
            ("12-06T21:00", "OVERNIGHT_23X5_SIP", "SIP_23X5", True),
            ("12-06T23:59", "OVERNIGHT_23X5_SIP", "SIP_23X5", True),
            ("12-07T00:00", "OVERNIGHT_23X5_SIP", "SIP_23X5", True),
            ("12-07T03:50", "OVERNIGHT_23X5_SIP", "SIP_23X5", True),
            ("12-07T04:00", "PRE_MARKET", "SIP", True),
            ("12-07T19:00", "AFTER_HOURS", "SIP", True),
            ("12-07T20:00", "DAILY_PAUSE_CLOSED", "BLOCKED", False),
            ("12-07T21:00", "OVERNIGHT_23X5_SIP", "SIP_23X5", True),
            ("12-11T20:00", "CLOSED", "BLOCKED", False),
        ]
        for instant, segment, feed, approved in cases:
            with self.subTest(instant=instant):
                result = evaluate(f"2026-{instant}:00-05:00")
                self.assertEqual(
                    (result["session_segment"], result["feed_route"], result["approved"]), (segment, feed, approved)
                )
                self.assertEqual(result["sip_available"], feed in {"SIP", "SIP_23X5"})
                self.assertEqual(bool(result["violations"]), not approved)

    def test_maintenance_all_four_evenings_and_explicit_boats(self):
        for day in range(7, 11):
            for time, segment in [
                ("19:59:59", "AFTER_HOURS"),
                ("20:00:00", "DAILY_PAUSE_CLOSED"),
                ("20:59:59", "DAILY_PAUSE_CLOSED"),
                ("21:00:00", "OVERNIGHT_23X5_SIP"),
            ]:
                instant = f"2026-12-{day:02}T{time}-05:00"
                with self.subTest(instant=instant):
                    result = evaluate(instant)
                    self.assertEqual(result["session_segment"], segment)
                    self.assertEqual(result["approved"], segment != "DAILY_PAUSE_CLOSED")
                    if segment == "DAILY_PAUSE_CLOSED":
                        self.assertTrue(result["boats_available"])
                        boats = evaluate(instant, overnight_feed="BOATS")
                        self.assertTrue(boats["approved"])
                        self.assertEqual(boats["feed_route"], "BOATS")
                        self.assertFalse(boats["sip_available"])

    def test_weekend_and_holiday_closures_and_resumption(self):
        for instant in (
            "12-04T20:30",
            "12-05T21:00",
            "12-06T10:00",
            "12-06T19:59:59",
            "11-25T20:00",
            "11-26T03:59",
            "12-24T21:00",
            "12-25T00:00",
            "12-25T10:00",
            "12-25T21:00",
            "12-27T19:59",
        ):
            with self.subTest(instant=instant):
                result = evaluate(f"2026-{instant}-05:00")
                self.assertEqual(result["session_segment"], "CLOSED")
                self.assertFalse(result["approved"])
                self.assertIsNone(result["trade_date"])
                self.assertFalse(result["boats_available"])
        for instant, trade_date, feed in [
            ("11-26T20:00", "2026-11-27", "BOATS"),
            ("12-27T20:00", "2026-12-28", "BOATS"),
            ("12-27T21:00", "2026-12-28", "SIP_23X5"),
        ]:
            with self.subTest(instant=instant):
                result = evaluate(f"2026-{instant}-05:00")
                self.assertEqual(
                    (result["approved"], result["trade_date"], result["feed_route"]), (True, trade_date, feed)
                )

    def test_half_day_exact_edges(self):
        for date in ("2026-11-27", "2026-12-24"):
            for time, segment in [
                ("12:59:59", "RTH_CORE"),
                ("13:00:00", "AFTER_HOURS"),
                ("16:59:59", "AFTER_HOURS"),
                ("17:00:00", "CLOSED"),
            ]:
                with self.subTest(date=date, time=time):
                    result = evaluate(f"{date}T{time}-05:00")
                    self.assertEqual(result["session_segment"], segment)
                    self.assertEqual(result["approved"], segment != "CLOSED")

    def test_trade_date_and_absolute_cutover(self):
        for instant in (
            "2026-12-06T20:00:00-05:00",
            "2026-12-06T23:59:59-05:00",
            "2026-12-07T00:00:00-05:00",
            "2026-12-07T08:59:59Z",
        ):
            with self.subTest(instant=instant):
                self.assertEqual(evaluate(instant)["trade_date"], "2026-12-07")
        for instant, route in [
            ("2026-12-07T00:59:59Z", "BLOCKED"),
            ("2026-12-07T01:00:00Z", "BOATS"),
            ("2026-12-07T01:59:59Z", "BOATS"),
            ("2026-12-07T02:00:00Z", "SIP_23X5"),
            ("2026-07-13T00:00:00Z", "BOATS"),
            ("2027-07-12T01:00:00Z", "SIP_23X5"),
        ]:
            with self.subTest(instant=instant):
                self.assertEqual(evaluate(dt.datetime.fromisoformat(instant))["feed_route"], route)
        for instant in ("2026-12-03T21:00:00-05:00", "2026-12-06T20:59:59-05:00"):
            self.assertFalse(evaluate(instant, overnight_feed="SIP_23X5")["approved"])

    def test_ibkr_expiry_is_broker_specific_in_both_regimes(self):
        for date, flag in [("2026-12-04", False), ("2026-12-07", True)]:
            for time, ibkr_ok in [("03:49:59", True), ("03:50:00", False), ("03:59:59", False), ("04:00:00", True)]:
                instant = f"{date}T{time}-05:00"
                with self.subTest(instant=instant):
                    ibkr = evaluate(instant, broker_port=4002, dec6_235_sip_enabled=flag)
                    alpaca = evaluate(instant, dec6_235_sip_enabled=flag)
                    self.assertTrue(alpaca["approved"])
                    self.assertEqual(ibkr["feed_route"], alpaca["feed_route"])
                    self.assertEqual(ibkr["approved"], ibkr_ok)
                    self.assertEqual("IBKR_OVERNIGHT_DAY_EXPIRED" in ibkr["violations"], not ibkr_ok)

    def test_eastern_clock_without_system_tzdata(self):
        with patch.object(drill, "ZoneInfo", side_effect=drill.ZoneInfoNotFoundError):
            for utc, eastern in [
                ("2026-03-08T06:59:59Z", "2026-03-08T01:59:59-05:00"),
                ("2026-03-08T07:00:00Z", "2026-03-08T03:00:00-04:00"),
                ("2026-11-01T05:59:59Z", "2026-11-01T01:59:59-04:00"),
                ("2026-11-01T06:00:00Z", "2026-11-01T01:00:00-05:00"),
            ]:
                with self.subTest(utc=utc):
                    result = evaluate(utc)
                    self.assertEqual(result["et_timestamp"], eastern)
                    self.assertFalse(result["approved"])

    def test_port_parity_and_strict_positive_allowlist(self):
        self.assertEqual(drill.LIVE_PROHIBITED_PORTS, cockpit.FORBIDDEN_LIVE_PORTS)
        self.assertEqual(drill.ALLOWED_PAPER_PORTS, cockpit.ALLOWED_PAPER_PORTS)
        for port in (
            *cockpit.ALLOWED_PAPER_PORTS,
            *cockpit.FORBIDDEN_LIVE_PORTS,
            None,
            443,
            9999,
            "4002",
            4002.0,
            True,
            [],
            10**5000,
        ):
            with self.subTest(port_type=type(port)):
                expected = type(port) is int and port in (4002, 8787, 8797, 8799)
                result = evaluate("2026-12-07T10:00:00-05:00", broker_port=port)
                self.assertEqual(result["approved"], expected)
                if type(port) is int and port in cockpit.FORBIDDEN_LIVE_PORTS:
                    self.assertIn(f"LIVE_BROKER_PORT_FORBIDDEN:{port}", result["violations"])

    def test_strict_flag_and_timestamps(self):
        instant = "2026-12-06T21:00:00-05:00"
        self.assertEqual(evaluate(instant, dec6_235_sip_enabled=False)["feed_route"], "BOATS")
        for flag in ("false", "true", 0, 1, None, []):
            with self.subTest(flag=flag):
                result = evaluate(instant, dec6_235_sip_enabled=flag)
                self.assertFalse(result["approved"])
                self.assertFalse(result["dec6_235_sip_enabled"])
        for stamp in (
            dt.datetime(2026, 12, 7, 10),
            "2026-12-07T10:00",
            "2026-12-07",
            "2026-12-07X10:00-05:00",
            "2026-12-07T10:00-04:99",
            "nonsense",
            None,
            [],
            10**5000,
            "0001-01-01T00:00:00Z",
            "9999-12-31T23:00:00-05:00",
        ):
            with self.subTest(timestamp_type=type(stamp)):
                result = evaluate(stamp)
                self.assertFalse(result["approved"])
                self.assertEqual(result["feed_route"], "BLOCKED")
                self.assertTrue(result["violations"])

    def test_malformed_numbers_never_raise_or_warn(self):
        for field, violation in [
            ("spread_bps", "NON_FINITE_OR_NEGATIVE_SPREAD_BPS"),
            ("stop_pct", "ADR0022_STOP_CAP_VIOLATION"),
        ]:
            for bad in (None, "1", True, float("nan"), float("inf"), -float("inf"), 10**400, -1, []):
                with self.subTest(field=field, bad=bad):
                    result = evaluate("2026-12-06T22:00:00-05:00", **{field: bad})
                    self.assertIn(violation, result["violations"])
                    self.assertFalse(result["approved"])
                    self.assertEqual(result["warnings"], [])

    def test_priced_limit_and_guardian_in_every_extended_session(self):
        unpriced = drill.evaluate_session_boundary_policy(
            "2026-12-07T18:00-05:00",
            dec6_235_sip_enabled=True,
            order_type="LMT",
            active_guardian=True,
            broker_port=8799,
            spread_bps=10,
            stop_pct=1.0,
        )
        self.assertFalse(unpriced["approved"])
        self.assertEqual(unpriced["violations"], ["EXTENDED_REQUIRES_POSITIVE_LIMIT_PRICE"])
        for time in ("04:00", "09:29", "16:00", "18:00", "21:00"):
            instant = f"2026-12-07T{time}-05:00"
            for overrides in (
                {"order_type": "MKT"},
                {"active_guardian": False},
                {"active_guardian": "true"},
                {"order_type": "MKT", "active_guardian": False},
                *({"limit_price": price} for price in (None, "10", 0, -1, True, float("inf"), float("nan"), 10**400)),
            ):
                with self.subTest(time=time, override=overrides):
                    self.assertFalse(evaluate(instant, **overrides)["approved"])
            self.assertTrue(evaluate(instant)["approved"])
        self.assertTrue(
            evaluate("2026-12-07T09:30-05:00", order_type="MKT", limit_price=None, active_guardian=False)["approved"]
        )

    def test_overnight_symbol_and_risk_boundaries(self):
        for port in (8799, 4002):
            for flag in (False, True):
                instant = "2026-12-06T22:00-05:00"
                for count in (0, 1, 8, 9, None, True, "1", [], 10**5000):
                    with self.subTest(port=port, flag=flag, count_type=type(count)):
                        result = evaluate(instant, broker_port=port, dec6_235_sip_enabled=flag, symbol_count=count)
                        self.assertEqual(result["approved"], type(count) is int and 1 <= count <= 8)
                for spread, approved, warned in [
                    (28, True, False),
                    (28.01, True, True),
                    (35, True, True),
                    (35.01, False, False),
                ]:
                    with self.subTest(port=port, flag=flag, spread=spread):
                        result = evaluate(
                            instant, broker_port=port, dec6_235_sip_enabled=flag, spread_bps=spread, stop_pct=2
                        )
                        self.assertEqual((result["approved"], bool(result["warnings"])), (approved, warned))
        for stop in (0, 2.0001):
            self.assertFalse(evaluate("2026-12-07T10:00-05:00", stop_pct=stop)["approved"])

    def test_subscription_cap_tracks_paper_lane_across_feed_changes(self):
        self.assertEqual(set(drill.OVERNIGHT_SYMBOL_CAP_BY_PORT), cockpit.ALLOWED_PAPER_PORTS)
        instant = "2026-12-07T22:00-05:00"
        with patch.dict(drill.OVERNIGHT_SYMBOL_CAP_BY_PORT, {8799: 3}):
            for feed in ("BOATS", "SIP_23X5"):
                self.assertFalse(evaluate(instant, symbol_count=4, overnight_feed=feed)["approved"])
                self.assertTrue(evaluate(instant, symbol_count=3, overnight_feed=feed)["approved"])
                self.assertTrue(evaluate(instant, symbol_count=4, broker_port=4002, overnight_feed=feed)["approved"])
        with patch.dict(drill.OVERNIGHT_SYMBOL_CAP_BY_PORT, clear=True):
            result = evaluate(instant)
            self.assertIn("MISSING_OVERNIGHT_SUBSCRIPTION_CAP", result["violations"])
            self.assertFalse(result["approved"])

    def test_calendar_coverage_and_year_boundary(self):
        for stamp, segment in [
            ("2025-01-09T10:00-05:00", "CLOSED"),
            ("2026-12-31T21:00-05:00", "CLOSED"),
            ("2027-01-03T21:00-05:00", "OVERNIGHT_23X5_SIP"),
            ("2027-12-31T10:00-05:00", "RTH_CORE"),
            ("2028-07-03T14:00-04:00", "AFTER_HOURS"),
            ("2029-01-02T10:00-05:00", "CALENDAR_UNAVAILABLE"),
        ]:
            with self.subTest(stamp=stamp):
                self.assertEqual(evaluate(stamp)["session_segment"], segment)
        self.assertFalse(evaluate("2029-01-02T10:00-05:00")["approved"])

    def test_invalid_route_and_rth_field_types(self):
        for overrides in (
            {"overnight_feed": []},
            {"overnight_feed": "sip?"},
            {"order_type": None},
            {"active_guardian": "false"},
        ):
            with self.subTest(overrides=overrides):
                self.assertFalse(evaluate("2026-12-07T10:00-05:00", **overrides)["approved"])
