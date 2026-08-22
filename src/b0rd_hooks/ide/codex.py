"""OpenAI Codex hooks.json install target (~/.codex or .codex/)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from b0rd_hooks.state import InstallRecord, is_b0rd_command

CODEX_TIMEOUT = 15
STATUS_MESSAGE = "B0RD agent notify"

CODEX_EVENTS: tuple[str, ...] = (
    "SessionStart",
    "SessionEnd",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "PermissionRequest",
    "PreCompact",
    "PostCompact",
    "SubagentStart",
    "SubagentStop",
    "Stop",
)

MATCHER_EVENTS = frozenset(
    {
        "PreToolUse",
        "PostToolUse",
        "PermissionRequest",
        "SessionStart",
        "SubagentStart",
        "SubagentStop",
        "PreCompact",
        "PostCompact",
    }
)


def config_path(scope: str, workspace: Path | None = None) -> Path:
    if scope == "user":
        return Path.home() / ".codex" / "hooks.json"
    if scope == "project":
        if workspace is None:
            raise ValueError("workspace required for project scope")
        return workspace / ".codex" / "hooks.json"
    raise ValueError(f"unknown scope: {scope}")


def _handler(command: str) -> dict[str, Any]:
    return {
        "type": "command",
        "command": command,
        "timeout": CODEX_TIMEOUT,
        "statusMessage": STATUS_MESSAGE,
    }


def _event_group(command: str, event: str) -> dict[str, Any]:
    handler = _handler(command)
    if event in MATCHER_EVENTS:
        return {"matcher": "*", "hooks": [handler]}
    return {"hooks": [handler]}


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
    hooks = group.get("hooks")
    if isinstance(hooks, list):
        return any(isinstance(h, dict) and is_b0rd_command(str(h.get("command", ""))) for h in hooks)
    if is_b0rd_command(str(group.get("command", ""))):
        return True
    return False


def _filter_groups(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    kept: list[dict[str, Any]] = []
    for group in items:
        if not isinstance(group, dict):
            continue
        hooks = group.get("hooks")
        if not isinstance(hooks, list):
            if not _group_has_b0rd(group):
                kept.append(group)
            continue
        filtered = [
            h for h in hooks if isinstance(h, dict) and not is_b0rd_command(str(h.get("command", "")))
        ]
        if filtered:
            copy = dict(group)
            copy["hooks"] = filtered
            kept.append(copy)
    return kept


def _event_has_b0rd(items: Any) -> bool:
    if not isinstance(items, list):
        return False
    return any(_group_has_b0rd(group) for group in items)


def install(scope: str, command: str, workspace: Path | None = None) -> InstallRecord:
    path = config_path(scope, workspace)
    doc = _load_json(path)
    hooks = doc.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        doc["hooks"] = hooks

    installed_events: list[str] = []
    for event in CODEX_EVENTS:
        existing = hooks.get(event)
        filtered = _filter_groups(existing)
        filtered.append(_event_group(command, event))
        hooks[event] = filtered
        installed_events.append(event)

    if "description" not in doc:
        doc["description"] = "B0RD agent monitoring hooks (managed by b0rd-hooks)"
    _write_json(path, doc)
    return InstallRecord(
        ide="codex",
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
        filtered = _filter_groups(items)
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
    present = [e for e in CODEX_EVENTS if _event_has_b0rd(hooks.get(e))]
    return {"config_path": str(path), "installed": bool(present), "events": present}
