#!/usr/bin/env python3
"""
context_nudge.py — e4 UserPromptSubmit hook: nudge to checkpoint before context gets expensive.

Long sessions that drift across tasks re-send all old context on every turn. This hook adds ONE line
of context (never blocks) when:
  1. the conversation's context passes a threshold band (80k, 160k, ... tokens; override with
     E4_CONTEXT_NUDGE_TOKENS) — suggests /e4:end-session then /clear; once per band per session.
  2. the prompt names a TASK-YYYYMMDD-HHMMSS id that isn't the in-progress task — suggests a
     checkpoint + /clear before switching; once per task per session.

Context size = the latest main-thread assistant entry's usage (input + cache_read + cache_creation
tokens), read from the END of the transcript JSONL; falls back to file size / 4.
State lives in the OS temp dir keyed by session id, so nothing shows up in `git status`.
Any error -> exit 0 silently. Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

DEFAULT_THRESHOLD = 80_000
TAIL_BYTES = 512 * 1024  # the latest assistant entry is near the end; never load the whole file
TASK_STAMP = re.compile(r"TASK-\d{8}-\d{6}")


def threshold() -> int:
    try:
        value = int(os.environ.get("E4_CONTEXT_NUDGE_TOKENS", DEFAULT_THRESHOLD))
        return value if value > 0 else DEFAULT_THRESHOLD
    except ValueError:
        return DEFAULT_THRESHOLD


def context_tokens(transcript: Path) -> int:
    size = transcript.stat().st_size
    with transcript.open("rb") as fh:
        fh.seek(max(0, size - TAIL_BYTES))
        lines = fh.read().split(b"\n")
    if size > TAIL_BYTES:
        lines = lines[1:]  # first line is probably cut in half
    for raw in reversed(lines):
        if b'"usage"' not in raw:
            continue
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if entry.get("type") != "assistant" or entry.get("isSidechain"):
            continue
        usage = (entry.get("message") or {}).get("usage") or {}
        total = sum(int(usage.get(k) or 0) for k in
                    ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        if total:
            return total
    return size // 4


def in_progress_ids(project: Path) -> list[str]:
    ids = []
    tasks = project / ".ai-memory" / "tasks"
    for path in sorted(tasks.glob("*.md")) if tasks.is_dir() else []:
        head = path.read_text(encoding="utf-8", errors="ignore")[:2000]
        status = re.search(r"^status\s*:\s*([\w-]+)", head, flags=re.MULTILINE)
        if status and status.group(1).lower() == "in-progress":
            id_match = re.search(r"^id\s*:\s*(\S+)", head, flags=re.MULTILINE)
            ids.append(id_match.group(1).strip("\"'") if id_match else path.stem)
    return ids


def main() -> int:
    event = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace") or "{}")
    session = re.sub(r"[^A-Za-z0-9_-]", "_", str(event.get("session_id") or "nosession"))
    marker = Path(tempfile.gettempdir()) / f".e4_nudge_{session}.json"
    try:
        state = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    band_seen = int(state.get("band", 0))
    tasks_seen = set(state.get("tasks", []))
    notes = []

    transcript = event.get("transcript_path")
    if transcript and Path(transcript).is_file():
        tokens = context_tokens(Path(transcript))
        band = tokens // threshold()
        if band >= 1 and band > band_seen:
            band_seen = band
            notes.append(f"e4: this conversation is ~{tokens // 1000}k tokens of context. If this is a "
                         "natural break, suggest /e4:end-session then /clear to continue from the summary.")

    mentioned = list(dict.fromkeys(TASK_STAMP.findall(str(event.get("prompt") or ""))))
    if mentioned:
        current = in_progress_ids(Path(event.get("cwd") or os.getcwd()))
        for stamp in mentioned:
            if current and stamp not in tasks_seen and not any(c.startswith(stamp) for c in current):
                tasks_seen.add(stamp)
                notes.append(f"e4: the prompt mentions {stamp}, but the in-progress task is {current[0]}. "
                             "Before switching, suggest a checkpoint (/e4:end-session) and /clear.")

    if notes:
        marker.write_text(json.dumps({"band": band_seen, "tasks": sorted(tasks_seen)}), encoding="utf-8")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                                 "additionalContext": "\n".join(notes)}}))
    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception:  # never block or disturb the prompt
        pass
    sys.exit(0)
