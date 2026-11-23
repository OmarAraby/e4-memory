#!/usr/bin/env bash
# session_start.sh — Claude Code SessionStart hook.
# Whatever this script prints to STDOUT is injected into Claude's context at the
# start of every session/resume/clear. That output IS the resume: status, current focus,
# and the last saved session's TL;DR + Next actions. Keep it small (target < ~300 tokens);
# the model opens individual memory files only when the current task needs them.
#
# Input: JSON on stdin (session_id, cwd, source, ...). We don't need it, but read it
# so the pipe doesn't break.
#
# Keep this FAST (it runs on every session). Output is plain text/markdown.

cat >/dev/null  # consume stdin

MEM=".ai-memory"

# e4_has_tldr FILE — true iff FILE carries a real TL;DR. e4_session.py drafts contain the marker
# "e4:fill TL;DR" until /e4:end-session fills them, so an unfilled draft still counts as incomplete.
# Keep this function identical in session_start.sh, session_end.sh and stop_reminder.sh.
e4_has_tldr() { grep -qi "TL;DR" "$1" && ! grep -q "e4:fill TL;DR" "$1"; }

# e4_section FILE LABEL MAX — print a session file's LABEL entry ("**TL;DR**: ...", "**Next actions**:")
# plus up to MAX body lines; stops at a blank line, the next **Field** or a heading. FILE may be "-".
e4_section() {
  awk -v label="$2" -v max="$3" '
    !on && index($0, label) {
      on = 1; rest = substr($0, index($0, label) + length(label)); gsub(/[*:#[:space:]]/, "", rest)
      body = (rest != ""); print; next
    }
    on {
      if ($0 ~ /^[[:space:]]*$/) { if (body) exit; next }
      if ($0 ~ /^(\*\*|#)/) exit
      body = 1; if (++n > max) exit; print
    }' "$1"
}

# If there's no memory here, gently suggest initializing and exit.
if [ ! -d "$MEM" ]; then
  echo "ℹ️ No .ai-memory/ found in this project. Run /e4:init to set up persistent memory."
  exit 0
fi

# active-tasks.md is a GENERATED view of tasks/* (gitignored). Refresh it from the task
# files before reading (best-effort, fast). No-op if the generator isn't installed.
PYDIR="${AI_MEMORY_PYDIR:-$HOME/AI-Vault/automation/python}"
[ -f "$PYDIR/generate_status.py" ] && python3 "$PYDIR/generate_status.py" --project "$PWD" >/dev/null 2>&1

echo "## 🧠 Project memory — e4 (forged by Omar Araby & contributors)"
echo "This is the resume. Open .ai-memory/ files only when the current task needs them; check decisions.md before architectural changes."
echo

# --- Status (≤4 lines): Phase + Health from progress.md (bold or plain labels), task counts from the view ---
STATUS="$( { [ -f "$MEM/progress.md" ] && grep -E -i '^[[:space:]]*([-*][[:space:]]*)?(\*\*)?(Phase|Health)(\*\*)?[[:space:]]*:' "$MEM/progress.md" | head -2
            [ -f "$MEM/active-tasks.md" ] && grep -E '^\*\*Tasks:\*\*' "$MEM/active-tasks.md" | head -1; } \
          | sed -E 's/\*\*//g; s/^[[:space:]]*[-*][[:space:]]*//; s/^/- /')"
if [ -n "$STATUS" ]; then
  echo "### Status"
  echo "$STATUS"
  echo
fi

# --- Current focus (≤5 lines): the generated "Current Task" section, minus the derivable file links ---
if [ -f "$MEM/active-tasks.md" ]; then
  FOCUS="$(awk '/^##[[:space:]].*[Cc]urrent/{flag=1; next} /^##[[:space:]]/{flag=0} flag' "$MEM/active-tasks.md" \
    | sed '/^[[:space:]]*$/d' | sed -E 's/ → `tasks\/[^`]*`//; s/ _\(priority: [a-z]+\)_//; s/\*\*//g' | head -5)"
  if [ -n "$FOCUS" ]; then
    echo "### Current focus"
    echo "$FOCUS"
    echo
  fi
fi

# --- Last session: TL;DR + Next actions only ---
# One file per session in sessions/; names are timestamp-prefixed, so the lexically-last is newest.
# Match ONLY the naming contract (YYYY-...-*.md): a bare *.md glob would pick sessions/README.md.
if [ -d "$MEM/sessions" ]; then
  FILES="$(ls -1 "$MEM/sessions"/[0-9][0-9][0-9][0-9]-*.md 2>/dev/null | LC_ALL=C sort -r)"
  LATEST="$(printf '%s\n' "$FILES" | head -1)"
  SAVED=""
  for f in $FILES; do
    case "$f" in *-auto.md) continue ;; esac   # SessionEnd breadcrumb, not a real summary
    e4_has_tldr "$f" && { SAVED="$f"; break; }
  done
  if [ -n "$SAVED" ]; then
    echo "### Last session — $(basename "$SAVED" .md)"
    e4_section "$SAVED" "TL;DR" 3
    e4_section "$SAVED" "Next actions" 5
    echo
  fi
  if [ -n "$LATEST" ] && [ "$LATEST" != "$SAVED" ]; then
    echo "> ⚠️ The most recent session ($(basename "$LATEST" .md)) ended without /e4:end-session and was only auto-recorded. If the user wants it backfilled, they will ask — don't reconstruct it unprompted."
    echo
  fi
elif [ -f "$MEM/session-log.md" ]; then
  # Legacy single-file fallback (pre-Tier-2 repos): newest entry is the first "## Session" block.
  LAST_BLOCK="$(awk '/^## Session/{c++} c==1{print} c==2{exit}' "$MEM/session-log.md")"
  echo "### Last session (legacy session-log.md)"
  printf '%s\n' "$LAST_BLOCK" | e4_section - "TL;DR" 3
  printf '%s\n' "$LAST_BLOCK" | e4_section - "Next actions" 5
  echo
  if ! printf '%s\n' "$LAST_BLOCK" | grep -qi "TL;DR"; then
    echo "> ⚠️ The last session-log entry has no TL;DR (likely ended without /e4:end-session). If the user wants it backfilled, they will ask."
    echo
  fi
fi

echo "Before finishing real work: /e4:end-session."
exit 0
