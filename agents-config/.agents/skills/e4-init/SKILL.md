---
name: e4-init
description: "[e4] Set up e4 persistent memory in this project: scaffold .ai-memory/, AGENTS.md, the shared e4 skills, .gitattributes and .gitignore. Top-up only; never overwrites existing memory. Use when the user asks to initialize or install project memory."
---

# e4-init — Initialize project memory

You are setting up the persistent memory system for **this** project (the current working directory).
Project name: <!-- adapter:args -->the name the user gave with this request<!-- /adapter:args --> (if empty, use the current folder name).

## Step 1 — Detect what's already installed
This workflow is a **top-up**: install only what is MISSING, never overwrite what exists. Check
independently for each piece — `.ai-memory/`, `./.agents/skills/e4-*`, `AGENTS.md` (and its memory
section), `.gitattributes`, `.gitignore`<!-- adapter:detect-extra --><!-- /adapter:detect-extra --> — and decide per piece:
- If `.ai-memory/` exists → SKIP Step 2 (do not touch existing memory), but CONTINUE to the remaining steps to add any missing pieces.
- If ALL pieces already exist → report that the project is fully set up and stop.
- Reinitialize memory from scratch ONLY if the user explicitly asks.

Wherever this workflow says "the e4 vault", search these locations (first match wins):
`$AI_VAULT/`, `~/AI-Vault/`, `./scripts/`.

## Step 2 — Scaffold the structure (only if `.ai-memory/` is missing)
Prefer the bundled initializer if available; otherwise create files yourself.

Look for the init script in these locations (first match wins):
- `./scripts/init_project_memory.py`
- `~/AI-Vault/automation/python/init_project_memory.py`
- `~/.claude/ai-memory/init_project_memory.py`

If found, run it (try `python3`, fall back to `python` on Windows):
```
python3 <path> . --name "<project name>"
```

If NOT found, create the structure yourself. Create `.ai-memory/` with these files, each with YAML front-matter (`tags`, `type`, `updated: <today>`):
- `onboarding.md` — entry point: what the project is, read order, golden rules, env setup, how to run tests
- `context.md` — purpose, goals, scope, constraints, domain glossary
- `architecture.md` — system overview, tech stack table, components, data model, design principles
- `decisions.md` — ADR log with an index table
- `progress.md` — phase, completion %, milestones, Completed/In-Progress/Up-Next sections
- `active-tasks.md` — Current Task, Next Up, Blocked, In Review
- `sessions/` — one file per session (date-prefixed names, e.g. `2026-06-18-164530-main.md`); seed it with `<today>-000000-init.md` (TL;DR: initialized memory). Do NOT create a single `session-log.md` — per-session files avoid cross-branch merge conflicts.
- `README.md` — the read order and "commit this dir to git"
- `tasks/` — empty directory

## Step 3 — Install the shared e4 skills (portable, all agents)
For each `e4-*` folder in `<e4 vault>/agents-config/.agents/skills/`, copy it into `./.agents/skills/`
**only if that folder does not exist there yet** — so a partial install is completed. Never overwrite
or merge into an existing folder (it may be customised). GitHub Copilot and Cursor load skills from `.agents/skills/` natively.
If no source is found, tell the user where the skills live and continue without failing.

## Step 4 — Ensure `.gitattributes` (prevent cross-branch memory conflicts)
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
# legacy pre-Tier-2 repos only (git does not allow comments at the end of a line)
.ai-memory/session-log.md merge=union
```
`merge=union` is a built-in git driver — no `.git/config` setup needed; the committed
`.gitattributes` carries it to every clone. It covers only the append-only files; `progress.md`
holds stable fields (rare conflicts) and `active-tasks.md` is gitignored (next step).

## Step 5 — Ensure `.gitignore` excludes the generated view
`active-tasks.md` is a **generated view** of `tasks/*.md` (rebuilt by `generate_status.py`),
so it must NOT be committed — otherwise two branches regenerate different content and conflict.
Ensure `./.gitignore` contains this line (create the file if missing; append only if not already present):
```
.ai-memory/active-tasks.md
```
If the repo already tracks `active-tasks.md` from before, untrack it once (keeps the file on disk):
`git rm --cached .ai-memory/active-tasks.md`.

## Step 6 — Install AGENTS.md (the agent-neutral operating contract)
If `AGENTS.md` does not exist at the project root, create it from `<e4 vault>/project-template/AGENTS.md`,
or write the standard one with: session-start protocol, before-changes checks, memory-update rules,
task-tracking rules, session-summary rules, coding rules.

If `AGENTS.md` already exists, do NOT clobber it — instead append a short `## Persistent Memory (.ai-memory)`
section pointing at `.ai-memory/` and the read order, only if such a section isn't already present.

## Step 7 — Agent-specific integration
<!-- adapter:agent-steps -->
GitHub Copilot and Cursor need nothing more: both read `AGENTS.md` and `.agents/skills/` natively.
Optional for Copilot: if `./.github/copilot-instructions.md` is missing, copy it from
`<e4 vault>/copilot-config/.github/copilot-instructions.md` (a short pointer to `AGENTS.md`, for
Copilot surfaces that read only that file). Never overwrite an existing one.
For Claude Code, its e4 init command performs this workflow plus its own hook and `CLAUDE.md`
steps — see `docs/agent-setup.md` in the e4 vault.
<!-- /adapter:agent-steps -->

## Step 8 — Confirm
Print a short confirmation:
- which files were created (or skipped)<!-- adapter:confirm-extra --><!-- /adapter:confirm-extra -->
- the read order
- remind the user to fill in `context.md` and `architecture.md`
- suggest committing `.ai-memory/`, `.agents/`, `AGENTS.md`<!-- adapter:commit-extra --><!-- /adapter:commit-extra -->, and `.gitattributes` to git (the `.gitattributes` pins `*.sh` to LF for Windows hooks and union-merges the append-only memory files to avoid cross-branch conflicts)

Do not start coding work. This workflow only sets up memory.
