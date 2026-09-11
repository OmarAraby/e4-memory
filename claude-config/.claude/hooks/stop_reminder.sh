#!/usr/bin/env bash
# stop_reminder.sh — Claude Code Stop hook (OPTIONAL, gentle enforcement).
# Fires when Claude finishes a response (once per turn).
#
# Purpose: nudge toward saving memory when meaningful work happened but the
# no session file has been written today. This is what makes Claude "remember"
# to log — without you having to rely on it.
#
# Behavior is intentionally SOFT: it injects a reminder via additionalContext at
# most once per session (guarded by a marker file). It does NOT hard-block, to
# avoid loops. If you want hard enforcement, see the commented block at the bottom.
#
# Input: JSON on stdin. Output: optional JSON to control the stop.

INPUT="$(cat)"
MEM=".ai-memory"
TODAY="$(date +%F)"
# Marker lives in temp (keyed by project path + date) so it never shows up in
# 'git status' and never needs gitignoring.
_KEY="$(printf '%s' "$PWD" | tr -c 'A-Za-z0-9' '_')"
MARKER="${TMPDIR:-/tmp}/.claude_stop_${_KEY}_${TODAY}"

# No memory, or already reminded today → stay silent.
[ ! -d "$MEM" ] && exit 0
[ -f "$MARKER" ] && exit 0

# Did meaningful work happen? Use uncommitted changes as a cheap proxy.
CHANGES="$(git status --short 2>/dev/null | wc -l | tr -d ' ')"
[ "${CHANGES:-0}" -eq 0 ] && exit 0

# Has this session already been logged today?
# Tier-2: sessions are one file per session in sessions/. A REAL entry for today = a file named
# with today's date that contains a TL;DR (auto-breadcrumbs from session_end.sh carry a TL;DR
# marked with a warning, but they are only written AFTER the session ends, so they can't race us).
# This is the same test session_end.sh uses — keep the two in sync.
if [ -d "$MEM/sessions" ]; then
  for f in "$MEM/sessions/$TODAY"*.md; do
    [ -f "$f" ] || continue
    grep -qi "TL;DR" "$f" && exit 0   # already logged today
  done
fi
# Legacy fallback (pre-Tier-2 repos): a same-day TL;DR entry in the old single session-log.md counts.
LOG="$MEM/session-log.md"
if [ -f "$LOG" ]; then
  LAST_BLOCK="$(awk '/^## Session/{c++} c==1{print} c==2{exit}' "$LOG")"
  echo "$LAST_BLOCK" | grep -q "$TODAY" && echo "$LAST_BLOCK" | grep -qi "TL;DR" && exit 0
fi

# Emit a one-time, non-blocking reminder as additional context.
touch "$MARKER"
cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "additionalContext": "Reminder: there are uncommitted changes and no session file logged for today yet. If this is a good stopping point, run /e4:end-session to write a session file to .ai-memory/sessions/ and update progress.md and the relevant tasks/ file so the next session can resume cleanly."
  }
}
JSON
exit 0

# ---------------------------------------------------------------------------
# HARD ENFORCEMENT (opt-in): block the stop and force Claude to log first.
# Replace the JSON above with this. Note: Stop-hook blocks are capped by
# CLAUDE_CODE_STOP_HOOK_BLOCK_CAP (default 8) to prevent infinite loops.
#
# echo '{"decision":"block","reason":"Run /e4:end-session to persist this session before stopping."}'
# exit 0
# ---------------------------------------------------------------------------
