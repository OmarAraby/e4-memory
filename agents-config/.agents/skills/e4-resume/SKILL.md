---
name: e4-resume
description: "[e4] Re-read the project's .ai-memory/ in order and post a Resume Summary of where work left off. Use at the start of a session, after a context reset, or when the user says resume or asks where we left off."
---

# e4-resume — Reconstruct context from memory

## Step 0 — Refresh the generated view
`active-tasks.md` is a **generated, gitignored view** of `tasks/*.md`. Refresh it before reading so
you never resume off a stale board: run `python3 <path>/generate_status.py --project .`
(search `~/AI-Vault/automation/python/`, then `./scripts/`; on Windows try `python` if `python3` is missing). If the generator isn't found, skip it
and read the existing file — <!-- adapter:regen-fallback -->the view is regenerated the next time the generator runs<!-- /adapter:regen-fallback -->.

## Step 1 — Read the memory in this exact order

1. `.ai-memory/onboarding.md`
2. `.ai-memory/context.md`
3. `.ai-memory/architecture.md`
4. `.ai-memory/active-tasks.md`
5. `.ai-memory/progress.md`
6. **The most recent session file** (see below)
7. `.ai-memory/decisions.md` (index only; read full ADRs only if relevant to the current task)

### Finding the most recent session
e4 keeps **one file per session** in `.ai-memory/sessions/` so parallel branches never conflict.
Filenames are timestamp-prefixed (`YYYY-MM-DD-HHMMSS-<branch>.md`), so they sort chronologically:

- If `.ai-memory/sessions/` exists → list only files matching the session naming contract
  (`ls -1 .ai-memory/sessions/[0-9][0-9][0-9][0-9]-*.md`) and read the **lexically-last** one.
  That is the newest session. Do **not** use a bare `*.md` glob: `sessions/README.md` sorts after
  every date-prefixed name and would be picked as the newest session.
- **Legacy fallback**: if `sessions/` does not exist, read the **top entry** of
  `.ai-memory/session-log.md` (the pre-Tier-2 single shared file). Repos created before the
  per-session redesign still use it; treat it as read-only history and note that the project
  hasn't been migrated.

If the newest session file contains no **TL;DR**, it is an auto-breadcrumb (written when a session
ended without `/e4-end-session`) — say so, and offer to reconstruct what happened from `git log` and
backfill a proper session file.

If any file is missing, note it and suggest `/e4-init`.

## Step 2 — Check for drift
Run `git status --short` and `git log --oneline -5`. If the working tree changed since the last
logged session, that's a sign the last session ended without `/e4-end-session` — flag it.

## Step 3 — Post the Resume Summary (≤8 lines)
```
📋 Resumed: <project>
Phase: <phase> | Health: <🟢/🟡/🔴>
Current task: <TASK-ID — title> (<status>)
Last session: <date> — <TL;DR>
Picking up at: <first next-action from the newest session file>
Blockers: <none/list>
Uncommitted drift since last log: <none / N files — last session may not have been saved>
```

Do not start working until the user confirms the direction.
