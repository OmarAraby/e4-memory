# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

`D:\AI-Vault` is the **global Obsidian vault** for the **AI Memory System for Claude Code** — a persistent-memory system that gives Claude long-term memory across projects, sessions, and restarts. The full distribution currently ships as zip bundles in the root (`files.zip`, `files (1).zip`); `files (1).zip` is the newer, more complete bundle (adds `claude-config/` slash commands + hooks and `COMMANDS-AND-HOOKS.md`). Unpacking `vault-structure/` from the bundle into this directory is what turns it into the live vault.

This is a **docs + templates + automation-scripts** project, not a compiled application. There is no build step. The Python automation is stdlib-only (no dependencies, no package manifest), the Bash/PowerShell scripts are thin wrappers over it, and there is no test suite — do not invent build/lint/test commands.

## The two-layer memory model (the core architecture)

Memory lives in two places that mirror each other; understanding the split is essential before touching anything:

1. **Global vault** (`~/AI-Vault`, i.e. this repo) — cross-project, opened in Obsidian. Contains `User/` (developer identity + `coding-standards.md`, treated as authoritative global rules), `Knowledge/` (reusable project-independent notes), `Templates/`, `DailyLogs/` (rolling journal), `Projects/` (one dashboard note per project, linked into the actual repos), and `Archive/`.
2. **Per-project memory** (`.ai-memory/` committed inside each code repo) — the source of truth for that project. Key files in read-order: `onboarding.md` → `context.md` → `architecture.md` → `active-tasks.md` → `progress.md` → newest file in `sessions/` → `decisions.md` (ADR log, consulted before architectural changes). Detailed per-task files live in `.ai-memory/tasks/TASK-<YYYYMMDD-HHMMSS>-<slug>.md` — IDs are timestamp-based, never sequential, so parallel branches can't collide. Pre-Tier-2 repos have a single `session-log.md` instead of `sessions/`; it is still read as a fallback.

The vault `Projects/` notes are **indexes/dashboards** that link into each repo's `.ai-memory/`; the in-repo `.ai-memory/` is the **authority**. Dashboards are generated, not hand-maintained.

## Commands vs hooks (the automation split)

The system deliberately divides work between two mechanisms — see `docs/COMMANDS-AND-HOOKS.md`:

- **Slash commands** (`claude-config/.claude/commands/e4/*.md`, namespaced `e4:`) produce *content* that needs model intelligence: `/e4:init [name]`, `/e4:end-session [note]` (the workhorse — pulls live `git status`/`diff`/`log`, then writes a **new** structured file to `.ai-memory/sessions/` and updates `progress.md`/`tasks/`/`decisions.md`), `/e4:resume`, `/e4:new-task <title>`.
- **Hooks** (`claude-config/.claude/settings.json` → `.claude/hooks/*.sh`) provide *mechanical guarantees* that must not depend on the model: `SessionStart` auto-injects memory into context (its stdout is the load mechanism); `SessionEnd` leaves a breadcrumb file in `sessions/` if `/e4:end-session` was skipped, then backgrounds archiving + daily roll-up; `Stop` optionally nudges to run `/e4:end-session`. A `PreToolUse` guard (`guard-destructive-git.py`) blocks destructive git commands and secret commits.

A `SessionEnd` hook **cannot** make the model write a summary (the session is ending) — that is exactly why the intelligent summary is a command and the load/backstop is a hook. Hooks must finish within their `timeout` or you get `Hook cancelled`; push slow work into a backgrounded subshell that returns immediately.

## The workflow contract (rule sets A–E)

`project-template/CLAUDE.md` is the per-project operating contract Claude follows automatically, formalized in `docs/WORKFLOW.md` as five rule sets: **A** entering a project (read order + post a ≤8-line Resume Summary), **B** before changes (restate task, check ADRs — never silently contradict an accepted one, supersede instead), **C** during work (incremental diffs + task checkpoints), **D** after work (update `progress.md`/`tasks/`/`decisions.md`/`architecture.md`), **E** session end (write a new `sessions/` file). Note `active-tasks.md` is a **generated, gitignored view** of `tasks/*.md` — never hand-edited. When editing the template or workflow doc, keep these two files consistent — the template encodes the doc.

## Automation commands

Python (cross-platform core, run from `automation/python/`):

```bash
# Scaffold .ai-memory/ in a project (+ optional CLAUDE stub)
python3 init_project_memory.py <project-root> --name "MyApp" --with-claude-md [--force]

# Roll today's session files into the global daily note
python3 generate_daily_summary.py --vault ~/AI-Vault --projects-root ~/code [--date YYYY-MM-DD]

# Regenerate .ai-memory/active-tasks.md from tasks/*.md (also run by the SessionStart hook)
python3 generate_status.py --project <project-root>

# Move completed tasks to Archive/tasks/
python3 archive_completed_tasks.py --project <project-root> --vault ~/AI-Vault [--infer] [--dry-run]

# Generate a project dashboard and/or rebuild the global Projects index
python3 create_dashboard.py --vault ~/AI-Vault --project <project-root>
python3 create_dashboard.py --vault ~/AI-Vault --rebuild-index --projects-root ~/code
```

Wrappers delegate to the Python tools. **Windows (this environment) — use PowerShell:**

```powershell
.\automation\powershell\Init-ProjectMemory.ps1 <project-root> "MyApp"
.\automation\powershell\Ai-Memory.ps1 daily
.\automation\powershell\Ai-Memory.ps1 dashboard <project-root>
.\automation\powershell\Ai-Memory.ps1 archive <project-root>
.\automation\powershell\Ai-Memory.ps1 sync
```

The wrappers read `AI_VAULT`, `AI_MEMORY_PYDIR`, and `AI_PROJECTS_ROOT` from the environment; set these or edit the script defaults before running.

## Conventions when editing memory content

- All notes use YAML front-matter with tags and `{{date}}` placeholders (Templater-compatible). Templates in `vault-structure/Templates/` are the global source; `project-template/.ai-memory/` mirrors them as live per-project starting files — keep the two in sync when changing a template.
- Use Obsidian-style `[[note]]` links inside memory files so the knowledge graph stays connected.
- Session history is **one file per session** in `.ai-memory/sessions/`, named `YYYY-MM-DD-HHMMSS-<branch>.md` so the lexically-last file is the newest. Files are immutable — never edit one, write a new one. A strong 2–3 line TL;DR in each is what makes the next session resume instantly; a file without one is treated as an incomplete auto-breadcrumb.
- `active-tasks.md` and the `Projects/` dashboards are **generated** — edit the source (`tasks/*.md`, the repos) and regenerate, never the view.
- `.ai-memory/` is committed to git and must never contain secrets.
- Python scripts are intended to stay dependency-free (stdlib only), idempotent, and safe to re-run.
