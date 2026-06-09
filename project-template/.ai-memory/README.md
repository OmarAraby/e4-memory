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
| `progress.md` | What's done / in-progress / next. | Every session |
| `active-tasks.md` | Current + next tasks (lean). | Every session |
| `session-log.md` | Append-only session history. Crash recovery. | Every session |
| `tasks/` | Detailed per-task files (TASK-NNN.md). | Per task |

## Read Order (Claude)
`onboarding → context → architecture → active-tasks → progress → decisions → session-log (latest)`

## Commit this directory
`.ai-memory/` **should be committed to git**. It's part of the project's knowledge.
(Exception: if it contains secrets — it shouldn't.)
