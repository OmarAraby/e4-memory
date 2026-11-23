#!/usr/bin/env python3
"""
e4_session.py — Write the mechanical skeleton of a session file so /e4:end-session's model only
has to fill in the judgment sections.

Owns: collecting git facts (file NAMES only, never diff contents) and writing
.ai-memory/sessions/YYYY-MM-DD-HHMMSS-<branch>.md with `<!-- e4:fill ... -->` placeholders.
Must NOT write a TL;DR: an unfilled draft has to stay "incomplete" to the hooks, which treat a
file as logged only if it has a TL;DR and no `e4:fill TL;DR` marker.

Usage:
    python3 e4_session.py draft [--project PATH] [--note TEXT]

Prints the session file path, then one line per in-progress task. Re-running before the draft is
filled rewrites that same draft (fresh facts, same name) instead of piling up new files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_status import parse_task  # noqa: E402  (sibling module, path set above)

SESSION_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2}-\d{6})-.+\.md$")
FILL_TLDR = "<!-- e4:fill TL;DR -->"
MAX_FILES = 40
MAX_COMMITS = 15

DRAFT = """---
type: session
date: {date}
branch: {branch}
---
## Session — {date}
**Time**: ended {time}
**Branch**: {branch}
{note}
**TL;DR**: {fill_tldr}

**Did**:
<!-- e4:fill Did -->

**Decisions**: <!-- e4:fill Decisions -->

**State**: <!-- e4:fill State -->

**Blockers**: <!-- e4:fill Blockers -->

**Next actions**:
<!-- e4:fill Next actions -->

**Checkpoint**:
```
last_command: <!-- e4:fill last_command -->
working_file: {working_file}
test_status: <!-- e4:fill pass|fail|not run -->
uncommitted_changes: {uncommitted}
```

**Files changed** (from git):
{files}

**Commits since last session**:
{commits}
"""


def git(root: Path, *args: str) -> str:
    """Run git in root; return stdout, or "" if git is missing or the command fails."""
    try:
        proc = subprocess.run(["git", "-c", "core.quotepath=false", "-C", str(root), *args],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=15)
    except (OSError, subprocess.SubprocessError):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def current_branch(root: Path) -> str:
    if not git(root, "rev-parse", "--is-inside-work-tree").strip():
        return "nogit"
    # symbolic-ref also works before the first commit, where rev-parse HEAD fails.
    return (git(root, "symbolic-ref", "--short", "-q", "HEAD").strip()
            or git(root, "rev-parse", "--short", "HEAD").strip() or "nogit")


def status_paths(porcelain: str) -> list[str]:
    paths = []
    for line in porcelain.splitlines():
        if len(line) > 3:
            path = line[3:]
            paths.append(path.split(" -> ", 1)[-1].strip('"'))  # renames: keep the new name
    return paths


def bullets(items: list[str], cap: int, empty: str) -> str:
    if not items:
        return f"- {empty}"
    shown = [f"- {i}" for i in items[:cap]]
    if len(items) > cap:
        shown.append(f"- ... and {len(items) - cap} more")
    return "\n".join(shown)


def session_files(sessions: Path) -> list[Path]:
    return sorted(p for p in sessions.glob("*.md") if SESSION_NAME.match(p.name)) if sessions.is_dir() else []


def cmd_draft(root: Path, note: str) -> int:
    mem = root / ".ai-memory"
    sessions = mem / "sessions"
    now = dt.datetime.now()
    branch = current_branch(root)
    branch_san = re.sub(r"[^A-Za-z0-9]", "-", branch)

    existing = session_files(sessions)
    newest = existing[-1] if existing else None
    if newest and newest.name.endswith(f"-{branch_san}.md") and \
            FILL_TLDR in newest.read_text(encoding="utf-8", errors="ignore"):
        path = newest  # unfilled draft from an earlier run: refresh it in place
        previous = existing[-2] if len(existing) > 1 else None
    else:
        path = sessions / f"{now:%Y-%m-%d-%H%M%S}-{branch_san}.md"
        previous = newest

    if previous is not None:
        since = dt.datetime.strptime(SESSION_NAME.match(previous.name).group(1), "%Y-%m-%d-%H%M%S")
    else:
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
    since_arg = f"--since={since:%Y-%m-%d %H:%M:%S}"

    porcelain = git(root, "status", "--porcelain")
    changed = status_paths(porcelain)
    changed += git(root, "diff", "--name-only", "HEAD").splitlines()
    changed += git(root, "log", since_arg, "--name-only", "--pretty=format:").splitlines()
    self_path = path.relative_to(root).as_posix()  # a refreshed draft must not list itself
    files = sorted({f.strip() for f in changed if f.strip() and f.strip() != self_path})
    commits = git(root, "log", since_arg, "--oneline", f"-n{MAX_COMMITS}").splitlines()
    working = next((p for p in status_paths(porcelain)
                    if not p.startswith(".ai-memory/") and not p.endswith("/")), "")

    note = " ".join(note.split())
    text = DRAFT.format(
        date=now.date().isoformat(), time=f"{now:%H:%M}", branch=branch,
        note=f"**User note**: {note}\n" if note else "",
        fill_tldr=FILL_TLDR, working_file=working,
        uncommitted="yes" if porcelain.strip() else "no",
        files=bullets(files, MAX_FILES, "none"),
        commits=bullets(commits, MAX_COMMITS, "none"),
    )
    sessions.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

    print(path.relative_to(root).as_posix())
    tasks_dir = mem / "tasks"
    active = [parse_task(f) for f in sorted(tasks_dir.glob("*.md"))] if tasks_dir.is_dir() else []
    active = [t for t in active if t["status"] == "in-progress"]
    for t in active:
        print(f"in-progress: {t['id']} - {t['title']}")
    if not active:
        print("in-progress: none")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="e4 session-file skeleton (no model needed)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("draft", help="write a session file with judgment placeholders")
    p.add_argument("--project", default=".", help="project root (contains .ai-memory/)")
    p.add_argument("--note", default="", help="the user's note for this session")
    args = ap.parse_args()

    root = Path(args.project).expanduser().resolve()
    if not (root / ".ai-memory").is_dir():
        print(f"e4: error: no .ai-memory/ in {root}. Run /e4:init first.")
        return 1
    return cmd_draft(root, args.note)


if __name__ == "__main__":
    raise SystemExit(main())
