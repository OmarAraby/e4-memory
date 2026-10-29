#!/usr/bin/env python3
"""
read_guard.py — e4 PreToolUse hook (Read | Grep | Glob): deny reads that burn context for nothing.

Denies, with a reason that says how to proceed:
  * Read of a file matching PATTERNS below (lockfiles, minified bundles, build/dependency dirs,
    .git internals, the vault Archive/) or of an old .ai-memory/sessions/ file (only the newest
    session is useful context);
  * Read of any file over MAX_BYTES unless offset/limit (or pages) is given;
  * Grep/Glob aimed at a denied directory (Grep on a single lockfile stays allowed: it is the cheap
    way to look one package up).

Per-project tuning: .claude/e4-read-guard.txt — one glob per line, `#` comments, `!glob` to ALLOW
something PATTERNS denies (e.g. `!bin/**` for a repo whose bin/ holds real scripts).
Escape hatch: E4_READ_GUARD=off. Any error -> allow (exit 0). Stdlib only.

Globs are gitignore-like: no "/" -> matches the file name anywhere; otherwise anchored at the
project root; `**/` = any directories. Matching is case-insensitive on Windows.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MAX_BYTES = 200 * 1024
DEPS = "dependency/vendor code - use the package's docs or your own source, or ask the user"
BUILD = "build output - read the source instead, or ask the user"
LOCK = "lockfile - Grep it for the one package you need instead of reading it whole"

# (glob, reason) — edit freely; a project can override with .claude/e4-read-guard.txt
PATTERNS: list[tuple[str, str]] = [
    ("Archive/**", "archived memory - ask the user if something from the archive is needed"),
    ("**/node_modules/**", DEPS),
    ("**/.git/**", "git internals - use git commands instead"),
    ("**/dist/**", BUILD), ("**/build/**", BUILD), ("**/bin/**", BUILD), ("**/obj/**", BUILD),
    ("*.min.js", "minified bundle - read the unminified source instead"),
    ("*.min.mjs", "minified bundle - read the unminified source instead"),
    ("*.min.css", "minified stylesheet - read the unminified source instead"),
] + [(name, LOCK) for name in (
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb",
    "poetry.lock", "Pipfile.lock", "uv.lock", "Cargo.lock", "composer.lock", "Gemfile.lock",
    "go.sum", "packages.lock.json", "mix.lock", "pubspec.lock", "flake.lock",
)]
DIR_PATTERNS = {"Archive/**", "**/node_modules/**", "**/.git/**", "**/dist/**", "**/build/**",
                "**/bin/**", "**/obj/**"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}  # cost isn't size-proportional
SESSION_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}-.+\.md$")
HOW = "If it is really needed, ask the user (they can allow it via .claude/e4-read-guard.txt or E4_READ_GUARD=off)."
FLAGS = re.IGNORECASE if os.name == "nt" else 0


def glob_regex(pattern: str) -> re.Pattern:
    if "/" not in pattern.rstrip("/"):
        pattern = "**/" + pattern
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out, FLAGS)


def load_rules(root: Path) -> tuple[list[tuple[re.Pattern, str, str]], list[re.Pattern]]:
    deny = [(glob_regex(p), p, reason) for p, reason in PATTERNS]
    allow = []
    custom = root / ".claude" / "e4-read-guard.txt"
    if custom.is_file():
        for line in custom.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("!"):
                allow.append(glob_regex(line[1:].strip()))
            else:
                deny.append((glob_regex(line), line, "listed in .claude/e4-read-guard.txt"))
    return deny, allow


def rel_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def match_rule(rel: str, deny, allow, dirs_only: bool = False) -> str | None:
    if any(a.fullmatch(rel) for a in allow):
        return None
    for regex, pattern, reason in deny:
        if dirs_only and pattern not in DIR_PATTERNS:
            continue
        if regex.fullmatch(rel):
            return reason
    return None


def old_session(path: Path) -> str | None:
    """Return the newest session's name if `path` is an older .ai-memory/sessions/ file."""
    if path.parent.name != "sessions" or path.parent.parent.name != ".ai-memory" \
            or not SESSION_NAME.match(path.name):
        return None
    names = sorted(p.name for p in path.parent.glob("*.md") if SESSION_NAME.match(p.name))
    return names[-1] if names and path.name != names[-1] else None


def vault_archive(path: Path) -> bool:
    vault = os.environ.get("AI_VAULT")
    if not vault:
        return False
    try:
        path.relative_to(Path(vault).resolve() / "Archive")
        return True
    except ValueError:
        return False


def check_read(inp: dict, root: Path, deny, allow) -> str | None:
    raw = inp.get("file_path")
    if not raw:
        return None
    path = Path(os.path.abspath(Path(root, raw)))
    rel = rel_posix(path, root)
    reason = match_rule(rel, deny, allow) or \
        ("archived memory - ask the user if something from the archive is needed" if vault_archive(path) else None)
    if reason:
        return f"{rel}: {reason}. {HOW}"
    newest = old_session(path)
    if newest and not any(a.fullmatch(rel) for a in allow):
        return (f"{rel} is an old session file; only the newest ({newest}) is useful context. "
                "Ask the user if older session history is really needed.")
    sliced = any(inp.get(k) not in (None, "") for k in ("offset", "limit", "pages"))
    if not sliced and path.suffix.lower() not in IMAGE_EXT and path.is_file():
        size = path.stat().st_size
        if size > MAX_BYTES:
            return (f"{rel} is {size // 1024} KB. Read a slice with offset/limit (e.g. limit: 300), "
                    "or Grep for what you need first.")
    return None


def check_search(base_path: str | None, glob_pattern: str, root: Path, deny, allow) -> str | None:
    """Deny a Grep/Glob whose search root (path, plus a Glob pattern's literal prefix) is a denied dir."""
    base = Path(os.path.abspath(Path(root, base_path or ".")))
    targets = [base]
    literal = []
    for part in glob_pattern.split("/"):
        if not part or any(ch in part for ch in "*?[{"):
            break
        literal.append(part)
    if literal:
        targets.append(Path(os.path.abspath(base.joinpath(*literal))))
    for target in targets:
        if target.is_file():
            continue  # single files: Grep on a lockfile is the cheap path, allow it
        rel = rel_posix(target, root)
        probe = "x" if rel == "." else rel + "/x"
        reason = match_rule(probe, deny, allow, dirs_only=True) or             ("archived memory - ask the user if something from the archive is needed" if vault_archive(target / "x") else None)
        if reason:
            return f"{rel}/: {reason}. {HOW}"
    return None


def main() -> int:
    if os.environ.get("E4_READ_GUARD", "").lower() == "off":
        return 0
    event = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace") or "{}")
    tool = event.get("tool_name")
    inp = event.get("tool_input") or {}
    root = Path(os.path.abspath(event.get("cwd") or os.getcwd()))
    deny, allow = load_rules(root)
    if tool == "Read":
        reason = check_read(inp, root, deny, allow)
    elif tool == "Glob":
        reason = check_search(inp.get("path"), str(inp.get("pattern") or ""), root, deny, allow)
    elif tool == "Grep":
        reason = check_search(inp.get("path"), "", root, deny, allow)
    else:
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "[e4 read-guard] " + reason,
        }}))
    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception:  # fail open: never block a read the guard didn't understand
        pass
    sys.exit(0)
