#!/usr/bin/env python3
"""
e4_pr.py — Collect the facts /e4:pr needs to write a pull-request description, so the model only
writes the judgment parts (what / why) instead of re-deriving git history.

Owns: reading git and .ai-memory/ (read-only) and printing a facts sheet. Must NOT write the PR
text, push, or call `gh pr create` — the command does that, and only when the user asked to.

Usage:
    python3 e4_pr.py facts [--project PATH] [--base BRANCH] [--note TEXT]

A note starting with the word `create` sets "Mode: create"; the rest of the note is free text.
Works in any git repo; without .ai-memory/ the task and session sections are omitted.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e4_session import current_branch, git  # noqa: E402  # pyright: ignore[reportMissingImports]
from generate_status import parse_task  # noqa: E402  # pyright: ignore[reportMissingImports]

SIZE_LIMIT = 400  # coding-standards: PRs under ~400 changed lines, generated files excluded
MAX_COMMITS = 30
MAX_FILES = 60
MAX_SESSIONS = 5
TASK_ID = re.compile(r"TASK-\d{8}-\d{6}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?")
BREAKING = re.compile(r"^\w+(?:\([^)]*\))?!:|BREAKING[ -]CHANGE|^BREAKING:", re.MULTILINE)
GENERATED = ["*.lock", "package-lock.json", "pnpm-lock.yaml", "go.sum", "poetry.lock", "*.min.js",
             "*.min.css", "*.Designer.cs", "*/Migrations/*", "*.snap", "*.g.cs",
             ".ai-memory/active-tasks.md", "*/sqlc/*", "*_gen.go", "*.pb.go"]
GROUPS = [("tests", re.compile(r"(^|/)(tests?|spec|__tests__)/|(_test|\.test|\.spec|Tests?)\.\w+$|"
                               r"(^|/)test_[^/]+$", re.IGNORECASE)),
          ("memory", re.compile(r"^\.ai-memory/")),
          ("docs", re.compile(r"\.md$|^docs/", re.IGNORECASE)),
          ("config", re.compile(r"(^|/)\.|\.(json|ya?ml|toml|ini|csproj|props|sln)$|"
                                r"(^|/)(Dockerfile|Makefile)$", re.IGNORECASE))]


def ref_exists(root: Path, ref: str) -> bool:
    return bool(git(root, "rev-parse", "--verify", "-q", ref + "^{commit}").strip())


def resolve_base(root: Path, explicit: str) -> str:
    """Prefer origin/<base> (what the PR is compared against) over a possibly stale local branch."""
    candidates = [explicit] if explicit else []
    remote_head = git(root, "symbolic-ref", "--short", "-q", "refs/remotes/origin/HEAD").strip()
    if remote_head and not explicit:
        candidates.append(remote_head.removeprefix("origin/"))
    if not explicit:
        candidates += ["main", "master", "develop"]
    for name in candidates:
        for ref in (f"origin/{name}", name):
            if ref_exists(root, ref):
                return ref
    return ""


def is_generated(path: str) -> bool:
    return any(fnmatch.fnmatch(path, pat) or fnmatch.fnmatch("/" + path, pat) for pat in GENERATED)


def group_of(path: str) -> str:
    return next((name for name, rx in GROUPS if rx.search(path)), "code")


def commits(root: Path, rng: str) -> list[tuple[str, str, str]]:
    raw = git(root, "log", "--no-merges", "--format=%h%x1f%s%x1f%b%x1e", rng)
    out = []
    for rec in raw.split("\x1e"):
        parts = rec.strip("\n").split("\x1f")
        if len(parts) == 3:
            body = "\n".join(ln for ln in parts[2].strip().splitlines()
                             if not ln.lower().startswith(("co-authored-by:", "signed-off-by:")))
            out.append((parts[0], parts[1], body.strip()))
    return out


def numstat(root: Path, base: str) -> list[tuple[str, int, int]]:
    rows = []
    for line in git(root, "diff", "--numstat", "-M", f"{base}...HEAD").splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add, dele, path = parts
        path = re.sub(r"\{[^{}]* => ([^{}]*)\}", r"\1", path).split(" => ")[-1]  # renames: new name
        rows.append((path, int(add) if add.isdigit() else 0, int(dele) if dele.isdigit() else 0))
    return rows


def section(text: str, heading: str, cap: int = 10) -> list[str]:
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    lines = [ln.rstrip() for ln in (m.group(1) if m else "").splitlines() if ln.strip()]
    return lines[:cap]


def field(text: str, name: str) -> str:
    m = re.search(rf"\*\*{re.escape(name)}\*\*:?\s*(.+)|^{re.escape(name)}:\s*(.+)$", text, re.MULTILINE)
    return (m.group(1) or m.group(2)).strip() if m else ""


def gh_pr(root: Path) -> str:
    try:
        proc = subprocess.run(["gh", "pr", "view", "--json", "number,url,state"], cwd=root,
                              capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return "unknown (gh CLI not available)"
    if proc.returncode != 0:
        return "none"
    try:
        info = json.loads(proc.stdout)
        return f"#{info['number']} ({info['state'].lower()}) {info['url']}"
    except (ValueError, KeyError):
        return "unknown"


def cmd_facts(root: Path, base_arg: str, note: str) -> int:
    if not git(root, "rev-parse", "--is-inside-work-tree").strip():
        print(f"e4: error: {root} is not a git repository.")
        return 1
    branch = current_branch(root)
    base = resolve_base(root, base_arg)
    if not base:
        print(f"e4: error: base branch {base_arg or 'main/master'} not found. Pass --base <branch>.")
        return 1
    if base.removeprefix("origin/") == branch:
        print(f"e4: error: you are on the base branch ({branch}). Switch to the feature branch first.")
        return 1
    log = commits(root, f"{base}..HEAD")
    if not log:
        print(f"e4: error: {branch} has no commits that aren't already in {base}. Nothing to describe.")
        return 1

    words = note.split(maxsplit=1)
    mode = "create" if words and words[0].lower() == "create" else "draft"
    note = (words[1] if len(words) > 1 else "") if mode == "create" else note
    body_path = Path(git(root, "rev-parse", "--path-format=absolute", "--git-path", "e4/PR_BODY.md").strip()
                     or root / ".git" / "e4" / "PR_BODY.md")

    rows = numstat(root, base)
    counted = [(p, a, d) for p, a, d in rows if not is_generated(p)]
    adds, dels = sum(a for _, a, _ in counted), sum(d for _, _, d in counted)
    gen_lines = sum(a + d for p, a, d in rows if is_generated(p))
    groups: dict[str, list[str]] = {}
    for p, a, d in rows:
        groups.setdefault(group_of(p), []).append(f"{p} (+{a}/-{d})" + (" [generated]" if is_generated(p) else ""))

    upstream = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").strip()
    ahead = git(root, "rev-list", "--count", "@{u}..HEAD").strip() if upstream else ""
    dirty = git(root, "status", "--porcelain").strip()

    out = [f"Mode: {mode}", f"Branch: {branch}", f"Base: {base}", f"Body file: {body_path}",
           f"Existing PR: {gh_pr(root)}",
           "Pushed: " + (f"yes ({upstream}), {ahead} local commit(s) not pushed" if upstream else "no upstream yet")]
    if dirty:
        out.append("WARNING: uncommitted changes exist — they will NOT be in this PR.")
    if note:
        out.append(f"User note: {note}")

    total = adds + dels
    out += ["", "## Size",
            f"+{adds} / -{dels} = {total} changed lines in {len(counted)} file(s), generated files excluded"
            + (f" ({gen_lines} generated lines not counted)" if gen_lines else "") + ".",
            f"OVER the ~{SIZE_LIMIT}-line PR guideline — the description must say why it isn't split."
            if total > SIZE_LIMIT else f"Within the ~{SIZE_LIMIT}-line guideline."]

    out += ["", f"## Commits ({len(log)})"]
    for sha, subject, body in log[:MAX_COMMITS]:
        out.append(f"- {sha} {subject}")
        out += [f"    {ln}" for ln in body.splitlines()[:8]]
    if len(log) > MAX_COMMITS:
        out.append(f"- … {len(log) - MAX_COMMITS} older commit(s) omitted")

    out += ["", "## Files by kind"]
    shown = 0
    for name in ("code", "tests", "docs", "config", "memory"):
        for entry in groups.get(name, []):
            if shown < MAX_FILES:
                out.append(f"- [{name}] {entry}")
            shown += 1
    if shown > MAX_FILES:
        out.append(f"- … {shown - MAX_FILES} more file(s)")
    changed = {p for p, _, _ in rows}
    out.append(f"Tests changed: {'yes' if groups.get('tests') else 'NO'}. "
               f"README changed: {'yes' if any(p.lower().endswith('readme.md') for p in changed) else 'no'}. "
               f"CHANGELOG changed: {'yes' if any('changelog' in p.lower() for p in changed) else 'no'}.")

    breaking = [f"{sha} {subject}" for sha, subject, body in log if BREAKING.search(f"{subject}\n{body}")]
    out += ["", "## Breaking changes", *([f"- {b}" for b in breaking] or ["None marked in commits."])]

    mem = root / ".ai-memory"
    if mem.is_dir():
        adr_diff = git(root, "diff", f"{base}...HEAD", "--", ".ai-memory/decisions.md")
        adrs = [m.group(1).strip() for m in re.finditer(r"^\+#+\s*(ADR-\d+.*)$", adr_diff, re.MULTILINE)]
        out += ["", "## ADRs added on this branch", *([f"- {a}" for a in adrs] or ["None."])]

        text_for_ids = "\n".join([branch, note] + [f"{s}\n{b}" for _, s, b in log])
        session_paths = sorted(p for p in changed if p.startswith(".ai-memory/sessions/") and p.endswith(".md"))
        sessions = [(p, (root / p).read_text(encoding="utf-8", errors="replace"))
                    for p in session_paths[-MAX_SESSIONS:] if (root / p).is_file()]
        text_for_ids += "\n".join(t for _, t in sessions)
        task_files = {p for p in changed if p.startswith(".ai-memory/tasks/") and p.endswith(".md")}
        ids = sorted(set(TASK_ID.findall(text_for_ids)))
        tasks_dir = mem / "tasks"
        found = []
        if tasks_dir.is_dir():
            for f in sorted(tasks_dir.glob("TASK-*.md")):
                rel = f".ai-memory/tasks/{f.name}"
                if rel in task_files or any(f.name.startswith(i) or i.startswith(f.stem) for i in ids):
                    found.append(f)
        out += ["", "## Tasks"]
        for f in found:
            info, text = parse_task(f), f.read_text(encoding="utf-8", errors="replace")
            out.append(f"- {info['id']} — {info['title']} (status: {info['status']})")
            out += [f"    {ln}" for ln in section(text, "Acceptance Criteria")]
        if not found:
            out.append("None referenced by branch name, commits, or session files.")

        out += ["", "## Sessions on this branch"]
        for p, text in sessions:
            out.append(f"- {Path(p).name}: TL;DR: {field(text, 'TL;DR') or '(missing)'}")
            for name in ("Decisions", "test_status"):
                if field(text, name):
                    out.append(f"    {name}: {field(text, name)}")
        if not sessions:
            out.append("None committed on this branch.")
    else:
        out += ["", "(No .ai-memory/ in this repo — tasks, sessions and ADRs omitted.)"]

    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("utf-8"))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect facts for a PR description.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("facts", help="print the facts sheet for the current branch")
    p.add_argument("--project", default=".", help="repository root (default: current directory)")
    p.add_argument("--base", default="", help="base branch (default: origin/HEAD, then main/master)")
    p.add_argument("--note", default="", help="free text; a leading 'create' selects create mode")
    args = ap.parse_args()
    return cmd_facts(Path(args.project).resolve(), args.base.strip(), args.note.strip())


if __name__ == "__main__":
    sys.exit(main())
