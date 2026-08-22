import json
from pathlib import Path

import pytest

from b0rd_hooks.companion import is_companion_root, resolve_companion_root
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


def test_resolve_companion_explicit(tmp_path: Path) -> None:
    companion = tmp_path / "companion"
    (companion / "core").mkdir(parents=True)
    (companion / "core" / "hook.py").write_text("", encoding="utf-8")
    adapter = companion / "adapters" / "cursor"
    adapter.mkdir(parents=True)
    (adapter / "b0rd-agent-notify.sh").write_text("", encoding="utf-8")
    root = resolve_companion_root(str(companion))
    assert is_companion_root(root)
