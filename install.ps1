# Installe « Nik Collection pour LightCraft » : lanceur, canal de contrôle de LightCraft, raccourci, serveur MCP.
#   powershell -ExecutionPolicy Bypass -File install.ps1 [-Port 7980] [-NoMcp]
param([int]$Port = 7980, [switch]$NoMcp)
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path

$pythonw = Get-Command pythonw.exe -ErrorAction SilentlyContinue
$python  = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $pythonw -or -not $python) { throw "Python 3 introuvable : installez-le depuis python.org (case « Add python.exe to PATH »)." }
& $python.Source -c "import tkinter" 2>$null
if ($LASTEXITCODE -ne 0) { throw "Python est installé sans tkinter : réinstallez-le avec l'option « tcl/tk and IDLE »." }
if (-not (Get-ChildItem 'C:\Program Files\LightCraft\lightcraft-cli.exe' -ErrorAction SilentlyContinue)) {
  Write-Warning "LightCraft n'est pas dans C:\Program Files\LightCraft : installez-le depuis github.com/storytold/lightcraft/releases."
}
if (-not (Get-ChildItem 'C:\Program Files\DxO\Nik Collection*\bin\Nik *.exe' -ErrorAction SilentlyContinue)) {
  Write-Warning "Aucune Nik Collection trouvée dans C:\Program Files\DxO : installez-la (essai ou licence sur dxo.com)."
}

# 1. Lanceur NikPourLightCraft.exe (compilateur C# de .NET Framework, fourni avec Windows)
$csc = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
& $csc /nologo /target:winexe /optimize+ /r:System.Windows.Forms.dll "/out:$dir\NikPourLightCraft.exe" "$dir\launcher\NikPourLightCraft.cs"
if ($LASTEXITCODE -ne 0) { throw "compilation du lanceur impossible" }
[IO.File]::WriteAllText("$dir\launcher.cfg", $pythonw.Source)

# 2. Canal de contrôle de LightCraft sur 127.0.0.1:$Port à chaque lancement (variable lue par LightCraft)
[Environment]::SetEnvironmentVariable('LIGHTCRAFT_CONTROL_PORT', "$Port", 'User')

# 3. Raccourci de la palette dans le menu Démarrer
$lnk = Join-Path ([Environment]::GetFolderPath('Programs')) 'Nik Collection pour LightCraft.lnk'
$sh = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
$sh.TargetPath = "$dir\NikPourLightCraft.exe"
$sh.WorkingDirectory = $dir
$sh.Description = 'Palette Nik Collection pour LightCraft'
$nik = Get-ChildItem 'C:\Program Files\DxO\Nik Collection*\bin\Nik Collection * Palette App.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($nik) { $sh.IconLocation = "$($nik.FullName),0" }
$sh.Save()

# 4. Serveur MCP pour Claude Code (si Claude Code est installé)
$claude = Get-Command claude -ErrorAction SilentlyContinue
if (-not $NoMcp -and $claude) {
  $ErrorActionPreference = 'Continue'
  & $claude.Source mcp remove -s user lightcraft-nik 2>&1 | Out-Null
  & $claude.Source mcp add -s user lightcraft-nik -- $python.Source -I "$dir\lcnik_mcp.py"
}

"Installé. Fermez et rouvrez LightCraft pour qu'il ouvre son canal de contrôle (port $Port)."
