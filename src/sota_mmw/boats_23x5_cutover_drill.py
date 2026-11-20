"""Offline Dec 6, 2026 SIP cutover drill for the four paper lanes (ADR-0031)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

if __name__ == "__main__" and not __package__:
    # Also support running this drill by filename in a checkout.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sota_mmw import unified_cockpit_convergence as cockpit

ALLOWED_PAPER_PORTS = cockpit.ALLOWED_PAPER_PORTS
LIVE_PROHIBITED_PORTS = cockpit.FORBIDDEN_LIVE_PORTS
ADR0022_MAX_STOP_PCT = cockpit.MAX_ADR0022_STOP_PCT
MAX_OVERNIGHT_SPREAD_BPS = cockpit.MAX_OVERNIGHT_BOATS_SPREAD_BPS
DEC6_CUTOVER_DATE = dt.date(2026, 12, 6)
SIP_CUTOVER_UTC = dt.datetime(2026, 12, 7, 2, tzinfo=dt.UTC)
MAX_BOATS_SYMBOLS = 8
PAPER_TARGET_SPREAD_BPS = 28.0
# fromisoformat also accepts arbitrary separators and normalizes overflowed
# offset minutes. Require a dated time and a well-formed offset at this boundary.
OFFSET_TIMESTAMP = re.compile(r"[0-9W-]+[T ][0-9:.,]+(?:Z|[+-](?:[01][0-9]|2[0-3])(?::?[0-5][0-9])?)")

# The modeled Alpaca and IBKR paper subscriptions each retain an eight-symbol
# overnight budget. The consolidated feed is not an execution entitlement.
OVERNIGHT_SYMBOL_CAP_BY_PORT = {8799: 8, 8787: 8, 8797: 8, 4002: 8}


def _dates(table: str) -> frozenset[dt.date]:
    return frozenset(dt.date.fromisoformat(day) for day in table.split())


# NYSE Group's 2024–26 and 2026–28 published cash-equity calendars, including
# the January 9, 2025 national day of mourning. Unknown trade dates fail closed.
# https://www.nyse.com/trade/hours-calendars
XNYS_FIRST_YEAR, XNYS_LAST_YEAR = 2024, 2028
XNYS_HOLIDAYS = _dates("""
2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19 2025-07-04 2025-09-01 2025-11-27 2025-12-25
2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26 2026-12-25
2027-01-01 2027-01-18 2027-02-15 2027-03-26 2027-05-31 2027-06-18 2027-07-05 2027-09-06 2027-11-25 2027-12-24
2028-01-17 2028-02-21 2028-04-14 2028-05-29 2028-06-19 2028-07-04 2028-09-04 2028-11-23 2028-12-25
""")
XNYS_HALF_DAYS = _dates("""
2024-07-03 2024-11-29 2024-12-24
2025-07-03 2025-11-28 2025-12-24
2026-11-27 2026-12-24
2027-11-26
2028-07-03 2028-11-24
""")


def _to_eastern(timestamp: str | dt.datetime) -> dt.datetime:
    if isinstance(timestamp, str):
        if not OFFSET_TIMESTAMP.fullmatch(timestamp):
            raise ValueError("Expected an ISO-8601 timestamp with an offset")
        parsed = dt.datetime.fromisoformat(timestamp)
    else:
        parsed = timestamp
    if not isinstance(parsed, dt.datetime) or parsed.utcoffset() is None:
        raise ValueError("An explicit timestamp offset is required")
    utc = parsed.astimezone(dt.UTC)
    try:
        return utc.astimezone(ZoneInfo("America/New_York"))
    except ZoneInfoNotFoundError:
        # Windows may lack IANA tzdata. For the published calendar years US DST
        # starts at 07:00 UTC on the second March Sunday and ends at 06:00 UTC
        # on the first November Sunday. Work in UTC to avoid ambiguous wall time.
        march = dt.datetime(utc.year, 3, 8, 7, tzinfo=dt.UTC)
        november = dt.datetime(utc.year, 11, 1, 6, tzinfo=dt.UTC)
        start = march + dt.timedelta(days=(6 - march.weekday()) % 7)
        end = november + dt.timedelta(days=(6 - november.weekday()) % 7)
        return utc.astimezone(dt.timezone(dt.timedelta(hours=-4 if start <= utc < end else -5)))


@dataclass(frozen=True)
class _Session:
    segment: str
    feed: str = "BLOCKED"
    trade_date: dt.date | None = None
    sip_available: bool = False
    boats_available: bool = False


def _session_at(et: dt.datetime, sip_enabled: bool, overnight_feed: str) -> _Session:
    day = et.date()
    if not XNYS_FIRST_YEAR <= day.year <= XNYS_LAST_YEAR:
        return _Session("CALENDAR_UNAVAILABLE")
    # Evening sessions belong to tomorrow. Never skip a holiday or weekend to
    # find a later session: the preceding evening must be its immediate neighbor.
    trade_date = day + dt.timedelta(days=1) if et.hour >= 20 else day
    if trade_date.year > XNYS_LAST_YEAR:
        return _Session("CALENDAR_UNAVAILABLE")
    if trade_date.weekday() >= 5 or trade_date in XNYS_HOLIDAYS:
        return _Session("CLOSED")

    if et.hour >= 20 or et.hour < 4:
        # UTP 2026-24 / SEC 34-105780. Sunday opens at 21:00, with a SIP
        # fence each Mon–Thu at 20:00. BOATS remains a separate venue.
        launched = sip_enabled and et >= SIP_CUTOVER_UTC
        sip_open = launched and et.hour != 20
        pause = launched and et.hour == 20 and day.weekday() < 4 and day not in XNYS_HOLIDAYS
        if overnight_feed == "BOATS":
            return _Session("OVERNIGHT_BOATS", "BOATS", trade_date, sip_open, True)
        if sip_open:
            return _Session("OVERNIGHT_23X5_SIP", "SIP_23X5", trade_date, True, True)
        if pause or overnight_feed == "SIP_23X5":
            return _Session("DAILY_PAUSE_CLOSED" if pause else "SIP_CLOSED", boats_available=True)
        return _Session("OVERNIGHT_BOATS", "BOATS", trade_date, boats_available=True)

    close_hour = 13 if trade_date in XNYS_HALF_DAYS else 16
    if et.time() < dt.time(9, 30):
        segment = "PRE_MARKET"
    elif et.hour < close_hour:
        segment = "RTH_CORE"
    elif et.hour < close_hour + 4:
        segment = "AFTER_HOURS"
    else:
        return _Session("CLOSED")
    return _Session(segment, "SIP", trade_date, sip_available=True)


def _finite_number(value: object) -> float | None:
    if type(value) is not int and type(value) is not float:
        return None
    try:
        num = float(value)
    except (OverflowError, ValueError, TypeError):
        return None
    return num if math.isfinite(num) else None


def evaluate_session_boundary_policy(
    et_iso_ts: str | dt.datetime,
    *,
    dec6_235_sip_enabled: bool,
    spread_bps: float,
    order_type: str,
    stop_pct: float,
    active_guardian: bool,
    broker_port: int | None = None,
    symbol_count: int = 1,
    limit_price: float | None = None,
    overnight_feed: str = "AUTO",
) -> dict[str, Any]:
    """Evaluate a paper ticket. Overnight orders model the broker's DAY limit profile.

    AUTO selects BOATS before the SIP opening and holds during weekday SIP
    maintenance. Explicit BOATS or SIP_23X5 selection never substitutes feeds.
    Feed availability describes the modeled schedule, independent of order approval.
    """
    violations: list[str] = []
    warnings: list[str] = []
    et = None
    try:
        et = _to_eastern(et_iso_ts)
    except (TypeError, ValueError, OverflowError, OSError):
        violations.append("INVALID_TIMESTAMP_ISO8601")
    if type(dec6_235_sip_enabled) is not bool:
        violations.append("INVALID_SIP_ENABLE_FLAG")
    if not isinstance(overnight_feed, str) or overnight_feed not in ("AUTO", "BOATS", "SIP_23X5"):
        violations.append("INVALID_OVERNIGHT_FEED")

    session = _Session("INVALID")
    if et is not None and not violations:
        session = _session_at(et, dec6_235_sip_enabled, overnight_feed)
        if session.feed == "BLOCKED":
            violations.append(session.segment)

    if type(broker_port) is not int or broker_port not in ALLOWED_PAPER_PORTS:
        if type(broker_port) is int and broker_port in LIVE_PROHIBITED_PORTS:
            violations.append(f"LIVE_BROKER_PORT_FORBIDDEN:{broker_port}")
        else:
            violations.append("PAPER_PORT_NOT_ALLOWLISTED")

    spread = _finite_number(spread_bps)
    if spread is None or spread < 0:
        violations.append("NON_FINITE_OR_NEGATIVE_SPREAD_BPS")
    stop = _finite_number(stop_pct)
    if stop is None or not 0 < stop <= ADR0022_MAX_STOP_PCT:
        violations.append("ADR0022_STOP_CAP_VIOLATION")
    if type(symbol_count) is not int or symbol_count <= 0:
        violations.append("INVALID_SYMBOL_COUNT")
    if type(active_guardian) is not bool:
        violations.append("INVALID_ACTIVE_GUARDIAN")
    if not isinstance(order_type, str) or not order_type.strip():
        violations.append("INVALID_ORDER_TYPE")

    overnight = session.segment in ("OVERNIGHT_BOATS", "OVERNIGHT_23X5_SIP")
    if overnight or session.segment in ("PRE_MARKET", "AFTER_HOURS"):
        profile = "OVERNIGHT" if overnight else "EXTENDED"
        if not isinstance(order_type, str) or order_type.strip().upper() != "LMT":
            violations.append(f"{profile}_REQUIRES_LMT_ONLY")
        price = _finite_number(limit_price)
        if price is None or price <= 0:
            violations.append("EXTENDED_REQUIRES_POSITIVE_LIMIT_PRICE")
        if active_guardian is not True:
            violations.append(f"{profile}_REQUIRES_ACTIVE_GUARDIAN")
    if overnight:
        if (
            type(broker_port) is int
            and broker_port == 4002
            and et is not None
            and dt.time(3, 50) <= et.time() < dt.time(4)
        ):
            violations.append("IBKR_OVERNIGHT_DAY_EXPIRED")
        if spread is not None and spread > MAX_OVERNIGHT_SPREAD_BPS:
            violations.append(f"OVERNIGHT_SPREAD_EXCEEDS_35BPS:{spread:.2f}")
        elif spread is not None and spread > PAPER_TARGET_SPREAD_BPS:
            warnings.append(f"OVERNIGHT_SPREAD_ABOVE_28BPS_TARGET:{spread:.2f}")
        if type(broker_port) is int and broker_port in ALLOWED_PAPER_PORTS:
            cap = OVERNIGHT_SYMBOL_CAP_BY_PORT.get(broker_port)
            if cap is None:
                violations.append("MISSING_OVERNIGHT_SUBSCRIPTION_CAP")
            elif type(symbol_count) is int:
                if et is not None and et < SIP_CUTOVER_UTC:
                    cap = min(MAX_BOATS_SYMBOLS, cap)
                if symbol_count > cap:
                    violations.append(f"OVERNIGHT_SYMBOL_CAP_EXCEEDED:MAX_{cap}")

    return {
        "approved": not violations,
        "et_timestamp": et.isoformat() if et is not None else None,
        "trade_date": session.trade_date.isoformat() if session.trade_date is not None else None,
        "session_segment": session.segment,
        "feed_route": session.feed,
        "sip_available": session.sip_available,
        "boats_available": session.boats_available,
        "dec6_235_sip_enabled": dec6_235_sip_enabled is True,
        "violations": violations,
        "warnings": warnings,
    }


def run_dec6_23x5_cutover_drill() -> dict[str, Any]:
    """Exercise the public evaluator against independently specified paper tickets."""
    ticket: dict[str, Any] = {
        "dec6_235_sip_enabled": True,
        "spread_bps": 16.0,
        "stop_pct": 1.8,
        "order_type": "LMT",
        "limit_price": 100.00,
        "active_guardian": True,
        "broker_port": 8799,
        "symbol_count": 8,
    }
    # Scenario, ET timestamp, expected session, required refusal (None for approval), ticket overrides.
    scenarios: list[tuple[str, str, str, str | None, dict[str, Any]]] = [
        ("thanksgiving", "11-26T10:00", "CLOSED", "CLOSED", {}),
        ("half_day_postmarket", "11-27T14:00", "AFTER_HOURS", None, {}),
        ("half_day_closed", "11-27T17:00", "CLOSED", "CLOSED", {}),
        ("precutover_boats", "12-03T20:00", "OVERNIGHT_BOATS", None, {}),
        ("boats_cap", "12-03T21:15", "OVERNIGHT_BOATS", "OVERNIGHT_SYMBOL_CAP_EXCEEDED:MAX_8", {"symbol_count": 9}),
        ("friday_last_second", "12-04T19:59:59", "AFTER_HOURS", None, {}),
        ("friday_close", "12-04T20:00", "CLOSED", "CLOSED", {}),
        ("saturday_noon", "12-05T12:00", "CLOSED", "CLOSED", {}),
        ("sunday_midnight", "12-06T00:00", "CLOSED", "CLOSED", {}),
        ("sunday_before_boats", "12-06T19:59", "CLOSED", "CLOSED", {}),
        ("sunday_boats_open", "12-06T20:00", "OVERNIGHT_BOATS", None, {}),
        ("sunday_boats_only", "12-06T20:59", "OVERNIGHT_BOATS", None, {}),
        ("sunday_sip_open", "12-06T21:00", "OVERNIGHT_23X5_SIP", None, {}),
        ("sunday_before_midnight", "12-06T23:59", "OVERNIGHT_23X5_SIP", None, {}),
        ("monday_midnight", "12-07T00:00", "OVERNIGHT_23X5_SIP", None, {}),
        ("ibkr_day_expiry", "12-07T03:50", "OVERNIGHT_23X5_SIP", "IBKR_OVERNIGHT_DAY_EXPIRED", {"broker_port": 4002}),
        ("alpaca_while_ibkr_expired", "12-07T03:50", "OVERNIGHT_23X5_SIP", None, {}),
        ("premarket", "12-07T04:00", "PRE_MARKET", None, {"broker_port": 4002}),
        ("regular_open", "12-07T09:30", "RTH_CORE", None, {}),
        ("extended_market_order", "12-07T18:00", "AFTER_HOURS", "EXTENDED_REQUIRES_LMT_ONLY", {"order_type": "MKT"}),
        ("ordinary_after_hours", "12-07T19:00", "AFTER_HOURS", None, {}),
        ("monday_sip_pause", "12-07T20:00", "DAILY_PAUSE_CLOSED", "DAILY_PAUSE_CLOSED", {}),
        ("tuesday_sip_pause", "12-08T20:59:59", "DAILY_PAUSE_CLOSED", "DAILY_PAUSE_CLOSED", {}),
        ("wednesday_sip_pause", "12-09T20:59", "DAILY_PAUSE_CLOSED", "DAILY_PAUSE_CLOSED", {}),
        ("thursday_sip_pause", "12-10T20:00", "DAILY_PAUSE_CLOSED", "DAILY_PAUSE_CLOSED", {}),
        ("monday_sip_resume", "12-07T21:00", "OVERNIGHT_23X5_SIP", None, {}),
        ("sip_cap", "12-07T21:00", "OVERNIGHT_23X5_SIP", "OVERNIGHT_SYMBOL_CAP_EXCEEDED:MAX_8", {"symbol_count": 9}),
        (
            "overnight_market_order",
            "12-07T21:00",
            "OVERNIGHT_23X5_SIP",
            "OVERNIGHT_REQUIRES_LMT_ONLY",
            {"order_type": "MKT"},
        ),
        ("oversized_stop", "12-07T21:00", "OVERNIGHT_23X5_SIP", "ADR0022_STOP_CAP_VIOLATION", {"stop_pct": 2.5}),
        (
            "missing_guardian",
            "12-07T21:00",
            "OVERNIGHT_23X5_SIP",
            "OVERNIGHT_REQUIRES_ACTIVE_GUARDIAN",
            {"active_guardian": False},
        ),
        ("live_port", "12-07T21:00", "OVERNIGHT_23X5_SIP", "LIVE_BROKER_PORT_FORBIDDEN:8796", {"broker_port": 8796}),
        ("weekly_close", "12-11T20:00", "CLOSED", "CLOSED", {}),
        ("christmas", "12-25T10:00", "CLOSED", "CLOSED", {}),
    ]

    results: list[dict[str, Any]] = []
    for name, instant, segment, refusal, overrides in scenarios:
        result = evaluate_session_boundary_policy(f"2026-{instant}-05:00", **(ticket | overrides))
        approved = refusal is None
        matched = result["approved"] == approved and result["session_segment"] == segment
        results.append(
            {
                "scenario": name,
                "matched_expectation": matched and (refusal is None or refusal in result["violations"]),
                "expected_approved": approved,
                "expected_segment": segment,
                "expected_violation": refusal,
                **result,
            }
        )
    passed = sum(row["matched_expectation"] for row in results)
    out: dict[str, Any] = {
        "schema_version": "sota-boats-23x5-cutover-drill.v1",
        "cutover_date": DEC6_CUTOVER_DATE.isoformat(),
        "cutover_utc": SIP_CUTOVER_UTC.isoformat(),
        "scenarios_total": len(scenarios),
        "scenarios_passed": passed,
        "all_passed": passed == len(scenarios),
        "results": results,
    }
    out["receipt_sha256"] = hashlib.sha256(json.dumps(out, sort_keys=True).encode("utf-8")).hexdigest()
    return out


def main() -> int:
    drill = run_dec6_23x5_cutover_drill()
    print(json.dumps(drill, indent=2))
    return 0 if drill["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
