"""DataMend — Smart Spreadsheet Cleaner & Merger."""
from pathlib import Path
from typing import Dict

import pandas as pd
import streamlit as st

from cleaner import clean_dataframe, get_data_quality_report
from merger import append_dataframes, join_dataframes
from utils import load_uploaded_file, dataframe_to_csv_bytes, dataframe_to_excel_bytes

st.set_page_config(page_title="DataMend | Spreadsheet Cleaner", page_icon="🧹", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px;}
.hero {padding: 1.5rem 1.8rem; border-radius: 18px;
background: linear-gradient(115deg, #12233f 0%, #1e4772 62%, #167c80 100%);
color: white; margin-bottom: 1rem;}
.hero h1 {font-size: 2.5rem; margin: 0 0 .25rem 0; color: white;}
.hero p {font-size: 1rem; margin: 0; color: #e5eef9;}
div[data-testid="stMetric"] {border: 1px solid rgba(110,130,160,.25); padding: 1rem; border-radius: 12px;}
</style>
<div class="hero"><h1>DataMend</h1><p>Clean your data. Connect your data. Make it useful.</p></div>
""", unsafe_allow_html=True)
st.caption("Inspect, clean, append, and join CSV and Excel spreadsheets.")

with st.sidebar:
    st.header("Workspace")
    page = st.radio("Choose an operation", ["Data overview", "Clean data", "Append files", "Join datasets"])
    st.divider()
    st.markdown("**Supported formats**")
    st.write("CSV · XLSX · XLSM")
    st.info("Review changes before downloading. Uploaded originals are not overwritten.")

uploaded_files = st.file_uploader(
    "Upload spreadsheet files", type=["csv", "xlsx", "xlsm"], accept_multiple_files=True,
    help="Upload one file to inspect or clean it, or multiple files to combine them."
)

frames: Dict[str, pd.DataFrame] = {}
if uploaded_files:
    for uploaded in uploaded_files:
        try:
            frames[uploaded.name] = load_uploaded_file(uploaded)
        except Exception as exc:
            st.error(f"Could not read **{uploaded.name}**: {exc}")

if not frames:
    st.markdown("### Start with a spreadsheet")
    st.write("Upload one or more CSV or Excel files above to see a preview and available actions.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 🔎 Inspect")
        st.write("Review dimensions, columns, missing values, and duplicates.")
    with c2:
        st.markdown("#### 🧹 Clean")
        st.write("Choose cleaning operations and preview changes.")
    with c3:
        st.markdown("#### 🔗 Combine")
        st.write("Append similar tables or join related datasets.")
    st.stop()

file_names = list(frames)
chosen_file = st.selectbox("Select a file to preview", file_names)
selected_df = frames[chosen_file]

if page == "Data overview":
    st.subheader("Data overview")
    a, b, c, d = st.columns(4)
    a.metric("Rows", f"{selected_df.shape[0]:,}")
    b.metric("Columns", f"{selected_df.shape[1]:,}")
    c.metric("Missing cells", f"{int(selected_df.isna().sum().sum()):,}")
    d.metric("Duplicate rows", f"{int(selected_df.duplicated().sum()):,}")
    st.markdown(f"**Preview — {chosen_file}**")
    st.dataframe(selected_df.head(100), use_container_width=True)
    with st.expander("Data quality details"):
        st.dataframe(get_data_quality_report(selected_df), use_container_width=True)

elif page == "Clean data":
    st.subheader("Clean a spreadsheet")
    st.write(f"Selected file: **{chosen_file}**. Choose the transformations you want to apply.")
    with st.form("cleaning_options"):
        remove_duplicates = st.checkbox("Remove exact duplicate rows", value=True)
        trim_text = st.checkbox("Trim extra spaces in text cells", value=True)
        strip_column_names = st.checkbox("Trim extra spaces in column names", value=True)
        standardize_text = st.checkbox("Standardize text capitalization (Title Case)", value=False)
        drop_empty_rows = st.checkbox("Remove rows that are completely empty", value=True)
        missing_action = st.selectbox("Missing-value handling", [
            "Keep missing values", "Drop rows with any missing value", "Fill text/numeric missing values"
        ])
        fill_text = st.text_input("Replacement for missing text values", value="Unknown")
        fill_number = st.number_input("Replacement for missing numeric values", value=0.0)
        run_clean = st.form_submit_button("Preview cleaning", type="primary")
    if run_clean:
        cleaned, summary = clean_dataframe(
            selected_df, remove_duplicates=remove_duplicates, trim_text=trim_text,
            standardize_text=standardize_text, drop_empty_rows=drop_empty_rows,
            missing_action=missing_action, fill_text=fill_text, fill_number=fill_number,
            strip_column_names=strip_column_names,
        )
        st.session_state["clean_result"] = cleaned
        st.session_state["clean_summary"] = summary
        st.session_state["clean_source"] = chosen_file
    if st.session_state.get("clean_source") == chosen_file and "clean_result" in st.session_state:
        cleaned = st.session_state["clean_result"]
        summary = st.session_state["clean_summary"]
        st.markdown("#### Before and after")
        left, right = st.columns(2)
        with left:
            st.markdown("**Original**")
            st.dataframe(selected_df.head(50), use_container_width=True)
        with right:
            st.markdown("**Cleaned preview**")
            st.dataframe(cleaned.head(50), use_container_width=True)
        st.markdown("#### Change summary")
        x, y, z = st.columns(3)
        x.metric("Rows before", summary["rows_before"])
        y.metric("Rows after", summary["rows_after"])
        z.metric("Rows removed", summary["rows_removed"])
        st.write(f"Missing cells before: **{summary['missing_before']}** · after: **{summary['missing_after']}**")
        st.download_button("Download cleaned CSV", dataframe_to_csv_bytes(cleaned),
            file_name=f"{Path(chosen_file).stem}_cleaned.csv", mime="text/csv")
        st.download_button("Download cleaned Excel", dataframe_to_excel_bytes(cleaned),
            file_name=f"{Path(chosen_file).stem}_cleaned.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif page == "Append files":
    st.subheader("Append files — stack rows")
    st.write("Use this when files contain the same kind of records. Columns are aligned by name.")
    if len(frames) < 2:
        st.warning("Upload at least two files to append them.")
    else:
        selected_names = st.multiselect("Choose files to append", file_names, default=file_names)
        align_columns = st.checkbox("Keep the union of all column names", value=True)
        if st.button("Preview appended dataset", type="primary", disabled=len(selected_names) < 2):
            try:
                result = append_dataframes({name: frames[name] for name in selected_names}, align_columns=align_columns)
                st.session_state["append_result"] = result
                st.session_state["append_signature"] = (selected_names, align_columns)
            except ValueError as exc:
                st.error(str(exc))
        if st.session_state.get("append_signature") == (selected_names, align_columns) and "append_result" in st.session_state:
            result = st.session_state["append_result"]
            st.success(f"Appended {len(selected_names)} files into {len(result):,} rows.")
            st.dataframe(result.head(100), use_container_width=True)
            st.download_button("Download appended CSV", dataframe_to_csv_bytes(result),
                file_name="datamend_appended.csv", mime="text/csv")
            st.download_button("Download appended Excel", dataframe_to_excel_bytes(result),
                file_name="datamend_appended.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif page == "Join datasets":
    st.subheader("Join datasets — connect related columns")
    st.write("Use a shared key (for example, Student ID) to combine information from two tables.")
    if len(frames) < 2:
        st.warning("Upload at least two files to join them.")
    else:
        left_name = st.selectbox("Left dataset", file_names, index=0)
        right_options = [name for name in file_names if name != left_name]
        right_name = st.selectbox("Right dataset", right_options, index=0)
        left_df, right_df = frames[left_name], frames[right_name]
        left_columns, right_columns = list(map(str, left_df.columns)), list(map(str, right_df.columns))
        common_columns = [col for col in left_columns if col in right_columns]
        left_default = common_columns[0] if common_columns else left_columns[0]
        key_left = st.selectbox("Key in left dataset", left_columns, index=left_columns.index(left_default))
        right_default = key_left if key_left in right_columns else right_columns[0]
        key_right = st.selectbox("Matching key in right dataset", right_columns, index=right_columns.index(right_default))
        join_type = st.selectbox("Join type", ["left", "inner", "outer", "right"], index=0)
        validate_keys = st.selectbox("Key relationship validation",
            ["No validation", "One-to-one", "Many-to-one", "One-to-many"],
            help="Validation can catch duplicate keys that could unexpectedly multiply rows.")
        keep_both_keys = st.checkbox("Keep both key columns when names differ", value=False)
        signature = (left_name, right_name, key_left, key_right, join_type, validate_keys, keep_both_keys)
        if st.button("Preview joined dataset", type="primary"):
            try:
                validate_map = {"No validation": None, "One-to-one": "one_to_one",
                                "Many-to-one": "many_to_one", "One-to-many": "one_to_many"}
                result = join_dataframes(left_df, right_df, left_key=key_left, right_key=key_right,
                    how=join_type, validate=validate_map[validate_keys], keep_both_keys=keep_both_keys)
                st.session_state["join_result"] = result
                st.session_state["join_signature"] = signature
            except (ValueError, KeyError, pd.errors.MergeError) as exc:
                st.error(f"Join could not be completed: {exc}")
        if st.session_state.get("join_signature") == signature and "join_result" in st.session_state:
            result = st.session_state["join_result"]
            st.success(f"Join complete: {len(result):,} rows and {len(result.columns):,} columns.")
            st.dataframe(result.head(100), use_container_width=True)
            st.download_button("Download joined CSV", dataframe_to_csv_bytes(result),
                file_name="datamend_joined.csv", mime="text/csv")
            st.download_button("Download joined Excel", dataframe_to_excel_bytes(result),
                file_name="datamend_joined.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.divider()
st.caption("DataMend MVP · Review results before exporting. Original uploaded files are not overwritten.")
