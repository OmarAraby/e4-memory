---
# e4 — forged by Omar Araby & contributors
description: "[e4] Scaffold .ai-memory/ and CLAUDE.md for this project"
argument-hint: [project name (optional)]
allowed-tools: Bash(python3:*), Bash(python:*), Bash(ls:*), Bash(test:*), Bash(cat:*), Bash(mkdir:*), Bash(cp:*), Read, Write, Edit
---
<!-- region:args -->
"$ARGUMENTS"
<!-- /region:args -->
<!-- region:detect-extra -->
, `./.claude/hooks/`, hooks in `./.claude/settings.json`, `CLAUDE.md`
<!-- /region:detect-extra -->
<!-- region:agent-steps -->
### 7a — Install the auto-load hooks (PER-PROJECT)
The hooks give this repo mechanical guarantees that don't depend on the model: **SessionStart**
auto-loads memory into context, **SessionEnd** leaves a breadcrumb + refreshes maintenance, **Stop**
nudges to run `/e4:end-session`. Install them **into this project only** — never globally
(a global hook would fire in every repo you open, including ones with no `.ai-memory/`).

Find the hook source (first match wins):
- `$AI_VAULT/claude-config/.claude/` (env var)
- `~/AI-Vault/claude-config/.claude/`
- `./scripts/.claude/`

If a source is found AND `./.claude/hooks/` does not already exist:
1. Copy `hooks/session_start.sh`, `hooks/session_end.sh`, `hooks/stop_reminder.sh` into `./.claude/hooks/`.
2. Install the hooks config into `./.claude/settings.json`:
   - If `settings.json` does NOT exist, copy the source `settings.json` (it contains the SessionStart/SessionEnd/Stop block).
   - If it DOES exist, merge only the `hooks` key in — never overwrite other keys (e.g. `permissions`). Leave any `settings.local.json` untouched.
3. Tell the user (Windows): the hooks run via **Git Bash** (`bash`) and call **`python3`** — both must be on PATH.

If `./.claude/hooks/` already exists, skip (don't clobber). If no hook source is found, tell the user where the hooks live and continue without failing.

### 7b — Install CLAUDE.md
Claude Code reads `AGENTS.md` on its own only when the project has **no** `CLAUDE.md`, so the
shared contract is pulled in with an `@AGENTS.md` import.

If `CLAUDE.md` does not exist at the project root, create it from the bundled template
(`project-template/CLAUDE.md` in the same locations as the hook source, one level up from
`claude-config/`) — a thin file that imports `@AGENTS.md` and adds the Claude Code specifics.
If no template is found, write a `CLAUDE.md` whose first content line is `@AGENTS.md`.

If `CLAUDE.md` already exists, do NOT clobber it — instead append a short `## Persistent Memory (.ai-memory)`
section containing the line `@AGENTS.md` (plus one sentence pointing at `.ai-memory/` and the read order),
only if such a section or import isn't already present.

GitHub Copilot and Cursor need nothing more: both read `AGENTS.md` and `.agents/skills/` natively.
<!-- /region:agent-steps -->
<!-- region:confirm-extra -->
 — including whether hooks + `settings.json` were installed
- note that the SessionStart auto-load hook takes effect on the **next** session (reopen the project)
<!-- /region:confirm-extra -->
<!-- region:commit-extra -->
, `.claude/`, `CLAUDE.md`
<!-- /region:commit-extra -->
