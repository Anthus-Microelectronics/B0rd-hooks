import json
from pathlib import Path

import pytest

from b0rd_hooks.companion import is_companion_root, resolve_companion_root
from b0rd_hooks.ide import antigravity as antigravity_mod
from b0rd_hooks.ide import codex as codex_mod
from b0rd_hooks.ide import cursor as cursor_mod
from b0rd_hooks.state import is_b0rd_command


def test_is_b0rd_command() -> None:
    assert is_b0rd_command("/path/b0rd-agent-notify.sh")
    assert not is_b0rd_command("/other/script.sh")


def test_cursor_install_user(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    companion = tmp_path / "companion"
    (companion / "core").mkdir(parents=True)
    (companion / "core" / "hook.py").write_text("# stub\n", encoding="utf-8")
    adapter = companion / "adapters" / "cursor"
    adapter.mkdir(parents=True)
    (adapter / "b0rd-agent-notify.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    command = str((adapter / "b0rd-agent-notify.sh").resolve())
    record = cursor_mod.install("user", command)
    assert record.ide == "cursor"
    path = Path(record.config_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["hooks"]["stop"][0]["command"] == command

    assert cursor_mod.status("user")["installed"] is True
    cursor_mod.uninstall("user")
    assert cursor_mod.status("user")["installed"] is False


def test_antigravity_install_user(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    companion = tmp_path / "companion"
    (companion / "core").mkdir(parents=True)
    (companion / "core" / "hook.py").write_text("# stub\n", encoding="utf-8")
    (companion / "core" / "agy_hook.py").write_text("# stub\n", encoding="utf-8")
    adapter = companion / "adapters" / "antigravity"
    adapter.mkdir(parents=True)
    (adapter / "b0rd-agent-notify.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    command = str((adapter / "b0rd-agent-notify.sh").resolve())
    record = antigravity_mod.install("user", command)
    assert record.ide == "antigravity"
    path = Path(record.config_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    group = data["b0rd-agent-monitor"]
    assert group["PreToolUse"][0]["matcher"] == "*"
    assert group["PreToolUse"][0]["hooks"][0]["command"] == f"{command} PreToolUse"
    assert group["Stop"][0]["command"] == f"{command} Stop"

    assert antigravity_mod.status("user")["installed"] is True
    antigravity_mod.uninstall("user")
    assert antigravity_mod.status("user")["installed"] is False


def test_codex_install_user(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    companion = tmp_path / "companion"
    (companion / "core").mkdir(parents=True)
    (companion / "core" / "hook.py").write_text("# stub\n", encoding="utf-8")
    adapter = companion / "adapters" / "codex"
    adapter.mkdir(parents=True)
    (adapter / "b0rd-agent-notify.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    command = str((adapter / "b0rd-agent-notify.sh").resolve())
    record = codex_mod.install("user", command)
    assert record.ide == "codex"
    path = Path(record.config_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    group = data["hooks"]["PreToolUse"][0]
    assert group["matcher"] == "*"
    assert group["hooks"][0]["command"] == command
    assert data["hooks"]["Stop"][0]["hooks"][0]["command"] == command

    assert codex_mod.status("user")["installed"] is True
    codex_mod.uninstall("user")
    assert codex_mod.status("user")["installed"] is False


def test_resolve_companion_explicit(tmp_path: Path) -> None:
    companion = tmp_path / "companion"
    (companion / "core").mkdir(parents=True)
    (companion / "core" / "hook.py").write_text("", encoding="utf-8")
    adapter = companion / "adapters" / "cursor"
    adapter.mkdir(parents=True)
    (adapter / "b0rd-agent-notify.sh").write_text("", encoding="utf-8")
    root = resolve_companion_root(str(companion))
    assert is_companion_root(root)
