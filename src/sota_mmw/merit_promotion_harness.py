"""Grand Merit-Promotion Harness (`ADR-0027`/`ADR-0028`, `sota-grand-merit-harness.v2`).

Unifies:
- **Primary Always-On 24/5 Sovereign Workstation Host (`Noesis`, `stationary_noesis_win32`, `100.110.115.22`, 64c/128GB/RTX4090 + `Noesis-Carbon` WSL2):**
  Hosts the Main Framework Foundation, `S1/S2` NEVER-GATED Sim lanes, all `4` NEVER-GATED Paper Farm accounts (`:8799`, `:8787`, `:8797`, `:4002`), Proven-Only Stage-5 Lossless Live (`:8798`), 4K TradingView, and scheduled Orca Automations.
- **Portable Command Cockpit & Hot Failover Host (`MacBook Pro M5 Max`, `portable_mac_m5_max`, `100.93.211.101`):**
  Interactive control plane (read-only mirror when Noesis is primary) and explicit single-host failover when workstation is offline or during cutover.
- **Strict `single_active_broker_host_only = True`:** Never dual-active on both machines simultaneously.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from sota_mmw.promotion_gate import MAX_STOP_ADR0022_PCT, STUDY_WALL_DATE

MERIT_HARNESS_SCHEMA_VERSION = "sota-grand-merit-harness.v1"
POST_ANT_ERA_ID = "POST_ANT_WHOLE_MARKET_MERIT"
ACTIVE_MARKET_TARGETS_SCHEMA = "sota.active-market-targets.v1"
STRATEGY_CONTRACT_SCHEMA_V2 = "sota.strategy-contract.v2"

POST_ANT_CONCENTRATED_SOTA_STRATEGIES: frozenset[str] = frozenset(
    {
        "BJZZ_SUBPENNY_INST_DARK_SWEEP",
        "VIX_SPIKE_AND_CRUSH_REGIME_SURFER",
        "ZARATTINI_2024_5M_ORB",
        "ZARATTINI_2025_NOISE_VWAP",
        "H090_TIGHT_SPREAD_HIGH_OFI_PASSIVE_BID",
        "H01_PRE_TRAVEL_POCKET_PIVOT",
        "H08_FIRST_HAND_CATALYST_IGNITION",
    }
)

POST_ANT_QUARANTINED_STRATEGIES: frozenset[str] = frozenset(
    {
        "SOTA_DUAL_CLIMAX_STOP_AND_REVERSE",
        "POST_VIX_REVERSAL",
        "POST_VIX_REVERSAL_MAJOR_GROWTH_THRUST",
        "SOTA_DUAL_EXTREME_BALANCE_BREAK_EARLY",
        "BLIND_WAVE2_REENTRY",
        "RAPID_WAVE2_REENTRY_STRESS",
        "FLOW_VELOCITY_CAPITAL_RECYCLE",
    }
)


def is_post_ant_strategy_quarantined(strategy_id: str) -> bool:
    """Canonical ADR-0064 quarantine predicate matching exact IDs and family variants."""
    sid = str(strategy_id or "").strip().upper()
    if sid in POST_ANT_QUARANTINED_STRATEGIES:
        return True
    return sid.startswith("POST_VIX_REVERSAL") or "FLOW_VELOCITY_CAPITAL_RECYCLE" in sid


POST_ANT_VALID_SESSIONS: frozenset[str] = frozenset({"PRE_MARKET", "RTH_CORE", "POST_CLOSE", "OVERNIGHT_BOATS"})

POST_ANT_STRATEGY_CONTRACTS_V2: dict[str, dict[str, Any]] = {
    "BJZZ_SUBPENNY_INST_DARK_SWEEP": {
        "allowed_sessions": frozenset({"PRE_MARKET", "RTH_CORE", "POST_CLOSE", "OVERNIGHT_BOATS"}),
        "max_spread_bps": 28.0,
        "spread_strict_lt": False,
        "max_stop_pct": 1.60,
        "allowed_symbols": None,
    },
    "VIX_SPIKE_AND_CRUSH_REGIME_SURFER": {
        "allowed_sessions": frozenset({"PRE_MARKET", "RTH_CORE", "POST_CLOSE"}),
        "max_spread_bps": 18.0,
        "spread_strict_lt": False,
        "max_stop_pct": 1.25,
        "allowed_symbols": frozenset({"SPY", "QQQ", "IWM", "UVXY", "VXX", "SVIX", "VIXY"}),
    },
    "ZARATTINI_2024_5M_ORB": {
        "allowed_sessions": frozenset({"RTH_CORE"}),
        "max_spread_bps": 25.0,
        "spread_strict_lt": False,
        "max_stop_pct": 1.60,
        "allowed_symbols": None,
    },
    "ZARATTINI_2025_NOISE_VWAP": {
        "allowed_sessions": frozenset({"RTH_CORE"}),
        "max_spread_bps": 3.0,
        "spread_strict_lt": True,
        "max_stop_pct": 0.50,
        "allowed_symbols": frozenset({"SPY", "QQQ", "IWM"}),
    },
    "H090_TIGHT_SPREAD_HIGH_OFI_PASSIVE_BID": {
        "allowed_sessions": frozenset({"RTH_CORE"}),
        "max_spread_bps": 10.0,
        "spread_strict_lt": False,
        "max_stop_pct": 1.25,
        "allowed_symbols": None,
    },
    "H01_PRE_TRAVEL_POCKET_PIVOT": {
        "allowed_sessions": frozenset({"PRE_MARKET", "RTH_CORE", "POST_CLOSE", "OVERNIGHT_BOATS"}),
        "max_spread_bps": 28.0,
        "spread_strict_lt": False,
        "max_stop_pct": 1.60,
        "allowed_symbols": None,
    },
    "H08_FIRST_HAND_CATALYST_IGNITION": {
        "allowed_sessions": frozenset({"PRE_MARKET", "RTH_CORE", "POST_CLOSE", "OVERNIGHT_BOATS"}),
        "max_spread_bps": 28.0,
        "spread_strict_lt": False,
        "max_stop_pct": 1.60,
        "allowed_symbols": None,
    },
}


LOSSLESS_FOUNDATION_INVARIANTS: tuple[str, ...] = (
    "PAPER_MERIT_PROVENANCE_NO_NEGATIVE_EB",
    "ZERO_NAKED_ORDERS_ADR0022_LE_2PCT_OR_8799_GUARDIAN",
    "1000RPM_WITH_100RPM_PROTECTIVE_EXIT_RESERVE_AND_ADR0024_RUNNER_FLOOR",
    "MINUS_1_50PCT_DAILY_DRAWDOWN_AND_3_STOPOUT_BREAKER",
    "SANCTIONED_KEYCHAIN_WINDOW_AND_ZERO_PII_USD_LEAKS",
)

LOSSLESS_FOUNDATION_SEED_STRATEGIES: frozenset[str] = frozenset(
    {
        "MEGA_CAP_NEAR_LOSSLESS_ORB",
        "LARGE_CAP_4X_IPO_PRECURSOR_BASKET",
        "SOTA_LOSSLESS_FOUNDATION_RUNNER",
        "SOTA_DUAL_EXTREME_BALANCE_BREAK_EARLY",
        "IPO_DAY1_CROSS_STABILIZATION_AND_VWAP_WAVE2_V1",
        "SOTA_ZERO_SELL_VWAP_BRACKET",
    }
)

GRAND_MERIT_EXECUTION_LANES: dict[str, dict[str, Any]] = {
    "S1_PREWALL_BACKTEST_FACTORY": {
        "lane_id": "S1_PREWALL_BACKTEST_FACTORY",
        "tier": "SIM_BACKTEST",
        "order": 1,
        "gating_policy": "NEVER_GATED",
        "primary_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "macro_hub_lane": "T3_prewall_cpcv_gpu_and_strategy_factory",
        "repos": ("sota-compounding-lab", "trading-sota", "tsl", "sota-private-vault"),
        "engines": ("polars", "duckdb", "vectorbt", "skfolio-cpcv", "ml4t-dsr", "rtx4090-gpu"),
        "handbook_id": "H-S1_PREWALL_CPCV_DSR_HLZ_FACTORY",
        "aggressiveness": "EXHAUSTIVE_PREWALL_SWEEP",
        "invariants": ("study_end_date <= 2026-10-15", "ADIA #19 MinTRL", "HLZ t*(N)", "1x/2x Almgren-Chriss impact"),
    },
    "S2_EVENT_SIM_MICROSTRUCTURE": {
        "lane_id": "S2_EVENT_SIM_MICROSTRUCTURE",
        "tier": "EVENT_SIM",
        "order": 2,
        "gating_policy": "NEVER_GATED",
        "primary_surface": "stationary_noesis_carbon_wsl2",
        "failover_surface": "portable_mac_m5_max",
        "macro_hub_lane": "T2_ibkr_paper_4002_and_event_sim_parity",
        "repos": ("meridian", "astrolabe"),
        "engines": ("nautilus_trader-v2rc9", "hftbacktest-RiskAdverseQueueModel"),
        "handbook_id": "H-S2_QUEUE_COLLAR_AND_LOSSLESS_SIM",
        "aggressiveness": "MICROSTRUCTURE_PARITY_VERIFICATION",
        "invariants": (
            "RiskAdverseQueueModel -n 8",
            "ADR-0022 <= 2.00% hard stop verified in sim",
            "halt & collar replay",
        ),
    },
    "PAPER_P1_ALPACA_LOSSLESS_FOUNDATION": {
        "lane_id": "PAPER_P1_ALPACA_LOSSLESS_FOUNDATION",
        "tier": "PAPER_FARM",
        "order": 3,
        "gating_policy": "NEVER_GATED",
        "broker": "ALPACA_PAPER",
        "account_prefix": "PA",
        "account_alias": "Account_C_Protect",
        "keychain_service": "canon-alpaca-paper-protect",
        "port": 8799,
        "rate_limit_rpm": 1000,
        "primary_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "macro_hub_lane": "T1_live_24x5_alpaca_paper_and_guardian",
        "repos": ("sota-dynamic-trail-c",),
        "handbook_id": "H-C_LOSSLESS_FOUNDATION_LIVE_MIRROR",
        "aggressiveness": "CONSERVATIVE_LOSSLESS_MIRROR",
        "gross_leverage_max_x": 2.0,
        "max_stop_pct": 1.00,
        "adr0022_ceiling_pct": MAX_STOP_ADR0022_PCT,
        "live_foundation_seed": True,
        "strategies": (
            "MEGA_CAP_NEAR_LOSSLESS_ORB",
            "LARGE_CAP_4X_IPO_PRECURSOR_BASKET",
            "SOTA_LOSSLESS_FOUNDATION_RUNNER",
            "EXTENDED_HOURS_24X5_GUARDIAN",
        ),
    },
    "PAPER_P2_ALPACA_BALANCED_RANKER": {
        "lane_id": "PAPER_P2_ALPACA_BALANCED_RANKER",
        "tier": "PAPER_FARM",
        "order": 4,
        "gating_policy": "NEVER_GATED",
        "broker": "ALPACA_PAPER",
        "account_prefix": "PA",
        "account_alias": "Account_B_Windows",
        "keychain_service": "canon-alpaca-paper-windows",
        "port": 8787,
        "rate_limit_rpm": 1000,
        "primary_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "macro_hub_lane": "T1_live_24x5_alpaca_paper_and_guardian",
        "repos": ("sota-mover-ranker",),
        "handbook_id": "H-B_BALANCED_WHOLE_MARKET_AND_IPO",
        "aggressiveness": "BALANCED_COMPOUNDING",
        "gross_leverage_max_x": 3.0,
        "max_stop_pct": 1.85,
        "adr0022_ceiling_pct": MAX_STOP_ADR0022_PCT,
        "live_foundation_seed": False,
        "strategies": (
            "SOTA_DUAL_EXTREME_BALANCE_BREAK_EARLY",
            "H01_PRE_TRAVEL_POCKET_PIVOT",
            "SOTA_ZERO_SELL_VWAP_BRACKET",
            "IPO_DAY1_CROSS_STABILIZATION_AND_VWAP_WAVE2_V1",
        ),
    },
    "PAPER_P3_ALPACA_AGGRESSIVE_LAB": {
        "lane_id": "PAPER_P3_ALPACA_AGGRESSIVE_LAB",
        "tier": "PAPER_FARM",
        "order": 5,
        "gating_policy": "NEVER_GATED",
        "broker": "ALPACA_PAPER",
        "account_prefix": "PA",
        "account_alias": "Account_A_Frontier",
        "keychain_service": "trading-sota-alpaca",
        "port": 8797,
        "rate_limit_rpm": 1000,
        "primary_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "macro_hub_lane": "T1_live_24x5_alpaca_paper_and_guardian",
        "repos": ("sota-mover-ranker", "trading-sota", "tsl"),
        "handbook_id": "H-A_AGGRESSIVE_FRONTIER_CRUCIBLE",
        "aggressiveness": "AGGRESSIVE_FRONTIER_CRUCIBLE",
        "gross_leverage_max_x": 4.0,
        "max_stop_pct": 2.00,
        "adr0022_ceiling_pct": MAX_STOP_ADR0022_PCT,
        "live_foundation_seed": False,
        "strategies": (
            "SOTA_DUAL_CLIMAX_STOP_AND_REVERSE",
            "STOCKBEE_EPISODIC_PIVOT_DAY1",
            "STOCKBEE_MOMENTUM_BURST_4PCT",
            "PEAD_POST_EARNINGS_DRIFT",
            "RAPID_WAVE2_REENTRY_STRESS",
        ),
    },
    "PAPER_P4_IBKR_INSTITUTIONAL_4002": {
        "lane_id": "PAPER_P4_IBKR_INSTITUTIONAL_4002",
        "tier": "PAPER_FARM",
        "order": 6,
        "gating_policy": "NEVER_GATED",
        "broker": "IBKR_PAPER",
        "account_prefix": "DU",
        "account_alias": "Account_D_IBKR_4002",
        "keychain_service": "ibkr-gateway-paper-4002",
        "port": 4002,
        "rate_limit_rpm": 3000,
        "primary_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "macro_hub_lane": "T2_ibkr_paper_4002_and_event_sim_parity",
        "repos": ("astrolabe", "meridian", "sota-mover-ranker"),
        "handbook_id": "H-D_IBKR_INSTITUTIONAL_OUTSIDERTH_3000RPM",
        "aggressiveness": "INSTITUTIONAL_CROSS_BROKER_PARITY",
        "gross_leverage_max_x": 4.0,
        "max_stop_pct": 2.00,
        "adr0022_ceiling_pct": MAX_STOP_ADR0022_PCT,
        "live_foundation_seed": False,
        "strategies": (
            "IBKR_OUTSIDERTH_NATIVE_OTO",
            "NAUTILUS_CROSS_BROKER_PARITY",
            "HIGH_THROUGHPUT_3000RPM_OVERFLOW",
        ),
    },
    "LIVE_L5_STAGE5_LOSSLESS": {
        "lane_id": "LIVE_L5_STAGE5_LOSSLESS",
        "tier": "STAGE5_LOSSLESS_LIVE",
        "order": 7,
        "gating_policy": "PROVEN_AUTOMATION_ONLY_LOSSLESS_FOUNDATION",
        "broker": "ALPACA_LIVE",
        "account_prefix": "LIVE",
        "account_alias": "Live_Stage5_Lossless",
        "keychain_service": "canon-alpaca-live|claude-trading-skills-live",
        "port": 8798,
        "rate_limit_rpm": 1000,
        "protective_exit_reserve_rpm": 100,
        "daily_drawdown_breaker_pct": -1.50,
        "primary_surface": "stationary_noesis_win32",
        "failover_surface": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "macro_hub_lane": "T1_live_24x5_alpaca_paper_and_guardian",
        "repos": ("sota-mover-ranker", "sota-dynamic-trail-c"),
        "handbook_id": "H-L5_STAGE5_LOSSLESS_FOUNDATION_AND_MERIT_GRADUATES",
        "aggressiveness": "LOSSLESS_FOUNDATION_TO_MERIT_GRADUATED",
        "starts_with_lossless_foundation": True,
        "adr0022_ceiling_pct": MAX_STOP_ADR0022_PCT,
        "invariants": LOSSLESS_FOUNDATION_INVARIANTS,
    },
}

GEMINI_TO_ORCA_ORCHESTRATION_MAP: dict[str, dict[str, Any]] = {
    "master_control_plane": {
        "runtime": "Antigravity Native Gemini (Gemini 4 Neon / Carbon + run_workflow WF20)",
        "owns": "Cross-repo architecture, merit-ladder governance, ADR enforcement, E2E verification, owner live handoff",
        "workflow_script": "~/.agents/workflows/grand_merit_harness_workflow.py",
    },
    "orca_lead_central_supervisor": {
        "runtime": "Claude Code cc-lead (claude-fable-5-2 xhigh + OMC v2 + Orca)",
        "owns": "Multi-session worker supervision, adversarial falsification, paper-to-live firewall verification",
        "cli": "~/.agents/bin/sota-cc-hub status",
    },
    "workstation_prewall_backtest_engine": {
        "runtime": "Noesis Win32 64c/128GB/RTX4090 (Codex OMX gpt-6.2-astra + DSH deepseek-flash)",
        "owns": "Lane S1: NEVER-GATED pre-wall CPCV/DSR/HLZ/2x-impact sweeps on Z:/sota-data/prewall-lake",
        "orca_target": "--on 100.110.115.22",
    },
    "workstation_event_sim_engine": {
        "runtime": "Noesis-Carbon WSL2 ext4 (NautilusTrader v2.0.0rc9 + hftbacktest RiskAdverseQueueModel)",
        "owns": "Lane S2: NEVER-GATED POSIX queue, spread, halt, collar & Lossless Foundation parity simulation",
        "orca_target": "--on 100.110.115.22",
    },
    "sovereign_workstation_trading_engine": {
        "runtime": "Stationary Noesis Workstation (100.110.115.22, 64c/128GB/RTX4090 + Noesis-Carbon WSL2)",
        "owns": "Primary 24/5 Main Framework Foundation + 4 NEVER-GATED Paper Accounts (:8799 P1, :8787 P2, :8797 P3, :4002 P4) + Proven-Only Stage-5 Live (:8798) + 4K TradingView",
        "orca_target": "--on 100.110.115.22",
    },
    "portable_mac_command_cockpit_and_failover": {
        "runtime": "Portable MacBook Pro M5 Max (100.93.211.101, 64GB)",
        "owns": "Portable Command Cockpit (read-only mirror of 100.110.115.22 while Noesis is active) + Explicit Single-Host Hot Failover when Workstation offline",
        "orca_target": "local (portable_mac_m5_max)",
    },
}


def _finite(val: float) -> bool:
    return not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(float(val))


@dataclass(frozen=True)
class MeritStrategyEvidence:
    """Empirical Sim + Multi-Paper evidence packet evaluated for automatic lane assignment & Live graduation."""

    strategy_id: str
    study_end_date: str
    max_stop_pct: float
    sim_engine_verified: bool
    prewall_net_1x_bps: float
    prewall_net_2x_bps: float
    closed_roundtrips: int = 0
    distinct_paper_accounts: tuple[str, ...] = ()
    eb_expectancy_r: float = 0.0
    profit_factor: float = 1.0
    realized_slippage_bps: float | None = None
    adr0022_breaches: int = 0
    tuning_regime: str = "NEUTRAL"
    lossless_foundation_verified: bool = False
    p1_closed_roundtrips: int | None = None


VALID_PAPER_ACCOUNT_IDS: frozenset[str] = frozenset(
    k for k, v in GRAND_MERIT_EXECUTION_LANES.items() if v["tier"] == "PAPER_FARM"
)


def _is_nonneg_int(val: Any) -> bool:
    return not isinstance(val, bool) and isinstance(val, int) and val >= 0


def evaluate_merit_ladder(ev: MeritStrategyEvidence) -> dict[str, Any]:
    """Deterministically place a strategy across Sim (NEVER GATED) -> 4-Paper Farm (NEVER GATED) -> Stage-5 Live (PROVEN ONLY)."""
    reasons: list[str] = []
    if not isinstance(ev.strategy_id, str) or not ev.strategy_id.strip():
        reasons.append("MISSING_STRATEGY_ID")
    if not isinstance(ev.study_end_date, str) or not ev.study_end_date.strip():
        reasons.append("INVALID_STUDY_END_DATE")
    else:
        try:
            end_d = dt.date.fromisoformat(ev.study_end_date.strip())
            if end_d > STUDY_WALL_DATE:
                reasons.append(f"PREWALL_VIOLATION:{ev.study_end_date}>{STUDY_WALL_DATE.isoformat()}")
        except ValueError:
            reasons.append(f"INVALID_STUDY_END_DATE:{ev.study_end_date}")
    if not isinstance(ev.sim_engine_verified, bool) or not isinstance(ev.lossless_foundation_verified, bool):
        reasons.append("INVALID_BOOLEAN_VERIFICATION_FLAG")
    if not _is_nonneg_int(ev.closed_roundtrips):
        reasons.append(f"INVALID_CLOSED_ROUNDTRIPS:{ev.closed_roundtrips!r}")
    if not _is_nonneg_int(ev.adr0022_breaches):
        reasons.append(f"INVALID_ADR0022_BREACHES:{ev.adr0022_breaches!r}")
    elif ev.adr0022_breaches > 0:
        reasons.append(f"ADR0022_REALIZED_BREACHES:{ev.adr0022_breaches}")
    if ev.p1_closed_roundtrips is not None:
        if not _is_nonneg_int(ev.p1_closed_roundtrips):
            reasons.append(f"INVALID_P1_CLOSED_ROUNDTRIPS:{ev.p1_closed_roundtrips!r}")
        elif _is_nonneg_int(ev.closed_roundtrips) and ev.p1_closed_roundtrips > ev.closed_roundtrips:
            reasons.append(f"P1_ROUNDTRIPS_EXCEED_TOTAL:{ev.p1_closed_roundtrips}>{ev.closed_roundtrips}")
    if not _finite(ev.max_stop_pct) or ev.max_stop_pct <= 0.0 or ev.max_stop_pct > MAX_STOP_ADR0022_PCT:
        reasons.append(f"ADR0022_STOP_VIOLATION:{ev.max_stop_pct}")
    else:
        norm_check = str(ev.strategy_id or "").strip().upper()
        strat_contract = POST_ANT_STRATEGY_CONTRACTS_V2.get(norm_check)
        if strat_contract is not None and ev.max_stop_pct > float(strat_contract["max_stop_pct"]):
            reasons.append(
                f"STRATEGY_STOP_CEILING_EXCEEDED:{norm_check}:{ev.max_stop_pct}>{strat_contract['max_stop_pct']}"
            )
    if not all(
        _finite(v)
        for v in (
            ev.prewall_net_1x_bps,
            ev.prewall_net_2x_bps,
            ev.eb_expectancy_r,
            ev.profit_factor,
        )
    ):
        reasons.append("NON_FINITE_METRIC")
    if ev.realized_slippage_bps is not None and not _finite(ev.realized_slippage_bps):
        reasons.append("NON_FINITE_METRIC")

    acct_set: set[str] = set()
    if isinstance(ev.distinct_paper_accounts, (str, bytes)) or not isinstance(
        ev.distinct_paper_accounts, (tuple, list, set, frozenset)
    ):
        reasons.append("INVALID_PAPER_ACCOUNTS_COLLECTION")
    else:
        for raw_acct in ev.distinct_paper_accounts:
            if not isinstance(raw_acct, str) or raw_acct.strip() not in VALID_PAPER_ACCOUNT_IDS:
                reasons.append(f"INVALID_PAPER_ACCOUNT_ID:{raw_acct!r}")
            else:
                acct_set.add(raw_acct.strip())

    if reasons:
        return {
            "strategy_id": ev.strategy_id,
            "assigned_lanes": [],
            "merit_tier": "HARD_REJECTED_SAFETY_OR_PREWALL",
            "live_8798_allowed": False,
            "live_notional_scale": 0.0,
            "gating_policy": "SAFETY_REJECTED",
            "reasons": reasons,
        }

    # ADR-0036 / ADR-0064: quarantined noisy/negative-expectancy strategies & family variants
    # are NEVER eligible for active Paper or Stage-5 Live (runs BEFORE Full-Auto & Canary!).
    norm_sid = str(ev.strategy_id or "").strip().upper()
    if is_post_ant_strategy_quarantined(norm_sid):
        return {
            "strategy_id": ev.strategy_id,
            "assigned_lanes": [],
            "merit_tier": "QUARANTINED_ADR0064_BLOCKED",
            "live_8798_allowed": False,
            "live_notional_scale": 0.0,
            "gating_policy": "QUARANTINED_OUT_OF_ACTIVE_PAPER_AND_LIVE",
            "reasons": [f"QUARANTINED_ADR0064:{norm_sid}"],
        }

    # Probation / Negative EB stays strictly in Sim/Aggressive Paper Lab, NEVER promoted to Live!
    if ev.tuning_regime == "PROBATION_NEGATIVE_EB_THROTTLE" or ev.eb_expectancy_r < 0.0:
        return {
            "strategy_id": ev.strategy_id,
            "assigned_lanes": [
                "S1_PREWALL_BACKTEST_FACTORY",
                "S2_EVENT_SIM_MICROSTRUCTURE",
                "PAPER_P3_ALPACA_AGGRESSIVE_LAB",
            ],
            "merit_tier": "PAPER_P3_PROBATION_RETEST",
            "live_8798_allowed": False,
            "live_notional_scale": 0.0,
            "gating_policy": "PAPER_NEVER_GATED_LIVE_DENIED_NEGATIVE_EB",
            "reasons": [f"PROBATION_OR_NEGATIVE_EB(regime={ev.tuning_regime},eb_r={ev.eb_expectancy_r:+.2f}R)"],
        }

    if ev.sim_engine_verified is not True or ev.prewall_net_1x_bps <= 0.0:
        return {
            "strategy_id": ev.strategy_id,
            "assigned_lanes": ["S1_PREWALL_BACKTEST_FACTORY", "S2_EVENT_SIM_MICROSTRUCTURE"],
            "merit_tier": "SIM_LANES_UNPROVEN",
            "live_8798_allowed": False,
            "live_notional_scale": 0.0,
            "gating_policy": "SIM_NEVER_GATED",
            "reasons": ["AWAITING_SIM_VERIFICATION_OR_POSITIVE_1X"],
        }

    has_p1_foundation = "PAPER_P1_ALPACA_LOSSLESS_FOUNDATION" in acct_set
    # Strict proven P1 roundtrip attribution (unattributed mixed ledgers yield 0 proven P1 trades on BOTH live tiers!)
    if ev.p1_closed_roundtrips is not None:
        proven_p1_roundtrips = ev.p1_closed_roundtrips
    elif acct_set == {"PAPER_P1_ALPACA_LOSSLESS_FOUNDATION"}:
        proven_p1_roundtrips = ev.closed_roundtrips
    else:
        proven_p1_roundtrips = 0

    # Full Stage-5 Lossless Live Graduation (1.00x fully automated; requires explicit lossless proof, slippage, P1>=15 & non-P1>=1!)
    non_p1_roundtrips = ev.closed_roundtrips - proven_p1_roundtrips
    if (
        ev.lossless_foundation_verified is True
        and ev.prewall_net_2x_bps > 0.0
        and ev.closed_roundtrips >= 30
        and len(acct_set) >= 2
        and has_p1_foundation
        and proven_p1_roundtrips >= 15
        and non_p1_roundtrips >= 1
        and ev.eb_expectancy_r >= 0.20
        and ev.profit_factor >= 1.35
        and ev.realized_slippage_bps is not None
        and ev.realized_slippage_bps <= 3.0
    ):
        return {
            "strategy_id": ev.strategy_id,
            "assigned_lanes": [
                "PAPER_P1_ALPACA_LOSSLESS_FOUNDATION",
                "PAPER_P2_ALPACA_BALANCED_RANKER",
                "PAPER_P4_IBKR_INSTITUTIONAL_4002",
                "LIVE_L5_STAGE5_LOSSLESS",
            ],
            "merit_tier": "STAGE5_LOSSLESS_LIVE_FULL_AUTO",
            "live_8798_allowed": True,
            "live_notional_scale": 1.00,
            "gating_policy": "PROVEN_AUTOMATION_UNRESTRICTED_WITH_LOSSLESS_INVARIANTS",
            "reasons": [
                f"MERIT_CERTIFIED(n={ev.closed_roundtrips},accts={len(acct_set)},eb={ev.eb_expectancy_r:+.2f}R,pf={ev.profit_factor:.2f})"
            ],
        }

    # Stage-5 Lossless Foundation Canary (0.10x automated on :8798; ZERO strategies bypass proven P1 roundtrips!)
    if (
        ev.lossless_foundation_verified is True
        and ev.prewall_net_2x_bps > 0.0
        and has_p1_foundation
        and proven_p1_roundtrips >= 15
        and ev.eb_expectancy_r >= 0.12
    ):
        return {
            "strategy_id": ev.strategy_id,
            "assigned_lanes": [
                "PAPER_P1_ALPACA_LOSSLESS_FOUNDATION",
                "PAPER_P2_ALPACA_BALANCED_RANKER",
                "PAPER_P4_IBKR_INSTITUTIONAL_4002",
                "LIVE_L5_STAGE5_LOSSLESS",
            ],
            "merit_tier": "STAGE5_LOSSLESS_FOUNDATION_CANARY_10PCT",
            "live_8798_allowed": True,
            "live_notional_scale": 0.10,
            "gating_policy": "LOSSLESS_FOUNDATION_CANARY_AUTO_ACCUMULATING_MERIT",
            "reasons": [
                f"P1_PROVEN_CANARY(2x_bps={ev.prewall_net_2x_bps:+.1f},p1_n={proven_p1_roundtrips},eb={ev.eb_expectancy_r:+.2f}R)"
            ],
        }

    # Balanced Paper Core + IBKR Institutional Parity (NEVER GATED)
    if ev.closed_roundtrips >= 10 and ev.eb_expectancy_r >= 0.05:
        return {
            "strategy_id": ev.strategy_id,
            "assigned_lanes": [
                "PAPER_P2_ALPACA_BALANCED_RANKER",
                "PAPER_P3_ALPACA_AGGRESSIVE_LAB",
                "PAPER_P4_IBKR_INSTITUTIONAL_4002",
            ],
            "merit_tier": "PAPER_P2_BALANCED_AND_IBKR_PARITY",
            "live_8798_allowed": False,
            "live_notional_scale": 0.0,
            "gating_policy": "PAPER_NEVER_GATED",
            "reasons": [f"PAPER_PROMOTED_FROM_P3_TO_P2_P4(n={ev.closed_roundtrips},eb={ev.eb_expectancy_r:+.2f}R)"],
        }

    # Default Sim-cleared entry into Aggressive Frontier Paper Crucible (NEVER GATED!)
    return {
        "strategy_id": ev.strategy_id,
        "assigned_lanes": ["PAPER_P3_ALPACA_AGGRESSIVE_LAB"],
        "merit_tier": "PAPER_P3_AGGRESSIVE_CRUCIBLE",
        "live_8798_allowed": False,
        "live_notional_scale": 0.0,
        "gating_policy": "PAPER_NEVER_GATED",
        "reasons": [f"SIM_CLEARED_AUTO_ADMITTED_TO_P3_CRUCIBLE(1x_bps={ev.prewall_net_1x_bps:+.1f})"],
    }


def build_grand_merit_harness_manifest() -> dict[str, Any]:
    """Emit the canonical deterministic Grand Merit-Promotion Harness manifest across Sim, 4 Paper Accounts & Stage-5 Live."""
    sim_lanes = [k for k, v in GRAND_MERIT_EXECUTION_LANES.items() if v["tier"] in ("SIM_BACKTEST", "EVENT_SIM")]
    paper_lanes = [k for k, v in GRAND_MERIT_EXECUTION_LANES.items() if v["tier"] == "PAPER_FARM"]
    alpaca_papers = [k for k in paper_lanes if GRAND_MERIT_EXECUTION_LANES[k]["broker"] == "ALPACA_PAPER"]
    ibkr_papers = [k for k in paper_lanes if GRAND_MERIT_EXECUTION_LANES[k]["broker"] == "IBKR_PAPER"]
    live_lanes = [k for k, v in GRAND_MERIT_EXECUTION_LANES.items() if v["tier"] == "STAGE5_LOSSLESS_LIVE"]

    payload: dict[str, Any] = {
        "ok": True,
        "schema_version": MERIT_HARNESS_SCHEMA_VERSION,
        "adr": "ADR-0028",
        "post_ant_consolidation_adr": "ADR-0036",
        "era": POST_ANT_ERA_ID,
        "ecosystem_version": "3.11.1",
        "active_market_targets_schema": ACTIVE_MARKET_TARGETS_SCHEMA,
        "strategy_contract_schema": STRATEGY_CONTRACT_SCHEMA_V2,
        "post_ant_concentrated_sota_strategies": sorted(POST_ANT_CONCENTRATED_SOTA_STRATEGIES),
        "post_ant_quarantined_strategies": sorted(POST_ANT_QUARANTINED_STRATEGIES),
        "primary_sovereign_host": "stationary_noesis_win32",
        "portable_cockpit_and_failover_host": "portable_mac_m5_max",
        "single_active_broker_host_only": True,
        "counts": {
            "total_execution_lanes": len(GRAND_MERIT_EXECUTION_LANES),
            "sim_lanes_never_gated": len(sim_lanes),
            "paper_accounts_never_gated": len(paper_lanes),
            "alpaca_paper_accounts": len(alpaca_papers),
            "ibkr_paper_accounts": len(ibkr_papers),
            "live_stage5_lossless_lanes": len(live_lanes),
        },
        "gating_charter": {
            "sim_lanes": "NEVER_GATED",
            "paper_farm_4_accounts": "NEVER_GATED",
            "live_stage5_8798": "PROVEN_AUTOMATION_ONLY_STARTING_WITH_LOSSLESS_FOUNDATION",
        },
        "merit_progression": (
            "S1_PREWALL_BACKTEST_FACTORY (Noesis 64c/RTX4090, NEVER GATED) -> "
            "S2_EVENT_SIM_MICROSTRUCTURE (Noesis-Carbon WSL2 Nautilus/QueueModel, NEVER GATED) -> "
            "PAPER_P3_ALPACA_AGGRESSIVE_LAB (:8797 Account A, NEVER GATED) -> "
            "PAPER_P2_ALPACA_BALANCED_RANKER (:8787 Account B) + PAPER_P4_IBKR_INSTITUTIONAL_4002 (:4002 Account D, NEVER GATED) -> "
            "PAPER_P1_ALPACA_LOSSLESS_FOUNDATION (:8799 Account C Live Mirror, NEVER GATED) -> "
            "LIVE_L5_STAGE5_LOSSLESS (:8798, PROVEN AUTOMATION ONLY starting with Lossless Foundation)"
        ),
        "lossless_foundation_invariants": list(LOSSLESS_FOUNDATION_INVARIANTS),
        "lossless_foundation_seed_strategies": sorted(LOSSLESS_FOUNDATION_SEED_STRATEGIES),
        "lanes": GRAND_MERIT_EXECUTION_LANES,
        "gemini_to_orca_orchestration": GEMINI_TO_ORCA_ORCHESTRATION_MAP,
    }
    raw_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=list).encode()).hexdigest()
    payload["harness_sha256"] = raw_hash
    return payload


def evaluate_post_ant_symbol_merit_admission(
    *,
    symbol: str,
    strategy_id: str,
    merit_score: float,
    df_pillars_manifested: int,
    spread_bps: float,
    sec_dilution_clean: bool = False,
    max_stop_pct: float = 1.60,
    session_mode: str = "RTH_CORE",
) -> dict[str, Any]:
    """Symbol-agnostic Post-ANT admission gate binding any manifested DF1..DF12 equity to lossless Paper/Merit lanes."""
    sym = str(symbol or "").strip().upper()
    sid = str(strategy_id or "").strip().upper()
    sess = str(session_mode or "").strip().upper()
    if not sym or not sym.replace(".", "").isalnum():
        raise ValueError(f"Invalid symbol: {symbol!r}")
    if sess not in POST_ANT_VALID_SESSIONS:
        raise ValueError(f"Unsupported session_mode: {session_mode!r}")
    if isinstance(df_pillars_manifested, bool) or not isinstance(df_pillars_manifested, int):
        raise TypeError("df_pillars_manifested must be an int")
    if not isinstance(sec_dilution_clean, bool):
        raise TypeError("sec_dilution_clean must be a bool")
    if not (_finite(merit_score) and _finite(spread_bps) and _finite(max_stop_pct)):
        raise ValueError("merit_score, spread_bps, and max_stop_pct must be finite non-bool numbers")

    reasons: list[str] = []
    contract = POST_ANT_STRATEGY_CONTRACTS_V2.get(sid)
    if is_post_ant_strategy_quarantined(sid):
        reasons.append(f"QUARANTINED_ADR0064:{sid}")
    elif contract is None:
        reasons.append(f"NON_ACTIVE_SOTA_STRATEGY:{sid}")
    else:
        if sess not in contract["allowed_sessions"]:
            reasons.append(f"STRATEGY_SESSION_NOT_ALLOWED:{sid}:{sess}")
        allowed_syms = contract["allowed_symbols"]
        if allowed_syms is not None and sym not in allowed_syms:
            reasons.append(f"STRATEGY_SYMBOL_NOT_ALLOWED:{sid}:{sym}")
        c_max_spr = float(contract["max_spread_bps"])
        if spread_bps > 0.0 and (
            (contract["spread_strict_lt"] and spread_bps >= c_max_spr)
            or (not contract["spread_strict_lt"] and spread_bps > c_max_spr)
        ):
            reasons.append(f"STRATEGY_SPREAD_EXCEEDS_CONTRACT:{sid}:{spread_bps}>{c_max_spr}")
        c_max_stop = float(contract["max_stop_pct"])
        if 0.0 < max_stop_pct <= MAX_STOP_ADR0022_PCT and max_stop_pct > c_max_stop:
            reasons.append(f"STRATEGY_STOP_EXCEEDS_CONTRACT:{sid}:{max_stop_pct}>{c_max_stop}")

    if not sec_dilution_clean:
        reasons.append("SEC_90D_DILUTION_UNVERIFIED_OR_BLOCKED")
    if max_stop_pct <= 0.0 or max_stop_pct > MAX_STOP_ADR0022_PCT:
        reasons.append(f"ADR0022_STOP_OUT_OF_BOUNDS:{max_stop_pct}")
    if spread_bps <= 0.0 or spread_bps > 35.0:
        reasons.append(f"SPREAD_OUT_OF_BOATS_CAP:{spread_bps}")
    if df_pillars_manifested < 0 or df_pillars_manifested > 6:
        reasons.append(f"INVALID_DF_PILLARS_COUNT:{df_pillars_manifested}")
    elif df_pillars_manifested < 3:
        reasons.append(f"INSUFFICIENT_DF_PILLARS:{df_pillars_manifested}")

    if reasons:
        tier = "REJECTED"
        lanes: list[str] = []
    elif merit_score >= 58.0 and spread_bps <= 15.0 and df_pillars_manifested >= 4:
        tier = "MERIT_TIER_1_CORE"
        lanes = [
            "PAPER_P1_ALPACA_LOSSLESS_FOUNDATION",
            "PAPER_P2_ALPACA_BALANCED_RANKER",
            "PAPER_P3_ALPACA_AGGRESSIVE_LAB",
            "PAPER_P4_IBKR_INSTITUTIONAL_4002",
        ]
    elif merit_score >= 38.0 and spread_bps <= 35.0 and df_pillars_manifested >= 3:
        tier = "MERIT_TIER_2_ACTIVE"
        lanes = [
            "PAPER_P2_ALPACA_BALANCED_RANKER",
            "PAPER_P3_ALPACA_AGGRESSIVE_LAB",
            "PAPER_P4_IBKR_INSTITUTIONAL_4002",
        ]
    else:
        tier = "WATCH_ONLY"
        lanes = []

    return {
        "era": POST_ANT_ERA_ID,
        "symbol": sym,
        "strategy_id": sid,
        "merit_tier": tier,
        "admitted": tier in ("MERIT_TIER_1_CORE", "MERIT_TIER_2_ACTIVE"),
        "assigned_paper_lanes": lanes,
        "rejection_reasons": reasons,
        "take_profit_cap_enabled": False,
        "adr0022_max_stop_pct": MAX_STOP_ADR0022_PCT,
        "promotion_track": "PROTECTIVE_FILTER_OR_GOVERNANCE",
        "standalone_alpha_claim": False,
    }
