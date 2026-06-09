#!/usr/bin/env bash
# session_end.sh — Claude Code SessionEnd hook.
# Runs automatically when the session closes (reasons: clear|resume|logout|prompt_input_exit).
#
# IMPORTANT LIMITATION: the session is ending, so Claude will NOT generate more text.
# This script therefore does only MECHANICAL work — it cannot write an intelligent
# summary (that's what /e4:end-session is for, while Claude is still active).
#
# What it guarantees:
#   1. A breadcrumb is appended to session-log.md IF the latest entry is stale,
#      so a session is never completely unrecorded — even if the user closed the
#      terminal without running /e4:end-session.
#   2. Completed tasks are archived and the daily summary is refreshed (best-effort).
#
# Heavy/slow work is backgrounded so the hook returns immediately (avoids "Hook cancelled").
#
# Input: JSON on stdin (session_id, reason, cwd, transcript_path, ...).

INPUT="$(cat)"                       # consume stdin
MEM=".ai-memory"
TODAY="$(date +%F)"
NOW="$(date '+%Y-%m-%d %H:%M')"

# Try to pull the reason out of the JSON without requiring jq.
REASON="$(printf '%s' "$INPUT" | sed -n 's/.*"reason"[: ]*"\([^"]*\)".*/\1/p')"
[ -z "$REASON" ] && REASON="unknown"

[ ! -d "$MEM" ] && exit 0

LOG="$MEM/session-log.md"
if [ -f "$LOG" ]; then
  # Is today's date already present in the most recent entry? If the latest
  # '## Session' block mentions today AND has a TL;DR, assume /end-session ran.
  LAST_BLOCK="$(awk '/^## Session/{c++} c==1{print} c==2{exit}' "$LOG")"
  if echo "$LAST_BLOCK" | grep -q "$TODAY" && echo "$LAST_BLOCK" | grep -qi "TL;DR"; then
    : # properly logged already — nothing to do
  else
    # Append a mechanical breadcrumb entry. Insert after the first blank line that
    # follows the front-matter/title so it lands near the top.
    BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
    [ -z "$BRANCH" ] && BRANCH="n/a"
    DIRTY="$(git status --short 2>/dev/null | wc -l | tr -d ' ')"
    BREADCRUMB="## Session — $TODAY (auto-recorded by SessionEnd hook)
**Time**: ended $NOW
**Branch**: $BRANCH
**TL;DR**: ⚠️ Session ended via '$REASON' without /e4:end-session. This is an auto-breadcrumb — next session should reconstruct details from git log and write a proper entry.
**Uncommitted files at end**: $DIRTY
**Next actions**:
1. Review git log/diff for this session and backfill the summary.
"
    # Prepend the breadcrumb right after the first '# ' title line block.
    TMP="$(mktemp)"
    awk -v bc="$BREADCRUMB" '
      BEGIN{done=0}
      { print }
      /^#[^#]/ && done==0 { print ""; print bc; done=1 }
    ' "$LOG" > "$TMP" && mv "$TMP" "$LOG"
  fi
fi

# --- Best-effort maintenance, backgrounded so we exit fast ---
VAULT="${AI_VAULT:-$HOME/AI-Vault}"
PROJECTS_ROOT="${AI_PROJECTS_ROOT:-$(dirname "$PWD")}"
PYDIR="${AI_MEMORY_PYDIR:-$HOME/AI-Vault/automation/python}"
(
  if [ -f "$PYDIR/archive_completed_tasks.py" ]; then
    python3 "$PYDIR/archive_completed_tasks.py" --project "$PWD" --vault "$VAULT" --infer
  fi
  if [ -f "$PYDIR/generate_daily_summary.py" ]; then
    python3 "$PYDIR/generate_daily_summary.py" --vault "$VAULT" --projects-root "$PROJECTS_ROOT"
  fi
) >/dev/null 2>&1 &

exit 0
