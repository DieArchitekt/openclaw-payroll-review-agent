# v2 changelog

rough notes for v2

## reconciliation

Added the payroll reconciliation work.

Started as `processors/reconciliation_engine.py`, then moved into:

processors/reconciliation_engine_v1/
  __init__.py
  compare.py
  constants.py
  dataframe.py
  math_utils.py
  names.py
  summary.py

Main stuff:

- normalise employee names
- turn rows into dataframes
- compare current vs previous
- mark people as Existing / New / Missing
- calculate movement on GrossPay, NetPay, PAYE, EmployerNI
- calculate summary totals

Employer cost is:

GrossPay + EmployerNI + EmployerPension

## anomaly detector

Added anomaly detection.

Now lives in:

processors/anomaly_detector_v1/
  __init__.py
  constants.py
  detector.py
  rules.py
  utils.py

Checks added:

- duplicate names
- missing employees
- new employees
- big GrossPay movement
- big NetPay movement
- big PAYE movement
- big EmployerNI movement
- big EmployerPension movement
- zero NetPay
- negative money values
- total NetPay movement
- total employer cost movement

Output is just a dataframe with Severity / Category / Employee / Field / values / message.

Severity is HIGH or MEDIUM for now.

## report generator

Added report generator after that.

Started as one file, then moved into:

processors/report_generator_v1/
  __init__.py
  constants.py
  data.py
  generator.py
  sheets.py
  styles.py

Sheets:

- Current Payroll
- Previous Payroll
- Reconciliation
- Anomalies
- Summary
- Current Field Recognition
- Previous Field Recognition

Formatting:

- bold headers
- freeze top row
- auto-size columns
- 2 decimal money columns
- HIGH rows red
- MEDIUM rows amber
- summary split into sections

## app wiring

- app/main.py
- app/ui.py
- app/payroll_review_workflow.py
- app/config.py

Flow is now:

1. upload current payroll file
2. upload previous payroll file
3. pick variance threshold
4. run review
5. see summary
6. see anomalies
7. see reconciliation
8. see current / previous payroll previews
9. see field recognition
10. download files

Downloads:

- full review pack
- anomalies csv
- reconciliation csv

## direct run fix

Running `python .\app\main.py` broke at first.

Fixed `app/main.py` so it can run direct or through Streamlit.

Commands:

python .\app\main.py
or
streamlit run .\app\main.py

## state now

It reads two payroll files, extracts rows, compares them, flags review points, and makes a review pack.