# ruff: noqa: E402, F704, F821, PLE1142
"""AGY SOTA `run_workflow` (`v3.1.0`): Dual-Machine Portable M5 Max + Stationary Noesis 64c/RTX4090 Orca Lane."""

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

phase("Phase 1: Dual-Machine Orca Mesh Telemetry & Preflight")

peer_brief = kit.load_peer_brief(target_repo)
preflight = kit.run_preflight_summary(live_org=False)
ws_bin = Path.home() / ".agents" / "bin" / "sota-workstation"

st_proc = subprocess.run(
    kit.agent_bin_argv(ws_bin, "status", "--json"),
    capture_output=True,
    text=True,
    timeout=15,
    check=False,
)
ws_status = json.loads(st_proc.stdout) if st_proc.returncode == 0 else {"ok": False, "stderr": st_proc.stderr}

sync_receipt: dict[str, object] | None = None
if sync_repos:
    sy_proc = subprocess.run(
        kit.agent_bin_argv(ws_bin, "sync", "--repo", target_repo, "--json"),
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )
    sync_receipt = json.loads(sy_proc.stdout) if sy_proc.returncode == 0 else {"ok": False, "stderr": sy_proc.stderr}

bundle = {
    "target_repo": target_repo,
    "preflight": preflight,
    "workstation_status": ws_status,
    "sync_receipt": sync_receipt,
}
log(json.dumps(bundle, indent=2))

if fast_deterministic_only:
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="dual-workstation-orca-fast",
        done_summary=(
            f"Dual-Machine Orca Lane ok={ws_status.get('ok')} | "
            f"Noesis reachable={(ws_status.get('stationaryNoesis') or {}).get('reachable')} "
            f"rttMs={(ws_status.get('stationaryNoesis') or {}).get('rttMs')}"
        ),
        verified_by="sota-workstation status --json + sota-doctor 11/11",
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
            "summary": {"type": "string"},
        },
        "required": ["recommended_host", "orca_command", "firewall_verified", "summary"],
    }

    phase("Phase 2: Cross-Machine Placement & Two-Pass Firewall Verification")

    verdict = await agent(
        f"{peer_brief}\n\nDual-Workstation Telemetry:\n{json.dumps(bundle, indent=2)}\n"
        f"Verify ADR-0020 single-broker-host firewall (`singleActiveBrokerHostOnly=True`), zero secret/home-path leaks, "
        f"and emit the exact `sota-workstation` or `orca` placement command for `{target_repo}`.",
        schema=PLACEMENT_SCHEMA,
        role=f"Dual-Machine Orca Verifier ({target_repo})",
        type_name="sota-code-verifier",
    )
    kit.record_workflow_run(
        repo=target_repo,
        workflow_id="dual-workstation-orca",
        done_summary=f"host={verdict['recommended_host']} firewall={verdict['firewall_verified']}: {verdict['summary'][:300]}",
        verified_by="sota-workstation status + sota-code-verifier",
        next_priority=verdict["orca_command"][:200],
    )
    print(json.dumps({"telemetry": bundle, "verdict": verdict}, indent=2))
