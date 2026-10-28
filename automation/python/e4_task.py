#!/usr/bin/env python3
"""
e4_task.py — Create tasks and change their status without spending model tokens.

Owns the task-file template and the status/checkpoint bookkeeping for .ai-memory/tasks/*.md.
Does NOT render the active-tasks view itself — it calls generate_status.regenerate() for that.

Usage:
    python3 e4_task.py new "Wire gRPC notification" [--project PATH] [--priority high]
    python3 e4_task.py set-status TASK-20260624-164530 in-progress [--note "picked up"] [--project PATH]

Output is one line (the created path / the result), so a slash command can embed it cheaply.
Exit status: 0 on success, 1 on a user error (bad id, empty title) with the reason on stdout.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_status import regenerate  # noqa: E402  (sibling module, path set above)

STATUSES = ("todo", "in-progress", "blocked", "in-review", "done")
PRIORITIES = ("low", "medium", "high", "critical")

# The task shape generate_status.py parses: id / title / status / priority front-matter.
# Allowed statuses live on their own comment line, NOT as a trailing comment on `status:` —
# a stale trailing comment once mis-filed tasks for months (see generate_status.parse_task).
TASK_TEMPLATE = """---
id: {id}
title: "{fm_title}"
status: todo
# status: todo | in-progress | blocked | in-review | done
priority: {priority}
created: {today}
---
# {title}
## Goal
## Context
## Acceptance Criteria
- [ ] ...
## Implementation Plan
## Files Likely Affected
## Checkpoints
## Blockers
## Notes / Log
- {today}: Created.
"""


def slugify(title: str) -> str:
    """Return an ASCII slug (max 50 chars); non-ASCII-only titles fall back to 'task'."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:50].rstrip("-") or "task"


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def cmd_new(root: Path, title: str, priority: str) -> int:
    # `/e4:new-task Title -- extra detail`: only the part before ' -- ' is the title; the command's
    # model step turns the detail into acceptance criteria. Whitespace/newlines are collapsed.
    title = " ".join(title.split(" -- ", 1)[0].split())
    if not title:
        print("e4: error: empty task title. Usage: /e4:new-task <title> [-- details]")
        return 1
    now = dt.datetime.now()
    task_id = f"TASK-{now:%Y%m%d-%H%M%S}-{slugify(title)}"
    path = root / ".ai-memory" / "tasks" / f"{task_id}.md"
    if path.exists():  # same title within the same second: re-running is a no-op
        print(rel(path, root))
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        TASK_TEMPLATE.format(
            id=task_id,
            # generate_status strips only the outer quotes, so an inner " would leak into the view.
            fm_title=title.replace('"', "'"),
            title=title,
            priority=priority,
            today=now.date().isoformat(),
        ),
        encoding="utf-8",
    )
    regenerate(root)
    print(rel(path, root))
    return 0


def find_task(root: Path, task_id: str) -> Path | None:
    """Resolve a full id, an id without slug (TASK-YYYYMMDD-HHMMSS), or a file name."""
    tasks = root / ".ai-memory" / "tasks"
    key = Path(task_id).stem
    exact = tasks / f"{key}.md"
    if exact.is_file():
        return exact
    matches = sorted(tasks.glob(f"{key}*.md")) if tasks.is_dir() else []
    return matches[0] if len(matches) == 1 else None


def set_front_matter_status(text: str, status: str) -> tuple[str, str]:
    """Return (new_text, old_status). Only the leading front-matter block is touched."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, flags=re.DOTALL)
    if not m:
        return f"---\nstatus: {status}\n---\n" + text, ""
    fm = m.group(1)
    sm = re.search(r"^status\s*:\s*(.*)$", fm, flags=re.MULTILINE)
    old = re.split(r"\s+#", sm.group(1), maxsplit=1)[0].strip().strip("\"'").lower() if sm else ""
    if sm:
        fm_new = fm[: sm.start()] + f"status: {status}" + fm[sm.end():]
    else:
        fm_new = fm + f"\nstatus: {status}"
    return text[: m.start(1)] + fm_new + text[m.end(1):], old


def append_checkpoint(text: str, line: str) -> str:
    """Append `line` as the last entry of the ## Checkpoints section (created if missing)."""
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines) if re.match(r"^##\s+Checkpoints\b", l)), None)
    if start is None:
        return text.rstrip("\n") + f"\n\n## Checkpoints\n{line}\n"
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    insert_at = end
    while insert_at - 1 > start and not lines[insert_at - 1].strip():
        insert_at -= 1  # keep the blank lines that separate sections
    lines.insert(insert_at, line)
    return "\n".join(lines)


def cmd_set_status(root: Path, task_id: str, status: str, note: str) -> int:
    path = find_task(root, task_id)
    if path is None:
        print(f"e4: error: no unique task matches {task_id!r} in .ai-memory/tasks/")
        return 1
    text = path.read_text(encoding="utf-8")
    new_text, old = set_front_matter_status(text, status)
    note = " ".join(note.split())
    if old == status and not note:
        print(f"{path.stem}: already {status}")
        return 0
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"- {stamp} status: {old or '?'} -> {status}" + (f" ({note})" if note else "")
    path.write_text(append_checkpoint(new_text, entry), encoding="utf-8")
    regenerate(root)
    print(f"{path.stem}: {old or '?'} -> {status}")
    return 0


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", default=".", help="project root (contains .ai-memory/)")
    ap = argparse.ArgumentParser(description="e4 task bookkeeping (no model needed)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new", parents=[common],
                           help="create a task file and regenerate active-tasks.md")
    p_new.add_argument("title")
    p_new.add_argument("--priority", default="medium", choices=PRIORITIES)
    p_set = sub.add_parser("set-status", parents=[common],
                           help="change a task's status and log a checkpoint")
    p_set.add_argument("task_id")
    p_set.add_argument("status", choices=STATUSES)
    p_set.add_argument("--note", default="")
    args = ap.parse_args()

    root = Path(args.project).expanduser().resolve()
    if not (root / ".ai-memory").is_dir():
        print(f"e4: error: no .ai-memory/ in {root}. Run /e4:init first.")
        return 1
    if args.cmd == "new":
        return cmd_new(root, args.title, args.priority)
    return cmd_set_status(root, args.task_id, args.status, args.note)


if __name__ == "__main__":
    raise SystemExit(main())
