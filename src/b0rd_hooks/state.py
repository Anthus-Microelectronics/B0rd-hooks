"""Install state under ~/.config/b0rd-hooks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

STATE_DIR = Path.home() / ".config" / "b0rd-hooks"
STATE_FILE = STATE_DIR / "state.json"
MARKER = "b0rd-agent-notify.sh"


@dataclass
class InstallRecord:
    ide: str
    scope: str
    config_path: str
    command: str
    events: list[str] = field(default_factory=list)


@dataclass
class State:
    version: int = 1
    companion_root: str = ""
    installs: list[InstallRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "companion_root": self.companion_root,
            "installs": [asdict(i) for i in self.installs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> State:
        installs = [
            InstallRecord(**item) for item in data.get("installs", []) if isinstance(item, dict)
        ]
        return cls(
            version=int(data.get("version", 1)),
            companion_root=str(data.get("companion_root", "")),
            installs=installs,
        )


def load_state() -> State:
    if not STATE_FILE.is_file():
        return State()
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return State()
    if isinstance(data, dict):
        return State.from_dict(data)
    return State()


def save_state(state: State) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")


def is_b0rd_command(command: str) -> bool:
    return MARKER in (command or "")


def upsert_install(state: State, record: InstallRecord) -> None:
    state.installs = [i for i in state.installs if not (i.ide == record.ide and i.scope == record.scope)]
    state.installs.append(record)


def remove_install(state: State, ide: str, scope: str) -> InstallRecord | None:
    found: InstallRecord | None = None
    kept: list[InstallRecord] = []
    for item in state.installs:
        if item.ide == ide and item.scope == scope:
            found = item
        else:
            kept.append(item)
    state.installs = kept
    return found
