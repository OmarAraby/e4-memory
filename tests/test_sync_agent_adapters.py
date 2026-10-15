"""Generator tests: the Claude /e4:* commands must be an exact rendering of the shared skills."""
from __future__ import annotations
import unittest

from _util import ROOT, run_script
import sync_agent_adapters as sync


class SyncAgentAdaptersTest(unittest.TestCase):
    def test_check_committedCommandsMatchSkills(self):
        r = run_script("sync_agent_adapters.py", "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_applyRegions_blockReplacedAndMarkersConsumed(self):
        body = "a\n<!-- adapter:x -->\ndefault\n<!-- /adapter:x -->\nb\n"
        self.assertEqual(sync.apply_regions(body, {"x": "claude"}), "a\nclaude\nb\n")

    def test_applyRegions_undefinedRegionKeepsDefault(self):
        body = "say <!-- adapter:y -->hello<!-- /adapter:y -->!"
        self.assertEqual(sync.apply_regions(body, {}), "say hello!")

    def test_applyRegions_emptyBlockRemovesLines(self):
        body = "a\n<!-- adapter:x -->\ndefault\n<!-- /adapter:x -->\nb\n"
        self.assertEqual(sync.apply_regions(body, {"x": ""}), "a\nb\n")

    def test_render_slashNamesMappedButPathsUntouched(self):
        skill = "---\nname: e4-init\n---\n# e4-init — t\nrun `/e4-end-session`; copy skills/e4-init/ and .agents/skills/e4-resume/\n"
        overlay = "---\ndescription: x\n---\n"
        out = sync.render_command("init", skill, overlay)
        self.assertIn("# /e4:init — t", out)
        self.assertIn("`/e4:end-session`", out)
        self.assertIn("skills/e4-init/", out)
        self.assertIn(".agents/skills/e4-resume/", out)

    def test_render_frontmatterFromOverlayWithGeneratedNotice(self):
        out = sync.render_command("resume", "---\nname: e4-resume\n---\nbody\n",
                                  "---\ndescription: \"[e4] d\"\n---\n")
        self.assertTrue(out.startswith("---\ndescription: \"[e4] d\"\n# GENERATED"))
        self.assertNotIn("name: e4-resume", out)

    def test_render_unclosedMarker_raises(self):
        skill = "---\nname: e4-new-task\n---\nstamp: <!-- adapter:stamp -->run date\n"
        with self.assertRaisesRegex(ValueError, "unbalanced"):
            sync.render_command("new-task", skill, "---\ndescription: x\n---\n")

    def test_render_overlayRegionTypo_raises(self):
        skill = "---\nname: e4-new-task\n---\nstamp: <!-- adapter:stamp -->run date<!-- /adapter:stamp -->\n"
        overlay = "---\ndescription: x\n---\n<!-- region:stamq -->\n!`date`\n<!-- /region:stamq -->\n"
        with self.assertRaisesRegex(ValueError, "stamq"):
            sync.render_command("new-task", skill, overlay)

    def test_generatedCommands_keepClaudeOnlyFeatures(self):
        cmds = ROOT / "claude-config" / ".claude" / "commands" / "e4"
        end = (cmds / "end-session.md").read_text(encoding="utf-8")
        self.assertIn('!`git status --short 2>/dev/null`', end)
        self.assertIn('"$ARGUMENTS"', end)
        init = (cmds / "init.md").read_text(encoding="utf-8")
        self.assertIn("session_start.sh", init)
        self.assertIn("@AGENTS.md", init)
        for f in cmds.glob("*.md"):
            self.assertNotIn("<!-- adapter:", f.read_text(encoding="utf-8"), f.name)


if __name__ == "__main__":
    unittest.main()
