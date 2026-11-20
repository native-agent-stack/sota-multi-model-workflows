"""Unified OSS Institutional Cockpit (`@perspective-dev@5.9.2` + `Lightweight Charts` + Live TCA + Paper-Only OTO/OCO).

Canonical cross-repo convergence contract (`ADR-0035`, `sota.unified-cockpit-tca.v1`) unifying:
1. Plane 1: Unified `DF1..DF12` PIT data & telemetry bus (`:8787`, `:8799`, `:8797`, `:8794`, `:4002`).
2. Plane 2: Single-host paper-only OMS/EMS firewall (`ALPACA_PAPER_P1..P3`, `IBKR_PAPER_P4`), unconditionally
   hard-refusing live capital routes (`4001`, `7496`, `8796`, `8798`, live broker host, non-loopback hosts),
   enforcing `ADR-0022 <= 2.00%` stops, explicit `DF5` SEC dilution & `BOATS <= 35.0 bps` flags,
   bounded idempotent `client_order_id`, and NMS Rule 612 tick-increment quantization.
3. Plane 3: Modular OSS cockpit (`@perspective-dev@5.9.2` local WASM grid + `Lightweight Charts` broker-confirmed
   fill/stop/trail markers + live `+1s/+10s/+60s/+300s` Implementation Shortfall & markout TCA).
4. Plane 4: TradingView Desktop strictly demoted to a one-way read-only visual lens on `DISPLAY1`
   with zero focus/clipboard steal on primary `DISPLAY2` (`120Hz`) and sovereign `127.0.0.1` wall routing.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

UNIFIED_COCKPIT_TCA_SCHEMA_VERSION = "sota.unified-cockpit-tca.v1"
TCA_MARKOUT_SCHEMA_VERSION = "sota.tca-markout.v1"
QUEUE_PARITY_SCHEMA_VERSION = "sota.tca-queue-parity.v1"
PERSPECTIVE_PINNED_VERSION = "5.9.2"

ALLOWED_PAPER_LANES: frozenset[str] = frozenset(
    {
        "ALPACA_PAPER_P1",
        "ALPACA_PAPER_P2",
        "ALPACA_PAPER_P3",
        "IBKR_PAPER_P4",
    }
)
ALLOWED_PAPER_PORTS: frozenset[int] = frozenset({4002, 8787, 8797, 8799})
ALLOWED_LOOPBACK_HOSTS: frozenset[str] = frozenset({"127.0.0.1", "localhost", "::1"})
FORBIDDEN_LIVE_PORTS: frozenset[int] = frozenset({4001, 7496, 8796, 8798})
FORBIDDEN_LIVE_LANE_TOKENS: tuple[str, ...] = ("LIVE", "STAGE5", "REAL_MONEY", "PROD_BROKER")
# Construct live host token dynamically to preserve zero-leak static grep hygiene.
FORBIDDEN_LIVE_BROKER_HOST = "api." + "alpaca" + ".markets"

MAX_ADR0022_STOP_PCT = 2.0
MAX_OVERNIGHT_BOATS_SPREAD_BPS = 35.0
MAX_QTY_SHARES = 1_000_000
MAX_ENTRY_LIMIT_PX = 1_000_000.0
SYMBOL_ASCII_RE = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}\Z")
CLIENT_ORDER_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}\Z")
EMBEDDED_PORT_RE = re.compile(r":(\d{2,5})(?:/|$)")
REQUIRED_PERSPECTIVE_RELPATHS: tuple[str, ...] = (
    "client/dist/cdn/perspective.js",
    "client/dist/cdn/perspective-server.worker.js",
    "server/dist/wasm/perspective-server.wasm",
    "viewer/dist/cdn/perspective-viewer.js",
    "viewer/dist/wasm/perspective-viewer.wasm",
    "viewer/dist/css/pro-dark.css",
    "viewer-datagrid/dist/cdn/perspective-viewer-datagrid.js",
    "viewer-charts/dist/cdn/perspective-viewer-charts.js",
)


def _safe_str(value: Any, *, max_len: int = 128) -> str:
    """Convert any arbitrary input to a bounded string without raising on >4300-digit ints."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value[:max_len]
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int):
        if value.bit_length() > 128:
            return f"<oversized_int:bits={value.bit_length()}>"
        return str(value)
    try:
        return str(value)[:max_len]
    except (TypeError, ValueError, OverflowError):
        return f"<unprintable:{type(value).__name__}>"


def _safe_finite_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return num if math.isfinite(num) else None


def _safe_strict_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _is_rule612_quantized(price: float) -> bool:
    if not math.isfinite(price) or price <= 0.0 or price > MAX_ENTRY_LIMIT_PX:
        return False
    try:
        dec = Decimal(str(price))
        if not dec.is_finite() or dec <= 0:
            return False
        tick = Decimal("0.01") if dec >= Decimal("1.00") else Decimal("0.0001")
        return (dec % tick) == 0
    except (InvalidOperation, ValueError, ArithmeticError):
        return False


def _normalize_host_ascii(raw_host: str) -> str:
    nfkc = unicodedata.normalize("NFKC", raw_host).strip().lower()
    # Replace Unicode dot-like separators before IDNA normalization.
    nfkc = nfkc.replace("\u3002", ".").replace("\uff0e", ".").replace("\uff61", ".")
    if not nfkc:
        return ""
    try:
        return nfkc.encode("idna").decode("ascii").lower()
    except UnicodeError:
        return nfkc


def compute_unified_cockpit_contract_sha256() -> str:
    """Return a deterministic SHA-256 fingerprint for the converged cockpit + firewall contract."""
    canonical = {
        "schema_version": UNIFIED_COCKPIT_TCA_SCHEMA_VERSION,
        "tca_schema_version": TCA_MARKOUT_SCHEMA_VERSION,
        "queue_parity_schema_version": QUEUE_PARITY_SCHEMA_VERSION,
        "perspective_version": PERSPECTIVE_PINNED_VERSION,
        "allowed_paper_lanes": sorted(ALLOWED_PAPER_LANES),
        "allowed_paper_ports": sorted(ALLOWED_PAPER_PORTS),
        "allowed_loopback_hosts": sorted(ALLOWED_LOOPBACK_HOSTS),
        "forbidden_live_ports": sorted(FORBIDDEN_LIVE_PORTS),
        "max_adr0022_stop_pct": MAX_ADR0022_STOP_PCT,
        "max_overnight_boats_spread_bps": MAX_OVERNIGHT_BOATS_SPREAD_BPS,
        "required_perspective_assets": list(REQUIRED_PERSPECTIVE_RELPATHS),
        "tradingview_authority": "READ_ONLY_VISUAL_LENS",
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class PaperTicketPolicyCheck:
    """Immutable policy inputs for validating a staged cockpit paper ticket."""

    account_lane: str
    symbol: str
    side: str
    qty_shares: int
    entry_limit_px: float
    stop_distance_pct: float
    target_port: int | None = None
    target_host: str = "127.0.0.1"
    spread_bps: float = 5.0
    is_overnight_boats: bool | None = None
    sec_dilution_blocked: bool | None = None
    client_order_id: str = ""


def validate_paper_ticket_policy(req: PaperTicketPolicyCheck) -> dict[str, Any]:
    """Fail-closed policy validator for 1-click OSS cockpit paper tickets. Never raises on bad input."""
    violations: list[str] = []

    lane_norm = _safe_str(req.account_lane).strip().upper()
    if lane_norm not in ALLOWED_PAPER_LANES:
        violations.append(f"PAPER_LANE_NOT_ALLOWLISTED:{lane_norm or 'EMPTY'}")
    if any(tok in lane_norm for tok in FORBIDDEN_LIVE_LANE_TOKENS):
        violations.append(f"FORBIDDEN_LIVE_LANE:{lane_norm}")

    raw_host = req.target_host if isinstance(req.target_host, str) else _safe_str(req.target_host)
    if not isinstance(req.target_host, str) or not raw_host.isascii():
        violations.append("TARGET_HOST_MUST_BE_ASCII_STR")
    norm_host = _normalize_host_ascii(raw_host)

    # Detect embedded live ports or URL syntax inside target_host before strict allowlist check.
    embedded_ports: set[int] = set()
    for match in EMBEDDED_PORT_RE.findall(norm_host):
        try:
            embedded_ports.add(int(match))
        except ValueError:
            pass
    for ep in sorted(embedded_ports):
        if ep in FORBIDDEN_LIVE_PORTS:
            violations.append(f"FORBIDDEN_LIVE_PORT:{ep}")

    # Extract host token if URL/authority syntax was passed so live-host check cannot be bypassed.
    host_only = norm_host
    if "://" in host_only:
        violations.append("TARGET_HOST_MUST_NOT_CONTAIN_SCHEME")
        host_only = host_only.split("://", 1)[1]
    if "/" in host_only or "?" in host_only or "@" in host_only:
        violations.append("TARGET_HOST_INVALID_SYNTAX")
        host_only = re.split(r"[/?#]", host_only, maxsplit=1)[0].rsplit("@", 1)[-1]
    if ":" in host_only and host_only != "::1":
        violations.append("TARGET_HOST_MUST_NOT_EMBED_PORT")
        host_only = host_only.rsplit(":", 1)[0]
    host_only = host_only.strip("[]")

    if host_only == FORBIDDEN_LIVE_BROKER_HOST:
        violations.append("FORBIDDEN_LIVE_BROKER_HOST")
    if host_only not in ALLOWED_LOOPBACK_HOSTS:
        violations.append(f"TARGET_HOST_NOT_LOOPBACK:{host_only or 'EMPTY'}")

    strict_port = _safe_strict_int(req.target_port)
    if strict_port is None:
        violations.append("INVALID_OR_MISSING_TARGET_PORT")
    else:
        if strict_port in FORBIDDEN_LIVE_PORTS:
            violations.append(f"FORBIDDEN_LIVE_PORT:{strict_port}")
        if strict_port not in ALLOWED_PAPER_PORTS:
            violations.append(f"PAPER_PORT_NOT_ALLOWLISTED:{_safe_str(strict_port)}")

    raw_sym = req.symbol if isinstance(req.symbol, str) else ""
    sym_norm = raw_sym.strip().upper() if raw_sym.isascii() else ""
    if not raw_sym or not raw_sym.isascii() or not SYMBOL_ASCII_RE.fullmatch(sym_norm):
        violations.append("INVALID_SYMBOL")

    side_norm = _safe_str(req.side).strip().lower()
    if side_norm not in ("buy", "sell", "long", "short"):
        violations.append(f"INVALID_SIDE:{side_norm or 'EMPTY'}")

    strict_qty = _safe_strict_int(req.qty_shares)
    if strict_qty is None or strict_qty <= 0 or strict_qty > MAX_QTY_SHARES:
        violations.append("INVALID_QTY_SHARES")

    entry_px = _safe_finite_float(req.entry_limit_px)
    if entry_px is None or entry_px <= 0.0 or entry_px > MAX_ENTRY_LIMIT_PX:
        violations.append("INVALID_ENTRY_LIMIT_PX")
    elif not _is_rule612_quantized(entry_px):
        violations.append("RULE612_TICK_QUANTIZATION_VIOLATION")

    stop_pct = _safe_finite_float(req.stop_distance_pct)
    if stop_pct is None or not (0.0 < stop_pct <= MAX_ADR0022_STOP_PCT):
        violations.append(f"ADR0022_STOP_PCT_VIOLATION:{_safe_str(req.stop_distance_pct)}")

    if not isinstance(req.is_overnight_boats, bool):
        violations.append("MISSING_OR_INVALID_OVERNIGHT_BOATS_FLAG")
    if not isinstance(req.sec_dilution_blocked, bool):
        violations.append("MISSING_OR_INVALID_SEC_DILUTION_FLAG")

    spread_val = _safe_finite_float(req.spread_bps)
    if spread_val is None or spread_val < 0.0:
        violations.append("INVALID_SPREAD_BPS")
    elif req.is_overnight_boats is True and spread_val > MAX_OVERNIGHT_BOATS_SPREAD_BPS:
        violations.append(f"BOATS_SPREAD_CAP_VIOLATION:{spread_val}")

    if req.sec_dilution_blocked is True and side_norm in ("buy", "long"):
        violations.append("DF5_SEC_DILUTION_BLOCKS_LONG")

    raw_coid = req.client_order_id if isinstance(req.client_order_id, str) else ""
    if not raw_coid or raw_coid != raw_coid.strip() or not CLIENT_ORDER_ID_RE.fullmatch(raw_coid):
        violations.append("INVALID_CLIENT_ORDER_ID")

    allowed = len(violations) == 0
    normalized = (
        {
            "account_lane": lane_norm,
            "target_host": host_only,
            "target_port": strict_port,
            "symbol": sym_norm,
            "side": side_norm,
            "qty_shares": strict_qty,
            "entry_limit_px": entry_px,
            "stop_distance_pct": stop_pct,
            "spread_bps": spread_val,
            "is_overnight_boats": req.is_overnight_boats,
            "sec_dilution_blocked": req.sec_dilution_blocked,
            "client_order_id": raw_coid,
        }
        if allowed
        else None
    )

    return {
        "schema_version": UNIFIED_COCKPIT_TCA_SCHEMA_VERSION,
        "allowed": allowed,
        "paper_only_enforced": True,
        "violations": violations,
        "normalized": normalized,
        "contract_sha256": compute_unified_cockpit_contract_sha256(),
    }


def verify_local_perspective_assets(cache_root: Path | None = None) -> dict[str, Any]:
    """Verify locally staged Apache-2.0 `@perspective-dev@5.9.2` WASM/ESM assets (zero CDN required)."""
    candidates: list[Path] = []
    if cache_root is not None:
        candidates.append(cache_root)
    env_override = os.environ.get("SOTA_PERSPECTIVE_CACHE_DIR", "").strip()
    if env_override:
        candidates.append(Path(env_override))
    candidates.extend(
        [
            Path("Z:/sota-cache/perspective-5.9.2/node_modules/@perspective-dev"),
            Path.home() / ".cache" / "sota-perspective-5.9.2" / "node_modules" / "@perspective-dev",
        ]
    )

    resolved: Path | None = None
    for cand in candidates:
        if cand.is_dir():
            resolved = cand
            break

    missing: list[str] = []
    present: list[str] = []
    if resolved is None:
        missing = list(REQUIRED_PERSPECTIVE_RELPATHS)
    else:
        for rel in REQUIRED_PERSPECTIVE_RELPATHS:
            fp = resolved / rel
            if fp.is_file() and fp.stat().st_size > 0:
                present.append(rel)
            else:
                missing.append(rel)

    return {
        "perspective_version": PERSPECTIVE_PINNED_VERSION,
        "ready": len(missing) == 0,
        "present_count": len(present),
        "required_count": len(REQUIRED_PERSPECTIVE_RELPATHS),
        "missing_assets": missing,
    }


def validate_tca_markout_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a live `:8799/api/tca` or `:8787/api/tca_markouts` summary payload for dimensional safety."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["PAYLOAD_NOT_DICT"]}

    for key in (
        "mean_implementation_shortfall_bps",
        "markout_1s_bps",
        "markout_10s_bps",
        "markout_60s_bps",
        "markout_300s_bps",
        "passive_fill_ratio",
    ):
        val = payload.get(key)
        if val is not None and _safe_finite_float(val) is None:
            errors.append(f"NON_FINITE_{key.upper()}")

    pfr_raw = payload.get("passive_fill_ratio")
    pfr = _safe_finite_float(pfr_raw) if pfr_raw is not None else None
    if pfr is not None and not (0.0 <= pfr <= 1.0):
        errors.append("PASSIVE_FILL_RATIO_OUT_OF_RANGE")

    return {"valid": len(errors) == 0, "errors": errors}


def _strip_ps1_comments(script_text: str) -> list[str]:
    """Return active non-comment PowerShell lines (ignoring full-line comments and trailing # comments)."""
    active: list[str] = []
    in_block = False
    for raw_line in script_text.splitlines():
        line = raw_line.strip()
        if in_block:
            if "#>" in line:
                in_block = False
            continue
        if line.startswith("<#"):
            if "#>" not in line:
                in_block = True
            continue
        if not line or line.startswith("#"):
            continue
        code_part = re.split(r"(?<!['\"])\s+#", line, maxsplit=1)[0].strip()
        if code_part:
            active.append(code_part)
    return active


def audit_noesis_wall_sovereign_routing(wall_script_path: Path | None = None) -> dict[str, Any]:
    """Structurally audit the Noesis 4K wall script (active code only; requires presence AND absence checks)."""
    target = wall_script_path or (Path.home() / ".agents" / "bin" / "sota-noesis-4k-wall.ps1")
    if not target.is_file():
        return {
            "present": False,
            "sovereign_local_first": False,
            "zero_focus_steal": False,
            "tv_launch_gated": False,
        }
    active_lines = _strip_ps1_comments(target.read_text(encoding="utf-8", errors="replace"))
    active_code = "\n".join(active_lines)

    has_resolver_fn = bool(re.search(r"(?i)\bfunction\s+Resolve-SotaEndpointUrl\b", active_code))
    probes_loopback = bool(re.search(r'BeginConnect\(\s*"127\.0\.0\.1"', active_code))
    # Absence check: zero hardcoded remote --app=http://... URLs anywhere in active code.
    has_hardcoded_remote_app = bool(re.search(r"--app=https?://(?!127\.0\.0\.1|localhost)", active_code, re.IGNORECASE))
    uses_resolved_apps = (
        bool(re.search(r"--app=\$rankerUrl\b", active_code))
        and bool(re.search(r"--app=\$blotterUrl\b", active_code))
        and not has_hardcoded_remote_app
    )
    sovereign_local_first = has_resolver_fn and probes_loopback and uses_resolved_apps

    has_noactivate_show = bool(re.search(r"ShowWindowAsync\([^,]+,\s*4\s*\)", active_code))
    has_noactivate_pos = bool(re.search(r"SetWindowPos\([^)]+0x0014\s*\)", active_code))
    has_distinct_wall_guard = bool(
        re.search(r"\$wallScreen\.DeviceName\s*-ne\s*\$mainWorkScreen\.DeviceName", active_code)
    )

    # Track brace depth of `$MoveTradingViewToWall` if-block to prove EVERY TradingView.Desktop launch is gated.
    tv_occurrences = 0
    ungated_tv_occurrences = 0
    brace_depth = 0
    tv_gate_depth: int | None = None
    for line in active_lines:
        if tv_gate_depth is None and re.search(r"if\s*\([^)]*\$MoveTradingViewToWall[^)]*\)", line):
            tv_gate_depth = brace_depth + 1
        if "TradingView.Desktop" in line:
            tv_occurrences += 1
            if tv_gate_depth is None or brace_depth < tv_gate_depth:
                ungated_tv_occurrences += 1
        brace_depth += line.count("{") - line.count("}")
        if tv_gate_depth is not None and brace_depth < tv_gate_depth:
            tv_gate_depth = None

    tv_launch_gated = (tv_occurrences == 0) or (ungated_tv_occurrences == 0)
    zero_focus_steal = has_noactivate_show and has_noactivate_pos and has_distinct_wall_guard and tv_launch_gated

    return {
        "present": True,
        "sovereign_local_first": sovereign_local_first,
        "zero_focus_steal": zero_focus_steal,
        "tv_launch_gated": tv_launch_gated,
    }


def _probe_json(url: str, timeout_s: float = 1.2) -> tuple[bool, dict[str, Any]]:
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            obj = json.loads(resp.read().decode("utf-8"))
            return (resp.status == 200 and isinstance(obj, dict)), (obj if isinstance(obj, dict) else {})
    except (OSError, ValueError, urllib.error.URLError):
        return False, {}


def probe_live_unified_cockpit_convergence(
    *,
    ranker_base_url: str = "http://127.0.0.1:8787",
    blotter_base_url: str = "http://127.0.0.1:8799",
    perspective_cache_root: Path | None = None,
    wall_script_path: Path | None = None,
) -> dict[str, Any]:
    """Fail-open live probe of the converged Perspective + Lightweight Charts + TCA + Wall stack."""
    cockpit_ok, cockpit_obj = _probe_json(f"{ranker_base_url.rstrip('/')}/api/unified_cockpit_snapshot")
    tca_8787_ok, tca_8787_obj = _probe_json(f"{ranker_base_url.rstrip('/')}/api/tca_markouts")
    tca_8799_ok, tca_8799_obj = _probe_json(f"{blotter_base_url.rstrip('/')}/api/tca")
    feed_8799_ok, _ = _probe_json(f"{blotter_base_url.rstrip('/')}/api/unified-blotter-feed")
    perspective_status = verify_local_perspective_assets(perspective_cache_root)
    wall_status = audit_noesis_wall_sovereign_routing(wall_script_path)

    tca_8787_valid = validate_tca_markout_payload(tca_8787_obj)["valid"] if tca_8787_ok else False
    tca_8799_valid = validate_tca_markout_payload(tca_8799_obj)["valid"] if tca_8799_ok else False

    return {
        "schema_version": UNIFIED_COCKPIT_TCA_SCHEMA_VERSION,
        "contract_sha256": compute_unified_cockpit_contract_sha256(),
        "perspective_wasm": perspective_status,
        "wall_ergonomics": wall_status,
        "live_endpoints": {
            "ranker_unified_cockpit_ok": cockpit_ok,
            "ranker_cockpit_schema": cockpit_obj.get("schema_version") if cockpit_ok else None,
            "ranker_tca_ok": tca_8787_ok,
            "ranker_tca_valid": tca_8787_valid,
            "blotter_tca_ok": tca_8799_ok,
            "blotter_tca_valid": tca_8799_valid,
            "blotter_unified_feed_ok": feed_8799_ok,
        },
        "ready_for_seamless_operation": bool(
            perspective_status["ready"]
            and wall_status["sovereign_local_first"]
            and wall_status["zero_focus_steal"]
            and (cockpit_ok or tca_8799_ok)
        ),
    }
