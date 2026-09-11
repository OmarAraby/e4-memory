#!/usr/bin/env python3
"""
init_project_memory.py — Scaffold a .ai-memory/ structure + CLAUDE.md in a project.

Usage:
    python init_project_memory.py /path/to/project --name "My Project"
    python init_project_memory.py .            # uses current dir, infers name

Idempotent: won't overwrite existing files unless --force is passed.

Tier-2: session history is one file per session under .ai-memory/sessions/
(never a single shared file), so branches never conflict on memory.
"""
from __future__ import annotations
import argparse
import datetime as dt
from pathlib import Path
import sys

TODAY = dt.date.today().isoformat()

FILES: dict[str, str] = {
    "onboarding.md": """---
tags: [project, onboarding, memory]
type: onboarding
updated: {today}
---

# 🚀 Onboarding — READ THIS FIRST

> Claude: read this completely before doing anything else.

## What is this project?
> One paragraph elevator pitch.

## How to read the memory (in order)
1. onboarding.md → 2. context.md → 3. architecture.md → 4. active-tasks.md → 5. progress.md → 6. decisions.md → 7. sessions/ (newest file)

## Golden Rules for this project
-

## Environment Setup
```bash
# how to run locally
```

## How to run tests
```bash
#
```
""",
    "context.md": """---
tags: [project, context, memory]
type: context
updated: {today}
---

# Project Context

## Purpose
## Goals
## Scope (In / Out)
## Stakeholders / Users
## Constraints
## Domain Glossary
| Term | Meaning |
|------|---------|
## Non-Functional Requirements
""",
    "architecture.md": """---
tags: [project, architecture, memory]
type: architecture
updated: {today}
---

# Architecture

## System Overview
## Tech Stack
| Layer | Technology | Version |
|-------|-----------|---------|
## Component Breakdown
## Data Model
## Directory Structure
## Design Principles in Effect
## Known Technical Debt
""",
    "decisions.md": """---
tags: [project, decisions, adr, memory]
type: decisions
updated: {today}
---

# Architecture Decisions Log

> Consult before any architectural change. Add an ADR per lasting decision.

## Index
| ID | Title | Status | Date |
|----|-------|--------|------|

---
<!-- ADR template
## ADR-NNN: Title
**Status**:  **Date**:
**Context**:  **Decision**:
**Alternatives considered**:  **Consequences**:  **Links**:
-->
""",
    "progress.md": """---
tags: [project, progress, memory]
type: progress
updated: {today}
---

# Progress

## Status at a Glance
- Phase: Planning
- Overall completion: ░░░░░░░░░░ ~0%
- Last updated: {today}
- Health: 🟢 On track

## Milestones
| Milestone | Target | Status |
|-----------|--------|--------|

## Completed ✅
- [x] ({today}) Initialized memory system

## In Progress 🔄
## Up Next ⏳
## Recently Changed
- {today} — Memory initialized
""",
    "active-tasks.md": """---
tags: [project, tasks, active, memory]
type: active-tasks
updated: {today}
---

# Active Tasks

## 🎯 Current Task
> None yet. Create one in tasks/ and reference it here.

## 🔜 Next Up
| ID | Task | Priority | Detail |
|----|------|----------|--------|

## 🚧 Blocked
## 👀 In Review
## Recently Completed (last 5)
""",
    "README.md": """---
tags: [project, memory, index]
---

# .ai-memory — Project Memory

Persistent brain for this project. Read order:
onboarding → context → architecture → active-tasks → progress → decisions → sessions/ (newest)

Session history is **one file per session** under `sessions/` (filenames are date-prefixed, so the
newest sorts last). This avoids cross-branch merge conflicts — never re-introduce a single shared
`session-log.md`. Commit this directory to git (no secrets).
""",
}

# Tier-2: the seed session. The 000000 timestamp sorts before any real session,
# so the "newest" file is always the latest real session.
SEED_SESSION = """---
type: session
date: {today}
---
## Session — {today}
**TL;DR**: Initialized project memory (e4).
**Did**: Scaffolded .ai-memory/. Session history lives in sessions/ (one file per session).
**Decisions**: None.
**Files changed**: .ai-memory/*
**State**: Scaffolding complete.
**Blockers**: None.
**Next actions**:
1. Fill in context.md and architecture.md.
**Checkpoint**:
```
last_command: init_project_memory
working_file:
test_status: not run
uncommitted_changes: yes
```
"""

CLAUDE_MD_POINTER = """# CLAUDE.md

> See the full operating instructions. At session start, read `.ai-memory/` in this order:
> onboarding → context → architecture → active-tasks → progress → decisions → sessions/ (newest),
> then post a Resume Summary. After significant work, update progress.md, active-tasks.md,
> decisions.md (if needed), and write a new file in `.ai-memory/sessions/` for the session.
>
> (Replace this stub with the full CLAUDE.md from the AI-Memory-System package for complete rules.)
"""


def write(path: Path, content: str, force: bool) -> str:
    if path.exists() and not force:
        return f"skip  {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"write {path}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Initialize .ai-memory for a project")
    ap.add_argument("project", nargs="?", default=".", help="Project root path")
    ap.add_argument("--name", help="Project name (default: folder name)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    ap.add_argument("--with-claude-md", action="store_true",
                    help="Also create a stub CLAUDE.md at project root")
    args = ap.parse_args()

    root = Path(args.project).expanduser().resolve()
    if not root.exists():
        print(f"error: {root} does not exist", file=sys.stderr)
        return 1
    name = args.name or root.name

    mem = root / ".ai-memory"
    print(f"Initializing memory for '{name}' at {mem}\n")

    for fname, tmpl in FILES.items():
        print(write(mem / fname, tmpl.format(today=TODAY), args.force))

    (mem / "tasks").mkdir(exist_ok=True)
    print(f"write {mem / 'tasks'}/")

    # Tier-2: one file per session under sessions/
    (mem / "sessions").mkdir(exist_ok=True)
    seed = mem / "sessions" / f"{TODAY}-000000-init.md"
    print(write(seed, SEED_SESSION.format(today=TODAY), args.force))

    if args.with_claude_md:
        print(write(root / "CLAUDE.md", CLAUDE_MD_POINTER, args.force))

    print("\nDone. Next: fill in context.md and architecture.md, then start working.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
