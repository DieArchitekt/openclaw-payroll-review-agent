# How to Access

## 1. Clone and Install

```bash
git clone https://github.com/DieArchitekt/openclaw-payroll-review-agent.git
cd openclaw-payroll-review-agent
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Windows activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux activation:

```bash
source .venv/bin/activate
```

## 2. Run with OpenClaw

```bash
corepack pnpm openclaw agent --local --agent payroll-review --message "Read openclaw/agent_instruction.md and follow it exactly."
```

This assumes OpenClaw has been installed/onboarded locally and that
Node/Corepack can run `pnpm`.

Outputs are written under:

```text
outputs/reviews/openclaw_submission/
```

## 3. Direct Wrapper Fallback

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_openclaw_payroll_review.ps1 -IncomingRoot ".\incoming_payroll" -OutputFolder ".\outputs\reviews\local_run" -OutputPrefix "local_run" -PreparedBy "OpenClaw"
```

macOS/Linux:

```bash
bash ./scripts/run_openclaw_payroll_review.sh --incoming-root ./incoming_payroll --output-folder ./outputs/reviews/local_run --output-prefix local_run --prepared-by OpenClaw
```

## 4. Check Outputs

```text
outputs/reviews/local_run/local_run_review.xlsx
outputs/reviews/local_run/local_run_summary.json
outputs/reviews/local_run/local_run_receipt.json
outputs/reviews/local_run/local_run_manifest.json
```

Validate:

```bash
python -m processors.openclaw_runtime_v1 check-env
python -m processors.openclaw_runtime_v1 check-outputs outputs/reviews/local_run local_run
```

## Optional

Prepared OpenClaw instruction:

```text
openclaw/agent_instruction.md
```

Streamlit inspection:

```bash
python -m streamlit run app/main.py
```
