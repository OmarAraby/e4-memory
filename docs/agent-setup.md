# Agent Setup

How to enable e4 persistent memory for each supported coding agent. Background and design:
[`architecture/agent-agnostic-architecture.md`](architecture/agent-agnostic-architecture.md).

| Agent | Status | What a project needs |
|---|---|---|
| Claude Code | **Tested** | `CLAUDE.md` (imports `AGENTS.md`), `.claude/commands/e4/`, `.claude/hooks/`, `.claude/settings.json` |
| GitHub Copilot | **Unverified** (static checks only) | `AGENTS.md`, `.agents/skills/e4-*`; optional `.github/copilot-instructions.md` |
| Cursor | **Unverified** (static checks only) | `AGENTS.md`, `.agents/skills/e4-*` |

All agents share the same `.ai-memory/` — there is one knowledge base, not one per agent.

---

## 1. Prerequisites (all agents)

- **Python 3.9+** on PATH as `python3` (or `python` on Windows). Stdlib only — nothing to install.
- **Git**.
- The e4 repo cloned as your global vault (e.g. `~/AI-Vault`), opened in Obsidian
  (see [`OBSIDIAN-INTEGRATION.md`](OBSIDIAN-INTEGRATION.md)).
- Environment variables used by the scripts and Claude hooks:

| Variable | Purpose | Example | Required |
|---|---|---|---|
| `AI_VAULT` | vault root | `~/AI-Vault` | optional (defaults to `~/AI-Vault`) |
| `AI_MEMORY_PYDIR` | `automation/python` dir | `~/AI-Vault/automation/python` | optional (same default) |
| `AI_PROJECTS_ROOT` | where your repos live (daily roll-up) | `~/code` | optional |

## 2. Install the portable core in a project (every agent)

```bash
python ~/AI-Vault/automation/python/init_project_memory.py <repo> --name "MyApp" \
  --with-agents-md --with-skills
python ~/AI-Vault/automation/python/validate_memory.py --project <repo> --agents
```

This creates `.ai-memory/`, `AGENTS.md`, and `.agents/skills/e4-{init,resume,new-task,end-session}/`.
It never overwrites an existing file unless you pass `--force`. Then:

- add `.ai-memory/active-tasks.md` to the repo's `.gitignore` (generated view);
- add `.ai-memory/decisions.md merge=union` to `.gitattributes`;
- commit `.ai-memory/`, `.agents/`, `AGENTS.md`, `.gitattributes`.

(The `e4-init` skill / `/e4:init` command does those `.gitignore`/`.gitattributes` steps for you.)

---

## 3. Claude Code

```bash
python ~/AI-Vault/automation/python/init_project_memory.py <repo> \
  --with-agents-md --with-claude-md --with-skills
cp -r ~/AI-Vault/claude-config/.claude <repo>/.claude      # commands + hooks + settings.json
```
Or open the repo in Claude Code and run `/e4:init` (with the commands installed globally in
`~/.claude/commands/e4/`).

- **How it reaches the knowledge base:** `CLAUDE.md` contains the line `@AGENTS.md`; Claude Code
  expands it at launch. The SessionStart hook injects a memory summary; the vault is read from
  `~/AI-Vault` when local.
- **Existing project with its own `CLAUDE.md`:** add the single line `@AGENTS.md` to it. Without it
  Claude Code ignores `AGENTS.md` (it reads `AGENTS.md` only when there is no `CLAUDE.md`).
- **Hooks on Windows:** run via Git Bash (`bash`) and call `python3` — both must be on PATH.
- **Verify:** reopen the repo — the first message shows `## 🧠 Project Memory (auto-loaded)`.
  Headless check:
  ```bash
  claude -p "Without tools: quote the heading of section 6 of AGENTS.md"   # → "6. Session Summary Rules"
  claude -p "/e4:resume"                                                   # → Resume Summary
  ```

## 4. GitHub Copilot (VS Code, Copilot CLI, Copilot cloud agent) — unverified

Install the portable core (§2). Optionally add the pointer file for Copilot surfaces that read only
`copilot-instructions.md`:

```bash
mkdir -p <repo>/.github
cp ~/AI-Vault/copilot-config/.github/copilot-instructions.md <repo>/.github/   # skip if you already have one
```

- **How it reaches the knowledge base:** Copilot reads `AGENTS.md` at the repo root (VS Code: keep
  `chat.useAgentsMdFile` enabled) and loads Agent Skills from `.agents/skills/`. Ask
  *"resume"* or run the `e4-resume` skill at session start; *"wrap up"* / `e4-end-session` at the end.
- **The vault:** local Copilot sessions can read `~/AI-Vault/User/…` if you allow it. The **cloud
  agent cannot** — keep essential conventions in `.ai-memory/onboarding.md`.
- **Verify:** in Copilot Chat (agent mode) ask *"Which file defines your instructions, and what is the
  session-start read order?"* — it should cite `AGENTS.md` and list the `.ai-memory/` files. Type
  `/` and check that `e4-resume`, `e4-end-session` appear among skills (if your Copilot surface lists skills there).

## 5. Cursor — unverified

Install the portable core (§2). No Cursor-specific files are needed.

- **How it reaches the knowledge base:** Cursor reads `AGENTS.md` (root and nested) and loads Agent
  Skills from `.agents/skills/`. Skills appear in the Agent `/` menu (`/e4-resume`, `/e4-end-session`, …).
- **Optional:** if you want an always-on rule instead, create `.cursor/rules/e4-memory.mdc` with
  `alwaysApply: true` whose body only says "Follow AGENTS.md" — do not copy the rules into it.
- **Verify:** in Agent chat type `/e4-resume`; it should read `.ai-memory/` and post a Resume Summary.

---

## 6. Housekeeping without Claude Code

Claude's SessionEnd hook archives done tasks and rolls up the daily note automatically. For other
agents, run the same scripts yourself (or via cron / Task Scheduler):

```bash
automation/bash/ai-memory.sh daily            # roll today's session files into DailyLogs/
automation/bash/ai-memory.sh archive <repo>   # move done tasks to Archive/tasks/
python automation/python/generate_status.py --project <repo>   # refresh active-tasks.md
```
Windows: `automation\powershell\Ai-Memory.ps1 daily|archive|dashboard|sync`.

## 7. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Claude ignores `AGENTS.md` | `CLAUDE.md` exists without `@AGENTS.md` — add the line. `validate_memory.py --agents` warns about this. |
| Claude asks to approve external imports | the import points outside the repo; keep `AGENTS.md` at the repo root. |
| Skill doesn't appear in Copilot/Cursor | `name` must be lowercase-hyphenated and equal its folder name — run `validate_memory.py --skills-dir .agents/skills`. |
| `active-tasks.md` stale in Copilot/Cursor | no SessionStart hook there; run `generate_status.py` (the skills also do this). |
| `/e4:*` command text differs from skill | regenerate: `python automation/python/sync_agent_adapters.py`; never edit the command directly. |
| `Hook cancelled` (Claude) | a hook exceeded its `timeout`; see `COMMANDS-AND-HOOKS.md`. |

## 8. Known limitations

- Only Claude Code has mechanical (hook) guarantees; elsewhere loading/saving memory depends on the
  model following `AGENTS.md`.
- Copilot and Cursor integrations follow their documented file conventions but were not exercised
  in a live session.
