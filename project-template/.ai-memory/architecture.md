---
tags: [project, architecture, memory]
type: architecture
updated: 2026-01-01
---

# Architecture

## System Overview
> High-level description. What are the major components and how do they interact?

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│   API    │────▶│ Database │
└──────────┘     └──────────┘     └──────────┘
```
> Replace with an accurate diagram (ASCII or link to a `.excalidraw`/mermaid file).

## Tech Stack
| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Language |  |  |  |
| Framework |  |  |  |
| Database |  |  |  |
| Cache |  |  |  |
| Queue |  |  |  |
| Hosting |  |  |  |

## Component Breakdown
### {{Component A}}
- **Responsibility**: 
- **Location**: `src/...`
- **Key files**: 
- **Depends on**: 

## Data Model
> Core entities and relationships. Link to schema or migrations.

```
User ──< Order ──< OrderItem >── Product
```

## Key Data Flows
### {{Flow: e.g. User Authentication}}
1. 
2. 

## Directory Structure
```
src/
├── api/          → 
├── services/     → 
├── models/       → 
├── config/       → 
└── utils/        → 
```

## Design Principles in Effect
> The architectural rules this codebase follows. Claude must respect these.
- 
- 

## Known Technical Debt
| Item | Impact | Tracked in |
|------|--------|-----------|
|      |        |           |

## See Also
- Decisions that shaped this: [[project-name-decisions]]
