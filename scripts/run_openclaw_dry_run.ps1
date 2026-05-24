param(
    [string]$OutputFolder = ".\outputs\reviews\dry_run",
    [switch]$PrintJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$WrapperPath = Join-Path $RepoRoot "scripts\run_openclaw_payroll_review.ps1"
$CurrentPath = Join-Path $RepoRoot "sample_data\payroll_controls_current.csv"
$PreviousPath = Join-Path $RepoRoot "sample_data\payroll_controls_previous.csv"

if ($PrintJson) {
    & $WrapperPath `
        -Current $CurrentPath `
        -Previous $PreviousPath `
        -OutputFolder $OutputFolder `
        -OutputPrefix "sample_openclaw" `
        -PreparedBy "OpenClaw dry run" `
        -PrintJson
}
else {
    & $WrapperPath `
        -Current $CurrentPath `
        -Previous $PreviousPath `
        -OutputFolder $OutputFolder `
        -OutputPrefix "sample_openclaw" `
        -PreparedBy "OpenClaw dry run"
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
