# ruff: noqa: E402, F704, F821, PLE1142
"""AGY & CC-Lead SOTA `run_workflow` (`v3.8.0` #16): 9-Feed Ranking System DataFeeds (`DF1..DF9`), Architecture ADR & Compounding Versioning Gate.

Audits and enforces:
- `CANONICAL_RANKING_DATAFEEDS_V38` (`DF1..DF9` first-hand PIT Ranking System DataFeeds, backward-compatible superset of `sota-research-feeds.v2`).
- Strictly monotonic SemVer (`prev_semver < next_semver`), 4-hash cryptographic lineage (`input_lake_sha256`, `upstream_shelf_tree_sha256` across all 18 `PINS.md` commits, `ranking_datafeed_contract_sha256`, sequential `ADR-XXXX`), HLZ ledger state (`trials_n >= 90`, `t*(N+1) >= 4.1760`, `lessons_count >= 59`), and `PHILOSOPHY_ONLY` sibling-repo authority.
- Two-track promotion discipline (`ALPHA_STRATEGY_MINOR` vs `PROTECTIVE_FILTER_OR_GOVERNANCE`).
"""

import json
import sys
from pathlib import Path

WF_DIR = Path.home() / ".agents" / "workflows"
CWD_DIR = Path.cwd()
LOCAL_WF_DIR = (
    Path(__file__).resolve().parent
    if "__file__" in globals()
    else (CWD_DIR / "workflows" if (CWD_DIR / "workflows" / "_sota_kit.py").is_file() else WF_DIR)
)
REPO_SRC = LOCAL_WF_DIR.parent / "src"
CWD_SRC = CWD_DIR / "src"
HOME_MMW_SRC = Path.home() / "Documents" / "sota-multi-model-workflows" / "src"
for _cand_src in (REPO_SRC, CWD_SRC, HOME_MMW_SRC):
    if (_cand_src / "sota_mmw").is_dir() and str(_cand_src) not in sys.path:
        sys.path.insert(0, str(_cand_src))
        break
for _wf_cand in (LOCAL_WF_DIR, WF_DIR):
    if _wf_cand.is_dir() and str(_wf_cand) not in sys.path:
        sys.path.insert(0, str(_wf_cand))

import _sota_kit as kit

from sota_mmw.compounding_versioning import (
    CANONICAL_RANKING_DATAFEEDS_V38,
    DEFAULT_PREWALL_LAKE_SHA256,
    RANKING_DATAFEEDS_SCHEMA_VERSION,
    CompoundingVersionRecord,
    build_compounding_version_status,
    compute_ranking_datafeed_contract_sha256,
    compute_upstream_shelf_tree_sha256,
    load_live_ledger_counts,
    verify_compounding_version_transition,
)

cfg = kit.get_workflow_args(globals())
target_repo = str(cfg.get("repo") or "sota-multi-model-workflows")
prev_semver = str(cfg.get("prev_semver") or "3.7.0")
next_semver = str(cfg.get("next_semver") or "3.8.0")
raw_kind = str(cfg.get("promotion_kind") or "PROTECTIVE_FILTER_OR_GOVERNANCE")
promotion_kind = (
    raw_kind
    if raw_kind in ("ALPHA_STRATEGY_MINOR", "PROTECTIVE_FILTER_OR_GOVERNANCE")
    else "PROTECTIVE_FILTER_OR_GOVERNANCE"
)
adr_id = str(cfg.get("adr_id") or "ADR-0015")
prev_adr_id = str(cfg.get("prev_adr_id") or "ADR-0014")
candidate_id = str(cfg.get("candidate_id") or "H090_LIT_ONLY_PROTECTIVE_FILTER")
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))

peer_brief = kit.load_peer_brief(target_repo)
rc_context = kit.load_research_convergence_context()
rc_envelope = kit.verify_workflow_research_convergence("compounding-versioning-and-ranking-adr", repo=target_repo)
preflight = kit.run_preflight_summary(live_org=False)
trials_n, lessons_count = load_live_ledger_counts()

cand_metrics = cfg.get("candidate_metrics") or {}
record = CompoundingVersionRecord(
    prev_semver=prev_semver,
    next_semver=next_semver,
    promotion_kind=promotion_kind,
    adr_id=adr_id,
    input_lake_sha256=str(cand_metrics.get("input_lake_sha256") or DEFAULT_PREWALL_LAKE_SHA256),
    upstream_shelf_tree_sha256=compute_upstream_shelf_tree_sha256(),
    ranking_datafeed_contract_sha256=compute_ranking_datafeed_contract_sha256(),
    trials_n=trials_n,
    lessons_count=lessons_count,
    sibling_repo_authority="PHILOSOPHY_ONLY",
    study_end_date=str(cand_metrics.get("study_end_date") or "2026-10-15"),
    candidate_id=candidate_id,
    dsr_probability=float(cand_metrics.get("dsr_probability", 0.42)),
    cpcv_positive_fold_pct=float(cand_metrics.get("cpcv_positive_fold_pct", 100.0)),
    t_stat_date_clustered=float(cand_metrics.get("t_stat_date_clustered", 1.2919)),
    net_1x_bps=float(cand_metrics.get("net_1x_bps", 20.84)),
    net_2x_bps=float(cand_metrics.get("net_2x_bps", 15.43)),
    closed_roundtrips=int(cand_metrics.get("closed_roundtrips", 0)),
    distinct_sessions=int(cand_metrics.get("distinct_sessions", 0)),
    hard_stop_pct=float(cand_metrics.get("hard_stop_pct", 1.80)),
)
transition_verdict = verify_compounding_version_transition(record, prev_adr_id=prev_adr_id)

# Deterministically verify that attempting to promote sub-hurdle H090 as ALPHA_STRATEGY_MINOR fails closed
alpha_rejection_verified = False
if promotion_kind == "PROTECTIVE_FILTER_OR_GOVERNANCE" and record.t_stat_date_clustered < 4.1735:
    probe_alpha = verify_compounding_version_transition(
        CompoundingVersionRecord(
            prev_semver=prev_semver,
            next_semver=next_semver,
            promotion_kind="ALPHA_STRATEGY_MINOR",
            adr_id=adr_id,
            input_lake_sha256=record.input_lake_sha256,
            upstream_shelf_tree_sha256=record.upstream_shelf_tree_sha256,
            ranking_datafeed_contract_sha256=record.ranking_datafeed_contract_sha256,
            trials_n=trials_n,
            lessons_count=lessons_count,
            candidate_id=candidate_id,
            dsr_probability=record.dsr_probability,
            cpcv_positive_fold_pct=record.cpcv_positive_fold_pct,
            t_stat_date_clustered=record.t_stat_date_clustered,
            net_1x_bps=record.net_1x_bps,
            net_2x_bps=record.net_2x_bps,
            closed_roundtrips=record.closed_roundtrips,
            distinct_sessions=record.distinct_sessions,
            hard_stop_pct=record.hard_stop_pct,
        ),
        prev_adr_id=prev_adr_id,
    )
    alpha_rejection_verified = (not probe_alpha["approved"]) and (not probe_alpha["alpha_stage_elevated"])
else:
    alpha_rejection_verified = True

status_snapshot = build_compounding_version_status()
deterministic_audit = {
    "target_repo": target_repo,
    "ranking_datafeeds_schema": RANKING_DATAFEEDS_SCHEMA_VERSION,
    "legacy_compat_schema": rc_context.get("schema_version", "sota-research-feeds.v2"),
    "sibling_repo_authority": rc_context.get("sibling_repo_authority", "PHILOSOPHY_ONLY"),
    "canonical_ranking_feeds_count": len(CANONICAL_RANKING_DATAFEEDS_V38),
    "canonical_ranking_feed_ids": list(CANONICAL_RANKING_DATAFEEDS_V38.keys()),
    "research_convergence_envelope": rc_envelope,
    "status_snapshot": status_snapshot,
    "transition_verdict": transition_verdict,
    "two_track_subhurdle_alpha_rejection_verified": alpha_rejection_verified,
    "preflight": preflight,
}
log(f"{peer_brief}\n{json.dumps(deterministic_audit, indent=2, default=list)}")

if fast_deterministic_only:
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="compounding-versioning-and-ranking-adr-fast",
        done_summary=(
            f"v3.8.0 Ranking Feeds 9/9 + SemVer {prev_semver}->{next_semver} ({adr_id}) "
            f"approved={transition_verdict['approved']} track={transition_verdict['track_disposition']} "
            f"HLZ N={trials_n} t*(N+1)={transition_verdict['next_trial_hlz_t_hurdle']}"
        ),
        verified_by="compounding_versioning.py + verify_workflow_research_convergence + sota-doctor",
        open_risks="none" if (transition_verdict["approved"] and alpha_rejection_verified) else "version_gate_blocked",
        next_priority=f"Maintain two-track promotion discipline under HLZ N={trials_n}",
    )
    print(json.dumps(deterministic_audit, indent=2, default=list))
else:
    VERSION_AUDIT_SCHEMA = {
        "type": "object",
        "properties": {
            "passed": {"type": "boolean"},
            "evidence_grade": {"type": "string", "enum": ["E1", "E2", "E3", "E4"]},
            "findings": {"type": "array", "items": {"type": "string"}},
            "recommended_next_step": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": ["passed", "evidence_grade", "findings", "recommended_next_step", "summary"],
    }

    phase("Phase 1: Parallel 9-Feed Ranking System DataFeeds (DF1..DF9) & ADR Lineage Synthesis")

    recon = await parallel(
        [
            (
                "9-Feed PIT Ranking System DataFeeds (DF1..DF9) Primary-Source Synthesizer",
                "sota-deep-synthesizer",
                f"{peer_brief}\n\nDeterministic v3.8.0 Audit:\n{json.dumps(deterministic_audit, indent=2, default=list)}\n"
                "Verify all 9 Ranking System DataFeeds (`DF1..DF9` in `sota-ranking-datafeeds.v3.8`, backward-compatible "
                "with `sota-research-feeds.v2`) against `~/Documents/upstream/PINS.md` (`alpaca-py`, `polars`, `duckdb`, "
                "`exchange_calendars`, `edgartools`, `ib_async`) and `PHILOSOPHY_ONLY` sibling-repo rules.",
            ),
            (
                "Architecture ADR & 4-Hash Cryptographic Lineage Scout",
                "self",
                f"{peer_brief}\n\nDeterministic v3.8.0 Audit:\n{json.dumps(deterministic_audit, indent=2, default=list)}\n"
                "Verify monotonic SemVer (`prev_semver < next_semver`), sequential MADR 4.0 `ADR-XXXX` indexing, and "
                "all 4 cryptographic lineage anchors (`input_lake_sha256`, `upstream_shelf_tree_sha256`, "
                "`ranking_datafeed_contract_sha256`, `adr_id`). Never print secrets or account IDs.",
            ),
        ],
        lambda item: agent(item[2], schema=VERSION_AUDIT_SCHEMA, role=item[0], type_name=item[1]),
    )

    phase("Phase 2: Adversarial Two-Track Promotion, Lookahead & HLZ Multiplicity Falsification")

    falsifier_out = await agent(
        f"{peer_brief}\n\nTransition Verdict:\n{json.dumps(transition_verdict, indent=2)}\n"
        f"Phase 1 Recon:\n{json.dumps(recon, indent=2)}\n"
        "Attempt to falsify: (1) any sub-hurdle structural discovery (`t < t*(N)`) sneaking into `ALPHA_STRATEGY_MINOR`, "
        "(2) point-in-time lag leakage across `DF5` (`acceptanceDateTime`), `DF6` (`filed <= as_of`), `DF7` (`T-1`), "
        "or `DF8` (`+8 XNYS` business days -> `20260930` as-of `2026-10-15`), and (3) `ADR-0022 > 2.00%` stop breaches.",
        schema=VERSION_AUDIT_SCHEMA,
        role=f"Compounding Version Falsifier ({target_repo})",
        type_name="sota-falsifier",
    )

    phase("Phase 3: Deterministic ADR Catalog, Merge Gate & Test Suite Sign-Off")

    verifier_out = await agent(
        f"{peer_brief}\n\nTarget Repo: `{target_repo}`\n"
        f"Falsifier Output:\n{json.dumps(falsifier_out, indent=2)}\n"
        "Run deterministic repo gates (`ruff`, `ty`, `pytest`, `architecture_catalog.py --check`, `merge_gate.py`, "
        "`gitleaks`) and confirm 0 leaks.",
        schema=VERSION_AUDIT_SCHEMA,
        role=f"Compounding Version Code Verifier ({target_repo})",
        type_name="sota-code-verifier",
    )

    final_report = {
        "deterministic_audit": deterministic_audit,
        "ranking_feeds_scout": recon[0],
        "adr_lineage_scout": recon[1],
        "falsifier": falsifier_out,
        "verifier": verifier_out,
    }
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="compounding-versioning-and-ranking-adr",
        done_summary=(
            f"v3.8.0 {prev_semver}->{next_semver} ({adr_id}) "
            f"approved={transition_verdict['approved']} verifier={verifier_out['passed']}"
        ),
        verified_by=f"sota-falsifier({falsifier_out['evidence_grade']}) + sota-code-verifier({verifier_out['evidence_grade']})",
        open_risks="; ".join(list(falsifier_out["findings"]) + list(verifier_out["findings"]))[:240] or "none",
        next_priority=verifier_out["recommended_next_step"][:200],
    )
    print(json.dumps(final_report, indent=2, default=list))
