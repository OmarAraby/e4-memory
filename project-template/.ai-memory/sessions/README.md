---
tags: [project, session, memory, index]
---

# sessions/ — one file per session

Session history lives here as **one markdown file per session**. Nothing is ever appended to a
shared file, which is why parallel branches never produce merge conflicts on memory.

- **Filename**: `YYYY-MM-DD-HHMMSS-<branch>.md` (branch sanitized — every non-alphanumeric
  character becomes `-`; no git → `nogit`). Timestamp-first means the files sort chronologically,
  so **the lexically-last file is the newest session**.
- **Written by**: `/e4:end-session` (the real, intelligent entry).
- **Also written by**: the `SessionEnd` hook, which drops an `*-auto.md` breadcrumb if a session
  ends without `/e4:end-session`. A breadcrumb is a placeholder — the next session should
  reconstruct the details from `git log` and write a proper file.
- **Never edit an existing session file.** History is immutable; corrections go in a new session.

Every entry must carry a **TL;DR** — it is the anchor `/e4:resume` and the `SessionStart` hook
read to rebuild context. A file without one is treated as incomplete.

> **Legacy**: repos created before the per-session redesign have a single `session-log.md`
> instead. It is still read as a fallback, but it is now history — all new entries go here.
