param(
    [string]$IncomingRoot = ".\incoming_payroll",
    [string]$Current = "",
    [string]$Previous = "",
    [string]$OutputFolder = ".\outputs\reviews",
    [string]$OutputPrefix = "",
    [string]$PreparedBy = "OpenClaw",
    [double]$VarianceThreshold = 20.0,
    [switch]$WaitForPair,
    [double]$WaitTimeoutSeconds = 60.0,
    [double]$PollIntervalSeconds = 2.0,
    [int]$StableChecks = 2,
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

$Arguments = @("-m", "processors.payroll_review_cli")

if ($Current -and $Previous) {
    $Arguments += @($Current, $Previous)
}
else {
    $Arguments += @("--incoming-root", $IncomingRoot)

    if ($WaitForPair) {
        $Arguments += @(
            "--wait-for-pair",
            "--wait-timeout", $WaitTimeoutSeconds,
            "--poll-interval", $PollIntervalSeconds,
            "--stable-checks", $StableChecks
        )
    }
}

$Arguments += @(
    "--output-dir", $OutputPath,
    "--variance-threshold", $VarianceThreshold,
    "--prepared-by", $PreparedBy
)

if ($OutputPrefix) {
    $Arguments += @("--output-prefix", $OutputPrefix)
}

if ($PrintJson) {
    $Arguments += "--print-json"
}

Push-Location $RepoRoot
try {
    & $PythonPath @Arguments
}
finally {
    Pop-Location
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
