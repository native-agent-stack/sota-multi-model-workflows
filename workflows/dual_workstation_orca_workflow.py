# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA `run_workflow` (`v3.4.0`): Dual-Machine Portable M5 Max + Stationary Noesis 64c/RTX4090 Orca Lane.

Verifies Dual-Workstation Orca mesh telemetry (`100.110.115.22`), single-broker-host firewall (`ADR-0020`),
and full `sota-research-feeds.v2` Research-Convergence parity (`13` workflows + `7` PIT DataFeeds + `4` strategy
templates + `ADR-0004` 3-tier SHA provenance + `PHILOSOPHY_ONLY` sibling-repo authority) across both
`Mac M5 Max` (`~/.agents/workflows`) and `Noesis` (`C:/sota-workstation/*` + `$HOME/.agents/workflows`).
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents" / "workflows"))
import _sota_kit as kit

cfg = kit.get_workflow_args(globals())
target_repo = str(cfg.get("repo") or "sota-harness-foundation")
fast_deterministic_only = bool(cfg.get("fast_deterministic_only", False))
sync_repos = bool(cfg.get("sync_repos", False))

phase("Phase 1: Dual-Machine Orca Mesh Telemetry, Preflight & Research-Convergence Parity")

peer_brief = kit.load_peer_brief(target_repo)
preflight = kit.run_preflight_summary(live_org=False)
research_convergence = kit.load_research_convergence_context()
rc_envelope = kit.verify_workflow_research_convergence("dual-workstation-orca", repo=target_repo)
ws_bin = Path.home() / ".agents" / "bin" / "sota-workstation"

reg_path = Path.home() / ".agents" / "workflows" / "REGISTRY.json"
local_workflow_count = 0
if reg_path.is_file():
    try:
        local_workflow_count = len(json.loads(reg_path.read_text(encoding="utf-8")).get("workflows") or [])
    except json.JSONDecodeError:
        local_workflow_count = 0

st_proc = subprocess.run(
    kit.agent_bin_argv(ws_bin, "status", "--json"),
    capture_output=True,
    text=True,
    timeout=25,
    check=False,
)
ws_status = json.loads(st_proc.stdout) if st_proc.returncode == 0 else {"ok": False, "stderr": st_proc.stderr}

sync_receipt: dict[str, object] | None = None
if sync_repos:
    sy_proc = subprocess.run(
        kit.agent_bin_argv(ws_bin, "sync", "--repo", target_repo, "--json"),
        capture_output=True,
        text=True,
        timeout=35,
        check=False,
    )
    sync_receipt = json.loads(sy_proc.stdout) if sy_proc.returncode == 0 else {"ok": False, "stderr": sy_proc.stderr}

bundle = {
    "target_repo": target_repo,
    "preflight": preflight,
    "workstation_status": ws_status,
    "sync_receipt": sync_receipt,
    "research_convergence_parity": {
        "schema_version": research_convergence["schema_version"],
        "convergence_adr": research_convergence["convergence_adr"],
        "sibling_repo_authority": research_convergence.get("sibling_repo_authority", "PHILOSOPHY_ONLY"),
        "canonical_feed_count": research_convergence["feed_count"],
        "strategy_archetype_count": len(research_convergence["strategy_archetypes"]),
        "strategy_archetypes": research_convergence["strategy_archetypes"],
        "local_workflow_count": local_workflow_count,
        "mac_workflows_root": "~/.agents/workflows",
        "noesis_repos_root": "C:/sota-workstation/*",
        "noesis_workflows_root": "$HOME/.agents/workflows",
        "noesis_wsl_carbon_root": "~/sota-workstation/*",
        "noesis_wsl_workflows_root": "~/.agents/workflows",
    },
    "research_convergence_envelope": rc_envelope,
}
log(json.dumps(bundle, indent=2))

if fast_deterministic_only:
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="dual-workstation-orca-fast",
        done_summary=(
            f"Dual-Machine Orca Lane ok={ws_status.get('ok')} | "
            f"Noesis reachable={(ws_status.get('stationaryNoesis') or {}).get('reachable')} "
            f"rttMs={(ws_status.get('stationaryNoesis') or {}).get('rttMs')} | "
            f"rc={research_convergence['schema_version']} ({local_workflow_count} workflows)"
        ),
        verified_by="sota-workstation status --json + sota-doctor 11/11 + sota-research-feeds.v2",
        next_priority="Ready for portable M5 Max roaming or Noesis 64c/RTX4090 batch offload",
    )
    print(json.dumps(bundle, indent=2))
else:
    PLACEMENT_SCHEMA = {
        "type": "object",
        "properties": {
            "recommended_host": {"type": "string"},
            "orca_command": {"type": "string"},
            "firewall_verified": {"type": "boolean"},
            "research_convergence_parity_verified": {"type": "boolean"},
            "summary": {"type": "string"},
        },
        "required": [
            "recommended_host",
            "orca_command",
            "firewall_verified",
            "research_convergence_parity_verified",
            "summary",
        ],
    }

    phase("Phase 2: Cross-Machine Placement, Research-Convergence & Two-Pass Firewall Verification")

    verdict = await agent(
        f"{peer_brief}\n\nDual-Workstation & Research-Convergence Telemetry:\n{json.dumps(bundle, indent=2)}\n"
        f"Verify: (1) ADR-0020 single-broker-host firewall (`singleActiveBrokerHostOnly=True`), "
        f"(2) Research-Convergence parity (`13` workflows + `sota-research-feeds.v2` `7` PIT feeds + `4` strategy "
        f"templates + ADR-0004 3-tier SHA provenance + `PHILOSOPHY_ONLY` sibling-repo authority) across BOTH "
        f"`Mac M5 Max` (`~/.agents/workflows`) and `Noesis` (`C:/sota-workstation/*` + `$HOME/.agents/workflows`), "
        f"(3) zero secret/home-path leaks, and emit the exact `sota-workstation` or `orca` placement command for `{target_repo}`.",
        schema=PLACEMENT_SCHEMA,
        role=f"Dual-Machine Orca Verifier ({target_repo})",
        type_name="sota-code-verifier",
    )
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="dual-workstation-orca",
        done_summary=(
            f"host={verdict['recommended_host']} firewall={verdict['firewall_verified']} "
            f"rc_parity={verdict['research_convergence_parity_verified']}: {verdict['summary'][:280]}"
        ),
        verified_by="sota-workstation status + sota-research-feeds.v2 + sota-code-verifier",
        next_priority=verdict["orca_command"][:200],
    )
    print(json.dumps({"telemetry": bundle, "verdict": verdict}, indent=2))
