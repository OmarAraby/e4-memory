---
tags: [project, onboarding, memory]
type: onboarding
updated: 2026-01-01
---

# 🚀 Onboarding — READ THIS FIRST

> **Claude: this is your entry point. Read this file completely before doing anything else in this project.**

## What is this project?
> One paragraph. The elevator pitch. What it does and for whom.

## How to read the memory (in order)
1. **This file** (`onboarding.md`) — orientation
2. **`context.md`** — domain, goals, constraints, glossary
3. **`architecture.md`** — how the system is built
4. **`active-tasks.md`** — what to work on now
5. **`progress.md`** — what's done and what's left
6. **`decisions.md`** — *consult before changing architecture*
7. **`sessions/`** — session history, one file per session (read the newest 1-2 files;
   timestamp-prefixed names sort chronologically, so the last one is the newest)

## Golden Rules for this project
> Project-specific overrides. General rules live in `CLAUDE.md` at repo root.
- 
- 

## Environment Setup
```bash
# How to get the project running locally
# e.g.
# cp .env.example .env
# docker compose up -d
# npm install && npm run dev
```

## How to run tests
```bash
# 
```

## Key Entry Points
| What | Where |
|------|-------|
| App entry | `src/main.ts` |
| Config | `src/config/` |
| Tests | `tests/` |
| API routes | `src/routes/` |

## Who to ask / where to look
- Architecture questions → `architecture.md` + `decisions.md`
- "Why was X done this way?" → search `decisions.md`
- "What's the current task?" → `active-tasks.md`

## Project Conventions Snapshot
> The 5 most important conventions. Full standards in global vault `User/coding-standards.md`.
1. 
2. 
3. 
4. 
5. 
