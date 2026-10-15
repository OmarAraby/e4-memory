---
name: e4-end-session
description: "[e4] Wrap up a work session: write a new .ai-memory/sessions/ file and update progress, tasks and decisions so the next session can resume. Use when the user says wrap up, checkpoint, end session, or save memory."
---

# e4-end-session — Persist this session to memory

You are closing out the current work session. Update the project's memory so the **next** session can resume instantly. Follow every step. Do not skip the session file.

## Step 0 — Gather facts (don't guess)
Collect ground truth before writing:
<!-- adapter:facts -->
Run each command and use its real output (PowerShell equivalents in brackets):
- Current date/time: `date "+%Y-%m-%d %H:%M"` [`Get-Date -Format "yyyy-MM-dd HH:mm"`]
- Filename stamp: `date "+%Y-%m-%d-%H%M%S"` [`Get-Date -Format "yyyy-MM-dd-HHmmss"`]
- Branch: `git rev-parse --abbrev-ref HEAD` (no git → `no-git`)
- Uncommitted changes: `git status --short`
- Files changed since last commit: `git diff --name-only HEAD`
- Recent commits this session: `git log --oneline -10`
<!-- /adapter:facts -->

Also review THIS conversation to recall: what was attempted, what decisions were made, what's blocking, and what the next concrete step is. The user's note (if any): <!-- adapter:args -->any note the user gave with this request<!-- /adapter:args -->

## Step 1 — Write a new session file in `.ai-memory/sessions/`  (REQUIRED — do this first)
e4 keeps **one file per session** (never a shared file) so branches never conflict on memory.
Create `.ai-memory/sessions/` if it doesn't exist, then **write a NEW file** (never edit an existing one):

- **Filename**: `<Filename stamp>-<branch>.md` — use the Filename stamp from Step 0 and the branch with
  every non-alphanumeric character replaced by `-` (e.g. `feature/x` → `feature-x`; no git → `nogit`).
  Example: `.ai-memory/sessions/2026-06-18-164530-feature-x.md`
- **Contents** (this exact shape):

```
---
type: session
date: <today's date>
branch: <branch>
---
## Session — <today's date>
**Time**: <start–end if known, else just end time>
**Branch**: <branch>

**TL;DR**: <2–3 sentences — the single most important section>

**Did**:
- <bullets of concrete work>

**Decisions**: <new decisions, or "None new">

**Files changed**:
- <from git diff above>

**State**: <what works / what doesn't right now>

**Blockers**: <list, or "None">

**Next actions**:
1. <the FIRST thing next session should do — be concrete>
2. ...

**Checkpoint**:
```
last_command: <last meaningful command run>
working_file: <file in progress, if any>
test_status: <pass / fail / not run>
uncommitted_changes: <yes/no>
```
```

> Do NOT prepend to `.ai-memory/session-log.md` — that single shared file caused cross-branch merge conflicts. If a legacy `session-log.md` exists, leave it as a historical archive; all new entries go only in `sessions/`.

## Step 2 — Update `.ai-memory/progress.md` (stable fields only)
progress.md now holds only **deliberate, low-churn** fields so it rarely conflicts across branches:
- Update **Phase** and the **Health** indicator (🟢/🟡/🔴) if they changed.
- Update **Milestones** when one is hit.
Do NOT hand-bump a completion % or keep a per-session "Recently Changed" list here — task completion
is derived in the generated active-tasks view, and per-session history already lives in `sessions/`.

## Step 3 — Update task state in `.ai-memory/tasks/` (NOT active-tasks.md)
`active-tasks.md` is a **generated, gitignored view** — never hand-edit it.
- In the relevant `tasks/<id>.md` file, set `status:` to one of `todo` / `in-progress` / `blocked` / `in-review` / `done`, and update its **Checkpoints** / **Notes**.
- Then regenerate the view: run `python3 <path>/generate_status.py --project .` (search `~/AI-Vault/automation/python/`, then `./scripts/`; on Windows try `python` if `python3` is missing). If the generator isn't found, skip — <!-- adapter:regen-fallback -->the view is regenerated the next time the generator runs<!-- /adapter:regen-fallback -->.

## Step 4 — Update `.ai-memory/decisions.md` (only if needed)
If a lasting architectural decision was made this session, add an ADR entry (Context / Decision / Alternatives / Consequences) and add it to the index table. If none, skip.

## Step 5 — Print the session summary
Output a concise summary to the user (this is the "Session Summary" deliverable):
```
✅ Session saved
TL;DR: <one line>
Completed: <count> | In progress: <current task> | Blockers: <none/list>
Next session starts with: <first next-action>
Files updated: sessions/<new file>, tasks/<updated>[, progress.md][, decisions.md]
```

## Rules
- The session file is mandatory even for short sessions (one new file per session).
- Keep entries factual and concise; prefer bullets.
- Never fabricate file changes — use the git output from Step 0.
- Do not push to git or run destructive commands.
