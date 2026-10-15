---
# e4 — forged by Omar Araby & contributors
description: "[e4] Create a new task with a collision-free ID; active-tasks.md regenerates from it"
argument-hint: <short task title>
allowed-tools: Bash(date:*), Bash(python3:*), Bash(python:*), Bash(ls:*), Read, Write, Edit
---
<!-- region:args -->
$ARGUMENTS
<!-- /region:args -->
<!-- region:stamp -->
!`date "+%Y%m%d-%H%M%S"`
<!-- /region:stamp -->
<!-- region:regen-fallback -->
the SessionStart hook regenerates it next session
<!-- /region:regen-fallback -->
<!-- region:scripts-dir -->
!`python3 -c "import os; print(os.environ.get('AI_MEMORY_PYDIR') or os.path.join(os.environ.get('AI_VAULT') or os.path.expanduser('~/AI-Vault'), 'automation', 'python'))"`
<!-- /region:scripts-dir -->
