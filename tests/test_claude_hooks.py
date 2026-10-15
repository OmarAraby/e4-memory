"""Regression tests for the Claude Code hooks against a freshly scaffolded project (needs bash)."""
from __future__ import annotations
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _util import PYDIR, ROOT, run_script

HOOKS = ROOT / "claude-config" / ".claude" / "hooks"
BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "bash not on PATH")
class ClaudeHooksTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.proj = Path(self._tmp.name)
        r = run_script("init_project_memory.py", str(self.proj), "--with-agents-md", "--with-skills")
        self.assertEqual(r.returncode, 0, r.stderr)

    def tearDown(self):
        self._tmp.cleanup()

    def hook(self, name: str, stdin: str = "{}") -> subprocess.CompletedProcess:
        env = {**__import__("os").environ, "AI_MEMORY_PYDIR": str(PYDIR)}
        return subprocess.run([BASH, str(HOOKS / name)], cwd=self.proj, input=stdin, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_sessionStart_withMemory_injectsSummary(self):
        r = self.hook("session_start.sh", '{"source":"startup"}')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Project Memory (auto-loaded)", r.stdout)
        self.assertIn("### Last session", r.stdout)
        self.assertIn("-000000-init.md", r.stdout)
        self.assertTrue((self.proj / ".ai-memory" / "active-tasks.md").is_file())

    def test_sessionStart_withoutMemory_suggestsInit(self):
        with tempfile.TemporaryDirectory() as empty:
            r = subprocess.run([BASH, str(HOOKS / "session_start.sh")], cwd=empty, input="{}",
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertIn("/e4:init", r.stdout)

    def test_stopReminder_cleanTree_staysSilent(self):
        r = self.hook("stop_reminder.sh")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
