"""Deterministic Dec 6, 2026 23/5 SIP Cutover & Overnight BOATS Verification Drill (`ADR-0031`).

Provides fail-closed session-boundary policy checks across regular ETH/RTH, pre-cutover
`OVERNIGHT_BOATS` (`20:00-04:00 ET`), and post-Dec-6 `OVERNIGHT_23X5_SIP` while preserving
`LMT`-only, spread cap, active guardian, `ADR-0022 <= 2.00%` stop cap, and live-broker port refusal.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from typing import Any

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment,misc]
    ZoneInfoNotFoundError = Exception  # type: ignore[assignment,misc]

DEC6_CUTOVER_DATE = dt.date(2026, 12, 6)
MAX_BOATS_SYMBOLS = 8
MAX_OVERNIGHT_SPREAD_BPS = 35.0
PAPER_TARGET_SPREAD_BPS = 28.0
ADR0022_MAX_STOP_PCT = 2.00
LIVE_PROHIBITED_PORTS = (4001, 7496, 8798)


def _us_eastern_tz_fallback(naive_or_utc: dt.datetime, *, is_utc: bool) -> dt.tzinfo:
    """Compute US Eastern EST/EDT fixed offset cleanly even when OS lacks ``tzdata``."""
    yr = naive_or_utc.year
    # Second Sunday of March at 02:00 EST (= 07:00 UTC), first Sunday of November at 02:00 EDT (= 06:00 UTC)
    mar1 = dt.date(yr, 3, 1)
    dst_start_day = 1 + ((6 - mar1.weekday()) % 7) + 7
    nov1 = dt.date(yr, 11, 1)
    dst_end_day = 1 + ((6 - nov1.weekday()) % 7)
    if is_utc:
        utc_naive = naive_or_utc.replace(tzinfo=None)
        dst_start = dt.datetime(yr, 3, dst_start_day, 7, 0)
        dst_end = dt.datetime(yr, 11, dst_end_day, 6, 0)
        in_dst = dst_start <= utc_naive < dst_end
    else:
        loc_naive = naive_or_utc.replace(tzinfo=None)
        dst_start = dt.datetime(yr, 3, dst_start_day, 2, 0)
        dst_end = dt.datetime(yr, 11, dst_end_day, 2, 0)
        in_dst = dst_start <= loc_naive < dst_end
    return dt.timezone(dt.timedelta(hours=-4 if in_dst else -5), name="EDT" if in_dst else "EST")


def _to_eastern(parsed: dt.datetime) -> dt.datetime:
    if ZoneInfo is not None:
        try:
            et_zone = ZoneInfo("America/New_York")
            return parsed.replace(tzinfo=et_zone) if parsed.tzinfo is None else parsed.astimezone(et_zone)
        except ZoneInfoNotFoundError:
            pass
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=_us_eastern_tz_fallback(parsed, is_utc=False))
    as_utc = parsed.astimezone(dt.UTC)
    return as_utc.astimezone(_us_eastern_tz_fallback(as_utc, is_utc=True))


def evaluate_session_boundary_policy(
    et_iso_ts: str,
    *,
    dec6_235_sip_enabled: bool,
    spread_bps: float,
    order_type: str,
    stop_pct: float,
    active_guardian: bool,
    broker_port: int | None = None,
    symbol_count: int = 1,
) -> dict[str, Any]:
    """Evaluate fail-closed session routing, BOATS/23x5 SIP cutover, stop cap & live-port invariants."""
    violations: list[str] = []
    warnings: list[str] = []

    try:
        parsed = dt.datetime.fromisoformat(str(et_iso_ts))
    except ValueError:
        return {
            "approved": False,
            "session_segment": "INVALID",
            "feed_route": "BLOCKED",
            "violations": ["INVALID_TIMESTAMP_ISO8601"],
            "warnings": [],
        }

    et_dt = _to_eastern(parsed)

    if (
        not isinstance(spread_bps, (int, float))
        or isinstance(spread_bps, bool)
        or not math.isfinite(float(spread_bps))
        or float(spread_bps) < 0.0
    ):
        violations.append("NON_FINITE_OR_NEGATIVE_SPREAD_BPS")
    if (
        not isinstance(stop_pct, (int, float))
        or isinstance(stop_pct, bool)
        or not math.isfinite(float(stop_pct))
        or float(stop_pct) <= 0.0
        or float(stop_pct) > ADR0022_MAX_STOP_PCT
    ):
        violations.append("ADR0022_STOP_CAP_VIOLATION")
    if not isinstance(symbol_count, int) or isinstance(symbol_count, bool) or symbol_count <= 0:
        violations.append("INVALID_SYMBOL_COUNT")
    if broker_port is not None and broker_port in LIVE_PROHIBITED_PORTS:
        violations.append(f"LIVE_BROKER_PORT_FORBIDDEN:{broker_port}")

    hhmm = et_dt.hour * 100 + et_dt.minute
    is_overnight = hhmm >= 2000 or hhmm < 400
    is_rth = 930 <= hhmm < 1600
    if is_rth:
        session_segment = "RTH_CORE"
        feed_route = "SIP"
    elif is_overnight:
        post_cutover_active = et_dt.date() >= DEC6_CUTOVER_DATE and bool(dec6_235_sip_enabled)
        if post_cutover_active:
            session_segment = "OVERNIGHT_23X5_SIP"
            feed_route = "SIP_23X5"
        else:
            session_segment = "OVERNIGHT_BOATS"
            feed_route = "BOATS"
    elif hhmm < 930:
        session_segment = "PRE_MARKET"
        feed_route = "SIP"
    else:
        session_segment = "AFTER_HOURS"
        feed_route = "SIP"

    norm_order = str(order_type or "").strip().upper()
    if is_overnight:
        if norm_order != "LMT":
            violations.append(f"OVERNIGHT_REQUIRES_LMT_ONLY:{norm_order or 'UNSET'}")
        if not active_guardian:
            violations.append("OVERNIGHT_REQUIRES_ACTIVE_GUARDIAN")
        if math.isfinite(float(spread_bps)) and float(spread_bps) > MAX_OVERNIGHT_SPREAD_BPS:
            violations.append(f"OVERNIGHT_SPREAD_EXCEEDS_35BPS:{float(spread_bps):.2f}")
        elif math.isfinite(float(spread_bps)) and float(spread_bps) > PAPER_TARGET_SPREAD_BPS:
            warnings.append(f"OVERNIGHT_SPREAD_ABOVE_28BPS_TARGET:{float(spread_bps):.2f}")
        if session_segment == "OVERNIGHT_BOATS" and symbol_count > MAX_BOATS_SYMBOLS:
            violations.append(f"BOATS_SYMBOL_CAP_EXCEEDED:{symbol_count}>{MAX_BOATS_SYMBOLS}")

    return {
        "approved": len(violations) == 0,
        "et_timestamp": et_dt.isoformat(),
        "session_segment": session_segment,
        "feed_route": feed_route,
        "dec6_235_sip_enabled": bool(dec6_235_sip_enabled),
        "violations": violations,
        "warnings": warnings,
    }


def run_dec6_23x5_cutover_drill() -> dict[str, Any]:
    """Execute the 10-scenario deterministic Dec 6, 2026 23/5 SIP cutover drill."""
    scenarios: list[tuple[str, dict[str, Any], bool, str]] = [
        (
            "01_after_hours_195959_sip",
            {
                "et_iso_ts": "2026-12-04T19:59:59-05:00",
                "dec6_235_sip_enabled": False,
                "spread_bps": 12.0,
                "order_type": "LMT",
                "stop_pct": 1.80,
                "active_guardian": True,
                "broker_port": 4002,
                "symbol_count": 4,
            },
            True,
            "AFTER_HOURS",
        ),
        (
            "02_pre_cutover_200000_boats_ok",
            {
                "et_iso_ts": "2026-12-04T20:00:00-05:00",
                "dec6_235_sip_enabled": False,
                "spread_bps": 18.0,
                "order_type": "LMT",
                "stop_pct": 1.80,
                "active_guardian": True,
                "broker_port": 4002,
                "symbol_count": 8,
            },
            True,
            "OVERNIGHT_BOATS",
        ),
        (
            "03_post_cutover_200000_sip_23x5_ok",
            {
                "et_iso_ts": "2026-12-06T20:00:00-05:00",
                "dec6_235_sip_enabled": True,
                "spread_bps": 16.0,
                "order_type": "LMT",
                "stop_pct": 1.80,
                "active_guardian": True,
                "broker_port": 4002,
                "symbol_count": 12,
            },
            True,
            "OVERNIGHT_23X5_SIP",
        ),
        (
            "04_overnight_035959_sip_23x5_ok",
            {
                "et_iso_ts": "2026-12-07T03:59:59-05:00",
                "dec6_235_sip_enabled": True,
                "spread_bps": 15.0,
                "order_type": "LMT",
                "stop_pct": 1.50,
                "active_guardian": True,
                "broker_port": 4002,
                "symbol_count": 10,
            },
            True,
            "OVERNIGHT_23X5_SIP",
        ),
        (
            "05_premarket_040000_sip",
            {
                "et_iso_ts": "2026-12-07T04:00:00-05:00",
                "dec6_235_sip_enabled": True,
                "spread_bps": 10.0,
                "order_type": "LMT",
                "stop_pct": 1.80,
                "active_guardian": True,
                "broker_port": 4002,
                "symbol_count": 20,
            },
            True,
            "PRE_MARKET",
        ),
        (
            "06_rth_093000_sip",
            {
                "et_iso_ts": "2026-12-07T09:30:00-05:00",
                "dec6_235_sip_enabled": True,
                "spread_bps": 4.0,
                "order_type": "LMT",
                "stop_pct": 1.50,
                "active_guardian": True,
                "broker_port": 8787,
                "symbol_count": 40,
            },
            True,
            "RTH_CORE",
        ),
        (
            "07_overnight_mkt_order_blocked",
            {
                "et_iso_ts": "2026-12-06T21:15:00-05:00",
                "dec6_235_sip_enabled": True,
                "spread_bps": 12.0,
                "order_type": "MKT",
                "stop_pct": 1.80,
                "active_guardian": True,
                "broker_port": 4002,
                "symbol_count": 4,
            },
            False,
            "OVERNIGHT_23X5_SIP",
        ),
        (
            "08_adr0022_stop_over_2pct_blocked",
            {
                "et_iso_ts": "2026-12-06T21:15:00-05:00",
                "dec6_235_sip_enabled": True,
                "spread_bps": 12.0,
                "order_type": "LMT",
                "stop_pct": 2.50,
                "active_guardian": True,
                "broker_port": 4002,
                "symbol_count": 4,
            },
            False,
            "OVERNIGHT_23X5_SIP",
        ),
        (
            "09_pre_cutover_boats_9_symbols_blocked",
            {
                "et_iso_ts": "2026-12-04T21:15:00-05:00",
                "dec6_235_sip_enabled": False,
                "spread_bps": 12.0,
                "order_type": "LMT",
                "stop_pct": 1.80,
                "active_guardian": True,
                "broker_port": 4002,
                "symbol_count": 9,
            },
            False,
            "OVERNIGHT_BOATS",
        ),
        (
            "10_missing_guardian_and_live_port_blocked",
            {
                "et_iso_ts": "2026-12-06T22:00:00-05:00",
                "dec6_235_sip_enabled": True,
                "spread_bps": 12.0,
                "order_type": "LMT",
                "stop_pct": 1.80,
                "active_guardian": False,
                "broker_port": 7496,
                "symbol_count": 2,
            },
            False,
            "OVERNIGHT_23X5_SIP",
        ),
    ]

    results: list[dict[str, Any]] = []
    passed = 0
    for name, kwargs, exp_approved, exp_segment in scenarios:
        res = evaluate_session_boundary_policy(**kwargs)
        ok = (res["approved"] == exp_approved) and (res["session_segment"] == exp_segment)
        if ok:
            passed += 1
        results.append(
            {
                "scenario": name,
                "matched_expectation": ok,
                "expected_approved": exp_approved,
                "expected_segment": exp_segment,
                **res,
            }
        )

    out: dict[str, Any] = {
        "schema_version": "sota-boats-23x5-cutover-drill.v1",
        "cutover_date": DEC6_CUTOVER_DATE.isoformat(),
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
