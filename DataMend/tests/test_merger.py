import pandas as pd
import pytest
from merger import append_dataframes, join_dataframes


def test_append_aligns_columns_by_name():
    first = pd.DataFrame({"id": [1], "name": ["A"]})
    second = pd.DataFrame({"name": ["B"], "score": [9]})
    result = append_dataframes({"first": first, "second": second})
    assert list(result.columns) == ["id", "name", "score"]
    assert len(result) == 2
    assert pd.isna(result.loc[1, "id"])


def test_append_requires_two_dataframes():
    with pytest.raises(ValueError):
        append_dataframes({"only": pd.DataFrame({"x": [1]})})


def test_join_left_keeps_left_rows():
    left = pd.DataFrame({"id": [1, 2], "name": ["A", "B"]})
    right = pd.DataFrame({"id": [1], "score": [90]})
    result = join_dataframes(left, right, left_key="id", right_key="id", how="left")
    assert len(result) == 2
    assert result.loc[result["id"] == 1, "score"].iloc[0] == 90
    assert pd.isna(result.loc[result["id"] == 2, "score"].iloc[0])


def test_join_validation_catches_duplicate_right_keys():
    left = pd.DataFrame({"id": [1], "name": ["A"]})
    right = pd.DataFrame({"id": [1, 1], "score": [90, 91]})
    with pytest.raises(pd.errors.MergeError):
        join_dataframes(left, right, left_key="id", right_key="id", validate="many_to_one")
