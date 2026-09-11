# Obsidian Integration Guide

This system is designed to live inside Obsidian as the primary knowledge base. Here's how the pieces connect and how to set it up for a great experience: cross-linking, dashboards, graph view, tags, daily notes, and navigation.

## 1. Two-Layer Memory Model

There are two physical locations, joined by links:

```
~/AI-Vault/                     ← Global vault (open this in Obsidian)
│
├── Projects/myapp.md           ← Lightweight INDEX + dashboard for a project
│        │  links to ↓
~/code/myapp/.ai-memory/        ← SOURCE OF TRUTH, committed in the repo
         ├── context.md
         ├── architecture.md
         └── ...
```

The global vault holds your identity (`User/`), reusable knowledge (`Knowledge/`), templates, daily logs, and a thin index per project. Each project's *actual* memory lives in its repo so it travels with the code and is versioned in git.

### Making the link work in Obsidian
Two options:

- **Symlink (recommended)**: link each repo's `.ai-memory` into the vault so Obsidian indexes it.
  ```bash
  # macOS / Linux
  ln -s ~/code/myapp/.ai-memory ~/AI-Vault/Projects/myapp
  ```
  ```powershell
  # Windows (admin shell)
  New-Item -ItemType SymbolicLink -Path "$HOME\AI-Vault\Projects\myapp" -Target "$HOME\code\myapp\.ai-memory"
  ```
  Now `[[myapp/.ai-memory/context]]` style links resolve, and the project's notes appear in the graph.

- **Vault-as-superset**: keep projects under a folder that is itself inside the vault. Simpler, but mixes code repos and notes.

## 2. Cross-Linking Between Notes

Use `[[wikilinks]]` everywhere. Examples already baked into the templates:

- In `architecture.md`: `## See Also → [[myapp-decisions]]`
- In a `Knowledge/` note: `## See also → [[repository-pattern]]`, `[[dependency-injection]]`
- In `Projects/myapp.md`: links to every memory file.

**Rule for Claude**: when writing memory files, link related concepts with `[[ ]]` so the graph stays connected.

## 3. Project Dashboards (Dataview)

Install the **Dataview** community plugin. The `create_dashboard.py` script generates dashboards that use it. Example block (auto-generated in `Projects/myapp.md`):

````markdown
## Open Tasks
```dataview
TASK
FROM "myapp"
WHERE !completed
GROUP BY status
```
````

A master dashboard at `Projects/_Dashboard.md` aggregates all projects:

````markdown
| Project | Phase | Health | Completion |
|---------|-------|--------|-----------|
| [[myapp]] | MVP | 🟢 | ~30% |
````

## 4. Knowledge Graph Support

The graph view becomes useful once notes are tagged and linked. To get value:
- Tag every note (see tag taxonomy below).
- Link decisions ↔ architecture ↔ tasks.
- Use the **Local Graph** pane while viewing a project to see its neighborhood.

Color groups (Graph settings → Groups):
- `tag:#project` → blue
- `tag:#adr` → orange
- `tag:#lesson` → green
- `tag:#bug` → red

## 5. Tag Taxonomy

Nested tags keep things filterable:

```
#project                 #status/active  #status/blocked  #status/done
#task                    #priority/low   #priority/high   #priority/critical
#adr  #decision          #severity/medium
#architecture #pattern   #anti-pattern
#lesson #reference       #technology/postgres  #technology/react
#daily #session-summary  #postmortem #bug
```

Find everything blocked across all projects:
````markdown
```dataview
TABLE file.path
FROM #status/blocked
```
````

## 6. Daily Notes Integration

1. Settings → Core plugins → enable **Daily notes**.
2. Set "New file location" to `DailyLogs/`.
3. Set "Template file location" to `Templates/daily-note.md`.
4. Run `generate_daily_summary.py` (or the `daily` wrapper) on a schedule to pull each project's `sessions/` files for that date into that day's note.

This gives you one place answering "what did I do across everything today?" with links back into each project.

## 7. Templater (optional but powerful)

Install **Templater** to auto-insert templates with live dates:
- Map a hotkey to "Create new note from template".
- Point it at `Templates/`.
- `{{date}}` / `{{time}}` placeholders in the templates become real values.

## 8. Recommended Plugins Summary

| Plugin | Why |
|--------|-----|
| Dataview | Dashboards, task rollups, dynamic tables |
| Templater | Auto-fill templates with dates/variables |
| Daily Notes (core) | Daily journal in `DailyLogs/` |
| Graph Analysis (optional) | Surfaces related notes |
| Git (optional) | Auto-commit the vault for backup/history |

## 9. Easy Navigation Setup

- Pin `Projects/_Dashboard.md` as your home note (Settings → set as start page, or use the **Homepage** plugin).
- Add a top-level `🏠 Home.md` with links to: Dashboard, User profile, Knowledge index, today's daily note.
- Use Obsidian's **Bookmarks** for the 5 notes you open most.

### Example Home note
```markdown
# 🏠 Home
- 📊 [[_Dashboard|Projects Dashboard]]
- 👤 [[profile|My Profile]] · [[coding-standards|Coding Standards]]
- 📚 [[Knowledge/README|Knowledge Base]]
- 📅 [[DailyLogs/README|Daily Logs]]
```
