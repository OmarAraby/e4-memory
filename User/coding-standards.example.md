---
tags: [user, standards, coding]
updated: YYYY-MM-DD
---

# Coding Standards & Conventions

> Copy this file to `coding-standards.md` and adapt it. `coding-standards.md` is gitignored.
> Claude reads it before writing any code; project-specific conventions override it.

## Code Quality Gates
Before any commit is considered done:
- [ ] Builds / compiles cleanly
- [ ] Tests pass
- [ ] No linter / analyzer errors
- [ ] Public functions documented
- [ ] No debug statements left in
- [ ] Secrets never committed (use env vars / a secret store)

## Naming Conventions
- Document the casing rules for each language you use.

## Error Handling
- Handle errors explicitly — no silent failures.
- Log with context; never log secrets, PII, or internal IDs.

## Architecture Conventions
- Describe the patterns you expect (layering, DI, repository, etc.).

## Git Conventions
- Branch naming and Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).
- Keep PRs small; describe *what* and *why*.

## Testing Strategy
- Test pyramid: mostly unit, some integration, few E2E.

## Security Standards
- Validate external input at the boundary.
- Parameterize all SQL.
- Use environment variables / secret stores for all secrets.
