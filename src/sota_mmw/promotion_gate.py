"""5-Stage Compounding Strategy Promotion Validator (`Sim -> Backtest -> Paper -> Fine-Tune -> Broker`)."""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Any

STUDY_WALL_DATE = dt.date(2026, 10, 15)
MAX_STOP_ADR0022_PCT = 2.00
MIN_STAGE3_CLOSED_ROUNDTRIPS = 30
MIN_STAGE3_DISTINCT_SESSIONS = 10
FORBIDDEN_IBKR_LIVE_PORTS = frozenset({4001, 7496})
_STD_NORMAL = NormalDist(0.0, 1.0)


def _is_real_finite(val: float) -> bool:
    return not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(float(val))


def compute_hlz_t_hurdle(trial_n: int, base_hurdle: float = 3.00) -> float:
    """Exact Harvey-Liu-Zhu normal-quantile multiple-testing t-hurdle growing with global trial count N."""
    if isinstance(trial_n, bool) or trial_n < 1:
        raise ValueError("trial_n must be >= 1")
    if not _is_real_finite(base_hurdle) or base_hurdle <= 0.0:
        raise ValueError("base_hurdle must be finite and > 0")
    quantile = _STD_NORMAL.inv_cdf(1.0 - 0.00135 / float(trial_n))
    return round(max(float(base_hurdle), quantile), 4)


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
    closed_roundtrips: int = MIN_STAGE3_CLOSED_ROUNDTRIPS
    distinct_sessions: int = MIN_STAGE3_DISTINCT_SESSIONS


def evaluate_promotion_gate(c: StrategyCandidateManifest) -> dict[str, Any]:
    """Deterministically evaluate whether a candidate clears all 5 SOTA promotion & safety gates."""
    failures: list[str] = []
    end_d = dt.date.fromisoformat(c.study_end_date)
    if end_d > STUDY_WALL_DATE:
        failures.append(f"PREWALL_VIOLATION:{c.study_end_date}>{STUDY_WALL_DATE.isoformat()}")

    if (
        not _is_real_finite(c.max_initial_stop_pct)
        or c.max_initial_stop_pct <= 0.0
        or c.max_initial_stop_pct > MAX_STOP_ADR0022_PCT
    ):
        failures.append(f"ADR0022_STOP_VIOLATION:{c.max_initial_stop_pct}")

    if not _is_real_finite(c.mega_cap_scratch_bps) or not (4.0 <= c.mega_cap_scratch_bps <= 25.0):
        failures.append(f"NEAR_LOSSLESS_SCRATCH_BOUNDS:{c.mega_cap_scratch_bps}")

    if c.broker_port in FORBIDDEN_IBKR_LIVE_PORTS:
        failures.append(f"HARD_FIREWALL_LIVE_PORT:{c.broker_port}")

    if c.broker_lane == "ALPACA_PAPER":
        if c.account_prefix != "PA":
            failures.append("HARD_FIREWALL_NON_PA_ALPACA")
    elif c.broker_lane == "IBKR_PAPER":
        if c.account_prefix != "DU" or c.broker_port != 4002:
            failures.append("HARD_FIREWALL_NON_DU_OR_PORT_IBKR")
    else:
        failures.append(f"UNSANCTIONED_BROKER_LANE:{c.broker_lane}")

    if not c.sim_engine_verified:
        failures.append("SIM_STAGE_UNVERIFIED")

    req_t = compute_hlz_t_hurdle(c.trial_n)
    stat_floats_finite = all(
        _is_real_finite(v)
        for v in (
            c.t_stat_date_clustered,
            c.dsr_probability,
            c.cpcv_positive_fold_pct,
            c.net_expectancy_1x_bps,
            c.net_expectancy_2x_impact_bps,
        )
    )
    stat_ok = (
        stat_floats_finite
        and c.events_count >= 200
        and c.distinct_dates >= 60
        and c.t_stat_date_clustered >= req_t
        and c.dsr_probability >= 0.95
        and c.cpcv_positive_fold_pct >= 70.0
        and c.net_expectancy_1x_bps > 0.0
        and c.net_expectancy_2x_impact_bps > 0.0
    )
    if not stat_ok:
        failures.append(f"STATISTICAL_GATE_REJECTED:t={c.t_stat_date_clustered}<{req_t}_or_dsr={c.dsr_probability}")

    stage3_ok = (
        not isinstance(c.closed_roundtrips, bool)
        and c.closed_roundtrips >= MIN_STAGE3_CLOSED_ROUNDTRIPS
        and not isinstance(c.distinct_sessions, bool)
        and c.distinct_sessions >= MIN_STAGE3_DISTINCT_SESSIONS
    )
    if not stage3_ok:
        failures.append(
            f"STAGE3_PAPER_SHADOW_INSUFFICIENT:roundtrips={c.closed_roundtrips}<{MIN_STAGE3_CLOSED_ROUNDTRIPS}"
            f"_or_sessions={c.distinct_sessions}<{MIN_STAGE3_DISTINCT_SESSIONS}"
        )

    hard_safety_ok = not any(f.startswith(("HARD_FIREWALL", "ADR0022", "PREWALL", "UNSANCTIONED")) for f in failures)
    only_stage3_pending = (
        hard_safety_ok and len(failures) == 1 and failures[0].startswith("STAGE3_PAPER_SHADOW_INSUFFICIENT:")
    )
    if not hard_safety_ok:
        stage_reached = "HARD_BLOCKED"
    elif not failures:
        stage_reached = "STAGE_4_PAPER_EXECUTION_APPROVED"
    elif only_stage3_pending:
        stage_reached = "STAGE_3_PAPER_SHADOW_ACCUMULATING"
    else:
        stage_reached = "STAGE_1_PROTECTIVE_OVERLAY_ONLY"

    return {
        "strategy_id": c.strategy_id,
        "approved_for_autonomous_alpha": len(failures) == 0,
        "hard_safety_verified": hard_safety_ok,
        "required_hlz_t_hurdle": req_t,
        "closed_roundtrips": c.closed_roundtrips,
        "distinct_sessions": c.distinct_sessions,
        "stage_reached": stage_reached,
        "failures": failures,
    }
