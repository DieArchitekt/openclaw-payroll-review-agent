# Submission Readiness Plan

Purpose: make the repository straightforward for judges to clone, inspect, and
run as an OpenClaw automation workflow.

This project should not present OpenClaw as optional. Streamlit is available for
human visual inspection, but the submission is the OpenClaw-driven payroll
review workflow.

## Target Judge Experience

A judge should be able to:

1. Clone the repository.
2. Install Python dependencies.
3. Confirm the incoming payroll files are present.
4. Run the OpenClaw wrapper command.
5. Inspect generated outputs.
6. Validate the receipt and manifest.
7. Understand how to connect the same command surface to a local OpenClaw
   runtime.

The ideal experience is deterministic and boring in the best way: one input
folder, one approved command path, one review pack, one receipt, one manifest.

## Repository Input Model

The project now uses a flat incoming folder:

```text
incoming_payroll/
  current.pdf
  previous.pdf
```

For the competition:

- `current.pdf` is the May payroll file.
- `previous.pdf` is the April payroll file.
- The system expects only those two payroll input files in `incoming_payroll/`.

The old model with `incoming_payroll/current/` and
`incoming_payroll/previous/` subfolders is no longer the judge-facing workflow.

## What Was Removed

The repo should no longer depend on:

- `sample_data/`
- sample CSV files
- sample Excel files
- incoming payroll subfolders
- arbitrary `screenshots/` folder

Supporting README images should live in:

```text
docs/images/
```

## Git Tracking Decision

### `incoming_payroll/`

Do not ignore `incoming_payroll/`.

The two competition input PDFs should be committed:

```text
incoming_payroll/current.pdf
incoming_payroll/previous.pdf
```

This makes the OpenClaw wrapper command work from a fresh clone without asking
judges to move files around first.

### `outputs/`

Do not ignore `outputs/`.

For this submission, committed outputs help judges see what a successful run
produces. Keep empty output folders with `.gitkeep` where needed:

```text
outputs/agent/.gitkeep
outputs/audit/.gitkeep
outputs/reviews/.gitkeep
```

Before final submission, review the contents of `outputs/` and remove noisy
local experiment runs if they do not help judging.

Suggested committed example output:

```text
outputs/reviews/openclaw_submission/
  openclaw_submission_review.xlsx
  openclaw_submission_summary.json
  openclaw_submission_receipt.json
  openclaw_submission_manifest.json
```

## Primary Run Path

The main run path should be the OpenClaw wrapper.

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_openclaw_payroll_review.ps1 -IncomingRoot ".\incoming_payroll" -OutputFolder ".\outputs\reviews\openclaw_submission" -OutputPrefix "openclaw_submission" -PreparedBy "OpenClaw"
```

Bash:

```bash
bash ./scripts/run_openclaw_payroll_review.sh --incoming-root ./incoming_payroll --output-folder ./outputs/reviews/openclaw_submission --output-prefix openclaw_submission --prepared-by OpenClaw
```

Validation:

```bash
python -m processors.openclaw_runtime_v1 check-env
python -m processors.openclaw_runtime_v1 check-outputs outputs/reviews/openclaw_submission openclaw_submission
```

## Secondary Inspection Path

Streamlit is only for human visual inspection:

```bash
python -m streamlit run app/main.py
```

The README should make clear that the product is judged as an automation
workflow, not as a dashboard-first app.

## OpenClaw Runtime Setup

The repo does not include OpenClaw itself. OpenClaw is an external agent runtime
that needs to be installed and configured locally.

The DataVita OpenClaw Challenge page describes OpenClaw as a free open-source
agent and shows an installation/onboarding path similar to:

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

Exact setup may depend on the current OpenClaw documentation and the model
provider being used.

## What OpenClaw Should Be Configured To Do

OpenClaw should:

1. Use the repository root as its working directory.
2. Treat `scripts/run_openclaw_payroll_review.ps1` or
   `scripts/run_openclaw_payroll_review.sh` as the approved command.
3. Run the wrapper against `incoming_payroll/`.
4. Read only generated safe outputs:
   - summary JSON
   - receipt JSON
   - manifest JSON
   - runtime policy
5. Report status, blockers, and recommended next action.

OpenClaw should not:

- approve payroll
- reject payroll
- mark payroll as exported
- send files externally
- delete or move source files
- install packages
- run arbitrary shell commands outside the approved wrappers

Those boundaries are represented in:

```text
openclaw/runtime_policy.json
```

## Local OpenClaw Validation Before Submission

Before submitting, validate your own OpenClaw setup end to end:

1. Install and onboard OpenClaw locally.
2. Configure model/API credentials in OpenClaw, not in this repo.
3. Clone or open this repository as the OpenClaw workspace.
4. Confirm `incoming_payroll/current.pdf` and `incoming_payroll/previous.pdf`
   are present.
5. Give OpenClaw the approved wrapper command.
6. Run the review.
7. Confirm the review workbook, summary, receipt, and manifest are generated.
8. Confirm OpenClaw reports from the receipt/manifest rather than raw payroll
   file contents.
9. Confirm no source files are moved, deleted, edited, or sent.

Suggested OpenClaw instruction:

```text
Run the payroll review workflow using the approved wrapper script. Use the
incoming_payroll folder as input. After completion, read the generated receipt
and manifest only. Report run_status, blocker count, high anomaly count, medium
anomaly count, recommended_next_action, and review workbook path. Do not approve
payroll or modify source files.
```

## Secrets and API Keys

Do not commit:

- OpenClaw tokens
- OpenAI, Anthropic, or other model provider keys
- `.env`
- real payroll data

Credentials belong in the local OpenClaw/model provider environment.

Current `.gitignore` should keep `.env` and `real_data/` out of version control.

## Requirements Check

Current dependency files should be simple and installable:

```text
requirements.txt
requirements-dev.txt
```

Before final submission, run:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip check
```

Then run:

```bash
python -m black --check app gui processors tests
python -m pytest -q
python -m compileall -q app gui processors tests
```

If dependency versions fail on a fresh machine or GitHub Actions, loosen only
the minimum necessary pins.

## CI Expectations

CI should use the committed incoming PDFs, not deleted sample files.

Expected CI smoke path:

```bash
python -m processors.payroll_review_cli --incoming-root incoming_payroll --output-dir outputs/reviews/ci --output-prefix sample_ci --prepared-by CI
```

CI should verify:

- install dependencies
- Black formatting
- tests
- CLI smoke run

## Final Repo Checklist

- [ ] `incoming_payroll/current.pdf` exists.
- [ ] `incoming_payroll/previous.pdf` exists.
- [ ] No `sample_data/` folder remains.
- [ ] No `screenshots/` folder remains.
- [ ] README image paths point to `docs/images/`.
- [ ] `.gitignore` does not ignore `incoming_payroll/`.
- [ ] `.gitignore` does not ignore `outputs/`.
- [ ] Empty output folders have `.gitkeep`.
- [ ] README run command uses the OpenClaw wrapper.
- [ ] CI smoke test uses `incoming_payroll/`.
- [ ] Runtime validation passes.
- [ ] Tests pass.
- [ ] Formatting passes.
- [ ] No secrets are committed.
- [ ] OpenClaw runtime setup has been tested locally by you.

## Remaining Risk

The main unresolved question is external OpenClaw setup for the judges.

The repo can make its command surface, runtime policy, inputs, and outputs
clear. It cannot bundle the judge's OpenClaw installation, model credentials, or
local agent permissions.

To reduce that risk:

1. Keep the README OpenClaw-first.
2. Add a short `submission/openclaw_judge_runbook.md` if needed.
3. Record a short demo of OpenClaw running the wrapper locally.
4. Confirm the GitHub repo works without hidden local files.
5. Confirm CI is green after the final push.

