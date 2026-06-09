---
tags: [template, project]
type: project-index
status: active
created: {{date}}
---

# {{Project Name}}

> Project index note. Lives in the global vault at `Projects/{{project-name}}.md`.
> Links to the project's local `.ai-memory/` directory.

## Overview
**One-line description**: 

**Repository**: `path/or/url`
**Local memory**: `[[{{project-name}}/.ai-memory/context|Project Context]]`
**Status**: #status/active
**Started**: {{date}}

## Quick Links
- [[{{project-name}}-context|Context]]
- [[{{project-name}}-architecture|Architecture]]
- [[{{project-name}}-progress|Progress]]
- [[{{project-name}}-decisions|Decisions]]
- [[{{project-name}}-active-tasks|Active Tasks]]

## Tech Stack
- **Language**: 
- **Framework**: 
- **Database**: 
- **Deployment**: 

## Tags
#project #status/active

## Current Focus
> What's the team/I working on right now?

## Dataview: Open Tasks
```dataview
TASK
FROM "Projects/{{project-name}}"
WHERE !completed
```
