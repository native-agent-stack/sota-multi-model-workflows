"""Grand Merit-Promotion Harness (`ADR-0027`, `sota-grand-merit-harness.v1`).

Unifies:
- **2 NEVER-GATED Sim/Backtest Lanes (`S1` Noesis Win32 64c/RTX4090 + `S2` Noesis-Carbon WSL2 Nautilus/QueueModel)**
- **4 NEVER-GATED Multi-Paper Farm Accounts on Sovereign Mac M5 Max (`3` Distinct Alpaca Paper + `1` IBKR Paper `:4002`):**
  - `PAPER_P1_ALPACA_LOSSLESS_FOUNDATION` (`Account C`, `canon-alpaca-paper-protect`, `:8799`, Conservative Lossless Live Mirror)
  - `PAPER_P2_ALPACA_BALANCED_RANKER` (`Account B`, `canon-alpaca-paper-windows`, `:8787`, Balanced Whole-Market & IPO Core)
  - `PAPER_P3_ALPACA_AGGRESSIVE_LAB` (`Account A`, `trading-sota-alpaca`, `:8797`, Aggressive Frontier Crucible)
  - `PAPER_P4_IBKR_INSTITUTIONAL_4002` (`Account D`, `127.0.0.1:4002`, `DU...`, `3,000 req/min` Cross-Broker Parity)
- **1 Proven-Automation-Only Stage-5 Lossless Live Lane (`LIVE_L5_STAGE5_LOSSLESS`, `:8798`, `ADR-0030`):**
  - Never gated once merit-proven and lossless-protected; starts immediately with the **Lossless Foundation**
    seeded by `P1` (`ADR-0022 <= 2.00%` stop / `:8799` guardian, `1,000 req/min` with `100/min` strict exit reserve,
    `ADR-0024` lossless floor/runner ratchet, `-1.50%` daily drawdown breaker, zero PII/USD telemetry).
- **Native Gemini-to-Orca Grand Orchestration:** Connects Antigravity native Gemini models (`run_workflow` WF20)
  with `cc-lead` (`OMC v2`), `Codex OMX`, `DSH` (`deepseek-flash`), and Dual-Machine Orca Automations.
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
        "primary_surface": "portable_mac_m5_max",
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
        "primary_surface": "portable_mac_m5_max",
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
        "primary_surface": "portable_mac_m5_max",
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
        "primary_surface": "portable_mac_m5_max",
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
        "primary_surface": "portable_mac_m5_max",
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
    "sovereign_mac_broker_farm": {
        "runtime": "Mac M5 Max Sovereign Broker Host (100.93.211.101)",
        "owns": "4 NEVER-GATED Paper Accounts (:8799 P1, :8787 P2, :8797 P3, :4002 P4) + Proven-Only Stage-5 Lossless Live (:8798)",
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
    realized_slippage_bps: float = 0.0
    adr0022_breaches: int = 0
    tuning_regime: str = "NEUTRAL"
    lossless_foundation_verified: bool = True


def evaluate_merit_ladder(ev: MeritStrategyEvidence) -> dict[str, Any]:
    """Deterministically place a strategy across Sim (NEVER GATED) -> 4-Paper Farm (NEVER GATED) -> Stage-5 Live (PROVEN ONLY)."""
    reasons: list[str] = []
    end_d = dt.date.fromisoformat(ev.study_end_date)
    if end_d > STUDY_WALL_DATE:
        reasons.append(f"PREWALL_VIOLATION:{ev.study_end_date}>{STUDY_WALL_DATE.isoformat()}")
    if not _finite(ev.max_stop_pct) or ev.max_stop_pct <= 0.0 or ev.max_stop_pct > MAX_STOP_ADR0022_PCT:
        reasons.append(f"ADR0022_STOP_VIOLATION:{ev.max_stop_pct}")
    if ev.adr0022_breaches > 0:
        reasons.append(f"ADR0022_REALIZED_BREACHES:{ev.adr0022_breaches}")
    if not all(
        _finite(v)
        for v in (
            ev.prewall_net_1x_bps,
            ev.prewall_net_2x_bps,
            ev.eb_expectancy_r,
            ev.profit_factor,
            ev.realized_slippage_bps,
        )
    ):
        reasons.append("NON_FINITE_METRIC")

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

    if not ev.sim_engine_verified or ev.prewall_net_1x_bps <= 0.0:
        return {
            "strategy_id": ev.strategy_id,
            "assigned_lanes": ["S1_PREWALL_BACKTEST_FACTORY", "S2_EVENT_SIM_MICROSTRUCTURE"],
            "merit_tier": "SIM_LANES_UNPROVEN",
            "live_8798_allowed": False,
            "live_notional_scale": 0.0,
            "gating_policy": "SIM_NEVER_GATED",
            "reasons": ["AWAITING_SIM_VERIFICATION_OR_POSITIVE_1X"],
        }

    acct_set = set(ev.distinct_paper_accounts)
    has_p1_foundation = "PAPER_P1_ALPACA_LOSSLESS_FOUNDATION" in acct_set

    # Full Stage-5 Lossless Live Graduation (1.00x fully automated, zero manual per-trade clicks!)
    if (
        ev.lossless_foundation_verified
        and ev.prewall_net_2x_bps > 0.0
        and ev.closed_roundtrips >= 30
        and len(acct_set) >= 2
        and has_p1_foundation
        and ev.eb_expectancy_r >= 0.20
        and ev.profit_factor >= 1.35
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

    # Stage-5 Lossless Foundation Canary (0.10x automated on :8798 for Lossless Foundation seed strategies verified at 2x cost)
    if (
        ev.lossless_foundation_verified
        and ev.prewall_net_2x_bps > 0.0
        and (
            ev.strategy_id in LOSSLESS_FOUNDATION_SEED_STRATEGIES
            or (has_p1_foundation and ev.closed_roundtrips >= 15 and ev.eb_expectancy_r >= 0.12)
        )
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
                f"LOSSLESS_FOUNDATION_SEED_OR_P1_PROVEN(2x_bps={ev.prewall_net_2x_bps:+.1f},n={ev.closed_roundtrips})"
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
        "adr": "ADR-0027",
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
