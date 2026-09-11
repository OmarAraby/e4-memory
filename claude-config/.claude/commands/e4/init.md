---
# e4 — forged by Omar Araby & contributors
description: "[e4] Scaffold .ai-memory/ and CLAUDE.md for this project"
argument-hint: [project name (optional)]
allowed-tools: Bash(python3:*), Bash(python:*), Bash(ls:*), Bash(test:*), Bash(cat:*), Bash(mkdir:*), Bash(cp:*), Read, Write, Edit
---

# /e4:init — Initialize project memory

You are setting up the persistent memory system for **this** project (the current working directory).

## Step 1 — Detect what's already installed
This command is a **top-up**: install only what is MISSING, never overwrite what exists. Check
independently for each piece — `.ai-memory/`, `./.claude/hooks/`, hooks in `./.claude/settings.json`,
and `CLAUDE.md` — and decide per piece:
- If `.ai-memory/` exists → SKIP Step 2 (do not touch existing memory), but CONTINUE to the remaining steps to add any missing hooks / CLAUDE.md section.
- If ALL of (`.ai-memory/`, hooks, CLAUDE.md) already exist → report that the project is fully set up and stop.
- Reinitialize memory from scratch ONLY if the user explicitly asks.

## Step 2 — Scaffold the structure (only if `.ai-memory/` is missing)
Prefer the bundled initializer if available; otherwise create files yourself.

Look for the init script in these locations (first match wins):
- `./scripts/init_project_memory.py`
- `~/AI-Vault/automation/python/init_project_memory.py`
- `~/.claude/ai-memory/init_project_memory.py`

If found, run it (try `python3`, fall back to `python` on Windows):
```
python3 <path> . --name "$ARGUMENTS"
```
(If `$ARGUMENTS` is empty, use the current folder name.)

If NOT found, create the structure yourself using the Write tool. Create `.ai-memory/` with these files, each with YAML front-matter (`tags`, `type`, `updated: <today>`):
- `onboarding.md` — entry point: what the project is, read order, golden rules, env setup, how to run tests
- `context.md` — purpose, goals, scope, constraints, domain glossary
- `architecture.md` — system overview, tech stack table, components, data model, design principles
- `decisions.md` — ADR log with an index table
- `progress.md` — phase, completion %, milestones, Completed/In-Progress/Up-Next sections
- `active-tasks.md` — Current Task, Next Up, Blocked, In Review
- `sessions/` — one file per session (date-prefixed names, e.g. `2026-06-18-164530-main.md`); seed it with `<today>-000000-init.md` (TL;DR: initialized memory). Do NOT create a single `session-log.md` — per-session files avoid cross-branch merge conflicts.
- `README.md` — the read order and "commit this dir to git"
- `tasks/` — empty directory

## Step 2.5 — Install the auto-load hooks (PER-PROJECT)
The hooks give this repo mechanical guarantees that don't depend on the model: **SessionStart**
auto-loads memory into context, **SessionEnd** leaves a breadcrumb + refreshes maintenance, **Stop**
nudges to run `/e4:end-session`. Install them **into this project only** — never globally
(a global hook would fire in every repo you open, including ones with no `.ai-memory/`).

Find the hook source (first match wins):
- `$AI_VAULT/claude-config/.claude/` (env var; on this machine `D:\AI-Vault\claude-config\.claude\`)
- `~/AI-Vault/claude-config/.claude/`
- `./scripts/.claude/`

If a source is found AND `./.claude/hooks/` does not already exist:
1. Copy `hooks/session_start.sh`, `hooks/session_end.sh`, `hooks/stop_reminder.sh` into `./.claude/hooks/`.
2. Install the hooks config into `./.claude/settings.json`:
   - If `settings.json` does NOT exist, copy the source `settings.json` (it contains the SessionStart/SessionEnd/Stop block).
   - If it DOES exist, merge only the `hooks` key in — never overwrite other keys (e.g. `permissions`). Leave any `settings.local.json` untouched.
3. Tell the user (Windows): the hooks run via **Git Bash** (`bash`) and call **`python3`** — both must be on PATH.

If `./.claude/hooks/` already exists, skip (don't clobber). If no hook source is found, tell the user where the hooks live and continue without failing.

## Step 2.6 — Ensure `.gitattributes` (prevent cross-branch memory conflicts)
`decisions.md` is the one remaining **append-only** file — every session/branch adds an ADR at
the same spot, so merging branches collides. Mark it `merge=union` so git concatenates both sides
instead of raising a conflict. (`sessions/` needs no union merge: one file per session means two
branches never touch the same file. The legacy `session-log.md` line is kept only for repos that
still have that file.) Also pin hook scripts to LF so they run on Windows checkouts.

Ensure `./.gitattributes` contains these lines — **create it if missing; if it already exists,
append only the lines not already present** (don't duplicate or reorder existing entries):
```
*.sh text eol=lf
.ai-memory/decisions.md   merge=union
.ai-memory/session-log.md merge=union   # legacy pre-Tier-2 repos only
```
`merge=union` is a built-in git driver — no `.git/config` setup needed; the committed
`.gitattributes` carries it to every clone. It covers only the append-only files; `progress.md`
holds stable fields (rare conflicts) and `active-tasks.md` is gitignored (next step).

## Step 2.7 — Ensure `.gitignore` excludes the generated view
`active-tasks.md` is a **generated view** of `tasks/*.md` (rebuilt each session by `generate_status.py`),
so it must NOT be committed — otherwise two branches regenerate different content and conflict.
Ensure `./.gitignore` contains this line (create the file if missing; append only if not already present):
```
.ai-memory/active-tasks.md
```
If the repo already tracks `active-tasks.md` from before, untrack it once (keeps the file on disk):
`git rm --cached .ai-memory/active-tasks.md`.

## Step 3 — Install CLAUDE.md
If `CLAUDE.md` does not exist at the project root, create it from the bundled template (search the same locations for `CLAUDE.md`), or write the standard one with: session-start protocol, before-changes checks, memory-update rules, task-tracking rules, session-summary rules, coding rules.

If `CLAUDE.md` already exists, do NOT clobber it — instead append a short `## Persistent Memory (.ai-memory)` section pointing at `.ai-memory/` and the read order, only if such a section isn't already present.

## Step 4 — Confirm
Print a short confirmation:
- which files were created (or skipped) — including whether hooks + `settings.json` were installed
- the read order
- remind the user to fill in `context.md` and `architecture.md`
- note that the SessionStart auto-load hook takes effect on the **next** session (reopen the project)
- suggest committing `.ai-memory/`, `.claude/`, `CLAUDE.md`, and `.gitattributes` to git (the `.gitattributes` pins `*.sh` to LF for Windows hooks and union-merges the append-only memory files to avoid cross-branch conflicts)

Do not start coding work. This command only sets up memory.

<!-- e4 · forged by Omar Araby & contributors · add your name to CONTRIBUTORS.md when you extend these commands -->
