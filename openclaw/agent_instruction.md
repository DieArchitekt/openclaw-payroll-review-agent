# OpenClaw Agent Instruction

Use this instruction when asking OpenClaw to run the payroll review workflow.

```text
Run the payroll review workflow from the repository root.

Use this approved command:

powershell -ExecutionPolicy Bypass -File .\scripts\run_openclaw_payroll_review.ps1 -IncomingRoot ".\incoming_payroll" -OutputFolder ".\outputs\reviews\openclaw_submission" -OutputPrefix "openclaw_submission" -PreparedBy "OpenClaw"

After the command completes, read only these generated evidence files:

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
Do not mark payroll as exported.
Do not move, edit, delete, email, upload, or archive source files.
Do not inspect raw payroll files.
Do not install packages.
Do not run arbitrary shell commands.
```

