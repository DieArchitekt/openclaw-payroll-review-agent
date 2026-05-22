import sys
from pathlib import Path


ROOT_DIR: Path = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from processors.payroll_processor_v1.streamlit_app import render_streamlit_app


render_streamlit_app()
