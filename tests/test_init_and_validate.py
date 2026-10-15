"""Initializer + validator tests: scaffolding stays backward compatible and validates clean."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from _util import ROOT, SKILLS, run_script


class InitProjectMemoryTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.proj = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def init(self, *flags: str):
        r = run_script("init_project_memory.py", str(self.proj), "--name", "Demo", *flags)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def test_init_defaultFlags_noAgentFilesCreated(self):
        self.init()
        self.assertTrue((self.proj / ".ai-memory" / "onboarding.md").is_file())
        self.assertFalse((self.proj / "AGENTS.md").exists())
        self.assertFalse((self.proj / ".agents").exists())

    def test_init_claudeMdOnly_keepsLegacyStub(self):
        self.init("--with-claude-md")
        text = (self.proj / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("Replace this stub", text)
        self.assertNotIn("@AGENTS.md", text)

    def test_init_agentsAndClaude_claudeImportsAgents(self):
        self.init("--with-agents-md", "--with-claude-md", "--with-skills")
        self.assertEqual((self.proj / "AGENTS.md").read_text(encoding="utf-8"),
                         (ROOT / "project-template" / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertRegex((self.proj / "CLAUDE.md").read_text(encoding="utf-8"), r"(?m)^@AGENTS\.md$")
        for skill in SKILLS.iterdir():
            self.assertTrue((self.proj / ".agents" / "skills" / skill.name / "SKILL.md").is_file())

    def test_init_rerun_neverOverwritesUserEdits(self):
        self.init("--with-agents-md", "--with-skills")
        agents = self.proj / "AGENTS.md"
        skill = self.proj / ".agents" / "skills" / "e4-resume" / "SKILL.md"
        agents.write_text("mine", encoding="utf-8")
        skill.write_text("mine", encoding="utf-8")
        self.init("--with-agents-md", "--with-skills")
        self.assertEqual(agents.read_text(encoding="utf-8"), "mine")
        self.assertEqual(skill.read_text(encoding="utf-8"), "mine")

    def test_validate_freshFullInstall_passesStrict(self):
        self.init("--with-agents-md", "--with-claude-md", "--with-skills")
        r = run_script("validate_memory.py", "--project", str(self.proj), "--agents", "--strict")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_validate_badSessionNameAndStatus_fails(self):
        self.init()
        mem = self.proj / ".ai-memory"
        (mem / "sessions" / "notes.md").write_text("x", encoding="utf-8")
        (mem / "tasks" / "TASK-20260101-000000-x.md").write_text(
            "---\nstatus: doing   # todo | done\n---\n", encoding="utf-8")
        r = run_script("validate_memory.py", "--project", str(self.proj))
        self.assertEqual(r.returncode, 1)
        self.assertIn("sessions/notes.md", r.stdout)
        self.assertIn("unknown status 'doing'", r.stdout)

    def test_validate_statusWithTrailingComment_accepted(self):
        self.init()
        (self.proj / ".ai-memory" / "tasks" / "TASK-20260101-000000-x.md").write_text(
            "---\nstatus: in-review   # todo | in-progress | done\n---\n", encoding="utf-8")
        r = run_script("validate_memory.py", "--project", str(self.proj))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_validate_bomPrefixedFiles_accepted(self):
        self.init()
        mem = self.proj / ".ai-memory"
        (mem / "tasks" / "TASK-20260101-000000-bom.md").write_bytes(
            b"\xef\xbb\xbf---\r\nstatus: in-progress\r\n---\r\n")
        onboarding = mem / "onboarding.md"
        onboarding.write_bytes(b"\xef\xbb\xbf" + onboarding.read_bytes())
        r = run_script("validate_memory.py", "--project", str(self.proj), "--strict")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_validate_dotfileInSessions_ignored(self):
        self.init()
        (self.proj / ".ai-memory" / "sessions" / ".gitkeep").write_text("", encoding="utf-8")
        r = run_script("validate_memory.py", "--project", str(self.proj), "--strict")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_validate_completedAlias_warnsNotErrors(self):
        self.init()
        (self.proj / ".ai-memory" / "tasks" / "TASK-20260101-000000-x.md").write_text(
            "---\nstatus: completed\n---\n", encoding="utf-8")
        r = run_script("validate_memory.py", "--project", str(self.proj))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("use 'done'", r.stdout)

    def test_validate_claudeMdWithoutImport_warns(self):
        self.init("--with-agents-md", "--with-skills")
        (self.proj / "CLAUDE.md").write_text("# mine\n", encoding="utf-8")
        r = run_script("validate_memory.py", "--project", str(self.proj), "--agents")
        self.assertEqual(r.returncode, 0)
        self.assertIn("does not import @AGENTS.md", r.stdout)


if __name__ == "__main__":
    unittest.main()
