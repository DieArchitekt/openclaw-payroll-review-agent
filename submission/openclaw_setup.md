# OpenClaw Setup Guide

This guide explains how to set up and test OpenClaw with this payroll review
project from scratch.

It is written for a beginner. Follow it slowly and verify each checkpoint before
moving on.

## Current Repo Status

The repo-side submission changes are implemented.

The README now reflects the OpenClaw-first workflow:

- `incoming_payroll/current.pdf` and `incoming_payroll/previous.pdf` are the
  committed input files.
- `sample_data/` has been removed.
- `screenshots/` has been removed.
- README images live in `docs/images/`.
- The main run path is the OpenClaw wrapper script.
- Streamlit is presented as secondary visual inspection only.
- `incoming_payroll/` and `outputs/` are not ignored.
- Runtime validation expects the flat incoming payroll model.
- CI uses `incoming_payroll/`.

What is not implemented inside the repo:

- OpenClaw itself
- OpenClaw account/runtime setup
- model/API provider credentials
- OpenClaw daemon/service installation
- OpenClaw workspace permission configuration

That is expected. OpenClaw is an external runtime. This repo provides the
workflow, command surface, runtime policy, inputs, and outputs.

## Official References

Use the official OpenClaw documentation as the source of truth if commands
change:

- OpenClaw install docs: `https://docs.openclaw.ai/install/index`
- DataVita OpenClaw Challenge page:
  `https://jobs.datavita.co.uk/openclaw-challenge`

The OpenClaw docs list Node as a system requirement and show install paths such
as:

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

The DataVita challenge page also shows the same basic install/onboard flow.

## Mental Model

OpenClaw is not the payroll engine.

In this project:

```text
OpenClaw = workflow orchestration layer
repo = constrained payroll review tooling
```

OpenClaw should:

- run the approved wrapper script
- wait for completion
- read generated JSON evidence
- report status and blockers

OpenClaw should not:

- approve payroll
- edit source payroll files
- move or delete source files
- send payroll data externally
- inspect raw payroll rows unless you explicitly allow that for a demo

## Prerequisites

Install these first:

- Git
- Python 3.12
- Node.js supported by your OpenClaw install route
- npm
- an LLM/model provider API key, if OpenClaw asks for one

For this repo, Python dependencies are installed with:

```bash
python -m pip install -r requirements-dev.txt
```

For OpenClaw, follow the current official install docs.

## Step 1: Clone and Prepare the Repo

Clone the project:

```bash
git clone <your-repo-url>
cd openclaw-payroll-review-agent
```

Create a Python environment:

```bash
python -m venv .venv
```

Activate it.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Verify dependencies:

```bash
python -m pip check
```

Expected result:

```text
No broken requirements found.
```

## Step 2: Confirm Input Files Exist

Check that these files exist:

```text
incoming_payroll/current.pdf
incoming_payroll/previous.pdf
```

PowerShell:

```powershell
Test-Path .\incoming_payroll\current.pdf
Test-Path .\incoming_payroll\previous.pdf
```

Expected result:

```text
True
True
```

If either file is missing, the OpenClaw workflow will fail.

## Step 3: Run the Workflow Without OpenClaw First

Before involving OpenClaw, run the exact wrapper command OpenClaw will call.

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_openclaw_payroll_review.ps1 -IncomingRoot ".\incoming_payroll" -OutputFolder ".\outputs\reviews\openclaw_submission" -OutputPrefix "openclaw_submission" -PreparedBy "OpenClaw"
```

Expected console output should look like:

```text
Payroll review completed.

Review ID: <id>
Approval status: Prepared
Run status: completed_with_exceptions
Review pack: <path>\outputs\reviews\openclaw_submission\openclaw_submission_review.xlsx
High exceptions: 10
Medium exceptions: 114
Total exceptions: 124

Recommended next action: Review HIGH anomalies before approving payroll.
```

The exact review ID may differ.

Expected output files:

```text
outputs/reviews/openclaw_submission/openclaw_submission_review.xlsx
outputs/reviews/openclaw_submission/openclaw_submission_summary.json
outputs/reviews/openclaw_submission/openclaw_submission_receipt.json
outputs/reviews/openclaw_submission/openclaw_submission_manifest.json
```

## Step 4: Validate the Runtime Contract

Run:

```bash
python -m processors.openclaw_runtime_v1 check-env
```

Expected result:

```json
{
  "ok": true,
  "errors": [],
  "warnings": []
}
```

Then validate the generated output set:

```bash
python -m processors.openclaw_runtime_v1 check-outputs outputs/reviews/openclaw_submission openclaw_submission
```

Expected result:

```json
{
  "ok": true,
  "errors": [],
  "warnings": []
}
```

If this fails, OpenClaw should not be considered ready yet.

## Step 5: Install OpenClaw

Use the official OpenClaw documentation for the latest install route.

The commonly documented npm path is:

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

During onboarding, OpenClaw may ask for:

- model provider
- API key
- default model
- workspace or channel setup
- daemon/background service setup

Use your own provider credentials. Do not put API keys in this repo.

After installation, try:

```bash
openclaw --version
```

Depending on the installed version, these may also be available:

```bash
openclaw doctor
openclaw status
openclaw health
openclaw dashboard
```

If a command is unavailable, check the current OpenClaw docs for the equivalent.

## Step 6: Configure OpenClaw Workspace

OpenClaw needs to operate from this repo root:

```text
openclaw-payroll-review-agent/
```

The important paths are:

```text
incoming_payroll/current.pdf
incoming_payroll/previous.pdf
scripts/run_openclaw_payroll_review.ps1
scripts/run_openclaw_payroll_review.sh
openclaw/runtime_policy.json
outputs/reviews/
```

If OpenClaw asks for workspace access:

- allow this repository folder
- do not grant broad access to your desktop or documents
- do not grant access to `real_data/`
- do not grant email/upload permissions for this demo

The goal is to let OpenClaw run one approved local workflow, not browse your
machine.

## Step 7: Give OpenClaw the Approved Task

The safest mitigation is simple:

1. Run the local verifier yourself first.
2. Then ask OpenClaw to perform the same workflow using
   `openclaw/agent_instruction.md`.

```powershell
.\scripts\verify_openclaw_workflow.ps1
```

If that command does not pass locally, do not ask OpenClaw to run the workflow
yet. Fix the local issue first.

Use this prompt/instruction:

The same instruction is stored at:

```text
openclaw/agent_instruction.md
```

```text
Run the payroll review workflow from the repository root using the approved
wrapper script.

Use incoming_payroll as the input folder.

Run:
powershell -ExecutionPolicy Bypass -File .\scripts\run_openclaw_payroll_review.ps1 -IncomingRoot ".\incoming_payroll" -OutputFolder ".\outputs\reviews\openclaw_submission" -OutputPrefix "openclaw_submission" -PreparedBy "OpenClaw"

After completion, read only:
- outputs/reviews/openclaw_submission/openclaw_submission_receipt.json
- outputs/reviews/openclaw_submission/openclaw_submission_summary.json
- outputs/reviews/openclaw_submission/openclaw_submission_manifest.json
- openclaw/runtime_policy.json

Report:
- run_status
- review_pack
- high_anomaly_count
- medium_anomaly_count
- total_anomaly_count
- blockers
- recommended_next_action

Do not approve payroll.
Do not reject payroll.
Do not move, edit, delete, email, upload, or archive source files.
Do not inspect raw payroll files.
```

For Bash/macOS/Linux, replace the command with:

```bash
bash ./scripts/run_openclaw_payroll_review.sh --incoming-root ./incoming_payroll --output-folder ./outputs/reviews/openclaw_submission --output-prefix openclaw_submission --prepared-by OpenClaw
```

## Step 8: Check What OpenClaw Reports

OpenClaw should report something close to:

```text
Run status: completed_with_exceptions
Review pack: outputs/reviews/openclaw_submission/openclaw_submission_review.xlsx
High exceptions: 10
Medium exceptions: 114
Total exceptions: 124
Recommended next action: Review HIGH anomalies before approving payroll.
```

It should not report payroll row-level values unless you deliberately allowed
that.

It should not say payroll is approved.

It should not say files were sent externally.

## Step 9: Verify Safety Flags

Open:

```text
outputs/reviews/openclaw_submission/openclaw_submission_receipt.json
```

Check:

```json
{
  "agent_mode": "read_only_review",
  "human_action_required": true,
  "source_files_modified": false,
  "external_messages_sent": false,
  "approval_performed_by_agent": false
}
```

Open:

```text
outputs/reviews/openclaw_submission/openclaw_submission_manifest.json
```

Check that it includes hashes for:

- current file
- previous file
- review workbook
- summary JSON
- receipt JSON

Then re-run:

```bash
python -m processors.openclaw_runtime_v1 check-outputs outputs/reviews/openclaw_submission openclaw_submission
```

## Step 10: Run the Full Local Verification Suite

Before submitting, run:

```powershell
.\scripts\verify_openclaw_workflow.ps1
```

Then run the general checks:

```bash
python -m black --check app gui processors tests
python -m pytest -q
python -m compileall -q app gui processors tests
python -m pip check
python -m processors.openclaw_runtime_v1 check-env
python -m processors.openclaw_runtime_v1 check-outputs outputs/reviews/openclaw_submission openclaw_submission
```

Expected current state:

```text
49 tests passing
Black check passing
compileall passing
pip check passing
runtime check-env passing
runtime check-outputs passing
```

## How To Explain This To Judges

Short version:

```text
OpenClaw runs the approved wrapper script. The wrapper calls the payroll review
CLI. The CLI ingests the committed current and previous payroll PDFs, generates
a workbook plus JSON evidence, and prints a safe status message. OpenClaw then
reports from the receipt and manifest. It does not approve payroll or modify
source files.
```

## Troubleshooting

### `openclaw` command not found

Likely causes:

- OpenClaw did not install globally
- npm global bin folder is not on `PATH`
- terminal was not restarted after install

Try:

```bash
npm list -g --depth=0
```

Then check the official OpenClaw install troubleshooting for your OS.

### OpenClaw asks for an API key

That is expected.

Use a model provider key configured in OpenClaw. Do not put it in this repo.

### Wrapper fails with missing Python dependencies

Activate the venv and reinstall:

```bash
python -m pip install -r requirements-dev.txt
```

Then retry the wrapper.

### Runtime check says incoming files are missing

Confirm:

```text
incoming_payroll/current.pdf
incoming_payroll/previous.pdf
```

The files must be named exactly like that for this submission workflow.

### Output validation fails

Most likely causes:

- wrong output folder
- wrong prefix
- wrapper failed before completing
- files were generated with timestamped fallback names because matching files
  already existed

Use a clean folder/prefix:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_openclaw_payroll_review.ps1 -IncomingRoot ".\incoming_payroll" -OutputFolder ".\outputs\reviews\fresh_openclaw_test" -OutputPrefix "fresh_openclaw_test" -PreparedBy "OpenClaw"
python -m processors.openclaw_runtime_v1 check-outputs outputs/reviews/fresh_openclaw_test fresh_openclaw_test
```

### OpenClaw tries to read raw payroll files

Redirect it to the safe outputs:

```text
Use the receipt, summary, and manifest only. Do not inspect raw payroll files.
```

The repo policy file blocks raw incoming payroll reads conceptually:

```text
openclaw/runtime_policy.json
```

Actual enforcement depends on how the OpenClaw runtime permissions are
configured locally.

## Final Pre-Submission Checklist

- [ ] OpenClaw installed locally.
- [ ] OpenClaw onboarding completed.
- [ ] API/model credentials configured outside the repo.
- [ ] Repo selected as OpenClaw workspace.
- [ ] Wrapper command approved.
- [ ] OpenClaw run completed successfully.
- [ ] Receipt and manifest read by OpenClaw.
- [ ] OpenClaw did not approve payroll.
- [ ] OpenClaw did not move or edit source files.
- [ ] Runtime validation passed.
- [ ] Tests passed.
- [ ] CI passed on GitHub.
- [ ] README instructions match the final workflow.
