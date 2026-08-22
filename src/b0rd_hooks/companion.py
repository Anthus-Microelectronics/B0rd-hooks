"""Resolve path to b0rd-scene-agent-monitor companion checkout."""

from __future__ import annotations

import os
from pathlib import Path

COMPANION_DIRNAME = "b0rd-scene-agent-monitor"
HOOK_SCRIPT = "adapters/cursor/b0rd-agent-notify.sh"
CORE_HOOK = "core/hook.py"


def default_search_roots(cwd: Path | None = None) -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("B0RD_AGENT_COMPANION_ROOT", "").strip()
    if env:
        roots.append(Path(env).expanduser())
    home_projects = Path.home() / "Projects"
    roots.append(home_projects / COMPANION_DIRNAME)
    if cwd:
        roots.append(cwd.parent / COMPANION_DIRNAME)
        roots.append(cwd / COMPANION_DIRNAME)
    return roots


def is_companion_root(path: Path) -> bool:
    return (path / CORE_HOOK).is_file() and (path / HOOK_SCRIPT).is_file()


def resolve_companion_root(explicit: str | None = None, cwd: Path | None = None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not is_companion_root(root):
            raise FileNotFoundError(f"Not a companion checkout: {root}")
        return root
    for candidate in default_search_roots(cwd):
        if is_companion_root(candidate):
            return candidate.resolve()
    raise FileNotFoundError(
        "b0rd-scene-agent-monitor not found. Clone it or pass --companion-root "
        "or set B0RD_AGENT_COMPANION_ROOT."
    )


def cursor_adapter_command(companion_root: Path) -> str:
    return str((companion_root / HOOK_SCRIPT).resolve())
