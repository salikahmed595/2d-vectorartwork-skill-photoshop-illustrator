# Installs every skill in .\skill (each folder with a SKILL.md) into Claude Code's user skills folder:
#   2d-vector-salik, 2dvector-photoshop-illustrator-salik, hand-made, ...
# An existing copy is moved to ~/.claude/skill-backups first, never overwritten.
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File .\install.ps1
$ErrorActionPreference = 'Stop'
$skillsRoot = Join-Path $PSScriptRoot 'skill'
$dstRoot = Join-Path $env:USERPROFILE '.claude\skills'
$bdir = Join-Path $env:USERPROFILE '.claude\skill-backups'
$stamp = Get-Date -Format yyyyMMdd-HHmmss

$skills = Get-ChildItem -LiteralPath $skillsRoot -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }
if (-not $skills) { throw "No skills found in $skillsRoot - run this from the repo root." }
New-Item -ItemType Directory -Force $dstRoot | Out-Null

foreach ($skill in $skills) {
    $dst = Join-Path $dstRoot $skill.Name
    if (Test-Path $dst) {
        # back up outside the skills folder, so Claude Code does not load the old copy as a second skill
        New-Item -ItemType Directory -Force $bdir | Out-Null
        $backup = Join-Path $bdir "$($skill.Name)-$stamp"
        Write-Host "Existing $($skill.Name) found - moving it to $backup"
        Move-Item -LiteralPath $dst -Destination $backup
    }
    Copy-Item -LiteralPath $skill.FullName -Destination $dst -Recurse
    $n = (Get-ChildItem -LiteralPath $dst -Recurse -File | Measure-Object).Count
    Write-Host "Installed $($skill.Name) ($n files) to $dst"
}
Write-Host "Restart Claude Code. The studio app (studio-frontend) picks the skills up on its next job."
