"""IDE registry — v1 ships Cursor; others are stubs for future phases."""

from __future__ import annotations

from b0rd_hooks.ide import cursor as cursor_mod

SUPPORTED = ("cursor", "claude", "codex", "antigravity")
IMPLEMENTED = frozenset({"cursor", "antigravity"})


def normalize_ides(ides: list[str] | None) -> list[str]:
    if not ides:
        return [i for i in SUPPORTED if i in IMPLEMENTED]
    out: list[str] = []
    for raw in ides:
        key = raw.strip().lower()
        if key in SUPPORTED and key not in out:
            out.append(key)
    return out
