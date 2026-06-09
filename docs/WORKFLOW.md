# Claude Code Workflow & Explicit Rules

This document specifies the exact, deterministic workflow Claude follows. The same rules live in condensed form inside `CLAUDE.md` (which Claude reads automatically). This is the expanded reference.

## The Memory Loop

```
        ┌─────────────────────────────────────────────┐
        │                SESSION START                 │
        │  Read memory → post Resume Summary            │
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
        │  Prepend session-log entry (checkpoint)      │
        └─────────────────────────────────────────────┘
                  ↑___________ next session ___________│
```

## Rule Set A — Entering a Project

> Triggered on the first message of any session, or when the user says "resume".

```
A1. Read .ai-memory/onboarding.md in full.
A2. Read .ai-memory/context.md.
A3. Read .ai-memory/architecture.md.
A4. Read .ai-memory/active-tasks.md.
A5. Read .ai-memory/progress.md.
A6. Read the TOP entry of .ai-memory/session-log.md.
A7. Open .ai-memory/decisions.md index (read full ADRs on demand).
A8. Post a Resume Summary (≤8 lines): project, phase, health,
    current task, last TL;DR, "picking up at", blockers.
A9. If .ai-memory/ is absent → offer to run init_project_memory.
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
    Checkpoints section AND prepend a brief session-log checkpoint.
    (So a crash mid-task loses minimal context.)
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
D6. tasks/TASK-NNN.md — check acceptance criteria; mark done.
```

## Rule Set E — Session End / Checkpoint

> Triggered when the user says "wrap up"/"checkpoint", or before ending.

```
E1. PREPEND a new entry to session-log.md with:
    TL;DR · Did · Decisions · Files changed · State ·
    Blockers · Next actions (numbered) · Checkpoint block.
E2. Ensure progress.md and active-tasks.md reflect reality.
E3. If tasks completed, optionally run archive_completed_tasks.
E4. State the single first action for the next session.
```

## Worked Example

**User (new session)**: "let's keep going"

**Claude** runs Rule Set A, then:
```
📋 Resumed: MyApp
Phase: MVP | Health: 🟢
Current task: TASK-001 — Health-check endpoint (in-progress)
Last session ended: 2026-06-09 — Added route skeleton, DB ping stubbed.
Picking up at: wire version from package metadata + add tests.
Blockers: none
```
Then applies Rule Set B (confirms task, checks decisions), does the work (Rule Set C), and on completion runs Rule Sets D and E — updating `progress.md`, marking `TASK-001` done, and prepending a session-log entry whose "Next actions" point to TASK-002.

## Why This Works for Long-Running Projects

- **Determinism**: the read order and update list are fixed, so behavior is consistent across sessions and models.
- **Crash resilience**: the append-only session-log + per-task checkpoints mean the worst case is losing minutes, not context.
- **Low overhead**: only "significant work" triggers full updates; the session-log is the one always-on habit.
- **Human-readable**: everything is markdown, versioned in git, and browsable in Obsidian.
