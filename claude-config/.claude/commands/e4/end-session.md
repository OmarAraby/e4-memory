---
# e4 — forged by Omar Araby & contributors
description: "[e4] Wrap up: update progress, tasks, session-log, and write a session summary"
argument-hint: [optional note about this session]
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(date:*), Read, Edit, Write
---

# /e4:end-session — Persist this session to memory

You are closing out the current work session. Update the project's memory so the **next** session can resume instantly. Follow every step. Do not skip the session-log.

## Step 0 — Gather facts (don't guess)
Collect ground truth before writing:
- Current date/time: !`date "+%Y-%m-%d %H:%M"`
- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git"`
- Uncommitted changes: !`git status --short 2>/dev/null`
- Files changed since last commit: !`git diff --name-only HEAD 2>/dev/null`
- Recent commits this session: !`git log --oneline -10 2>/dev/null`

Also review THIS conversation to recall: what was attempted, what decisions were made, what's blocking, and what the next concrete step is. The user's note (if any): "$ARGUMENTS"

## Step 1 — Update `.ai-memory/session-log.md`  (REQUIRED — do this first)
**Prepend** a new entry at the top (below the title/front-matter, above the previous newest entry):

```
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

## Step 2 — Update `.ai-memory/progress.md`
- Move finished items into **Completed ✅** with today's date.
- Update **In Progress 🔄** and **Up Next ⏳**.
- Bump **Last updated** to today.
- Adjust the completion % and the Health indicator (🟢/🟡/🔴) to match reality.
- Add a line to **Recently Changed**.

## Step 3 — Update `.ai-memory/active-tasks.md`
- Update the **Current Task** status, its **Checkpoint**, and its **next concrete step**.
- If the current task is done, move it to Recently Completed and promote the top item from **Next Up** into the Current Task slot.
- Update **Blocked** / **In Review** as needed.
- If a task file exists in `tasks/`, update its Checkpoints/Notes too.

## Step 4 — Update `.ai-memory/decisions.md` (only if needed)
If a lasting architectural decision was made this session, add an ADR entry (Context / Decision / Alternatives / Consequences) and add it to the index table. If none, skip.

## Step 5 — Print the session summary
Output a concise summary to the user (this is the "Session Summary" deliverable):
```
✅ Session saved
TL;DR: <one line>
Completed: <count> | In progress: <current task> | Blockers: <none/list>
Next session starts with: <first next-action>
Files updated: session-log.md, progress.md, active-tasks.md[, decisions.md]
```

## Rules
- The session-log entry is mandatory even for short sessions.
- Keep entries factual and concise; prefer bullets.
- Never fabricate file changes — use the git output from Step 0.
- Do not push to git or run destructive commands.

<!-- e4 · forged by Omar Araby & contributors · add your name to CONTRIBUTORS.md when you extend these commands -->
