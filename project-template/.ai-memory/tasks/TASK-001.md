---
tags: [task]
type: task
status: in-progress
priority: high
created: 2026-01-01
---

# Task: Example — Implement health-check endpoint

**ID**: TASK-001
**Status**: #status/in-progress
**Priority**: #priority/high
**Owner**: Claude
**Estimate**: 1h

## Goal
Add a `GET /health` endpoint returning service status and version.

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
