# OpenClaw Integration Report

This report explains the OpenClaw-specific parts of the Payroll Review Agent:
where they live, what they do, what is configured, and what still depends on an
external OpenClaw runtime.

## Executive Summary

OpenClaw is intended to be the primary execution layer for this project.

The repository provides:

- committed incoming payroll files
- approved wrapper scripts
- a Python CLI review engine
- runtime policy metadata
- review output validation
- agent-facing receipt and manifest files
- safeguards that keep the workflow evidence-focused

OpenClaw itself is not bundled in the repository. It must be installed and
configured separately. Once installed, OpenClaw should run the approved wrapper
script from the repository root and report from the generated receipt and
manifest.

## OpenClaw's Role

OpenClaw acts as the workflow orchestration layer.

In practical terms, it should:

1. Work from the repository root.
2. Use `incoming_payroll/` as the payroll input location.
3. Run an approved wrapper script.
4. Generate review outputs under `outputs/reviews/`.
5. Read the generated receipt, summary, and manifest.
6. Report the run status, blockers, exception counts, and next action.

OpenClaw should not act as the finance decision-maker. The workflow prepares
review evidence; approval remains outside agent authority.

## Key Files and Folders

| Path | OpenClaw relevance |
|---|---|
| `incoming_payroll/current.pdf` | Current payroll input file |
| `incoming_payroll/previous.pdf` | Previous payroll input file |
| `scripts/run_openclaw_payroll_review.ps1` | Primary Windows wrapper for OpenClaw |
| `scripts/run_openclaw_payroll_review.sh` | Bash wrapper for OpenClaw |
| `scripts/run_openclaw_dry_run.ps1` | Windows dry-run helper |
| `scripts/run_openclaw_dry_run.sh` | Bash dry-run helper |
| `scripts/verify_openclaw_workflow.ps1` | Windows end-to-end verification helper |
| `scripts/verify_openclaw_workflow.sh` | Bash end-to-end verification helper |
| `processors/payroll_review_cli.py` | Python module entry point |
| `processors/payroll_review_cli_runner.py` | CLI execution logic |
| `processors/openclaw_file_pairing.py` | Finds `current.*` and `previous.*` in the incoming folder |
| `processors/openclaw_runtime_v1/` | Runtime policy and output validation |
| `processors/agent_controls_v1/` | Receipt, review gate, redaction, and agent guard logic |
| `processors/run_manifest_v1/` | Manifest generation |
| `openclaw/runtime_policy.json` | Machine-readable OpenClaw operating boundary |
| `openclaw/agent_instruction.md` | Copy-paste instruction for OpenClaw |
| `outputs/reviews/` | Review workbook, summary, receipt, and manifest outputs |
| `outputs/agent/` | Reserved for agent-facing outputs |
| `outputs/audit/` | Reserved for audit events |
| `submission/submission_readiness_plan.md` | Submission preparation notes |

## Input Model

The judge-facing workflow uses a flat incoming folder:

```text
incoming_payroll/
  current.pdf
  previous.pdf
```

The file-pairing code accepts supported payroll input file types with the stem
`current` and `previous`.

Supported extensions:

```text
.pdf, .csv, .txt, .xlsx, .xlsm
```

For the competition repository, the committed files are PDFs:

```text
incoming_payroll/current.pdf
incoming_payroll/previous.pdf
```

The folder should contain one current file and one previous file. Extra
supported payroll files in that folder are rejected to avoid ambiguous runs.

## Primary OpenClaw Command

Windows / PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_openclaw_payroll_review.ps1 -IncomingRoot ".\incoming_payroll" -OutputFolder ".\outputs\reviews\openclaw_submission" -OutputPrefix "openclaw_submission" -PreparedBy "OpenClaw"
```

Bash:

```bash
bash ./scripts/run_openclaw_payroll_review.sh --incoming-root ./incoming_payroll --output-folder ./outputs/reviews/openclaw_submission --output-prefix openclaw_submission --prepared-by OpenClaw
```

These wrapper scripts are the intended command surface for OpenClaw.

## Wrapper Script Behaviour

### PowerShell Wrapper

File:

```text
scripts/run_openclaw_payroll_review.ps1
```

Defaults:

| Parameter | Default |
|---|---|
| `IncomingRoot` | `.\incoming_payroll` |
| `OutputFolder` | `.\outputs\reviews` |
| `PreparedBy` | `OpenClaw` |
| `VarianceThreshold` | `20.0` |
| `WaitTimeoutSeconds` | `60.0` |
| `PollIntervalSeconds` | `2.0` |
| `StableChecks` | `2` |

Behaviour:

- resolves the repo root from the script location
- uses `.venv\Scripts\python.exe` if present
- falls back to `python`
- creates the output folder
- calls `python -m processors.payroll_review_cli`
- passes incoming root, output folder, threshold, preparer, and optional prefix

### Bash Wrapper

File:

```text
scripts/run_openclaw_payroll_review.sh
```

Defaults:

| Option | Default |
|---|---|
| `--incoming-root` | `./incoming_payroll` |
| `--output-folder` | `./outputs/reviews` |
| `--prepared-by` | `OpenClaw` |
| `--variance-threshold` | `20.0` |
| `--wait-timeout-seconds` | `60.0` |
| `--poll-interval-seconds` | `2.0` |
| `--stable-checks` | `2` |

Behaviour mirrors the PowerShell wrapper.

## CLI Entry Point

Module:

```bash
python -m processors.payroll_review_cli
```

The CLI defaults to:

```text
--incoming-root incoming_payroll
```

That means a plain CLI run can use the committed `incoming_payroll/current.pdf`
and `incoming_payroll/previous.pdf` files without explicit paths.

The CLI can also accept explicit current and previous files, but that is a
developer/test path rather than the main OpenClaw workflow.

## Runtime Policy

Policy file:

```text
openclaw/runtime_policy.json
```

Current settings:

| Field | Value |
|---|---|
| `agent_mode` | `read_only_review` |
| `working_directory` | `.` |
| `allowed_write_roots` | `outputs/reviews`, `outputs/agent`, `outputs/audit` |

Allowed commands:

```text
scripts/run_openclaw_payroll_review.ps1
scripts/run_openclaw_dry_run.ps1
scripts/verify_openclaw_workflow.ps1
scripts/run_openclaw_payroll_review.sh
scripts/run_openclaw_dry_run.sh
scripts/verify_openclaw_workflow.sh
```

Allowed read globs:

```text
outputs/reviews/*_receipt.json
outputs/reviews/*_summary.json
outputs/reviews/*_manifest.json
openclaw/runtime_policy.json
openclaw/agent_instruction.md
```

Blocked read globs:

```text
incoming_payroll/*
real_data/*
*.xlsx
*.xlsm
```

Blocked actions:

```text
approve_review
reject_review
mark_exported
send_external_file
delete_file
move_source_file
archive_source_file
edit_source_file
install_package
run_arbitrary_shell
send_email
upload_file
```

Required output suffixes:

```text
_review.xlsx
_summary.json
_receipt.json
_manifest.json
```

Required receipt flags:

```json
{
  "agent_mode": "read_only_review",
  "human_action_required": true,
  "source_files_modified": false,
  "external_messages_sent": false,
  "approval_performed_by_agent": false
}
```

## What OpenClaw Practically Does

OpenClaw should perform only the orchestration around the review.

Practical sequence:

1. Confirm the repo is the workspace.
2. Run the approved wrapper script.
3. Wait for the process to complete.
4. Read the generated receipt JSON.
5. Read the generated manifest JSON.
6. Optionally read the summary JSON.
7. Report:
   - run status
   - review ID
   - review workbook path
   - high anomaly count
   - medium anomaly count
   - total anomaly count
   - blockers
   - recommended next action

The Python review engine performs the payroll extraction, reconciliation,
anomaly detection, workbook generation, receipt generation, and manifest
generation.

OpenClaw does not need to understand payroll calculations directly. It needs to
run the approved command and report from structured evidence.

## Generated Outputs

Example committed output set:

```text
outputs/reviews/openclaw_submission/
  openclaw_submission_review.xlsx
  openclaw_submission_summary.json
  openclaw_submission_receipt.json
  openclaw_submission_manifest.json
```

The latest verified run produced:

```text
High exceptions: 10
Medium exceptions: 114
Total exceptions: 124
Run status: completed_with_exceptions
```

The recommended next action was:

```text
Review HIGH anomalies before approving payroll.
```

## Receipt

The receipt is the main agent-facing status file.

Generated by:

```text
processors/agent_controls_v1/receipt.py
```

Important fields:

| Field | Meaning |
|---|---|
| `agent_mode` | Confirms read-only review mode |
| `review_id` | Unique review identifier |
| `approval_status` | Current approval workflow status |
| `human_action_required` | Always true |
| `recommended_next_action` | Safe next action for reviewer |
| `source_files_modified` | Should be false |
| `external_messages_sent` | Should be false |
| `approval_performed_by_agent` | Should be false |
| `run_status` | `completed`, `completed_with_exceptions`, or `blocked` |
| `review_pack` | Workbook path |
| `summary_json` | Summary path |
| `file_hashes` | Input/output SHA-256 hashes |
| `high_anomaly_count` | Count of HIGH anomalies |
| `medium_anomaly_count` | Count of MEDIUM anomalies |
| `ready_for_review` | Whether blockers are absent |
| `ready_for_approval` | Always false for agent |
| `blockers` | Review blockers |
| `critical_controls` | Key control flags |

OpenClaw should prefer this file for user-facing status.

## Manifest

The manifest is the audit evidence file.

Generated by:

```text
processors/run_manifest_v1/manifest.py
```

Important fields:

| Field | Meaning |
|---|---|
| `manifest_version` | Manifest schema/version |
| `generated_at` | UTC generation timestamp |
| `review_id` | Matches receipt review ID |
| `approval_status` | Current approval status |
| `prepared_by` | Actor label |
| `schema_version` | Payroll schema version |
| `rule_version` | Payroll rule version |
| `thresholds` | Review thresholds used |
| `file_hashes` | Source and generated file hashes |
| `source_files` | Current and previous file names |
| `generated_files` | Workbook, summary, receipt, manifest paths |
| `anomaly_counts` | High, medium, total anomaly counts |
| `agent_mode` | Read-only review mode |

The manifest is used to validate that the review evidence is reproducible and
that generated files match expected hashes.

## Runtime Validation

Validation module:

```text
processors/openclaw_runtime_v1/
```

Check environment:

```bash
python -m processors.openclaw_runtime_v1 check-env
```

This checks:

- `openclaw/runtime_policy.json` exists
- policy uses `read_only_review`
- `incoming_payroll/current.pdf` exists
- `incoming_payroll/previous.pdf` exists
- allowed wrapper commands exist
- `.gitignore` exists
- `real_data/` remains ignored

Check generated outputs:

```bash
python -m processors.openclaw_runtime_v1 check-outputs outputs/reviews/openclaw_submission openclaw_submission
```

This checks:

- required workbook, summary, receipt, and manifest exist
- receipt has required safety flags
- manifest uses read-only review mode
- manifest review ID matches receipt review ID
- expected hashes are present and valid length
- thresholds are included

## Review Gate

Review gate logic lives in:

```text
processors/agent_controls_v1/review_gate.py
```

The gate counts HIGH and MEDIUM anomalies and builds blockers.

Blockers include:

- no current payroll rows extracted
- no previous payroll rows extracted
- one or more HIGH payroll anomalies

The gate always sets:

```text
human_action_required = true
ready_for_approval = false
```

This is one of the main controls preventing the agent from acting as an
approval authority.

## Agent-Facing Reporting

Completion message code:

```text
processors/openclaw_reporting.py
```

The CLI prints a safe completion message containing:

- review ID
- approval status
- run status
- review pack path
- high exception count
- medium exception count
- total exception count
- recommended next action

It deliberately avoids printing payroll totals or row-level sensitive values.

## Safeguards

The OpenClaw-facing design uses several safeguards:

- approved wrapper scripts only
- flat input folder with exactly one current and one previous file
- source file hashes in receipt and manifest
- output hashes in receipt and manifest
- runtime validation before/after runs
- receipt flags proving no source modification, external send, or approval
- policy-level blocked actions
- safe path controls for agent-accessible paths
- redaction utilities for sensitive identifiers
- review gate that blocks approval readiness when HIGH anomalies exist

## What Is Not Implemented Inside This Repo

The repository does not include:

- OpenClaw installation
- OpenClaw daemon/service
- model provider configuration
- OpenAI/Anthropic/API credentials
- judge device pairing
- hosted OpenClaw runtime
- actual OpenClaw permission UI configuration

Those belong to the external OpenClaw environment.

## What You Need To Configure In OpenClaw

At minimum:

1. Install OpenClaw using the current official route.
2. Configure model/provider credentials.
3. Set this repository as the workspace.
4. Restrict OpenClaw to the approved wrapper command.
5. Direct it to read generated receipt, summary, and manifest outputs.
6. Do not grant general filesystem or shell permissions beyond the wrapper path.

Suggested instruction to OpenClaw:

```text
Run the payroll review workflow using the approved wrapper script from the
repository root. Use incoming_payroll as input. After completion, read only the
generated receipt, summary, and manifest. Report run_status, review_pack,
high_anomaly_count, medium_anomaly_count, blockers, and recommended_next_action.
Do not approve payroll, send files, edit files, move source files, or inspect
raw payroll inputs.
```

## Recommended Local Validation Flow

Use this before submission:

```powershell
.\scripts\verify_openclaw_workflow.ps1
```

Or run the checks manually:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_openclaw_payroll_review.ps1 -IncomingRoot ".\incoming_payroll" -OutputFolder ".\outputs\reviews\openclaw_submission" -OutputPrefix "openclaw_submission" -PreparedBy "OpenClaw"
python -m processors.openclaw_runtime_v1 check-env
python -m processors.openclaw_runtime_v1 check-outputs outputs/reviews/openclaw_submission openclaw_submission
python -m pytest -q
```

Expected current validation state:

```text
49 tests passing
runtime check-env passing
runtime check-outputs passing for openclaw_submission
PowerShell wrapper run passing
pip check passing
```

## Practical Judge Narrative

The simplest explanation for judges:

> OpenClaw runs the approved wrapper. The wrapper calls the payroll review CLI.
> The CLI ingests the committed current and previous payroll PDFs, generates a
> workbook, summary, receipt, and manifest, and prints a safe status message.
> OpenClaw reports from those structured outputs. It does not approve payroll or
> modify source data.

## Open Questions Before Final Submission

These are the remaining OpenClaw-specific items to confirm outside the repo:

1. Which OpenClaw version judges are expected to use.
2. Whether judges will run OpenClaw locally or inspect a demo.
3. Whether the competition expects an OpenClaw config file in the repo beyond
   `openclaw/runtime_policy.json`.
4. How OpenClaw permissions are configured in the current runtime UI/CLI.
5. Whether a short demo video should be provided showing OpenClaw running the
   wrapper and reading the receipt.

The repo is prepared for OpenClaw automation, but the external runtime setup
still needs to be validated in your own OpenClaw installation before final
submission.
