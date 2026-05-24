param(
    [string]$IncomingRoot = ".\incoming_payroll",
    [string]$Current = "",
    [string]$Previous = "",
    [string]$OutputFolder = ".\outputs\reviews",
    [string]$PreparedBy = "OpenClaw",
    [double]$VarianceThreshold = 20.0,
    [switch]$PrintJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    $PythonPath = "python"
}

$OutputPath = Join-Path $RepoRoot $OutputFolder
New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null

$ReviewPackPath = Join-Path $OutputPath "payroll_review.xlsx"
$SummaryJsonPath = Join-Path $OutputPath "payroll_review_summary.json"
$CliPath = Join-Path $RepoRoot "payroll_review_cli.py"

$Arguments = @($CliPath)

if ($Current -and $Previous) {
    $Arguments += @($Current, $Previous)
}
else {
    $Arguments += @("--incoming-root", $IncomingRoot)
}

$Arguments += @(
    "--out", $ReviewPackPath,
    "--summary-json", $SummaryJsonPath,
    "--variance-threshold", $VarianceThreshold,
    "--prepared-by", $PreparedBy
)

if ($PrintJson) {
    $Arguments += "--print-json"
}

& $PythonPath @Arguments

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
