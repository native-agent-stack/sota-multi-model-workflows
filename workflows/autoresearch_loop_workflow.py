"""SOTA Autoresearch & Adversarial Falsification Pipeline (`run_workflow` Engine — Self-Bootstrapping).

Grounded in `karpathy/autoresearch`, `wanshuiyin/ARIS`, and `microsoft/RD-Agent(Q)`.
Pass `Args={"repo": "sota-mover-ranker", "hypothesis_id": "H_AUTO_01", "hypothesis": "..."}`.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = kit.get_workflow_args(globals())
repo = str(cfg.get("repo") or "sota-mover-ranker")
hyp_id = str(cfg.get("hypothesis_id") or "H_AUTO_CANDIDATE")
hyp_prompt = str(
    cfg.get("hypothesis") or "Identify the next highest-lift pre-wall microstructure hypothesis from prior lessons."
)
peer_brief = kit.load_peer_brief(repo)
rc_ctx = kit.load_research_convergence_context()
rc_envelope = kit.verify_workflow_research_convergence("autoresearch-loop", repo=repo)

SPEC_SCHEMA = {
    "type": "object",
    "properties": {
        "hypothesis_id": {"type": "string"},
        "title": {"type": "string"},
        "mechanism_and_causal_dag": {"type": "string"},
        "exact_spec": {"type": "string"},
        "required_hlz_t_hurdle": {"type": "number"},
    },
    "required": [
        "hypothesis_id",
        "title",
        "mechanism_and_causal_dag",
        "exact_spec",
        "required_hlz_t_hurdle",
    ],
}

RUN_SCHEMA = {
    "type": "object",
    "properties": {
        "events_count": {"type": "integer"},
        "distinct_dates": {"type": "integer"},
        "t_stat_clustered": {"type": "number"},
        "dsr": {"type": "number"},
        "net_return_1x_bps": {"type": "number"},
        "net_return_2x_bps": {"type": "number"},
        "summary": {"type": "string"},
    },
    "required": [
        "events_count",
        "distinct_dates",
        "t_stat_clustered",
        "dsr",
        "net_return_1x_bps",
        "net_return_2x_bps",
        "summary",
    ],
}

FALSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["KEEP", "DISCARD"]},
        "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
        "red_team_findings": {"type": "array", "items": {"type": "string"}},
        "next_iteration": {"type": "string"},
    },
    "required": ["verdict", "evidence_grade", "red_team_findings", "next_iteration"],
}

log(f"{peer_brief}\n[Explicit RC: {rc_ctx['schema_version']} / PHILOSOPHY_ONLY]")  # noqa: F821
phase("Stage 1: Prior Search & Immutable SHA-256 Pre-Registration")  # noqa: F821

spec = await agent(  # noqa: F821
    f"{peer_brief}\n\nTarget repo: ~/Documents/{repo} | Candidate ID: {hyp_id}\nGoal: {hyp_prompt}\n"
    '1. Search `~/.agents/bin/sota-bus search "' + hyp_id + '"` and check UPSTREAM.md + `sota_get_research_feeds` + '
    "`sota_get_first_hand_incentives` + `sota_get_converged_strategy_templates`.\n"
    "2. Pre-register the immutable ADR-0004 3-tier spec (`sota_converged_strategy.template.json` + 64-hex input SHA-256 "
    "+ 40-hex upstream SHAs) via `~/.agents/bin/sota-bus preregister` BEFORE reading check/OOS data.\n"
    "3. Respect pre-wall boundaries (strictly <=2026-10-15 across all SOTA research & compounding repos).",
    schema=SPEC_SCHEMA,
    role="RD-Agent Pre-Registration Architect",
    type_name="sota-rd-proposer",
)
log(f"--- Stage 1 Locked Spec ---\n{json.dumps(spec, indent=2)}")  # noqa: F821

phase("Stage 2: Pre-Wall Empirical Execution")  # noqa: F821

emp_result = await agent(  # noqa: F821
    f"{peer_brief}\n\nExecute ONLY the pre-wall / fit+check empirical evaluation in ~/Documents/{repo} for:\n"
    f"{json.dumps(spec, indent=2)}\n"
    "Enforce 7-feed `sota-research-feeds.v2` PIT rules (`RAW` vs `ALL`, SEC `acceptanceDateTime` 15m decay + `424B*`/`S-3` "
    "dilution block, FINRA `T-1`) and record outcome via `~/.agents/bin/sota-bus outcome` so failed trials increment N. "
    "Never touch live broker routes or print credentials/account IDs.",
    schema=RUN_SCHEMA,
    role="Empirical Study Runner",
    type_name="sota-rd-proposer",
)
log(f"--- Stage 2 Empirical Metrics ---\n{json.dumps(emp_result, indent=2)}")  # noqa: F821

phase("Stage 3: Adversarial Falsification & Keep/Discard Verdict")  # noqa: F821

falsification = await agent(  # noqa: F821
    f"{peer_brief}\n\nAudit this candidate in ~/Documents/{repo}:\n"
    f"Locked Spec: {json.dumps(spec)}\nEmpirical Output: {json.dumps(emp_result)}\n\n"
    "Challenge ADR-0004 3-tier convergence, RAW/ALL split contamination, SEC `acceptanceDateTime` & FINRA `T-1` "
    "lookahead leakage, outlier-day concentration, 2x square-root impact survival, and HLZ t-hurdle / DSR >= 0.95.",
    schema=FALSIFY_SCHEMA,
    role="Adversarial Study Falsifier",
    type_name="sota-falsifier",
)

kit.record_workflow_run(
    repo=repo,
    workflow_id="autoresearch",
    done_summary=f"{spec['hypothesis_id']}: {falsification['verdict']} ({falsification['evidence_grade']}) "
    f"t={emp_result['t_stat_clustered']} 2x={emp_result['net_return_2x_bps']}bps",
    verified_by=f"events={emp_result['events_count']} dates={emp_result['distinct_dates']} DSR={emp_result['dsr']}",
    open_risks="; ".join(falsification["red_team_findings"][:2]) or "none",
    next_priority=falsification["next_iteration"],
)

out_text = json.dumps({"spec": spec, "metrics": emp_result, "adjudication": falsification}, indent=2)
log(out_text)  # noqa: F821
print(out_text)
