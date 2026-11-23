#!/usr/bin/env python3
"""
e4_doctor.py — Health check for an e4 install: tools, settings, hook wiring, hook drift,
line endings, LSP binaries and vault env vars. Read-only unless --fix is given.

--fix only repairs mechanical problems: it copies the repo version over drifted installed hooks
and converts CRLF hook scripts to LF, backing up every file it overwrites. Settings files are
never edited — duplicate or broken registrations need a human decision.

Usage:
    python e4_doctor.py                      # check ~/.claude + the current directory
    python e4_doctor.py --project C:\\code\\myapp
    python e4_doctor.py --fix

Exit code: 1 if any check FAILs, else 0.
"""
from __future__ import annotations
import argparse
import datetime as dt
import io
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PASS, WARN, FAIL, FIXED = "PASS", "WARN", "FAIL", "FIXED"
SCRIPT_RE = re.compile(r"""((?:\$\{?HOME\}?|~)?[^\s"']*?)\.claude/hooks/([\w.-]+\.(?:sh|py))""")


class Doctor:
    def __init__(self, repo: Path, home: Path, project: Path, fix: bool, force: bool = False):
        self.repo, self.home, self.project = repo, home, project
        self.fix, self.force = fix or force, force
        self.src_hooks = repo / "claude-config" / ".claude" / "hooks"
        self.results: list[tuple[str, str, str]] = []
        self.backup_dir: Path | None = None
        self.settings: list[tuple[str, Path, dict]] = []

    def add(self, status: str, check: str, detail: str) -> None:
        self.results.append((status, check, detail))

    def short(self, p: Path) -> str:
        try:
            return "~/" + p.resolve().relative_to(self.home.parent.resolve()).as_posix()
        except ValueError:
            return p.as_posix()

    def hook_dirs(self) -> list[Path]:
        dirs = [self.home / "hooks", self.project / ".claude" / "hooks"]
        return [d for d in dict.fromkeys(dirs) if d.is_dir()]

    # --- checks -------------------------------------------------------------------------------

    def check_tools(self) -> None:
        missing = [t for t in ("git",) if not shutil.which(t)]
        py = shutil.which("python3") or shutil.which("py")
        if not py:
            missing.append("python3/py")
        bash = shutil.which("bash")
        if not bash:
            missing.append("bash")
        if missing:
            self.add(FAIL, "tools", f"not on PATH: {', '.join(missing)} — hooks call these")
        elif is_wsl_bash(bash):
            self.add(WARN, "tools", f"`bash` resolves to WSL ({bash}), not Git Bash; hooks will run "
                                    "inside WSL with Linux paths. Put Git's bin dir earlier on PATH.")
        else:
            self.add(PASS, "tools", "git, python, bash found")

    def check_settings(self) -> None:
        candidates = [("user", self.home / "settings.json"),
                      ("project", self.project / ".claude" / "settings.json"),
                      ("local", self.project / ".claude" / "settings.local.json")]
        for scope, path in candidates:
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except (ValueError, OSError) as e:
                # Claude Code silently ignores an unparsable settings file — every hook in it is off.
                self.add(FAIL, "settings", f"{self.short(path)} is not valid JSON ({e}); "
                                           "Claude Code ignores this whole file")
                continue
            self.settings.append((scope, path, data))
        if self.settings:
            self.add(PASS, "settings", ", ".join(f"{s}: {self.short(p)}" for s, p, _ in self.settings) + " parse")

    def iter_hook_commands(self):
        for scope, path, data in self.settings:
            for event, groups in (data.get("hooks") or {}).items():
                for group in groups or []:
                    for hook in group.get("hooks") or []:
                        if hook.get("type") == "command" and hook.get("command"):
                            yield scope, path, event, group.get("matcher", ""), hook["command"]

    def check_registrations(self) -> None:
        seen = defaultdict(list)
        missing = []
        for scope, _, event, matcher, command in self.iter_hook_commands():
            for prefix, script in SCRIPT_RE.findall(command):
                seen[(event, script)].append(f"{scope}" + (f" [{matcher}]" if matcher else ""))
                base = self.home if re.search(r"HOME|~", prefix) else self.project / ".claude"
                target = base / "hooks" / script
                if not target.is_file():
                    missing.append(f"{event} → {self.short(target)} ({scope} settings)")
        for m in missing:
            self.add(FAIL, "hook wiring", f"registered script not found: {m}")
        dupes = {k: v for k, v in seen.items() if len(v) > 1}
        for (event, script), where in sorted(dupes.items()):
            self.add(WARN, "hook wiring", f"{script} runs {len(where)}x on {event} ({', '.join(where)}); "
                                          "remove all but one registration")
        if seen and not missing and not dupes:
            self.add(PASS, "hook wiring", f"{len(seen)} hook registrations, no duplicates, all scripts exist")
        elif not seen:
            self.add(WARN, "hook wiring", "no command hooks registered in any settings file")

    def check_drift(self) -> None:
        if not self.src_hooks.is_dir():
            self.add(WARN, "hook drift", f"repo hooks not found at {self.short(self.src_hooks)}; skipped")
            return
        branch = git_branch(self.repo)
        compared = 0
        for d in self.hook_dirs():
            for src in sorted(self.src_hooks.iterdir()):
                dst = d / src.name
                if not (src.is_file() and dst.is_file()):
                    continue
                compared += 1
                # CRLF-only differences are reported by the line-ending check, not as drift.
                if normalized(src) == normalized(dst):
                    continue
                kind, origin = provenance(self.repo, src, normalized(dst))
                # Only an older version of this checkout's own history is safe to overwrite;
                # anything else may carry work the repo checkout doesn't have yet.
                if self.force or (self.fix and kind == "outdated"):
                    self.backup(dst)
                    shutil.copyfile(src, dst)
                    self.add(FIXED, "hook drift", f"{self.short(dst)} ({origin}) replaced with the "
                                                  f"repo version ({branch})")
                elif kind == "outdated":
                    self.add(WARN, "hook drift", f"{self.short(dst)} is outdated ({origin}); "
                                                 "--fix updates it")
                else:
                    self.add(WARN, "hook drift", f"{self.short(dst)} differs from the repo ({branch}): "
                                                 f"{origin}. Not auto-fixed — it may be newer; merge "
                                                 "that work or use --force to overwrite")
        if compared and not any(r[1] == "hook drift" for r in self.results):
            self.add(PASS, "hook drift", f"{compared} installed hook(s) match the repo ({branch})")

    def check_line_endings(self) -> None:
        bad = 0
        for d in self.hook_dirs():
            for sh in sorted(d.glob("*.sh")):
                raw = sh.read_bytes()
                if b"\r\n" not in raw:
                    continue
                bad += 1
                if self.fix:
                    self.backup(sh)
                    sh.write_bytes(raw.replace(b"\r\n", b"\n"))
                    self.add(FIXED, "line endings", f"{self.short(sh)} converted CRLF → LF")
                else:
                    self.add(FAIL, "line endings", f"{self.short(sh)} has CRLF endings; bash fails on "
                                                   "them (`$'\\r': command not found`). --fix converts")
        if not bad and self.hook_dirs():
            self.add(PASS, "line endings", "all installed .sh hooks use LF")

    def check_lsp(self) -> None:
        enabled = {pid for _, _, data in self.settings
                   for pid, on in (data.get("enabledPlugins") or {}).items() if on}
        try:
            installed = json.loads((self.home / "plugins" / "installed_plugins.json")
                                   .read_text(encoding="utf-8")).get("plugins", {})
        except (OSError, ValueError):
            installed = {}
        checked = 0
        for pid in sorted(enabled):
            entries = installed.get(pid) or []
            if not entries:
                continue
            install_path = Path(entries[0].get("installPath", ""))
            for name, command in lsp_commands(pid, install_path, self.home / "plugins" / "marketplaces"):
                checked += 1
                if shutil.which(command):
                    continue
                self.add(FAIL, "lsp", f"{pid}: server `{name}` needs `{command}` on PATH, not found. "
                                      f"Install it or disable the plugin")
        if checked and not any(r[1] == "lsp" for r in self.results):
            self.add(PASS, "lsp", f"{checked} LSP server binar{'y' if checked == 1 else 'ies'} found")

    def check_env(self) -> None:
        for var in ("AI_VAULT", "AI_MEMORY_PYDIR", "AI_PROJECTS_ROOT"):
            val = os.environ.get(var)
            if val and not Path(os.path.expanduser(val)).exists():
                self.add(WARN, "env", f"{var} points to a missing path: {val}")
        if not any(r[1] == "env" for r in self.results):
            unset = [v for v in ("AI_VAULT", "AI_MEMORY_PYDIR", "AI_PROJECTS_ROOT") if not os.environ.get(v)]
            self.add(PASS, "env", "vault env vars OK" + (f" (unset, wrapper defaults used: {', '.join(unset)})"
                                                         if unset else ""))

    def check_project_memory(self) -> None:
        uses_e4 = any(scope != "user" and "session_start" in cmd
                      for scope, _, _, _, cmd in self.iter_hook_commands())
        if uses_e4 and not (self.project / ".ai-memory").is_dir():
            self.add(WARN, "project", f"{self.short(self.project)} wires e4 hooks but has no .ai-memory/ — "
                                      "run /e4:init")

    # --- helpers ------------------------------------------------------------------------------

    def backup(self, path: Path) -> None:
        if self.backup_dir is None:
            stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
            self.backup_dir = self.home / "hooks" / f"backup-{stamp}"
        dest = self.backup_dir / path.parent.parent.name / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

    def run(self) -> int:
        self.check_tools()
        self.check_settings()
        self.check_registrations()
        self.check_drift()
        self.check_line_endings()
        self.check_lsp()
        self.check_env()
        self.check_project_memory()
        return self.report()

    def report(self) -> int:
        print(f"e4 doctor — repo {self.short(self.repo)} ({git_branch(self.repo)}), "
              f"project {self.short(self.project)}")
        for status, check, detail in self.results:
            print(f"{status:<5}  {check:<13} {detail}")
        counts = {s: sum(1 for r in self.results if r[0] == s) for s in (PASS, WARN, FAIL, FIXED)}
        print("\n" + ", ".join(f"{n} {s.lower()}" for s, n in counts.items() if n))
        if self.backup_dir:
            print(f"Backups of overwritten files: {self.short(self.backup_dir)}")
        elif counts[WARN] or counts[FAIL]:
            fixable = any(r[1] in ("hook drift", "line endings") and r[0] != PASS for r in self.results)
            if fixable:
                print("Re-run with --fix to repair hook drift and line endings.")
        return 1 if counts[FAIL] else 0


def is_wsl_bash(path: str | None) -> bool:
    return bool(path) and Path(path).as_posix().lower().endswith("windows/system32/bash.exe")


def normalized(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def lsp_commands(plugin_id: str, install_path: Path, marketplaces: Path) -> list[tuple[str, str]]:
    """(server name, command) pairs a plugin declares. LSP servers can be declared in the
    installed plugin.json, a root .lsp.json, or inline in the marketplace entry (strict: false
    plugins), so all three are read."""
    name, _, market = plugin_id.partition("@")
    servers: dict = {}
    sources = [(install_path / ".claude-plugin" / "plugin.json", "manifest"),
               (install_path / ".lsp.json", "lsp"),
               (marketplaces / market / "plugins" / name / ".claude-plugin" / "plugin.json", "manifest"),
               (marketplaces / market / "plugins" / name / ".lsp.json", "lsp")]
    for path, kind in sources:
        data = read_json(path)
        if isinstance(data, dict):
            servers.update(data.get("lspServers") or {} if kind == "manifest" else data)
    catalog = read_json(marketplaces / market / ".claude-plugin" / "marketplace.json")
    for entry in (catalog or {}).get("plugins") or []:
        if isinstance(entry, dict) and entry.get("name") == name:
            servers.update(entry.get("lspServers") or {})
    return [(n, cfg["command"]) for n, cfg in servers.items()
            if isinstance(cfg, dict) and isinstance(cfg.get("command"), str)]


def git_bytes(repo: Path, *args: str) -> tuple[int, bytes]:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=10)
    return r.returncode, r.stdout


def git_text(repo: Path, *args: str) -> tuple[int, str]:
    code, out = git_bytes(repo, *args)
    return code, out.decode("utf-8", "replace").strip()


def provenance(repo: Path, src: Path, installed: bytes) -> tuple[str, str]:
    """Classify an installed copy against the repo history of `src`.

    Returns ("outdated", ...) when it equals a version from HEAD's own history,
    ("other-branch", ...) when it equals a version only reachable from another branch,
    ("unknown", ...) when it matches no committed version or git is unavailable.
    """
    try:
        rel = src.resolve().relative_to(repo.resolve()).as_posix()
        code, log = git_text(repo, "log", "--all", "--format=%H", "--", rel)
        if code != 0:
            return "unknown", "git history unavailable"
        for sha in log.splitlines():
            code, blob = git_bytes(repo, "show", f"{sha}:{rel}")
            if code != 0 or blob.replace(b"\r\n", b"\n") != installed:
                continue
            short = sha[:7]
            if git_bytes(repo, "merge-base", "--is-ancestor", sha, "HEAD")[0] == 0:
                return "outdated", f"older version from {short}"
            _, branches = git_text(repo, "branch", "-a", "--contains", sha, "--format=%(refname:short)")
            names = sorted({b.removeprefix("origin/") for b in branches.splitlines() if b})
            return "other-branch", f"matches {short} on unmerged branch {', '.join(names) or '(none)'}"
    except (ValueError, OSError, subprocess.SubprocessError):
        return "unknown", "git history unavailable"
    return "unknown", "matches no committed version (locally modified)"


def git_branch(repo: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(repo), "branch", "--show-current"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        return f"branch {out}" if out else "detached HEAD"
    except (OSError, subprocess.SubprocessError):
        return "not a git checkout"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Health check for an e4 install.")
    ap.add_argument("--project", default=".", help="project to check (default: current directory)")
    ap.add_argument("--claude-home", default=str(Path.home() / ".claude"), help="default: ~/.claude")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]),
                    help="e4 source repo whose hooks are the reference (default: this script's repo)")
    ap.add_argument("--fix", action="store_true",
                    help="convert CRLF hooks to LF and update hooks that are older versions of the repo's")
    ap.add_argument("--force", action="store_true",
                    help="like --fix, but also overwrite hooks from other branches or edited locally")
    args = ap.parse_args(argv)
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return Doctor(Path(args.repo), Path(args.claude_home), Path(args.project).resolve(),
                  args.fix, args.force).run()


if __name__ == "__main__":
    sys.exit(main())
