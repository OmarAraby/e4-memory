"""Static checks on the portable core and the thin agent adapters (no agent runtime needed)."""
from __future__ import annotations
import re
import unittest

from _util import ROOT, SKILLS, run_script

TEMPLATE = ROOT / "project-template"


class PortableContractTest(unittest.TestCase):
    def test_skills_conformToAgentSkillsSpec(self):
        r = run_script("validate_memory.py", "--skills-dir", str(SKILLS), "--strict")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_skills_coverEveryClaudeCommand(self):
        cmds = {p.stem for p in (ROOT / "claude-config/.claude/commands/e4").glob("*.md")} - {"CONTRIBUTORS"}
        skills = {p.name.removeprefix("e4-") for p in SKILLS.iterdir()}
        self.assertEqual(cmds, skills)

    def test_neutralFiles_haveNoClaudeOnlyMechanics(self):
        files = [TEMPLATE / "AGENTS.md", *SKILLS.glob("*/SKILL.md")]
        for f in files:
            text = f.read_text(encoding="utf-8")
            # Claude-only: the /e4: namespace, !`cmd` injection, $ARGUMENTS, .claude/ paths.
            # (Adapter regions may hold neutral defaults; Claude text lives in claude-config/overlays/.)
            # (`~/.claude/ai-memory/` is only a legacy initializer search path, so it is allowed.)
            for needle in ("/e4:", "!`", "$ARGUMENTS", ".claude/commands", ".claude/hooks",
                           ".claude/settings"):
                self.assertFalse(needle in text, f"{f.parent.name}/{f.name} contains {needle!r}")

    def test_claudeTemplate_importsAgentsAndStaysThin(self):
        text = (TEMPLATE / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^@AGENTS\.md$")
        self.assertLess(len(text.splitlines()), 60, "CLAUDE.md should only hold Claude specifics")

    def test_claudeTemplate_hasSubdirectoryFallback(self):
        text = (TEMPLATE / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("read `AGENTS.md` at the repository root", text)

    def test_initSkill_gitattributesHasNoInlineComments(self):
        # git rejects trailing comments: `x merge=union  # c` sets attributes "#", "c", ...
        text = (SKILLS / "e4-init" / "SKILL.md").read_text(encoding="utf-8")
        block = text.split("Ensure `./.gitattributes`", 1)[1].split("```", 2)[1]
        for line in block.splitlines():
            if not line.lstrip().startswith("#"):
                self.assertNotIn("#", line, line)

    def test_initSkill_copiesEachMissingSkillFolder(self):
        text = (SKILLS / "e4-init" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("only if that folder does not exist there yet", text)

    def test_claudeInit_addsImportByLineNotHeading(self):
        text = (ROOT / "claude-config/.claude/commands/e4/init.md").read_text(encoding="utf-8")
        self.assertIn("Decide by the **import line**, not by the heading", text)
        self.assertIn("add the line `@AGENTS.md` at the end of that section", text)

    def test_copilotPointer_referencesAgentsMd(self):
        text = (ROOT / "copilot-config/.github/copilot-instructions.md").read_text(encoding="utf-8")
        self.assertIn("](../AGENTS.md)", text)

    def test_agentsMd_readOrderMatchesSkill(self):
        def order(text):
            return re.findall(r"\.ai-memory/(onboarding|context|architecture|active-tasks|progress)\.md", text)[:5]
        agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8").split("## 1.", 1)[1]
        resume = (SKILLS / "e4-resume" / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(order(agents), order(resume))


if __name__ == "__main__":
    unittest.main()
