#!/usr/bin/env python3
"""CLI for installing B0RD agent-notify hooks into IDEs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from b0rd_hooks import __version__
from b0rd_hooks.companion import cursor_adapter_command, resolve_companion_root
from b0rd_hooks.ide import IMPLEMENTED, normalize_ides
from b0rd_hooks.ide import cursor as cursor_mod
from b0rd_hooks.state import load_state, remove_install, save_state, upsert_install


def _cmd_install(args: argparse.Namespace) -> int:
    ides = normalize_ides(args.ides)
    skipped = [i for i in (args.ides or []) if i.lower() not in IMPLEMENTED]
    for name in skipped:
        print(f"skip: {name} installer not implemented yet (phase 2+)", file=sys.stderr)

    workspace = Path(args.workspace).resolve() if args.workspace else None
    if args.scope == "project" and workspace is None:
        workspace = Path.cwd()

    try:
        companion = resolve_companion_root(args.companion_root, cwd=workspace or Path.cwd())
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    command = cursor_adapter_command(companion)
    state = load_state()
    state.companion_root = str(companion)

    for ide in ides:
        if ide == "cursor":
            record = cursor_mod.install(args.scope, command, workspace=workspace)
            upsert_install(state, record)
            print(f"ok: cursor ({args.scope}) -> {record.config_path}")
            print(f"    command: {command}")
        else:
            print(f"skip: {ide} not implemented", file=sys.stderr)

    save_state(state)
    return 0


def _cmd_uninstall(args: argparse.Namespace) -> int:
    ides = normalize_ides(args.ides)
    workspace = Path(args.workspace).resolve() if args.workspace else None
    if args.scope == "project" and workspace is None:
        workspace = Path.cwd()

    state = load_state()
    for ide in ides:
        if ide == "cursor":
            if cursor_mod.uninstall(args.scope, workspace=workspace):
                print(f"ok: removed cursor hooks ({args.scope})")
            else:
                print(f"ok: no cursor b0rd hooks found ({args.scope})")
            remove_install(state, ide, args.scope)
        else:
            print(f"skip: {ide} not implemented", file=sys.stderr)
    save_state(state)
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve() if args.workspace else None
    state = load_state()
    if state.companion_root:
        print(f"companion: {state.companion_root}")
    for ide in normalize_ides(args.ides or list(IMPLEMENTED)):
        if ide == "cursor":
            for scope in ("user", "project"):
                if args.scope and args.scope != scope:
                    continue
                ws = workspace if scope == "project" else None
                if scope == "project" and ws is None:
                    continue
                info = cursor_mod.status(scope, workspace=ws)
                flag = "yes" if info["installed"] else "no"
                print(f"cursor/{scope}: {flag} ({info['config_path']}) events={len(info['events'])}")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    ok = True
    try:
        companion = resolve_companion_root(args.companion_root)
        print(f"companion: {companion}")
        print(f"adapter:  {cursor_adapter_command(companion)}")
    except FileNotFoundError as exc:
        print(f"companion: MISSING ({exc})")
        ok = False

    import shutil

    if shutil.which("python3"):
        print("python3: ok")
    else:
        print("python3: missing")
        ok = False

    user = cursor_mod.status("user")
    print(f"cursor/user: {'installed' if user['installed'] else 'not installed'}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="b0rd-hooks", description="Install B0RD agent-notify IDE hooks")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--scope",
            choices=("user", "project"),
            default="user",
            help="user (default) or project install",
        )
        p.add_argument(
            "--ides",
            nargs="+",
            choices=("cursor", "claude", "codex", "antigravity"),
            help="IDEs to target (default: implemented IDEs only)",
        )
        p.add_argument("--companion-root", help="Path to b0rd-scene-agent-monitor checkout")
        p.add_argument("--workspace", help="Project root for --scope project")

    p_install = sub.add_parser("install", help="Install hooks")
    add_common(p_install)
    p_install.set_defaults(func=_cmd_install)

    p_uninstall = sub.add_parser("uninstall", help="Remove b0rd-managed hooks")
    add_common(p_uninstall)
    p_uninstall.set_defaults(func=_cmd_uninstall)

    p_status = sub.add_parser("status", help="Show install status")
    add_common(p_status)
    p_status.set_defaults(func=_cmd_status)

    p_doctor = sub.add_parser("doctor", help="Check companion and toolchain")
    p_doctor.add_argument("--companion-root", help="Path to b0rd-scene-agent-monitor checkout")
    p_doctor.set_defaults(func=_cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
