<#
.SYNOPSIS
  Convenience wrapper around the Python memory automation tools (Windows-friendly).

.EXAMPLE
  .\Ai-Memory.ps1 daily
  .\Ai-Memory.ps1 dashboard C:\code\myapp
  .\Ai-Memory.ps1 archive C:\code\myapp
  .\Ai-Memory.ps1 sync
  .\Ai-Memory.ps1 doctor C:\code\myapp --fix

.NOTES
  Set $env:AI_VAULT and $env:AI_PROJECTS_ROOT, or edit defaults below.
#>
param(
  [Parameter(Position=0)][string]$Command = "help",
  [Parameter(Position=1)][string]$Project,
  [Parameter(Position=2, ValueFromRemainingArguments=$true)][string[]]$Rest
)

$Vault = if ($env:AI_VAULT) { $env:AI_VAULT } else { Join-Path $HOME "AI-Vault" }
$ProjectsRoot = if ($env:AI_PROJECTS_ROOT) { $env:AI_PROJECTS_ROOT } else { Join-Path $HOME "code" }
$PyDir = Resolve-Path (Join-Path $PSScriptRoot "..\python")

switch ($Command) {
  "daily" {
    python "$PyDir\generate_daily_summary.py" --vault $Vault --projects-root $ProjectsRoot
  }
  "dashboard" {
    if (-not $Project) { throw "usage: Ai-Memory.ps1 dashboard <project>" }
    python "$PyDir\create_dashboard.py" --vault $Vault --project $Project
    python "$PyDir\create_dashboard.py" --vault $Vault --rebuild-index --projects-root $ProjectsRoot
  }
  "archive" {
    if (-not $Project) { throw "usage: Ai-Memory.ps1 archive <project>" }
    python "$PyDir\archive_completed_tasks.py" --project $Project --vault $Vault --infer
  }
  "sync" {
    python "$PyDir\create_dashboard.py" --vault $Vault --rebuild-index --projects-root $ProjectsRoot
  }
  "doctor" {
    # `doctor --fix` binds --fix to $Project, so treat a leading "--" value as a flag.
    $flags = @($Rest | Where-Object { $_ })
    $proj = "."
    if ($Project -like "--*") { $flags = @($Project) + $flags } elseif ($Project) { $proj = $Project }
    python "$PyDir\e4_doctor.py" --project $proj @flags
    exit $LASTEXITCODE
  }
  default {
    @"
Ai-Memory.ps1 — memory maintenance

Commands:
  daily             Generate today's global daily summary
  dashboard PROJ    Rebuild project dashboard + master index
  archive PROJ      Archive completed tasks for PROJ
  sync              Rebuild master index across all projects
  doctor [PROJ] [--fix|--force]
                    Health-check hooks, settings, LSP binaries (PROJ defaults to .)

Env:
  AI_VAULT          = $Vault
  AI_PROJECTS_ROOT  = $ProjectsRoot

Scheduled Task (daily): use Task Scheduler to run:
  powershell -File <path>\Ai-Memory.ps1 daily
"@ | Write-Host
  }
}
