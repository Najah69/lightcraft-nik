# Tests de bout en bout, sans les applis Nik ni votre bibliothèque LightCraft :
#  - un faux Nik (FakeNik.exe) journalise ses arguments et imite les effets des vraies applis ;
#  - un LightCraft isolé (bibliothèque et réglages dans un dossier temporaire) écoute sur le port 7981.
#   powershell -ExecutionPolicy Bypass -File tests\run-tests.ps1 [-Keep]
param([switch]$Keep)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$work = Join-Path ([IO.Path]::GetTempPath()) ("lcnik-tests-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force "$work\photos", "$work\lib", "$work\cfg" | Out-Null
[Console]::OutputEncoding = [Text.Encoding]::UTF8

# faux Nik
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /r:System.Xml.Linq.dll "/out:$work\FakeNik.exe" "$here\FakeNik.cs"
if ($LASTEXITCODE -ne 0) { throw "compilation de FakeNik impossible" }

# trois photos de test (dégradés JPEG)
Add-Type -AssemblyName System.Drawing
foreach ($n in 1..3) {
  $bmp = New-Object Drawing.Bitmap 1600, 1000
  $g = [Drawing.Graphics]::FromImage($bmp)
  $rect = New-Object Drawing.Rectangle 0, 0, 1600, 1000
  $c1 = [Drawing.Color]::FromArgb(40 * $n, 90, 200 - 40 * $n)
  $brush = New-Object Drawing.Drawing2D.LinearGradientBrush $rect, $c1, ([Drawing.Color]::White), (30.0 * $n)
  $g.FillRectangle($brush, $rect)
  $bmp.Save("$work\photos\photo-$n.jpg", [Drawing.Imaging.ImageFormat]::Jpeg)
  $g.Dispose(); $bmp.Dispose()
}

# LightCraft isolé
$env:LIGHTCRAFT_CONFIG_DIR = "$work\cfg"
$lc = Start-Process "C:\Program Files\LightCraft\lightcraft.exe" -ArgumentList "--library `"$work\lib`" --control 7981" -PassThru
$up = $false
for ($i = 0; $i -lt 40 -and -not $up; $i++) {
  Start-Sleep 1
  try { $c = New-Object Net.Sockets.TcpClient('127.0.0.1', 7981); $c.Close(); $up = $true } catch {}
}
$failed = $false
try {
  if (-not $up) { throw "LightCraft ne répond pas sur le port 7981" }
  python -I "$here\test_e2e.py" $work
  if ($LASTEXITCODE -ne 0) { $failed = $true }
  python -I "$here\test_menu.py" $work
  if ($LASTEXITCODE -ne 0) { $failed = $true }
} finally {
  Stop-Process -Id $lc.Id -ErrorAction SilentlyContinue
  Start-Sleep 2
  if ($Keep) { "Dossier de travail conservé : $work" } else { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue }
}
if ($failed) { exit 1 }
