# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA Schema-Typed `run_workflow`: RD-Agent(Q) Pre-Registration -> Falsifier -> Verifier Pipeline.

Orchestrates custom AGY subagents (`sota-rd-proposer`, `sota-falsifier`) with immutable SHA-256
pre-registration context via `_sota_kit.py` (`<= 2026-10-15` strict wall).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = args if "args" in globals() and isinstance(args, dict) else {}
repo_hint = str(cfg.get("repo") or "sota-mover-ranker")
peer_brief = kit.load_peer_brief(repo_hint)
log(peer_brief)

HYPOTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "hypothesis_id": {"type": "string"},
        "title": {"type": "string"},
        "spec_text": {"type": "string"},
        "pre_wall_verified": {"type": "boolean"},
        "max_stop_pct": {"type": "number"},
    },
    "required": ["hypothesis_id", "title", "spec_text", "pre_wall_verified", "max_stop_pct"],
}

FALSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "survived_red_team": {"type": "boolean"},
        "lookahead_audit": {"type": "string"},
        "cost_and_dilution_stress": {"type": "string"},
        "fatal_flaws": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["survived_red_team", "lookahead_audit", "cost_and_dilution_stress", "fatal_flaws"],
}

phase("1. RD-Agent(Q) Factor Proposal (Pre-Wall <= 2026-10-15)")

proposal = await agent(
    f"{peer_brief}\n\n"
    f"Search `~/.agents/bin/sota-bus search 'early mover'`, `~/Documents/upstream/PINS.md` (read-only), and query "
    f"`sota_get_research_feeds`, `sota_get_first_hand_incentives`, and `sota_get_converged_strategy_templates`. "
    f"Formulate one falsifiable ADR-0004 3-tier microstructure hypothesis (`sota_converged_strategy.template.json`) "
    f"for `~/Documents/{repo_hint}` strictly inside `<= 2026-10-15` with `max_stop_pct <= 2.00` (ADR-0022). "
    "Return structured JSON.",
    schema=HYPOTHESIS_SCHEMA,
    role="RD-Agent Factor Proposer",
    type_name="sota-rd-proposer",
)
log(f"Proposed `{proposal['hypothesis_id']}`: {proposal['title']}")

phase("2. Adversarial Microstructure, Dilution & Lookahead Red-Team")

falsifier = agent(
    f"{peer_brief}\n\n"
    "You are an adversarial Quantitative Microstructure, Dilution & Lookahead Skeptic. "
    "Reject any proposal that fails ADR-0004 3-tier convergence (64-hex input SHA-256 + 40-hex upstream SHAs + "
    "converged template), risks post-2026-10-15 data snooping, mixes Adjustment.RAW vs ALL across splits, violates "
    "SEC `acceptanceDateTime` (15m half-life + `424B*`/`S-3` dilution block) or FINRA `T-1` lag, ignores HLZ t*(N)/DSR, "
    "assumes zero spread/impact decay, or violates ADR-0022 (<=2.00% stop).",
    role="Adversarial Quant Falsifier",
    type_name="sota-falsifier",
)

verdict = await falsifier(f"Red-team this pre-wall hypothesis:\n{json.dumps(proposal)}", FALSIFICATION_SCHEMA)
log(f"Falsifier survived={verdict['survived_red_team']} flaws={verdict['fatal_flaws']}")

if not verdict["survived_red_team"] and verdict["fatal_flaws"]:
    phase("3. Single-Parameter Tightening & Second-Pass Falsification")
    revised = await agent(
        f"{peer_brief}\n\n"
        f"Resolve these fatal flaws without adding degrees of freedom:\nProposal: {json.dumps(proposal)}\nFlaws: {verdict['fatal_flaws']}",
        schema=HYPOTHESIS_SCHEMA,
        role="RD-Agent Hypothesis Refiner",
        type_name="sota-rd-proposer",
    )
    verdict = await falsifier(f"Re-audit revised proposal:\n{json.dumps(revised)}", FALSIFICATION_SCHEMA)
    proposal = revised

del falsifier

kit.record_workflow_run(
    repo=repo_hint,
    workflow_id="rd-agent-hypothesis-bus",
    done_summary=f"{proposal['hypothesis_id']} ({proposal['title']}): survived_red_team={verdict['survived_red_team']}",
    verified_by=f"lookahead={verdict['lookahead_audit'][:100]}; stress={verdict['cost_and_dilution_stress'][:100]}",
    open_risks="; ".join(verdict["fatal_flaws"][:3]) or "none",
    next_priority=f"Pre-register and execute {proposal['hypothesis_id']} on pre-wall lake <=2026-10-15"
    if verdict["survived_red_team"]
    else "Discard or redesign hypothesis in new trial ID",
)

output = {"proposal": proposal, "falsification": verdict}
print(output)
