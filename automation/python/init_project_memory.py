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

# The slim per-project contract. Must stay byte-identical to project-template/CLAUDE.md
# (smoke_test.py checks it); the long-form rules live in docs/WORKFLOW.md.
CLAUDE_MD = """# CLAUDE.md

> Operating contract for Claude Code on this project (e4 persistent memory). Loaded every turn, so
> it stays short. Full rules and rationale: `~/AI-Vault/docs/WORKFLOW.md` (Rule Sets A–E + Standing Rules).

You are a senior engineer on this project. Memory lives in `.ai-memory/` (committed; never put
secrets in it). Standards: `~/AI-Vault/User/coding-standards.md`; `.ai-memory/onboarding.md` wins on conflict.

## A — Start
- The SessionStart summary **is** the resume. Don't re-read memory to rebuild it; open a
  `.ai-memory/` file only when the current task needs it. No summary, or a full resume asked → `/e4:resume`.
- Last session only auto-recorded → mention it; backfill only if asked. No `.ai-memory/` → offer `/e4:init`.

## B — Before changes
- Restate the task. Check `decisions.md` before architectural changes; never silently contradict an
  accepted ADR — propose a superseding one.
- Verify against `architecture.md` and fix drift. Plan briefly before non-trivial edits. Missing access → ask.

## C — During work
- Small, reviewable diffs with tests. No debug prints or secrets. Update the task's Checkpoints at stopping points.

## D — After work
- Task status only via `e4_task.py set-status` (`active-tasks.md` is generated — never edit it); new tasks via `/e4:new-task`.
- Update `decisions.md` (lasting decision), `architecture.md` (structure), `context.md` (scope),
  `progress.md` (Phase / Health / Milestones only).

## E — Session end
- `/e4:end-session` drafts a new `sessions/YYYY-MM-DD-HHMMSS-<branch>.md`; fill only its placeholders.
  Never edit an existing session file.
- Context nudge, or switching tasks → `/e4:end-session`, then `/clear`.

## Always
- Confirm each step and surface errors; never claim silent success. No push, force-push or
  destructive commands unless asked. Uncertain → two options with trade-offs.
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
                    help="Also create the slim e4 CLAUDE.md contract at project root")
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
        print(write(root / "CLAUDE.md", CLAUDE_MD, args.force))

    print("\nDone. Next: fill in context.md and architecture.md, then start working.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
