#!/usr/bin/env python3
"""
validate_memory.py — Check a project's e4 memory and agent wiring against the naming contracts.

Read-only: reports problems, never edits a file. Agent-neutral — it validates the portable core
(.ai-memory/) and, optionally, the thin agent entry points (AGENTS.md, CLAUDE.md, .agents/skills/).

Checks
  errors   : .ai-memory/ or a required memory file missing; a sessions/ file that breaks the
             YYYY-MM-DD-HHMMSS-<branch>.md contract; a task file with a missing/unknown status;
             (--agents) a SKILL.md whose name/description breaks the Agent Skills spec.
  warnings : missing front-matter, legacy session-log.md only, non-timestamp task IDs,
             (--agents) missing AGENTS.md or a CLAUDE.md that doesn't import it,
             (--check-links) [[wikilinks]] that resolve to no note in .ai-memory/.

Usage:
    python validate_memory.py --project .
    python validate_memory.py --project ~/code/myapp --agents --check-links
    python validate_memory.py --skills-dir agents-config/.agents/skills     # skills only
Exit code: 0 = no errors (warnings allowed unless --strict), 1 = errors, 2 = bad arguments.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

REQUIRED = ("onboarding.md", "context.md", "architecture.md", "decisions.md", "progress.md")
STATUSES = {"todo", "in-progress", "blocked", "in-review", "done"}
# Accepted as done by archive_completed_tasks.py, but generate_status.py files them under todo.
DONE_ALIASES = {"completed", "closed"}
SESSION_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}-[A-Za-z0-9._-]+\.md$")
TASK_NAME = re.compile(r"^TASK-\d{8}-\d{6}-[a-z0-9-]+\.md$")
SKILL_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WIKILINK = re.compile(r"\[\[([^\]|#]+)")
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.DOTALL)


class Report:
    """Collects findings; `ok` is False once any error is recorded."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def frontmatter_value(text: str, key: str) -> str | None:
    """Return a front-matter value with quotes and any trailing `# comment` removed."""
    fm = FRONTMATTER.match(text)
    if not fm:
        return None
    m = re.search(rf"^{re.escape(key)}\s*:\s*(.*?)\s*$", fm.group(1), re.MULTILINE)
    if not m:
        return None
    return re.sub(r"\s+#.*$", "", m.group(1)).strip().strip('"').strip("'")


def check_memory(mem: Path, rep: Report, check_links: bool) -> None:
    if not mem.is_dir():
        rep.error(f"{mem} not found - run init_project_memory.py or the e4-init skill")
        return
    for name in REQUIRED:
        f = mem / name
        if not f.is_file():
            rep.error(f"missing required file .ai-memory/{name}")
        elif not FRONTMATTER.match(f.read_text(encoding="utf-8-sig", errors="ignore")):
            rep.warn(f".ai-memory/{name} has no YAML front-matter")
    if not (mem / "active-tasks.md").exists():
        rep.warn(".ai-memory/active-tasks.md missing (generated - run generate_status.py)")

    sessions = mem / "sessions"
    if sessions.is_dir():
        for f in sorted(sessions.iterdir()):
            # Dotfiles (.gitkeep, .DS_Store) are placeholders, not sessions.
            if (f.is_file() and f.name != "README.md" and not f.name.startswith(".")
                    and not SESSION_NAME.match(f.name)):
                rep.error(f"sessions/{f.name} breaks the YYYY-MM-DD-HHMMSS-<branch>.md naming contract")
    elif (mem / "session-log.md").is_file():
        rep.warn("legacy session-log.md only (no sessions/) - new sessions should go to sessions/")
    else:
        rep.error("missing .ai-memory/sessions/")

    tasks = mem / "tasks"
    for f in sorted(tasks.glob("*.md")) if tasks.is_dir() else []:
        if f.name.upper() == "README.MD":
            continue
        if not TASK_NAME.match(f.name):
            rep.warn(f"tasks/{f.name}: not a timestamp ID (TASK-YYYYMMDD-HHMMSS-slug) - may collide across branches")
        status = frontmatter_value(f.read_text(encoding="utf-8-sig", errors="ignore"), "status")
        if status is None:
            rep.error(f"tasks/{f.name}: no `status:` in front-matter")
        elif status.lower() in DONE_ALIASES:
            rep.warn(f"tasks/{f.name}: status '{status}' is archived as done but shown under Next Up "
                     "by generate_status.py - use 'done'")
        elif status.lower() not in STATUSES:
            rep.error(f"tasks/{f.name}: unknown status '{status}' (expected one of {sorted(STATUSES)})")

    if check_links:
        stems = {p.stem.lower() for p in mem.rglob("*.md")}
        for f in sorted(mem.rglob("*.md")):
            for target in WIKILINK.findall(f.read_text(encoding="utf-8-sig", errors="ignore")):
                if Path(target.strip()).name.lower() not in stems:
                    rep.warn(f"{f.relative_to(mem)}: [[{target.strip()}]] resolves to no note in .ai-memory/ "
                             "(fine if it lives in the global vault)")


def check_skills(skills_dir: Path, rep: Report) -> None:
    """Validate SKILL.md files against the Agent Skills spec (name/description rules)."""
    found = sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.is_dir() else []
    if not found:
        rep.warn(f"no skills found in {skills_dir}")
    for f in found:
        text = f.read_text(encoding="utf-8-sig", errors="ignore")
        name = frontmatter_value(text, "name")
        desc = frontmatter_value(text, "description")
        where = f"{f.parent.name}/SKILL.md"
        if not name:
            rep.error(f"{where}: missing `name`")
        elif name != f.parent.name or not SKILL_NAME.match(name) or len(name) > 64:
            rep.error(f"{where}: name '{name}' must be lowercase-hyphenated, <=64 chars, and match its folder")
        if not desc:
            rep.error(f"{where}: missing `description`")
        elif len(desc) > 1024:
            rep.error(f"{where}: description is {len(desc)} chars (max 1024)")


def check_agents(root: Path, rep: Report) -> None:
    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    if not agents.is_file():
        rep.warn("AGENTS.md missing - Copilot/Cursor won't receive the e4 contract")
    elif claude.is_file():
        text = claude.read_text(encoding="utf-8-sig", errors="ignore")
        # Claude Code ignores AGENTS.md when a CLAUDE.md exists, unless CLAUDE.md imports it.
        if not re.search(r"^\s*@AGENTS\.md\s*$", text, re.MULTILINE):
            rep.warn("CLAUDE.md exists but does not import @AGENTS.md - Claude Code will not read AGENTS.md")
    check_skills(root / ".agents" / "skills", rep)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate e4 project memory and agent wiring")
    ap.add_argument("--project", help="Project root containing .ai-memory/")
    ap.add_argument("--agents", action="store_true", help="Also check AGENTS.md / CLAUDE.md / .agents/skills")
    ap.add_argument("--check-links", action="store_true", help="Warn on unresolved [[wikilinks]]")
    ap.add_argument("--skills-dir", help="Validate only the SKILL.md files under this directory")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = ap.parse_args()
    if not args.project and not args.skills_dir:
        ap.error("pass --project and/or --skills-dir")

    rep = Report()
    if args.skills_dir:
        check_skills(Path(args.skills_dir), rep)
    if args.project:
        root = Path(args.project).expanduser().resolve()
        check_memory(root / ".ai-memory", rep, args.check_links)
        if args.agents:
            check_agents(root, rep)

    for msg in rep.errors:
        print(f"ERROR {msg}")
    for msg in rep.warnings:
        print(f"WARN  {msg}")
    failed = bool(rep.errors) or (args.strict and bool(rep.warnings))
    print(f"{'FAIL' if failed else 'OK'}: {len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
