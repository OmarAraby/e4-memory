# AGENTS.md

> Operating instructions for any AI coding agent working on this project (GitHub Copilot, Cursor,
> Claude Code, Codex, …). This is the **agent-neutral** contract for the e4 persistent-memory system.
> Agent-specific entry points (e.g. `CLAUDE.md`) import or point at this file — edit the rules here, once.

---

## 0. Identity & Scope

You are working as a senior engineer on this project. You have **persistent memory** stored in `.ai-memory/` (committed to this repo — the source of truth). Global preferences and standards may live in the developer's Obsidian vault (`~/AI-Vault/User/`); read them when that path is reachable from your environment. Treat both as authoritative; project rules in `.ai-memory/onboarding.md` win on conflict.

> Cloud/remote agents usually cannot reach `~/AI-Vault/`. Everything required to work on this
> project must therefore be in this repo — the "Project Conventions Snapshot" in `onboarding.md`
> carries the essential standards.

---

## 1. Session Start Protocol (MANDATORY)

**Before responding to any request, on the first message of a session, run the onboarding sequence** (the `e4-resume` skill does exactly this):

1. Read `.ai-memory/onboarding.md` — orientation, setup, golden rules.
2. Read `.ai-memory/context.md` — domain, goals, constraints, glossary.
3. Read `.ai-memory/architecture.md` — system structure and design principles.
4. Read `.ai-memory/active-tasks.md` — what to work on now and the current checkpoint.
5. Read `.ai-memory/progress.md` — overall state.
6. Skim the **newest file** in `.ai-memory/sessions/` — names are timestamp-prefixed, so the
   lexically-last `YYYY-…` file is the newest (ignore `sessions/README.md`). Read its TL;DR and
   "Next actions". If it has no TL;DR it's an auto-breadcrumb (the last session ended without a
   proper wrap-up) — reconstruct from `git log`.
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

If `.ai-memory/` does not exist, offer to initialize it (Section 8).

---

## 2. Before Making Changes

- Restate the task in one sentence and confirm it matches `active-tasks.md`.
- Check `decisions.md` for any ADR that constrains the approach. **Never silently contradict an accepted ADR** — if you must, propose superseding it.
- Verify assumptions against `architecture.md`. If reality differs from the doc, flag the drift and update the doc.
- For non-trivial work, state a short plan before editing files.

---

## 3. Coding Rules

- Follow the global coding standards (`~/AI-Vault/User/coding-standards.md`, when reachable) for naming, error handling, testing, security. Project-specific overrides in `onboarding.md` win on conflict.
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
| Always (after work) | `progress.md` — Phase, Health and Milestones (low-churn fields only); bump "Last updated". |
| Always (after work) | `tasks/<id>.md` — update the `status:` field, checkpoints, and notes. **Never edit `active-tasks.md`** — it is a generated, gitignored view, regenerated from `tasks/*.md`. |
| Made a lasting decision | `decisions.md` — add a new ADR entry (Context / Decision / Alternatives / Consequences). |
| Architecture changed | `architecture.md` — reflect the new reality. |
| Scope/goals changed | `context.md`. |
| End of session / checkpoint | `sessions/` — write a **new file** `YYYY-MM-DD-HHMMSS-<branch>.md`. Never edit an existing session file. |

**Definition of "significant work"**: any change that alters behavior, structure, dependencies, or task status. Typo fixes and trivial edits don't require a full memory update, but still belong in the session file if notable.

Update memory by **editing the markdown files directly**. Keep entries concise and factual.

---

## 5. Task Tracking Rules

- One detailed file per task in `.ai-memory/tasks/TASK-<YYYYMMDD-HHMMSS>-<slug>.md` — create it with
  the `e4-new-task` skill. IDs are timestamp-based, never sequential: two branches allocating
  `TASK-002` at the same time would collide on merge.
- The task file's `status:` front-matter (`todo` / `in-progress` / `blocked` / `in-review` / `done`)
  is the **source of truth**. `active-tasks.md` is a generated view of it — never hand-edit it.
- Update the task file's **Checkpoints** as you progress so any session can resume mid-task.
- When a task is done: check all acceptance criteria, set `status: done`, regenerate `active-tasks.md`, and (optionally) let the archive script move the task file to `~/AI-Vault/Archive/tasks/`.

---

## 6. Session Summary Rules (SESSION END)

Before the session ends (or when the user says "wrap up" / "checkpoint"), run the `e4-end-session`
skill — it writes a **new file** to `.ai-memory/sessions/` named `YYYY-MM-DD-HHMMSS-<branch>.md`
(one file per session — never append to a shared file, which is what used to cause cross-branch
merge conflicts) containing:
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

If memory is missing or you need housekeeping, use the `e4-init` skill or the scripts in `~/AI-Vault/automation/python/` (or the project's `scripts/`):
- `init_project_memory` — scaffold `.ai-memory/` for a new project.
- `generate_status` — regenerate `active-tasks.md` from `tasks/*.md`.
- `validate_memory` — check `.ai-memory/` structure and naming contracts.
- `generate_daily_summary` — roll up today's session files into the global daily log.
- `archive_completed_tasks` — move done tasks to the archive.
- `create_dashboard` — (re)generate the Obsidian project dashboard.

Never run destructive commands without confirming. Never `git push` or force-push unless explicitly asked.

---

## 9. Safety & Honesty

- If a task needs credentials/access you don't have, stop and say so.
- Don't claim silent success — confirm each step and surface errors with context.
- When uncertain, present two options with trade-offs rather than guessing.
- Ask clarifying questions before designing systems.

---

## 10. Quick Reference

The e4 workflows ship as Agent Skills in `.agents/skills/` (invoke as `/e4-resume` etc. in agents
that expose skills as slash commands). Agent-specific entry points may map them to other names.

| User says | You do |
|-----------|--------|
| "resume" / first message / `e4-resume` | Run Section 1 onboarding + Resume Summary |
| "checkpoint" / "wrap up" / `e4-end-session` | Run Section 6 session summary |
| `e4-init` | Scaffold `.ai-memory/` + this file (Section 8) |
| `e4-new-task <title>` | Create `tasks/TASK-<timestamp>-<slug>.md`; `active-tasks.md` regenerates |
| "what's next?" | Read `active-tasks.md` → state current + next step |
| "why did we…?" | Search `decisions.md` |
| "status" | Summarize `progress.md` |

---

*Keep this file updated as the project's conventions evolve. It is the contract between the agents and the developer.*
