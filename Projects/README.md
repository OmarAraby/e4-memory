---
tags: [projects, index]
---

# Projects Index

One index note per project. Each links to that project's local `.ai-memory/` directory.
The **source of truth** lives inside each repo at `.ai-memory/`; these notes are the Obsidian-facing entry point.

## All Projects Dashboard
```dataview
TABLE status, file.mtime as "Updated"
FROM "Projects"
WHERE type = "project-index"
SORT status ASC, file.mtime DESC
```
