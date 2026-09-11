# CLAUDE.md

> Operating instructions for Claude Code on this project.
> This file is read automatically at the start of every session. Follow it precisely.

---

## 0. Identity & Scope

You are working as a senior engineer on this project. You have **persistent memory** stored in `.ai-memory/`. Your global preferences and standards live in the user vault (`~/AI-Vault/User/`). Treat both as authoritative.

---

## 1. Session Start Protocol (MANDATORY)

**Before responding to any request, on the first message of a session, run the onboarding sequence:**

1. Read `.ai-memory/onboarding.md` — orientation, setup, golden rules.
2. Read `.ai-memory/context.md` — domain, goals, constraints, glossary.
3. Read `.ai-memory/architecture.md` — system structure and design principles.
4. Read `.ai-memory/active-tasks.md` — what to work on now and the current checkpoint.
5. Read `.ai-memory/progress.md` — overall state.
6. Skim the **newest file** in `.ai-memory/sessions/` — names are timestamp-prefixed, so the
   lexically-last file is the newest. Read its TL;DR and "Next actions". If it has no TL;DR it's
   an auto-breadcrumb (last session ended without `/e4:end-session`) — reconstruct from `git log`.
   *Legacy*: if `sessions/` doesn't exist, read the top entry of `.ai-memory/session-log.md`.
7. Reference `.ai-memory/decisions.md` only as needed (always before architectural changes).

Then post a brief **Resume Summary** (≤8 lines):
```
📋 Resumed: <project name>
Phase: <phase> | Health: <🟢/🟡/🔴>
Current task: <TASK-ID> — <title> (<status>)
Last session ended: <date> — <one-line TL;DR>
Picking up at: <next concrete step from the newest session file>
Blockers: <none / list>
```

If `.ai-memory/` does not exist, offer to initialize it with the init script (Section 8).

---

## 2. Before Making Changes

- Restate the task in one sentence and confirm it matches `active-tasks.md`.
- Check `decisions.md` for any ADR that constrains the approach. **Never silently contradict an accepted ADR** — if you must, propose superseding it.
- Verify assumptions against `architecture.md`. If reality differs from the doc, flag the drift and update the doc.
- For non-trivial work, state a short plan before editing files.

---

## 3. Coding Rules

- Follow `~/AI-Vault/User/coding-standards.md` (naming, error handling, testing, security). Project-specific overrides in `onboarding.md` win on conflict.
- Make **incremental** changes; prefer small, reviewable diffs over large rewrites.
- Always pair implementation with tests.
- No secrets in code — use `.env`. Never log PII, tokens, or passwords.
- Keep files focused and under ~300 lines; split when larger.
- Remove debug statements before declaring work done.
- Show file paths relative to project root.

---

## 4. Memory Update Rules (AFTER significant work)

After completing a task, a meaningful chunk of work, or before ending the session, **update memory**:

| When | Update |
|------|--------|
| Always (after work) | `progress.md` — move items between Completed/In-Progress/Next; bump "Last updated"; update completion % and Health. |
| Always (after work) | `tasks/<id>.md` — update the `status:` field, checkpoints, and notes. **Never edit `active-tasks.md`** — it is a generated, gitignored view, regenerated from `tasks/*.md`. |
| Made a lasting decision | `decisions.md` — add a new ADR entry (Context / Decision / Alternatives / Consequences). |
| Architecture changed | `architecture.md` — reflect the new reality. |
| Scope/goals changed | `context.md`. |
| End of session / checkpoint | `sessions/` — write a **new file** `YYYY-MM-DD-HHMMSS-<branch>.md`. Never edit an existing session file. |

**Definition of "significant work"**: any change that alters behavior, structure, dependencies, or task status. Typo fixes and trivial edits don't require a full memory update, but still belong in the session file if notable.

Update memory by **editing the markdown files directly** (str_replace/append). Keep entries concise and factual.

---

## 5. Task Tracking Rules

- One detailed file per task in `.ai-memory/tasks/TASK-<YYYYMMDD-HHMMSS>-<slug>.md` — create it with
  `/e4:new-task`. IDs are timestamp-based, never sequential: two branches allocating `TASK-002` at
  the same time would collide on merge.
- The task file's `status:` front-matter (`todo` / `in-progress` / `blocked` / `in-review` / `done`)
  is the **source of truth**. `active-tasks.md` is a generated view of it — never hand-edit it.
- Update the task file's **Checkpoints** as you progress so any session can resume mid-task.
- When a task is done: check all acceptance criteria, mark it complete in `progress.md`, remove from `active-tasks.md` current slot, and (optionally) let the archive script move the task file to `~/AI-Vault/Archive/tasks/`.

---

## 6. Session Summary Rules (SESSION END)

Before the session ends (or when the user says "wrap up" / "checkpoint"), write a **new file** to
`.ai-memory/sessions/` named `YYYY-MM-DD-HHMMSS-<branch>.md` (one file per session — never append to
a shared file, which is what used to cause cross-branch merge conflicts) containing:
- **TL;DR** (2–3 sentences)
- **Did** (bullets)
- **Decisions** (or "None new")
- **Files changed** (list)
- **State** (what works / what doesn't)
- **Blockers** (or "None")
- **Next actions** (numbered, concrete — the first thing the next session should do)
- **Checkpoint block** (last_command, working_file, test_status, uncommitted_changes)

This is the most important habit: a good session file is what makes the *next* session instant.

---

## 7. Documentation Rules

- Public functions get docstrings/JSDoc; modules get a top-of-file purpose comment.
- Update the project README when adding setup steps or env vars.
- Significant architectural changes require an ADR in `decisions.md`.
- When you learn something broadly reusable, suggest adding a note to `~/AI-Vault/Knowledge/`.
- Use Obsidian-style links `[[note]]` inside memory files so the graph stays connected.

---

## 8. Initialization & Automation

If memory is missing or you need housekeeping, use the scripts in `~/AI-Vault/automation/` (or the project's `scripts/`):
- `init_project_memory` — scaffold `.ai-memory/` for a new project.
- `generate_daily_summary` — roll up today's session files into the global daily log.
- `generate_status` — regenerate `active-tasks.md` from `tasks/*.md` (also run by the SessionStart hook).
- `archive_completed_tasks` — move done tasks to the archive.
- `create_dashboard` — (re)generate the Obsidian project dashboard.
- `sync_obsidian` — refresh the global vault's project index links.

Never run destructive commands without confirming. Never `git push` or force-push unless explicitly asked.

---

## 9. Safety & Honesty

- If a task needs credentials/access you don't have, stop and say so.
- Don't claim silent success — confirm each step and surface errors with context.
- When uncertain, present two options with trade-offs rather than guessing.
- Ask clarifying questions before designing systems.

---

## 10. Quick Command Reference

| User says | You do |
|-----------|--------|
| "resume" / first message / `/e4:resume` | Run Section 1 onboarding + Resume Summary |
| "checkpoint" / "wrap up" / `/e4:end-session` | Run Section 6 session summary |
| `/e4:init` | Scaffold `.ai-memory/` + this file (Section 8) |
| `/e4:new-task <title>` | Create `tasks/TASK-<timestamp>-<slug>.md`; `active-tasks.md` regenerates |
| "what's next?" | Read `active-tasks.md` → state current + next step |
| "why did we…?" | Search `decisions.md` |
| "status" | Summarize `progress.md` |

> If custom slash commands and hooks are installed (see `docs/COMMANDS-AND-HOOKS.md`),
> the SessionStart hook auto-loads memory and `/e4:end-session` performs all Section 4–6
> updates in one step. The commands are the preferred, deterministic path.

---

*Keep this file updated as the project's conventions evolve. It is the contract between you and the developer.*
