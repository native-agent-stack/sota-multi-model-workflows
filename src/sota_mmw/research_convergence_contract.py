"""Deterministic Research-Convergence, 7-Feed PIT DataFeed, Strategy Template & Engine Source Contract (`v3.6.0`).

Enforces 3-tier `ADR-0004` / `ADR-0011` / `ADR-0013` convergence across all 14 self-bootstrapping `run_workflow`
scripts, live/offline `sota-research-feeds.v2` Trading Lane DataFeed APIs (`:8787`, `:8799`, `:4002`), the 4
canonical strategy templates + closed-bar Pine v6 (`sota_converged_strategy.template.json`), the 8 trading engine
source repositories, 18 40-char SHA pinned upstream clones, and 3-surface Dual-Workstation execution
(`Mac M5 Max` `~/Documents/*`, `Noesis Win32` `C:/sota-workstation/*`, and `Noesis-Carbon WSL2` `~/sota-workstation/*`).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any

RESEARCH_FEEDS_SCHEMA_VERSION = "sota-research-feeds.v2"
STRATEGY_TEMPLATES_SCHEMA_VERSION = "sota-converged-strategy-templates.v1"
CONVERGENCE_ENVELOPE_SCHEMA_VERSION = "sota-workflow-research-convergence.v3.6"
SIBLING_REPO_AUTHORITY = "PHILOSOPHY_ONLY"
DUAL_WORKSTATION_HOSTS: tuple[str, str] = ("portable_mac_m5_max", "stationary_noesis_win32_wsl")
DUAL_WORKSTATION_SURFACES: tuple[str, str, str] = (
    "portable_mac_m5_max",
    "stationary_noesis_win32",
    "stationary_noesis_wsl_carbon",
)
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

CANONICAL_TRADING_LANE_DATAFEED_APIS: dict[str, dict[str, Any]] = {
    "ranker_research_feeds": {
        "endpoint": "GET http://127.0.0.1:8787/api/research_feeds",
        "mcp_tool": "sota_get_research_feeds",
        "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION,
        "role": "7 canonical PIT DataFeeds (SIP, BOATS + 2026-12-06 23/5 flag, RAW/ALL, SEC 15m, FINRA T-1, Splits, IBKR :4002)",
    },
    "ranker_first_hand_incentives": {
        "endpoint": "GET http://127.0.0.1:8787/api/first_hand_incentives",
        "mcp_tool": "sota_get_first_hand_incentives",
        "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION,
        "role": "Direct SEC EDGAR 8-K (1.01/2.02/7.01/8.01) & SC 13D Atom catalysts + 424B*/S-3 dilution blocks",
    },
    "ranker_strategy_templates": {
        "endpoint": "GET http://127.0.0.1:8787/api/strategy_templates",
        "mcp_tool": "sota_get_converged_strategy_templates",
        "schema_version": STRATEGY_TEMPLATES_SCHEMA_VERSION,
        "role": "4 canonical converged strategy templates validated under ADR-0022 <=2.00% stop & <=2026-10-15 pre-wall",
    },
    "ranker_research_convergence": {
        "endpoint": "GET http://127.0.0.1:8787/api/research_convergence",
        "mcp_tool": "sota_get_strategy_backtest_manifest",
        "schema_version": "sota-research-convergence.v1",
        "role": "Unified ADR-0004 3-tier SHA provenance, 16-tool MCP parity & PHILOSOPHY_ONLY sibling-repo audit",
    },
    "trail_guardian_24x5": {
        "endpoint": "GET http://127.0.0.1:8799/api/status + POST /api/tv-webhook",
        "mcp_tool": "sota_arm_live_protection_watch",
        "schema_version": "sota-trail-guardian.v1",
        "role": "Sub-50ms dual-tranche dynamic trailing guardian & non-repainting closed-bar Pine v6 webhook relay",
    },
    "astrolabe_ibkr_paper_4002": {
        "endpoint": "tcp://127.0.0.1:4002 (ib_ids.PAPER_PORT; live ports 4001/7496 hard-refused)",
        "mcp_tool": "sota_get_paper_auto_and_protection_status",
        "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION,
        "role": "NautilusTrader v2.0.0rc9 + ib_async Paper lane (2,700/300 msg/min reserve, Rule 612 25..75 bps StopLimit collars)",
    },
}

CANONICAL_STRATEGY_TEMPLATES_MATRIX: dict[str, dict[str, Any]] = {
    "PRE_TRAVEL_EARLY_IGNITION": {
        "archetype": "PRE_TRAVEL_EARLY_IGNITION",
        "default_initial_stop_pct": 1.80,
        "max_hard_stop_pct": MAX_HARD_STOP_PCT,
        "intrabar_tie_rule": "ADVERSE_STOP_FIRST",
        "queue_model": "hftbacktest::RiskAdverseQueueModel (100x CTA/UTP round-lot scaling)",
        "required_feeds": (
            "alpaca_sip",
            "alpaca_boats",
            "alpaca_raw_vs_all_adjustment",
            "corporate_actions_split_guard",
        ),
        "target_lanes": ("ALPACA_PAPER", "IBKR_PAPER"),
    },
    "FIRST_HAND_SEC_EPISODIC_PIVOT": {
        "archetype": "FIRST_HAND_SEC_EPISODIC_PIVOT",
        "default_initial_stop_pct": 1.90,
        "max_hard_stop_pct": MAX_HARD_STOP_PCT,
        "intrabar_tie_rule": "ADVERSE_STOP_FIRST",
        "queue_model": "hftbacktest::RiskAdverseQueueModel (100x CTA/UTP round-lot scaling)",
        "required_feeds": (
            "sec_edgar_acceptance_datetime",
            "alpaca_sip",
            "alpaca_raw_vs_all_adjustment",
            "corporate_actions_split_guard",
        ),
        "target_lanes": ("ALPACA_PAPER", "IBKR_PAPER"),
    },
    "MEGA_CAP_NEAR_LOSSLESS_ORB": {
        "archetype": "MEGA_CAP_NEAR_LOSSLESS_ORB",
        "default_initial_stop_pct": 0.85,
        "scratch_shield_bps": (6.0, 14.0),
        "instant_breakeven_arm_bps": (5.0, 10.0),
        "max_hard_stop_pct": MAX_HARD_STOP_PCT,
        "intrabar_tie_rule": "ADVERSE_STOP_FIRST",
        "queue_model": "hftbacktest::RiskAdverseQueueModel (100x CTA/UTP round-lot scaling)",
        "required_feeds": ("alpaca_sip", "alpaca_raw_vs_all_adjustment", "ibkr_paper_4002_l1"),
        "target_lanes": ("ALPACA_PAPER", "IBKR_PAPER"),
    },
    "CLIMAX_VWAP_MEAN_REVERSION": {
        "archetype": "CLIMAX_VWAP_MEAN_REVERSION",
        "default_initial_stop_pct": 1.75,
        "max_hard_stop_pct": MAX_HARD_STOP_PCT,
        "intrabar_tie_rule": "ADVERSE_STOP_FIRST",
        "queue_model": "hftbacktest::RiskAdverseQueueModel (100x CTA/UTP round-lot scaling)",
        "required_feeds": (
            "alpaca_sip",
            "finra_regsho_cnmsshvol_t1",
            "sec_edgar_acceptance_datetime",
            "ibkr_paper_4002_l1",
        ),
        "target_lanes": ("ALPACA_PAPER", "IBKR_PAPER"),
    },
}

DEFAULT_PINNED_ENGINE_COMMITS: dict[str, str] = {
    "nautilus_trader": "da6b57aefdd62b44f675e434ffcfefca7f4025dd",
    "hftbacktest": "5f3ec40b2afb764e0fea112f941ed85523ef4e88",
    "alpaca-py": "c42add7c0a7026e2ead3ed64e76f4def2b99fda4",
    "edgartools": "574c2bd15f6c629bceef03b6550ea8ac8abf3473",
    "ml4t-diagnostic": "19e76072e64a18c9ba56130e4a7bcc0bc871f57e",
}

CANONICAL_TRADING_ENGINE_SOURCES: dict[str, dict[str, Any]] = {
    "meridian": {
        "stage": "Stage_1_Simulation_And_Queue_Parity",
        "primary_upstreams": ("nautechsystems/nautilus_trader@v2.0.0rc9", "nkaz001/hftbacktest"),
        "convergence_module": "meridian/research_convergence.py",
        "adr_anchor": "ADR 0057..0059",
    },
    "canon": {
        "stage": "Stage_2A_Deterministic_Causal_Snapshots",
        "primary_upstreams": ("golang/mod@v0.43.0 (sumdb/dirhash)", "duckdb/duckdb", "pola-rs/polars"),
        "convergence_module": "docs/adr/0176-ecosystem-research-convergence-and-orca-coop.md",
        "adr_anchor": "ADR 0169..0176",
    },
    "tsl": {
        "stage": "Stage_2B_PIT_Strategy_Lab_And_Engine_Host",
        "primary_upstreams": ("alpacahq/alpaca-py@v0.45.0", "nautechsystems/nautilus_trader@v2.0.0rc9"),
        "convergence_module": "hosts/engine/host.py",
        "adr_anchor": "ADR-0018..0019",
    },
    "trading-sota": {
        "stage": "Stage_2C_Converged_Strategy_Archive_And_Host",
        "primary_upstreams": ("alpacahq/alpaca-py@v0.45.0", "nautechsystems/nautilus_trader@v2.0.0rc9"),
        "convergence_module": "hosts/engine/host.py",
        "adr_anchor": "ADR-0011..0012",
    },
    "sota-mover-ranker": {
        "stage": "Stage_3A_Whole_Market_SIP_BOATS_And_Alpaca_200RPM_Paper",
        "primary_upstreams": ("alpacahq/alpaca-py@v0.45.0", "dgunning/edgartools@v6.2.0", "pola-rs/polars"),
        "convergence_module": "server.py",
        "adr_anchor": "ADR-0007..0011",
    },
    "astrolabe": {
        "stage": "Stage_3B_IBKR_Port_4002_Nautilus_Paper_Lane",
        "primary_upstreams": (
            "nautechsystems/nautilus_trader@v2.0.0rc9",
            "ib-api-reloaded/ib_async@v2.1.0",
            "nkaz001/hftbacktest",
        ),
        "convergence_module": "astrolabe/research_convergence.py",
        "adr_anchor": "ADR-0004..0005",
    },
    "sota-compounding-lab": {
        "stage": "Stage_4_Five_Stage_HLZ_CPCV_DSR_And_Empirical_Bayes",
        "primary_upstreams": ("skfolio/skfolio", "ml4t/diagnostic@0.2.0", "golang/mod (dirhash)"),
        "convergence_module": "src/sota_compounding/strategy_template.py",
        "adr_anchor": "ADR-0006..0007",
    },
    "sota-dynamic-trail-c": {
        "stage": "Stage_5_24x5_Sub50ms_Dual_Tranche_Trailing_Guardian",
        "primary_upstreams": ("alpacahq/alpaca-py@v0.45.0", "gerrymanoim/exchange_calendars@4.13.2"),
        "convergence_module": "src/sota_trail",
        "adr_anchor": "ADR-0006..0009",
    },
}

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
        "window_et": "Post-EOD T-1 lag (CNMSshvol) + FINRA Rule 4560 T+8 short-interest",
        "lag_trading_days": 1,
        "upstream": "FINRA RegSHO CNMSshvol + duckdb@v2.0.0",
        "pit_rule": "Strict T-1 trading-day lag (d_tag < target_tag) and T+8 short-interest lag; zero same-day lookahead",
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
        "pit_rule": "Paper-only DU... account on 127.0.0.1:4002 (2,700/300 msg/min reserve); live ports 4001/7496 100% hard-refused",
        "features": (
            "outside_rth_protective_stops",
            "l1_bid_ask_spread_gate",
            "short_locate_availability_probe",
        ),
    },
}


def resolve_ecosystem_repo_dir(
    repo_name: str,
    *,
    home: Path | None = None,
    win_root: Path | None = None,
) -> Path:
    """Resolve an ecosystem repo directory seamlessly across Mac (`~/Documents`), Noesis Win32 (`C:/sota-workstation`), and WSL2 (`~/sota-workstation`)."""
    h = home if home is not None else Path.home()
    w = (
        win_root
        if win_root is not None
        else (Path("C:/sota-workstation") if os.name == "nt" else Path("/mnt/c/sota-workstation"))
    )
    folder = "dot-github" if repo_name == ".github" else repo_name

    candidates: list[Path] = []
    if repo_name == "canon":
        candidates.append(h / "canon")
    candidates.extend(
        [
            h / "Documents" / folder,
            h / "sota-workstation" / folder,
            w / folder,
        ]
    )
    if repo_name == "dsh-plugin-landscape":
        candidates.insert(1, h / "Documents" / "dsh")
    if repo_name == ".github":
        candidates.insert(1, h / "Documents" / ".github")

    for cand in candidates:
        try:
            if cand.is_dir():
                return cand
        except OSError:
            continue
    return candidates[0]


def detect_workstation_surface(*, home: Path | None = None, win_root: Path | None = None) -> str:
    """Identify which of the 3 canonical workstation surfaces is executing."""
    h = home if home is not None else Path.home()
    w = win_root if win_root is not None else Path("C:/sota-workstation")
    if os.name == "nt" or (os.name == "nt" and w.is_dir()):
        return "stationary_noesis_win32"
    if (h / "sota-workstation").is_dir():
        return "stationary_noesis_wsl_carbon"
    return "portable_mac_m5_max"


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


def build_workflow_research_convergence_envelope(
    *,
    workflow_id: str,
    repo: str = "sota-multi-model-workflows",
    archetype: str = "PRE_TRAVEL_EARLY_IGNITION",
    upstream_pins: dict[str, str] | None = None,
    home: Path | None = None,
    win_root: Path | None = None,
) -> dict[str, Any]:
    """Build and deterministically verify the full-stack Research-Convergence envelope for any workflow."""
    selected_archetype = archetype if archetype in CANONICAL_STRATEGY_ARCHETYPES else CANONICAL_STRATEGY_ARCHETYPES[0]
    tpl_spec = CANONICAL_STRATEGY_TEMPLATES_MATRIX[selected_archetype]
    pins = dict(upstream_pins) if upstream_pins else dict(DEFAULT_PINNED_ENGINE_COMMITS)
    surface = detect_workstation_surface(home=home, win_root=win_root)

    compounding_dir = resolve_ecosystem_repo_dir("sota-compounding-lab", home=home, win_root=win_root)
    trading_sota_dir = resolve_ecosystem_repo_dir("trading-sota", home=home, win_root=win_root)
    tsl_dir = resolve_ecosystem_repo_dir("tsl", home=home, win_root=win_root)
    meridian_dir = resolve_ecosystem_repo_dir("meridian", home=home, win_root=win_root)
    astrolabe_dir = resolve_ecosystem_repo_dir("astrolabe", home=home, win_root=win_root)
    shelf_lock_dir = resolve_ecosystem_repo_dir("sota-upstream-shelf-lock", home=home, win_root=win_root)

    template_artifacts = {
        "sota-compounding-lab/templates/sota_converged_strategy.template.json": (
            compounding_dir / "templates" / "sota_converged_strategy.template.json"
        ).is_file(),
        "sota-compounding-lab/templates/sota_pine_v6_nonrepainting.template.pine": (
            compounding_dir / "templates" / "sota_pine_v6_nonrepainting.template.pine"
        ).is_file(),
        "trading-sota/strategies/_template/manifest.json": (
            trading_sota_dir / "strategies" / "_template" / "manifest.json"
        ).is_file(),
        "tsl/strategies/_template/manifest.json": (tsl_dir / "strategies" / "_template" / "manifest.json").is_file(),
        "meridian/meridian/research_convergence.py": (meridian_dir / "meridian" / "research_convergence.py").is_file(),
        "astrolabe/astrolabe/research_convergence.py": (
            astrolabe_dir / "astrolabe" / "research_convergence.py"
        ).is_file(),
        "sota-upstream-shelf-lock/PINS": (shelf_lock_dir / "pyproject.toml").is_file(),
    }

    engine_repos_present = {
        eng_repo: resolve_ecosystem_repo_dir(eng_repo, home=home, win_root=win_root).is_dir()
        for eng_repo in CANONICAL_TRADING_ENGINE_SOURCES
    }

    canonical_seed = {
        "schema": CONVERGENCE_ENVELOPE_SCHEMA_VERSION,
        "workflow_id": workflow_id,
        "repo": repo or "sota-multi-model-workflows",
        "archetype": selected_archetype,
        "feeds": sorted(CANONICAL_DATAFEEDS.keys()),
        "datafeed_apis": sorted(CANONICAL_TRADING_LANE_DATAFEED_APIS.keys()),
        "engine_sources": sorted(CANONICAL_TRADING_ENGINE_SOURCES.keys()),
        "pre_wall": PRE_WALL_MAX_DATE,
        "sibling_authority": SIBLING_REPO_AUTHORITY,
    }
    envelope_sha256 = hashlib.sha256(json.dumps(canonical_seed, sort_keys=True).encode("utf-8")).hexdigest()
    default_stop = float(tpl_spec["default_initial_stop_pct"])
    violations = verify_research_convergence_claim(
        input_sha256=envelope_sha256,
        upstream_pins=pins,
        study_max_date=PRE_WALL_MAX_DATE,
        hard_stop_pct=default_stop,
        evidence_grade="E4",
    )

    return {
        "schema_version": CONVERGENCE_ENVELOPE_SCHEMA_VERSION,
        "workflow_id": workflow_id,
        "target_repo": repo or "sota-multi-model-workflows",
        "workstation_surface": surface,
        "envelope_input_sha256": envelope_sha256,
        "valid": len(violations) == 0,
        "violations": violations,
        "sibling_repo_authority": SIBLING_REPO_AUTHORITY,
        "pre_wall_max_date": PRE_WALL_MAX_DATE,
        "max_hard_stop_pct": MAX_HARD_STOP_PCT,
        "selected_strategy_template": tpl_spec,
        "datafeed_api_count": len(CANONICAL_TRADING_LANE_DATAFEED_APIS),
        "datafeed_apis": list(CANONICAL_TRADING_LANE_DATAFEED_APIS.keys()),
        "canonical_feed_count": len(CANONICAL_DATAFEEDS),
        "strategy_archetypes": list(CANONICAL_STRATEGY_ARCHETYPES),
        "template_artifacts": template_artifacts,
        "trading_engine_source_count": len(CANONICAL_TRADING_ENGINE_SOURCES),
        "trading_engine_repos_present": engine_repos_present,
        "pinned_engine_commits": pins,
    }
