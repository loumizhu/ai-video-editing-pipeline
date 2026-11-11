<#
 .SYNOPSIS  values JSON -> ProRes 4444 alpha .mov + reference PNG for the keyword-pop family.
 .EXAMPLE   powershell -NoProfile -File render.ps1 -Values .\keyword-pop.json.example
 .NOTES     Style: ..\style.json.
            The template is rebuilt from the values on every run (build.py measures the text), into a temp
            folder, so the committed .ectemplate/.ecproj are only rewritten with -UpdateTemplate.
#>
param (
    [string]$Values = "$PSScriptRoot\keyword-pop.json.example",
    [string]$Out = "$PSScriptRoot\renders\keyword-pop.mov",
    [string]$Style = "$PSScriptRoot\..\style.json",
    [switch]$UpdateTemplate,
    [switch]$NoFrame
)
$ErrorActionPreference = "Stop"
$CLI = (Get-Content -Raw "$PSScriptRoot\..\style.json" | ConvertFrom-Json).toolchain.effectcraft_cli
$BuildDir = if ($UpdateTemplate) { "$PSScriptRoot" } else { Join-Path $env:TEMP ("publora_" + [guid]::NewGuid().ToString("N")) }
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
$Resolved = Join-Path $BuildDir "values.resolved.json"

python "$PSScriptRoot\build.py" --style "$Style" --values "$Values" --out-dir "$BuildDir" --emit-values "$Resolved"
if ($LASTEXITCODE -ne 0) { throw "build.py failed ($LASTEXITCODE)" }

$Template = Join-Path $BuildDir "keyword-pop.ectemplate"
$outDir = Split-Path -Parent $Out
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

& $CLI render --template $Template --values $Resolved --out $Out --format prores --prores 4444 --channels rgba
if ($LASTEXITCODE -ne 0) { throw "render failed ($LASTEXITCODE)" }
if (-not $NoFrame) {
    $png = [System.IO.Path]::ChangeExtension($Out, ".png")
    & $CLI render-frame --template $Template --values $Resolved --time 1.0 --out $png --transparent
    if ($LASTEXITCODE -ne 0) { throw "render-frame failed ($LASTEXITCODE)" }
}
if (-not $UpdateTemplate) { Remove-Item -Recurse -Force $BuildDir } else { Remove-Item -Force $Resolved }
Write-Host "OK: $Out"
