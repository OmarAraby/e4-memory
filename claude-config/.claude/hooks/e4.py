#!/usr/bin/env python3
"""
e4.py — project-relative launcher for the e4 automation scripts, used by the /e4:* commands.

Why it exists (verified against Claude Code 2.1.312):
  * A command's !`...` line may not contain shell variables — the permission checker rejects
    `$AI_MEMORY_PYDIR/...` and `${X:-default}` — so commands call this fixed relative path and
    the script lookup happens here instead.
  * $ARGUMENTS is pasted into the shell text BEFORE bash parses it, so `"$ARGUMENTS"` would let
    quotes, backticks or $(...) in user input execute. Commands pass arguments through a quoted
    heredoc on stdin instead; an argument of `-` is replaced with that stdin text.
  * A non-zero exit aborts the whole command, so this launcher always exits 0 and reports
    failures on stdout, where the model can see and relay them.

Usage:  python3 .claude/hooks/e4.py <task|session|status> [args...]   (`-` = read value from stdin)
Must not contain bookkeeping logic — that lives in the scripts it launches.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

TOOLS = {"task": "e4_task.py", "session": "e4_session.py", "status": "generate_status.py"}


def search_dirs() -> list[Path]:
    dirs = []
    if os.environ.get("AI_MEMORY_PYDIR"):
        dirs.append(Path(os.environ["AI_MEMORY_PYDIR"]))
    if os.environ.get("AI_VAULT"):
        dirs.append(Path(os.environ["AI_VAULT"]) / "automation" / "python")
    dirs += [Path.home() / "AI-Vault" / "automation" / "python", Path.cwd() / "scripts",
             Path(__file__).resolve().parent]
    return dirs


def main() -> int:
    out = sys.stdout
    if len(sys.argv) < 2 or sys.argv[1] not in TOOLS:
        print(f"e4: error: usage: e4.py <{'|'.join(TOOLS)}> [args...]", file=out)
        return 0
    script = next((d / TOOLS[sys.argv[1]] for d in search_dirs() if (d / TOOLS[sys.argv[1]]).is_file()), None)
    if script is None:
        print(f"e4: error: {TOOLS[sys.argv[1]]} not found. Set AI_MEMORY_PYDIR to "
              f"<AI-Vault>/automation/python (searched: {', '.join(map(str, search_dirs()))}).", file=out)
        return 0
    args = sys.argv[2:]
    if "-" in args:
        stdin_text = sys.stdin.buffer.read().decode("utf-8", errors="replace").strip()
        args = [stdin_text if a == "-" else a for a in args]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        proc = subprocess.run([sys.executable, str(script), *args], capture_output=True, env=env, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"e4: error: could not run {script.name}: {exc}", file=out)
        return 0
    text = (proc.stdout + proc.stderr).decode("utf-8", errors="replace").rstrip()
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:  # never abort the calling command
        print(f"e4: error: {exc}")
        raise SystemExit(0)
