import tempfile
from pathlib import Path

from .models import UploadedFile


def write_uploaded_file(uploaded_file: UploadedFile) -> Path:
    """Save an uploaded payroll file to a temporary path."""
    suffix = Path(uploaded_file.name).suffix or ".tmp"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(uploaded_file.getvalue())
    temp_file.close()

    return Path(temp_file.name)
