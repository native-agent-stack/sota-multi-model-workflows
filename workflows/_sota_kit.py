"""Shared Self-Bootstrapping Helper (`v3.3.0`) for SOTA `run_workflow` Orchestration Scripts.

Automatically loads live cross-peer leases, handovers, compiled lessons, HLZ trial multiplicity N,
`sota-doctor` (`11/11`), `sota-org-doctor` (`4` org invariants), `ECOSYSTEM_CONVERGENCE_LOCK.json`,
and the 7-feed `sota-research-feeds.v2` Research-Convergence & Strategy Template contract (`ADR-0004` / `ADR-0011`)
before spawning workflow agents, and writes redacted workflow checkpoints back to `peer_bus.db`.
"""

from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

BUS_DIR = Path.home() / ".agents" / "bus"
if BUS_DIR.is_dir() and str(BUS_DIR) not in sys.path:
    sys.path.insert(0, str(BUS_DIR))

HOME_MMW_SRC = Path.home() / "Documents" / "sota-multi-model-workflows" / "src"
REPO_SRC = Path(__file__).resolve().parent.parent / "src" if "__file__" in globals() else Path.cwd() / "src"
_ACTIVE_MMW_SRC = REPO_SRC if (REPO_SRC / "sota_mmw").is_dir() else HOME_MMW_SRC
if (_ACTIVE_MMW_SRC / "sota_mmw").is_dir() and str(_ACTIVE_MMW_SRC) not in sys.path:
    sys.path.insert(0, str(_ACTIVE_MMW_SRC))

try:
    bus: Any = importlib.import_module("sota_bus_engine")
except Exception:  # noqa: BLE001
    bus = None

try:
    from sota_mmw.research_convergence_contract import (
        CANONICAL_DATAFEEDS,
        CANONICAL_RESEARCH_MCP_TOOLS,
        CANONICAL_STRATEGY_ARCHETYPES,
        MAX_HARD_STOP_PCT,
        PRE_WALL_MAX_DATE,
        RESEARCH_FEEDS_SCHEMA_VERSION,
    )
except Exception:  # noqa: BLE001
    RESEARCH_FEEDS_SCHEMA_VERSION = "sota-research-feeds.v2"
    PRE_WALL_MAX_DATE = "2026-10-15"
    MAX_HARD_STOP_PCT = 2.00
    CANONICAL_RESEARCH_MCP_TOOLS = (
        "sota_get_research_feeds",
        "sota_get_first_hand_incentives",
        "sota_get_converged_strategy_templates",
    )
    CANONICAL_STRATEGY_ARCHETYPES = (
        "PRE_TRAVEL_EARLY_IGNITION",
        "FIRST_HAND_SEC_EPISODIC_PIVOT",
        "MEGA_CAP_NEAR_LOSSLESS_ORB",
        "CLIMAX_VWAP_MEAN_REVERSION",
    )
    CANONICAL_DATAFEEDS = {
        k: {"feed_id": k, "schema_version": RESEARCH_FEEDS_SCHEMA_VERSION}
        for k in (
            "alpaca_sip",
            "alpaca_boats",
            "alpaca_raw_vs_all_adjustment",
            "sec_edgar_acceptance_datetime",
            "finra_regsho_cnmsshvol_t1",
            "corporate_actions_split_guard",
            "ibkr_paper_4002_l1",
        )
    }

_PIN_SHA_RE = re.compile(r"`([0-9a-f]{40})`")
DEFAULT_RESEARCH_FEEDS_URL = "http://127.0.0.1:8787/api/research_feeds"


def get_workflow_args(ns: dict[str, Any]) -> dict[str, Any]:
    """Safely extract `args` dict injected by `run_workflow` even when omitted."""
    raw = ns.get("args")
    return dict(raw) if isinstance(raw, dict) else {}


def get_primary_workspace(ns: dict[str, Any], default: str = "") -> str:
    """Safely extract primary workspace path injected by `run_workflow`."""
    ws = ns.get("WORKSPACES")
    if isinstance(ws, (list, tuple)) and ws:
        return str(ws[0])
    return default


def load_research_convergence_context(
    feed_url: str = DEFAULT_RESEARCH_FEEDS_URL,
    timeout: float = 0.8,
) -> dict[str, Any]:
    """Probe live `:8787/api/research_feeds` (`timeout=0.8`) with instant fallback to 7-feed `sota-research-feeds.v2`."""
    home = Path.home()
    source = "offline_canonical_contract"
    schema_version = RESEARCH_FEEDS_SCHEMA_VERSION
    live_feeds: list[str] = []
    dec6_235_sip_enabled = False
    live_session_segment = "OFFLINE_FALLBACK"

    if feed_url.startswith(("http://127.0.0.1:", "http://localhost:")):
        try:
            with urllib.request.urlopen(feed_url, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            if isinstance(payload, dict):
                source = "live_8787_api"
                schema_version = str(payload.get("schema_version") or RESEARCH_FEEDS_SCHEMA_VERSION)
                raw_feeds = payload.get("feeds") or []
                live_feeds = [
                    str(item.get("feed_id")) for item in raw_feeds if isinstance(item, dict) and item.get("feed_id")
                ]
                dec6_235_sip_enabled = bool(payload.get("dec6_235_sip_enabled", False))
                live_session_segment = str(payload.get("live_session_segment") or "LIVE")
        except Exception:  # noqa: BLE001
            source = "offline_canonical_contract"

    pins_file = home / "Documents" / "upstream" / "PINS.md"
    pins_on_disk = pins_file.is_file()
    pin_shas: list[str] = []
    if pins_on_disk:
        try:
            pin_shas = _PIN_SHA_RE.findall(pins_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pin_shas = []
    upstream_pin_count = len(pin_shas) if pin_shas else 18

    compounding_tpl = (
        home / "Documents" / "sota-compounding-lab" / "templates" / "sota_converged_strategy.template.json"
    )
    trading_sota_tpl = home / "Documents" / "trading-sota" / "strategies" / "_template" / "manifest.json"

    return {
        "schema_version": schema_version,
        "source": source,
        "convergence_adr": "ADR-0004",
        "feed_count": len(CANONICAL_DATAFEEDS),
        "canonical_datafeeds": list(CANONICAL_DATAFEEDS.keys()),
        "datafeed_specs": CANONICAL_DATAFEEDS,
        "live_feed_ids": live_feeds,
        "live_session_segment": live_session_segment,
        "dec6_235_sip_enabled": dec6_235_sip_enabled,
        "upstream_pins_path": "~/Documents/upstream/PINS.md",
        "upstream_pins_on_disk": pins_on_disk,
        "upstream_pin_count": upstream_pin_count,
        "pre_wall_max_date": PRE_WALL_MAX_DATE,
        "max_hard_stop_pct": MAX_HARD_STOP_PCT,
        "strategy_archetypes": list(CANONICAL_STRATEGY_ARCHETYPES),
        "strategy_templates": {
            "~/Documents/sota-compounding-lab/templates/sota_converged_strategy.template.json": compounding_tpl.is_file(),
            "~/Documents/trading-sota/strategies/_template/manifest.json": trading_sota_tpl.is_file(),
        },
        "mcp_tools": list(CANONICAL_RESEARCH_MCP_TOOLS),
    }


def format_research_convergence_brief(rc: dict[str, Any] | None = None) -> str:
    """Render the concise 2-line `[SOTA Research-Convergence & 7-Feed PIT Contract]` Turn-0 header."""
    ctx = rc if isinstance(rc, dict) else load_research_convergence_context()
    mcp_list = ",".join(ctx.get("mcp_tools") or CANONICAL_RESEARCH_MCP_TOOLS)
    return (
        f"[SOTA Research-Convergence & 7-Feed PIT Contract | schema={ctx['schema_version']} ({ctx['source']}) | "
        f"ADR-0004 SHA-256 input + {ctx['upstream_pin_count']} pinned ~/Documents/upstream/ SHAs]\n"
        f"- PIT & Template Gates: SIP(04:00-20:00)/BOATS(20:00-04:00+2026-12-06 23/5) + RAW/ALL + "
        f"SEC acceptanceDateTime(15m, 424B*/S-3 block) + FINRA T-1 | pre-wall<={ctx['pre_wall_max_date']} | "
        f"ADR-0022<={ctx['max_hard_stop_pct']:.2f}% stop | template=sota_converged_strategy.template.json | MCP={{{mcp_list}}}"
    )


def run_preflight_summary(live_org: bool = False) -> dict[str, Any]:
    """Run deterministic local + org preflight checks (`sota-doctor`, `sota-org-doctor`, umbrella lock)."""
    home = Path.home()
    out: dict[str, Any] = {
        "sota_doctor": "UNAVAILABLE",
        "sota_org_doctor": "UNAVAILABLE",
        "umbrella_lock": "UNAVAILABLE",
    }

    doc_bin = home / ".agents" / "bin" / "sota-doctor"
    if doc_bin.is_file():
        proc = subprocess.run([str(doc_bin)], capture_output=True, text=True, timeout=15, check=False)
        try:
            dj = json.loads(proc.stdout)
            out["sota_doctor"] = {
                "status": dj.get("status"),
                "checks_passed": dj.get("checks_passed"),
                "checks_total": dj.get("checks_total"),
            }
        except json.JSONDecodeError:
            out["sota_doctor"] = {"exit_code": proc.returncode}

    org_bin = home / ".agents" / "bin" / "sota-org-doctor"
    if org_bin.is_file():
        flag = "--live" if live_org else "--offline"
        proc = subprocess.run([str(org_bin), flag], capture_output=True, text=True, timeout=30, check=False)
        try:
            oj = json.loads(proc.stdout)
            out["sota_org_doctor"] = {
                "status": oj.get("status"),
                "mode": oj.get("mode"),
                "repos_total": oj.get("repos_total"),
                "violations_count": len(oj.get("violations") or []),
            }
        except json.JSONDecodeError:
            out["sota_org_doctor"] = {"exit_code": proc.returncode}

    lock_file = home / "Documents" / "native-agent-stack" / "ECOSYSTEM_CONVERGENCE_LOCK.json"
    if lock_file.is_file():
        try:
            lj = json.loads(lock_file.read_text(encoding="utf-8"))
            out["umbrella_lock"] = {
                "schemaVersion": lj.get("schemaVersion"),
                "public_repos": len(lj.get("publicUnlimitedActionsTier") or []),
                "active_private_repos": len(lj.get("privateProprietaryExecutionAndVaultTier") or []),
                "cold_archived_repos": len(lj.get("coldArchivedSupersededTier") or []),
                "single_owner_layers": len(lj.get("layerSingleOwnerMap") or {}),
            }
        except Exception:  # noqa: BLE001
            out["umbrella_lock"] = "PARSE_ERROR"

    return out


def load_peer_brief(repo: str = "") -> str:
    """Return a compact, secret-redacted live peer-bus + Research-Convergence brief for child agent prompts."""
    rc_summary = format_research_convergence_brief()
    if bus is None:
        return f"[Peer Bus: unavailable]\n{rc_summary}"
    try:
        conn = bus.get_conn()
        try:
            st = bus.bus_status(conn, repo=repo)
            lessons = conn.execute(
                "SELECT domain, title, evidence_grade FROM lessons ORDER BY created_at DESC LIMIT 4"
            ).fetchall()
        finally:
            conn.close()
    except Exception:  # noqa: BLE001
        return f"[Peer Bus: unavailable]\n{rc_summary}"

    lines = [
        f"[Live SOTA Peer Bus @ {st['as_of_utc']} | Trials N={st['hypothesis_trials_total']} | Next HLZ t*={st['next_trial_hlz_t_hurdle']}]"
    ]
    leases: list[dict[str, Any]] = st.get("active_leases") or []
    if leases:
        lease_txt = "; ".join(
            f"{it['agent_family']}@{it['repo']}({','.join(it['paths'][:2])}: {it['intent'][:60]})" for it in leases[:4]
        )
        lines.append(f"- Active Peer Leases (DO NOT clobber): {lease_txt}")
    handovers: list[dict[str, Any]] = st.get("handovers") or []
    if handovers:
        h0 = handovers[0]
        lines.append(f"- Latest Handover ({h0['repo']}): done='{h0['done'][:110]}' | next='{h0['next_priority'][:90]}'")
    if lessons:
        l_txt = "; ".join(f"[{r['evidence_grade']}:{r['domain']}] {r['title'][:65]}" for r in lessons)
        lines.append(f"- Top Compiled Lessons: {l_txt}")
    lines.append(rc_summary)
    return "\n".join(lines)


def record_workflow_run(
    *,
    repo: str,
    workflow_id: str,
    done_summary: str,
    verified_by: str,
    open_risks: str = "none",
    next_priority: str = "",
) -> None:
    """Persist a redacted workflow execution checkpoint into `peer_bus.db` and `HANDOVER.md`."""
    if bus is None:
        return
    try:
        conn = bus.get_conn()
        try:
            bus.sync_handover(
                conn,
                repo=repo or "agy-workflow",
                agent_family=f"agy-workflow:{workflow_id}",
                done=done_summary[:500],
                verified_by=verified_by[:240],
                open_risks=open_risks[:240],
                next_priority=next_priority[:240],
            )
        finally:
            conn.close()
    except Exception:  # noqa: BLE001
        return
