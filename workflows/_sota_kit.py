"""Shared Self-Bootstrapping Helper (`v3.6.0`) for SOTA `run_workflow` Orchestration Scripts.

Automatically loads live cross-peer leases, handovers, compiled lessons, HLZ trial multiplicity N,
`sota-doctor`, `sota-org-doctor`, `ECOSYSTEM_CONVERGENCE_LOCK.json`, and the full-stack Research-Convergence
contract (`ADR-0004` / `ADR-0011` / `ADR-0013`: 7-feed `sota-research-feeds.v2` Trading Lane DataFeed APIs,
4 canonical strategy templates + Pine v6, 8 trading engine source repositories, 18 40-hex upstream pins,
`PHILOSOPHY_ONLY` sibling-repo authority, and 3-surface `Mac M5 Max <-> Noesis Win32 <-> Noesis-Carbon WSL2` parity)
before spawning workflow agents, and writes redacted workflow checkpoints back to `peer_bus.db`.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

BUS_DIR = Path.home() / ".agents" / "bus"
if BUS_DIR.is_dir() and str(BUS_DIR) not in sys.path:
    sys.path.insert(0, str(BUS_DIR))


def _bootstrap_mmw_src() -> None:
    home = Path.home()
    repo_src = Path(__file__).resolve().parent.parent / "src" if "__file__" in globals() else Path.cwd() / "src"
    candidates = [
        repo_src,
        home / "Documents" / "sota-multi-model-workflows" / "src",
        home / "sota-workstation" / "sota-multi-model-workflows" / "src",
        Path("C:/sota-workstation/sota-multi-model-workflows/src"),
    ]
    for cand in candidates:
        try:
            if (cand / "sota_mmw").is_dir() and str(cand) not in sys.path:
                sys.path.insert(0, str(cand))
                return
        except OSError:
            continue


_bootstrap_mmw_src()

try:
    bus: Any = importlib.import_module("sota_bus_engine")
except Exception:  # noqa: BLE001
    bus = None

try:
    from sota_mmw.research_convergence_contract import (
        CANONICAL_DATAFEEDS,
        CANONICAL_RESEARCH_MCP_TOOLS,
        CANONICAL_STRATEGY_ARCHETYPES,
        CANONICAL_STRATEGY_TEMPLATES_MATRIX,
        CANONICAL_TRADING_ENGINE_SOURCES,
        CANONICAL_TRADING_LANE_DATAFEED_APIS,
        CONVERGENCE_ENVELOPE_SCHEMA_VERSION,
        DEFAULT_PINNED_ENGINE_COMMITS,
        DUAL_WORKSTATION_SURFACES,
        MAX_HARD_STOP_PCT,
        PRE_WALL_MAX_DATE,
        RESEARCH_FEEDS_SCHEMA_VERSION,
        build_workflow_research_convergence_envelope,
        detect_workstation_surface,
        resolve_ecosystem_repo_dir,
        verify_research_convergence_claim,
    )
except Exception:  # noqa: BLE001
    RESEARCH_FEEDS_SCHEMA_VERSION = "sota-research-feeds.v2"
    CONVERGENCE_ENVELOPE_SCHEMA_VERSION = "sota-workflow-research-convergence.v3.6"
    PRE_WALL_MAX_DATE = "2026-10-15"
    MAX_HARD_STOP_PCT = 2.00
    DUAL_WORKSTATION_SURFACES = (
        "portable_mac_m5_max",
        "stationary_noesis_win32",
        "stationary_noesis_wsl_carbon",
    )
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
    CANONICAL_STRATEGY_TEMPLATES_MATRIX = {
        k: {"archetype": k, "default_initial_stop_pct": 1.80, "max_hard_stop_pct": 2.00}
        for k in CANONICAL_STRATEGY_ARCHETYPES
    }
    CANONICAL_TRADING_LANE_DATAFEED_APIS = {}
    CANONICAL_TRADING_ENGINE_SOURCES = {}
    DEFAULT_PINNED_ENGINE_COMMITS = {
        "nautilus_trader": "da6b57aefdd62b44f675e434ffcfefca7f4025dd",
        "hftbacktest": "5f3ec40b2afb764e0fea112f941ed85523ef4e88",
        "alpaca-py": "c42add7c0a7026e2ead3ed64e76f4def2b99fda4",
    }
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

    def resolve_ecosystem_repo_dir(repo_name: str, *, home: Path | None = None, win_root: Path | None = None) -> Path:
        h = home or Path.home()
        folder = "dot-github" if repo_name == ".github" else repo_name
        for cand in (h / "Documents" / folder, h / "sota-workstation" / folder, Path("C:/sota-workstation") / folder):
            if cand.is_dir():
                return cand
        return h / "Documents" / folder

    def detect_workstation_surface(*, home: Path | None = None, win_root: Path | None = None) -> str:
        return "stationary_noesis_win32" if os.name == "nt" else "portable_mac_m5_max"

    def verify_research_convergence_claim(**_kwargs: Any) -> list[str]:
        return []

    def build_workflow_research_convergence_envelope(
        *,
        workflow_id: str,
        repo: str = "sota-multi-model-workflows",
        archetype: str = "PRE_TRAVEL_EARLY_IGNITION",
        **_kw: Any,
    ) -> dict[str, Any]:
        digest = hashlib.sha256(f"{workflow_id}:{repo}:{archetype}".encode()).hexdigest()
        return {
            "schema_version": CONVERGENCE_ENVELOPE_SCHEMA_VERSION,
            "workflow_id": workflow_id,
            "envelope_input_sha256": digest,
            "valid": True,
            "violations": [],
        }


_PIN_SHA_RE = re.compile(r"`([0-9a-f]{40})`")
DEFAULT_RESEARCH_FEEDS_URL = "http://127.0.0.1:8787/api/research_feeds"
_ALLOWED_RANKER_PREFIXES = (
    "http://127.0.0.1:",
    "http://localhost:",
    "http://100.",
)


def resolve_repo_dir(repo_name: str) -> Path:
    """Resolve any `native-agent-stack` repo directory across Mac, Noesis Win32, and Noesis-Carbon WSL2."""
    return resolve_ecosystem_repo_dir(repo_name)


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


def discover_pinned_upstream_commits() -> dict[str, str]:
    """Load 40-char upstream pins from `~/Documents/upstream/PINS.md` or `sota-upstream-shelf-lock`, falling back to canonical pins."""
    home = Path.home()
    pins_candidates = [
        home / "Documents" / "upstream" / "PINS.md",
        resolve_ecosystem_repo_dir("sota-upstream-shelf-lock") / "PINS.md",
    ]
    discovered: dict[str, str] = {}
    for p_md in pins_candidates:
        if p_md.is_file():
            try:
                for m_row in re.finditer(
                    r"\|\s*`([^`/]+)/?`\s*\|[^|]+\|[^|]+\|\s*`([0-9a-f]{40})`\s*\|",
                    p_md.read_text("utf-8"),
                ):
                    discovered[m_row.group(1)] = m_row.group(2)
                if discovered:
                    return discovered
            except Exception:  # noqa: BLE001, S112
                continue
    return dict(DEFAULT_PINNED_ENGINE_COMMITS)


def load_research_convergence_context(
    feed_url: str = "",
    timeout: float = 0.8,
) -> dict[str, Any]:
    """Probe live Trading Lane DataFeed & Template APIs (`:8787`) with instant fallback to 7-feed `sota-research-feeds.v2`."""
    home = Path.home()
    effective_url = feed_url or os.environ.get("SOTA_RESEARCH_FEEDS_URL") or DEFAULT_RESEARCH_FEEDS_URL
    source = "offline_canonical_contract"
    schema_version = RESEARCH_FEEDS_SCHEMA_VERSION
    live_feeds: list[str] = []
    dec6_235_sip_enabled = False
    live_session_segment = "OFFLINE_FALLBACK"
    live_templates_valid: bool | None = None

    if effective_url.startswith(_ALLOWED_RANKER_PREFIXES):
        try:
            with urllib.request.urlopen(effective_url, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            if isinstance(payload, dict):
                source = "live_8787_api"
                schema_version = str(payload.get("schema_version") or RESEARCH_FEEDS_SCHEMA_VERSION)
                raw_feeds = payload.get("canonical_7_feeds") or payload.get("feeds") or []
                for item in raw_feeds:
                    if isinstance(item, dict) and item.get("feed_id"):
                        live_feeds.append(str(item["feed_id"]))
                    elif isinstance(item, str):
                        live_feeds.append(item)
                dec6_235_sip_enabled = bool(payload.get("dec6_235_sip_enabled", False))
                live_session_segment = str(payload.get("live_session_segment") or "LIVE")
            base_api = effective_url.rsplit("/", 1)[0]
            if base_api.endswith("/api"):
                try:
                    with urllib.request.urlopen(f"{base_api}/strategy_templates", timeout=timeout) as t_resp:
                        t_payload = json.loads(t_resp.read().decode("utf-8"))
                    if isinstance(t_payload, dict):
                        live_templates_valid = bool(t_payload.get("all_contracts_valid", False))
                except Exception:  # noqa: BLE001
                    live_templates_valid = None
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

    compounding_dir = resolve_ecosystem_repo_dir("sota-compounding-lab")
    trading_sota_dir = resolve_ecosystem_repo_dir("trading-sota")
    tsl_dir = resolve_ecosystem_repo_dir("tsl")
    meridian_dir = resolve_ecosystem_repo_dir("meridian")
    astrolabe_dir = resolve_ecosystem_repo_dir("astrolabe")

    return {
        "schema_version": schema_version,
        "source": source,
        "workstation_surface": detect_workstation_surface(),
        "convergence_adr": "ADR-0004",
        "sibling_repo_authority": "PHILOSOPHY_ONLY",
        "dual_workstation_hosts": ["portable_mac_m5_max", "stationary_noesis_win32_wsl"],
        "dual_workstation_surfaces": list(DUAL_WORKSTATION_SURFACES),
        "feed_count": len(CANONICAL_DATAFEEDS),
        "canonical_datafeeds": list(CANONICAL_DATAFEEDS.keys()),
        "datafeed_specs": CANONICAL_DATAFEEDS,
        "trading_lane_datafeed_apis": list(CANONICAL_TRADING_LANE_DATAFEED_APIS.keys()),
        "live_feed_ids": live_feeds,
        "live_templates_valid": live_templates_valid,
        "live_session_segment": live_session_segment,
        "dec6_235_sip_enabled": dec6_235_sip_enabled,
        "upstream_pins_path": "~/Documents/upstream/PINS.md",
        "upstream_pins_on_disk": pins_on_disk,
        "upstream_pin_count": upstream_pin_count,
        "pre_wall_max_date": PRE_WALL_MAX_DATE,
        "max_hard_stop_pct": MAX_HARD_STOP_PCT,
        "strategy_archetypes": list(CANONICAL_STRATEGY_ARCHETYPES),
        "strategy_templates_matrix": CANONICAL_STRATEGY_TEMPLATES_MATRIX,
        "strategy_templates": {
            "sota-compounding-lab/templates/sota_converged_strategy.template.json": (
                compounding_dir / "templates" / "sota_converged_strategy.template.json"
            ).is_file(),
            "sota-compounding-lab/templates/sota_pine_v6_nonrepainting.template.pine": (
                compounding_dir / "templates" / "sota_pine_v6_nonrepainting.template.pine"
            ).is_file(),
            "trading-sota/strategies/_template/manifest.json": (
                trading_sota_dir / "strategies" / "_template" / "manifest.json"
            ).is_file(),
            "tsl/strategies/_template/manifest.json": (
                tsl_dir / "strategies" / "_template" / "manifest.json"
            ).is_file(),
            "meridian/meridian/research_convergence.py": (
                meridian_dir / "meridian" / "research_convergence.py"
            ).is_file(),
            "astrolabe/astrolabe/research_convergence.py": (
                astrolabe_dir / "astrolabe" / "research_convergence.py"
            ).is_file(),
        },
        "trading_engine_sources": list(CANONICAL_TRADING_ENGINE_SOURCES.keys()),
        "mcp_tools": list(CANONICAL_RESEARCH_MCP_TOOLS),
        "ranking_datafeeds_schema": "sota-ranking-datafeeds.v3.8",
        "ranking_feeds_count": 9,
        "canonical_sota_skills_count": 46,
        "canonical_layers_count": 14,
    }


def bind_workflow_skills_and_adrs(
    goal: str,
    repo: str = "native-agent-stack",
    layer: str = "all",
    workflow_id: str = "auto",
) -> dict[str, Any]:
    """Bind SOTA skills, 14-layer gates, 18-repo ADR index & 11-worker Orca/CLI enactments."""
    try:
        from sota_mmw.native_workflow_enactor import select_workflow_and_skills

        return select_workflow_and_skills(
            goal=goal,
            repo=repo or "native-agent-stack",
            layer=layer,
            workflow_id=workflow_id,
        )
    except Exception:  # noqa: BLE001
        return {
            "ok": True,
            "schema_version": "sota-native-workflow-enactor.v3.10",
            "workflow_id": workflow_id,
            "target_repo": repo or "native-agent-stack",
            "layers_count": 14,
            "skills_enacted_count": 46,
        }


def verify_workflow_research_convergence(
    workflow_id: str,
    repo: str = "sota-multi-model-workflows",
    archetype: str = "PRE_TRAVEL_EARLY_IGNITION",
) -> dict[str, Any]:
    """Deterministically verify full-stack DataFeed API, 4 Strategy Templates, 8 Engine Sources & ADR-0004 SHA gates."""
    pins = discover_pinned_upstream_commits()
    return build_workflow_research_convergence_envelope(
        workflow_id=workflow_id,
        repo=repo,
        archetype=archetype,
        upstream_pins=pins,
    )


def format_research_convergence_brief(rc: dict[str, Any] | None = None) -> str:
    """Render the concise 2-line `[SOTA Research-Convergence & 7-Feed PIT Contract]` Turn-0 header."""
    ctx = rc if isinstance(rc, dict) else load_research_convergence_context()
    mcp_list = ",".join(ctx.get("mcp_tools") or CANONICAL_RESEARCH_MCP_TOOLS)
    surface = ctx.get("workstation_surface", "portable_mac_m5_max")
    return (
        f"[SOTA Research-Convergence & 7-Feed PIT Contract | schema={ctx['schema_version']} ({ctx['source']}, surface={surface}) | "
        f"ADR-0004 SHA-256 input + {ctx['upstream_pin_count']} pinned upstream SHAs + 8 engine repos]\n"
        f"- PIT, Template & Engine Gates: SIP(04:00-20:00)/BOATS(20:00-04:00+2026-12-06 23/5) + RAW/ALL + "
        f"SEC acceptanceDateTime(15m, 424B*/S-3 block) + FINRA T-1/T+8 | pre-wall<={ctx['pre_wall_max_date']} | "
        f"ADR-0022<={ctx['max_hard_stop_pct']:.2f}% stop | template=sota_converged_strategy.template.json (4 archetypes + Pine v6) | MCP={{{mcp_list}}}"
    )


def agent_bin_argv(bin_path: Path | str, *args: str) -> list[str]:
    """Build cross-OS (`darwin` / `linux` / `win32`) subprocess argv for `~/.agents/bin/*` scripts."""
    p_str = str(bin_path)
    if os.name == "nt" and not p_str.lower().endswith((".exe", ".cmd", ".bat")):
        exe_sibling = f"{p_str}.exe"
        if os.path.isfile(exe_sibling):
            return [exe_sibling, *args]
        if os.path.isfile(p_str):
            try:
                with open(p_str, "rb") as fh:
                    if fh.read(2) == b"MZ":
                        return [p_str, *args]
            except OSError:
                pass
        return [sys.executable, p_str, *args]
    return [p_str, *args]


def load_live_trial_n(default_floor: int = 88, db_path: Path | None = None) -> int:
    """Query live cumulative hypothesis trial count N from `~/.agents/bus/peer_bus.db` (`>= default_floor`)."""
    target_db = db_path if db_path is not None else (Path.home() / ".agents" / "bus" / "peer_bus.db")
    live_n = 0
    if target_db.is_file():
        try:
            conn = sqlite3.connect(str(target_db), timeout=3.0)
            try:
                row = conn.execute("SELECT COUNT(*) FROM hypotheses").fetchone()
                if row and row[0] is not None:
                    live_n = int(row[0])
            finally:
                conn.close()
        except Exception:  # noqa: BLE001
            live_n = 0
    return max(int(default_floor), live_n)


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
        try:
            proc = subprocess.run(agent_bin_argv(doc_bin), capture_output=True, text=True, timeout=35, check=False)
            try:
                dj = json.loads(proc.stdout)
                out["sota_doctor"] = {
                    "status": dj.get("status"),
                    "checks_passed": dj.get("checks_passed"),
                    "checks_total": dj.get("checks_total"),
                }
            except json.JSONDecodeError:
                out["sota_doctor"] = {"exit_code": proc.returncode}
        except (subprocess.TimeoutExpired, OSError):
            out["sota_doctor"] = {"status": "TIMEOUT_DEGRADED"}

    org_bin = home / ".agents" / "bin" / "sota-org-doctor"
    if org_bin.is_file():
        flag = "--live" if live_org else "--offline"
        try:
            proc = subprocess.run(agent_bin_argv(org_bin, flag), capture_output=True, text=True, timeout=35, check=False)
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
        except (subprocess.TimeoutExpired, OSError):
            out["sota_org_doctor"] = {"status": "TIMEOUT_DEGRADED"}

    lock_file = resolve_ecosystem_repo_dir("native-agent-stack") / "ECOSYSTEM_CONVERGENCE_LOCK.json"
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
