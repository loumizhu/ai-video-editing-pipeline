# Installs the preset's OFL fonts for the current user (no admin) so EffectCraft / FilmCraft can render them.
$src = Join-Path $PSScriptRoot "fonts"; $dst = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
New-Item -ItemType Directory -Force $dst | Out-Null
Add-Type -AssemblyName System.Drawing
Get-ChildItem $src -Filter *.ttf | ForEach-Object {
  Copy-Item $_.FullName $dst -Force
  $pfc = New-Object System.Drawing.Text.PrivateFontCollection; $pfc.AddFontFile($_.FullName)
  New-ItemProperty -Path "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts" -Name ($pfc.Families[0].Name + " " + $_.BaseName + " (TrueType)") -Value (Join-Path $dst $_.Name) -PropertyType String -Force | Out-Null
  Write-Host "installed $($_.Name)"
}
