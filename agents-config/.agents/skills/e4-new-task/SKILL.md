---
name: e4-new-task
description: "[e4] Create a new tracked task file in .ai-memory/tasks/ with a collision-free timestamp ID; active-tasks.md regenerates from it. Use when the user asks to add, create or track a task."
---

# e4-new-task — Create a tracked task

Create a new task for: **<!-- adapter:args -->the task title the user gave with this request<!-- /adapter:args -->**

1. **Build a collision-free ID.** Do NOT use a sequential `TASK-NNN` counter — two parallel branches
   would both pick the same next number and collide (add/add merge conflict) when merged. Use a
   timestamp-based ID instead:
   - stamp: <!-- adapter:stamp -->run `date "+%Y%m%d-%H%M%S"` [PowerShell: `Get-Date -Format "yyyyMMdd-HHmmss"`] and use its output<!-- /adapter:stamp -->
   - slug: lowercase the title, replace each run of non-alphanumeric characters with `-`, trim leading/trailing `-`
     (e.g. "Wire gRPC notification" → `wire-grpc-notification`).
   - **ID = `TASK-<stamp>-<slug>`** (e.g. `TASK-20260624-164530-wire-grpc-notification`).
2. Create `.ai-memory/tasks/<ID>.md` with front-matter and sections:
   ```
   ---
   id: <ID>
   title: "<title>"
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
   files: run `python3 "<scripts dir>/generate_status.py" --project .` where `<scripts dir>` is
   <!-- adapter:scripts-dir -->`$AI_MEMORY_PYDIR` if set, else `$AI_VAULT/automation/python` if `AI_VAULT` is set, else `~/AI-Vault/automation/python` (read the variables with `echo "$AI_MEMORY_PYDIR" "$AI_VAULT"`; PowerShell: `$env:AI_MEMORY_PYDIR`, `$env:AI_VAULT`)<!-- /adapter:scripts-dir -->;
   if the script isn't there, try `./scripts/`. Quote the path (it may contain spaces); on Windows try
   `python` if `python3` is missing. If the generator isn't found, skip — <!-- adapter:regen-fallback -->the view is regenerated the next time the generator runs<!-- /adapter:regen-fallback -->.
4. Print the created ID, title, and the path.

Ask one clarifying question only if the title is too vague to write a Goal.
