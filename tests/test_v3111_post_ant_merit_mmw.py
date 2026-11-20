"""Tests for `v3.11.1` Post-ANT Grand Merit Harness & whole-market lossless consolidation (`ADR-0036`)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from sota_mmw.merit_promotion_harness import (
    POST_ANT_CONCENTRATED_SOTA_STRATEGIES,
    POST_ANT_ERA_ID,
    POST_ANT_QUARANTINED_STRATEGIES,
    MeritStrategyEvidence,
    build_grand_merit_harness_manifest,
    evaluate_merit_ladder,
    evaluate_post_ant_symbol_merit_admission,
)


def test_post_ant_quarantine_blocks_variants_and_zero_roundtrip_live_canary_denied() -> None:
    mf = build_grand_merit_harness_manifest()
    assert mf["era"] == POST_ANT_ERA_ID
    assert mf["post_ant_consolidation_adr"] == "ADR-0036"
    assert mf["ecosystem_version"] == "3.11.1"
    assert set(mf["post_ant_concentrated_sota_strategies"]) == POST_ANT_CONCENTRATED_SOTA_STRATEGIES
    assert set(mf["post_ant_quarantined_strategies"]) == POST_ANT_QUARANTINED_STRATEGIES

    # Family variant quarantine blocked even with full-auto graduation metrics!
    blocked = evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="POST_VIX_REVERSAL_VARIANT_X",
            study_end_date="2026-10-15",
            max_stop_pct=1.60,
            sim_engine_verified=True,
            prewall_net_1x_bps=25.0,
            prewall_net_2x_bps=18.0,
            closed_roundtrips=50,
            distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION", "PAPER_P2_ALPACA_BALANCED_RANKER"),
            eb_expectancy_r=0.40,
            profit_factor=2.10,
            realized_slippage_bps=1.0,
        )
    )
    assert blocked["live_8798_allowed"] is False
    assert blocked["merit_tier"] == "QUARANTINED_ADR0064_BLOCKED"

    # Zero paper roundtrips NEVER grants live canary for ANY strategy (incl. legacy MEGA_CAP_NEAR_LOSSLESS_ORB)!
    for sid_check in ("BJZZ_SUBPENNY_INST_DARK_SWEEP", "MEGA_CAP_NEAR_LOSSLESS_ORB"):
        zero_rt = evaluate_merit_ladder(
            MeritStrategyEvidence(
                strategy_id=sid_check,
                study_end_date="2026-10-15",
                max_stop_pct=1.50,
                sim_engine_verified=True,
                prewall_net_1x_bps=21.0,
                prewall_net_2x_bps=14.0,
                closed_roundtrips=0,
            )
        )
        assert zero_rt["live_8798_allowed"] is False
        assert zero_rt["merit_tier"] == "PAPER_P3_AGGRESSIVE_CRUCIBLE"

    # Mixed accounts (1 P1 + 14 P3) MUST NOT satisfy proven P1 roundtrips for live canary!
    mixed_p1_p3 = evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="BJZZ_SUBPENNY_INST_DARK_SWEEP",
            study_end_date="2026-10-15",
            max_stop_pct=1.50,
            sim_engine_verified=True,
            prewall_net_1x_bps=21.0,
            prewall_net_2x_bps=14.0,
            closed_roundtrips=15,
            p1_closed_roundtrips=1,
            distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION", "PAPER_P3_ALPACA_AGGRESSIVE_LAB"),
            eb_expectancy_r=0.18,
        )
    )
    assert mixed_p1_p3["live_8798_allowed"] is False

    # Malformed proof (inf closed_roundtrips, NaN breaches, empty account, string "false" flags) HARD REJECTED!
    for bad_ev in (
        MeritStrategyEvidence(
            strategy_id="BJZZ_SUBPENNY_INST_DARK_SWEEP",
            study_end_date="2026-10-15",
            max_stop_pct=1.50,
            sim_engine_verified=True,
            prewall_net_1x_bps=21.0,
            prewall_net_2x_bps=14.0,
            closed_roundtrips=float("inf"),  # type: ignore[arg-type]
            distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION", "PAPER_P2_ALPACA_BALANCED_RANKER"),
            eb_expectancy_r=0.30,
            profit_factor=1.80,
            realized_slippage_bps=1.0,
        ),
        MeritStrategyEvidence(
            strategy_id="BJZZ_SUBPENNY_INST_DARK_SWEEP",
            study_end_date="2026-10-15",
            max_stop_pct=1.50,
            sim_engine_verified="false",  # type: ignore[arg-type]
            lossless_foundation_verified="false",  # type: ignore[arg-type]
            prewall_net_1x_bps=21.0,
            prewall_net_2x_bps=14.0,
            closed_roundtrips=35,
            distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION", ""),
            eb_expectancy_r=0.30,
            profit_factor=1.80,
            realized_slippage_bps=1.0,
            adr0022_breaches=float("nan"),  # type: ignore[arg-type]
        ),
    ):
        rej = evaluate_merit_ladder(bad_ev)
        assert rej["live_8798_allowed"] is False
        assert rej["merit_tier"] == "HARD_REJECTED_SAFETY_OR_PREWALL"

    # Proven P1 paper roundtrips (>=15, EB>=0.12, explicit lossless_foundation_verified=True) earns 10% live canary
    proven = evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="BJZZ_SUBPENNY_INST_DARK_SWEEP",
            study_end_date="2026-10-15",
            max_stop_pct=1.50,
            sim_engine_verified=True,
            prewall_net_1x_bps=21.0,
            prewall_net_2x_bps=14.0,
            closed_roundtrips=18,
            p1_closed_roundtrips=18,
            distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION",),
            eb_expectancy_r=0.16,
            lossless_foundation_verified=True,
        )
    )
    assert proven["merit_tier"] == "STAGE5_LOSSLESS_FOUNDATION_CANARY_10PCT"
    assert proven["live_8798_allowed"] is True

    # Pass-3 Findings 1, 2 & 7:
    # - Omitting p1_closed_roundtrips on mixed accounts MUST NOT unlock 1.00x full-auto live!
    # - Omitting lossless_foundation_verified or realized_slippage_bps MUST fail closed!
    # - Empty strategy_id or Noise-VWAP > 0.50% stop MUST be hard-rejected!
    mixed_full_omit = evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="BJZZ_SUBPENNY_INST_DARK_SWEEP",
            study_end_date="2026-10-15",
            max_stop_pct=1.50,
            sim_engine_verified=True,
            prewall_net_1x_bps=21.0,
            prewall_net_2x_bps=14.0,
            closed_roundtrips=36,
            distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION", "PAPER_P3_ALPACA_AGGRESSIVE_LAB"),
            eb_expectancy_r=0.30,
            profit_factor=1.60,
            realized_slippage_bps=1.5,
            lossless_foundation_verified=True,
        )
    )
    assert mixed_full_omit["live_8798_allowed"] is False

    omit_proof = evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="BJZZ_SUBPENNY_INST_DARK_SWEEP",
            study_end_date="2026-10-15",
            max_stop_pct=1.50,
            sim_engine_verified=True,
            prewall_net_1x_bps=21.0,
            prewall_net_2x_bps=14.0,
            closed_roundtrips=36,
            p1_closed_roundtrips=20,
            distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION", "PAPER_P2_ALPACA_BALANCED_RANKER"),
            eb_expectancy_r=0.30,
            profit_factor=1.60,
        )
    )
    assert omit_proof["live_8798_allowed"] is False

    empty_sid = evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="   ",
            study_end_date="2026-10-15",
            max_stop_pct=1.00,
            sim_engine_verified=True,
            prewall_net_1x_bps=20.0,
            prewall_net_2x_bps=12.0,
            lossless_foundation_verified=True,
        )
    )
    assert empty_sid["live_8798_allowed"] is False and empty_sid["merit_tier"] == "HARD_REJECTED_SAFETY_OR_PREWALL"

    vwap_stop_breach = evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="ZARATTINI_2025_NOISE_VWAP",
            study_end_date="2026-10-15",
            max_stop_pct=1.00,
            sim_engine_verified=True,
            prewall_net_1x_bps=20.0,
            prewall_net_2x_bps=12.0,
            lossless_foundation_verified=True,
        )
    )
    assert vwap_stop_breach["live_8798_allowed"] is False
    assert vwap_stop_breach["merit_tier"] == "HARD_REJECTED_SAFETY_OR_PREWALL"

    # Pass-4 Additional P1: 30 total with all 30 on P1 proves 0 closures on P3 -> MUST NOT grant 1.00x multi-account live!
    all_p1_multi_label = evaluate_merit_ladder(
        MeritStrategyEvidence(
            strategy_id="BJZZ_SUBPENNY_INST_DARK_SWEEP",
            study_end_date="2026-10-15",
            max_stop_pct=1.50,
            sim_engine_verified=True,
            prewall_net_1x_bps=21.0,
            prewall_net_2x_bps=14.0,
            closed_roundtrips=30,
            p1_closed_roundtrips=30,
            distinct_paper_accounts=("PAPER_P1_ALPACA_LOSSLESS_FOUNDATION", "PAPER_P3_ALPACA_AGGRESSIVE_LAB"),
            eb_expectancy_r=0.30,
            profit_factor=1.60,
            realized_slippage_bps=1.5,
            lossless_foundation_verified=True,
        )
    )
    assert all_p1_multi_label["merit_tier"] != "STAGE5_LOSSLESS_LIVE_FULL_AUTO"
    assert all_p1_multi_label["live_notional_scale"] < 1.00


def test_post_ant_symbol_agnostic_whole_market_admission_failclosed_sec_and_pillars() -> None:
    t1 = evaluate_post_ant_symbol_merit_admission(
        symbol="MU",
        strategy_id="BJZZ_SUBPENNY_INST_DARK_SWEEP",
        merit_score=74.5,
        df_pillars_manifested=5,
        spread_bps=6.2,
        sec_dilution_clean=True,
    )
    assert t1["admitted"] is True
    assert t1["merit_tier"] == "MERIT_TIER_1_CORE"
    assert "PAPER_P1_ALPACA_LOSSLESS_FOUNDATION" in t1["assigned_paper_lanes"]
    assert "PAPER_P4_IBKR_INSTITUTIONAL_4002" in t1["assigned_paper_lanes"]
    assert t1["take_profit_cap_enabled"] is False
    assert t1["standalone_alpha_claim"] is False

    # Per-strategy ADR-0064 contract enforcement: H090 at 30 bps in RTH or OVERNIGHT_BOATS rejected!
    h090_wide = evaluate_post_ant_symbol_merit_admission(
        symbol="NVDA",
        strategy_id="H090_TIGHT_SPREAD_HIGH_OFI_PASSIVE_BID",
        merit_score=65.0,
        df_pillars_manifested=5,
        spread_bps=30.0,
        sec_dilution_clean=True,
        max_stop_pct=1.25,
        session_mode="RTH_CORE",
    )
    assert h090_wide["admitted"] is False
    assert any("STRATEGY_SPREAD_EXCEEDS_CONTRACT" in r for r in h090_wide["rejection_reasons"])

    h090_overnight = evaluate_post_ant_symbol_merit_admission(
        symbol="NVDA",
        strategy_id="H090_TIGHT_SPREAD_HIGH_OFI_PASSIVE_BID",
        merit_score=75.0,
        df_pillars_manifested=5,
        spread_bps=5.0,
        sec_dilution_clean=True,
        max_stop_pct=1.25,
        session_mode="OVERNIGHT_BOATS",
    )
    assert h090_overnight["admitted"] is False
    assert any("STRATEGY_SESSION_NOT_ALLOWED" in r for r in h090_overnight["rejection_reasons"])

    # Omitted sec_dilution_clean defaults fail-closed; impossible pillars > 6 rejected
    bad = evaluate_post_ant_symbol_merit_admission(
        symbol="NVDA",
        strategy_id="POST_VIX_REVERSAL_V9",
        merit_score=80.0,
        df_pillars_manifested=8,
        spread_bps=4.0,
    )
    assert bad["admitted"] is False
    assert any("QUARANTINED_ADR0064" in r for r in bad["rejection_reasons"])
    assert "SEC_90D_DILUTION_UNVERIFIED_OR_BLOCKED" in bad["rejection_reasons"]
    assert any("INVALID_DF_PILLARS_COUNT" in r for r in bad["rejection_reasons"])
