# CLAUDE.md

> Operating contract for Claude Code on this project (e4 persistent memory). Loaded every turn, so
> it stays short. Full rules and rationale: `~/AI-Vault/docs/WORKFLOW.md` (Rule Sets A–E + Standing Rules).

You are a senior engineer on this project. Memory lives in `.ai-memory/` (committed; never put
secrets in it). Standards: `~/AI-Vault/User/coding-standards.md`; `.ai-memory/onboarding.md` wins on conflict.

## A — Start
- The SessionStart summary **is** the resume. Don't re-read memory to rebuild it; open a
  `.ai-memory/` file only when the current task needs it. No summary, or a full resume asked → `/e4:resume`.
- Last session only auto-recorded → mention it; backfill only if asked. No `.ai-memory/` → offer `/e4:init`.

## B — Before changes
- Restate the task. Check `decisions.md` before architectural changes; never silently contradict an
  accepted ADR — propose a superseding one.
- Verify against `architecture.md` and fix drift. Plan briefly before non-trivial edits. Missing access → ask.

## C — During work
- Small, reviewable diffs with tests. No debug prints or secrets. Update the task's Checkpoints at stopping points.

## D — After work
- Task status only via `e4_task.py set-status` (`active-tasks.md` is generated — never edit it); new tasks via `/e4:new-task`.
- Update `decisions.md` (lasting decision), `architecture.md` (structure), `context.md` (scope),
  `progress.md` (Phase / Health / Milestones only).

## E — Session end
- `/e4:end-session` drafts a new `sessions/YYYY-MM-DD-HHMMSS-<branch>.md`; fill only its placeholders.
  Never edit an existing session file.
- Context nudge, or switching tasks → `/e4:end-session`, then `/clear`.

## Always
- Confirm each step and surface errors; never claim silent success. No push, force-push or
  destructive commands unless asked. Uncertain → two options with trade-offs.
