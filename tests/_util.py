"""Shared test helpers: repo paths and running the stdlib-only automation scripts as subprocesses."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYDIR = ROOT / "automation" / "python"
SKILLS = ROOT / "agents-config" / ".agents" / "skills"

if str(PYDIR) not in sys.path:
    sys.path.insert(0, str(PYDIR))


def run_script(name: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run automation/python/<name> with the current interpreter and capture text output."""
    return subprocess.run([sys.executable, str(PYDIR / name), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
