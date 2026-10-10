param(
    [ValidateSet('cpu', 'cuda')][string]$Backend = 'cpu',
    [ValidateRange(1, 65535)][int]$Port = 8765,
    [switch]$SetupOnly
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$bootstrapDir = Join-Path $PSScriptRoot '.bootstrap'
$uvPath = Join-Path $bootstrapDir 'uv.exe'
$uvVersion = '0.13.0'
$archiveHash = '088962f9e7b7bd9ea740c04c650b2a21c8928c345bd99ac24350dc924dba656c'
try {
    if (-not (Test-Path -LiteralPath $uvPath)) {
        Write-Host 'Preparing SceneScout / SceneScout hazirlaniyor...'
        New-Item -ItemType Directory -Path $bootstrapDir -Force | Out-Null
        $archivePath = Join-Path $bootstrapDir 'uv.zip'
        Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/astral-sh/uv/releases/download/$uvVersion/uv-x86_64-pc-windows-msvc.zip" -OutFile $archivePath
        $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $archiveHash) { throw 'Runtime download checksum mismatch. Please retry from the official release.' }
        Expand-Archive -LiteralPath $archivePath -DestinationPath $bootstrapDir -Force
    }
    Write-Host "Preparing Python and dependencies ($Backend). First launch needs internet."
    Write-Host 'Python ve bagimliliklar otomatik hazirlaniyor. Ilk acilis internet gerektirir.'
    & $uvPath sync --frozen --no-dev --extra $Backend
    if ($LASTEXITCODE -ne 0) { throw 'Dependency setup failed. Check internet access and free disk space.' }
    if ($SetupOnly) { Write-Host 'SceneScout setup complete.'; exit 0 }
    & $uvPath run --frozen --no-dev --extra $Backend scenescout --open-browser --port $Port
    exit $LASTEXITCODE
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
