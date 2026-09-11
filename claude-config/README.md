# claude-config — Drop-in .claude/ for your project

Copy the `.claude/` directory here into your project root (or merge into an existing one):

    cp -r claude-config/.claude  /path/to/project/.claude
    chmod +x /path/to/project/.claude/hooks/*.sh

Contents:
- `.claude/commands/e4/` → slash commands: /e4:init, /e4:end-session, /e4:resume, /e4:new-task
- `.claude/hooks/`     → session_start.sh, session_end.sh, stop_reminder.sh,
                         guard-destructive-git.py (PreToolUse: blocks destructive git + secret commits)
- `.claude/settings.json` → wires the hooks to SessionStart / SessionEnd / Stop

For commands available in ALL projects, copy the command files to ~/.claude/commands/ instead.
Full guide: ../docs/COMMANDS-AND-HOOKS.md
