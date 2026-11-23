# Installs the 2d-vector-salik skill into Claude Code's user skills folder.
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File .\install.ps1
$ErrorActionPreference = 'Stop'
$src = Join-Path $PSScriptRoot 'skill\2d-vector-salik'
$dst = Join-Path $env:USERPROFILE '.claude\skills\2d-vector-salik'
if (-not (Test-Path (Join-Path $src 'SKILL.md'))) { throw "SKILL.md not found in $src - run this from the repo root." }
if (Test-Path $dst) {
    # back up outside the skills folder, so Claude Code does not load the old copy as a second skill
    $bdir = Join-Path $env:USERPROFILE '.claude\skill-backups'
    New-Item -ItemType Directory -Force $bdir | Out-Null
    $backup = Join-Path $bdir "2d-vector-salik-$(Get-Date -Format yyyyMMdd-HHmmss)"
    Write-Host "Existing skill found - moving it to $backup"
    Move-Item -LiteralPath $dst -Destination $backup
}
New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
Copy-Item -LiteralPath $src -Destination $dst -Recurse
$n = (Get-ChildItem -LiteralPath $dst -Recurse -File | Measure-Object).Count
Write-Host "Installed $n files to $dst"
Write-Host "Restart Claude Code, then run /2d-vector-salik"
