"""Finalized 12-Feed Symbol Ranking System DataFeeds (`DF1..DF12`) & 6 Auto-Trading Strategy Routes (`v3.10.2`).

Establishes the single authoritative foundation feeding every autonomous paper-trading strategy
across the `native-agent-stack` ecosystem while preserving full backward compatibility with
`sota-research-feeds.v2` (`7` feeds) and `sota-ranking-datafeeds.v3.8` (`DF1..DF9`).

Enforces (`ADR-0024` + `ADR-0026` IEEE-754 & Bitemporal Hardening):
- Strict IEEE-754 `math.isfinite()` validation and negated inequality gates (`not (x >= floor)` / `not (x <= cap)`) so `NaN` / `+-Inf` join failures ALWAYS fail closed.
- Bitemporal point-in-time ordering (`ts_event_ns <= ts_recv_ns <= decision_ns`), real UNIX epoch nanosecond validation (`>= 2000-01-01`), `decision_ns` UTC date `<= 2026-10-15`, and exact consistency with `study_date`.
- Bijective `feed_id == feeds_key` across all `12` feeds plus `feeds_by_short_id` (`DF1..DF12`) resolving every `required_feeds` entry across all `6` strategy routes.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sota_mmw.compounding_versioning import (
    CANONICAL_RANKING_DATAFEEDS_V38,
    RANKING_DATAFEEDS_SCHEMA_VERSION,
)
from sota_mmw.promotion_gate import MAX_STOP_ADR0022_PCT, STUDY_WALL_DATE

SYMBOL_RANKING_DATAFEEDS_V310_SCHEMA = "sota-symbol-ranking-datafeeds.v3.10"
SYMBOL_RANKING_HANDOFF_SCHEMA = "sota-symbol-ranking-handoff.v3.10"

MIN_RVOL_TOD_THRESHOLD = 2.20
MIN_VOL_Z_TOD_THRESHOLD = 2.30
MIN_OFI_THRESHOLD = 0.25
MIN_DRY_POWDER_SEC = 15.0
MAX_SPREAD_COLLAR_BPS = 10.0
MIN_HARD_STOP_PCT = 0.05  # 5.0 bps realistic tick/spread floor (ADR-0031)
WAVE2_DEAD_FLOW_COOLDOWN_SEC = 900.0
POSTWALL_EB_KAPPA = 40
MIN_EPOCH_2000_NS = 946_684_800_000_000_000  # 2000-01-01T00:00:00Z in nanoseconds
ALPACA_PAPER_PORTS: tuple[int, ...] = (8787, 8799, 8797)
IBKR_PAPER_PORTS: tuple[int, ...] = (4002,)
ALL_SANCTIONED_PAPER_PORTS: tuple[int, ...] = (*ALPACA_PAPER_PORTS, *IBKR_PAPER_PORTS)

DF10_TO_DF12_EXTENSION: dict[str, dict[str, Any]] = {
    "DF10_own_history_tod_abnormal_rate_and_ucurve": {
        "feed_id": "DF10_own_history_tod_abnormal_rate_and_ucurve",
        "short_id": "DF10",
        "v2_compat_feeds": ("tod_rvol_normalizer",),
        "window_et": "09:30-16:00 ET (20d trailing same-minute buckets)",
        "upstream": (
            "QuantConnect/Lean@e28820c9c846 + "
            "pola-rs/polars@7f902bd3ffd27ff82d14278a09a295ff2f7aed92 + "
            "duckdb/duckdb@d54cbbe3df17e8e5ce68312f483b4155836112aa"
        ),
        "pit_and_microstructure_rules": (
            "polars asof join <= 2026-10-15 own_tod_mean_rate & own_tod_std_rate; zero raw dollar-volume bias",
            f"RVOL_tod >= {MIN_RVOL_TOD_THRESHOLD:.2f} and vol_z_tod >= {MIN_VOL_Z_TOD_THRESHOLD:.2f}",
            "NYSE U-curve X1_open_ignition and X2_close_drift bucket normalization",
        ),
        "endpoint": "GET http://127.0.0.1:8787/api/research_feeds?include=tod_abnormal_rate",
        "thresholds": {
            "min_rvol_tod": MIN_RVOL_TOD_THRESHOLD,
            "min_vol_z_tod": MIN_VOL_Z_TOD_THRESHOLD,
            "nyse_ucurve_buckets": ("X1_open_ignition", "X2_close_drift"),
        },
    },
    "DF11_bitemporal_databento_pit_and_h096_collar": {
        "feed_id": "DF11_bitemporal_databento_pit_and_h096_collar",
        "short_id": "DF11",
        "v2_compat_feeds": ("alpaca_sip",),
        "window_et": "04:00-20:00 ET bitemporal L1/L2",
        "upstream": (
            "databento/databento-python + "
            "nkaz001/hftbacktest@5f3ec40b2afb764e0fea112f941ed85523ef4e88 + "
            "nautechsystems/nautilus_trader@da6b57aefdd62b44f675e434ffcfefca7f4025dd"
        ),
        "pit_and_microstructure_rules": (
            "strict bitemporal inequality ts_event_ns <= ts_recv_ns <= decision_ns with RiskAdverseQueueModel",
            f"H096 >= {MIN_DRY_POWDER_SEC:.1f}s dry-powder bid survival and <= {MAX_SPREAD_COLLAR_BPS:.1f} bps collar",
            f"OFI >= {MIN_OFI_THRESHOLD:.2f}, ISO fraction >= 0.15 or BJZZ institutional fraction >= 0.12",
        ),
        "endpoint": "GET http://127.0.0.1:8787/api/tv/seamless_practice",
        "thresholds": {
            "min_ofi": MIN_OFI_THRESHOLD,
            "min_iso_fraction": 0.15,
            "min_bjzz_fraction": 0.12,
            "min_dry_powder_sec": MIN_DRY_POWDER_SEC,
            "max_spread_collar_bps": MAX_SPREAD_COLLAR_BPS,
        },
    },
    "DF12_qlib_rank_ic_and_kappa40_postwall_eb_feedback": {
        "feed_id": "DF12_qlib_rank_ic_and_kappa40_postwall_eb_feedback",
        "short_id": "DF12",
        "v2_compat_feeds": ("ibkr_paper_4002_l1",),
        "window_et": "Post-session & continuous paper blotter",
        "upstream": (
            "microsoft/qlib + "
            "ml4t/diagnostic@19e76072e64a18c9ba56130e4a7bcc0bc871f57e + "
            "skfolio/skfolio@90e3fb907fab39d244d899f3caf4e9676889309c"
        ),
        "pit_and_microstructure_rules": (
            "REAL_BROKER_ONLY post-wall posterior updates; never back-propagated into <=2026-10-15 feature study",
            f"Empirical-Bayes shrinkage prior kappa={POSTWALL_EB_KAPPA}",
            f"DEAD_FLOW_RECYCLED Wave-2 cooldown >= {WAVE2_DEAD_FLOW_COOLDOWN_SEC:.1f}s",
        ),
        "endpoint": "GET http://127.0.0.1:8799/api/paper_feedback_manifest",
        "thresholds": {
            "eb_shrinkage_kappa": POSTWALL_EB_KAPPA,
            "wave2_dead_flow_cooldown_sec": WAVE2_DEAD_FLOW_COOLDOWN_SEC,
        },
    },
}


def _build_12feed_catalog() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key, val in CANONICAL_RANKING_DATAFEEDS_V38.items():
        short_prefix = key.split("_", 1)[0]
        out[key] = {"short_id": short_prefix, **val}
    out.update(DF10_TO_DF12_EXTENSION)
    return out


FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS: dict[str, dict[str, Any]] = _build_12feed_catalog()
FEEDS_BY_SHORT_ID: dict[str, dict[str, Any]] = {
    str(v["short_id"]): v for v in FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS.values()
}

SYMBOL_RANKING_SYSTEM_APIS_V310: dict[str, dict[str, Any]] = {
    "ranker_symbol_ranking_feeds_v310": {
        "endpoint": "GET http://127.0.0.1:8787/api/research_feeds?schema=v3.10",
        "cli": "sota-version ranking-feeds --v310 --json",
        "schema_version": SYMBOL_RANKING_DATAFEEDS_V310_SCHEMA,
        "feeds_count": 12,
        "role": "12-Feed DF1..DF12 Bitemporal PIT Symbol Ranking DataFeeds foundation",
    },
    "ranker_tv_seamless_practice": {
        "endpoint": "GET http://127.0.0.1:8787/api/tv/seamless_practice",
        "mcp_tool": "sota_get_tv_practice_and_reentry_status",
        "schema_version": SYMBOL_RANKING_HANDOFF_SCHEMA,
        "role": "Stage-1 RVOL_tod + H096 15s collar + 900s Wave-2 re-entry practice snapshot",
    },
    "guardian_paper_eb_feedback": {
        "endpoint": "GET http://127.0.0.1:8799/api/paper_feedback_manifest",
        "schema_version": SYMBOL_RANKING_DATAFEEDS_V310_SCHEMA,
        "role": "Real broker paper telemetry (PA-prefix / DU-prefix :4002) feeding kappa=40 EB shrinkage",
    },
}

SYMBOL_RANKING_TO_AUTO_STRATEGY_ROUTES: dict[str, dict[str, Any]] = {
    "PRE_TRAVEL_EARLY_IGNITION": {
        "archetype": "PRE_TRAVEL_EARLY_IGNITION",
        "required_feeds": ("DF1", "DF2", "DF4", "DF6", "DF10", "DF11"),
        "paper_broker_lane": "ALPACA_PAPER_PA_200RPM_PORT_8787",
        "max_initial_stop_pct": 1.80,
        "trail_mode": "6-14bps_mega_cap_or_core50_zero_loss_runner",
        "requires_wave2_cooldown": False,
    },
    "FIRST_HAND_SEC_EPISODIC_PIVOT": {
        "archetype": "FIRST_HAND_SEC_EPISODIC_PIVOT",
        "required_feeds": ("DF1", "DF3", "DF5", "DF10", "DF11"),
        "paper_broker_lane": "ALPACA_PAPER_PA_200RPM_PORT_8787",
        "max_initial_stop_pct": 2.00,
        "trail_mode": "50_50_core_harvest_and_trailing_runner",
        "requires_wave2_cooldown": False,
    },
    "BOATS_23X5_OVERNIGHT_CONTINUATION": {
        "archetype": "MEGA_CAP_NEAR_LOSSLESS_ORB",
        "required_feeds": ("DF1", "DF2", "DF3", "DF8", "DF10", "DF11"),
        "paper_broker_lane": "IBKR_PAPER_DU_3000MPM_PORT_4002",
        "max_initial_stop_pct": 1.50,
        "trail_mode": "6-14bps_boats_23x5_limit_only_day_tif",
        "requires_wave2_cooldown": False,
    },
    "PARABOLIC_EXHAUSTION_CONTROLLED_SHORT": {
        "archetype": "CLIMAX_VWAP_MEAN_REVERSION",
        "required_feeds": ("DF1", "DF4", "DF6", "DF7", "DF10", "DF11"),
        "paper_broker_lane": "IBKR_PAPER_DU_3000MPM_PORT_4002",
        "max_initial_stop_pct": 1.75,
        "trail_mode": "vwap_fail_orl_ssr_gated_bracket",
        "requires_wave2_cooldown": False,
    },
    "HYBRID_50_50_CORE_AND_WAVE2_REENTRY": {
        "archetype": "PRE_TRAVEL_EARLY_IGNITION",
        "required_feeds": ("DF1", "DF6", "DF9", "DF10", "DF11", "DF12"),
        "paper_broker_lane": "ALPACA_PAPER_PA_200RPM_PORT_8787",
        "max_initial_stop_pct": 1.80,
        "trail_mode": "zero_loss_floor_wave2_reentry_900s_cooldown",
        "requires_wave2_cooldown": True,
    },
    "IPO_DAY1_CROSS_STABILIZATION_WAVE2": {
        "archetype": "FIRST_HAND_SEC_EPISODIC_PIVOT",
        "required_feeds": ("DF1", "DF3", "DF5", "DF6", "DF10", "DF11"),
        "paper_broker_lane": "ALPACA_PAPER_PA_200RPM_PORT_8787",
        "max_initial_stop_pct": 1.90,
        "trail_mode": "ipo_cross_vwap_wave2_stabilization",
        "requires_wave2_cooldown": True,
    },
}


def resolve_route_required_feeds(strategy_route: str) -> list[dict[str, Any]]:
    """Resolve short feed IDs (`DF1..DF12`) for `strategy_route` into canonical feed definitions (fail-closed)."""
    route = SYMBOL_RANKING_TO_AUTO_STRATEGY_ROUTES.get(strategy_route)
    if route is None:
        raise KeyError(f"Unknown strategy_route: {strategy_route!r}")
    resolved: list[dict[str, Any]] = []
    for short_id in route["required_feeds"]:
        if short_id not in FEEDS_BY_SHORT_ID:
            raise KeyError(f"Route {strategy_route!r} references unresolved feed {short_id!r}")
        resolved.append(FEEDS_BY_SHORT_ID[short_id])
    return resolved


def _to_ny_datetime(dt_utc: dt.datetime) -> dt.datetime:
    """Convert aware UTC datetime to America/New_York (cross-OS fallback when Windows lacks tzdata)."""
    try:
        return dt_utc.astimezone(ZoneInfo("America/New_York"))
    except (ZoneInfoNotFoundError, KeyError, ValueError):
        y = dt_utc.year
        if y < 2007:
            # Uniform Time Act (1987-2006): 1st Sunday of April 07:00 UTC -> last Sunday of October 06:00 UTC
            apr1_wd = dt.date(y, 4, 1).weekday()
            dst_start = dt.datetime(y, 4, 1 + ((6 - apr1_wd) % 7), 7, 0, tzinfo=dt.UTC)
            oct31_wd = dt.date(y, 10, 31).weekday()
            dst_end = dt.datetime(y, 10, 31 - ((oct31_wd + 1) % 7), 6, 0, tzinfo=dt.UTC)
        else:
            # Energy Policy Act of 2005 (2007+): 2nd Sunday of March 07:00 UTC -> 1st Sunday of November 06:00 UTC
            mar1_wd = dt.date(y, 3, 1).weekday()
            dst_start = dt.datetime(y, 3, 1 + ((6 - mar1_wd) % 7) + 7, 7, 0, tzinfo=dt.UTC)
            nov1_wd = dt.date(y, 11, 1).weekday()
            dst_end = dt.datetime(y, 11, 1 + ((6 - nov1_wd) % 7), 6, 0, tzinfo=dt.UTC)
        is_edt = dst_start <= dt_utc < dst_end
        return dt_utc.astimezone(dt.timezone(dt.timedelta(hours=-4 if is_edt else -5), name="EDT" if is_edt else "EST"))


_FEED_ID_LOWER_MAP: dict[str, str] = {k.lower(): k for k in FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS}
_KNOWN_CROSS_REPO_FEED_ALIASES: dict[str, str] = {
    "df10_own_history_tod_normal_rate_and_nyse_ucurve_x1_x2": "DF10_own_history_tod_abnormal_rate_and_ucurve",
    "df11_databento_bitemporal_pit_and_h096_15s_collar": "DF11_bitemporal_databento_pit_and_h096_collar",
    "df12_qlib_rank_ic_and_kappa40_postwall_eb_feedback": "DF12_qlib_rank_ic_and_kappa40_postwall_eb_feedback",
}


def normalize_ranking_feed_id(feed_id: str) -> str:
    """Normalize canonical DF1..DF12 feed IDs & explicit cross-repo aliases (fail-closed on arbitrary suffixes)."""
    if not isinstance(feed_id, str) or not feed_id.strip():
        raise ValueError(f"feed_id must be a non-empty string, got {feed_id!r}")
    key = feed_id.strip()
    if key in FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS:
        return key
    low = key.lower()
    if low in _FEED_ID_LOWER_MAP:
        return _FEED_ID_LOWER_MAP[low]
    if low in _KNOWN_CROSS_REPO_FEED_ALIASES:
        return _KNOWN_CROSS_REPO_FEED_ALIASES[low]
    upper = key.upper()
    if upper in FEEDS_BY_SHORT_ID:
        return str(FEEDS_BY_SHORT_ID[upper]["feed_id"])
    raise KeyError(f"Unrecognized ranking feed_id: {feed_id!r}")


def _is_finite_real(val: Any) -> bool:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return False
    try:
        return math.isfinite(float(val))
    except OverflowError:
        return False


def _allowed_ports_for_route(route: dict[str, Any]) -> tuple[int, ...]:
    lane = str(route.get("paper_broker_lane") or "").upper()
    if lane.startswith("IBKR_PAPER"):
        return IBKR_PAPER_PORTS
    if lane.startswith("ALPACA_PAPER"):
        return ALPACA_PAPER_PORTS
    return ()


def compute_symbol_ranking_v310_sha256() -> str:
    """Return deterministic SHA-256 over the finalized 12-Feed DF1..DF12 Symbol Ranking catalog."""
    payload = json.dumps(FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS, sort_keys=True, default=list)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evaluate_symbol_ranking_to_strategy_handoff(
    *,
    symbol: str,
    strategy_route: str,
    study_date: str,
    ts_event_ns: int,
    ts_recv_ns: int,
    decision_ns: int,
    rvol_tod: float,
    vol_z_tod: float,
    ofi: float,
    dry_powder_sec: float,
    spread_collar_bps: float,
    hard_stop_pct: float,
    is_wave2_reentry: bool = False,
    cooldown_elapsed_sec: float = 0.0,
    pullback_held_zero_loss_floor: bool = True,
    broker_port: int = 8787,
) -> dict[str, Any]:
    """Fail-closed validation of a DF1..DF12 Symbol Ranking candidate handing off into autonomous paper strategy."""
    violations: list[str] = []
    route = SYMBOL_RANKING_TO_AUTO_STRATEGY_ROUTES.get(strategy_route)
    if route is None:
        violations.append(f"UNKNOWN_STRATEGY_ROUTE: {strategy_route!r}")

    try:
        parsed_study_date = dt.date.fromisoformat(study_date)
    except ValueError:
        parsed_study_date = None
        violations.append(f"INVALID_STUDY_DATE: {study_date!r}")

    if parsed_study_date is not None and parsed_study_date > STUDY_WALL_DATE:
        violations.append(f"PREWALL_VIOLATION: study_date {study_date} > {STUDY_WALL_DATE.isoformat()}")

    # Strict integer & bitemporal UNIX epoch nanosecond checks (Defect B)
    for ts_name, ts_val in (("ts_event_ns", ts_event_ns), ("ts_recv_ns", ts_recv_ns), ("decision_ns", decision_ns)):
        if not isinstance(ts_val, int) or isinstance(ts_val, bool) or ts_val < MIN_EPOCH_2000_NS:
            violations.append(f"INVALID_EPOCH_NS: {ts_name}={ts_val!r} must be UNIX epoch ns >= 2000-01-01")
    if (
        isinstance(ts_event_ns, int)
        and isinstance(ts_recv_ns, int)
        and isinstance(decision_ns, int)
        and not isinstance(ts_event_ns, bool)
        and not isinstance(ts_recv_ns, bool)
        and not isinstance(decision_ns, bool)
    ):
        if not (ts_event_ns <= ts_recv_ns <= decision_ns):
            violations.append("BITEMPORAL_PIT_VIOLATION: require ts_event_ns <= ts_recv_ns <= decision_ns")
        if decision_ns >= MIN_EPOCH_2000_NS:
            try:
                # Exact integer nanosecond division + America/New_York session date (ADR-0031: BOATS 20:00-23:59 ET)
                decision_sec = decision_ns // 1_000_000_000
                decision_dt_ny = _to_ny_datetime(dt.datetime.fromtimestamp(decision_sec, tz=dt.UTC))
                decision_date = decision_dt_ny.date()
                if decision_date > STUDY_WALL_DATE:
                    violations.append(
                        f"PREWALL_DECISION_NS_VIOLATION: decision_ns ET date {decision_date.isoformat()} > {STUDY_WALL_DATE.isoformat()}"
                    )
                if parsed_study_date is not None and decision_date != parsed_study_date:
                    violations.append(
                        f"DECISION_NS_STUDY_DATE_MISMATCH: decision_ns ET date {decision_date.isoformat()} != study_date {study_date}"
                    )
            except (OverflowError, OSError, ValueError):
                violations.append(f"INVALID_EPOCH_NS_RANGE: decision_ns={decision_ns!r}")

    # Strict IEEE-754 finite checks + negated comparisons so NaN/+Inf/-Inf ALWAYS fail closed (Defect A)
    for num_name, num_val in (
        ("rvol_tod", rvol_tod),
        ("vol_z_tod", vol_z_tod),
        ("ofi", ofi),
        ("dry_powder_sec", dry_powder_sec),
        ("spread_collar_bps", spread_collar_bps),
        ("hard_stop_pct", hard_stop_pct),
        ("cooldown_elapsed_sec", cooldown_elapsed_sec),
    ):
        if not _is_finite_real(num_val):
            violations.append(f"NON_FINITE_NUMERIC_INPUT: {num_name}={num_val!r}")

    if _is_finite_real(rvol_tod) and not (float(rvol_tod) >= MIN_RVOL_TOD_THRESHOLD):
        violations.append(f"RVOL_TOD_BELOW_MIN: {rvol_tod:.2f} < {MIN_RVOL_TOD_THRESHOLD:.2f}")
    if _is_finite_real(vol_z_tod) and not (float(vol_z_tod) >= MIN_VOL_Z_TOD_THRESHOLD):
        violations.append(f"VOL_Z_TOD_BELOW_MIN: {vol_z_tod:.2f} < {MIN_VOL_Z_TOD_THRESHOLD:.2f}")
    if _is_finite_real(ofi) and not (float(ofi) >= MIN_OFI_THRESHOLD):
        violations.append(f"OFI_BELOW_MIN: {ofi:.3f} < {MIN_OFI_THRESHOLD:.2f}")
    if _is_finite_real(dry_powder_sec) and not (float(dry_powder_sec) >= MIN_DRY_POWDER_SEC):
        violations.append(f"DRY_POWDER_BELOW_15S: {dry_powder_sec:.2f}s < {MIN_DRY_POWDER_SEC:.1f}s")
    if _is_finite_real(spread_collar_bps) and not (0.0 <= float(spread_collar_bps) <= MAX_SPREAD_COLLAR_BPS):
        violations.append(
            f"SPREAD_COLLAR_EXCEEDED: {spread_collar_bps:.2f} outside [0.0, {MAX_SPREAD_COLLAR_BPS:.1f}] bps"
        )
    if _is_finite_real(hard_stop_pct) and not (MIN_HARD_STOP_PCT <= float(hard_stop_pct) <= MAX_STOP_ADR0022_PCT):
        violations.append(
            f"ADR0022_STOP_OUT_OF_BOUNDS: {float(hard_stop_pct):.4f}% outside [{MIN_HARD_STOP_PCT:.2f}%, {MAX_STOP_ADR0022_PCT:.2f}%]"
        )
    if (
        route is not None
        and _is_finite_real(hard_stop_pct)
        and not (float(hard_stop_pct) <= float(route["max_initial_stop_pct"]))
    ):
        violations.append(f"ROUTE_STOP_EXCEEDED: {hard_stop_pct:.2f}% > {float(route['max_initial_stop_pct']):.2f}%")

    if (
        not isinstance(broker_port, int)
        or isinstance(broker_port, bool)
        or broker_port not in ALL_SANCTIONED_PAPER_PORTS
    ):
        violations.append(
            f"LIVE_BROKER_FIREWALL_BLOCK: unsupported port {broker_port}; only 8787/8799/8797/4002 paper allowed"
        )
    elif route is not None:
        allowed_ports = _allowed_ports_for_route(route)
        if broker_port not in allowed_ports:
            violations.append(
                f"ROUTE_BROKER_PORT_MISMATCH: port {broker_port} invalid for {route['paper_broker_lane']} (allowed={allowed_ports})"
            )
    if is_wave2_reentry or (route is not None and route["requires_wave2_cooldown"]):
        if not _is_finite_real(cooldown_elapsed_sec) or not (
            float(cooldown_elapsed_sec) >= WAVE2_DEAD_FLOW_COOLDOWN_SEC
        ):
            violations.append(f"WAVE2_COOLDOWN_ACTIVE: {cooldown_elapsed_sec}s < {WAVE2_DEAD_FLOW_COOLDOWN_SEC:.1f}s")
        if pullback_held_zero_loss_floor is not True:
            violations.append("WAVE2_ZERO_LOSS_FLOOR_LOST: pullback_held_zero_loss_floor must be True")

    return {
        "schema_version": SYMBOL_RANKING_HANDOFF_SCHEMA,
        "symbol": symbol.upper(),
        "strategy_route": strategy_route,
        "approved": len(violations) == 0,
        "violations": violations,
        "required_feeds": list(route["required_feeds"]) if route else [],
        "paper_broker_lane": route["paper_broker_lane"] if route else "BLOCKED",
        "single_active_broker_host_only": True,
        "ranking_v310_sha256": compute_symbol_ranking_v310_sha256(),
    }


def build_symbol_ranking_foundation_manifest() -> dict[str, Any]:
    """Build complete v3.10.2 12-Feed Symbol Ranking DataFeeds & 6-Strategy Foundation manifest."""
    return {
        "schema_version": SYMBOL_RANKING_DATAFEEDS_V310_SCHEMA,
        "backward_compat_v38_schema": RANKING_DATAFEEDS_SCHEMA_VERSION,
        "feed_count": len(FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS),
        "feed_ids": list(FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS.keys()),
        "short_feed_ids": list(FEEDS_BY_SHORT_ID.keys()),
        "feeds_by_short_id": FEEDS_BY_SHORT_ID,
        "strategy_route_count": len(SYMBOL_RANKING_TO_AUTO_STRATEGY_ROUTES),
        "strategy_routes": SYMBOL_RANKING_TO_AUTO_STRATEGY_ROUTES,
        "datafeed_apis": SYMBOL_RANKING_SYSTEM_APIS_V310,
        "ranking_v310_contract_sha256": compute_symbol_ranking_v310_sha256(),
        "single_active_broker_host_only": True,
        "max_hard_stop_pct": MAX_STOP_ADR0022_PCT,
        "pre_wall_cutoff": STUDY_WALL_DATE.isoformat(),
        "feeds": FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS,
    }
