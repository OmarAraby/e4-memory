#!/usr/bin/env python3
"""
archive_completed_tasks.py — Move completed task files from a project's
.ai-memory/tasks/ to the global vault Archive/tasks/.

A task is "completed" if its front-matter has `status: done` (or all checklist
items in '## Acceptance Criteria' are checked, when --infer is used).

Usage:
    python archive_completed_tasks.py --project ~/code/myapp --vault ~/AI-Vault
    python archive_completed_tasks.py --project . --vault ~/AI-Vault --dry-run
"""
from __future__ import annotations
import argparse
import datetime as dt
import re
import shutil
from pathlib import Path


def is_done(text: str, infer: bool) -> bool:
    fm = re.search(r"^status:\s*(\w[\w-]*)", text, flags=re.MULTILINE)
    if fm and fm.group(1).lower() in {"done", "completed", "closed"}:
        return True
    if infer:
        crit = re.search(r"## Acceptance Criteria(.*?)(?=^## |\Z)", text,
                         flags=re.MULTILINE | re.DOTALL)
        if crit:
            boxes = re.findall(r"- \[( |x|X)\]", crit.group(1))
            if boxes and all(b.lower() == "x" for b in boxes):
                return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--infer", action="store_true",
                    help="Also archive if all acceptance criteria are checked")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tasks_dir = Path(args.project).expanduser().resolve() / ".ai-memory" / "tasks"
    archive_dir = Path(args.vault).expanduser().resolve() / "Archive" / "tasks"
    if not tasks_dir.exists():
        print(f"No tasks dir at {tasks_dir}")
        return 0
    archive_dir.mkdir(parents=True, exist_ok=True)

    proj = Path(args.project).resolve().name
    moved = 0
    for task in sorted(tasks_dir.glob("*.md")):
        text = task.read_text(encoding="utf-8", errors="ignore")
        if is_done(text, args.infer):
            stamp = dt.date.today().isoformat()
            dest = archive_dir / f"{proj}__{task.stem}__archived-{stamp}.md"
            if args.dry_run:
                print(f"[dry-run] would move {task.name} -> {dest.name}")
            else:
                shutil.move(str(task), str(dest))
                print(f"archived {task.name} -> {dest.name}")
            moved += 1
    print(f"\n{'Would archive' if args.dry_run else 'Archived'} {moved} task(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
