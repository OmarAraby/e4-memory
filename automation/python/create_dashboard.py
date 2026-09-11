#!/usr/bin/env python3
"""
create_dashboard.py — Generate an Obsidian project dashboard note and refresh the
global Projects index, linking each project's .ai-memory to the vault.

Does two jobs:
  1. For a given project, writes <vault>/Projects/<project>.md  (index + dashboard)
  2. Optionally rebuilds <vault>/Projects/_Dashboard.md aggregating all projects.

Reads light metadata (phase, health, completion) from progress.md when available.

Usage:
    python create_dashboard.py --project ~/code/myapp --vault ~/AI-Vault
    python create_dashboard.py --vault ~/AI-Vault --rebuild-index --projects-root ~/code
"""
from __future__ import annotations
import argparse
import datetime as dt
import re
from pathlib import Path

TODAY = dt.date.today().isoformat()


def read_progress_meta(mem: Path) -> dict[str, str]:
    meta = {"phase": "?", "health": "?", "completion": "?"}
    pf = mem / "progress.md"
    if pf.exists():
        t = pf.read_text(encoding="utf-8", errors="ignore")
        if m := re.search(r"Phase:\s*(.+)", t):
            meta["phase"] = m.group(1).strip().strip("*")
        if m := re.search(r"Health:\s*(.+)", t):
            meta["health"] = m.group(1).strip().strip("*")
        if m := re.search(r"completion:\s*([\d~%]+)", t) or re.search(r"~(\d+)%", t):
            meta["completion"] = m.group(1).strip()
    return meta


def project_dashboard(name: str, project_path: Path, meta: dict) -> str:
    rel = project_path / ".ai-memory"
    return f"""---
tags: [project, dashboard]
type: project-index
status: active
updated: {TODAY}
---

# {name} — Dashboard

**Repo path**: `{project_path}`
**Memory**: `{rel}`
**Phase**: {meta['phase']} | **Health**: {meta['health']} | **Completion**: {meta['completion']}
**Updated**: {TODAY}

## Memory Files
- [[{name}/.ai-memory/onboarding|Onboarding]]
- [[{name}/.ai-memory/context|Context]]
- [[{name}/.ai-memory/architecture|Architecture]]
- [[{name}/.ai-memory/progress|Progress]]
- [[{name}/.ai-memory/decisions|Decisions]]
- [[{name}/.ai-memory/active-tasks|Active Tasks]]
- [[{name}/.ai-memory/sessions/README|Session History]]

## Open Tasks (Dataview)
```dataview
TASK
FROM "{name}"
WHERE !completed
GROUP BY status
```

## Recent Sessions (Dataview)
```dataview
TABLE file.mtime as "Modified"
FROM "{name}"
WHERE contains(file.name, "session")
SORT file.mtime DESC
LIMIT 5
```

## Tags
#project #status/active
"""


def rebuild_index(vault: Path, projects_root: Path) -> str:
    rows = []
    for memdir in list(projects_root.glob("*/.ai-memory")) + list(projects_root.glob("*/*/.ai-memory")):
        name = memdir.parent.name
        meta = read_progress_meta(memdir)
        rows.append(f"| [[{name}]] | {meta['phase']} | {meta['health']} | {meta['completion']} |")
    table = "\n".join(rows) if rows else "| _no projects found_ | | | |"
    return f"""---
tags: [projects, dashboard, index]
type: master-dashboard
updated: {TODAY}
---

# 📊 Projects Master Dashboard

Updated: {TODAY}

| Project | Phase | Health | Completion |
|---------|-------|--------|-----------|
{table}

## Active (Dataview)
```dataview
TABLE status, file.mtime as "Updated"
FROM "Projects"
WHERE type = "project-index"
SORT file.mtime DESC
```
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--project", help="Project root to (re)generate a dashboard for")
    ap.add_argument("--rebuild-index", action="store_true")
    ap.add_argument("--projects-root", help="Root of all projects (for --rebuild-index)")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    proj_dir = vault / "Projects"
    proj_dir.mkdir(parents=True, exist_ok=True)

    if args.project:
        p = Path(args.project).expanduser().resolve()
        meta = read_progress_meta(p / ".ai-memory")
        out = proj_dir / f"{p.name}.md"
        out.write_text(project_dashboard(p.name, p, meta), encoding="utf-8")
        print(f"Wrote project dashboard: {out}")

    if args.rebuild_index:
        root = Path(args.projects_root).expanduser().resolve() if args.projects_root \
            else vault.parent / "code"
        out = proj_dir / "_Dashboard.md"
        out.write_text(rebuild_index(vault, root), encoding="utf-8")
        print(f"Rebuilt master dashboard: {out}")

    if not args.project and not args.rebuild_index:
        print("Nothing to do. Pass --project and/or --rebuild-index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
