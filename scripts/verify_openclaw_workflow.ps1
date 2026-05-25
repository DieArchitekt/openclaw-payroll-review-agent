param(
    [string]$OutputRoot = ".\outputs\reviews",
    [string]$PreparedBy = "OpenClaw verification"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    $PythonPath = "python"
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Prefix = "openclaw_verify_$Timestamp"
$OutputFolder = Join-Path $OutputRoot $Prefix
$WrapperPath = Join-Path $RepoRoot "scripts\run_openclaw_payroll_review.ps1"

Push-Location $RepoRoot
try {
    & $WrapperPath `
        -IncomingRoot ".\incoming_payroll" `
        -OutputFolder $OutputFolder `
        -OutputPrefix $Prefix `
        -PreparedBy $PreparedBy

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    & $PythonPath -m processors.openclaw_runtime_v1 check-env

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    & $PythonPath -m processors.openclaw_runtime_v1 check-outputs $OutputFolder $Prefix

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Host ""
    Write-Host "OpenClaw workflow verification passed."
    Write-Host "Output folder: $OutputFolder"
    Write-Host "Output prefix: $Prefix"
}
finally {
    Pop-Location
}
