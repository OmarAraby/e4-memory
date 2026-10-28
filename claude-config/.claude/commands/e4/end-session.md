---
# e4 — forged by Omar Araby & contributors
description: "[e4] Wrap up: update progress, tasks, sessions/, and write a session summary"
argument-hint: [optional note about this session]
allowed-tools: Bash(python3:*), Read, Edit
---

# /e4:end-session — Persist this session to memory

`e4_session.py` has already written the session file with every mechanical fact (time, branch,
files changed, commits, uncommitted yes/no). Its output — the file path, then the in-progress tasks:

```!
python3 .claude/hooks/e4.py session draft --note - <<'E4_ARGS'
$ARGUMENTS
E4_ARGS
```

If that output starts with `e4: error`, show it to the user and stop.

## 1. Fill the draft — one Read, one Edit
Replace every `<!-- e4:fill ... -->` placeholder in that file, from **this conversation** only.
They form one contiguous block from `**TL;DR**` to `test_status:` — replace it in a single Edit.
Do not touch the git-derived sections below it.
- **TL;DR**: 2–3 sentences — what changed and where things stand. The next session resumes from it.
- **Did**: short bullets of concrete work. **Decisions**: lasting ones, or "None new".
- **State**: what works / what doesn't. **Blockers**: list, or "None".
- **Next actions**: numbered, concrete; #1 is the first thing the next session does.
- **last_command** / **test_status**: from the conversation; `not run` if tests weren't run.

## 2. Task status — via the script, never by hand
For each task whose state changed this session, run:
`python3 .claude/hooks/e4.py task set-status <TASK-id> <todo|in-progress|blocked|in-review|done> --note "<few words>"`
It updates the task file, logs a checkpoint, and regenerates `active-tasks.md`.

## 3. Only if something actually changed
- `progress.md`: edit **only** if Phase, Health, or a Milestone changed.
- `decisions.md`: add an ADR (Context / Decision / Alternatives / Consequences + index row) **only**
  if a lasting decision was made.
Do not open `progress.md`, task files, or `decisions.md` unless you are about to change them.

## 4. Reply with one line
`✅ Session saved → <session file path> · Next: <next action #1>`

Never fabricate file changes, push, or run destructive commands.

<!-- e4 · forged by Omar Araby & contributors · add your name to CONTRIBUTORS.md when you extend these commands -->
