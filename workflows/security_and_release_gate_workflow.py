"""SOTA Two-Pass Security, Type, Merge-Gate & Self-Refuting Review (`run_workflow` Engine — Self-Bootstrapping).

Grounded in `meridian` gate, `alibaba/open-code-review`, `trailofbits/skills`, and `cloudflare/security-audit-skill`.
Pass `Args={"repo_path": "/abs/path/to/repo"}` (defaults to Cwd / primary workspace).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = kit.get_workflow_args(globals())
repo_path = str(cfg.get("repo_path") or kit.get_primary_workspace(globals(), "."))
repo_name = Path(repo_path).resolve().name
peer_brief = kit.load_peer_brief(repo_name)

GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "gate_verdict": {"type": "string", "enum": ["PASS", "BLOCK"]},
        "deterministic_checks_summary": {"type": "string"},
        "confirmed_p0_p2_defects": {"type": "array", "items": {"type": "string"}},
        "recorded_minor_p3": {"type": "array", "items": {"type": "string"}},
        "refuted_false_positives": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "gate_verdict",
        "deterministic_checks_summary",
        "confirmed_p0_p2_defects",
        "recorded_minor_p3",
        "refuted_false_positives",
    ],
}

log(peer_brief)  # noqa: F821
phase("Phase 1: Parallel Deterministic Gate + Security/Firewall Scan")  # noqa: F821

checks = await parallel(  # noqa: F821
    [
        (
            "Deterministic Lint, Type & Test Gate",
            f"{peer_brief}\n\nIn `{repo_path}`, run available deterministic checks (`scripts/merge_gate.py`, "
            "`~/.local/bin/ruff check .`, `~/.local/bin/ty check` or `~/.local/bin/pyright`, and `pytest -q`) "
            "without modifying files. Return exact exit codes and concise failure lines only.",
        ),
        (
            "Firewall, Secret & Public-Tree Leak Auditor",
            f"{peer_brief}\n\nIn `{repo_path}`, inspect `git status -s` and `git diff` plus run `gitleaks detect --no-git --source .` "
            "if available. Verify zero live-broker imports/ports (`4001`, `7496`, `.claude/bin/live`), zero `PA...`/`DU...` IDs, "
            "zero raw keys, and zero hardcoded `/Users/<user>/` paths in tracked files.",
        ),
    ],
    lambda item: agent(  # noqa: F821
        item[1],
        schema={"type": "string"},
        role=item[0],
        type_name="sota-code-verifier",
    ),
)

phase("Phase 2: Stateful Two-Pass P0-P3 Defect Enumeration & Self-Refutation")  # noqa: F821

reviewer = agent(  # noqa: F821
    "You are a stateful two-pass Meridian/Open-Code-Review auditor. Cite exact file paths and line numbers.",
    role="Two-Pass Defect & Refutation Auditor",
    type_name="sota-code-verifier",
)

pass1_candidates = await reviewer(
    f"{peer_brief}\n\nTarget `{repo_path}`.\nGate report:\n{checks[0]}\n\nSecurity report:\n{checks[1]}\n\n"
    "Inspect `git diff` and enumerate all candidate P0-P3 defects (race conditions, clock/timezone leaks, "
    "None/type hazards, lookahead, boundary violations).",
    schema={"type": "string"},
)

final_report = await reviewer(
    "Now execute Pass 2 (Self-Refutation): check every candidate defect from Pass 1 against actual callers, "
    "invariants, and tests. Drop refuted items into `refuted_false_positives` and set `gate_verdict` to BLOCK "
    "if any deterministic gate failed or any P0-P2 defect remains confirmed/undecided.",
    schema=GATE_SCHEMA,
)
del reviewer

kit.record_workflow_run(
    repo=repo_name,
    workflow_id="security-release-gate",
    done_summary=f"Release Gate {final_report['gate_verdict']}: {final_report['deterministic_checks_summary'][:180]}",
    verified_by=f"P0-P2={len(final_report['confirmed_p0_p2_defects'])}, P3={len(final_report['recorded_minor_p3'])}, Refuted={len(final_report['refuted_false_positives'])}",
    open_risks="; ".join(final_report["confirmed_p0_p2_defects"][:2]) or "none",
    next_priority="Fix P0-P2 blockers" if final_report["confirmed_p0_p2_defects"] else "Ready for cited PR/merge",
)

out_text = json.dumps(final_report, indent=2)
log(out_text)  # noqa: F821
print(out_text)
