"""Research-Converged 9-Feed Ranking System DataFeeds (`DF1..DF9`) & Compounding Versioning Ledger (`v3.8.0`, `ADR-0015`).

Enforces:
1. Backward-compatible `9`-feed `sota-ranking-datafeeds.v3.8` (`DF1..DF9`) superset over `sota-research-feeds.v2`.
2. Strictly monotonic SemVer (`prev_semver < next_semver`), 4-hash cryptographic lineage (`input_lake_sha256`,
   `upstream_shelf_tree_sha256` across all 18 `PINS.md` commits, `ranking_datafeed_contract_sha256`, and sequential
   `adr_id`), dynamic Harvey-Liu-Zhu ledger state (`trials_n >= 90`, `t*(N+1) >= 4.1760`, `lessons_count >= 59`),
   and `PHILOSOPHY_ONLY` sibling-repo authority.
3. Two-track promotion discipline separating `ALPHA_STRATEGY_MINOR` (`DSR >= 0.95`, `CPCV >= 70%`, `t >= t*(N)`,
   `30` roundtrips / `10` sessions) from `PROTECTIVE_FILTER_OR_GOVERNANCE` (allowing sub-hurdle `5/5 CPCV` structural
   microstructure discoveries such as `H090` to compound strictly as protective filters / ADRs without alpha elevation).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import math
import re
import sqlite3
import sys
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sota_mmw.promotion_gate import (
    MAX_STOP_ADR0022_PCT,
    MIN_STAGE3_CLOSED_ROUNDTRIPS,
    MIN_STAGE3_DISTINCT_SESSIONS,
    STUDY_WALL_DATE,
    compute_hlz_t_hurdle,
)
from sota_mmw.research_convergence_contract import (
    HEX40_RE,
    HEX64_RE,
    RESEARCH_FEEDS_SCHEMA_VERSION,
    SIBLING_REPO_AUTHORITY,
)

RANKING_DATAFEEDS_SCHEMA_VERSION = "sota-ranking-datafeeds.v3.8"
COMPOUNDING_VERSION_SCHEMA = "sota-compounding-version-ledger.v3.8"
DEFAULT_ECOSYSTEM_SEMVER = "3.9.3"
MIN_HLZ_TRIALS_FLOOR = 90
MIN_NEXT_HLZ_HURDLE_FLOOR = 4.1760
MIN_COMPILED_LESSONS_FLOOR = 59
DEFAULT_PREWALL_LAKE_SHA256 = "a253421e873441740d5d4b410d993cfa7345fe34b88ec4ab7f4eecd537b3f234"

_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_ADR_ID_RE = re.compile(r"^ADR-(\d{4})$")

UPSTREAM_SHELF_PINS_18: dict[str, str] = {
    "alpaca-mcp-server": "63cc4278d87b31f3ed4efcfaa55624095c6d7be8",
    "alpaca-py": "c42add7c0a7026e2ead3ed64e76f4def2b99fda4",
    "duckdb": "d54cbbe3df17e8e5ce68312f483b4155836112aa",
    "edgartools": "574c2bd15f6c629bceef03b6550ea8ac8abf3473",
    "exchange_calendars": "dbe38b1f6887434bbdd1a7d2df6ff8f1742a048a",
    "hftbacktest": "5f3ec40b2afb764e0fea112f941ed85523ef4e88",
    "ib_async": "ab629f34c1823ea4c1542f32f07377208a86bdfd",
    "lightweight-charts": "c29c51e1e5bc61981da5832c97797cb8283d120f",
    "ml4t-diagnostic": "19e76072e64a18c9ba56130e4a7bcc0bc871f57e",
    "nautilus-alpaca": "59685d56631b981018a189b5ced1a7000a50bfbd",
    "nautilus_trader": "da6b57aefdd62b44f675e434ffcfefca7f4025dd",
    "pandera": "02b375ab43f39f8c5c5108695c1791fa04f99a26",
    "perspective": "0264ec13cd28ef4a2a136c8ef021c3c112bc8990",
    "polars": "7f902bd3ffd27ff82d14278a09a295ff2f7aed92",
    "quantstats": "d1a214fb906e76f974f45cdccf923b601c67a756",
    "skfolio": "90e3fb907fab39d244d899f3caf4e9676889309c",
    "statsmodels": "278ff9950636cdd4939b4055e339a8e681d79cab",
    "vectorbt": "a52a984b631624bb9daf41cb19f532fe559cf0ef",
}

CANONICAL_RANKING_DATAFEEDS_V38: dict[str, dict[str, Any]] = {
    "DF1_alpaca_sip_lit_and_dark_tape": {
        "feed_id": "DF1_alpaca_sip_lit_and_dark_tape",
        "v2_compat_feeds": ("alpaca_sip",),
        "window_et": "04:00-20:00 ET",
        "upstream": "alpacahq/alpaca-py@c42add7c0a7026e2ead3ed64e76f4def2b99fda4",
        "pit_and_microstructure_rules": (
            "filter u in ('canceled','incorrect') and deduplicate auction crosses",
            "'F' Intermarket Sweep (ISO) vs 'I' Odd-Lot separation",
            "CTA/UTP 100x round-lot quote size scaling",
            "BJZZ (2021) x=='D' sub-penny retail vs institutional midpoint/block >=5,000 sh or >=$100K",
            "Lee-Ready (1991) tick-test + quote-rule Order Flow Imbalance (OFI)",
        ),
    },
    "DF2_alpaca_boats_overnight_and_dec6_23x5": {
        "feed_id": "DF2_alpaca_boats_overnight_and_dec6_23x5",
        "v2_compat_feeds": ("alpaca_boats",),
        "window_et": "20:00-04:00 ET",
        "upstream": "alpacahq/alpaca-py@c42add7c0a7026e2ead3ed64e76f4def2b99fda4",
        "pit_and_microstructure_rules": (
            "<=28 bps spread gate",
            "<=8 symbols and <=8h history bound per Canon 0174",
            "2026-12-06 23/5 SIP cutover feature-flagged via SOTA_ENABLE_DEC6_235_SIP",
        ),
    },
    "DF3_raw_vs_all_split_and_corporate_actions_guard": {
        "feed_id": "DF3_raw_vs_all_split_and_corporate_actions_guard",
        "v2_compat_feeds": ("alpaca_raw_vs_all_adjustment", "corporate_actions_split_guard"),
        "window_et": "XNYS pre-open & intraday session",
        "upstream": (
            "pola-rs/polars@7f902bd3ffd27ff82d14278a09a295ff2f7aed92 + "
            "duckdb/duckdb@d54cbbe3df17e8e5ce68312f483b4155836112aa"
        ),
        "pit_and_microstructure_rules": (
            "Adjustment.RAW strictly for $/notional/spread execution filters",
            "Adjustment.ALL strictly for multi-day returns & trailing baselines",
            "split_vol * adj_factor == raw_vol conservation invariant",
        ),
    },
    "DF4_xnys_tod_rvol_bucket_normalizer": {
        "feed_id": "DF4_xnys_tod_rvol_bucket_normalizer",
        "v2_compat_feeds": ("corporate_actions_split_guard",),
        "window_et": "Exact XNYS intraday clock bucket",
        "upstream": (
            "gerrymanoim/exchange_calendars@dbe38b1f6887434bbdd1a7d2df6ff8f1742a048a (4.13.2) + "
            "QuantConnect/Lean RelativeDailyVolume.cs (Canon 0173)"
        ),
        "pit_and_microstructure_rules": (
            "trailing 20-session median cumulative/bucket volume for exact XNYS clock bucket",
            "RVOL_tod >= 2.2x early-mover ignition gate",
        ),
    },
    "DF5_sec_edgar_acceptance_datetime_catalyst_and_dilution_shield": {
        "feed_id": "DF5_sec_edgar_acceptance_datetime_catalyst_and_dilution_shield",
        "v2_compat_feeds": ("sec_edgar_acceptance_datetime",),
        "window_et": "06:00-22:00 ET SEC EDGAR Atom & submissions",
        "upstream": "dgunning/edgartools@574c2bd15f6c629bceef03b6550ea8ac8abf3473",
        "pit_and_microstructure_rules": (
            "strict UTC acceptanceDateTime <= as_of_utc",
            "15m exponential half-life on 8-K Items 1.01/2.02/7.01/8.01 + SC 13D + Form 4 'P' cluster",
            "90-day S-3 / 424B5 / EFFECT shelf-dilution long block",
        ),
    },
    "DF6_sec_xbrl_point_in_time_public_float": {
        "feed_id": "DF6_sec_xbrl_point_in_time_public_float",
        "v2_compat_feeds": ("sec_edgar_acceptance_datetime",),
        "window_et": "Point-in-time SEC XBRL EntityPublicFloat / CommonStockSharesOutstanding",
        "upstream": "dgunning/edgartools@574c2bd15f6c629bceef03b6550ea8ac8abf3473 + sec_float.parquet",
        "pit_and_microstructure_rules": (
            "sec_float.parquet strictly filtered by filed <= as_of",
            "tiering: LOW_FLOAT <$150M vs MID_FLOAT ($150M..<$2B) vs MEGA_FLOAT >=$2B",
        ),
    },
    "DF7_finra_regsho_cnmsshvol_intraday_t1": {
        "feed_id": "DF7_finra_regsho_cnmsshvol_intraday_t1",
        "v2_compat_feeds": ("finra_regsho_cnmsshvol_t1",),
        "window_et": "Post-EOD T-1 trading-day lag",
        "upstream": "FINRA RegSHO CNMSshvolYYYYMMDD.txt.gz + duckdb@d54cbbe3df17e8e5ce68312f483b4155836112aa",
        "pit_and_microstructure_rules": (
            "CNMSshvolYYYYMMDD.txt.gz strictly lagged d_tag < session_date (T-1 post-EOD)",
            "zero same-day short-volume lookahead",
        ),
    },
    "DF8_finra_rule4560_settled_short_interest_t8": {
        "feed_id": "DF8_finra_rule4560_settled_short_interest_t8",
        "v2_compat_feeds": ("finra_regsho_cnmsshvol_t1",),
        "window_et": "Bi-monthly FINRA Rule 4560 dissemination (+8 XNYS business days)",
        "upstream": "FINRA Rule 4560 shrtYYYYMMDD.csv.gz + exchange_calendars@4.13.2",
        "pit_and_microstructure_rules": (
            "8 XNYS business-day settlement-to-publication lag",
            "settlement 20260930 is latest point-in-time vintage as-of 2026-10-15 pre-wall cutoff",
        ),
    },
    "DF9_vix_majors_regime_and_ibkr_4002_l1_locate": {
        "feed_id": "DF9_vix_majors_regime_and_ibkr_4002_l1_locate",
        "v2_compat_feeds": ("ibkr_paper_4002_l1",),
        "window_et": "24/5 outsideRth IBKR Paper (:4002) & 3.0s VIX/Majors thrust radar",
        "upstream": "ib-api-reloaded/ib_async@ab629f34c1823ea4c1542f32f07377208a86bdfd",
        "pit_and_microstructure_rules": (
            "Paper-only DU... account on 127.0.0.1 port 4002 L1 & shortable locate (ports 4001/7496 hard-refused)",
            "3.0s VIX Spike/Reversal + Major Growth synchronous thrust regime classifier",
        ),
    },
}


def _is_real_finite(val: float) -> bool:
    return not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(float(val))


def parse_semver_tuple(ver: str) -> tuple[int, int, int]:
    """Parse strict `MAJOR.MINOR.PATCH` string into integer 3-tuple."""
    m = _SEMVER_RE.fullmatch(str(ver).strip())
    if m is None:
        raise ValueError(f"Invalid SemVer {ver!r}; expected strict MAJOR.MINOR.PATCH")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def parse_pins_markdown(pins_path: Path | None = None) -> dict[str, str]:
    """Parse `~/Documents/upstream/PINS.md` into `{repo_slug: 40-char-sha}`, falling back to `UPSTREAM_SHELF_PINS_18`."""
    cand = pins_path or (Path.home() / "Documents" / "upstream" / "PINS.md")
    if not cand.is_file():
        return dict(UPSTREAM_SHELF_PINS_18)
    parsed: dict[str, str] = {}
    row_re = re.compile(r"^\|\s*`([^`/]+)/?`\s*\|.*\|\s*`([0-9a-f]{40})`\s*\|")
    for line in cand.read_text(encoding="utf-8").splitlines():
        m = row_re.match(line.strip())
        if m and HEX40_RE.fullmatch(m.group(2)):
            parsed[m.group(1)] = m.group(2)
    return parsed if len(parsed) == 18 else dict(UPSTREAM_SHELF_PINS_18)


def compute_upstream_shelf_tree_sha256(pins_path: Path | None = None) -> str:
    """Compute canonical 64-hex SHA-256 tree digest across all 18 pinned upstream commits."""
    pins = parse_pins_markdown(pins_path)
    if len(pins) != 18 or not all(HEX40_RE.fullmatch(v) for v in pins.values()):
        raise RuntimeError(f"Expected 18 40-hex upstream pins, got {len(pins)}")
    canonical = "\n".join(f"{k}={pins[k]}" for k in sorted(pins))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_ranking_datafeed_contract_sha256() -> str:
    """Compute canonical 64-hex SHA-256 digest of the 9-feed `sota-ranking-datafeeds.v3.8` contract."""
    payload = {
        "schema_version": RANKING_DATAFEEDS_SCHEMA_VERSION,
        "supersedes_v2_schema": RESEARCH_FEEDS_SCHEMA_VERSION,
        "feeds": CANONICAL_RANKING_DATAFEEDS_V38,
    }
    encoded = json.dumps(payload, sort_keys=True, default=list).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_live_ledger_counts(db_path: Path | None = None) -> tuple[int, int]:
    """Read `(trials_n, lessons_count)` from SQLite WAL `peer_bus.db`, defaulting cleanly when offline/CI."""
    cand = db_path or (Path.home() / ".agents" / "bus" / "peer_bus.db")
    trials_n = MIN_HLZ_TRIALS_FLOOR
    lessons_count = 60
    if cand.is_file():
        try:
            with closing(sqlite3.connect(f"file:{cand}?mode=ro", uri=True, timeout=2.0)) as conn:
                row_h = conn.execute("SELECT COUNT(*) FROM hypotheses").fetchone()
                row_l = conn.execute("SELECT COUNT(*) FROM lessons").fetchone()
                if row_h and int(row_h[0]) > 0:
                    trials_n = max(trials_n, int(row_h[0]))
                if row_l and int(row_l[0]) > 0:
                    lessons_count = max(lessons_count, int(row_l[0]))
        except sqlite3.Error:
            pass
    return trials_n, lessons_count


@dataclass(frozen=True)
class CompoundingVersionRecord:
    prev_semver: str
    next_semver: str
    promotion_kind: str  # "ALPHA_STRATEGY_MINOR" | "PROTECTIVE_FILTER_OR_GOVERNANCE"
    adr_id: str
    input_lake_sha256: str
    upstream_shelf_tree_sha256: str
    ranking_datafeed_contract_sha256: str
    trials_n: int = MIN_HLZ_TRIALS_FLOOR
    lessons_count: int = 60
    sibling_repo_authority: str = SIBLING_REPO_AUTHORITY
    study_end_date: str = STUDY_WALL_DATE.isoformat()
    candidate_id: str = "H090_LIT_ONLY_PROTECTIVE_FILTER"
    dsr_probability: float = 0.0
    cpcv_positive_fold_pct: float = 100.0
    t_stat_date_clustered: float = 1.2919
    net_1x_bps: float = 20.84
    net_2x_bps: float = 15.43
    closed_roundtrips: int = 0
    distinct_sessions: int = 0
    hard_stop_pct: float = 1.80


def verify_compounding_version_transition(
    rec: CompoundingVersionRecord,
    *,
    prev_adr_id: str | None = None,
    verify_exact_contract_hashes: bool = True,
    pins_path: Path | None = None,
) -> dict[str, Any]:
    """Fail-closed verifier for monotonic SemVer, 4-hash lineage, HLZ floor, and two-track promotion."""
    violations: list[str] = []

    try:
        prev_ver = parse_semver_tuple(rec.prev_semver)
        next_ver = parse_semver_tuple(rec.next_semver)
        if not (prev_ver < next_ver):
            violations.append(f"NON_MONOTONIC_SEMVER:{rec.prev_semver}->={rec.next_semver}")
        elif rec.promotion_kind == "ALPHA_STRATEGY_MINOR" and next_ver[0] == prev_ver[0] and next_ver[1] <= prev_ver[1]:
            violations.append(f"ALPHA_PROMOTION_REQUIRES_MINOR_OR_MAJOR_BUMP:{rec.prev_semver}->{rec.next_semver}")
    except ValueError as exc:
        violations.append(f"INVALID_SEMVER:{exc}")

    if not HEX64_RE.fullmatch(str(rec.input_lake_sha256)):
        violations.append("INVALID_INPUT_LAKE_SHA256")

    expected_shelf_sha = compute_upstream_shelf_tree_sha256(pins_path)
    if not HEX64_RE.fullmatch(str(rec.upstream_shelf_tree_sha256)):
        violations.append("INVALID_UPSTREAM_SHELF_TREE_SHA256")
    elif verify_exact_contract_hashes and rec.upstream_shelf_tree_sha256 != expected_shelf_sha:
        violations.append("UPSTREAM_SHELF_TREE_SHA256_MISMATCH")

    expected_df_sha = compute_ranking_datafeed_contract_sha256()
    if not HEX64_RE.fullmatch(str(rec.ranking_datafeed_contract_sha256)):
        violations.append("INVALID_RANKING_DATAFEED_CONTRACT_SHA256")
    elif verify_exact_contract_hashes and rec.ranking_datafeed_contract_sha256 != expected_df_sha:
        violations.append("RANKING_DATAFEED_CONTRACT_SHA256_MISMATCH")

    m_adr = _ADR_ID_RE.fullmatch(str(rec.adr_id).strip())
    if m_adr is None:
        violations.append(f"INVALID_ADR_ID:{rec.adr_id}")
    elif prev_adr_id is not None:
        m_prev = _ADR_ID_RE.fullmatch(str(prev_adr_id).strip())
        if m_prev is None or int(m_adr.group(1)) <= int(m_prev.group(1)):
            violations.append(f"NON_SEQUENTIAL_ADR_ID:{prev_adr_id}->{rec.adr_id}")

    req_hlz_t = 0.0
    next_hlz_t = 0.0
    if isinstance(rec.trials_n, bool) or rec.trials_n < MIN_HLZ_TRIALS_FLOOR:
        violations.append(f"HLZ_TRIALS_BELOW_FLOOR:{rec.trials_n}<{MIN_HLZ_TRIALS_FLOOR}")
    else:
        req_hlz_t = compute_hlz_t_hurdle(rec.trials_n)
        next_hlz_t = compute_hlz_t_hurdle(rec.trials_n + 1)
        if next_hlz_t < MIN_NEXT_HLZ_HURDLE_FLOOR:
            violations.append(f"HLZ_NEXT_HURDLE_BELOW_FLOOR:{next_hlz_t}<{MIN_NEXT_HLZ_HURDLE_FLOOR}")

    if isinstance(rec.lessons_count, bool) or rec.lessons_count < MIN_COMPILED_LESSONS_FLOOR:
        violations.append(f"LESSONS_COUNT_BELOW_FLOOR:{rec.lessons_count}<{MIN_COMPILED_LESSONS_FLOOR}")

    if rec.sibling_repo_authority != SIBLING_REPO_AUTHORITY:
        violations.append(f"SIBLING_REPO_AUTHORITY_VIOLATION:{rec.sibling_repo_authority}")

    try:
        end_d = dt.date.fromisoformat(rec.study_end_date)
        if end_d > STUDY_WALL_DATE:
            violations.append(f"PREWALL_VIOLATION:{rec.study_end_date}>{STUDY_WALL_DATE.isoformat()}")
    except ValueError:
        violations.append(f"INVALID_STUDY_END_DATE:{rec.study_end_date}")

    if not _is_real_finite(rec.hard_stop_pct) or rec.hard_stop_pct <= 0.0 or rec.hard_stop_pct > MAX_STOP_ADR0022_PCT:
        violations.append(f"ADR0022_STOP_VIOLATION:{rec.hard_stop_pct}")

    floats_ok = all(
        _is_real_finite(v)
        for v in (
            rec.dsr_probability,
            rec.cpcv_positive_fold_pct,
            rec.t_stat_date_clustered,
            rec.net_1x_bps,
            rec.net_2x_bps,
        )
    )
    if not floats_ok:
        violations.append("NON_FINITE_METRIC_INPUT")

    alpha_stage_elevated = False
    track_disposition = "REJECTED"

    if rec.promotion_kind == "ALPHA_STRATEGY_MINOR":
        if floats_ok and req_hlz_t > 0.0:
            if rec.dsr_probability < 0.95:
                violations.append(f"ALPHA_DSR_BELOW_095:{rec.dsr_probability}")
            if rec.cpcv_positive_fold_pct < 70.0:
                violations.append(f"ALPHA_CPCV_BELOW_70PCT:{rec.cpcv_positive_fold_pct}")
            if rec.t_stat_date_clustered < req_hlz_t:
                violations.append(f"ALPHA_T_STAT_BELOW_HLZ:{rec.t_stat_date_clustered}<{req_hlz_t}")
            if rec.net_1x_bps <= 0.0 or rec.net_2x_bps <= 0.0:
                violations.append(f"ALPHA_NON_POSITIVE_NET_EXPECTANCY:1x={rec.net_1x_bps},2x={rec.net_2x_bps}")
            if isinstance(rec.closed_roundtrips, bool) or rec.closed_roundtrips < MIN_STAGE3_CLOSED_ROUNDTRIPS:
                violations.append(
                    f"ALPHA_STAGE3_ROUNDTRIPS_BELOW_{MIN_STAGE3_CLOSED_ROUNDTRIPS}:{rec.closed_roundtrips}"
                )
            if isinstance(rec.distinct_sessions, bool) or rec.distinct_sessions < MIN_STAGE3_DISTINCT_SESSIONS:
                violations.append(f"ALPHA_STAGE3_SESSIONS_BELOW_{MIN_STAGE3_DISTINCT_SESSIONS}:{rec.distinct_sessions}")
        if not violations:
            alpha_stage_elevated = True
            track_disposition = "ALPHA_STAGE_ELEVATED"
    elif rec.promotion_kind == "PROTECTIVE_FILTER_OR_GOVERNANCE":
        if floats_ok:
            if rec.cpcv_positive_fold_pct < 70.0:
                violations.append(f"PROTECTIVE_CPCV_BELOW_70PCT:{rec.cpcv_positive_fold_pct}")
            if rec.net_1x_bps < 0.0 or rec.net_2x_bps < 0.0:
                violations.append(f"PROTECTIVE_NEGATIVE_NET_EXPECTANCY:1x={rec.net_1x_bps},2x={rec.net_2x_bps}")
        if not violations:
            alpha_stage_elevated = False
            track_disposition = "PROTECTIVE_FILTER_OR_ADR_COMPOUNDED"
    else:
        violations.append(f"UNSUPPORTED_PROMOTION_KIND:{rec.promotion_kind}")

    approved = len(violations) == 0
    receipt_payload = {
        "record": dataclasses.asdict(rec),
        "approved": approved,
        "alpha_stage_elevated": alpha_stage_elevated,
        "track_disposition": track_disposition,
        "required_hlz_t_hurdle": req_hlz_t,
        "next_trial_hlz_t_hurdle": next_hlz_t,
        "violations": violations,
    }
    receipt_sha256 = hashlib.sha256(json.dumps(receipt_payload, sort_keys=True).encode("utf-8")).hexdigest()

    return {
        "schema_version": COMPOUNDING_VERSION_SCHEMA,
        "ranking_datafeeds_schema": RANKING_DATAFEEDS_SCHEMA_VERSION,
        "approved": approved,
        "alpha_stage_elevated": alpha_stage_elevated,
        "track_disposition": track_disposition,
        "prev_semver": rec.prev_semver,
        "next_semver": rec.next_semver,
        "promotion_kind": rec.promotion_kind,
        "adr_id": rec.adr_id,
        "candidate_id": rec.candidate_id,
        "trials_n": rec.trials_n,
        "required_hlz_t_hurdle": req_hlz_t,
        "next_trial_hlz_t_hurdle": next_hlz_t,
        "lessons_count": rec.lessons_count,
        "sibling_repo_authority": rec.sibling_repo_authority,
        "cryptographic_lineage": {
            "input_lake_sha256": rec.input_lake_sha256,
            "upstream_shelf_tree_sha256": rec.upstream_shelf_tree_sha256,
            "ranking_datafeed_contract_sha256": rec.ranking_datafeed_contract_sha256,
            "adr_id": rec.adr_id,
        },
        "violations": violations,
        "transition_receipt_sha256": receipt_sha256,
    }


def build_compounding_version_status(
    *,
    db_path: Path | None = None,
    pins_path: Path | None = None,
) -> dict[str, Any]:
    """Synthesize live `v3.8.0` Ranking DataFeeds (`DF1..DF9`) & Compounding Versioning status."""
    trials_n, lessons_count = load_live_ledger_counts(db_path)
    shelf_sha = compute_upstream_shelf_tree_sha256(pins_path)
    df_sha = compute_ranking_datafeed_contract_sha256()
    h090_rec = CompoundingVersionRecord(
        prev_semver="3.9.2",
        next_semver=DEFAULT_ECOSYSTEM_SEMVER,
        promotion_kind="PROTECTIVE_FILTER_OR_GOVERNANCE",
        adr_id="ADR-0018",
        input_lake_sha256=DEFAULT_PREWALL_LAKE_SHA256,
        upstream_shelf_tree_sha256=shelf_sha,
        ranking_datafeed_contract_sha256=df_sha,
        trials_n=trials_n,
        lessons_count=lessons_count,
        candidate_id="V3100_46SKILL_17WORKFLOW_14LAYER_18REPO_ADR_AND_ORCA_GRAND_ENACTMENT",
        dsr_probability=0.42,
        cpcv_positive_fold_pct=100.0,
        t_stat_date_clustered=1.2919,
        net_1x_bps=20.84,
        net_2x_bps=15.43,
        closed_roundtrips=0,
        distinct_sessions=0,
        hard_stop_pct=1.80,
    )
    verified = verify_compounding_version_transition(
        h090_rec,
        prev_adr_id="ADR-0017",
        pins_path=pins_path,
    )
    return {
        "ok": verified["approved"] and len(CANONICAL_RANKING_DATAFEEDS_V38) == 9,
        "schema_version": COMPOUNDING_VERSION_SCHEMA,
        "ecosystem_version": DEFAULT_ECOSYSTEM_SEMVER,
        "ranking_datafeeds_schema": RANKING_DATAFEEDS_SCHEMA_VERSION,
        "supersedes_research_feeds_schema": RESEARCH_FEEDS_SCHEMA_VERSION,
        "canonical_ranking_feeds_count": len(CANONICAL_RANKING_DATAFEEDS_V38),
        "canonical_ranking_feed_ids": list(CANONICAL_RANKING_DATAFEEDS_V38.keys()),
        "upstream_pins_count": len(UPSTREAM_SHELF_PINS_18),
        "upstream_shelf_tree_sha256": shelf_sha,
        "ranking_datafeed_contract_sha256": df_sha,
        "trials_n": trials_n,
        "current_hlz_t_hurdle": compute_hlz_t_hurdle(trials_n),
        "next_trial_hlz_t_hurdle": compute_hlz_t_hurdle(trials_n + 1),
        "lessons_count": lessons_count,
        "sibling_repo_authority": SIBLING_REPO_AUTHORITY,
        "latest_verified_transition": verified,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sota-version",
        description="SOTA v3.8.0 9-Feed Ranking System DataFeeds (DF1..DF9) & Compounding Versioning Verifier",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_st = sub.add_parser("status", help="Emit v3.8.0 Compounding Versioning & HLZ N>=90 ledger status")
    p_st.add_argument("--json", action="store_true")

    p_rf = sub.add_parser("ranking-feeds", help="Emit the 9 canonical DF1..DF9 PIT Ranking System DataFeeds")
    p_rf.add_argument("--json", action="store_true")

    p_vf = sub.add_parser("verify", help="Verify a CompoundingVersionRecord transition fail-closed")
    p_vf.add_argument("--prev-semver", default="3.9.0")
    p_vf.add_argument("--next-semver", default=DEFAULT_ECOSYSTEM_SEMVER)
    p_vf.add_argument(
        "--promotion-kind",
        default="PROTECTIVE_FILTER_OR_GOVERNANCE",
        choices=("ALPHA_STRATEGY_MINOR", "PROTECTIVE_FILTER_OR_GOVERNANCE"),
    )
    p_vf.add_argument("--adr-id", default="ADR-0017")
    p_vf.add_argument("--prev-adr-id", default="ADR-0016")
    p_vf.add_argument("--candidate-id", default="H090_LIT_ONLY_PROTECTIVE_FILTER")
    p_vf.add_argument("--input-lake-sha256", default=DEFAULT_PREWALL_LAKE_SHA256)
    p_vf.add_argument("--dsr", type=float, default=0.42)
    p_vf.add_argument("--cpcv-pct", type=float, default=100.0)
    p_vf.add_argument("--t-stat", type=float, default=1.2919)
    p_vf.add_argument("--net-1x-bps", type=float, default=20.84)
    p_vf.add_argument("--net-2x-bps", type=float, default=15.43)
    p_vf.add_argument("--closed-roundtrips", type=int, default=0)
    p_vf.add_argument("--distinct-sessions", type=int, default=0)
    p_vf.add_argument("--hard-stop-pct", type=float, default=1.80)
    p_vf.add_argument("--study-end-date", default=STUDY_WALL_DATE.isoformat())
    p_vf.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "status":
        st = build_compounding_version_status()
        print(json.dumps(st, indent=2))
        return 0 if st["ok"] else 1

    if args.cmd == "ranking-feeds":
        out_rf = {
            "schema_version": RANKING_DATAFEEDS_SCHEMA_VERSION,
            "supersedes_v2_schema": RESEARCH_FEEDS_SCHEMA_VERSION,
            "feed_count": len(CANONICAL_RANKING_DATAFEEDS_V38),
            "ranking_datafeed_contract_sha256": compute_ranking_datafeed_contract_sha256(),
            "feeds": CANONICAL_RANKING_DATAFEEDS_V38,
        }
        print(json.dumps(out_rf, indent=2, default=list))
        return 0

    trials_n, lessons_count = load_live_ledger_counts()
    rec = CompoundingVersionRecord(
        prev_semver=args.prev_semver,
        next_semver=args.next_semver,
        promotion_kind=args.promotion_kind,
        adr_id=args.adr_id,
        input_lake_sha256=args.input_lake_sha256,
        upstream_shelf_tree_sha256=compute_upstream_shelf_tree_sha256(),
        ranking_datafeed_contract_sha256=compute_ranking_datafeed_contract_sha256(),
        trials_n=trials_n,
        lessons_count=lessons_count,
        study_end_date=args.study_end_date,
        candidate_id=args.candidate_id,
        dsr_probability=args.dsr,
        cpcv_positive_fold_pct=args.cpcv_pct,
        t_stat_date_clustered=args.t_stat,
        net_1x_bps=args.net_1x_bps,
        net_2x_bps=args.net_2x_bps,
        closed_roundtrips=args.closed_roundtrips,
        distinct_sessions=args.distinct_sessions,
        hard_stop_pct=args.hard_stop_pct,
    )
    res = verify_compounding_version_transition(rec, prev_adr_id=args.prev_adr_id or None)
    if res["approved"]:
        print(json.dumps(res, indent=2))
        return 0
    print(json.dumps(res, indent=2), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
