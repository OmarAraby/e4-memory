#!/usr/bin/env python3
"""commit_suggest.py — Claude Code Stop hook: suggest a commit after Claude changes files.

Fires when Claude finishes a reply. If Claude changed files in this turn and the git repo is
dirty, it blocks the stop once and asks Claude to end with a suggested Conventional Commits
message. It never commits — committing stays an explicit user request.

"Changed files this turn" = an Edit/Write/MultiEdit/NotebookEdit tool call since the last real
user prompt (read from the transcript), or a shell call that changed the working-tree
fingerprint since the previous Stop. Stays silent if the reply already ends with a suggestion
(text after the turn's last change has `git commit -m` or a "Suggested commit" heading). Fail-open: any error -> exit 0.
Stdlib only.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}

CHANGE_TOOLS = EDIT_TOOLS | SHELL_TOOLS
SUGGESTION_RE = re.compile(r"git commit -m|^#+\s*Suggested commit", re.IGNORECASE | re.MULTILINE)

# Mirrors "Suggested commit format" in User/coding-standards.md — keep the two in sync.
REASON = (
    "You changed files in this turn and they are not committed. End your reply with ONE suggested "
    "commit in this exact layout (do NOT run it):\n"
    "### Suggested commit (not run)\n"
    "**type(scope): subject**  (Conventional Commits)\n"
    "Why: one or two lines on the reason, not a list of edits.\n"
    "Files (N):\n- path/one\n- path/two\n"
    "then one ```bash block: one `git add <repo-relative path>` line per file, then "
    "`git commit -m \"type(scope): subject\" -m \"Why line(s).\"`.\n"
    "Unrelated changes: one such block per commit. Work in progress: say so in one line instead."
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


def read_turn(transcript_path):
    """Assistant content blocks since the last real user prompt; None if unreadable."""
    try:
        with open(transcript_path, encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
    except (OSError, ValueError, TypeError):
        return None
    start = 0
    for i, e in enumerate(entries):
        if is_real_prompt(e):
            start = i
    blocks = []
    for e in entries[start:]:
        if e.get("type") == "assistant":
            blocks += [b for b in (e.get("message") or {}).get("content") or [] if isinstance(b, dict)]
    return blocks


def already_suggested(blocks, last_message):
    """True if the reply already shows a commit suggestion after the turn's last change."""
    if isinstance(last_message, str) and SUGGESTION_RE.search(last_message):
        return True
    texts = []
    for b in blocks or []:
        if b.get("type") == "tool_use" and b.get("name") in CHANGE_TOOLS:
            texts = []  # a suggestion made before a later change doesn't count
        elif b.get("type") == "text":
            texts.append(b.get("text") or "")
    return bool(SUGGESTION_RE.search("\n".join(texts)))


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
        blocks = read_turn(payload.get("transcript_path") or "")
        tools = None if blocks is None else {b.get("name") for b in blocks if b.get("type") == "tool_use"}
        edited = bool(tools and tools & EDIT_TOOLS)
        shelled = tools is None or bool(tools & SHELL_TOOLS)
        # Shell-made changes count only if the tree differs from what we saw at the last Stop.
        changed = edited or (shelled and previous is not None and current != previous)
        if changed and already_suggested(blocks, payload.get("last_assistant_message")):
            changed = False  # Claude already ended with a suggestion; don't make it repeat

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
