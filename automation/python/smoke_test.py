#!/usr/bin/env python3
"""
smoke_test.py — End-to-end smoke test for the e4 scripts and hooks, in a throwaway temp project.

Covers: init_project_memory (+ slim CLAUDE.md), e4_task new/set-status, the e4.py launcher's stdin
argument passing, session_start.sh output size, e4_session draft + the hooks' "incomplete" check,
context_nudge.py bands, read_guard.py allow/deny, and `bash -n` + LF endings for every hook script.
Does not touch the real vault or any real project. Stdlib only.

Usage:  python3 automation/python/smoke_test.py      (set E4_BASH to pick a bash; default: PATH)
Exit status 0 = all checks passed.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PYDIR = Path(__file__).resolve().parent
REPO = PYDIR.parent.parent
HOOKS = REPO / "claude-config" / ".claude" / "hooks"
TOKEN_TARGET = 300  # SessionStart output budget, estimated as chars / 4
BASH = os.environ.get("E4_BASH") or shutil.which("bash") or "bash"

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def run(cmd: list[str], cwd: Path, env: dict, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, input=stdin.encode("utf-8"), capture_output=True, timeout=60)


def out(proc: subprocess.CompletedProcess) -> str:
    return proc.stdout.decode("utf-8", errors="replace")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="e4-smoke-") as tmp:
        tmp = Path(tmp)
        proj = tmp / "proj"
        proj.mkdir()
        tmpdir = tmp / "t"
        tmpdir.mkdir()
        # Isolate every marker file (stop_reminder, context_nudge) inside this temp dir.
        env = dict(os.environ, AI_MEMORY_PYDIR=str(PYDIR), PYTHONIOENCODING="utf-8",
                   TMPDIR=str(tmpdir), TEMP=str(tmpdir), TMP=str(tmpdir))
        env.pop("E4_READ_GUARD", None)
        env.pop("E4_CONTEXT_NUDGE_TOKENS", None)
        py = sys.executable

        # 1. init ----------------------------------------------------------------------------
        run(["git", "init", "-q"], proj, env)
        r = run([py, str(PYDIR / "init_project_memory.py"), str(proj), "--name", "Smoke", "--with-claude-md"], proj, env)
        mem = proj / ".ai-memory"
        check("init: .ai-memory scaffolded", r.returncode == 0 and (mem / "progress.md").is_file(), out(r))
        template = (REPO / "project-template" / "CLAUDE.md").read_text(encoding="utf-8").replace("\r\n", "\n")
        written = (proj / "CLAUDE.md").read_text(encoding="utf-8")
        check("init: CLAUDE.md is the slim template", written == template)
        check("template CLAUDE.md is slim (<= 350 words)", len(template.split()) <= 350, f"{len(template.split())} words")
        (proj / ".claude" / "hooks").mkdir(parents=True)
        for hook in HOOKS.iterdir():
            if hook.is_file():
                shutil.copy(hook, proj / ".claude" / "hooks" / hook.name)

        # 2. tasks ---------------------------------------------------------------------------
        r = run([py, str(PYDIR / "e4_task.py"), "new", "Example", "--project", str(proj)], proj, env)
        task_rel = out(r).strip()
        task_id = Path(task_rel).stem
        check("task new: prints one path line", r.returncode == 0 and len(out(r).splitlines()) == 1, out(r))
        check("task new: id shape", re.fullmatch(r"TASK-\d{8}-\d{6}-example", task_id) is not None, task_id)
        check("task new: file exists", (proj / task_rel).is_file(), task_rel)
        board = (mem / "active-tasks.md").read_text(encoding="utf-8")
        check("task new: active-tasks lists it under Next Up", task_id in board.split("## 🔜 Next Up")[1].split("##")[0])
        r = run([py, str(PYDIR / "e4_task.py"), "set-status", task_id, "in-progress", "--note", "started",
                 "--project", str(proj)], proj, env)
        board = (mem / "active-tasks.md").read_text(encoding="utf-8")
        task_text = (proj / task_rel).read_text(encoding="utf-8")
        check("set-status: front-matter updated", "\nstatus: in-progress\n" in task_text)
        check("set-status: checkpoint logged", "todo -> in-progress (started)" in task_text)
        check("set-status: reflected under Current Task", task_id in board.split("## 🎯 Current Task")[1].split("##")[0])
        r = run([py, ".claude/hooks/e4.py", "task", "new", "-"], proj, env, stdin="Quote \"x\" $(whoami) `id` -- detail\n")
        made = out(r).strip()
        check("launcher: stdin title passed literally", made.endswith("-quote-x-whoami-id.md") and r.returncode == 0, out(r))
        r = run([py, ".claude/hooks/e4.py", "task", "set-status", "nope", "done"], proj, env)
        check("launcher: errors exit 0 with 'e4: error'", r.returncode == 0 and out(r).startswith("e4: error"), out(r))

        # 3. SessionStart size ---------------------------------------------------------------
        r = run([BASH, ".claude/hooks/session_start.sh"], proj, env, stdin="{}")
        start_out = out(r)
        tokens = len(start_out) // 4
        check("session_start: produces the resume", "Project memory" in start_out and task_id in start_out, start_out)
        check(f"session_start: under {TOKEN_TARGET} tokens", tokens < TOKEN_TARGET, f"~{tokens} tokens")
        print(f"      session_start output: {len(start_out)} chars, ~{tokens} tokens")

        # 4. session draft -------------------------------------------------------------------
        # The init seed session is dated today and has a TL;DR, which would make stop_reminder
        # treat today as already logged; remove it so the draft is the only session today.
        for seed in (mem / "sessions").glob("*-000000-init.md"):
            seed.unlink()
        r = run([py, str(PYDIR / "e4_session.py"), "draft", "--project", str(proj), "--note", "smoke"], proj, env)
        lines = out(r).splitlines()
        draft = proj / lines[0] if lines else proj / "missing"
        check("draft: name shape", re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d{6}-[A-Za-z0-9-]+\.md", draft.name) is not None, draft.name)
        check("draft: file exists", draft.is_file())
        check("draft: lists in-progress task", any(task_id in l for l in lines[1:]), out(r))
        text = draft.read_text(encoding="utf-8") if draft.is_file() else ""
        check("draft: TL;DR left as placeholder", "**TL;DR**: <!-- e4:fill TL;DR -->" in text)
        check("draft: file names only, no diff hunks", "@@" not in text and "+++" not in text)
        r = run([BASH, ".claude/hooks/session_start.sh"], proj, env, stdin="{}")
        check("draft: session_start flags it as unsaved", "ended without /e4:end-session" in out(r), out(r))
        r = run([BASH, ".claude/hooks/stop_reminder.sh"], proj, env, stdin="{}")
        check("draft: stop_reminder still nudges", "additionalContext" in out(r), out(r))
        draft.write_text(text.replace("<!-- e4:fill TL;DR -->", "Smoke-tested the e4 flow."), encoding="utf-8")
        for marker in tmpdir.glob(".claude_stop_*"):
            marker.unlink()
        r = run([BASH, ".claude/hooks/session_start.sh"], proj, env, stdin="{}")
        check("filled: session_start shows its TL;DR", "Smoke-tested the e4 flow." in out(r)
              and "ended without" not in out(r), out(r))
        r = run([BASH, ".claude/hooks/stop_reminder.sh"], proj, env, stdin="{}")
        check("filled: stop_reminder is silent", out(r).strip() == "", out(r))

        # 5. context nudge -------------------------------------------------------------------
        transcript = tmp / "transcript.jsonl"

        def nudge(cache_read: int, prompt: str = "hi") -> str:
            entry = {"type": "assistant", "message": {"usage": {
                "input_tokens": 10, "cache_read_input_tokens": cache_read, "cache_creation_input_tokens": 0}}}
            transcript.write_text(json.dumps({"type": "user"}) + "\n" + json.dumps(entry) + "\n", encoding="utf-8")
            event = {"session_id": "smoke", "transcript_path": str(transcript), "cwd": str(proj), "prompt": prompt}
            return out(run([py, ".claude/hooks/context_nudge.py"], proj, env, stdin=json.dumps(event))).strip()

        check("nudge: silent under threshold", nudge(10_000) == "")
        over = nudge(90_000)
        check("nudge: fires over threshold", "/e4:end-session" in over and json.loads(over)
              ["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit", over)
        check("nudge: silent on repeat in same band", nudge(95_000) == "")
        check("nudge: fires again at the next band", "~170k" in nudge(170_000))
        other = "TASK-20200101-000000"
        check("nudge: task switch noticed once", other in nudge(170_000, f"now do {other}")
              and nudge(170_000, f"now do {other}") == "")
        check("nudge: bad input exits 0 silently",
              run([py, ".claude/hooks/context_nudge.py"], proj, env, stdin="not json").returncode == 0)

        # 6. read guard ----------------------------------------------------------------------
        (proj / "src.py").write_text("print(1)\n", encoding="utf-8")
        (proj / "package-lock.json").write_text("{}", encoding="utf-8")
        (proj / "big.txt").write_text("x" * 300_000, encoding="utf-8")
        old_session = mem / "sessions" / "2000-01-01-000000-main.md"
        old_session.write_text("**TL;DR**: old\n", encoding="utf-8")

        def guard(tool_input: dict, tool: str = "Read") -> str:
            event = {"tool_name": tool, "tool_input": tool_input, "cwd": str(proj)}
            return out(run([py, ".claude/hooks/read_guard.py"], proj, env, stdin=json.dumps(event))).strip()

        def denied(result: str) -> bool:
            return bool(result) and json.loads(result)["hookSpecificOutput"]["permissionDecision"] == "deny"

        check("guard: allows a normal file", guard({"file_path": str(proj / "src.py")}) == "")
        check("guard: denies a lockfile", denied(guard({"file_path": str(proj / "package-lock.json")})))
        check("guard: denies an old session file", denied(guard({"file_path": str(old_session)})))
        check("guard: allows the newest session file", guard({"file_path": str(draft)}) == "")
        big = guard({"file_path": str(proj / "big.txt")})
        check("guard: denies a large file without limit", denied(big) and "offset/limit" in big, big)
        check("guard: allows a large file with limit", guard({"file_path": str(proj / "big.txt"), "limit": 50}) == "")
        check("guard: Grep on a lockfile allowed", guard({"pattern": "x", "path": str(proj / "package-lock.json")}, "Grep") == "")
        env_off = dict(env, E4_READ_GUARD="off")
        r = run([py, ".claude/hooks/read_guard.py"], proj, env_off,
                stdin=json.dumps({"tool_name": "Read", "tool_input": {"file_path": str(proj / "package-lock.json")}}))
        check("guard: E4_READ_GUARD=off disables it", out(r).strip() == "")

    # 7. hook scripts: syntax + line endings -------------------------------------------------
    for sh in sorted(HOOKS.glob("*.sh")):
        r = subprocess.run([BASH, "-n", str(sh)], capture_output=True)
        check(f"bash -n {sh.name}", r.returncode == 0, r.stderr.decode(errors="replace"))
        check(f"LF endings {sh.name}", b"\r\n" not in sh.read_bytes())

    print(f"\n{'OK' if not failures else 'FAILED'}: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
