"""Finalized 12-Feed Symbol Ranking System DataFeeds (`DF1..DF12`) & 6 Auto-Trading Strategy Routes (`v3.10.0`).

Establishes the single authoritative foundation feeding every autonomous paper-trading strategy
across the `native-agent-stack` ecosystem while preserving full backward compatibility with
`sota-research-feeds.v2` (`7` feeds) and `sota-ranking-datafeeds.v3.8` (`DF1..DF9`).

Enforces:
- Bitemporal point-in-time ordering (`ts_event_ns <= ts_recv_ns <= decision_ns`) and `<= 2026-10-15` pre-wall study lock.
- Per-symbol own-history time-of-day abnormal-rate normalization (`RVOL_tod >= 2.20`, `vol_z_tod >= 2.30`, NYSE U-curve `X1`/`X2`) eliminating mega-cap dollar-volume bias.
- `H096` `15.0s` dry-powder bid-survival + `<= 10.0` bps collar (`OFI >= 0.25`, `ISO_F >= 0.15 | BJZZ >= 0.12`).
- `microsoft/qlib` cross-sectional `RankIC` / `ICIR` telemetry + `kappa=40` post-wall Empirical-Bayes shrinkage (`REAL_BROKER_ONLY`, `900.0s` `DEAD_FLOW_RECYCLED` Wave-2 cooldown).
- `ADR-0022` `<= 2.00%` hard initial stop, `6-14` bps mega-cap near-lossless trail, `<= 200` req/min Alpaca Paper (`PA-prefix`, `:8787`) & `<= 3000` msg/min IBKR Paper (`DU-prefix`, `:4002`), and `singleActiveBrokerHostOnly = True`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any

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
WAVE2_DEAD_FLOW_COOLDOWN_SEC = 900.0
POSTWALL_EB_KAPPA = 40

DF10_TO_DF12_EXTENSION: dict[str, dict[str, Any]] = {
    "DF10_OWN_HISTORY_TOD_ABNORMAL_RATE_AND_UCURVE": {
        "feed_id": "DF10",
        "name": "20d SIP Own-History Time-of-Day Normal Rate & NYSE U-Curve X1/X2",
        "endpoint": "GET http://127.0.0.1:8787/api/research_feeds?include=tod_abnormal_rate",
        "primary_upstreams": (
            "https://github.com/QuantConnect/Lean",
            "https://github.com/pola-rs/polars",
            "https://github.com/duckdb/duckdb",
        ),
        "pit_rule": "polars asof join <= 2026-10-15 own_tod_mean_rate & own_tod_std_rate; zero raw dollar-volume bias",
        "thresholds": {
            "min_rvol_tod": MIN_RVOL_TOD_THRESHOLD,
            "min_vol_z_tod": MIN_VOL_Z_TOD_THRESHOLD,
            "nyse_ucurve_buckets": ("X1_open_ignition", "X2_close_drift"),
        },
        "target_strategies": ("all_6_autonomous_routes",),
    },
    "DF11_BITEMPORAL_DATABENTO_PIT_AND_H096_COLLAR": {
        "feed_id": "DF11",
        "name": "Databento Bitemporal L1/L2 Event-vs-Receipt PIT & H096 15s Dry-Powder Collar",
        "endpoint": "GET http://127.0.0.1:8787/api/tv/seamless_practice",
        "primary_upstreams": (
            "https://github.com/databento/databento-python",
            "https://github.com/nkaz001/hftbacktest",
            "https://github.com/nautechsystems/nautilus_trader",
        ),
        "pit_rule": "strict bitemporal inequality ts_event_ns <= ts_recv_ns <= decision_ns with RiskAdverseQueueModel",
        "thresholds": {
            "min_ofi": MIN_OFI_THRESHOLD,
            "min_iso_fraction": 0.15,
            "min_bjzz_fraction": 0.12,
            "min_dry_powder_sec": MIN_DRY_POWDER_SEC,
            "max_spread_collar_bps": MAX_SPREAD_COLLAR_BPS,
        },
        "target_strategies": ("all_6_autonomous_routes",),
    },
    "DF12_QLIB_RANK_IC_AND_KAPPA40_POSTWALL_EB_FEEDBACK": {
        "feed_id": "DF12",
        "name": "Microsoft Qlib RankIC/ICIR & kappa=40 Post-Wall Empirical-Bayes Paper Feedback",
        "endpoint": "GET http://127.0.0.1:8799/api/paper_feedback_manifest",
        "primary_upstreams": (
            "https://github.com/microsoft/qlib",
            "https://github.com/ml4t/ml4t-diagnostic",
            "https://github.com/skfolio/skfolio",
        ),
        "pit_rule": "REAL_BROKER_ONLY post-wall posterior updates; never back-propagated into <=2026-10-15 feature study",
        "thresholds": {
            "eb_shrinkage_kappa": POSTWALL_EB_KAPPA,
            "wave2_dead_flow_cooldown_sec": WAVE2_DEAD_FLOW_COOLDOWN_SEC,
        },
        "target_strategies": (
            "HYBRID_50_50_CORE_AND_WAVE2_REENTRY",
            "PRE_TRAVEL_EARLY_IGNITION",
            "FIRST_HAND_SEC_EPISODIC_PIVOT",
        ),
    },
}

FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS: dict[str, dict[str, Any]] = {
    **CANONICAL_RANKING_DATAFEEDS_V38,
    **DF10_TO_DF12_EXTENSION,
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
    if dt.date.fromisoformat(study_date) > STUDY_WALL_DATE:
        violations.append(f"PREWALL_VIOLATION: study_date {study_date} > {STUDY_WALL_DATE.isoformat()}")
    if not (ts_event_ns <= ts_recv_ns <= decision_ns):
        violations.append("BITEMPORAL_PIT_VIOLATION: require ts_event_ns <= ts_recv_ns <= decision_ns")
    if rvol_tod < MIN_RVOL_TOD_THRESHOLD:
        violations.append(f"RVOL_TOD_BELOW_MIN: {rvol_tod:.2f} < {MIN_RVOL_TOD_THRESHOLD:.2f}")
    if vol_z_tod < MIN_VOL_Z_TOD_THRESHOLD:
        violations.append(f"VOL_Z_TOD_BELOW_MIN: {vol_z_tod:.2f} < {MIN_VOL_Z_TOD_THRESHOLD:.2f}")
    if ofi < MIN_OFI_THRESHOLD:
        violations.append(f"OFI_BELOW_MIN: {ofi:.3f} < {MIN_OFI_THRESHOLD:.2f}")
    if dry_powder_sec < MIN_DRY_POWDER_SEC:
        violations.append(f"DRY_POWDER_BELOW_15S: {dry_powder_sec:.2f}s < {MIN_DRY_POWDER_SEC:.1f}s")
    if spread_collar_bps > MAX_SPREAD_COLLAR_BPS:
        violations.append(f"SPREAD_COLLAR_EXCEEDED: {spread_collar_bps:.2f} > {MAX_SPREAD_COLLAR_BPS:.1f} bps")
    if not (0.0 < hard_stop_pct <= MAX_STOP_ADR0022_PCT):
        violations.append(f"ADR0022_STOP_EXCEEDED: {hard_stop_pct:.2f}% outside (0, {MAX_STOP_ADR0022_PCT:.2f}%]")
    if route is not None and hard_stop_pct > float(route["max_initial_stop_pct"]):
        violations.append(f"ROUTE_STOP_EXCEEDED: {hard_stop_pct:.2f}% > {float(route['max_initial_stop_pct']):.2f}%")
    if broker_port not in (8787, 8799, 4002):
        violations.append(
            f"LIVE_BROKER_FIREWALL_BLOCK: unsupported port {broker_port}; only 8787/8799/4002 paper allowed"
        )
    if is_wave2_reentry or (route is not None and route["requires_wave2_cooldown"]):
        if cooldown_elapsed_sec < WAVE2_DEAD_FLOW_COOLDOWN_SEC:
            violations.append(
                f"WAVE2_COOLDOWN_ACTIVE: {cooldown_elapsed_sec:.1f}s < {WAVE2_DEAD_FLOW_COOLDOWN_SEC:.1f}s"
            )
        if not pullback_held_zero_loss_floor:
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
    """Build complete v3.10.0 12-Feed Symbol Ranking DataFeeds & 6-Strategy Foundation manifest."""
    return {
        "schema_version": SYMBOL_RANKING_DATAFEEDS_V310_SCHEMA,
        "backward_compat_v38_schema": RANKING_DATAFEEDS_SCHEMA_VERSION,
        "feed_count": len(FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS),
        "feed_ids": [v["feed_id"] for v in FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS.values()],
        "strategy_route_count": len(SYMBOL_RANKING_TO_AUTO_STRATEGY_ROUTES),
        "strategy_routes": SYMBOL_RANKING_TO_AUTO_STRATEGY_ROUTES,
        "datafeed_apis": SYMBOL_RANKING_SYSTEM_APIS_V310,
        "ranking_v310_contract_sha256": compute_symbol_ranking_v310_sha256(),
        "single_active_broker_host_only": True,
        "max_hard_stop_pct": MAX_STOP_ADR0022_PCT,
        "pre_wall_cutoff": STUDY_WALL_DATE.isoformat(),
        "feeds": FINALIZED_12FEED_SYMBOL_RANKING_DATAFEEDS,
    }
