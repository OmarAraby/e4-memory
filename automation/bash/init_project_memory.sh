#!/usr/bin/env bash
# init_project_memory.sh — Scaffold .ai-memory/ + CLAUDE.md stub for a project.
#
# Usage:
#   ./init_project_memory.sh [PROJECT_DIR] [PROJECT_NAME]
#   ./init_project_memory.sh .              # current dir, name = folder
#   ./init_project_memory.sh ~/code/myapp "My App"
#
# Idempotent: skips files that already exist (unless FORCE=1).

set -euo pipefail

PROJECT_DIR="${1:-.}"
PROJECT_NAME="${2:-$(basename "$(cd "$PROJECT_DIR" && pwd)")}"
FORCE="${FORCE:-0}"
TODAY="$(date +%F)"
MEM="$PROJECT_DIR/.ai-memory"

write() {
  # write <path> <<<content via stdin>
  local path="$1"
  if [[ -e "$path" && "$FORCE" != "1" ]]; then
    echo "skip  $path"
    return
  fi
  mkdir -p "$(dirname "$path")"
  cat > "$path"
  echo "write $path"
}

# Tier-2: session history is one file per session under sessions/ (never a single shared file).
mkdir -p "$MEM/tasks" "$MEM/sessions"
echo "Initializing memory for '$PROJECT_NAME' at $MEM"
echo

write "$MEM/onboarding.md" <<EOF
---
tags: [project, onboarding, memory]
type: onboarding
updated: $TODAY
---

# 🚀 Onboarding — READ THIS FIRST

> Claude: read this completely before doing anything else.

## What is this project?
> One paragraph elevator pitch.

## How to read the memory (in order)
1. onboarding → 2. context → 3. architecture → 4. active-tasks → 5. progress → 6. decisions → 7. sessions/ (newest file)

## Golden Rules
- 

## Environment Setup
\`\`\`bash
# how to run locally
\`\`\`

## How to run tests
\`\`\`bash
#
\`\`\`
EOF

write "$MEM/context.md" <<EOF
---
tags: [project, context, memory]
type: context
updated: $TODAY
---

# Project Context

## Purpose
## Goals
## Scope (In / Out)
## Constraints
## Domain Glossary
| Term | Meaning |
|------|---------|
EOF

write "$MEM/architecture.md" <<EOF
---
tags: [project, architecture, memory]
type: architecture
updated: $TODAY
---

# Architecture

## System Overview
## Tech Stack
| Layer | Technology | Version |
|-------|-----------|---------|
## Component Breakdown
## Data Model
## Directory Structure
## Design Principles in Effect
EOF

write "$MEM/decisions.md" <<EOF
---
tags: [project, decisions, adr, memory]
type: decisions
updated: $TODAY
---

# Architecture Decisions Log

> Consult before any architectural change. Add an ADR per lasting decision.

## Index
| ID | Title | Status | Date |
|----|-------|--------|------|
EOF

write "$MEM/progress.md" <<EOF
---
tags: [project, progress, memory]
type: progress
updated: $TODAY
---

# Progress

## Status at a Glance
- Phase: Planning
- Overall completion: ░░░░░░░░░░ ~0%
- Last updated: $TODAY
- Health: 🟢 On track

## Completed ✅
- [x] ($TODAY) Initialized memory system

## In Progress 🔄
## Up Next ⏳
EOF

write "$MEM/active-tasks.md" <<EOF
---
tags: [project, tasks, active, memory]
type: active-tasks
updated: $TODAY
---

# Active Tasks

> ⚙️ GENERATED from \`tasks/*.md\` by \`generate_status.py\` — **do not edit by hand.**
> Change a task's \`status:\` in its \`tasks/\` file, then regenerate.

## 🎯 Current Task
> None yet.

## 🔜 Next Up
| ID | Task | Priority | Detail |
|----|------|----------|--------|

## 🚧 Blocked
## 👀 In Review
EOF

# Tier-2 seed session. The 000000 timestamp sorts before any real session, so the newest file
# is always the most recent work. One file per session — never a shared session-log.md.
write "$MEM/sessions/$TODAY-000000-init.md" <<EOF
---
type: session
date: $TODAY
branch: init
---
## Session — $TODAY
**TL;DR**: Initialized project memory. Session history lives in sessions/, one file per session.
**Did**: Created .ai-memory structure.
**Decisions**: None.
**Next actions**:
1. Fill in context.md
2. Define architecture.md
**Checkpoint**:
\`\`\`
last_command: init_project_memory.sh
test_status: not run
uncommitted_changes: yes
\`\`\`
EOF

write "$MEM/sessions/README.md" <<EOF
---
tags: [project, session, memory, index]
---

# sessions/ — one file per session

Filename: \`YYYY-MM-DD-HHMMSS-<branch>.md\` — timestamp-first, so the lexically-last file is the
newest session. Written by \`/e4:end-session\`; the SessionEnd hook drops an \`*-auto.md\`
breadcrumb if that command was skipped. **Never edit an existing session file** — write a new one.
Every entry needs a **TL;DR**: it is the anchor the next session resumes from.
EOF

write "$MEM/README.md" <<EOF
---
tags: [project, memory, index]
---

# .ai-memory — Project Memory

Read order: onboarding → context → architecture → active-tasks → progress → decisions → sessions/ (newest)

Session history is **one file per session** under \`sessions/\`, and \`active-tasks.md\` is a
generated view of \`tasks/*.md\`. Both exist so parallel branches never conflict on memory.
Commit this directory to git (no secrets).
EOF

echo
echo "✅ Done. Fill in context.md and architecture.md, then start working."
