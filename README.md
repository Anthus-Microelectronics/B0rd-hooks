# B0rd-hooks

Public MIT installer for B0RD **agent monitoring** IDE lifecycle hooks.

Wires [Cursor](https://cursor.com), [Claude Code](https://code.claude.com), [OpenAI Codex](https://developers.openai.com/codex), and [Google Antigravity](https://antigravity.google) hook events to the companion publish pipeline in [`b0rd-scene-agent-monitor`](https://github.com/Anthus-Microelectronics/B0rd-scene-agent-monitor) (`notify.show` + `source=agent`).

## Quick start

Clone the companion next to B0RD (or anywhere), then install **user-level** hooks (default):

```bash
git clone https://github.com/Anthus-Microelectronics/B0rd-scene-agent-monitor.git ~/Projects/b0rd-scene-agent-monitor

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
| `b0rd-hooks install` | Install hooks (default: `--scope user`, Cursor + Antigravity + Codex) |
| `b0rd-hooks install --scope project --workspace /path/to/repo` | Project hooks (required for Cursor cloud/private-worker agents) |
| `b0rd-hooks uninstall` | Remove b0rd-managed hook entries only |
| `b0rd-hooks status` | Show installed IDEs and config paths |
| `b0rd-hooks doctor` | Check companion checkout and `python3` |

### Options

- `--companion-root` — path to `b0rd-scene-agent-monitor` (or set `B0RD_AGENT_COMPANION_ROOT`)
- `--ides cursor antigravity codex claude` — filter IDEs (Claude: phase 2+)

## IDE config paths

| IDE | User | Project |
| --- | --- | --- |
| Cursor | `~/.cursor/hooks.json` | `.cursor/hooks.json` |
| Claude Code | `~/.claude/settings.json` | `.claude/settings.json` |
| Codex | `~/.codex/hooks.json` | `.codex/hooks.json` |
| Antigravity | `~/.gemini/config/hooks.json` | `.agents/hooks.json` |

**v0.3** implements Cursor, Antigravity, and Codex install/uninstall. Claude Code is planned.

Requires **b0rd-scene-agent-monitor** `develop` (2026-08-22+) for Antigravity session titles and rich tool messages.

### Antigravity

User-level hooks live in `~/.gemini/config/hooks.json` under the `b0rd-agent-monitor` group. Events: `PreInvocation`, `PostInvocation`, `PreToolUse`, `PostToolUse`, `Stop`. The adapter is fail-open (`PreToolUse` returns `{"decision":"allow"}`). See [Antigravity hooks docs](https://antigravity.google/docs/ide/hooks/).

```bash
b0rd-hooks install --ides antigravity --scope user
```

**Session titles:** the companion reads Antigravity's sidebar label from `~/.gemini/antigravity/agyhub_summaries_proto.pb` (keyed by hook `conversationId`), with transcript `# USER Objective:` as fallback — not the raw workspace folder name.

**Tool messages:** notifications use `toolSummary`, command lines, file paths, and search queries when present (e.g. `Shell · List open Kanbus issues` instead of `Tool · run_command`).

### Codex

User-level hooks live in `~/.codex/hooks.json` under the top-level `hooks` object. Events include `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, and `Stop`. The adapter prints `{}` on stdout (fail-open). See [Codex hooks docs](https://developers.openai.com/codex/hooks).

```bash
b0rd-hooks install --ides codex --scope user
```

After install, open Codex and run `/hooks` to **review and trust** the `b0rd-agent-notify` entries (Codex skips untrusted hooks silently).

**Session titles:** companion reads `thread_name` from `~/.codex/session_index.jsonl` by `session_id`, with prompt mining on `UserPromptSubmit` as fallback.

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
