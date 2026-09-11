---
id: TASK-20260101-090000-example-health-endpoint
title: "Example — implement health-check endpoint"
status: in-progress    # todo | in-progress | blocked | in-review | done
priority: high
created: 2026-01-01
---

# Example — implement health-check endpoint

> **This is the example task shipped with the template — delete it once real work starts.**
> Note the ID shape: `TASK-<YYYYMMDD-HHMMSS>-<slug>`. IDs are timestamp-based, never sequential,
> so two branches creating a task at the same time can never collide on the same filename.
> Create new tasks with `/e4:new-task <title>` rather than copying this by hand.

## Goal
Add a `GET /health` endpoint returning service status and version.

## Context
Ops needs a cheap liveness probe before the service can be deployed behind a load balancer.

## Acceptance Criteria
- [ ] Returns 200 with `{ status: "ok", version, uptime }`
- [ ] Includes DB connectivity check
- [ ] Unit test covers healthy + unhealthy DB

## Implementation Plan
1. Add route handler
2. Add DB ping helper
3. Wire version from package metadata
4. Add tests

## Files Likely Affected
- `src/routes/health.ts`
- `tests/health.test.ts`

## Checkpoints
- [ ] Checkpoint 1: route returns static ok
- [ ] Checkpoint 2: DB check wired
- [ ] Checkpoint 3: tests green

## Blockers
None.

## Notes / Log
- 2026-01-01: Created as example task.
