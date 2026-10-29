---
# e4 — forged by Omar Araby & contributors
description: "[e4] Re-read project memory and summarize where we left off"
argument-hint: [full]
allowed-tools: Read, Bash(ls:*), Bash(git status:*), Bash(python3:*)
model: sonnet
---

# /e4:resume — Where did we leave off?

## Case 1 — the SessionStart summary is in your context (the usual case)
If this conversation already contains the hook's "Project memory — e4" block and the user did
**not** ask for a full resume (`$ARGUMENTS` is not `full`), read **no files**. Post the Resume
Summary below from that block alone, then stop.

## Case 2 — no injected summary, or `/e4:resume full`
1. Refresh the generated view: `python3 .claude/hooks/e4.py status --project .`
2. Read, in order: `.ai-memory/onboarding.md`, `context.md`, `architecture.md`, `active-tasks.md`,
   `progress.md`, the **newest** session file, then only the index table of `decisions.md`.
   - Newest session: `ls -1 .ai-memory/sessions/[0-9][0-9][0-9][0-9]-*.md` and take the
     lexically-last name (a bare `*.md` glob would wrongly pick `sessions/README.md`).
     If it is an `*-auto.md` breadcrumb or its TL;DR is still `<!-- e4:fill TL;DR -->`, the session
     wasn't saved: also read the newest file that has a real TL;DR, and say so in the summary.
   - Legacy: no `sessions/` → read the top entry of `.ai-memory/session-log.md`.
   - Missing files → note them and suggest `/e4:init`.
3. Run `git status --short`; if files are uncommitted, note the count as drift.

## Resume Summary (≤7 lines)
```
📋 Resumed: <project>
Phase: <phase> | Health: <🟢/🟡/🔴>
Current task: <TASK-ID — title> (<status>)
Last session: <date> — <TL;DR>
Picking up at: <next action #1>
Blockers: <none/list>
Unsaved session / drift: <none / details>
```

Do not start working until the user confirms the direction. Backfill an unsaved session only if
the user asks (via `/e4:end-session`).

<!-- e4 · forged by Omar Araby & contributors · add your name to CONTRIBUTORS.md when you extend these commands -->
