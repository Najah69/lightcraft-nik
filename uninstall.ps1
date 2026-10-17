# Désinstalle « Nik Collection pour LightCraft ». Ne touche ni à LightCraft, ni à Nik, ni à vos photos.
#   powershell -ExecutionPolicy Bypass -File uninstall.ps1 [-KeepData]
param([switch]$KeepData)
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path

Remove-Item (Join-Path ([Environment]::GetFolderPath('Programs')) 'Nik Collection pour LightCraft.lnk') -ErrorAction SilentlyContinue
[Environment]::SetEnvironmentVariable('LIGHTCRAFT_CONTROL_PORT', $null, 'User')
$claude = Get-Command claude -ErrorAction SilentlyContinue
if ($claude) { & $claude.Source mcp remove -s user lightcraft-nik 2>&1 | Out-Null }
Remove-Item "$dir\NikPourLightCraft.exe", "$dir\launcher.cfg" -ErrorAction SilentlyContinue
if (-not $KeepData) { Remove-Item "$env:LOCALAPPDATA\LightCraftNik" -Recurse -Force -ErrorAction SilentlyContinue }

"Désinstallé. Dans LightCraft, videz Settings ▸ External Editing ▸ Other editor s'il pointe encore vers NikPourLightCraft.exe."
