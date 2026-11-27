#!/usr/bin/env python3
"""Tests for the adr_nudge.py Stop hook. Stdlib only; each test builds a throwaway e4 project.

Run: python automation/python/test_adr_nudge.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "claude-config" / ".claude" / "hooks" / "adr_nudge.py"

PACKAGE_JSON = '{\n  "name": "app",\n  "version": "1.0.0",\n  "dependencies": {\n    "express": "^4.18.0"\n  }\n}\n'
CSPROJ = ('<Project Sdk="Microsoft.NET.Sdk">\n  <ItemGroup>\n'
          '    <PackageReference Include="Serilog" Version="3.0.0" />\n  </ItemGroup>\n</Project>\n')
GO_MOD = "module example.com/app\n\ngo 1.22\n\nrequire (\n\tgithub.com/jackc/pgx/v5 v5.5.0\n)\n"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                    "-c", "core.autocrlf=false", *args], check=True, capture_output=True)


class AdrNudgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        git(Path(self.tmp.name), "init", "-q", "-b", "main", str(self.repo))
        self.write(".ai-memory/decisions.md", "# Decisions\n")
        self.write("package.json", PACKAGE_JSON)
        self.write("src/Api/Api.csproj", CSPROJ)
        self.write("go.mod", GO_MOD)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        self.session = uuid.uuid4().hex

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel: str, text: str) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_hook(self, payload: dict | str | None = None, env: dict | None = None) -> str:
        if payload is None:
            payload = {"session_id": self.session, "cwd": str(self.repo)}
        proc = subprocess.run([sys.executable, "-B", str(HOOK)],
                              input=payload if isinstance(payload, str) else json.dumps(payload),
                              capture_output=True, text=True, cwd=self.repo, timeout=60,
                              env=dict(os.environ, **(env or {})))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    def reason(self) -> str:
        out = self.run_hook()
        return json.loads(out)["reason"] if out else ""

    def test_new_npm_package_nudges(self):
        self.write("package.json", PACKAGE_JSON.replace('"express": "^4.18.0"',
                                                        '"express": "^4.18.0",\n    "redis": "^4.6.0"'))
        r = self.reason()
        self.assertIn("package `redis` (package.json)", r)
        self.assertNotIn("express", r)
        self.assertIn("Do NOT write the ADR unless they agree", r)

    def test_version_bump_is_silent(self):
        self.write("package.json", PACKAGE_JSON.replace("^4.18.0", "^4.19.2"))
        self.write("src/Api/Api.csproj", CSPROJ.replace("3.0.0", "3.1.1"))
        self.write("go.mod", GO_MOD.replace("v5.5.0", "v5.6.0"))
        self.assertEqual(self.run_hook(), "")

    def test_csproj_package_and_project_reference(self):
        self.write("src/Api/Api.csproj", CSPROJ.replace(
            "  </ItemGroup>",
            '    <PackageReference Include="MediatR" Version="12.0.0" />\n'
            '    <ProjectReference Include="..\\Domain\\Domain.csproj" />\n  </ItemGroup>'))
        r = self.reason()
        self.assertIn("package `MediatR` (src/Api/Api.csproj)", r)
        self.assertIn("project reference `..\\Domain\\Domain.csproj`", r)

    def test_go_indirect_is_ignored_direct_is_not(self):
        self.write("go.mod", GO_MOD.replace(")\n", "\tgolang.org/x/text v0.14.0 // indirect\n"
                                                   "\tgithub.com/go-chi/chi/v5 v5.0.12\n)\n"))
        r = self.reason()
        self.assertIn("module `github.com/go-chi/chi/v5`", r)
        self.assertNotIn("golang.org/x/text", r)

    def test_new_untracked_manifest_and_compose_image(self):
        self.write("requirements.txt", "# deps\nrequests==2.31.0\nfastapi>=0.110\n-r base.txt\n")
        self.write("docker-compose.yml", "services:\n  cache:\n    image: redis:7-alpine\n")
        r = self.reason()
        for expected in ("package `requests`", "package `fastapi`", "service image `redis`"):
            self.assertIn(expected, r)
        self.assertNotIn("base.txt", r)

    def test_decisions_md_changed_is_silent(self):
        self.write("package.json", PACKAGE_JSON.replace('"express": "^4.18.0"',
                                                        '"express": "^4.18.0",\n    "redis": "^4.6.0"'))
        self.write(".ai-memory/decisions.md", "# Decisions\n\n## ADR-1: Use Redis\n")
        self.assertEqual(self.run_hook(), "")

    def test_each_dependency_nudges_once_per_session(self):
        self.write("package.json", PACKAGE_JSON.replace('"express": "^4.18.0"',
                                                        '"express": "^4.18.0",\n    "redis": "^4.6.0"'))
        self.assertIn("redis", self.reason())
        self.assertEqual(self.run_hook(), "")
        self.write("requirements.txt", "httpx==0.27.0\n")
        r = self.reason()
        self.assertIn("httpx", r)
        self.assertNotIn("redis", r)

    def test_silent_cases(self):
        self.write("package.json", PACKAGE_JSON.replace('"express": "^4.18.0"',
                                                        '"express": "^4.18.0",\n    "redis": "^4.6.0"'))
        self.assertEqual(self.run_hook({"session_id": self.session, "cwd": str(self.repo),
                                        "stop_hook_active": True}), "")
        self.assertEqual(self.run_hook(env={"E4_ADR_NUDGE": "off"}), "")
        self.assertEqual(self.run_hook("not json"), "")
        git(self.repo, "rm", "-q", "-r", "--cached", ".ai-memory")
        (self.repo / ".ai-memory" / "decisions.md").unlink()
        (self.repo / ".ai-memory").rmdir()
        self.assertEqual(self.run_hook(), "")

    def test_config_keys_are_not_packages(self):
        self.write("pyproject.toml", '[project]\nname = "app"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n'
                                     '[build-system]\nbuild-backend = "setuptools.build_meta"\n')
        self.write("Cargo.toml", '[package]\nname = "app"\nedition = "2021"\nrust-version = "1.70"\n'
                                 '[dependencies]\nserde = { version = "1" }\n')
        r = self.reason()
        self.assertIn("crate `serde`", r)
        for word in ("`name`", "`version`", "build-backend", "rust-version", "`edition`"):
            self.assertNotIn(word, r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
