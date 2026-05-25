# OpenClaw Payroll Review Agent

[![CI](https://github.com/DieArchitekt/openclaw-payroll-review-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/DieArchitekt/openclaw-payroll-review-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)

## *Deterministic automation for payroll oversight.*

![Review output preview](docs/images/header-image.png)


## What this is
A controlled OpenClaw workflow for payroll reconciliation, exception detection, and auditable review evidence.


## How this works
OpenClaw detects payroll inputs, runs a constrained review workflow, generates structured evidence and control outputs, and returns the results for human finance review.


## Why build this

Payroll review is repetitive, time-sensitive, and operationally risky, yet still heavily dependent on manual reconciliation and fragmented evidence gathering.


## Why OpenClaw

Payroll oversight is a constrained, evidence-driven workflow that suits deterministic automation, controlled execution, and explicit operational boundaries.


## Automation Model

The scope is intentionally narrow. The agent performs deterministic tasks inside a controlled workflow and within explicit operational boundaries.

The workflow produces measurable outputs rather than subjective responses: reconciliation results, anomaly reports, manifests, receipts, and review workbooks.

The design does not rely on prompting to behave. It relies on constrained tooling, runtime policy, explicit permissions, and reproducible workflows.


## How to Run

Install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

On Windows, activate with `.\.venv\Scripts\Activate.ps1`.

Run the workflow through OpenClaw from the repository root:

```bash
corepack pnpm openclaw agent --local --agent payroll-review --message "Read openclaw/agent_instruction.md and follow it exactly."
```

This is the command used for the verified OpenClaw run shown below. It assumes
OpenClaw is installed/onboarded locally and that Node/Corepack can run `pnpm`.

The prepared OpenClaw instruction lives at `openclaw/agent_instruction.md`.

The repository includes a demonstration input pair:

```text
incoming_payroll/current.pdf
incoming_payroll/previous.pdf
```

The generated evidence is written under:

```text
outputs/reviews/openclaw_submission/
```

To run the same workflow without the OpenClaw agent, use the wrapper directly:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_openclaw_payroll_review.ps1 -IncomingRoot ".\incoming_payroll" -OutputFolder ".\outputs\reviews\local_run" -OutputPrefix "local_run" -PreparedBy "OpenClaw"
```

Or run the full local verifier:

```powershell
.\scripts\verify_openclaw_workflow.ps1
```

Validate runtime wiring:

```bash
python -m processors.openclaw_runtime_v1 check-env
python -m processors.openclaw_runtime_v1 check-outputs outputs/reviews/local_run local_run
```

For human visual inspection only, the Streamlit app can also be launched:

```bash
python -m streamlit run app/main.py
```


## Problem

Finance teams compare current payroll against previous runs, explain movements,
check exceptions, and retain approval evidence.

The work is manual. Inputs are messy. Headers vary between providers.
Evidence can be scattered.

The objective is controlled review automation: faster evidence preparation
without weakening governance.


## System

The Payroll Review Agent ingests current and previous payroll files, recognises
fields, reconciles rows, detects exceptions, and generates a local review pack.

| It is | It is not |
|---|---|
| An OpenClaw-operated review workflow | A payment release tool |
| A reconciliation and anomaly engine | A finance decision-maker |
| A local evidence pack generator | A system that sends payroll data externally |


## Agent workflow

![Architecture overview](docs/images/architecture-overview.svg)

The workflow is executed through the OpenClaw command path. The Streamlit interface is available for human visual inspection, but the project is designed around automation.

OpenClaw is the workflow layer: it runs the approved wrapper, then reports from the generated receipt and manifest.

Runtime policy: `openclaw/runtime_policy.json`.


## Design goals

- Human sign-off remains part of the process.
- Source payroll files are immutable.
- The agent prepares evidence, not decisions.
- Outputs are reproducible and auditable.
- Sensitive identifiers are minimised where possible.
- The workflow fails closed on unsafe or ambiguous inputs.
- Modules stay small, explicit, and testable.


## Payroll controls

The control checks are designed as review prompts rather than final payroll
decisions.

| Area | Examples |
|---|---|
| Employee controls | New or missing employees, leavers still paid, starters without approval, duplicate or similar names |
| Financial controls | High net pay, negative values, gross pay with zero tax or NI, bonus/overtime/commission movement |
| Compliance-oriented checks | Missing pension values, unusually low PAYE or NI against gross pay |
| Reconciliation checks | Net pay movement, employer cost movement, BACS mismatch, missing department or cost centre |


## Verified OpenClaw run outputs

The workflow was run through OpenClaw and produced a timestamped evidence set:

```text
Run status: completed_with_exceptions
Review pack generated: yes
Receipt generated: yes
Manifest generated: yes
Source files modified: false
External messages sent: false
Approval performed by agent: false
HIGH anomalies: 10
MEDIUM anomalies: 114
Recommended next action: Review HIGH anomalies before approving payroll.
```

```text
outputs/reviews/openclaw_submission/openclaw_submission_2026-05-25_212230_review.xlsx
outputs/reviews/openclaw_submission/openclaw_submission_2026-05-25_212230_summary.json
outputs/reviews/openclaw_submission/openclaw_submission_2026-05-25_212230_receipt.json
outputs/reviews/openclaw_submission/openclaw_submission_2026-05-25_212230_manifest.json
```

![Reconciliation Preview](docs/images/rec-window.png)

![Anomaly preview](docs/images/anomalies-window.png)

Receipt excerpt from the OpenClaw run:

```json
{
  "agent_mode": "read_only_review",
  "review_id": "7fc1027c-993e-40ad-9a3b-7ac7fedf2b43",
  "approval_status": "Prepared",
  "human_action_required": true,
  "recommended_next_action": "Review HIGH anomalies before approving payroll.",
  "run_status": "completed_with_exceptions",
  "source_files_modified": false,
  "external_messages_sent": false,
  "approval_performed_by_agent": false,
  "high_anomaly_count": 10,
  "medium_anomaly_count": 114,
  "total_anomaly_count": 124,
  "ready_for_review": false,
  "ready_for_approval": false
}
```

Manifest excerpt from the OpenClaw run:

```json
{
  "manifest_version": "payroll_review_manifest_v1",
  "prepared_by": "OpenClaw",
  "source_files": {
    "current_file": "current.pdf",
    "previous_file": "previous.pdf"
  },
  "anomaly_counts": {
    "high": 10,
    "medium": 114,
    "total": 124
  },
  "agent_mode": "read_only_review",
  "human_action_required": true,
  "approval_performed_by_agent": false,
  "external_messages_sent": false,
  "source_files_modified": false
}
```


## Operating boundary

| Risk | Control |
|---|---|
| Agent performs approval | Approval actions are outside agent authority |
| Source data changes | Incoming payroll files are treated as immutable |
| Evidence is disputed | Manifests include file hashes |
| Sensitive identifiers leak into summaries | Agent-facing outputs minimise sensitive values |
| Payroll data contains instructions | Text is treated as data and can be flagged |

Approval states are represented in the generated review evidence.

| Stage | Meaning |
|---|---|
| Prepared | Review pack generated |
| Reviewed | Reviewer has inspected the evidence |
| Queries raised | Exceptions require follow-up |
| Approved / Rejected | Human decision recorded |
| Exported for payment | Downstream finance process, outside agent authority |



## Repository architecture

| Area | Purpose |
|---|---|
| `app/` | Streamlit review interface |
| `gui/` | Shared UI and workbook styling |
| `processors/payroll_processor_v1/` | Extraction and field recognition |
| `processors/reconciliation_engine_v1/` | Current vs previous payroll comparison |
| `processors/anomaly_detector_v1/` | Payroll control checks |
| `processors/report_generator_v1/` | Excel review pack generation |
| `processors/approval_workflow_v1/` | Approval status model |
| `processors/agent_controls_v1/` | Receipt, redaction, and review gate controls |
| `processors/openclaw_runtime_v1/` | Runtime policy and environment validation |
| `openclaw/runtime_policy.json` | Machine-readable agent boundary |
| `openclaw/agent_instruction.md` | Prepared instruction for OpenClaw |
| `scripts/` | Wrapper scripts for OpenClaw and local automation |


## Testing

```bash
python -m black --check app gui processors tests
python -m pytest -q
python -m compileall -q app gui processors tests
```

GitHub Actions runs formatting, tests, and a CLI test using the incoming payroll files.


## Business value

The value is operational: less repetitive checking, more consistent evidence,
clearer exception visibility, and a cleaner review handoff.

A more complete product could add configurable control packs, client-specific mapping,
role-based review access, audit retention, payroll provider connectors, and
stronger BACS reconciliation.


## Limitations

- Prototype only; not production payroll approval software.
- Included demonstration PDFs only.
- Payroll rules need client-specific configuration before live use.
- OpenClaw runtime permissions must be configured outside this repository.
- Human review remains required before any payroll decision.


## Repository structure

```text
.github/
app/
docs/
gui/
incoming_payroll/
openclaw/
outputs/
processors/
scripts/
tests/
```


## Future Plans

- generate a formal report from the workbook, receipt, and
  manifest
- add configurable control packs by employer, payroll provider, or country
- support reviewer comments, query resolution, and approval history
- connect to payroll provider exports and payment/BACS files for stronger
  reconciliation
- create controlled posting files for finance systems after human approval
- add role-based access and retained audit trails
- add client-specific mapping profiles for recurring payroll formats
- improve exception prioritisation and trend analysis across payroll periods
