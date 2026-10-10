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
$installed = Test-Path -LiteralPath (Join-Path $PSScriptRoot '.installed')
$appHome = $PSScriptRoot
if ($installed) {
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $appHome = Join-Path $env:LOCALAPPDATA 'SceneScout'
    if ($env:SCENESCOUT_HOME) { $appHome = [IO.Path]::GetFullPath($env:SCENESCOUT_HOME) }
    $env:SCENESCOUT_DATA_DIR = Join-Path $appHome 'Data'
    $env:UV_PROJECT_ENVIRONMENT = Join-Path $appHome "Environments\$Backend"
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $appHome 'Runtime\python'
} elseif (-not $env:UV_PROJECT_ENVIRONMENT) {
    $env:UV_PROJECT_ENVIRONMENT = Join-Path $PSScriptRoot ".venv-$Backend"
}
$logDir = Join-Path $appHome 'Logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logPath = Join-Path $logDir "setup-$Backend.log"
try {
    Add-Content -LiteralPath $logPath -Value ("`n--- " + (Get-Date -Format o) + " | $Backend ---") -Encoding UTF8
    Write-Host ''
    Write-Host 'SceneScout - First launch / Ilk acilis' -ForegroundColor Cyan
    Write-Host 'No manual Python setup needed / Elle Python kurmaniz gerekmez.'
    Write-Host 'Keep this window open. Stop the app with Ctrl+C.'
    Write-Host 'Bu pencereyi acik tutun. Kapatmak icin Ctrl+C kullanin.'
    Write-Host "Data / Veriler: $appHome"
    Write-Host "Setup log / Kurulum kaydi: $logPath"
    if (-not (Test-Path -LiteralPath $uvPath)) {
        Write-Host 'Preparing SceneScout / SceneScout hazirlaniyor...'
        New-Item -ItemType Directory -Path $bootstrapDir -Force | Out-Null
        $archivePath = Join-Path $bootstrapDir 'uv.zip'
        Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/astral-sh/uv/releases/download/$uvVersion/uv-x86_64-pc-windows-msvc.zip" -OutFile $archivePath
        $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $archiveHash) { throw 'Runtime download checksum mismatch. Please retry from the official release.' }
        Expand-Archive -LiteralPath $archivePath -DestinationPath $bootstrapDir -Force
    }
    Write-Host "[1/3] Preparing Python and dependencies ($Backend). First launch needs internet."
    Write-Host 'Python ve bagimliliklar otomatik hazirlaniyor. Ilk acilis internet gerektirir.'
    # Windows PowerShell 5 wraps native stderr as errors even on successful runs.
    $previousErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $uvPath sync --frozen --no-dev --extra $Backend 2>&1 | ForEach-Object {
            $line = $_.ToString()
            Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
            Write-Host $line
        }
        $syncExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorPreference
    }
    if ($syncExitCode -ne 0) { throw 'Dependency setup failed. Check internet access and free disk space.' }
    $denoPath = Join-Path $bootstrapDir 'deno.exe'
    Write-Host '[2/3] Preparing video link support / Video baglantilari hazirlaniyor...'
    if (-not (Test-Path -LiteralPath $denoPath)) {
        Write-Host 'Preparing YouTube link support / YouTube baglanti destegi hazirlaniyor...'
        $denoArchive = Join-Path $bootstrapDir 'deno.zip'
        Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/denoland/deno/releases/download/v2.9.7/deno-x86_64-pc-windows-msvc.zip' -OutFile $denoArchive
        $denoHash = (Get-FileHash -LiteralPath $denoArchive -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($denoHash -ne 'a0c3101b4158d1dfb7d6a78a7bf0f3de80c96bb423c152beec8beb22786f2238') { throw 'YouTube runtime checksum mismatch. Please retry.' }
        Expand-Archive -LiteralPath $denoArchive -DestinationPath $bootstrapDir -Force
    }
    if ($SetupOnly) { Write-Host 'SceneScout setup complete / Kurulum tamamlandi.'; exit 0 }
    Write-Host "[3/3] Opening / Aciliyor: http://127.0.0.1:$Port" -ForegroundColor Green
    Write-Host 'First video: ~1.5 GB model download. Wait for Ready before searching.'
    Write-Host 'Ilk video: ~1,5 GB model indirilir. Arama icin Hazir yazmasini bekleyin.'
    & $uvPath run --frozen --no-dev --extra $Backend scenescout --device $Backend --open-browser --port $Port
    exit $LASTEXITCODE
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Help / Yardim: QUICKSTART.html | Log / Kayit: $logPath"
    exit 1
}
