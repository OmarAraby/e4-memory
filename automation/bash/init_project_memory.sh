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

mkdir -p "$MEM/tasks"
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
1. onboarding → 2. context → 3. architecture → 4. active-tasks → 5. progress → 6. decisions → 7. session-log (latest)

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

## 🎯 Current Task
> None yet.

## 🔜 Next Up
| ID | Task | Priority | Detail |
|----|------|----------|--------|

## 🚧 Blocked
## 👀 In Review
EOF

write "$MEM/session-log.md" <<EOF
---
tags: [project, session-log, memory]
type: session-log
updated: $TODAY
---

# Session Log

> Append-only, newest on top. Crash-recovery backbone.

## Session — $TODAY
**TL;DR**: Initialized project memory.
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

write "$MEM/README.md" <<EOF
---
tags: [project, memory, index]
---

# .ai-memory — Project Memory

Read order: onboarding → context → architecture → active-tasks → progress → decisions → session-log
Commit this directory to git (no secrets).
EOF

echo
echo "✅ Done. Fill in context.md and architecture.md, then start working."
