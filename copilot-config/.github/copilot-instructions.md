# Copilot instructions

This repository uses **e4 persistent memory**. The operating contract is in [AGENTS.md](../AGENTS.md)
at the repository root — follow it. In short:

- At the start of a session, read `.ai-memory/` in this order: `onboarding.md` → `context.md` →
  `architecture.md` → `active-tasks.md` → `progress.md` → newest `YYYY-…` file in `sessions/` →
  `decisions.md` (index), then post a Resume Summary. The `e4-resume` skill does this.
- Never contradict an accepted ADR in `.ai-memory/decisions.md` silently — propose superseding it.
- Never hand-edit `.ai-memory/active-tasks.md` (generated) or an existing `sessions/` file (immutable).
- Before ending, run the `e4-end-session` skill to write a new `sessions/` file.

The e4 workflows are Agent Skills in `.agents/skills/` (`e4-resume`, `e4-end-session`, `e4-new-task`, `e4-init`).
