$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
$BuildDir = Join-Path $Root ".build"
$DistDir = Join-Path $BuildDir "dist"
$WorkDir = Join-Path $BuildDir "work"
$ReleaseDir = Join-Path $Root "release"

Write-Host "Building Potential Evidence Finder v$Version"
Write-Host "Repository: $Root"

if (Test-Path $BuildDir) { Remove-Item $BuildDir -Recurse -Force }
if (Test-Path $ReleaseDir) { Remove-Item $ReleaseDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $DistDir, $WorkDir, $ReleaseDir | Out-Null

python -m pip install --upgrade pip
python -m pip install -r (Join-Path $Root "build\requirements-build.txt")

python -m PyInstaller --noconfirm --clean `
  --distpath $DistDir `
  --workpath (Join-Path $WorkDir "field_collector") `
  (Join-Path $Root "build\FieldCollector.spec")

python -m PyInstaller --noconfirm --clean `
  --distpath $DistDir `
  --workpath (Join-Path $WorkDir "case_manager") `
  (Join-Path $Root "build\CaseManager.spec")

$FieldDir = Join-Path $DistDir "FieldCollector"
if (-not (Test-Path (Join-Path $FieldDir "FieldCollector.exe"))) {
  throw "FieldCollector.exe was not produced."
}
New-Item -ItemType Directory -Force -Path (Join-Path $FieldDir "results") | Out-Null
Copy-Item (Join-Path $Root "field_collector\README.md") (Join-Path $FieldDir "README.txt") -Force

$FieldZip = Join-Path $ReleaseDir "FieldCollector_Windows_x64_v$Version.zip"
Compress-Archive -Path (Join-Path $FieldDir "*") -DestinationPath $FieldZip -CompressionLevel Optimal

$CaseExeSource = Join-Path $DistDir "CaseManager.exe"
if (-not (Test-Path $CaseExeSource)) {
  throw "CaseManager.exe was not produced."
}
$CaseExe = Join-Path $ReleaseDir "CaseManager_Windows_x64_v$Version.exe"
Copy-Item $CaseExeSource $CaseExe -Force

$HashFile = Join-Path $ReleaseDir "SHA256SUMS.txt"
$Lines = @()
Get-ChildItem $ReleaseDir -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | Sort-Object Name | ForEach-Object {
  $Hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  $Lines += "$Hash  $($_.Name)"
}
$Lines | Set-Content -Path $HashFile -Encoding ascii

Write-Host ""
Write-Host "Release assets:"
Get-ChildItem $ReleaseDir -File | ForEach-Object { Write-Host " - $($_.FullName)" }
