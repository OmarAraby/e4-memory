---
tags: [project, memory, index]
---

# .ai-memory — Project Memory

This directory is the **persistent brain** for this project. It survives sessions, restarts, and crashes.

## File Reference
| File | Purpose | Update frequency |
|------|---------|-----------------|
| `onboarding.md` | Entry point. Read first. Orientation + setup. | Rarely |
| `context.md` | Domain, goals, constraints, glossary. | When scope changes |
| `architecture.md` | How the system is built. | When architecture changes |
| `decisions.md` | Log of architectural decisions (ADRs). | Per decision |
| `progress.md` | Phase, health, milestones. Low-churn fields only. | When phase/health changes |
| `active-tasks.md` | ⚙️ **Generated** view of `tasks/` — never edit by hand. Gitignored. | Auto, every session |
| `sessions/` | Session history, **one file per session**. Crash recovery. | Every session |
| `tasks/` | Detailed per-task files (`TASK-<timestamp>-<slug>.md`). Source of truth for task state. | Per task |

> Two files are deliberately **not** hand-maintained: `active-tasks.md` is regenerated from
> `tasks/*.md` by `generate_status.py`, and `sessions/` is append-only (one new file per session,
> never an edit). Both exist so parallel git branches never conflict on memory.

## Read Order (Claude)
`onboarding → context → architecture → active-tasks → progress → decisions → sessions/ (newest file)`

The newest session is the **lexically-last** file in `sessions/` — names are timestamp-prefixed,
so they sort chronologically.

> **Legacy**: repos created before the per-session redesign have a single `session-log.md`
> instead of `sessions/`. It is still read as a fallback, but new entries go to `sessions/`.

## Commit this directory
`.ai-memory/` **should be committed to git**. It's part of the project's knowledge.
(Exception: if it contains secrets — it shouldn't.)
