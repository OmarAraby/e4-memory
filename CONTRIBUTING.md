# Contributing to e4

Thanks for your interest in **e4** — a persistent-memory system for AI coding agents (shared Agent
Skills, the Claude Code `/e4:*` commands and lifecycle hooks, and stdlib-only automation). Contributions are welcome.

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
| `agents-config/.agents/skills/e4-*/` | The shared e4 workflows (Agent Skills) — edit workflows **here** |
| `claude-config/overlays/` | Claude-only parts of each command (frontmatter, `!` injection, hooks install) |
| `claude-config/.claude/commands/e4/` | The `/e4:*` slash commands — **generated**, never hand-edit |
| `copilot-config/.github/` | Optional Copilot pointer to `AGENTS.md` |
| `claude-config/.claude/hooks/` | SessionStart / SessionEnd / Stop hook scripts |
| `claude-config/.claude/settings.json` | Hook wiring |
| `automation/python/` | Dependency-free (stdlib-only) Python tools |
| `automation/bash/`, `automation/powershell/` | Thin wrappers over the Python tools |
| `project-template/` | Per-project `.ai-memory/` starter + `AGENTS.md` contract + thin `CLAUDE.md` |
| `tests/` | stdlib `unittest` suite |
| `Templates/` | Obsidian note templates |
| `docs/` | `agent-setup.md`, `architecture/`, `WORKFLOW.md`, `OBSIDIAN-INTEGRATION.md`, `COMMANDS-AND-HOOKS.md` |

## Working on workflows and commands

- Workflow logic lives in `agents-config/.agents/skills/e4-<name>/SKILL.md` and must stay agent-neutral
  (no `/e4:` names, `` !`cmd` ``, `$ARGUMENTS`, or `.claude/` mechanics). Mark agent-variable text as
  `<!-- adapter:X -->default<!-- /adapter:X -->` and put the Claude text in `claude-config/overlays/<name>.md`.
- Regenerate the Claude commands after any skill/overlay change and commit both:
  `python automation/python/sync_agent_adapters.py`. The commands in `claude-config/.claude/commands/e4/`
  are generated — the filename is the command name (`init.md` → `/e4:init`).
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

## No build step — but run the tests

This is a docs + templates + scripts project — there's no compile/build. Before a PR, run:

```bash
python -m unittest discover -s tests                       # stdlib only; hook tests need bash
python automation/python/sync_agent_adapters.py --check     # generated commands are up to date
```
Also run any hook or script you changed manually and confirm the output.
