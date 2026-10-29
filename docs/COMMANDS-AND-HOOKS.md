# Implementing Custom Commands & Hooks

How to wire `/e4:init`, `/e4:end-session`, and automatic session hooks into Claude Code. Verified against the current Claude Code docs (slash commands + hooks reference).

---

## The key concept: commands vs hooks

Your goal — *"instead of relying on Claude to remember, it just does it"* — is solved by **two different mechanisms** working together. Understanding the split is the whole game:

| | **Slash command** (`.claude/commands/*.md`) | **Hook** (`settings.json`) |
|---|---|---|
| Trigger | You **type** `/e4:end-session` | Fires **automatically** on a lifecycle event |
| What runs | Instructions sent to **Claude** (the model acts) | A **script** you provide |
| Can write an intelligent summary? | ✅ Yes — Claude has the session context | ❌ No — it's just a script; at SessionEnd the model is already done |
| Best for | Producing **content** (the summary, the updates) | **Mechanical** guarantees + auto-loading context |

**The honest limitation:** a `SessionEnd` hook *cannot* make Claude write a session summary, because the session is ending and the model won't generate anything more. So:

- **Content that needs intelligence** → a command (`/e4:end-session`). The model writes the summary.
- **Guarantees that don't need intelligence** → hooks. Auto-load memory at start; drop a breadcrumb if you forgot to log; archive done tasks; refresh the daily roll-up.
- **The "remembering" itself** → the **SessionStart hook** (auto-injects memory every session, zero reliance on the model) plus an optional **Stop hook** (nudges Claude to run `/e4:end-session` when work happened but wasn't logged).

This combination is why you stop depending on Claude's discretion: memory is loaded mechanically, and the one human step left (`/e4:end-session`) is both reminded automatically *and* backstopped by a breadcrumb if skipped.

---

## How custom slash commands work

A command is just a markdown file. **The filename becomes the command name**, and a subdirectory becomes a namespace — `commands/e4/init.md` → `/e4:init`. (e4 namespaces its commands so they can't collide with Claude Code's own `/resume`.) The file's body becomes a prompt sent to Claude when you invoke it.

**Locations:**
- `.claude/commands/` — project-scoped, commit to git, shared with the team.
- `~/.claude/commands/` — personal, available in every project.

**Optional YAML frontmatter** (between `---` fences at the top):
- `description:` — shown in the `/` picker and `/help`.
- `argument-hint:` — placeholder text showing expected input.
- `allowed-tools:` — restricts which tools the command may use, e.g. `Bash(git diff:*), Read, Edit`. Narrow = safer.
- `model:` — the model for the rest of that turn: an alias (`sonnet`, `haiku`, `opus`), a full model ID, or `inherit`.

**Which model each e4 command uses.** The bookkeeping now happens in scripts, so the commands pin
cheaper models: `/e4:end-session` and `/e4:resume` → `sonnet` (they summarise), `/e4:new-task` and
`/e4:init` → `haiku` (mechanical). The pin lasts only for that turn; your next prompt is back on the
session model. To override:
- per command: edit its `model:` line — another alias, a full ID such as `claude-opus-5-5`, or
  `inherit` to always use the session model;
- globally: `ANTHROPIC_DEFAULT_SONNET_MODEL` / `ANTHROPIC_DEFAULT_HAIKU_MODEL` remap what the aliases resolve to;
- an organisation `availableModels` allowlist that excludes the pinned model makes Claude Code ignore
  the pin and stay on the session model.

> Verified on Claude Code 2.1.312: in headless `claude -p` runs the command is invoked through the
> Skill tool and the pin is **not** applied (the session model answers). The docs say it applies in
> interactive sessions; check with your transcript's `message.model` after running a command.
- `disable-model-invocation:` — if `true`, only you can trigger it (Claude won't auto-run it).

**Body placeholders:**
- `$ARGUMENTS` — everything you type after the command.
- `$1`, `$2`, … — positional arguments.
- `@path/to/file` — injects that file's contents.
- `` !`some command` `` — runs the shell command at invocation time and embeds its output (the command must be permitted by `allowed-tools`). This is how `/e4:end-session` pulls live `git status`/`git diff` before writing.

### Commands that run scripts: `.claude/hooks/e4.py`

The bookkeeping commands embed a script's output with a fenced `` ```! `` block. Three behaviours of
Claude Code (checked on 2.1.312) shape how that block is written — keep them in mind when adding one:

1. **`$ARGUMENTS` is pasted into the shell text before bash parses it.** `"$ARGUMENTS"` in a `!` line
   lets quotes, backticks and `$(...)` in user input execute. e4 passes arguments through a quoted
   heredoc instead (`<<'E4_ARGS'`), and the launcher substitutes that stdin text for a `-` argument.
2. **Shell variables are rejected by the permission check** (`$AI_MEMORY_PYDIR/...`, `${X:-y}`), so
   commands call the fixed project-relative launcher `.claude/hooks/e4.py`, which finds the scripts
   (`$AI_MEMORY_PYDIR` → `$AI_VAULT/automation/python` → `~/AI-Vault/automation/python` → `./scripts`).
3. **A non-zero exit aborts the whole command.** The launcher always exits 0 and prints failures as
   `e4: error: ...` on stdout, which the command tells the model to relay.

`/e4:init` installs `e4.py` with the other hook files. If a command fails with "Shell command failed",
the project is missing `.claude/hooks/e4.py` — run `/e4:init` (it only adds missing files).

> Note: older guides show a `/project:command` prefix. Current Claude Code uses the bare `/command` form (filename → name). Subdirectories namespace commands (e.g. `commands/mem/save.md` → `/mem:save`).

---

## How hooks work

Hooks live in **`settings.json`** under a top-level `hooks` key — at `.claude/settings.json` (project) or `~/.claude/settings.json` (global). Each event maps to handlers; a command handler receives event JSON on **stdin** and can return output.

The events this system uses:

- **`SessionStart`** — fires on `startup`, `resume`, and `clear`. **Its stdout is injected into Claude's context.** This is the auto-load mechanism. Keep it fast.
- **`SessionEnd`** — fires when the session closes (`clear|resume|logout|prompt_input_exit`). Receives `session_id`, `reason`, `transcript_path`. Runs a script only — *cannot* prompt the model. Used as a mechanical safety net.
- **`Stop`** — fires when Claude finishes a response (once per turn). Can inject `additionalContext` (a nudge) or even block to force continuation. Used for the optional gentle reminder.

Config shape:
```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "startup|resume|clear",
        "hooks": [ { "type": "command", "command": "bash .claude/hooks/session_start.sh", "timeout": 30 } ] }
    ],
    "SessionEnd": [
      { "hooks": [ { "type": "command", "command": "bash .claude/hooks/session_end.sh", "timeout": 60 } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "bash .claude/hooks/stop_reminder.sh", "timeout": 15 } ] }
    ]
  }
}
```

**Critical gotcha — timeouts:** if a hook runs longer than its timeout you get `Hook cancelled`. Keep hooks quick; push slow work into a backgrounded subshell that returns immediately:
```bash
( slow_command ) >/dev/null 2>&1 &
exit 0
```
The provided `session_end.sh` does exactly this for archiving and the daily roll-up.

---

## Installation (step by step)

Assuming the package is unzipped and your global vault is at `~/AI-Vault`:

```bash
# 1. Per project: copy the .claude config into the repo
cp -r ai-memory-system/claude-config/.claude  /path/to/your/project/.claude

# 2. Make the hook scripts executable
chmod +x /path/to/your/project/.claude/hooks/*.sh

# 3. Point the hooks at your Python automation (used by session_end.sh).
#    Either export these in your shell profile, or edit the script defaults:
export AI_VAULT="$HOME/AI-Vault"
export AI_MEMORY_PYDIR="$HOME/AI-Vault/automation/python"
export AI_PROJECTS_ROOT="$HOME/code"

# 4. (Optional) make the commands available in ALL projects instead of one:
cp -r ai-memory-system/claude-config/.claude/commands/e4  ~/.claude/commands/e4

# 5. Open the project in Claude Code.
#    - SessionStart hook auto-injects memory (you'll see it summarize on open).
#    - Type /e4:init once if .ai-memory/ doesn't exist yet.
#    - Work normally.
#    - Type /e4:end-session to save (or get nudged by the Stop hook).
```

**Windows:** either install Git Bash and keep the `bash .claude/hooks/*.sh` commands, or translate the hooks to PowerShell and change the `command` fields to `powershell -File .claude/hooks/SessionStart.ps1`. The `/e4:*` commands call `python3 .claude/hooks/e4.py`, so `python3` must be on PATH for them too.

---

## What each piece does in practice

**`/e4:init [name]`** — checks for existing `.ai-memory/` (won't clobber), runs the bundled initializer if present or scaffolds the files itself, installs `CLAUDE.md`, and prints next steps. One command, full setup.

**`/e4:end-session [note]`** — the workhorse, split so the model only does judgment. `e4_session.py draft` collects the facts (time, branch, `git status`, changed file *names* — never diff contents — and commits since the last session file) and writes a **new file** `.ai-memory/sessions/YYYY-MM-DD-HHMMSS-<branch>.md` with `<!-- e4:fill ... -->` placeholders for TL;DR, Did, Decisions, State, Blockers, Next actions and two checkpoint fields. The model fills that one contiguous block in a single edit, runs `e4_task.py set-status` for tasks whose state changed, and touches `progress.md` / `decisions.md` only if Phase/Health/a Milestone changed or a lasting decision was made. It replies with one line: the file path and the first next action. An unfilled draft is still "incomplete" to the hooks (they ignore a TL;DR that is the `e4:fill TL;DR` placeholder), and re-running the draft refreshes it in place.

**`/e4:resume [full]`** — posts a Resume Summary. If the SessionStart summary is already in context it reads **no files** and summarises from that; it reads the memory files in order only when the injected summary is missing (hooks not installed) or you pass `full`.

**`/e4:new-task <title> [-- detail]`** — `e4_task.py` allocates a timestamp-based ID (`TASK-<YYYYMMDD-HHMMSS>-<slug>`, never a sequential counter, so parallel branches can't collide), writes the task file, and regenerates `active-tasks.md` — no model tokens. The model only turns optional ` -- detail` into acceptance criteria. Status changes go through `e4_task.py set-status <id> <status> [--note]`, which also logs a dated checkpoint line.

**`session_start.sh`** (hook) — every session, regenerates `active-tasks.md` from `tasks/*.md`, then prints a compact resume (~250 tokens on a typical project): Phase/Health/task counts (≤4 lines), the current task (≤5 lines), and only the **TL;DR + Next actions** of the newest *saved* session. This output **is** the resume — the contract tells Claude to open individual memory files only when the task needs them. If the newest session is an auto-breadcrumb or an unfilled draft, it adds one line saying so; Claude backfills it only if you ask (no unprompted git archaeology).

**`session_end.sh`** (hook) — if you forgot `/e4:end-session`, writes a dated breadcrumb file to `sessions/` so the session is never *completely* unrecorded, then (backgrounded) archives completed tasks and regenerates the daily summary.

**`context_nudge.py`** (hook, `UserPromptSubmit`) — long sessions that drift across tasks were most of the token bill, because every turn re-sends all earlier context. On each prompt this reads the **tail** of the transcript (the latest main-thread assistant `usage`: input + cache-read + cache-creation tokens; falls back to file size ÷ 4) and, once per 80k-token band (`E4_CONTEXT_NUDGE_TOKENS` to change), adds one line suggesting `/e4:end-session` then `/clear`. If the prompt names a `TASK-YYYYMMDD-HHMMSS` that isn't the in-progress task, it adds one line suggesting a checkpoint + `/clear` before switching (once per task per session). State lives in the OS temp dir keyed by session id. It never blocks a prompt: any error exits 0 silently. `UserPromptSubmit` takes no matcher, so it runs on every prompt (~0.1 s).

**`stop_reminder.sh`** (hook, optional) — once per session, if there are uncommitted changes and no session file logged today, injects a one-line nudge to run `/e4:end-session`. Soft by default; a commented block shows how to make it hard-block instead (subject to the Stop-hook block cap that prevents loops).

---

## Recommended workflow with all of this on

1. **Open project** → SessionStart hook loads memory; Claude greets you with where you left off.
2. **Work** → normal coding. (PostToolUse formatting/lint hooks can be added if you like.)
3. **Wrap up** → type `/e4:end-session`. If you forget and just close, the Stop hook reminds you mid-session, and the SessionEnd hook leaves a breadcrumb as last resort.
4. **Next session** → instant resume, because step 2/3 of the previous one populated memory.

The result: the *mechanical* parts never depend on Claude remembering (hooks handle them), and the *intelligent* part (`/e4:end-session`) is reminded and backstopped — so in practice it always gets done.
