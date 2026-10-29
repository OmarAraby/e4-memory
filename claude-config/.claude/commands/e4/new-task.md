---
# e4 — forged by Omar Araby & contributors
description: "[e4] Create a new task with a collision-free ID; active-tasks.md regenerates from it"
argument-hint: <short task title> [-- extra detail]
allowed-tools: Bash(python3:*), Read, Edit
model: haiku
---

# /e4:new-task — Create a tracked task

The task file has already been created by `e4_task.py` (timestamp ID, template, `status: todo`,
`active-tasks.md` regenerated):

```!
python3 .claude/hooks/e4.py task new - <<'E4_ARGS'
$ARGUMENTS
E4_ARGS
```

User input: $ARGUMENTS

Your job:
- If the output above starts with `e4: error`, show it to the user and stop.
- If the user input contains ` -- ` followed by extra detail, turn that detail into a Goal line
  and `- [ ]` Acceptance Criteria in the new file — one Read, one Edit. Nothing else.
- Otherwise do nothing to the file.

Then reply with one line: the task path.

<!-- e4 · forged by Omar Araby & contributors · add your name to CONTRIBUTORS.md when you extend these commands -->
