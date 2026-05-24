# Payroll Review Agent

Payroll Review Agent reviews current payroll data against a previous payroll file,
flags review exceptions, and produces an approval workbook plus JSON summaries for
automation.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Run the Streamlit app

```bash
python -m streamlit run app/main.py
```

## Run the CLI

```bash
python -m processors.payroll_review_cli \
  sample_data/payroll_controls_current.csv \
  sample_data/payroll_controls_previous.csv \
  --output-dir outputs/reviews/local \
  --output-prefix sample_local \
  --prepared-by "Local Review"
```

The root `payroll_review_cli.py` file is kept as a small convenience wrapper,
but CI and automation should prefer the module command above.

## Check the project

```bash
python -m black --check app gui processors tests payroll_review_cli.py
python -m pytest -q
python -m compileall -q app gui processors tests payroll_review_cli.py
```
