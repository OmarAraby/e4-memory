#!/usr/bin/env python3
"""commit_suggest.py — Claude Code Stop hook: suggest a commit after Claude changes files.

Fires when Claude finishes a reply. If Claude changed files in this turn and the git repo is
dirty, it blocks the stop once and asks Claude to end with a suggested Conventional Commits
message. It never commits — committing stays an explicit user request.

"Changed files this turn" = an Edit/Write/MultiEdit/NotebookEdit tool call since the last real
user prompt (read from the transcript), or a shell call that changed the working-tree
fingerprint since the previous Stop. Fail-open: any error -> exit 0 silently.
Stdlib only.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}

REASON = (
    "You changed files in this turn and they are not committed. Finish your reply with a "
    "suggested commit for these changes: a Conventional Commits message "
    "(`type(scope): subject`, plus a short body if the *why* isn't obvious) and the exact "
    "`git add <files>` / `git commit` commands. Only suggest it — do NOT run the commit. "
    "If the changes are not yet a coherent unit (work in progress), say so in one line instead."
)


def git(cwd, *args):
    r = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=8,
    )
    return r.returncode, r.stdout


def fingerprint(cwd, status):
    """Hash of tracked diffs + untracked files' size/mtime; changes whenever the tree does."""
    h = hashlib.sha256(status.encode())
    for args in (("diff", "--no-ext-diff"), ("diff", "--cached", "--no-ext-diff")):
        h.update(git(cwd, *args)[1].encode())
    _, untracked = git(cwd, "ls-files", "--others", "--exclude-standard")
    for rel in untracked.splitlines()[:500]:
        try:
            st = os.stat(os.path.join(cwd, rel))
            h.update(f"{rel}:{st.st_size}:{st.st_mtime_ns}".encode())
        except OSError:
            pass
    return h.hexdigest()


def is_real_prompt(entry):
    """A user entry typed by the human (not a tool_result echo or meta/hook message)."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
    return False


def tools_used_this_turn(transcript_path):
    """Tool names called since the last real user prompt; None if the transcript is unreadable."""
    try:
        with open(transcript_path, encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
    except (OSError, ValueError, TypeError):
        return None
    start = 0
    for i, e in enumerate(entries):
        if is_real_prompt(e):
            start = i
    names = set()
    for e in entries[start:]:
        if e.get("type") != "assistant":
            continue
        for b in (e.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                names.add(b.get("name"))
    return names


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    # Already continuing because a Stop hook blocked once this turn -> never loop.
    if payload.get("stop_hook_active"):
        return

    cwd = payload.get("cwd") or ""
    if not os.path.isdir(cwd):
        cwd = os.getcwd()  # hooks run in the project dir; covers odd/POSIX-style paths on Windows
    code, top = git(cwd, "rev-parse", "--show-toplevel")
    if code != 0:
        return  # not a git repo
    top = top.strip()
    _, status = git(top, "status", "--porcelain")

    key = hashlib.sha1(f"{payload.get('session_id', '')}|{top}".encode()).hexdigest()[:16]
    state = os.path.join(tempfile.gettempdir(), f".claude_commit_suggest_{key}")
    try:
        with open(state, encoding="utf-8") as f:
            previous = f.read().strip()
    except OSError:
        previous = None

    if not status.strip():
        current = ""
        changed = False
    else:
        current = fingerprint(top, status)
        tools = tools_used_this_turn(payload.get("transcript_path") or "")
        edited = bool(tools and tools & EDIT_TOOLS)
        shelled = tools is None or bool(tools & SHELL_TOOLS)
        # Shell-made changes count only if the tree differs from what we saw at the last Stop.
        changed = edited or (shelled and previous is not None and current != previous)

    try:
        with open(state, "w", encoding="utf-8") as f:
            f.write(current)
    except OSError:
        pass

    if changed:
        print(json.dumps({"decision": "block", "reason": REASON}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # fail-open: a broken hook must never block Claude
        pass
    sys.exit(0)
