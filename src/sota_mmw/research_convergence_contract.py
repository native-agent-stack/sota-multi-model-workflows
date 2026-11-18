"""Deterministic Research-Convergence, 7-Feed PIT DataFeed & Strategy Template Contract (`ADR-0011` / Org `ADR-0004`).

Enforces 3-tier convergence across self-bootstrapping `run_workflow` scripts, live/offline `sota-research-feeds.v2`
point-in-time DataFeeds, canonical strategy templates (`sota_converged_strategy.template.json`), and 40-char SHA
pinned upstream clones (`~/Documents/upstream/PINS.md`).
"""

from __future__ import annotations

import datetime as dt
import math
import re
from typing import Any

RESEARCH_FEEDS_SCHEMA_VERSION = "sota-research-feeds.v2"
PRE_WALL_MAX_DATE = "2026-10-15"
PRE_WALL_DATE_OBJ = dt.date(2026, 10, 15)
MAX_HARD_STOP_PCT = 2.00
VALID_EVIDENCE_GRADES: tuple[str, ...] = ("E0", "E1", "E2", "E3", "E4")

HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")

CANONICAL_RESEARCH_MCP_TOOLS: tuple[str, ...] = (
    "sota_get_research_feeds",
    "sota_get_first_hand_incentives",
    "sota_get_converged_strategy_templates",
)

CANONICAL_STRATEGY_ARCHETYPES: tuple[str, ...] = (
    "PRE_TRAVEL_EARLY_IGNITION",
    "FIRST_HAND_SEC_EPISODIC_PIVOT",
    "MEGA_CAP_NEAR_LOSSLESS_ORB",
    "CLIMAX_VWAP_MEAN_REVERSION",
)

CANONICAL_DATAFEEDS: dict[str, dict[str, Any]] = {
    "alpaca_sip": {
        "feed_id": "alpaca_sip",
        "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION,
        "window_et": "04:00-20:00 ET Mon-Fri",
        "upstream": "alpacahq/alpaca-py@v0.45.0",
        "pit_rule": "Nanosecond UTC trade/NBBO alignment; HostPinnedPacedAdapter <=185 req/min",
        "features": (
            "Lee-Ready OFI",
            "BJZZ sub-penny dark-pool x=='D'",
            "Lit ISO 'F' sweeps (never odd-lot 'I')",
            "Session VWAP",
        ),
    },
    "alpaca_boats": {
        "feed_id": "alpaca_boats",
        "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION,
        "window_et": "20:00-04:00 ET Sun-Fri",
        "cutover_date": "2026-12-06",
        "cutover_mode": "23/5 SIP cutover feature-flagged via SOTA_ENABLE_DEC6_235_SIP (default 0)",
        "upstream": "alpacahq/alpaca-py@v0.45.0",
        "pit_rule": "900s stale-print expiry; timestamp guard so BOATS never overwrites newer Premarket SIP",
        "features": (
            "boats_move_pct",
            "boats_dvol",
            "boats_active",
            "dec6_235_sip_cutover_flag",
        ),
    },
    "alpaca_raw_vs_all_adjustment": {
        "feed_id": "alpaca_raw_vs_all_adjustment",
        "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION,
        "window_et": "Intraday execution (RAW) vs multi-day historical series (ALL)",
        "upstream": "alpacahq/alpaca-py@v0.45.0 + pola-rs/polars@py-2.1.0",
        "pit_rule": "Use Adjustment.RAW for unadjusted execution/NBBO fill parity and Adjustment.ALL for multi-day indicators",
        "features": (
            "raw_execution_fill_parity",
            "all_adjusted_multi_day_returns",
            "zero_mixed_adjustment_contamination",
        ),
    },
    "sec_edgar_acceptance_datetime": {
        "feed_id": "sec_edgar_acceptance_datetime",
        "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION,
        "window_et": "06:00-22:00 ET Mon-Fri SEC EDGAR Atom & submissions",
        "half_life_minutes": 15,
        "dilution_block_forms": ("424B2", "424B3", "424B4", "424B5", "S-3", "S-3ASR", "F-3"),
        "upstream": "dgunning/edgartools@v6.2.0",
        "pit_rule": "acceptanceDateTime <= as_of_utc with 15m exponential freshness half-life + instant 424B*/S-3 dilution block",
        "features": (
            "first_hand_8k_item_1_01_2_02_7_01_8_01",
            "sc_13d_activist_radar",
            "15m_freshness_half_life_decay",
            "424b_s3_shelf_dilution_block",
        ),
    },
    "finra_regsho_cnmsshvol_t1": {
        "feed_id": "finra_regsho_cnmsshvol_t1",
        "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION,
        "window_et": "Post-EOD T-1 lag (CNMSshvol) + biweekly short-interest",
        "lag_trading_days": 1,
        "upstream": "FINRA RegSHO CNMSshvol + duckdb@v2.0.0",
        "pit_rule": "Strict T-1 trading-day lag (d_tag < target_tag); zero same-day short-volume lookahead",
        "features": (
            "finra_short_vol_pct_t1",
            "finra_days_to_cover",
            "squeeze_fuel_pit_flag",
        ),
    },
    "corporate_actions_split_guard": {
        "feed_id": "corporate_actions_split_guard",
        "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION,
        "window_et": "XNYS pre-open corporate-actions & holiday/early-close calendar",
        "upstream": "gerrymanoim/exchange_calendars@4.13.2 + unionai-oss/pandera@v0.35.0",
        "pit_rule": "Quarantine unadjusted split/reverse-split discontinuities on ex-date and pause entries across XNYS holidays",
        "features": (
            "ex_date_split_ratio_guard",
            "reverse_split_microcap_filter",
            "xnys_holiday_and_early_close_gate",
        ),
    },
    "ibkr_paper_4002_l1": {
        "feed_id": "ibkr_paper_4002_l1",
        "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION,
        "window_et": "24/5 outsideRth L1 quote & protective stop lane (:4002 Paper only)",
        "paper_port": 4002,
        "forbidden_live_ports": (4001, 7496),
        "upstream": "ib-api-reloaded/ib_async@v2.1.0 + nautechsystems/nautilus_trader@v2.0.0rc9",
        "pit_rule": "Paper-only DU... account on 127.0.0.1:4002 (<=3,000 msg/min); live ports 4001/7496 100% hard-refused",
        "features": (
            "outside_rth_protective_stops",
            "l1_bid_ask_spread_gate",
            "short_locate_availability_probe",
        ),
    },
}


def verify_research_convergence_claim(
    *,
    input_sha256: str,
    upstream_pins: dict[str, str],
    study_max_date: str,
    hard_stop_pct: float,
    evidence_grade: str,
) -> list[str]:
    """Deterministically validate a 3-tier Research-Convergence claim, returning empty list iff valid."""
    violations: list[str] = []

    if not isinstance(input_sha256, str) or not HEX64_RE.fullmatch(input_sha256):
        violations.append("ADR0004_INVALID_INPUT_SHA256:input_sha256 must be a 64-char lowercase hex SHA-256 digest")

    if not isinstance(upstream_pins, dict) or not upstream_pins:
        violations.append("ADR0004_EMPTY_UPSTREAM_PINS:at least one 40-char hex upstream commit SHA is required")
    else:
        for repo_name, commit_sha in sorted(upstream_pins.items()):
            if (
                not isinstance(repo_name, str)
                or not repo_name.strip()
                or not isinstance(commit_sha, str)
                or not HEX40_RE.fullmatch(commit_sha)
            ):
                violations.append(f"ADR0004_INVALID_UPSTREAM_SHA:{repo_name}={commit_sha}")

    if not isinstance(study_max_date, str):
        violations.append(f"INVALID_STUDY_MAX_DATE:{study_max_date}")
    else:
        try:
            parsed_max = dt.date.fromisoformat(study_max_date)
            if parsed_max > PRE_WALL_DATE_OBJ:
                violations.append(f"PREWALL_VIOLATION:{study_max_date}>{PRE_WALL_MAX_DATE}")
        except ValueError:
            violations.append(f"INVALID_STUDY_MAX_DATE:{study_max_date}")

    if (
        isinstance(hard_stop_pct, bool)
        or not isinstance(hard_stop_pct, (int, float))
        or not math.isfinite(float(hard_stop_pct))
        or float(hard_stop_pct) <= 0.0
        or float(hard_stop_pct) > MAX_HARD_STOP_PCT
    ):
        violations.append(f"ADR0022_HARD_STOP_VIOLATION:{hard_stop_pct} (must satisfy 0 < hard_stop_pct <= 2.0)")

    if not isinstance(evidence_grade, str) or evidence_grade not in VALID_EVIDENCE_GRADES:
        violations.append(f"INVALID_EVIDENCE_GRADE:{evidence_grade} (expected one of {VALID_EVIDENCE_GRADES})")

    return violations
