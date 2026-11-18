"""Master End-to-End SOTA Native Workflow (`run_workflow` Engine — 5-Phase Unified Pipeline).

Unifies MCP tool retrieval (`agy-sota-core`, `sota-peer-bus`, `sota-mover-ranker-stdio`, `alpaca-sota-watchlists`),
progressive-disclosure skills, specialist subagents (`sota-deep-synthesizer`, `sota-rd-proposer`, `sota-falsifier`,
`sota-code-verifier`), and automatic peer-bus handover into one native Antigravity workflow.

Pass `Args={"goal": "...", "repo": "optional-repo-name", "mode": "research|engineering|quant-trading"}`.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = kit.get_workflow_args(globals())
goal = str(cfg.get("goal") or "Audit active workspace health, verify SOTA gates, and identify highest-EV next step.")
ws0 = kit.get_primary_workspace(globals())
repo = str(cfg.get("repo") or (Path(ws0).name if ws0 else ""))
mode = str(cfg.get("mode") or "quant-trading")

# Phase 0: Deterministic Python Self-Bootstrap (Peer Bus + Research-Convergence + sota-doctor + sota-org-doctor)
peer_brief = kit.load_peer_brief(repo)
preflight = kit.run_preflight_summary(live_org=False)
doctor_line = f"[v3.3.0 preflight: {json.dumps(preflight)}]"

bootstrap_header = f"{doctor_line}\n{peer_brief}"
log(bootstrap_header)  # noqa: F821

RECON_SCHEMA = {
    "type": "object",
    "properties": {
        "upstream_and_mcp_facts": {"type": "array", "items": {"type": "string"}},
        "skills_activated": {"type": "array", "items": {"type": "string"}},
        "peer_lease_constraints": {"type": "string"},
        "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
    },
    "required": [
        "upstream_and_mcp_facts",
        "skills_activated",
        "peer_lease_constraints",
        "evidence_grade",
    ],
}

EXEC_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "artifacts_or_files_touched": {"type": "array", "items": {"type": "string"}},
        "metrics_or_outputs": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "artifacts_or_files_touched", "metrics_or_outputs"],
}

VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FALSIFIED_OR_BLOCKED"]},
        "evidence_grade": {"type": "string", "enum": ["E0", "E1", "E2", "E3", "E4"]},
        "confirmed_issues": {"type": "array", "items": {"type": "string"}},
        "gate_receipts": {"type": "array", "items": {"type": "string"}},
        "next_priority": {"type": "string"},
    },
    "required": [
        "verdict",
        "evidence_grade",
        "confirmed_issues",
        "gate_receipts",
        "next_priority",
    ],
}

phase("Phase 1: Parallel MCP, Skill & Upstream Shelf Reconnaissance")  # noqa: F821

recon_pair = await parallel(  # noqa: F821
    [
        (
            "Upstream Shelf & AST Reconnaissance",
            "sota-deep-synthesizer",
            f"{bootstrap_header}\n\nGoal: {goal} | Mode: {mode} | Repo: {repo or 'workspace'}\n"
            "Query `~/.agents/bin/sota-core` (`sota_shelf_search` / `sota_symbol_lookup`) and `~/.agents/bin/sota-bus search` first. "
            "Verify ADR-0004 3-tier convergence (64-hex input SHA-256, 18 `~/Documents/upstream/PINS.md` 40-hex SHAs, and "
            "`sota_converged_strategy.template.json`), relevant SOTA skills, and active peer leases.",
        ),
        (
            "Domain, Market & MCP Telemetry Scout",
            "self",
            f"{bootstrap_header}\n\nGoal: {goal} | Mode: {mode} | Repo: {repo or 'workspace'}\n"
            "Load relevant skills (e.g. `sota-quant-research-protocol`, `early-mover-compounding-goal`, `sota-tdd-superpowers`) "
            "and query applicable MCP tools (`sota_get_research_feeds`, `sota_get_first_hand_incentives`, "
            "`sota_get_converged_strategy_templates` on `sota-mover-ranker-stdio`, plus `agy-sota-core`, `sota-peer-bus`, "
            "and `alpaca-sota-watchlists`). Never print keys, account IDs, or balances.",
        ),
    ],
    lambda item: agent(  # noqa: F821
        item[2],
        schema=RECON_SCHEMA,
        role=item[0],
        type_name=item[1],
    ),
)

phase("Phase 2: Scoped Execution & Synthesis")  # noqa: F821

exec_out = await agent(  # noqa: F821
    f"{bootstrap_header}\n\nGoal: {goal}\n"
    f"Upstream/AST Recon: {json.dumps(recon_pair[0])}\n"
    f"Domain/MCP Recon: {json.dumps(recon_pair[1])}\n\n"
    "Execute the minimal, upstream-first work required by the goal while enforcing ADR-0004 3-tier convergence "
    "(`sota_get_converged_strategy_templates` / `sota_converged_strategy.template.json`), active peer leases, "
    "temporal pre-walls (`<= 2026-10-15`), and the hard paper-only/ADR-0022 (`<= 2.00%` stop)/secret firewall.",
    schema=EXEC_SCHEMA,
    role="SOTA Primary Executor",
    type_name="self",
)
log(json.dumps(exec_out, indent=2))  # noqa: F821

phase("Phase 3: Parallel Adversarial Falsification & Two-Pass Code/Security Gate")  # noqa: F821

audits = await parallel(  # noqa: F821
    [
        (
            "Adversarial Quant & Premortem Falsifier",
            "sota-falsifier",
            f"{bootstrap_header}\n\nGoal: {goal}\nExecution Output: {json.dumps(exec_out)}\n"
            "Audit ADR-0004 3-tier convergence and 7-feed `sota-research-feeds.v2` PIT discipline (`SIP`/`BOATS` + "
            "`Adjustment.RAW` vs `ALL` + SEC `acceptanceDateTime` 15m half-life & `424B*`/`S-3` dilution block + FINRA `T-1`), "
            "multiple-testing HLZ t-hurdle / CPCV / DSR >= 0.95 compliance, and 2x square-root impact survival.",
        ),
        (
            "Deterministic Lint, Type, Test & Secret Verifier",
            "sota-code-verifier",
            f"{bootstrap_header}\n\nGoal: {goal}\nTouched files: {json.dumps(exec_out['artifacts_or_files_touched'])}\n"
            "Run applicable deterministic gates (`ruff`, `ty`/`pyright`, `pytest`, `merge_gate.py`, `gitleaks`) "
            "and perform a two-pass self-refuting P0-P3 check.",
        ),
    ],
    lambda item: agent(  # noqa: F821
        item[2],
        schema=VERIFY_SCHEMA,
        role=item[0],
        type_name=item[1],
    ),
)

final_payload = {
    "preflight": doctor_line,
    "recon": recon_pair,
    "execution": exec_out,
    "falsifier_audit": audits[0],
    "verifier_gate": audits[1],
}

kit.record_workflow_run(
    repo=repo or "sota-master-workflow",
    workflow_id="master-sota-harness",
    done_summary=f"[{audits[1]['verdict']}/{audits[1]['evidence_grade']}] {exec_out['summary'][:240]}",
    verified_by="; ".join((audits[1]["gate_receipts"] + audits[0]["gate_receipts"])[:4]) or "falsifier+verifier",
    open_risks="; ".join((audits[0]["confirmed_issues"] + audits[1]["confirmed_issues"])[:3]) or "none",
    next_priority=audits[1]["next_priority"] or audits[0]["next_priority"],
)

out_text = json.dumps(final_payload, indent=2)
log(out_text)  # noqa: F821
print(out_text)
