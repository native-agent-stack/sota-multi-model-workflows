"""5-Stage Compounding Strategy Promotion Validator (`Sim -> Backtest -> Paper -> Fine-Tune -> Broker`)."""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import Any

STUDY_WALL_DATE = dt.date(2026, 10, 15)
MAX_STOP_ADR0022_PCT = 2.00
FORBIDDEN_IBKR_LIVE_PORTS = frozenset({4001, 7496})


def compute_hlz_t_hurdle(trial_n: int, base_hurdle: float = 3.00) -> float:
    """Dynamic Harvey-Liu-Zhu multiple-testing t-statistic hurdle growing with global trial count N."""
    if trial_n < 1:
        raise ValueError("trial_n must be >= 1")
    return round(max(base_hurdle, math.sqrt(max(9.0, 2.0 * math.log(max(2, trial_n)) + 8.35))), 4)


@dataclass(frozen=True)
class StrategyCandidateManifest:
    strategy_id: str
    study_end_date: str
    events_count: int
    distinct_dates: int
    t_stat_date_clustered: float
    trial_n: int
    dsr_probability: float
    cpcv_positive_fold_pct: float
    net_expectancy_1x_bps: float
    net_expectancy_2x_impact_bps: float
    sim_engine_verified: bool
    max_initial_stop_pct: float
    mega_cap_scratch_bps: float
    broker_lane: str  # "ALPACA_PAPER" or "IBKR_PAPER"
    account_prefix: str  # "PA" or "DU"
    broker_port: int | None = None


def evaluate_promotion_gate(c: StrategyCandidateManifest) -> dict[str, Any]:
    """Deterministically evaluate whether a candidate clears all 5 SOTA promotion & safety gates."""
    failures: list[str] = []
    end_d = dt.date.fromisoformat(c.study_end_date)
    if end_d > STUDY_WALL_DATE:
        failures.append(f"PREWALL_VIOLATION:{c.study_end_date}>{STUDY_WALL_DATE.isoformat()}")

    if c.max_initial_stop_pct <= 0.0 or c.max_initial_stop_pct > MAX_STOP_ADR0022_PCT:
        failures.append(f"ADR0022_STOP_VIOLATION:{c.max_initial_stop_pct}")

    if not (4.0 <= c.mega_cap_scratch_bps <= 25.0):
        failures.append(f"NEAR_LOSSLESS_SCRATCH_BOUNDS:{c.mega_cap_scratch_bps}")

    if c.broker_port in FORBIDDEN_IBKR_LIVE_PORTS:
        failures.append(f"HARD_FIREWALL_LIVE_PORT:{c.broker_port}")

    if c.broker_lane == "ALPACA_PAPER":
        if c.account_prefix != "PA":
            failures.append("HARD_FIREWALL_NON_PA_ALPACA")
    elif c.broker_lane == "IBKR_PAPER":
        if c.account_prefix != "DU" or (c.broker_port is not None and c.broker_port != 4002):
            failures.append("HARD_FIREWALL_NON_DU_OR_PORT_IBKR")
    else:
        failures.append(f"UNSANCTIONED_BROKER_LANE:{c.broker_lane}")

    if not c.sim_engine_verified:
        failures.append("SIM_STAGE_UNVERIFIED")

    req_t = compute_hlz_t_hurdle(c.trial_n)
    stat_ok = (
        c.events_count >= 200
        and c.distinct_dates >= 60
        and c.t_stat_date_clustered >= req_t
        and c.dsr_probability >= 0.95
        and c.cpcv_positive_fold_pct >= 70.0
        and c.net_expectancy_1x_bps > 0.0
        and c.net_expectancy_2x_impact_bps > 0.0
    )
    if not stat_ok:
        failures.append(f"STATISTICAL_GATE_REJECTED:t={c.t_stat_date_clustered}<{req_t}_or_dsr={c.dsr_probability}")

    hard_safety_ok = not any(f.startswith(("HARD_FIREWALL", "ADR0022", "PREWALL", "UNSANCTIONED")) for f in failures)
    stage_reached = (
        "STAGE_4_PAPER_EXECUTION_APPROVED"
        if not failures
        else ("STAGE_1_PROTECTIVE_OVERLAY_ONLY" if hard_safety_ok else "HARD_BLOCKED")
    )
    return {
        "strategy_id": c.strategy_id,
        "approved_for_autonomous_alpha": len(failures) == 0,
        "hard_safety_verified": hard_safety_ok,
        "required_hlz_t_hurdle": req_t,
        "stage_reached": stage_reached,
        "failures": failures,
    }
