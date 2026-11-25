# Custom artwork from one uploaded image, using only the two CLIs (every call --json, every result checked).
#   Photoshop:   open copy -> Select Subject cutout -> light retouch (sharpen) -> transparent hero.png
#   Illustrator: Image Trace the cutout into flat vector art -> hero-vector.ai / .svg / .png
#   Photoshop:   1080x1350 poster: gradient, glow, vector hero with sticker stroke + glow, title, grade -> poster.psd / .png
# Run:  powershell -ExecutionPolicy Bypass -File examples\custom_artwork.ps1 -Image C:\path\photo.jpg -Title "HUNTER"
param(
    [Parameter(Mandatory = $true)][string]$Image,
    [string]$Title = "",
    [string]$Job = "",
    [int]$Colors = 8,
    [string]$Accent = "#ff7a18",
    [string]$Dark = "#0d0b14"
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$bin  = Join-Path $root ".venv\Scripts"
if (-not (Test-Path $Image)) { throw "Image not found: $Image" }
if (-not $Job) { $Job = [IO.Path]::GetFileNameWithoutExtension($Image) }
$base = Join-Path $env:USERPROFILE "Documents\Adobe-Work\$Job"
$work = Join-Path $base "work"; $out = Join-Path $base "out"
New-Item -ItemType Directory -Force $work, $out | Out-Null
Get-ChildItem $work, $out -File | Remove-Item          # files this script made on an earlier run
$src = Join-Path $work ("source" + [IO.Path]::GetExtension($Image))
Copy-Item $Image $src                                   # never edit the user's original

function Illus { $r = & "$bin\cli-anything-illustrator.exe" --json @args | ConvertFrom-Json; if (-not $r.ok) { throw "illustrator $($args -join ' '): $($r.error)" }; $r.result }
function Pshop { $r = & "$bin\cli-anything-photoshop.exe"  --json @args | ConvertFrom-Json; if (-not $r.ok) { throw "photoshop $($args -join ' '): $($r.error)" }; $r.result }

# ---------------- 1. Photoshop: cutout
$d = Pshop doc open $src
$cut = Pshop cutout Background --mode layer --name Hero
Write-Host "subject bounds:" ($cut.subjectBounds -join ",")
Pshop retouch sharpen --layer Hero --radius 1.5 --strength 60 | Out-Null
Pshop layer set Background --hidden | Out-Null
Pshop doc export "$work\hero.png" | Out-Null
Pshop doc save "$out\cutout.psd" | Out-Null
Pshop doc close | Out-Null

# ---------------- 2. Illustrator: flat vector version (artboard matches the image aspect)
$w = 540; $h = [math]::Round($w * $d.height / $d.width)
Illus doc new --width $w --height $h | Out-Null
$tr = Illus trace image "$work\hero.png" --width $w --colors $Colors --noise 12 --snap-lines --drop-background --name HeroVector
Write-Host "vector:" $tr.trace.paths "paths," $tr.trace.colors "colours, background shapes removed:" $tr.trace.droppedBackground
Illus doc save "$out\hero-vector.ai" | Out-Null
Illus doc export "$out\hero-vector.svg" | Out-Null
Illus doc export "$work\hero-vector.png" --scale 2 | Out-Null
Illus doc close | Out-Null

# ---------------- 3. Photoshop: poster
Pshop doc new --width 1080 --height 1350 --name poster | Out-Null
Pshop fill-layer gradient --stop $Dark --stop "#2b1a3d@70" --stop $Dark --angle -90 --name Backdrop | Out-Null
Pshop fill $Accent --x 140 --y 160 --w 800 --h 800 --shape ellipse --new-layer Glow | Out-Null
Pshop filter apply gaussian-blur -p radius=160 --layer Glow | Out-Null
Pshop layer set Glow --opacity 55 --blend screen | Out-Null
Pshop place "$work\hero-vector.png" --name Hero | Out-Null
$hero = Pshop layer transform Hero --height 1210          # fit, keep aspect (smart object = no quality loss)
$b = $hero.bounds; $hw = $b[2] - $b[0]; $hh = $b[3] - $b[1]
if ($hw -gt 1000) { $hero = Pshop layer transform Hero --width 1000; $b = $hero.bounds; $hw = $b[2] - $b[0]; $hh = $b[3] - $b[1] }
$targetBottom = 1350 - 70
Pshop layer move Hero --dx ((1080 - $hw) / 2 - $b[0]) --dy ($targetBottom - $b[3]) | Out-Null
Pshop style set Hero --stroke '{\"color\":\"#ffffff\",\"size\":10}' --outer-glow ('{\"color\":\"' + $Accent + '\",\"opacity\":60,\"size\":45}') | Out-Null
if ($Title) {
    Pshop fill $Dark --x 0 --y 1090 --w 1080 --h 260 --new-layer "Title band" --feather 60 --opacity 85 | Out-Null
    $t = Pshop text add $Title --x 70 --y 1250 --size 120 --color "#ffffff" --font Arial-BoldMT --name Title
    $tw = $t.bounds[2] - $t.bounds[0]
    if ($tw -gt 960) { $t = Pshop text edit Title --size ([math]::Floor(120 * 960 / $tw)); $tw = $t.bounds[2] - $t.bounds[0] }
    Pshop layer move Title --dx ((1080 - $tw) / 2 - $t.bounds[0]) | Out-Null
    Pshop style set Title --drop-shadow '{\"distance\":8,\"size\":20,\"opacity\":70,\"color\":\"#000000\"}' --stroke ('{\"color\":\"' + $Accent + '\",\"size\":4}') | Out-Null
}
Pshop adjust add curves -p "points=[[0,0],[64,52],[190,205],[255,255]]" --name Grade | Out-Null
$layers = Pshop layer list
Pshop doc save "$out\poster.psd" | Out-Null
Pshop doc export "$out\poster.png" | Out-Null
Pshop doc close | Out-Null

Write-Host "hero size on poster:" $hw "x" $hh
Write-Host "layers:" (($layers.layers | ForEach-Object { $_.path }) -join " | ")
Write-Host "out:" $out
Get-ChildItem $out | ForEach-Object { Write-Host "  " $_.Name $_.Length }
