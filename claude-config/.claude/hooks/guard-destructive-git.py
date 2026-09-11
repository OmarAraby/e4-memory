#!/usr/bin/env python3
"""
guard-destructive-git.py — e4 PreToolUse hook.

Blocks dangerous Bash commands BEFORE they run by reading the PreToolUse event
JSON on stdin and returning a "deny" decision. Two guard families:

  1. Destructive git / filesystem ops (force-push, reset --hard, clean -f,
     branch -D, rm -rf).
  2. Secret/credential leaks — refuses to `git add` a secret file, and refuses a
     `git commit` whose STAGED files include one (caught before it happens).

Stdlib only. Fail-safe: if anything can't be parsed/inspected, it ALLOWS
(it never blocks a command it didn't understand).
"""
import os
import re
import sys
import json
import subprocess

# --- secret/credential file patterns (matched case-insensitively on the path) ---
SECRET_PATTERNS = [
    r"(^|/)\.env(\.[\w-]+)?$",                 # .env, .env.local, .env.production
    r"\.(key|pem|pfx|p12|keystore|jks)$",      # private keys / cert bundles
    r"(^|/)id_(rsa|dsa|ecdsa|ed25519)$",       # SSH private keys
    r"(^|/)\.?credentials(\.[\w-]+)?$",         # credentials / .credentials.json
    r"(^|/)secrets?\.(json|ya?ml|txt|env)$",   # secrets.json / secret.yaml
]
SECRET_EXCEPTIONS = [r"\.env\.(example|sample|template)$"]


def is_secret(path: str) -> bool:
    p = path.strip().strip('"').strip("'").lower()
    if not p:
        return False
    if any(re.search(x, p) for x in SECRET_EXCEPTIONS):
        return False
    return any(re.search(s, p) for s in SECRET_PATTERNS)


def staged_files(cwd: str):
    try:
        r = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    except Exception:
        pass
    return []


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "[e4 guard] " + reason,
        }
    }))
    sys.exit(0)


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = event.get("tool_input") or {}
    cmd = ti.get("command", "") if isinstance(ti, dict) else ""
    if not cmd or not cmd.strip():
        sys.exit(0)

    c = " " + re.sub(r"\s+", " ", cmd.strip()) + " "
    is_git = re.search(r"\bgit\b", c) is not None

    # ============ SECRET / CREDENTIAL GUARDS ============
    # Explicitly staging a secret file (catches `git add .env`, `git add -f key.pem`)
    if is_git and re.search(r"\badd\b", c):
        for tok in cmd.split():
            if is_secret(tok):
                deny("Refusing to stage a secret/credential file: '%s'. "
                     "Add it to .gitignore and keep secrets in an untracked .env / secret store." % tok)

    # Committing when a secret is already staged (the real 'before it happens' catch)
    if is_git and re.search(r"\bcommit\b", c):
        cwd = event.get("cwd") or os.getcwd()
        for f in staged_files(cwd):
            if is_secret(f):
                deny("A secret/credential file is staged for commit: '%s'. "
                     "Unstage it with `git rm --cached '%s'` and gitignore it before committing." % (f, f))

    # ============ DESTRUCTIVE GIT / FS GUARDS ============
    # git push --force / -f / +refspec / --mirror  (allow --force-with-lease)
    if is_git and re.search(r"\bpush\b", c):
        if "--mirror" in c:
            deny("`git push --mirror` rewrites ALL remote refs. Push specific branches instead.")
        if "--force-with-lease" not in c:
            if (re.search(r"--force(\b|=)", c)
                    or re.search(r" -[A-Za-z]*f[A-Za-z]* ", c)
                    or re.search(r"\bpush\b[^|;&]* \+[\w./-]+", c)):
                deny("Force-push can overwrite remote history. If you truly must, use "
                     "`--force-with-lease` (safer) and confirm with the user first.")

    # git reset --hard
    if is_git and re.search(r"\breset\b", c) and re.search(r"--hard\b", c):
        deny("`git reset --hard` irreversibly discards uncommitted work. Use --soft/--mixed, "
             "or `git stash` first.")

    # git clean -f (deletes untracked files; -fd also dirs)
    if is_git and re.search(r"\bclean\b", c) and not re.search(r"(-n\b|--dry-run\b)", c):
        if "--force" in c or re.search(r" -[A-Za-z]*f[A-Za-z]* ", c):
            deny("`git clean -f` permanently deletes untracked files. Preview first with `git clean -n`.")

    # git branch -D / --delete --force
    if is_git and re.search(r"\bbranch\b", c):
        if re.search(r" -D\b", c) or (re.search(r"--delete\b", c) and re.search(r"--force\b", c)):
            deny("Force-deleting a branch (`-D`) can lose unmerged commits. Use `-d` (merged only) "
                 "unless you've confirmed the branch is disposable.")

    # rm -rf / -fr / -r -f / --recursive --force
    if re.search(r"\brm\b", c):
        if (re.search(r" -[A-Za-z]*r[A-Za-z]*f[A-Za-z]* ", c)
                or re.search(r" -[A-Za-z]*f[A-Za-z]*r[A-Za-z]* ", c)
                or (re.search(r" -[A-Za-z]*r[A-Za-z]* ", c) and re.search(r" -[A-Za-z]*f[A-Za-z]* ", c))
                or (re.search(r"--recursive\b", c) and re.search(r"--force\b", c))):
            deny("`rm -rf` permanently deletes recursively with no undo. Re-check the path; "
                 "delete more narrowly, or move to a trash folder instead.")

    sys.exit(0)  # nothing matched -> allow


if __name__ == "__main__":
    main()
