# B0rd-hooks

Public MIT installer for B0RD **agent monitoring** IDE lifecycle hooks.

Wires [Cursor](https://cursor.com), [Claude Code](https://code.claude.com), [OpenAI Codex](https://developers.openai.com/codex), and [Google Antigravity](https://antigravity.google) hook events to the companion publish pipeline in [`b0rd-scene-agent-monitor`](https://github.com/Anthus-Microelectronics/b0rd-scene-agent-monitor) (`notify.show` + `source=agent`).

## Quick start

Clone the companion next to B0RD (or anywhere), then install **user-level** hooks (default):

```bash
git clone https://github.com/Anthus-Microelectronics/b0rd-scene-agent-monitor.git ~/Projects/b0rd-scene-agent-monitor

pip install git+https://github.com/Anthus-Microelectronics/B0rd-hooks.git
# or from a checkout: pip install -e /path/to/B0rd-hooks

b0rd-hooks doctor
b0rd-hooks install
```

Verify on the desk sign:

```bash
tail -f /tmp/b0rd-agent-hook-payload.log
```

## Commands

| Command | Purpose |
| --- | --- |
| `b0rd-hooks install` | Install hooks (default: `--scope user`, Cursor only in v0.1) |
| `b0rd-hooks install --scope project --workspace /path/to/repo` | Project hooks (required for Cursor cloud/private-worker agents) |
| `b0rd-hooks uninstall` | Remove b0rd-managed hook entries only |
| `b0rd-hooks status` | Show installed IDEs and config paths |
| `b0rd-hooks doctor` | Check companion checkout and `python3` |

### Options

- `--companion-root` — path to `b0rd-scene-agent-monitor` (or set `B0RD_AGENT_COMPANION_ROOT`)
- `--ides cursor claude codex antigravity` — filter IDEs (Claude/Codex/Antigravity: phase 2+)

## IDE config paths

| IDE | User | Project |
| --- | --- | --- |
| Cursor | `~/.cursor/hooks.json` | `.cursor/hooks.json` |
| Claude Code | `~/.claude/settings.json` | `.claude/settings.json` |
| Codex | `~/.codex/hooks.json` | `.codex/hooks.json` |
| Antigravity | `~/.gemini/config/hooks.json` | `.agents/hooks.json` |

**v0.1** implements Cursor install/uninstall. Other IDEs are planned; the CLI accepts `--ides` but skips unimplemented targets.

## Cloud Cursor agents

User hooks are **not** loaded in cloud/private-worker runs. For those workspaces:

```bash
cd /path/to/B0RD
b0rd-hooks install --scope project --workspace .
```

Use a **project-relative** companion clone or set `B0RD_AGENT_COMPANION_ROOT` in the environment.

## Development

```bash
python3 -m pytest
pip install -e ".[dev]"
```

## License

MIT — see [LICENSE](LICENSE). Desk notify publish logic remains in `b0rd-scene-agent-monitor` (PolyForm Perimeter).
