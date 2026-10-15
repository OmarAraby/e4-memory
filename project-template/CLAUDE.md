# CLAUDE.md

> Claude Code entry point for this project. The full operating contract is **agent-neutral** and
> lives in `AGENTS.md` (shared with GitHub Copilot, Cursor and other agents). It is imported below —
> change the rules there, not here. This file only adds what is specific to Claude Code.

@AGENTS.md

---

## Claude Code specifics

### Commands
In Claude Code the e4 workflows are the `/e4:*` slash commands (installed in `.claude/commands/e4/`,
generated from the same skills other agents use in `.agents/skills/`):

| AGENTS.md says | In Claude Code run |
|----------------|--------------------|
| `e4-resume` | `/e4:resume` |
| `e4-end-session` | `/e4:end-session` |
| `e4-new-task <title>` | `/e4:new-task <title>` |
| `e4-init` | `/e4:init` |

### Hooks (mechanical guarantees — see `docs/COMMANDS-AND-HOOKS.md` in the e4 vault)
If `.claude/settings.json` wires the e4 hooks:
- **SessionStart** auto-loads a memory summary into context (and regenerates `active-tasks.md`) —
  you still read the files in Section 1 of `AGENTS.md` for detail.
- **SessionEnd** writes an auto-breadcrumb to `sessions/` if `/e4:end-session` was skipped.
- **Stop** nudges once per day to run `/e4:end-session` when there is uncommitted, unlogged work.

`/e4:end-session` performs all Section 4–6 memory updates in one step. The commands are the
preferred, deterministic path.
