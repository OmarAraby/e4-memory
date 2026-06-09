---
tags: [template, daily]
type: daily-note
date: {{date}}
---

# {{date:dddd, MMMM Do YYYY}}

## Focus Today
- 

## Sessions
> Auto-populated by the daily summary script, or filled manually.

### {{project}} — {{time}}
- 

## Decisions
- 

## Blockers
- 

## Tomorrow
- 

## Links
- Yesterday: [[{{date-1}}]]
- Tomorrow: [[{{date+1}}]]

---
## Dataview: Today's Touched Notes
```dataview
TABLE file.mtime as "Modified"
WHERE file.mtime >= date(today)
SORT file.mtime DESC
```
