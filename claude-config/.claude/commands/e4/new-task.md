---
# e4 — forged by Omar Araby & contributors
description: "[e4] Create a new task with a collision-free ID; active-tasks.md regenerates from it"
argument-hint: <short task title>
allowed-tools: Bash(date:*), Bash(python3:*), Bash(python:*), Bash(ls:*), Read, Write, Edit
---

# /e4:new-task — Create a tracked task

Create a new task for: **$ARGUMENTS**

1. **Build a collision-free ID.** Do NOT use a sequential `TASK-NNN` counter — two parallel branches
   would both pick the same next number and collide (add/add merge conflict) when merged. Use a
   timestamp-based ID instead:
   - stamp: !`date "+%Y%m%d-%H%M%S"`
   - slug: lowercase the title, replace each run of non-alphanumeric characters with `-`, trim leading/trailing `-`
     (e.g. "Wire gRPC notification" → `wire-grpc-notification`).
   - **ID = `TASK-<stamp>-<slug>`** (e.g. `TASK-20260624-164530-wire-grpc-notification`).
2. Create `.ai-memory/tasks/<ID>.md` with front-matter and sections:
   ```
   ---
   id: <ID>
   title: "$ARGUMENTS"
   status: todo            # todo | in-progress | blocked | in-review | done
   priority: medium
   created: <today>
   ---
   # <title>
   ## Goal
   ## Context
   ## Acceptance Criteria
   - [ ] ...
   ## Implementation Plan
   ## Files Likely Affected
   ## Checkpoints
   ## Blockers
   ## Notes / Log
   ```
3. **Do NOT edit `active-tasks.md`** — it is a generated, gitignored view. Regenerate it from the task
   files: run `python3 <path>/generate_status.py --project .` (search `~/AI-Vault/automation/python/`,
   then `./scripts/`). If the generator isn't found, skip — the SessionStart hook regenerates it next session.
4. Print the created ID, title, and the path.

Ask one clarifying question only if the title is too vague to write a Goal.

<!-- e4 · forged by Omar Araby & contributors · add your name to CONTRIBUTORS.md when you extend these commands -->
