---
# e4 — forged by Omar Araby & contributors
description: "[e4] Re-read project memory and summarize where we left off"
allowed-tools: Read, Bash(git status:*), Bash(git log:*)
---

# /e4:resume — Reconstruct context from memory

Read the project memory in this exact order, then report:

1. `.ai-memory/onboarding.md`
2. `.ai-memory/context.md`
3. `.ai-memory/architecture.md`
4. `.ai-memory/active-tasks.md`
5. `.ai-memory/progress.md`
6. The **top entry** of `.ai-memory/session-log.md`
7. `.ai-memory/decisions.md` (index only; read full ADRs only if relevant to the current task)

If any file is missing, note it and suggest `/e4:init`.

Then check `git status --short` and `git log --oneline -5` to see if the working tree changed since the last logged session (a sign the last session ended without `/e4:end-session`). If so, flag it.

Finally, post a **Resume Summary** (≤8 lines):
```
📋 Resumed: <project>
Phase: <phase> | Health: <🟢/🟡/🔴>
Current task: <TASK-ID — title> (<status>)
Last session: <date> — <TL;DR>
Picking up at: <first next-action from session-log>
Blockers: <none/list>
Uncommitted drift since last log: <none / N files — last session may not have been saved>
```

Do not start working until the user confirms the direction.

<!-- e4 · forged by Omar Araby & contributors · add your name to CONTRIBUTORS.md when you extend these commands -->
