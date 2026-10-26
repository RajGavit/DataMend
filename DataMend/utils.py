"""File reading and export helpers."""
import io
from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xlsm"}


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Read a Streamlit UploadedFile or file-like object into a DataFrame."""
    name = getattr(uploaded_file, "name", "uploaded.csv")
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file extension. Supported formats: CSV, XLSX, XLSM.")
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    if suffix == ".csv":
        try:
            return pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="cp1252")
    return pd.read_excel(uploaded_file, engine="openpyxl")


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to UTF-8 CSV bytes."""
    return df.to_csv(index=False).encode("utf-8-sig")


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to an XLSX workbook in memory."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return buffer.getvalue()
