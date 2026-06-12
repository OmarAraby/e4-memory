# Contributing to e4

Thanks for your interest in **e4** — a persistent-memory system for Claude Code (the `/e4:*`
command namespace, lifecycle hooks, and stdlib-only automation). Contributions are welcome.

## ⚠️ Golden rule: never commit personal or private data

This repo is the **reusable system only**. It must contain **no** real project memory, work
content, secrets, or identity. Specifically, never commit:

- `DailyLogs/*`, `Projects/*` dashboards, or `Archive/*` content (only the folder `README.md` files belong here)
- `User/profile.md` / `User/coding-standards.md` — these are personal; only the `*.example.md` templates are tracked
- `.env`, tokens, keys, connection strings, internal hostnames, or any company/work project names

The `.gitignore` enforces most of this, but **check your diff before every commit**. When in doubt, leave it out.

## Project layout

| Path | What it is |
|------|------------|
| `claude-config/.claude/commands/e4/` | The `/e4:*` slash commands (markdown prompt files) |
| `claude-config/.claude/hooks/` | SessionStart / SessionEnd / Stop hook scripts |
| `claude-config/.claude/settings.json` | Hook wiring |
| `automation/python/` | Dependency-free (stdlib-only) Python tools |
| `automation/bash/`, `automation/powershell/` | Thin wrappers over the Python tools |
| `project-template/` | Per-project `.ai-memory/` starter + `CLAUDE.md` contract |
| `Templates/` | Obsidian note templates |
| `docs/` | `WORKFLOW.md`, `OBSIDIAN-INTEGRATION.md`, `COMMANDS-AND-HOOKS.md` |

## Working on commands

- Commands live in `claude-config/.claude/commands/e4/`. The filename is the command name (`init.md` → `/e4:init`).
- If you add or meaningfully change a command, **sign your work**: add yourself to
  `claude-config/.claude/commands/e4/CONTRIBUTORS.md`.
- Keep command behavior consistent with the others (frontmatter `description`, clear steps, `allowed-tools`).

## Working on hooks (Windows-friendly)

- Hook scripts must stay **LF** line endings (`.gitattributes` pins `*.sh text eol=lf`) so Git Bash can run them on Windows checkouts.
- Hooks run via `bash` and call `python3` — both must be on PATH. There is **no** global hook; hooks are installed per-project.
- Test a hook before submitting, e.g.:
  ```bash
  echo '{"source":"startup"}' | bash claude-config/.claude/hooks/session_start.sh
  ```

## Automation scripts

- Keep the Python **dependency-free (stdlib only)**, idempotent, and safe to re-run.
- Avoid non-ASCII characters in anything printed to stdout (Windows consoles use cp1252 and will crash on emoji).

## Commits & PRs

- **Conventional Commits**: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- Keep PRs focused and under ~400 lines where practical.
- Every PR explains **what** and **why**; link any related issue.
- Fill in the PR template checklist (including the "no personal data / no secrets" box).

## No build step

This is a docs + templates + scripts project — there's no compile/build and no test suite. Validate
changes by running the relevant script or hook manually and confirming the output.
