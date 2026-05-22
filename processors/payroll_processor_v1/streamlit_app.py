import tempfile
from pathlib import Path
from typing import Any

from gui.theme import use_streamlit_theme
from .extractor import extract_payroll
from .models import FieldMatch, PayrollExtraction, UploadedPdf
from .workbook import exported_rows, workbook_to_bytes


def default_output_name(pdf_name: str) -> str:
    """Return a sensible output filename for a PDF upload."""
    return f"{Path(pdf_name).stem}_processed.xlsx"


def write_uploaded_pdf(uploaded_file: UploadedPdf) -> Path:
    """Save an uploaded PDF to a temporary file for pdfplumber."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.write(uploaded_file.getvalue())
    temp_file.close()

    return Path(temp_file.name)


def render_streamlit_app() -> None:
    """Render the Streamlit payroll converter app."""
    import streamlit as st

    use_streamlit_theme(st)
    render_header(st)
    uploaded_file = st.file_uploader("Select a payroll PDF", type=["pdf"])

    if not uploaded_file:
        st.info("Upload a payroll PDF to begin.")
        return

    output_name: str = normalised_output_name(st.text_input("Excel filename", value=default_output_name(uploaded_file.name)))

    if st.button("Convert PDF to Excel", type="primary"):
        process_upload(st, uploaded_file, output_name)


def render_header(st: Any) -> None:
    """Render Streamlit title copy."""
    st.title("Payroll PDF to Excel Converter")
    st.caption("Recognise messy payroll fields, export the configured review workbook.")


def normalised_output_name(output_name: str) -> str:
    """Return an XLSX filename."""
    return output_name if output_name.lower().endswith(".xlsx") else f"{output_name}.xlsx"


def process_upload(st: Any, uploaded_file: UploadedPdf, output_name: str) -> None:
    """Run extraction and render Streamlit results for an uploaded PDF."""
    pdf_path: Path = write_uploaded_pdf(uploaded_file)

    try:
        with st.spinner("Reading payroll fields..."):
            extraction: PayrollExtraction = extract_payroll(pdf_path)

        render_results(st, extraction, output_name)

    except Exception as exc:
        st.error(f"Error: {exc}")

    finally:
        pdf_path.unlink(missing_ok=True)


def render_results(st: Any, extraction: PayrollExtraction, output_name: str) -> None:
    """Render extracted payroll results and workbook download."""
    if not extraction.rows:
        st.error("No payroll rows were found.")
        return

    st.success(f"Processed {len(extraction.rows)} payroll rows.")
    st.subheader("Export preview")
    st.dataframe(exported_rows(extraction.rows), use_container_width=True, hide_index=True)
    render_mapping_review(st, extraction)
    render_download(st, extraction, output_name)


def render_download(st: Any, extraction: PayrollExtraction, output_name: str) -> None:
    """Render the Streamlit XLSX download button."""
    st.download_button(
        "Download Excel",
        data=workbook_to_bytes(extraction),
        file_name=output_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_mapping_review(st: Any, extraction: PayrollExtraction) -> None:
    """Show recognised and unmapped fields in Streamlit."""
    if extraction.field_matches:
        st.subheader("Field recognition")
        st.dataframe(field_match_rows(extraction.field_matches), use_container_width=True, hide_index=True)

    if extraction.unmapped_headers:
        st.warning(f"Unmapped headers: {', '.join(extraction.unmapped_headers)}")


def field_match_rows(matches: list[FieldMatch]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly field match rows."""
    return [
        {
            "Source header": match.source_header,
            "Canonical field": match.canonical_field or "",
            "Status": match.status,
            "Confidence": match.confidence,
            "Reason": match.reason,
        }
        for match in matches
    ]
