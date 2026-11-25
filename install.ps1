# Installs everything this repo needs on Windows. Safe to run again.
#   1. Every skill in .\skill (each folder with a SKILL.md) -> Claude Code's user skills folder
#      (2d-vector-salik, 2dvector-photoshop-illustrator-salik, hand-made, ...). An existing copy is moved to
#      ~/.claude/skill-backups first, never overwritten.
#   2. The Photoshop / Illustrator connector (.\adobe-connector): a Python venv with cli-anything-photoshop and
#      cli-anything-illustrator. It works only with Photoshop 2023 (v24) and Illustrator 2022 (v26) and never opens another version.
#   3. The `photoshop` and `illustrator` MCP servers, registered with Claude Code (user scope) unless already there.
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File .\install.ps1
$ErrorActionPreference = 'Stop'
$skillsRoot = Join-Path $PSScriptRoot 'skill'
$dstRoot = Join-Path $env:USERPROFILE '.claude\skills'
$bdir = Join-Path $env:USERPROFILE '.claude\skill-backups'
$stamp = Get-Date -Format yyyyMMdd-HHmmss

# ---------------------------------------------------------------- 1. skills
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

# ---------------------------------------------------------------- 2. Adobe connector
$connector = Join-Path $PSScriptRoot 'adobe-connector'
$venv = Join-Path $connector '.venv'
$py = Join-Path $venv 'Scripts\python.exe'
$apps = @('photoshop', 'illustrator')

# Run a program without stopping on its stderr; returns exit code and all output as text.
function Invoke-Program([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'
    try { $out = & $exe @argv 2>&1 | ForEach-Object { "$_" } | Out-String; return @{ code = $LASTEXITCODE; out = $out } }
    catch { return @{ code = -1; out = "$_" } }
}

# A Python 3.10+ to create the venv with: the py launcher first, then python on PATH.
function Find-Python {
    $probe = "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
    foreach ($c in @(@('py', '-3'), @('python'))) {
        if (-not (Get-Command $c[0] -CommandType Application -ErrorAction SilentlyContinue)) { continue }
        $pre = @($c | Select-Object -Skip 1)
        if ((Invoke-Program $c[0] ($pre + @('-c', $probe))).code -eq 0) { return , $c }
    }
    return $null
}

Write-Host ""
Write-Host "Adobe connector (Photoshop 2023 + Illustrator 2022)"
if (-not (Test-Path $py)) {
    $base = Find-Python
    if (-not $base) {
        Write-Host "Python 3.10 or newer is needed for the Adobe connector. Install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then run this installer again." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "Creating the connector venv in $venv"
    $pre = @($base | Select-Object -Skip 1)
    & $base[0] @pre -m venv $venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $py)) { throw "Could not create the venv in $venv" }
}
Write-Host "Installing cli-anything-photoshop and cli-anything-illustrator into the venv"
& $py -m pip install --disable-pip-version-check --quiet `
    -e (Join-Path $connector 'photoshop\agent-harness') `
    -e (Join-Path $connector 'illustrator\agent-harness')
if ($LASTEXITCODE -ne 0) { throw "pip could not install the connector (exit code $LASTEXITCODE)." }

# Is the pinned release (Photoshop 2023 / Illustrator 2022) installed and registered for automation? Reads the registry only; starts nothing.
$missing = @()
foreach ($app in $apps) {
    $exe = Join-Path $venv "Scripts\cli-anything-$app.exe"
    $run = Invoke-Program $exe @('--json', 'app', 'check')
    $reply = $null
    try { $reply = (($run.out.Trim() -split "`r?`n") | Select-Object -Last 1) | ConvertFrom-Json } catch {}
    if ($run.code -eq 0 -and $reply -and $reply.ok) {
        Write-Host "  OK  $($reply.result.message)"
    } else {
        $msg = if ($reply -and $reply.error) { $reply.error } else { "cli-anything-$app could not check the installation (exit code $($run.code)): $($run.out.Trim())" }
        Write-Host "  MISSING  $msg" -ForegroundColor Yellow
        $missing += $app
    }
}
if ($missing) {
    Write-Host ""
    Write-Host "Install the missing Adobe app(s) above (Photoshop 2023 / Illustrator 2022), open each once, then run this installer again. Other versions (e.g. 2027) are never used." -ForegroundColor Yellow
    exit 1
}

# ---------------------------------------------------------------- 3. MCP servers
$claude = Get-Command claude -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $claude) {
    Write-Host ""
    Write-Host "Claude Code CLI not found, so the MCP servers were not registered. Install it (irm https://claude.ai/install.ps1 | iex), open a new terminal and run this installer again." -ForegroundColor Yellow
    exit 1
}
# Folders the connector may read and write: the user folder, plus the studio app's job folder
# (studio-frontend\production\jobs, the same roots the studio app registers) when the repo is outside the user folder.
$roots = @($env:USERPROFILE)
$jobs = Join-Path $PSScriptRoot 'studio-frontend\production\jobs'
$home_ = $env:USERPROFILE.TrimEnd('\') + '\'
if (-not $jobs.StartsWith($home_, [StringComparison]::OrdinalIgnoreCase)) { $roots += $jobs }
$rootArgs = @($roots | ForEach-Object { '--allowed-root'; $_ })
foreach ($app in $apps) {
    $exe = Join-Path $venv "Scripts\cli-anything-$app.exe"
    $get = Invoke-Program $claude.Source @('mcp', 'get', $app)
    if ($get.code -eq 0) {
        $cmd = ($get.out -split "`r?`n" | Where-Object { $_ -match '^\s*Command:' } | Select-Object -First 1) -replace '^\s*Command:\s*', ''
        Write-Host "  MCP server '$app' is already registered ($cmd) - left unchanged."
        continue
    }
    $add = Invoke-Program $claude.Source (@('mcp', 'add', '--scope', 'user', $app, '--', $exe, 'mcp') + $rootArgs)
    if ($add.code -ne 0) { throw "claude mcp add $app failed (exit code $($add.code)): $($add.out.Trim())" }
    Write-Host "  Registered MCP server '$app' -> $exe (files allowed under $($roots -join ', '))"
}

Write-Host ""
Write-Host "Done. Restart Claude Code. The studio app (studio-frontend) picks the skills up on its next job."
