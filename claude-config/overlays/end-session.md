---
# e4 — forged by Omar Araby & contributors
description: "[e4] Wrap up: update progress, tasks, sessions/, and write a session summary"
argument-hint: [optional note about this session]
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(date:*), Bash(python3:*), Bash(python:*), Read, Edit, Write
---
<!-- region:facts -->
- Current date/time: !`date "+%Y-%m-%d %H:%M"`
- Filename stamp: !`date "+%Y-%m-%d-%H%M%S"`
- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git"`
- Uncommitted changes: !`git status --short 2>/dev/null || echo "(not a git repository)"`
- Files changed since last commit: !`git diff --name-only HEAD 2>/dev/null || echo "(no commits yet - see uncommitted changes)"`
- Recent commits this session: !`git log --oneline -10 2>/dev/null || echo "(no commits yet)"`
<!-- /region:facts -->
<!-- region:args -->
"$ARGUMENTS"
<!-- /region:args -->
<!-- region:regen-fallback -->
the SessionStart hook regenerates it next session
<!-- /region:regen-fallback -->
<!-- region:scripts-dir -->
!`python3 -c "import os; print(os.environ.get('AI_MEMORY_PYDIR') or os.path.join(os.environ.get('AI_VAULT') or os.path.expanduser('~/AI-Vault'), 'automation', 'python'))"`
<!-- /region:scripts-dir -->
