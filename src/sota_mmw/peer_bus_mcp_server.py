"""Tracked Canonical SOTA Peer-Bus JSON-RPC 2.0 MCP Server (`v3.10.0`, Protocol `2025-03-26`).

Enforces:
- Strict JSON-RPC 2.0 notification silence: requests lacking `id`, having `id is None`, or invoking
  `notifications/*` return `None` and emit zero stdout bytes (eliminating spurious `{"id": null}` errors).
- Structured `isError: True` recovery on malformed or failing `tools/call` invocations so stdio stays alive.
- Protobuf-safe `TOOLS` schemas (`0` array `"default"` properties) covering all 9 `sota_bus_*` operations.
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections.abc import Callable
from typing import Any

TOOLS: list[dict[str, Any]] = [
    {
        "name": "sota_bus_status",
        "description": "Inspect active SQLite WAL peer leases, handovers, unread inbox count, and HLZ trial N / t*(N+1).",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}}},
    },
    {
        "name": "sota_bus_claim_lease",
        "description": "Acquire or release an atomic disjoint path-glob lease in peer_bus.db before mutating a repo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "agent_family": {"type": "string"},
                "session_id": {"type": "string"},
                "paths": {"type": "array", "items": {"type": "string"}},
                "intent": {"type": "string"},
                "ttl_minutes": {"type": "integer"},
                "release": {"type": "boolean"},
            },
            "required": ["repo"],
        },
    },
    {
        "name": "sota_bus_sync_handover",
        "description": "Read or write structured repository handover state across peer sessions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "agent_family": {"type": "string"},
                "done": {"type": "string"},
                "verified_by": {"type": "string"},
                "open_risks": {"type": "string"},
                "next_priority": {"type": "string"},
            },
            "required": ["repo"],
        },
    },
    {
        "name": "sota_bus_peer_message",
        "description": "Send a cross-peer message or read inbox messages from SQLite WAL peer_bus.db.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["send", "inbox"], "default": "send"},
                "sender": {"type": "string"},
                "recipient": {"type": "string"},
                "repo": {"type": "string"},
                "body": {"type": "string"},
                "peek": {"type": "boolean"},
            },
        },
    },
    {
        "name": "sota_bus_record_lesson",
        "description": "Record an E0-E4 root-cause lesson into peer_bus.db and lessons ledger.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string"},
                "title": {"type": "string"},
                "root_cause": {"type": "string"},
                "enforced_by": {"type": "string"},
                "evidence_grade": {"type": "string"},
            },
            "required": ["domain", "title", "root_cause", "enforced_by"],
        },
    },
    {
        "name": "sota_bus_preregister_hypothesis",
        "description": "Lock an immutable SHA-256 pre-registered quantitative hypothesis prior to OOS evaluation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "hypothesis_id": {"type": "string"},
                "title": {"type": "string"},
                "spec_text": {"type": "string"},
                "fit_daily_sigma": {"type": "number"},
                "held_out_days": {"type": "integer"},
            },
            "required": ["repo", "hypothesis_id", "title", "spec_text"],
        },
    },
    {
        "name": "sota_bus_record_outcome",
        "description": "Record clustered t-stat, DSR, and 1x/2x net return outcome against a pre-registered hypothesis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hypothesis_id": {"type": "string"},
                "t_stat_clustered": {"type": "number"},
                "net_return_1x_bps": {"type": "number"},
                "net_return_2x_bps": {"type": "number"},
                "events_count": {"type": "integer"},
                "distinct_dates": {"type": "integer"},
                "dsr": {"type": "number"},
                "notes": {"type": "string"},
            },
            "required": [
                "hypothesis_id",
                "t_stat_clustered",
                "net_return_1x_bps",
                "net_return_2x_bps",
                "events_count",
                "distinct_dates",
            ],
        },
    },
    {
        "name": "sota_bus_search_memory",
        "description": "FTS5 BM25 recall across lessons, handovers, pre-registered hypotheses, and MADR 4.0 ADRs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
                "refresh": {"type": "boolean"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "sota_bus_assign_worker",
        "description": "1-call multi-model task assignment with FTS5+qmd memory brief and disjoint lease.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "goal": {"type": "string"},
                "worker": {"type": "string"},
                "surface": {"type": "string"},
                "sender_session": {"type": "string"},
                "paths": {"type": "array", "items": {"type": "string"}},
                "claim_lease": {"type": "boolean"},
            },
            "required": ["repo", "goal"],
        },
    },
]


def _default_bus_module() -> Any:
    bus_dir = pathlib.Path.home() / ".agents" / "bus"
    if bus_dir.is_dir() and str(bus_dir) not in sys.path:
        sys.path.insert(0, str(bus_dir))
    import importlib

    return importlib.import_module("sota_bus_engine")


def _dispatch_tool(name: str, args: dict[str, Any], bus_module: Any) -> dict[str, Any]:
    conn = bus_module.get_conn()
    try:
        if name == "sota_bus_status":
            return dict(bus_module.bus_status(conn, repo=str(args.get("repo") or "")))
        if name in ("sota_bus_claim_lease", "sota_bus_claim_work"):
            return dict(
                bus_module.claim_or_release_work(
                    conn,
                    repo=str(args["repo"]),
                    agent_family=str(args.get("agent_family") or "mcp"),
                    session_id=str(args.get("session_id") or "mcp-session"),
                    paths=list(args.get("paths") or ["*"]),
                    intent=str(args.get("intent") or "mcp_work"),
                    ttl_minutes=int(args.get("ttl_minutes") or 45),
                    release=bool(args.get("release", False)),
                )
            )
        if name in ("sota_bus_sync_handover", "sota_bus_handover_sync"):
            done = str(args.get("done") or "")
            return dict(
                bus_module.sync_handover(
                    conn,
                    repo=str(args["repo"]),
                    agent_family=str(args.get("agent_family") or "mcp"),
                    done=done,
                    verified_by=str(args.get("verified_by") or ""),
                    open_risks=str(args.get("open_risks") or "none"),
                    next_priority=str(args.get("next_priority") or ""),
                    read_only=not bool(done.strip()),
                )
            )
        if name == "sota_bus_peer_message":
            action = str(args.get("action") or ("send" if args.get("body") else "inbox"))
            if action == "send":
                return dict(
                    bus_module.post_peer_message(
                        conn,
                        sender=str(args.get("sender") or "mcp"),
                        recipient=str(args.get("recipient") or "*"),
                        repo=str(args.get("repo") or "native-agent-stack"),
                        body=str(args["body"]),
                    )
                )
            return dict(
                bus_module.poll_peer_inbox(
                    conn,
                    consumer_id=str(args.get("recipient") or "mcp"),
                    mark_delivered=not bool(args.get("peek", True)),
                )
            )
        if name == "sota_bus_record_lesson":
            return dict(
                bus_module.record_lesson(
                    conn,
                    domain=str(args["domain"]),
                    title=str(args["title"]),
                    root_cause=str(args["root_cause"]),
                    enforced_by=str(args["enforced_by"]),
                    evidence_grade=str(args.get("evidence_grade") or "E4"),
                )
            )
        if name == "sota_bus_preregister_hypothesis":
            return dict(
                bus_module.preregister_hypothesis(
                    conn,
                    repo=str(args["repo"]),
                    hypothesis_id=str(args["hypothesis_id"]),
                    title=str(args["title"]),
                    spec_text=str(args["spec_text"]),
                    fit_daily_sigma=float(args["fit_daily_sigma"]) if args.get("fit_daily_sigma") is not None else 0.0,
                    held_out_days=int(args["held_out_days"]) if args.get("held_out_days") is not None else 0,
                )
            )
        if name == "sota_bus_record_outcome":
            dsr_raw = args.get("dsr")
            return dict(
                bus_module.record_hypothesis_outcome(
                    conn,
                    hypothesis_id=str(args["hypothesis_id"]),
                    t_stat_clustered=float(args["t_stat_clustered"]),
                    net_return_1x_bps=float(args["net_return_1x_bps"]),
                    net_return_2x_bps=float(args["net_return_2x_bps"]),
                    events_count=int(args["events_count"]),
                    distinct_dates=int(args["distinct_dates"]),
                    dsr=float(dsr_raw) if dsr_raw is not None else None,
                    notes=str(args.get("notes") or ""),
                )
            )
        if name == "sota_bus_search_memory":
            return dict(
                bus_module.search_memory(
                    conn,
                    str(args["query"]),
                    limit=int(args.get("limit") or 10),
                    refresh_repo_docs=bool(args.get("refresh", True)),
                )
            )
        if name == "sota_bus_assign_worker":
            return dict(
                bus_module.assign_multi_model_worker(
                    conn,
                    repo=str(args["repo"]),
                    goal=str(args["goal"]),
                    worker=str(args.get("worker") or "auto"),
                    placement=str(args.get("surface") or "auto"),
                    callback_to=str(args.get("sender_session") or "mcp"),
                    paths=list(args.get("paths") or ["*"]),
                    execute=bool(args.get("claim_lease", True)),
                )
            )
        raise KeyError(f"Unknown tool: {name}")
    finally:
        conn.close()


def handle_jsonrpc_message(
    req: dict[str, Any],
    *,
    bus_module: Any = None,
    tool_dispatcher: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Process one JSON-RPC 2.0 frame; return `None` for notifications (never emit `id: null`)."""
    method = str(req.get("method") or "")
    has_id = "id" in req and req.get("id") is not None
    if not has_id or method.startswith("notifications/"):
        return None
    rid = req["id"]

    if method == "initialize":
        req_ver = str((req.get("params") or {}).get("protocolVersion") or "2025-03-26")
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "protocolVersion": req_ver if req_ver in ("2024-11-05", "2025-03-26") else "2025-03-26",
                "serverInfo": {"name": "sota-peer-bus", "version": "3.10.0"},
                "capabilities": {"tools": {}},
            },
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = req.get("params") or {}
        t_name = str(params.get("name") or "")
        t_args = dict(params.get("arguments") or {})
        try:
            if tool_dispatcher is not None:
                data = tool_dispatcher(t_name, t_args)
            else:
                bm = bus_module if bus_module is not None else _default_bus_module()
                data = _dispatch_tool(t_name, t_args, bm)
            return {
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps(data, indent=2)}], "isError": False},
            }
        except Exception as exc:  # noqa: BLE001
            err_payload = {"ok": False, "error": str(exc), "tool": t_name}
            return {
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps(err_payload)}], "isError": True},
            }

    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Method not found: {method}"}}


def main() -> int:
    """Run the JSON-RPC 2.0 stdio loop with strict notification silence."""
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {exc}"}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()
            continue
        resp = handle_jsonrpc_message(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
