---
# e4 — forged by Omar Araby & contributors
description: "[e4] Create a new task file and register it in active-tasks.md"
argument-hint: <short task title>
allowed-tools: Bash(ls:*), Bash(date:*), Read, Write, Edit
---

# /e4:new-task — Create a tracked task

Create a new task for: **$ARGUMENTS**

1. Determine the next ID by listing `.ai-memory/tasks/` and finding the highest `TASK-NNN`. Use the next number (zero-padded, e.g. TASK-007).
2. Create `.ai-memory/tasks/TASK-NNN.md` with front-matter (`type: task`, `status: todo`, `priority: medium`, `created: <today>`) and sections: Goal, Context, Acceptance Criteria (checkboxes), Implementation Plan, Files Likely Affected, Checkpoints, Blockers, Notes/Log.
3. Add the task to `.ai-memory/active-tasks.md` under **🔜 Next Up** (or set as Current Task if there is none).
4. Print the created ID, title, and the path.

Ask one clarifying question only if the title is too vague to write a Goal.

<!-- e4 · forged by Omar Araby & contributors · add your name to CONTRIBUTORS.md when you extend these commands -->
