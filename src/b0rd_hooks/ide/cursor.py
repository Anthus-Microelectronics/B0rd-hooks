"""Cursor hooks.json install target."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from b0rd_hooks.state import InstallRecord, is_b0rd_command

CURSOR_VERSION = 1
CURSOR_TIMEOUT = 15

CURSOR_EVENTS: tuple[str, ...] = (
    "sessionStart",
    "sessionEnd",
    "beforeSubmitPrompt",
    "preToolUse",
    "postToolUse",
    "postToolUseFailure",
    "subagentStart",
    "subagentStop",
    "beforeShellExecution",
    "afterShellExecution",
    "beforeMCPExecution",
    "afterMCPExecution",
    "beforeReadFile",
    "afterFileEdit",
    "preCompact",
    "afterAgentThought",
    "afterAgentResponse",
    "stop",
)


def config_path(scope: str, workspace: Path | None = None) -> Path:
    if scope == "user":
        return Path.home() / ".cursor" / "hooks.json"
    if scope == "project":
        if workspace is None:
            raise ValueError("workspace required for project scope")
        return workspace / ".cursor" / "hooks.json"
    raise ValueError(f"unknown scope: {scope}")


def _hook_entry(command: str) -> dict[str, Any]:
    return {"command": command, "timeout": CURSOR_TIMEOUT}


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


def install(scope: str, command: str, workspace: Path | None = None) -> InstallRecord:
    path = config_path(scope, workspace)
    doc = _load_json(path)
    if "version" not in doc:
        doc["version"] = CURSOR_VERSION
    hooks = doc.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        doc["hooks"] = hooks

    entry = _hook_entry(command)
    installed_events: list[str] = []
    for event in CURSOR_EVENTS:
        existing = hooks.get(event)
        if not isinstance(existing, list):
            existing = []
        filtered = [h for h in existing if isinstance(h, dict) and not is_b0rd_command(str(h.get("command", "")))]
        filtered.append(entry)
        hooks[event] = filtered
        installed_events.append(event)

    _write_json(path, doc)
    return InstallRecord(
        ide="cursor",
        scope=scope,
        config_path=str(path),
        command=command,
        events=installed_events,
    )


def uninstall(scope: str, workspace: Path | None = None) -> bool:
    path = config_path(scope, workspace)
    doc = _load_json(path)
    hooks = doc.get("hooks")
    if not isinstance(hooks, dict):
        return False
    changed = False
    for event in list(hooks.keys()):
        items = hooks.get(event)
        if not isinstance(items, list):
            continue
        filtered = [h for h in items if isinstance(h, dict) and not is_b0rd_command(str(h.get("command", "")))]
        if len(filtered) != len(items):
            changed = True
        if filtered:
            hooks[event] = filtered
        else:
            del hooks[event]
            changed = True
    if changed:
        if hooks:
            doc["hooks"] = hooks
            _write_json(path, doc)
        elif path.is_file():
            path.unlink()
    return changed


def status(scope: str, workspace: Path | None = None) -> dict[str, Any]:
    path = config_path(scope, workspace)
    doc = _load_json(path)
    hooks = doc.get("hooks") if isinstance(doc.get("hooks"), dict) else {}
    present = [e for e in CURSOR_EVENTS if _has_b0rd(hooks.get(e))]
    return {"config_path": str(path), "installed": bool(present), "events": present}


def _has_b0rd(items: Any) -> bool:
    if not isinstance(items, list):
        return False
    return any(isinstance(h, dict) and is_b0rd_command(str(h.get("command", ""))) for h in items)
