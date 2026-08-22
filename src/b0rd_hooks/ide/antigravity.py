"""Antigravity hooks.json install target (~/.gemini/config or .agents/)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from b0rd_hooks.state import InstallRecord, is_b0rd_command

HOOK_GROUP = "b0rd-agent-monitor"
AGY_TIMEOUT = 15

AGY_EVENTS: tuple[str, ...] = (
    "PreInvocation",
    "PostInvocation",
    "PreToolUse",
    "PostToolUse",
    "Stop",
)

TOOL_EVENTS = frozenset({"PreToolUse", "PostToolUse"})
FLAT_EVENTS = frozenset({"PreInvocation", "PostInvocation", "Stop"})


def config_path(scope: str, workspace: Path | None = None) -> Path:
    if scope == "user":
        return Path.home() / ".gemini" / "config" / "hooks.json"
    if scope == "project":
        if workspace is None:
            raise ValueError("workspace required for project scope")
        return workspace / ".agents" / "hooks.json"
    raise ValueError(f"unknown scope: {scope}")


def _command_for_event(command: str, event: str) -> str:
    return f"{command} {event}"


def _handler(command: str, event: str) -> dict[str, Any]:
    return {
        "type": "command",
        "command": _command_for_event(command, event),
        "timeout": AGY_TIMEOUT,
    }


def _event_block(command: str, event: str) -> dict[str, Any]:
    handler = _handler(command, event)
    if event in TOOL_EVENTS:
        return {"matcher": "*", "hooks": [handler]}
    return handler


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _group_has_b0rd(group: Any) -> bool:
    if not isinstance(group, dict):
        return False
    for event in AGY_EVENTS:
        items = group.get(event)
        if not isinstance(items, list):
            continue
        for item in items:
            if event in TOOL_EVENTS:
                hooks = item.get("hooks") if isinstance(item, dict) else None
                if not isinstance(hooks, list):
                    continue
                for handler in hooks:
                    if isinstance(handler, dict) and is_b0rd_command(str(handler.get("command", ""))):
                        return True
            elif isinstance(item, dict) and is_b0rd_command(str(item.get("command", ""))):
                return True
    return False


def install(scope: str, command: str, workspace: Path | None = None) -> InstallRecord:
    path = config_path(scope, workspace)
    doc = _load_json(path)
    group = doc.get(HOOK_GROUP)
    if not isinstance(group, dict):
        group = {}
    group["enabled"] = True

    installed_events: list[str] = []
    for event in AGY_EVENTS:
        group[event] = [_event_block(command, event)]
        installed_events.append(event)

    doc[HOOK_GROUP] = group
    _write_json(path, doc)
    return InstallRecord(
        ide="antigravity",
        scope=scope,
        config_path=str(path),
        command=command,
        events=installed_events,
    )


def uninstall(scope: str, workspace: Path | None = None) -> bool:
    path = config_path(scope, workspace)
    doc = _load_json(path)
    group = doc.get(HOOK_GROUP)
    if not isinstance(group, dict):
        return False
    if not _group_has_b0rd(group):
        return False
    del doc[HOOK_GROUP]
    if doc:
        _write_json(path, doc)
    elif path.is_file():
        path.unlink()
    return True


def status(scope: str, workspace: Path | None = None) -> dict[str, Any]:
    path = config_path(scope, workspace)
    doc = _load_json(path)
    group = doc.get(HOOK_GROUP)
    installed = _group_has_b0rd(group)
    events: list[str] = []
    if isinstance(group, dict) and installed:
        events = [e for e in AGY_EVENTS if group.get(e)]
    return {"config_path": str(path), "installed": installed, "events": events}
