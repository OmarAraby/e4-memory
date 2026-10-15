"""Regression tests for the Claude Code hooks against a freshly scaffolded project (needs bash)."""
from __future__ import annotations
import os
import re
import shutil
import subprocess
import sys
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

    def test_sessionStart_onlyAiVaultSet_findsGeneratorViaVault(self):
        active = self.proj / ".ai-memory" / "active-tasks.md"
        active.unlink()
        env = {k: v for k, v in os.environ.items() if k != "AI_MEMORY_PYDIR"}
        env.update(AI_VAULT=str(ROOT), HOME=str(self.proj))  # ~/AI-Vault must not exist
        r = subprocess.run([BASH, str(HOOKS / "session_start.sh")], cwd=self.proj, input="{}", env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(active.is_file(), "generate_status.py was not found through $AI_VAULT")

    def test_injectedScriptsDir_resolvesEnvInOrder(self):
        # The exact `!` command Claude Code runs; it must always exit 0 (a failing `!` command
        # aborts the whole slash command silently), so the fallback lives inside Python.
        cmd = (ROOT / "claude-config/.claude/commands/e4/resume.md").read_text(encoding="utf-8")
        code = re.search(r'!`python3 -c "([^"]*AI_MEMORY_PYDIR[^"]*)"`', cmd).group(1)
        base = {k: v for k, v in os.environ.items()
                if k not in ("AI_MEMORY_PYDIR", "AI_VAULT", "HOME", "USERPROFILE")}
        home = str(Path.home())
        cases = [({"AI_MEMORY_PYDIR": "/p", "AI_VAULT": "/v"}, "/p"),
                 ({"AI_VAULT": "/v w"}, os.path.join("/v w", "automation", "python")),
                 ({"HOME": home, "USERPROFILE": home},
                  os.path.join(os.path.expanduser("~/AI-Vault"), "automation", "python"))]
        for extra, expected in cases:
            r = subprocess.run([sys.executable, "-c", code], env={**base, **extra},
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), expected, extra)

    def test_injectedCommands_exitZeroInEveryRepoState(self):
        # Claude Code silently drops a whole slash command when one `!` command exits non-zero
        # (verified headless: `git log` in a repo with no commits emptied /e4:end-session).
        cmds = ROOT / "claude-config/.claude/commands/e4"
        injected = [(f.name, c) for f in sorted(cmds.glob("*.md"))
                    for c in re.findall(r"(?<=\s)!`([^`]+)`", f.read_text(encoding="utf-8"))]
        self.assertGreater(len(injected), 5)
        with tempfile.TemporaryDirectory() as tmp:
            no_git, fresh, committed = (Path(tmp) / n for n in ("no-git", "fresh", "committed"))
            for d in (no_git, fresh, committed):
                d.mkdir()
            env = {**os.environ, "GIT_CEILING_DIRECTORIES": tmp,
                   "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
            for d in (fresh, committed):
                subprocess.run(["git", "init", "-q"], cwd=d, env=env, check=True)
            (committed / "a.txt").write_text("a", encoding="utf-8")
            subprocess.run(["git", "add", "a.txt"], cwd=committed, env=env, check=True)
            subprocess.run(["git", "commit", "-qm", "a"], cwd=committed, env=env, check=True)
            for d in (no_git, fresh, committed):
                for name, command in injected:
                    r = subprocess.run([BASH, "-c", command], cwd=d, env=env,
                                       capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, f"{name} in {d.name}: {command}")

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
