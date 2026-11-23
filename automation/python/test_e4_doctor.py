#!/usr/bin/env python3
"""Tests for e4_doctor.py. Stdlib only; builds a throwaway repo, ~/.claude and project per test.

Run: python automation/python/test_e4_doctor.py
"""
from __future__ import annotations
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import e4_doctor  # noqa: E402

V1, V2, V3, LOCAL = (f"#!/usr/bin/env bash\necho {v}\n".encode() for v in ("v1", "v2", "v3", "local"))


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                    "-c", "core.autocrlf=false", *args], check=True, capture_output=True)


class DoctorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo, self.home, self.project = root / "repo", root / "home" / ".claude", root / "project"
        self.src = self.repo / "claude-config" / ".claude" / "hooks" / "a.sh"
        self.src.parent.mkdir(parents=True)
        git(root, "init", "-q", "-b", "main", str(self.repo))
        for content, msg in ((V1, "v1"), (V2, "v2")):
            self.src.write_bytes(content)
            git(self.repo, "add", "-A")
            git(self.repo, "commit", "-q", "-m", msg)
        git(self.repo, "switch", "-q", "-c", "side")
        self.src.write_bytes(V3)
        git(self.repo, "commit", "-q", "-am", "v3")
        git(self.repo, "switch", "-q", "main")  # HEAD = v2; v3 only on `side`

        self.installed = self.home / "hooks" / "a.sh"
        self.installed.parent.mkdir(parents=True)
        self.installed.write_bytes(V2)
        self.write_settings(self.home / "settings.json",
                            {"Stop": [{"hooks": [{"type": "command",
                                                  "command": 'bash "$HOME/.claude/hooks/a.sh"'}]}]})
        self.project.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write_settings(self, path: Path, hooks: dict, **extra) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"hooks": hooks, **extra}), encoding="utf-8")

    def doctor(self, *flags: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = e4_doctor.main(["--repo", str(self.repo), "--claude-home", str(self.home),
                                   "--project", str(self.project), *flags])
        return code, out.getvalue()

    def lines(self, output: str, check: str) -> list[str]:
        return [ln for ln in output.splitlines() if f"  {check}" in ln]

    def test_healthy_install_passes(self):
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        for check in ("settings", "hook wiring", "hook drift", "line endings"):
            self.assertTrue(self.lines(out, check)[0].startswith("PASS"), out)

    def test_invalid_settings_json_fails(self):
        (self.home / "settings.json").write_text("{ not json", encoding="utf-8")
        code, out = self.doctor()
        self.assertEqual(code, 1)
        self.assertIn("ignores this whole file", out)

    def test_duplicate_registration_warns(self):
        self.write_settings(self.project / ".claude" / "settings.json",
                            {"Stop": [{"hooks": [{"type": "command", "command": "bash ~/.claude/hooks/a.sh"}]}]})
        _, out = self.doctor()
        self.assertIn("a.sh runs 2x on Stop (user, project)", out)

    def test_missing_registered_script_fails(self):
        self.write_settings(self.project / ".claude" / "settings.json",
                            {"SessionStart": [{"hooks": [{"type": "command",
                                                          "command": "bash .claude/hooks/gone.sh"}]}]})
        code, out = self.doctor()
        self.assertEqual(code, 1)
        self.assertIn("registered script not found: SessionStart", out)

    def test_outdated_hook_is_fixed_with_backup(self):
        self.installed.write_bytes(V1)
        _, out = self.doctor()
        self.assertIn("is outdated (older version from", out)
        _, out = self.doctor("--fix")
        self.assertIn("FIXED", self.lines(out, "hook drift")[0])
        self.assertEqual(self.installed.read_bytes(), V2)
        backups = list(self.home.glob("hooks/backup-*/**/a.sh"))
        self.assertEqual([b.read_bytes() for b in backups], [V1])

    def test_hook_from_unmerged_branch_is_not_fixed_without_force(self):
        self.installed.write_bytes(V3)
        _, out = self.doctor("--fix")
        self.assertIn("on unmerged branch side", out)
        self.assertEqual(self.installed.read_bytes(), V3)
        _, out = self.doctor("--force")
        self.assertIn("FIXED", self.lines(out, "hook drift")[0])
        self.assertEqual(self.installed.read_bytes(), V2)

    def test_locally_modified_hook_is_not_fixed(self):
        self.installed.write_bytes(LOCAL)
        _, out = self.doctor("--fix")
        self.assertIn("locally modified", out)
        self.assertEqual(self.installed.read_bytes(), LOCAL)

    def test_crlf_hook_fails_and_fix_converts_without_reporting_drift(self):
        self.installed.write_bytes(V2.replace(b"\n", b"\r\n"))
        code, out = self.doctor()
        self.assertEqual(code, 1)
        self.assertIn("has CRLF endings", out)
        self.assertTrue(self.lines(out, "hook drift")[0].startswith("PASS"), out)
        code, out = self.doctor("--fix")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.installed.read_bytes(), V2)

    def test_lsp_binary_missing_fails_and_present_passes(self):
        market = self.home / "plugins" / "marketplaces" / "mk"
        (market / ".claude-plugin").mkdir(parents=True)
        (market / ".claude-plugin" / "marketplace.json").write_text(json.dumps({"plugins": [
            {"name": "fake-lsp", "lspServers": {"fake": {"command": "e4doctorfakels"}}}]}), encoding="utf-8")
        install = self.home / "plugins" / "cache" / "mk" / "fake-lsp" / "1.0.0"
        install.mkdir(parents=True)
        (self.home / "plugins" / "installed_plugins.json").write_text(json.dumps(
            {"plugins": {"fake-lsp@mk": [{"installPath": str(install)}]}}), encoding="utf-8")
        data = json.loads((self.home / "settings.json").read_text(encoding="utf-8"))
        data["enabledPlugins"] = {"fake-lsp@mk": True}
        (self.home / "settings.json").write_text(json.dumps(data), encoding="utf-8")

        code, out = self.doctor()
        self.assertEqual(code, 1)
        self.assertIn("needs `e4doctorfakels` on PATH", out)

        bindir = Path(self.tmp.name) / "bin"
        bindir.mkdir()
        for name in ("e4doctorfakels", "e4doctorfakels.bat"):
            (bindir / name).write_text("exit 0\n")
            os.chmod(bindir / name, 0o755)
        old_path = os.environ["PATH"]
        os.environ["PATH"] = str(bindir) + os.pathsep + old_path
        try:
            _, out = self.doctor()
        finally:
            os.environ["PATH"] = old_path
        self.assertTrue(self.lines(out, "lsp")[0].startswith("PASS"), out)

    def test_project_wiring_e4_without_memory_warns(self):
        hooks_dir = self.project / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True)
        (hooks_dir / "session_start.sh").write_bytes(V2)
        self.write_settings(self.project / ".claude" / "settings.json",
                            {"SessionStart": [{"hooks": [{"type": "command",
                                                          "command": "bash .claude/hooks/session_start.sh"}]}]})
        _, out = self.doctor()
        self.assertIn("has no .ai-memory/", out)

    def test_is_wsl_bash(self):
        self.assertTrue(e4_doctor.is_wsl_bash(r"C:\Windows\System32\bash.exe"))
        self.assertFalse(e4_doctor.is_wsl_bash(r"C:\Program Files\Git\usr\bin\bash.exe"))
        self.assertFalse(e4_doctor.is_wsl_bash(None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
