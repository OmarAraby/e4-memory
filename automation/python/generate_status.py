#!/usr/bin/env python3
"""
generate_status.py — Regenerate .ai-memory/active-tasks.md from the task files.

Tier-3: active-tasks.md is a GENERATED VIEW (gitignored), so parallel branches never conflict
on it. The source of truth is .ai-memory/tasks/*.md — each task's frontmatter `status` drives
which bucket it lands in. Run it after changing a task, or let the SessionStart hook run it.

Statuses (frontmatter `status:`): in-progress → Current · todo → Next Up · blocked → Blocked ·
in-review → In Review · done → counted toward completion.

Usage:
    python generate_status.py --project /path/to/repo
    python generate_status.py --project .
"""
from __future__ import annotations
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

TODAY = dt.date.today().isoformat()


def parse_task(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")

    def fm(key: str, default: str = "", strip_comment: bool = False) -> str:
        m = re.search(rf"^{key}\s*:\s*(.+?)\s*$", text, flags=re.MULTILINE | re.IGNORECASE)
        if not m:
            return default
        val = m.group(1).strip().strip('"').strip("'")
        if strip_comment:
            # Drop a trailing YAML comment, e.g. `status: in-review   # todo | in-progress | ...`.
            # The /e4:new-task template SHIPS that comment, so a task whose status was later changed
            # without also deleting the comment used to fall through to the `todo` bucket silently —
            # the value never matched a bucket key and buckets.get(...) defaulted. That mis-filed
            # every in-progress / in-review / blocked task as "Next Up".
            #
            # Opt-in per field, NOT global: a title may legitimately contain '#' ("C#", "issue #123"),
            # and requiring whitespace before the '#' keeps those intact even here.
            val = re.split(r"\s+#", val, maxsplit=1)[0].strip()
        return val or default

    status = fm("status", "todo", strip_comment=True).lower()
    title = fm("title")
    if not title:
        m = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
        title = m.group(1).strip() if m else path.stem
    return {
        "id": fm("id") or path.stem,
        "title": title,
        "status": status,
        "priority": fm("priority", "medium", strip_comment=True).lower(),
        "file": path.name,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    args = ap.parse_args()

    mem = Path(args.project).expanduser().resolve() / ".ai-memory"
    tasks_dir = mem / "tasks"
    tasks = [parse_task(f) for f in sorted(tasks_dir.glob("*.md"))] if tasks_dir.is_dir() else []

    buckets: dict[str, list[dict]] = {
        "in-progress": [], "todo": [], "blocked": [], "in-review": [], "done": [],
    }
    # Bucket, and WARN on anything unrecognised. The silent fallback below is load-bearing (a task
    # must never vanish from the board just because its status is odd), but silence was also how a
    # template-shipped trailing comment kept 57 tasks mis-filed as "Next Up" for months. Unknown
    # statuses are now reported to stderr, named, so the next run surfaces them instead of absorbing
    # them. Exit status is unaffected — this is a hint, not a failure.
    unknown = [t for t in tasks if t["status"] not in buckets]
    for t in unknown:
        print(
            # ASCII only: this goes to a Windows cp1252 stderr under the SessionStart hook, where a
            # non-ASCII character (an em dash, originally) raises UnicodeEncodeError and takes the
            # whole hook down with it.
            f"warning: {t['file']}: unrecognised status {t['status']!r} - filed under 'todo'. "
            f"Expected one of: {', '.join(buckets)}.",
            file=sys.stderr,
        )
    for t in tasks:
        buckets.get(t["status"], buckets["todo"]).append(t)

    total = len(tasks)
    done = len(buckets["done"])
    pct = round(done / total * 100) if total else 0

    def line(t: dict) -> str:
        return f"- **{t['id']}** — {t['title']} _(priority: {t['priority']})_ → `tasks/{t['file']}`"

    def section(title: str, items: list[dict], empty: str) -> str:
        body = "\n".join(line(t) for t in items) if items else f"> {empty}"
        return f"## {title}\n{body}\n"

    parts = [
        f"---\ntags: [project, tasks, active, memory, generated]\ntype: active-tasks\nupdated: {TODAY}\n---\n",
        "# Active Tasks\n",
        "> ⚙️ GENERATED from `tasks/*.md` by `generate_status.py` — **do not edit by hand.**\n"
        "> Change a task's `status:` in its `tasks/` file. This file is gitignored and regenerated per session.\n",
        f"**Tasks:** {done}/{total} done ({pct}%)\n",
        section("🎯 Current Task", buckets["in-progress"], "None in progress."),
        section("🔜 Next Up", buckets["todo"], "Nothing queued."),
        section("🚧 Blocked", buckets["blocked"], "None."),
        section("👀 In Review", buckets["in-review"], "None."),
        section("✅ Done (recent)", buckets["done"][-5:], "None yet."),
    ]
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "active-tasks.md").write_text("\n".join(parts), encoding="utf-8")
    print(f"Regenerated {mem / 'active-tasks.md'} - {total} task(s), {done} done ({pct}%).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
