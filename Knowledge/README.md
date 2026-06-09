---
tags: [knowledge, index]
---

# Knowledge Base

Reusable technical knowledge, independent of any single project.

## Structure

```
Knowledge/
├── architecture/     → System design patterns, architecture styles
├── patterns/         → Design patterns, code patterns, anti-patterns
├── technologies/     → Notes on specific tools, libraries, frameworks
├── lessons-learned/  → Post-mortems, retrospectives, hard-won insights
└── references/       → Cheat sheets, quick references, API summaries
```

## Obsidian Navigation

Use the graph view to explore connections between notes.
Tag system:
- `#pattern` — a reusable implementation pattern
- `#anti-pattern` — a known bad approach to avoid
- `#architecture` — system design notes
- `#lesson` — something learned the hard way
- `#reference` — quick reference / cheat sheet
- `#technology/<name>` — notes on a specific tool

## Adding Knowledge

When you solve a non-trivial problem, capture it here:
1. Create a note in the appropriate folder
2. Add relevant tags
3. Link to related notes using `[[note-name]]`
4. Add a "See also" section at the bottom

## Dataview Dashboard

```dataview
TABLE file.mtime as "Updated", tags
FROM "Knowledge"
SORT file.mtime DESC
LIMIT 20
```
