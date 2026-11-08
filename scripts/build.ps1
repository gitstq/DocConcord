# Cross-platform one-shot build for Windows PowerShell.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/build.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$py = if ($env:PYTHON) { $env:PYTHON } else { "python" }

Write-Host "==> cleaning previous artifacts"
foreach ($p in @("build", "dist", "src/docconcord.egg-info")) {
    if (Test-Path $p) { Remove-Item -Recurse -Force $p }
}

Write-Host "==> building wheel"
& $py -m pip wheel . --no-deps --no-build-isolation -w dist
if ($LASTEXITCODE -ne 0) { throw "wheel build failed" }

Write-Host "==> building sdist"
& $py setup.py sdist --dist-dir dist
if ($LASTEXITCODE -ne 0) { throw "sdist build failed" }

Write-Host "==> writing SHA256SUMS"
$lines = @()
Get-ChildItem dist -Include *.whl, *.tar.gz -Recurse | ForEach-Object {
    $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    $lines += "$h  $($_.Name)"
}
Set-Content -Path (Join-Path dist "SHA256SUMS") -Value $lines -Encoding utf8

Write-Host "==> build complete"
Get-ChildItem dist | Format-Table Name, Length
