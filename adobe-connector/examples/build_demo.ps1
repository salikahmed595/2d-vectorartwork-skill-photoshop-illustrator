# Demo: an agent-style pipeline using only the two CLIs (every call is --json, every result checked).
#   Illustrator: logo from Pathfinder + gradients + symbols  ->  logo.ai / logo.svg / logo@2x.png
#   Photoshop:   1080x1350 poster with fill layers, glow, placed logo, styled text, adjustments -> poster.psd / poster.png
# Run:  powershell -ExecutionPolicy Bypass -File examples\build_demo.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$bin  = Join-Path $root ".venv\Scripts"
$out  = Join-Path $root "artifacts\demo"
New-Item -ItemType Directory -Force $out | Out-Null
Get-ChildItem $out -File | Remove-Item

function Illus { $r = & "$bin\cli-anything-illustrator.exe" --json @args | ConvertFrom-Json; if (-not $r.ok) { throw "illustrator $($args -join ' '): $($r.error)" }; $r.result }
function Pshop { $r = & "$bin\cli-anything-photoshop.exe"  --json @args | ConvertFrom-Json; if (-not $r.ok) { throw "photoshop $($args -join ' '): $($r.error)" }; $r.result }

# ---------------- Illustrator: logo (400 x 400 pt)
$doc = Illus doc new --width 400 --height 400
Illus shape ellipse --x 40 --y 40 --w 320 --h 320 --name Outer | Out-Null
Illus shape ellipse --x 105 --y 105 --w 190 --h 190 --name Inner | Out-Null
Illus pathfinder minus-front Outer Inner --name Ring | Out-Null
Illus item gradient Ring --stop "#ffb000" --stop "#ff3d6e@60" --stop "#9b2cff@100" --angle -45 | Out-Null
Illus shape star --x 130 --y 130 --w 140 --h 140 --points 4 --inner-ratio 0.32 --name Spark | Out-Null
Illus item gradient Spark --stop "#ffffff" --stop "#ffd36b" --kind radial | Out-Null
Illus shape star --x 0 --y 0 --w 40 --h 40 --points 4 --inner-ratio 0.3 --fill "#ffffff" --name Twinkle | Out-Null
Illus symbol create Twinkle Twinkle --remove-original | Out-Null
Illus symbol place Twinkle --x 318 --y 40 --scale 1.0 --name T1 | Out-Null
Illus symbol place Twinkle --x 46 --y 318 --scale 0.6 --name T2 | Out-Null
Illus symbol place Twinkle --x 340 --y 300 --scale 0.45 --name T3 | Out-Null
Illus doc save "$out\logo.ai" | Out-Null
Illus doc export "$out\logo.svg" | Out-Null
$logo = Illus doc export "$out\logo@2x.png" --scale 2
Illus doc close | Out-Null
Write-Host "logo:" $logo.path

# ---------------- Photoshop: poster (1080 x 1350 px)
Pshop doc new --width 1080 --height 1350 --name poster | Out-Null
Pshop fill-layer gradient --stop "#0b0a1f" --stop "#2a1f5c@55" --stop "#120d2b@100" --angle -90 --name "Backdrop" | Out-Null
Pshop fill "#ff3d6e" --x 190 --y 120 --w 700 --h 700 --shape ellipse --new-layer "Glow" | Out-Null
Pshop filter apply gaussian-blur -p radius=150 --layer Glow | Out-Null
Pshop layer set Glow --opacity 55 --blend screen | Out-Null
Pshop place "$out\logo@2x.png" --name Logo --x 220 --y 150 | Out-Null   # x,y = visible pixels (ring is 640 px wide -> centred) | Out-Null
Pshop style set Logo --outer-glow '{\"color\":\"#ffb000\",\"opacity\":45,\"size\":40}' | Out-Null
Pshop text add "BUILT BY AGENTS" --x 72 --y 1085 --size 104 --color "#ffffff" --font Arial-BoldMT --name Headline | Out-Null
Pshop style set Headline --drop-shadow '{\"distance\":6,\"size\":18,\"opacity\":60,\"color\":\"#000000\"}' | Out-Null
Pshop text add "Photoshop + Illustrator, driven from the command line" --x 76 --y 1160 --size 36 --color "#cfc8ff" --font ArialMT --name Tagline | Out-Null
Pshop fill "#ffb000" --x 76 --y 1210 --w 260 --h 8 --new-layer "Accent" | Out-Null
Pshop layer group Typography --layer Headline --layer Tagline --layer Accent | Out-Null
Pshop adjust add vibrance -p vibrance=20 --name "Vibrance" --above Typography | Out-Null
Pshop adjust add curves -p "points=[[0,0],[70,58],[190,205],[255,255]]" --name "Contrast" | Out-Null
$layers = Pshop layer list
Pshop doc save "$out\poster.psd" | Out-Null
$png = Pshop doc export "$out\poster.png"
Write-Host "poster:" $png.path
Write-Host "layers:" (($layers.layers | ForEach-Object { $_.path }) -join " | ")
