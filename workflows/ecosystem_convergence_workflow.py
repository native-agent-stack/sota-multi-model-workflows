# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA `run_workflow` (`v3.0.0`): Full-Ecosystem, 22-Repo Org Firewall & Harness Probe Convergence."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = kit.get_workflow_args(globals())
live_org = bool(cfg.get("live_org", False))
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))

phase("Phase 1: Deterministic Local, Org & Harness Probe Execution")

peer_brief = kit.load_peer_brief("native-agent-stack")
preflight = kit.run_preflight_summary(live_org=live_org)
research_convergence = kit.load_research_convergence_context()

docs = Path.home() / "Documents"
probe_cmds = [
    ("agy-sota-harness-13-probes", ["python3", str(docs / "agy-sota-harness" / "harness" / "run_probes.py")]),
    ("dsh-sota-harness-10-probes", ["node", str(docs / "dsh-sota-harness" / "harness" / "run.mjs")]),
    (
        "umbrella-v3-lock",
        ["python3", str(docs / "native-agent-stack" / "scripts" / "architecture_catalog.py"), "--check"],
    ),
]

probe_receipts: list[dict[str, object]] = []
for name, cmd in probe_cmds:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=False)
    tail = (proc.stdout or proc.stderr or "").strip().splitlines()[-2:]
    probe_receipts.append({"probe": name, "ok": proc.returncode == 0, "tail": " | ".join(tail)})

all_deterministic_ok = (
    isinstance(preflight.get("sota_doctor"), dict)
    and preflight["sota_doctor"].get("status") == "PASS"
    and isinstance(preflight.get("sota_org_doctor"), dict)
    and preflight["sota_org_doctor"].get("status") == "PASS"
    and all(bool(r["ok"]) for r in probe_receipts)
)

deterministic_bundle = {
    "all_deterministic_ok": all_deterministic_ok,
    "preflight": preflight,
    "research_convergence": {
        "schema_version": research_convergence["schema_version"],
        "convergence_adr": research_convergence["convergence_adr"],
        "sibling_repo_authority": research_convergence.get("sibling_repo_authority", "PHILOSOPHY_ONLY"),
        "feed_count": research_convergence["feed_count"],
        "upstream_pin_count": research_convergence["upstream_pin_count"],
    },
    "probe_receipts": probe_receipts,
}
log(json.dumps(deterministic_bundle, indent=2))

if fast_deterministic_only:
    kit.record_workflow_run(
        repo="native-agent-stack",
        workflow_id="ecosystem-convergence-fast",
        done_summary=f"Deterministic v3.0.0 Convergence PASS={all_deterministic_ok} (live_org={live_org})",
        verified_by="; ".join(f"{r['probe']}:{r['ok']}" for r in probe_receipts),
        next_priority="Ready for autonomous research & paper compounding",
    )
    print(json.dumps(deterministic_bundle, indent=2))
else:
    SUMMARY_SCHEMA = {
        "type": "object",
        "properties": {
            "all_converged": {"type": "boolean"},
            "executive_brief": {"type": "string"},
            "open_risks": {"type": "array", "items": {"type": "string"}},
            "next_actions": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["all_converged", "executive_brief", "open_risks", "next_actions"],
    }

    phase("Phase 2: Parallel Verifier & Deep-Synthesizer Adjudication")

    reviews = await parallel(
        [
            (
                "Harness & Org Firewall Verifier",
                "sota-code-verifier",
                f"{peer_brief}\n\nDeterministic Receipts:\n{json.dumps(deterministic_bundle, indent=2)}\n"
                "Verify zero regressions across L0-L12 probes, MADR 4.0 catalogs, ADR-0004 3-tier SHA provenance, "
                "`sota-research-feeds.v2` 7-feed PIT contract (`PHILOSOPHY_ONLY` sibling-repo authority), "
                "`Mac M5 Max <-> Noesis` parity, and the 22-repo Three-Tier org boundary.",
            ),
            (
                "Cross-Peer Continuity & Next-Move Synthesizer",
                "sota-deep-synthesizer",
                f"{peer_brief}\n\nDeterministic Receipts:\n{json.dumps(deterministic_bundle, indent=2)}\n"
                "Synthesize convergence posture and recommend the highest-EV next pre-wall or compounding action.",
            ),
        ],
        lambda item: agent(item[2], schema=SUMMARY_SCHEMA, role=item[0], type_name=item[1]),
    )

    verdict = reviews[1]
    kit.record_workflow_run(
        repo="native-agent-stack",
        workflow_id="ecosystem-convergence",
        done_summary=f"converged={verdict['all_converged']}: {verdict['executive_brief'][:320]}",
        verified_by="; ".join(f"{r['probe']}:{r['ok']}" for r in probe_receipts),
        open_risks="; ".join(verdict["open_risks"][:2]) or "none",
        next_priority=verdict["next_actions"][0] if verdict["next_actions"] else "Monitor peer bus",
    )
    log(verdict["executive_brief"])
    print(json.dumps({"deterministic": deterministic_bundle, "reviews": reviews}, indent=2))
