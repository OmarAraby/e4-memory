# Claude Code Workflow & Explicit Rules

This document specifies the exact, deterministic workflow Claude follows. The same rules live in condensed form inside `CLAUDE.md` (which Claude reads automatically). This is the expanded reference.

## The Memory Loop

```
        ┌─────────────────────────────────────────────┐
        │                SESSION START                 │
        │  Hook injects the resume · read on demand    │
        └───────────────────┬─────────────────────────┘
                            ▼
        ┌─────────────────────────────────────────────┐
        │              BEFORE CHANGES                  │
        │  Confirm task · check decisions · plan       │
        └───────────────────┬─────────────────────────┘
                            ▼
        ┌─────────────────────────────────────────────┐
        │                   WORK                       │
        │  Implement incrementally · test · checkpoint │
        └───────────────────┬─────────────────────────┘
                            ▼
        ┌─────────────────────────────────────────────┐
        │             AFTER COMPLETING                 │
        │  Update progress · tasks · decisions         │
        └───────────────────┬─────────────────────────┘
                            ▼
        ┌─────────────────────────────────────────────┐
        │                SESSION END                   │
        │  Write a new sessions/ file (checkpoint)     │
        └─────────────────────────────────────────────┘
                  ↑___________ next session ___________│
```

## Rule Set A — Entering a Project

> Applies at the start of every session (and after /clear).

```
A1. The SessionStart hook injects the resume: status, current focus,
    and the last saved session's TL;DR + Next actions. That summary
    IS the resume — do not re-read memory files to rebuild it, and
    no separate Resume Summary is needed unless the user asks.
A2. Open an individual .ai-memory/ file only when the current task
    needs it (architecture.md before structural work, the task's
    tasks/<id>.md before working on it). decisions.md is consulted
    before architectural changes (B2).
A3. If the injected summary is missing (hooks not installed) or the
    user asks for a full resume, run /e4:resume. It reads, in order:
    onboarding → context → architecture → active-tasks → progress →
    the NEWEST sessions/ file (lexically-last; legacy: top entry of
    session-log.md) → the decisions.md index.
A4. If the hook says the latest session was only auto-recorded,
    mention it once; backfill it only if the user asks.
A5. If .ai-memory/ is absent → offer /e4:init.
```

## Rule Set B — Before Making Changes

```
B1. Restate the task in one sentence; confirm it matches active-tasks.md.
B2. Search decisions.md for any ADR constraining the approach.
    - If a change would contradict an accepted ADR, STOP and propose
      a superseding ADR instead of silently diverging.
B3. Cross-check assumptions against architecture.md.
    - If the doc is wrong/stale, flag the drift and fix the doc.
B4. For non-trivial work, state a short plan before editing files.
B5. Confirm you have any needed access/credentials; if not, stop and ask.
```

## Rule Set C — During Work

```
C1. Make incremental, reviewable changes.
C2. Pair every implementation with tests.
C3. At natural stopping points in long tasks, update the task file's
    Checkpoints section. (So a crash mid-task loses minimal context.)
    Session files are written once at session end — mid-task progress
    belongs in the task file, not in a new sessions/ entry.
C4. Never leave debug prints or secrets.
```

## Rule Set D — After Completing Work

```
D1. progress.md — move items between Completed/In-Progress/Up-Next;
    bump "Last updated"; adjust completion % and Health.
D2. active-tasks.md — update current task status + checkpoint + next step;
    promote the next task if current is done.
D3. decisions.md — if a lasting decision was made, add an ADR entry.
D4. architecture.md — if structure changed, reflect new reality.
D5. context.md — if scope/goals changed, update.
D6. tasks/<task-id>.md — check acceptance criteria; set status: done,
    then regenerate active-tasks.md (generated view, never hand-edited).
```

## Rule Set E — Session End / Checkpoint

> Triggered when the user says "wrap up"/"checkpoint", or before ending.

```
E1. WRITE A NEW FILE to .ai-memory/sessions/ named
    YYYY-MM-DD-HHMMSS-<branch>.md (never edit an existing one) with:
    TL;DR · Did · Decisions · State · Blockers · Next actions
    (numbered) · Checkpoint block · Files changed · Commits.
    /e4:end-session runs e4_session.py draft, which writes the git
    facts (files, commits, branch, time) and leaves <!-- e4:fill -->
    placeholders; the model fills only those. A draft whose TL;DR is
    still a placeholder counts as incomplete to the hooks.
E2. Set task status with e4_task.py set-status (updates the task's
    status:, logs a checkpoint, regenerates active-tasks.md — a
    generated view, never hand-edited). Edit progress.md only if
    Phase, Health or a Milestone changed.
E3. If tasks completed, optionally run archive_completed_tasks.
E4. State the single first action for the next session.
```

## Worked Example

**User (new session)**: "let's keep going"

**Claude** already has the injected resume (Rule Set A) — current task
`TASK-20260609-142233-health-endpoint`, last TL;DR "route skeleton added, DB ping stubbed", next
action "wire version from package metadata + add tests" — so it picks that up directly, opening
`tasks/TASK-20260609-142233-health-endpoint.md` because it is about to work on it.
Then applies Rule Set B (confirms task, checks decisions), does the work (Rule Set C), and on completion runs Rule Sets D and E — updating `progress.md`, marking that task `done`, and writing a new `sessions/` file whose "Next actions" point to the next task.

## Why This Works for Long-Running Projects

- **Determinism**: the injected resume and the update list are fixed, so behavior is consistent across sessions and models.
- **Cheap by default**: the resume costs a few hundred tokens; scripts do the bookkeeping, hooks the guarantees, and the model only the judgment.
- **Crash resilience**: one immutable file per session + per-task checkpoints mean the worst case is losing minutes, not context. A `SessionEnd` hook drops a breadcrumb file even if `/e4:end-session` is skipped.
- **Conflict-free in parallel**: memory is never a shared file that two branches both append to — sessions are one file each, task IDs are timestamps, and `active-tasks.md` is generated and gitignored.
- **Low overhead**: only "significant work" triggers full updates; writing a session file is the one always-on habit.
- **Human-readable**: everything is markdown, versioned in git, and browsable in Obsidian.
