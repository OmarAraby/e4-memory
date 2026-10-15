# AI-Vault — Persistent Memory for AI Coding Agents · `e4`

> Give your coding agent long-term memory across **projects, sessions, and restarts** — with Obsidian as the knowledge base.
> Works with **Claude Code** (tested, with hooks), and **GitHub Copilot** and **Cursor** (via `AGENTS.md` + Agent Skills; unverified).

Open a project and the agent already knows its context, architecture, decisions, conventions, progress, and where the last session left off — then it keeps that memory current automatically. This repo is the **global vault** (your cross-project brain) plus the **tooling** that wires memory into each project.

*Forged by Omar Araby & contributors. The command namespace is the signature: when you type `/e4:` you know whose system you're in.*

---

## Why

Claude Code forgets everything when a session ends. This system makes the *mechanical* parts of remembering not depend on the model at all: memory is loaded by a hook on every session start, and persisted by a single command at the end. The result — you stop re-explaining your project every morning.

## Supported agents

| Agent | Entry point | Workflows | Lifecycle automation | Status |
|---|---|---|---|---|
| Claude Code | `CLAUDE.md` → `@AGENTS.md` | `/e4:*` commands | SessionStart / SessionEnd / Stop hooks | tested |
| GitHub Copilot | `AGENTS.md` (+ optional `.github/copilot-instructions.md`) | `.agents/skills/e4-*` | — | unverified |
| Cursor | `AGENTS.md` | `.agents/skills/e4-*` | — | unverified |

One knowledge base for all of them: the vault + each repo's `.ai-memory/`. Setup per agent:
[`docs/agent-setup.md`](docs/agent-setup.md) · design: [`docs/architecture/agent-agnostic-architecture.md`](docs/architecture/agent-agnostic-architecture.md).

## How it works — two layers

```
┌─ Global vault (this repo, opened in Obsidian) ──────────────┐
│  User/        who you are — preferences, coding standards    │
│  Knowledge/   reusable, project-independent notes            │
│  Templates/   starter files for every note type              │
│  DailyLogs/   rolling cross-project journal                  │
│  Projects/    one dashboard note per project (links in)      │
│  Archive/     completed work, superseded decisions           │
└──────────────────────────────────────────────────────────────┘
                    ▲ indexes / links into
                    │
┌─ Per-project memory (committed inside each repo) ───────────┐
│  AGENTS.md            agent-neutral operating contract        │
│  CLAUDE.md            thin Claude entry point (@AGENTS.md)    │
│  .agents/skills/e4-*  shared workflows (Copilot, Cursor)      │
│  .ai-memory/                                                  │
│    onboarding.md  context.md  architecture.md                 │
│    decisions.md (ADRs)  progress.md                           │
│    active-tasks.md (generated view, gitignored)               │
│    sessions/YYYY-MM-DD-HHMMSS-branch.md (the resume anchor)   │
│    tasks/TASK-<timestamp>-<slug>.md                           │
└──────────────────────────────────────────────────────────────┘
```

The **vault is personal** to each developer; the **`.ai-memory/` is shared** (committed, travels with the repo).

## The e4 workflows

Defined once as Agent Skills in `agents-config/.agents/skills/e4-*/` (used directly by Copilot and Cursor as
`e4-init`, `e4-resume`, …). For Claude Code they are generated into `/e4:*` slash commands, installed per-project
under `.claude/commands/e4/` (so the namespace — and the credit — travels with the code):

| Command | What it does |
|---|---|
| `/e4:init` | Scaffold `.ai-memory/` + a `CLAUDE.md` (won't clobber an existing one — it appends a memory section) |
| `/e4:resume` | Re-read memory in order and post a Resume Summary |
| `/e4:new-task <title>` | Create a tracked `tasks/TASK-<timestamp>-<slug>.md`; `active-tasks.md` regenerates from it |
| `/e4:end-session` | The workhorse — pull live `git` state, write a new `sessions/` file, update progress/tasks/decisions |

## Hooks (the "doesn't rely on the model" guarantee — Claude Code)

Wired in `.claude/settings.json`:

- **SessionStart** → injects the current memory summary into context on every open/resume.
- **SessionEnd** → drops a breadcrumb if you forgot `/e4:end-session`, then archives + refreshes the daily roll-up.
- **Stop** → a one-time gentle nudge to save when there's uncommitted work and no log entry yet.

A `SessionEnd` hook can't write an intelligent summary (the model is already done) — that's why the summary is a *command* and the load/backstop are *hooks*.

---

## Quick start

### 1. Make this your global vault
```bash
# Open the vault in Obsidian, then enable: Dataview, Templater, Daily Notes (folder = DailyLogs/)
# Create your identity files from the examples (these stay local — they're gitignored):
#   cp User/profile.example.md User/profile.md
#   cp User/coding-standards.example.md User/coding-standards.md
```

Set three environment variables so the automation/hooks find the vault:

| Variable | Value |
|---|---|
| `AI_VAULT` | `D:\AI-Vault` |
| `AI_MEMORY_PYDIR` | `D:\AI-Vault\automation\python` |
| `AI_PROJECTS_ROOT` | wherever your repos live |

### 2. Onboard a project
```bash
# portable core (any agent): .ai-memory/ + AGENTS.md + .agents/skills/
python automation/python/init_project_memory.py <repo-path> --name "MyApp" --with-agents-md --with-skills
# Claude Code: add --with-claude-md (imports AGENTS.md) and copy the commands + hooks, then commit:
#   <repo>/.claude/commands/e4/   <repo>/.claude/hooks/   <repo>/.claude/settings.json
python automation/python/validate_memory.py --project <repo-path> --agents
```
Claude Code: open the repo → SessionStart auto-loads memory → work → `/e4:end-session`.
Copilot / Cursor: ask to *resume* (`e4-resume`) → work → *wrap up* (`e4-end-session`). Details: [`docs/agent-setup.md`](docs/agent-setup.md).

## Automation scripts

Dependency-free Python (stdlib only), with Bash + PowerShell wrappers.

| Task | Command |
|---|---|
| Scaffold project memory | `python automation/python/init_project_memory.py <repo> --name "X" --with-claude-md` |
| Daily roll-up | `python automation/python/generate_daily_summary.py --vault $AI_VAULT --projects-root $AI_PROJECTS_ROOT` |
| Archive done tasks | `python automation/python/archive_completed_tasks.py --project <repo> --vault $AI_VAULT --infer` |
| Project dashboard | `python automation/python/create_dashboard.py --vault $AI_VAULT --project <repo>` |
| Rebuild master index | `python automation/python/create_dashboard.py --vault $AI_VAULT --rebuild-index --projects-root $AI_PROJECTS_ROOT` |
| Validate memory + agent wiring | `python automation/python/validate_memory.py --project <repo> --agents` |
| Regenerate Claude commands from skills | `python automation/python/sync_agent_adapters.py` (`--check` to detect drift) |
| Run the test suite | `python -m unittest discover -s tests` |

Windows wrappers: `automation/powershell/Ai-Memory.ps1 {daily|dashboard|archive|sync}`.

## Repository layout

| Path | Purpose |
|---|---|
| `User/` `Knowledge/` `Templates/` `DailyLogs/` `Projects/` `Archive/` | the global vault (opened in Obsidian) |
| `automation/` | Python core + Bash/PowerShell wrappers |
| `agents-config/.agents/skills/` | the shared e4 workflows (Agent Skills) — **source of truth** |
| `claude-config/.claude/` | Claude Code adapter: generated `e4` commands, hooks, `settings.json` (install per-project) |
| `claude-config/overlays/` | Claude-only parts merged into the generated commands |
| `copilot-config/.github/` | optional Copilot pointer to `AGENTS.md` |
| `project-template/` | per-project `.ai-memory/` starter + `AGENTS.md` contract + thin `CLAUDE.md` |
| `tests/` | stdlib `unittest` suite |
| `docs/` | `agent-setup.md`, `architecture/`, `WORKFLOW.md`, `OBSIDIAN-INTEGRATION.md`, `COMMANDS-AND-HOOKS.md` |

## Conventions

- **Commit `.ai-memory/` to each repo's git.** Memory travels with the code. Never put secrets in it.
- **Session history is sacred** — one immutable file per session in `sessions/`, never edited; a sharp TL;DR makes the next session instant.
- **Never hand-edit a generated view** — `active-tasks.md` comes from `tasks/*.md`, dashboards come from the repos. Edit the source, regenerate.
- **One ADR per lasting decision** in `decisions.md`; supersede, never silently contradict.
- Notes use `[[wikilinks]]` so the Obsidian graph stays connected.

## Notes for Windows

- Hooks run via **Git Bash** (`bash .claude/hooks/*.sh`) and call **`python3`** — both must be on PATH. Verified on Windows 11 with Python 3.14 + Git Bash.
- `.gitattributes` should pin `*.sh text eol=lf` so the hook scripts survive Windows checkouts.

## Contributing

Contributions welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md). The golden rule: **never commit
personal or work content** (DailyLogs, project dashboards, identity, secrets) — this repo is the
reusable system only. When you extend a command, sign your work in `commands/e4/CONTRIBUTORS.md`.

## License

Licensed under the **Apache License 2.0** — see [`LICENSE`](LICENSE). © 2026 Omar Araby.

---

*`e4` · a persistent-memory system for AI coding agents. Contributions welcome — add yourself to the namespace's `CONTRIBUTORS.md` when you extend the commands.*
