# claude-config — Drop-in .claude/ for your project

Copy the `.claude/` directory here into your project root (or merge into an existing one):

    cp -r claude-config/.claude  /path/to/project/.claude
    chmod +x /path/to/project/.claude/hooks/*.sh

Contents:
- `.claude/commands/e4/` → slash commands: /e4:init, /e4:end-session, /e4:resume, /e4:new-task, /e4:pr
- `.claude/hooks/`     → session_start.sh, session_end.sh, stop_reminder.sh,
                         e4.py (launcher the /e4:* commands call to run the automation scripts),
                         context_nudge.py (UserPromptSubmit: suggests end-session + /clear on big contexts / task switches),
                         read_guard.py (PreToolUse on Read/Grep/Glob: denies lockfiles, build dirs, old sessions, >200 KB reads),
                         guard-destructive-git.py (PreToolUse on Bash, not wired by default: blocks destructive git + secret commits)
- `.claude/settings.json` → wires the hooks to SessionStart / SessionEnd / Stop / UserPromptSubmit / PreToolUse

For commands available in ALL projects, copy the command files to ~/.claude/commands/ instead.
Full guide: ../docs/COMMANDS-AND-HOOKS.md
