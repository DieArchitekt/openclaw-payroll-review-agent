param(
    [string]$OutputFolder = ".\outputs\reviews\dry_run",
    [switch]$PrintJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$WrapperPath = Join-Path $RepoRoot "scripts\run_openclaw_payroll_review.ps1"

if ($PrintJson) {
    & $WrapperPath `
        -IncomingRoot ".\incoming_payroll" `
        -OutputFolder $OutputFolder `
        -OutputPrefix "sample_openclaw" `
        -PreparedBy "OpenClaw dry run" `
        -PrintJson
}
else {
    & $WrapperPath `
        -IncomingRoot ".\incoming_payroll" `
        -OutputFolder $OutputFolder `
        -OutputPrefix "sample_openclaw" `
        -PreparedBy "OpenClaw dry run"
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
