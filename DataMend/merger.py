"""Append and join operations for DataMend."""
from typing import Mapping, Optional

import pandas as pd


def append_dataframes(frames: Mapping[str, pd.DataFrame], *, align_columns: bool = True) -> pd.DataFrame:
    """Append rows; optionally align by the union of column names."""
    if len(frames) < 2:
        raise ValueError("Select at least two datasets to append.")
    for name, frame in frames.items():
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{name!r} is not a pandas DataFrame.")
        if frame.columns.duplicated().any():
            raise ValueError(f"{name!r} contains duplicate column names. Rename them before appending.")
    if not align_columns:
        sequences = [list(frame.columns) for frame in frames.values()]
        if any(columns != sequences[0] for columns in sequences[1:]):
            raise ValueError("Column names/order differ. Enable alignment or make the schemas consistent.")
    return pd.concat(list(frames.values()), axis=0, ignore_index=True, sort=False,
                     join="outer" if align_columns else "inner")


def join_dataframes(
    left: pd.DataFrame, right: pd.DataFrame, *, left_key: str, right_key: str,
    how: str = "left", validate: Optional[str] = None, keep_both_keys: bool = False,
) -> pd.DataFrame:
    """Join two DataFrames using selected key columns and optional validation."""
    if not isinstance(left, pd.DataFrame) or not isinstance(right, pd.DataFrame):
        raise TypeError("left and right must be pandas DataFrames.")
    if left_key not in left.columns:
        raise KeyError(f"Left key {left_key!r} is not present in the left dataset.")
    if right_key not in right.columns:
        raise KeyError(f"Right key {right_key!r} is not present in the right dataset.")
    if how not in {"left", "right", "inner", "outer"}:
        raise ValueError("how must be 'left', 'right', 'inner', or 'outer'.")
    if left.columns.duplicated().any() or right.columns.duplicated().any():
        raise ValueError("Both datasets must have unique column names before joining.")
    if left_key == right_key:
        return left.merge(right, how=how, on=left_key, validate=validate, suffixes=("_left", "_right"))
    result = left.merge(right, how=how, left_on=left_key, right_on=right_key,
                        validate=validate, suffixes=("_left", "_right"))
    if not keep_both_keys:
        result = result.drop(columns=[right_key])
    return result
