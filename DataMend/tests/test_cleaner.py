import pandas as pd
import pytest
from cleaner import clean_dataframe, get_data_quality_report


def test_quality_report_counts_missing_and_unique_values():
    df = pd.DataFrame({"name": ["A", None, "A"], "score": [1, 2, 2]})
    report = get_data_quality_report(df).set_index("column")
    assert report.loc["name", "missing_values"] == 1
    assert report.loc["name", "unique_values"] == 1


def test_quality_report_counts_whitespace_only_cells_as_missing():
    df = pd.DataFrame({"name": ["A", "   ", None]})
    report = get_data_quality_report(df).set_index("column")
    assert report.loc["name", "missing_values"] == 2


def test_cleaning_copies_input_and_removes_duplicates():
    df = pd.DataFrame({"name": ["  Amit ", "  Amit "], "score": [10, 10]})
    original = df.copy(deep=True)
    cleaned, summary = clean_dataframe(df, trim_text=True, remove_duplicates=True)
    pd.testing.assert_frame_equal(df, original)
    assert len(cleaned) == 1
    assert cleaned.loc[0, "name"] == "Amit"
    assert summary["rows_removed"] == 1


def test_fill_missing_values_by_column_type_and_whitespace():
    df = pd.DataFrame({"name": ["A", "  "], "score": [2.0, None]})
    cleaned, summary = clean_dataframe(
        df, drop_empty_rows=False, missing_action="Fill text/numeric missing values",
        fill_text="Unknown", fill_number=0,
    )
    assert cleaned.iloc[1]["name"] == "Unknown"
    assert cleaned.iloc[1]["score"] == 0
    assert summary["missing_after"] == 0


def test_strip_column_names_and_prevent_collisions():
    df = pd.DataFrame({" Student ID ": [1], "Name ": ["A"]})
    cleaned, _ = clean_dataframe(df, strip_column_names=True)
    assert list(cleaned.columns) == ["Student ID", "Name"]
    collision = pd.DataFrame({"Name": ["A"], " Name ": ["B"]})
    with pytest.raises(ValueError, match="duplicate labels"):
        clean_dataframe(collision, strip_column_names=True)
