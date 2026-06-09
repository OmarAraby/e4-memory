<#
.SYNOPSIS
  Initialize a .ai-memory/ structure + CLAUDE.md stub for a project.

.EXAMPLE
  .\Init-ProjectMemory.ps1 -ProjectDir . -Name "My App"
  .\Init-ProjectMemory.ps1 -ProjectDir C:\code\myapp -Force
#>
param(
  [string]$ProjectDir = ".",
  [string]$Name,
  [switch]$Force,
  [switch]$WithClaudeMd
)

$ErrorActionPreference = "Stop"
$Today = Get-Date -Format "yyyy-MM-dd"
$root = (Resolve-Path $ProjectDir).Path
if (-not $Name) { $Name = Split-Path $root -Leaf }
$mem = Join-Path $root ".ai-memory"
$tasks = Join-Path $mem "tasks"

New-Item -ItemType Directory -Force -Path $tasks | Out-Null

function Write-MemFile($Path, $Content) {
  if ((Test-Path $Path) -and -not $Force) {
    Write-Host "skip  $Path"
    return
  }
  $dir = Split-Path $Path -Parent
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  Set-Content -Path $Path -Value $Content -Encoding UTF8
  Write-Host "write $Path"
}

Write-Host "Initializing memory for '$Name' at $mem`n"

Write-MemFile (Join-Path $mem "onboarding.md") @"
---
tags: [project, onboarding, memory]
type: onboarding
updated: $Today
---

# 🚀 Onboarding — READ THIS FIRST

> Claude: read this completely before doing anything else.

## What is this project?
> One paragraph elevator pitch.

## How to read the memory (in order)
1. onboarding -> 2. context -> 3. architecture -> 4. active-tasks -> 5. progress -> 6. decisions -> 7. session-log (latest)

## Golden Rules
- 

## Environment Setup
``````bash
# how to run locally
``````
"@

Write-MemFile (Join-Path $mem "context.md") @"
---
tags: [project, context, memory]
type: context
updated: $Today
---

# Project Context

## Purpose
## Goals
## Scope (In / Out)
## Constraints
## Domain Glossary
| Term | Meaning |
|------|---------|
"@

Write-MemFile (Join-Path $mem "architecture.md") @"
---
tags: [project, architecture, memory]
type: architecture
updated: $Today
---

# Architecture

## System Overview
## Tech Stack
| Layer | Technology | Version |
|-------|-----------|---------|
## Component Breakdown
## Data Model
## Design Principles in Effect
"@

Write-MemFile (Join-Path $mem "decisions.md") @"
---
tags: [project, decisions, adr, memory]
type: decisions
updated: $Today
---

# Architecture Decisions Log

> Consult before any architectural change. Add an ADR per lasting decision.

## Index
| ID | Title | Status | Date |
|----|-------|--------|------|
"@

Write-MemFile (Join-Path $mem "progress.md") @"
---
tags: [project, progress, memory]
type: progress
updated: $Today
---

# Progress

## Status at a Glance
- Phase: Planning
- Overall completion: ~0%
- Last updated: $Today
- Health: 🟢 On track

## Completed ✅
- [x] ($Today) Initialized memory system

## In Progress 🔄
## Up Next ⏳
"@

Write-MemFile (Join-Path $mem "active-tasks.md") @"
---
tags: [project, tasks, active, memory]
type: active-tasks
updated: $Today
---

# Active Tasks

## 🎯 Current Task
> None yet.

## 🔜 Next Up
| ID | Task | Priority | Detail |
|----|------|----------|--------|

## 🚧 Blocked
## 👀 In Review
"@

Write-MemFile (Join-Path $mem "session-log.md") @"
---
tags: [project, session-log, memory]
type: session-log
updated: $Today
---

# Session Log

> Append-only, newest on top. Crash-recovery backbone.

## Session — $Today
**TL;DR**: Initialized project memory.
**Did**: Created .ai-memory structure.
**Decisions**: None.
**Next actions**:
1. Fill in context.md
2. Define architecture.md
**Checkpoint**:
``````
last_command: Init-ProjectMemory.ps1
test_status: not run
uncommitted_changes: yes
``````
"@

Write-MemFile (Join-Path $mem "README.md") @"
---
tags: [project, memory, index]
---

# .ai-memory — Project Memory

Read order: onboarding -> context -> architecture -> active-tasks -> progress -> decisions -> session-log
Commit this directory to git (no secrets).
"@

if ($WithClaudeMd) {
  Write-MemFile (Join-Path $root "CLAUDE.md") @"
# CLAUDE.md

At session start, read .ai-memory in order:
onboarding -> context -> architecture -> active-tasks -> progress -> decisions -> session-log (latest),
then post a Resume Summary. After significant work: update progress.md, active-tasks.md,
decisions.md (if needed), and prepend a session-log.md entry.
(Replace this stub with the full CLAUDE.md from the package.)
"@
}

Write-Host "`n✅ Done. Fill in context.md and architecture.md, then start working."
