"""Reusable data-quality reporting and cleaning operations."""
from typing import Any, Dict, Tuple

import pandas as pd


def _blank_text_mask(series: pd.Series) -> pd.Series:
    """Identify string cells that are empty or contain only whitespace."""
    return series.map(lambda value: isinstance(value, str) and value.strip() == "")


def get_data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """Return one data-quality summary row per column."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    total_rows = len(df)
    missing_counts = []
    for column in df.columns:
        blank_text_count = int(_blank_text_mask(df[column]).sum())
        missing_counts.append(int(df[column].isna().sum()) + blank_text_count)

    report = pd.DataFrame({
        "column": [str(col) for col in df.columns],
        "data_type": [str(dtype) for dtype in df.dtypes],
        "missing_values": missing_counts,
        "missing_percent": [
            round(count / total_rows * 100, 2) if total_rows else 0.0
            for count in missing_counts
        ],
        "unique_values": [int(df[col].nunique(dropna=True)) for col in df.columns],
    })
    return report


def clean_dataframe(
    df: pd.DataFrame,
    *,
    remove_duplicates: bool = True,
    trim_text: bool = True,
    standardize_text: bool = False,
    drop_empty_rows: bool = True,
    missing_action: str = "Keep missing values",
    fill_text: str = "Unknown",
    fill_number: float = 0.0,
    strip_column_names: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Return a cleaned copy and summary; never mutate the input DataFrame.

    Whitespace-only text cells are normalized to missing values when trim_text
    is enabled. Column names can optionally be trimmed as well.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")
    allowed = {
        "Keep missing values",
        "Drop rows with any missing value",
        "Fill text/numeric missing values",
    }
    if missing_action not in allowed:
        raise ValueError(f"missing_action must be one of: {sorted(allowed)}")

    result = df.copy(deep=True)
    rows_before = len(result)
    missing_before = sum(
        int(result[col].isna().sum()) + int(_blank_text_mask(result[col]).sum())
        for col in result.columns
    )
    duplicates_before = int(result.duplicated().sum())

    if strip_column_names:
        stripped_names = [str(column).strip() for column in result.columns]
        if len(set(stripped_names)) != len(stripped_names):
            raise ValueError(
                "Trimming column names would create duplicate labels. Rename the conflicting columns first."
            )
        result.columns = stripped_names

    if trim_text:
        for col in result.select_dtypes(include=["object", "string"]).columns:
            result[col] = result[col].map(
                lambda value: pd.NA if isinstance(value, str) and value.strip() == ""
                else value.strip() if isinstance(value, str)
                else value
            )

    if standardize_text:
        for col in result.select_dtypes(include=["object", "string"]).columns:
            result[col] = result[col].map(
                lambda value: value.title() if isinstance(value, str) else value
            )

    if drop_empty_rows:
        result = result.dropna(how="all")

    if remove_duplicates:
        result = result.drop_duplicates()

    if missing_action == "Drop rows with any missing value":
        result = result.dropna(how="any")
    elif missing_action == "Fill text/numeric missing values":
        for col in result.columns:
            if pd.api.types.is_numeric_dtype(result[col].dtype):
                result[col] = result[col].fillna(fill_number)
            else:
                result[col] = result[col].fillna(fill_text)

    result = result.reset_index(drop=True)
    missing_after = sum(
        int(result[col].isna().sum()) + int(_blank_text_mask(result[col]).sum())
        for col in result.columns
    )
    summary = {
        "rows_before": int(rows_before),
        "rows_after": int(len(result)),
        "rows_removed": int(rows_before - len(result)),
        "duplicates_detected_before": int(duplicates_before),
        "missing_before": int(missing_before),
        "missing_after": int(missing_after),
        "columns": int(result.shape[1]),
    }
    return result, summary
