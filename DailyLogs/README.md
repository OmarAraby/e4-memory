---
tags: [dailylogs, index]
---

# Daily Logs

Rolling journal across **all** projects. One note per day, named `YYYY-MM-DD.md`.
Generated automatically by `generate_daily_summary.py`, or via Obsidian Daily Notes.

## Why a global daily log?
Project memory answers "what's the state of project X?".
Daily logs answer "what did I do across everything today?" — useful for standups and weekly reviews.

## Weekly Review Dataview
```dataview
TABLE file.mtime as "Updated"
FROM "DailyLogs"
WHERE file.mtime >= date(today) - dur(7 days)
SORT file.name DESC
```
