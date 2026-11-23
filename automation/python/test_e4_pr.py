#!/usr/bin/env python3
"""Tests for e4_pr.py and its `pr` entry in the e4.py launcher. Stdlib only; each test builds a
throwaway repo with a main branch and a feature branch.

Run: python automation/python/test_e4_pr.py
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "e4_pr.py"
LAUNCHER = HERE.parent.parent / "claude-config" / ".claude" / "hooks" / "e4.py"
TASK_ID = "TASK-20261124-101500-add-login"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                    "-c", "core.autocrlf=false", *args], check=True, capture_output=True)


def write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PrFactsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        git(Path(self.tmp.name), "init", "-q", "-b", "main", str(self.repo))
        write(self.repo, "app.py", "print('v1')\n")
        write(self.repo, ".ai-memory/decisions.md", "# Decisions\n")
        write(self.repo, f".ai-memory/tasks/{TASK_ID}.md",
              f'---\nid: {TASK_ID}\ntitle: "Add login"\nstatus: in-progress\n---\n# Add login\n'
              "## Goal\nLet users sign in.\n## Acceptance Criteria\n- [ ] POST /login returns a JWT\n"
              "- [ ] Bad password returns 401\n## Checkpoints\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        git(self.repo, "switch", "-q", "-c", "feature/login")
        write(self.repo, "app.py", "print('v1')\ndef login():\n    return 'jwt'\n")
        write(self.repo, "tests/test_login.py", "def test_login():\n    assert True\n")
        write(self.repo, "package-lock.json", "{}\n" * 300)
        write(self.repo, ".ai-memory/decisions.md", "# Decisions\n\n## ADR-1: Use JWT for login\nBecause.\n")
        write(self.repo, ".ai-memory/sessions/2026-11-24-101500-feature-login.md",
              "## Session\n**TL;DR**: Login endpoint works end to end.\n\n"
              "**Decisions**: JWT over cookies.\n```\ntest_status: pass\n```\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", f"feat(auth): add login endpoint ({TASK_ID})",
            "-m", "Issues a JWT.\n\nCo-Authored-By: Bot <bot@example.invalid>")

    def tearDown(self):
        self.tmp.cleanup()

    def facts(self, *args: str, cwd: Path | None = None) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, "-B", str(SCRIPT), "facts", "--project", str(cwd or self.repo),
                               *args], capture_output=True, timeout=120,
                              env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        return proc.returncode, proc.stdout.decode("utf-8", "replace")

    def test_full_facts_sheet(self):
        code, out = self.facts()
        self.assertEqual(code, 0, out)
        self.assertIn("Mode: draft", out)
        self.assertIn("Base: main", out)  # no remote: falls back to the local base branch
        self.assertIn("feat(auth): add login endpoint", out)
        self.assertIn("Issues a JWT.", out)
        self.assertNotIn("Co-Authored-By", out)
        self.assertIn("Within the ~400-line guideline.", out)
        self.assertIn("300 generated lines not counted", out)
        self.assertIn("package-lock.json (+300/-0) [generated]", out)
        self.assertIn("[tests] tests/test_login.py", out)
        self.assertIn("Tests changed: yes", out)
        self.assertIn("- ADR-1: Use JWT for login", out)
        self.assertIn(f"- {TASK_ID} — Add login (status: in-progress)", out)
        self.assertIn("POST /login returns a JWT", out)
        self.assertIn("TL;DR: Login endpoint works end to end.", out)
        self.assertIn("test_status: pass", out)
        self.assertIn("None marked in commits.", out)

    def test_create_keyword_sets_mode_and_strips_it_from_the_note(self):
        _, out = self.facts("--note", "create mention the 401 case")
        self.assertIn("Mode: create", out)
        self.assertIn("User note: mention the 401 case", out)
        _, out = self.facts("--note", "created a login endpoint")
        self.assertIn("Mode: draft", out)

    def test_over_guideline_and_breaking_change(self):
        write(self.repo, "big.py", "x = 1\n" * 450)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "feat(api)!: drop the v1 endpoints")
        _, out = self.facts()
        self.assertIn("OVER the ~400-line PR guideline", out)
        self.assertIn("feat(api)!: drop the v1 endpoints", out.split("## Breaking changes")[1])

    def test_uncommitted_changes_warn(self):
        write(self.repo, "app.py", "changed\n")
        _, out = self.facts()
        self.assertIn("uncommitted changes exist", out)

    def test_errors(self):
        git(self.repo, "switch", "-q", "main")
        code, out = self.facts()
        self.assertEqual(code, 1)
        self.assertIn("you are on the base branch", out)
        git(self.repo, "switch", "-q", "-c", "empty")
        _, out = self.facts()
        self.assertIn("has no commits that aren't already in main", out)
        nogit = Path(self.tmp.name) / "plain"
        nogit.mkdir()
        _, out = self.facts(cwd=nogit)
        self.assertIn("is not a git repository", out)
        _, out = self.facts("--base", "nope")
        self.assertIn("base branch nope not found", out)

    def test_repo_without_memory_omits_memory_sections(self):
        git(self.repo, "rm", "-q", "-r", ".ai-memory")
        git(self.repo, "commit", "-q", "-m", "chore: drop memory")
        _, out = self.facts()
        self.assertIn("No .ai-memory/ in this repo", out)
        self.assertNotIn("## Tasks", out)

    def test_launcher_passes_stdin_note_and_always_exits_zero(self):
        env = dict(os.environ, AI_MEMORY_PYDIR=str(HERE), PYTHONIOENCODING="utf-8")
        proc = subprocess.run([sys.executable, "-B", str(LAUNCHER), "pr", "facts", "--note", "-"],
                              input="create $(echo pwned) `id`".encode(), cwd=self.repo, env=env,
                              capture_output=True, timeout=120)
        out = proc.stdout.decode("utf-8", "replace")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Mode: create", out)
        self.assertIn("User note: $(echo pwned) `id`", out)  # passed literally, never executed


if __name__ == "__main__":
    unittest.main(verbosity=2)
