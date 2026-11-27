#!/usr/bin/env python3
"""adr_nudge.py — Claude Code Stop hook: ask for an ADR when a change adds a dependency.

The coding standards require an ADR in .ai-memory/decisions.md when a change introduces a new
library, datastore or project reference. When the working tree adds one (compared with HEAD)
and decisions.md is untouched, this blocks the stop once and asks Claude to end its reply by
offering to record an ADR. Claude must not write the ADR unless the user agrees.

Version bumps are ignored: a package counts as new only if its name was added and not removed.
Silent when: no .ai-memory/, decisions.md already changed, the package was already mentioned this
session, E4_ADR_NUDGE=off, or a Stop hook is already continuing. Any error exits 0 silently.
Stdlib only.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

MAX_LISTED = 8
NOT_PACKAGES = {"name", "version", "description", "main", "module", "types", "type", "license",
                "private", "author", "homepage", "readme", "python", "edition", "requires-python",
                "authors", "keywords", "repository", "packagemanager", "engines", "workspaces",
                "node", "npm", "build-backend", "line-length", "target-version", "rust-version",
                "resolver", "packages", "include", "exclude", "scripts"}
VERSIONISH = r"""["'][\^~<>=*]?\s*(?:\d|latest|next|workspace:|npm:|file:|git|github:|https?:|link:)"""

# (glob on the file name, [(regex, kind)]) — group 1 of each regex is the dependency name.
RULES: list[tuple[str, list[tuple[re.Pattern, str]]]] = [
    ("package.json", [(re.compile(rf'^\s*"(@?[\w.\-/]+)"\s*:\s*{VERSIONISH}'), "package")]),
    ("composer.json", [(re.compile(rf'^\s*"([\w.\-]+/[\w.\-]+)"\s*:\s*{VERSIONISH}'), "package")]),
    ("*.csproj", [(re.compile(r'<PackageReference\s+Include="([^"]+)"', re.I), "package"),
                  (re.compile(r'<ProjectReference\s+Include="([^"]+)"', re.I), "project reference")]),
    ("*.fsproj", [(re.compile(r'<PackageReference\s+Include="([^"]+)"', re.I), "package")]),
    ("Directory.Packages.props", [(re.compile(r'<PackageVersion\s+Include="([^"]+)"', re.I), "package")]),
    ("packages.config", [(re.compile(r'<package\s+id="([^"]+)"', re.I), "package")]),
    ("go.mod", [(re.compile(r"^\s*(?:require\s+)?([\w.\-]+\.[\w.\-/]+)\s+v\d(?!.*//\s*indirect)"), "module")]),
    ("requirements*.txt", [(re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9_.\-]*)\s*(?:\[[^\]]*\])?\s*(?:[=<>!~]=?|;|$)"),
                            "package")]),
    ("pyproject.toml", [(re.compile(r'^\s*"([A-Za-z0-9][A-Za-z0-9_.\-]*)\s*(?:\[[^\]]*\])?\s*[<>=~!;"]'), "package"),
                        (re.compile(r'^\s*([A-Za-z0-9][A-Za-z0-9_.\-]*)\s*=\s*["{]'), "package")]),
    ("Cargo.toml", [(re.compile(r'^\s*([A-Za-z0-9_\-]+)\s*=\s*["{]'), "crate")]),
    ("Gemfile", [(re.compile(r"""^\s*gem\s+["']([^"']+)"""), "gem")]),
    ("build.gradle*", [(re.compile(r"""(?:implementation|api|compileOnly|runtimeOnly)\s*\(?\s*["']([^:"']+:[^:"']+)"""),
                        "library")]),
    ("pom.xml", [(re.compile(r"<artifactId>([^<]+)</artifactId>"), "artifact")]),
    ("docker-compose*.y*ml", [(re.compile(r"^\s*image:\s*[\"']?([^\s:\"'@]+)"), "service image")]),
    ("compose*.y*ml", [(re.compile(r"^\s*image:\s*[\"']?([^\s:\"'@]+)"), "service image")]),
]

REASON = (
    "This change adds {what} and .ai-memory/decisions.md was not updated. The coding standards "
    "require an ADR when a change introduces a new library/framework, datastore, or project "
    "reference. At the end of your reply, add ONE line asking the user whether to record an ADR "
    "for it (offer to draft Context / Decision / Alternatives considered / Consequences). Do NOT "
    "write the ADR unless they agree. If it is clearly trivial (a test-only or dev tool), say that "
    "in the same line instead."
)


def git(root: str, *args: str) -> tuple[int, str]:
    r = subprocess.run(["git", "-c", "core.quotepath=false", "-C", root, *args], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=10)
    return r.returncode, r.stdout


def rules_for(path: str):
    name = path.rsplit("/", 1)[-1]
    return [rx for pattern, rxs in RULES if fnmatch.fnmatch(name, pattern) for rx in rxs]


def names(lines: list[str], rules) -> dict[str, str]:
    found = {}
    for line in lines:
        if line.lstrip().startswith(("#", "//", "-r ", "--")):
            continue
        for rx, kind in rules:
            m = rx.search(line)
            if m and m.group(1).lower() not in NOT_PACKAGES:
                found[m.group(1)] = kind
    return found


def added_dependencies(root: str) -> list[tuple[str, str, str]]:
    """(name, kind, file) for dependencies added in the working tree relative to HEAD."""
    has_head = git(root, "rev-parse", "--verify", "-q", "HEAD")[0] == 0
    per_file: dict[str, tuple[list[str], list[str]]] = {}
    if has_head:
        _, diff = git(root, "diff", "HEAD", "--unified=0", "--no-ext-diff", "--no-color")
        current = None
        for line in diff.splitlines():
            if line.startswith("+++ "):
                current = line[6:] if line.startswith("+++ b/") else None
                if current:
                    per_file.setdefault(current, ([], []))
            elif current and line.startswith("+") and not line.startswith("+++"):
                per_file[current][0].append(line[1:])
            elif current and line.startswith("-") and not line.startswith("---"):
                per_file[current][1].append(line[1:])
    _, untracked = git(root, "ls-files", "--others", "--exclude-standard")
    tracked_new = [] if has_head else git(root, "ls-files")[1].splitlines()
    for rel in untracked.splitlines() + tracked_new:
        if rules_for(rel):
            try:
                with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as f:
                    per_file[rel] = (f.read().splitlines(), [])
            except OSError:
                pass
    out = []
    for path, (plus, minus) in per_file.items():
        rules = rules_for(path)
        if not rules:
            continue
        removed = {n.lower() for n in names(minus, rules)}
        for name, kind in names(plus, rules).items():
            if name.lower() not in removed:  # removed + re-added under the same name = version bump
                out.append((name, kind, path))
    return out


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    if payload.get("stop_hook_active") or os.environ.get("E4_ADR_NUDGE", "").lower() == "off":
        return
    cwd = payload.get("cwd") or ""
    if not os.path.isdir(cwd):
        cwd = os.getcwd()
    code, top = git(cwd, "rev-parse", "--show-toplevel")
    root = top.strip()
    if code != 0 or not os.path.isdir(os.path.join(root, ".ai-memory")):
        return
    _, touched = git(root, "status", "--porcelain", "--", ".ai-memory/decisions.md")
    if touched.strip():
        return  # an ADR is already being written

    deps = added_dependencies(root)
    key = hashlib.sha1(f"{payload.get('session_id', '')}|{root}".encode()).hexdigest()[:16]
    state = os.path.join(tempfile.gettempdir(), f".claude_adr_nudge_{key}")
    try:
        with open(state, encoding="utf-8") as f:
            seen = set(json.load(f))
    except (OSError, ValueError):
        seen = set()
    fresh = [(n, k, p) for n, k, p in deps if f"{p}|{n}" not in seen]
    if not fresh:
        return
    try:
        with open(state, "w", encoding="utf-8") as f:
            json.dump(sorted(seen | {f"{p}|{n}" for n, _, p in fresh}), f)
    except OSError:
        pass
    listed = [f"{k} `{n}` ({p})" for n, k, p in fresh[:MAX_LISTED]]
    if len(fresh) > MAX_LISTED:
        listed.append(f"{len(fresh) - MAX_LISTED} more")
    what = "a new dependency: " + listed[0] if len(fresh) == 1 else "new dependencies: " + "; ".join(listed)
    print(json.dumps({"decision": "block", "reason": REASON.format(what=what)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # fail-open: a broken hook must never block Claude
        pass
    sys.exit(0)
