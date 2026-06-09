#!/usr/bin/env bash
# ai-memory.sh — Convenience wrapper around the Python automation tools.
# Keeps one entry point for daily/maintenance tasks (cron-friendly).
#
# Usage:
#   ./ai-memory.sh daily          # generate today's daily summary
#   ./ai-memory.sh dashboard PROJ # rebuild a project dashboard + index
#   ./ai-memory.sh archive PROJ   # archive completed tasks for a project
#   ./ai-memory.sh sync           # rebuild master index across all projects
#
# Configure these or set as env vars:
VAULT="${AI_VAULT:-$HOME/AI-Vault}"
PROJECTS_ROOT="${AI_PROJECTS_ROOT:-$HOME/code}"
PYDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../python" && pwd)"

set -euo pipefail
cmd="${1:-help}"; shift || true

case "$cmd" in
  daily)
    python3 "$PYDIR/generate_daily_summary.py" --vault "$VAULT" --projects-root "$PROJECTS_ROOT"
    ;;
  dashboard)
    proj="${1:?usage: ai-memory.sh dashboard /path/to/project}"
    python3 "$PYDIR/create_dashboard.py" --vault "$VAULT" --project "$proj"
    python3 "$PYDIR/create_dashboard.py" --vault "$VAULT" --rebuild-index --projects-root "$PROJECTS_ROOT"
    ;;
  archive)
    proj="${1:?usage: ai-memory.sh archive /path/to/project}"
    python3 "$PYDIR/archive_completed_tasks.py" --project "$proj" --vault "$VAULT" --infer
    ;;
  sync)
    python3 "$PYDIR/create_dashboard.py" --vault "$VAULT" --rebuild-index --projects-root "$PROJECTS_ROOT"
    ;;
  *)
    cat <<USAGE
ai-memory.sh — memory maintenance

Commands:
  daily             Generate today's global daily summary
  dashboard PROJ    Rebuild project dashboard + master index
  archive PROJ      Archive completed tasks for PROJ
  sync              Rebuild master index across all projects

Env:
  AI_VAULT=$VAULT
  AI_PROJECTS_ROOT=$PROJECTS_ROOT

Cron example (daily at 23:50):
  50 23 * * * AI_VAULT=$HOME/AI-Vault AI_PROJECTS_ROOT=$HOME/code $PYDIR/../bash/ai-memory.sh daily
USAGE
    ;;
esac
