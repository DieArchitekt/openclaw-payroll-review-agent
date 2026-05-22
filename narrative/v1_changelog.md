# v1 changelog

Everything implemented in v1.

## Legacy cleanup & prep

Started with two legacy files:

- `legacy/payroll_processor.py`
- `legacy/payroll_processor_gui.py`

## Theme

Moved colour and styling rules out of the payroll code.

Created: `gui/theme.py`

That file now handles the black, magenta, and ultraviolet theme for:

- Tkinter
- CLI output
- review output styling
- Streamlit CSS

payroll logic should not be full of colour values.

## Main processor

Created main processor: `processors/payroll_processor.py`

Adapted legacy tools with CLI and Streamlit support.

## Dynamic payroll v1

Built a smarter v1 processor to move away from preset headers and fixed column positions. Fuzzy > hardcoded.

The new idea is:

1. Read the payroll file.
2. Try to detect tables.
3. Find likely header rows.
4. Match messy headers to known payroll fields.
5. Keep confidence/status information.
6. Export only the chosen fields.
7. Keep recognised but ignored and unmapped fields visible for review.

The schema recognises many payroll fields, including things like:

- gross pay
- tax/PAYE
- employee NI
- employer NI
- pensions
- GU costs
- student loans
- postgraduate loans
- AEO
- absence pay
- holiday pay
- taxable pay
- benefits
- expenses
- overtime
- department and cost centre

Not every recognised field is exported. Some are only recognised so the processor can say "I saw this but it is not part of the main output."

Field statuses are:

- `exported`
- `recognised_ignored`
- `unmapped`

This makes the output more auditable.

## Removing old assumptions

Removed company-specific leftovers from the v1 path for GDPR.

The v1 processor is meant to be agnostic, not tied to a particular payroll provider or one sample file.

## Modularising v1

The first dynamic v1 file got too large. It was over 900 lines.

It was split into a package:

processors/payroll_processor_v1/
  __init__.py
  __main__.py
  app.py
  extractor.py
  field_mapper.py
  models.py
  schema.py
  streamlit_app.py
  workbook.py

The split is roughly:

- `schema.py`: known payroll fields and aliases
- `models.py`: shared dataclasses
- `field_mapper.py`: fuzzy matching and confidence scoring
- `extractor.py`: PDF/table/text extraction
- `workbook.py`: Excel output and audit sheet
- `streamlit_app.py`: Streamlit workflow
- `app.py`: Streamlit launcher
- `__main__.py`: CLI launcher
- `__init__.py`: public package surface

The main entry point is now much smaller and easier to follow.

## How to run

CLI:
```powershell
python -m processors.payroll_processor_v1 input.pdf
```

Streamlit:
```powershell
streamlit run .\processors\payroll_processor_v1\app.py
```

## Current direction

The processor is now moving toward a generic payroll ingestion tool.

The goal is to handle messy payroll files without assuming one fixed header layout, while still giving a clean review output and an audit trail of what was recognised.

## Other / Misc

Also added `v1_changelog.md` to `narrative/` and sample payroll data to `sample_data/`.
