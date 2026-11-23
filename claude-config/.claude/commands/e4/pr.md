---
# e4 — forged by Omar Araby & contributors
description: "[e4] Write the PR description from commits + memory; `create` pushes and opens it"
argument-hint: [create] [optional note for the description]
allowed-tools: Bash(python3:*), Bash(git push:*), Bash(gh pr create:*), Bash(gh pr edit:*), Read, Write
model: sonnet
---

# /e4:pr — Pull-request description from memory

`e4_pr.py` has already collected every fact (base, size, commits, files by kind, ADRs, tasks,
session TL;DRs, push and PR state):

```!
python3 .claude/hooks/e4.py pr facts --note - <<'E4_ARGS'
$ARGUMENTS
E4_ARGS
```

If that output starts with `e4: error`, show it to the user and stop.

## 1. Write the description to the `Body file:` path — one Write
Use **only** those facts and this conversation. Never invent test results, numbers, or tickets.

```markdown
## What
- 2–5 bullets: the change as a reviewer sees it, grouped by theme (not one bullet per commit).

## Why
1–3 sentences: the problem this solves (task Goal, commit bodies, session TL;DRs, user note).

## Size                      ← only when the facts say OVER the guideline
+A / −D across N files. Why it isn't split; suggest reviewing commit by commit.

## Testing
What was actually run and its result (session `test_status`, commit bodies, this conversation).
"Not run" if there is no evidence. Name the test files added or changed.

## Docs
README / CHANGELOG / ADR / API-doc changes from the facts, or "None needed".

## Breaking changes          ← only if any; each line starts with `BREAKING:`

## Tasks                     ← only if any
- TASK-id — title (status). Mark an acceptance criterion met only with evidence.
```

**Title**: Conventional Commits, `type(scope): subject`, ≤ 72 characters, no backticks or `$`.
A single-commit branch reuses that commit's subject.

**Flag, don't fix** (one line each, at the end of your reply): code changed but `Tests changed: NO`;
a new dependency file changed with no ADR added; setup or env-var changes with `README changed: no`;
the uncommitted-changes warning.

## 2. Act on `Mode:`
- **draft** (default): reply with the title and the body exactly as written, then
  `Run /e4:pr create to push and open it.` Do nothing else.
- **create** — the user asked for this, so:
  1. If `Pushed:` says `no upstream yet` or local commits are not pushed:
     `git push -u origin <branch>`.
  2. `Existing PR: none` → `gh pr create --base <base without origin/> --head <branch> --title "<title>" --body-file "<body file>"`.
     An **open** PR → `gh pr edit <number> --title "<title>" --body-file "<body file>"` (update; never open a duplicate).
     A merged or closed PR → stop and tell the user.
  3. Reply with one line: `✅ PR #<n> → <url>`, then the flags.

Never force-push, merge, or push to the base branch.

<!-- e4 · forged by Omar Araby & contributors · add your name to CONTRIBUTORS.md when you extend these commands -->
