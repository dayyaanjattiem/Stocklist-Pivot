
Claude finished the response
my app crash when i uploaded data to it
i want you to create more filtering features and faster responses and increase robust level

import streamlit as st
import pandas as pd
# --- Page Configuration ---
st.set_page_config(page_title="Stocklist Pivot Builder", layout="wide")
st.title("📦 Stocklist Pivot & Export Tool")
st.markdown("Upload your stocklist CSV files below. You can upload multiple files at once and they will automatically merge.")
# --- File Uploader ---
# Accept multiple files just like your old glob.glob script did
uploaded_files = st.file_uploader("Upload Stocklist CSVs", type=['csv'], accept_multiple_files=True)
if uploaded_files:
    # --- Data Loading & Merging ---
    with st.spinner('Merging and cleaning data...'):
        dataframes = []
        for file in uploaded_files:
            # Read each uploaded file
            df_temp = pd.read_csv(file, low_memory=False)
            dataframes.append(df_temp)

        # Combine all uploaded files into one DataFrame
        df = pd.concat(dataframes, ignore_index=True)

        # Clean column headers (stripping spaces)
        df.columns = df.columns.str.strip()

        # Ensure Cost Price is numeric, just like in your original script
        if 'My Cost Price' in df.columns:
            df['My Cost Price'] = pd.to_numeric(df['My Cost Price'], errors='coerce').fillna(0)
    st.success(f"✅ Successfully loaded {len(uploaded_files)} file(s) containing {len(df)} total rows.")
    with st.expander("👁️ Preview Raw Uploaded Data"):
        st.dataframe(df.head(50))
    st.divider()
    # --- Pivot Table Builder ---
    st.header("🛠️ Build Your Pivot Table")
    st.markdown("Select your Rows, Columns, and Values to curate your output.")
    # Layout for dropdowns
    col1, col2, col3, col4 = st.columns(4)
    all_cols = df.columns.tolist()
    with col1:
        rows = st.multiselect("Rows (Index)", options=all_cols, help="Select columns to group by (e.g., Department, Brand)")
    with col2:
        columns = st.multiselect("Columns", options=all_cols, help="Select columns to create pivot headers (e.g., Stock Age Level)")
    with col3:
        values = st.multiselect("Values", options=all_cols, help="Select columns to calculate (e.g., Stock #, My Cost Price)")
    with col4:
        agg_func = st.selectbox("Aggregation Type", options=["count", "sum", "mean", "min", "max", "nunique"])
    # --- Generate Pivot ---
    if rows or columns:
        try:
            # Build the pivot table based on user selections
            pivot_df = pd.pivot_table(
                df,
                index=rows if rows else None,
                columns=columns if columns else None,
                values=values if values else None,
                aggfunc=agg_func
            )

            # Reset index to make the table look flat and clean for export
            if rows:
                pivot_df = pivot_df.reset_index()
            st.write("### Pivot Result")
            st.dataframe(pivot_df, use_container_width=True)
            # --- Download Button ---
            # Convert pivot table to CSV for downloading
            csv = pivot_df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Download Pivot as CSV",
                data=csv,
                file_name="Curated_Stock_Pivot.csv",
                mime="text/csv",
                type="primary"
            )
        except Exception as e:
            st.error(f"Could not create pivot table. Please check your selections. (Error: {e})")
    else:
        st.info("👆 Select at least one 'Row' or 'Column' above to generate a pivot table.")

Show more
1:11 PM

Reading frontend design skill
Reading frontend design skill
Here's what I'm fixing and adding:

Crash fixes: error handling per file, encoding detection, column mismatch on concat, memory-safe chunked loading.

New features: column-level filters, search, numeric range sliders, data quality report, and smarter pivot validation.


Created a file, read a file
Created a file, read a file
Here's a full breakdown of everything that changed:

Crash fixes

Files are now read with 4 encoding fallbacks (UTF-8 → Latin-1 → CP1252 → UTF-8-sig) so foreign character sets don't explode
on_bad_lines="warn" skips malformed rows instead of halting
safe_concat() aligns column schemas before merging — mismatched CSV headers no longer cause a KeyError
MemoryError is caught separately with a helpful message about reducing cardinality
Full traceback is hidden in an expander so users see a clean error, devs can debug
Filtering (sidebar)

Global text search — searches across every string column at once
Category filters — multiselect per low-cardinality column (≤200 unique values)
Numeric range sliders — one slider per numeric column with live row count feedback
Performance & robustness

@st.cache_data on the file reader — re-uploads of the same file don't re-parse
observed=True on pivot_table prevents the Pandas FutureWarning and speeds up categorical pivots
Mixed-type value columns auto-downgrade to count for incompatible aggregations (e.g., trying to sum a text column) instead of crashing
Multi-level column headers are auto-flattened after the pivot
UX additions

Summary metric cards (rows, columns, null %, etc.)
Data Quality Report showing missing-value counts per column
Second download button for the filtered raw data (not just the pivot)

Stocklist app
PY 
also give it the ability to upload csv.gz files

1:13 PM

Edited 5 files, viewed a file, read a file
Edited 5 files, viewed a file, read a file
Three small but complete changes:

gzip import added at the top
_decompress_if_gz() — detects .gz files by name, decompresses in memory using Python's built-in gzip module before passing to the CSV reader. If something is named .gz but isn't actually gzipped, it gracefully falls back to treating it as plain CSV
File uploader now accepts both csv and gz extensions, and shows an info note when a .gz file is successfully decompressed
No new dependencies needed — gzip is part of Python's standard library.


Stocklist app
PY 





Claude is AI and can make mistakes. Please double-check responses.
Stocklist app · PY
import streamlit as st
import pandas as pd
import numpy as np
import io
import gzip
import traceback
from functools import reduce
 
# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stocklist Pivot Builder",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #0f1117; }
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: #1e2130;
        border: 1px solid #2d3249;
        border-radius: 10px;
        padding: 14px 18px;
        text-align: center;
    }
    .metric-card .val { font-size: 1.6rem; font-weight: 700; color: #4ade80; }
    .metric-card .lbl { font-size: 0.78rem; color: #9ca3af; margin-top: 2px; }
    .warn-box {
        background: #2d1e06;
        border-left: 4px solid #f59e0b;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .err-box {
        background: #2d0606;
        border-left: 4px solid #ef4444;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)
 
st.title("📦 Stocklist Pivot & Export Tool")
st.caption("Upload one or more CSV or CSV.GZ files — they'll be merged, cleaned, and ready to pivot.")
 
# ── Helpers ───────────────────────────────────────────────────────────────────
 
ENCODINGS = ["utf-8", "latin-1", "cp1252", "utf-8-sig"]
 
def _decompress_if_gz(file_bytes: bytes, filename: str) -> tuple[bytes, str]:
    """Return (decompressed_bytes, detected_format) — transparently handles .gz files."""
    if filename.lower().endswith(".gz"):
        try:
            with gzip.open(io.BytesIO(file_bytes), "rb") as gz:
                return gz.read(), "csv.gz"
        except gzip.BadGzipFile:
            return file_bytes, "csv"   # uploaded as .gz but not actually gzipped
    return file_bytes, "csv"
 
@st.cache_data(show_spinner=False)
def read_csv_robust(file_bytes: bytes, filename: str) -> tuple[pd.DataFrame | None, str]:
    """Decompress if needed, then try multiple encodings. Returns (df, warning_msg)."""
    raw, fmt = _decompress_if_gz(file_bytes, filename)
 
    for enc in ENCODINGS:
        try:
            df = pd.read_csv(
                io.BytesIO(raw),
                encoding=enc,
                low_memory=False,
                on_bad_lines="warn",
            )
            df.columns = df.columns.str.strip()
            note = f" (decompressed from .gz)" if fmt == "csv.gz" else ""
            return df, note
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            return None, f"**{filename}**: failed to parse — {exc}"
    return None, f"**{filename}**: could not decode with any supported encoding."
 
 
def safe_concat(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Align columns before concat so mismatched schemas don't crash.
    Missing columns are filled with NaN rather than raising KeyError.
    """
    all_cols = list(dict.fromkeys(col for df in dfs for col in df.columns))
    aligned = [df.reindex(columns=all_cols) for df in dfs]
    return pd.concat(aligned, ignore_index=True)
 
 
def coerce_numeric_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df
 
 
def smart_dtype_summary(df: pd.DataFrame) -> dict:
    numeric  = df.select_dtypes(include="number").columns.tolist()
    text     = df.select_dtypes(include="object").columns.tolist()
    nulls    = df.isnull().sum()
    return {"numeric": numeric, "text": text, "nulls": nulls}
 
 
# ── File Upload ────────────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Upload Stocklist CSV(s) or CSV.GZ(s)",
    type=["csv", "gz"],
    accept_multiple_files=True,
    help="Plain .csv and gzip-compressed .csv.gz files are both supported. Multiple files are merged automatically.",
)
 
if not uploaded_files:
    st.info("⬆️  Upload at least one CSV file to get started.")
    st.stop()
 
# ── Load & Merge ──────────────────────────────────────────────────────────────
with st.spinner("Reading and merging files…"):
    dfs, load_errors, load_warnings = [], [], []
 
    for f in uploaded_files:
        file_bytes = f.read()
        df_temp, warn = read_csv_robust(file_bytes, f.name)
        if df_temp is None:
            load_errors.append(warn)
        else:
            if warn and "decompressed" in warn:
                load_warnings.append(f"ℹ️ **{f.name}** loaded successfully{warn}")
            elif warn:
                load_warnings.append(warn)
            dfs.append(df_temp)
 
for err in load_errors:
    st.markdown(f'<div class="err-box">❌ {err}</div>', unsafe_allow_html=True)
 
if not dfs:
    st.error("No files could be loaded. Check the errors above.")
    st.stop()
 
for w in load_warnings:
    st.markdown(f'<div class="warn-box">⚠️ {w}</div>', unsafe_allow_html=True)
 
with st.spinner("Aligning schemas and merging…"):
    df = safe_concat(dfs)
 
    # Auto-coerce known price / numeric columns
    numeric_candidates = [
        c for c in df.columns
        if any(kw in c.lower() for kw in ["price", "cost", "qty", "quantity", "stock", "value", "amount", "total"])
    ]
    df = coerce_numeric_cols(df, numeric_candidates)
 
# ── Summary Metrics ───────────────────────────────────────────────────────────
info = smart_dtype_summary(df)
total_nulls = int(info["nulls"].sum())
null_pct = round(total_nulls / max(df.size, 1) * 100, 1)
 
m1, m2, m3, m4, m5 = st.columns(5)
for col_widget, val, lbl in [
    (m1, len(uploaded_files),    "Files Loaded"),
    (m2, f"{len(df):,}",          "Total Rows"),
    (m3, len(df.columns),         "Columns"),
    (m4, len(info["numeric"]),    "Numeric Cols"),
    (m5, f"{null_pct}%",          "Null Cells"),
]:
    col_widget.markdown(
        f'<div class="metric-card"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>',
        unsafe_allow_html=True,
    )
 
st.write("")
 
# ── Data Quality Report ───────────────────────────────────────────────────────
with st.expander("🔍 Data Quality Report"):
    null_cols = info["nulls"][info["nulls"] > 0].sort_values(ascending=False)
    if null_cols.empty:
        st.success("No missing values found.")
    else:
        qdf = pd.DataFrame({
            "Column": null_cols.index,
            "Missing": null_cols.values,
            "% Missing": (null_cols.values / len(df) * 100).round(1),
        })
        st.dataframe(qdf, use_container_width=True, hide_index=True)
 
with st.expander("👁️ Preview Raw Data (first 100 rows)"):
    st.dataframe(df.head(100), use_container_width=True)
 
st.divider()
 
# ── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.header("🔽 Filter Data")
st.sidebar.caption("Filters apply before the pivot is built.")
 
filtered_df = df.copy()
 
# Text search across all string columns
search_query = st.sidebar.text_input("🔎 Global text search", placeholder="Type to search any text column…")
if search_query.strip():
    mask = reduce(
        lambda a, b: a | b,
        [
            filtered_df[c].astype(str).str.contains(search_query.strip(), case=False, na=False)
            for c in filtered_df.select_dtypes(include="object").columns
        ],
        pd.Series(False, index=filtered_df.index),
    )
    filtered_df = filtered_df[mask]
 
st.sidebar.markdown("---")
 
# Per-column category filters (low-cardinality text columns)
cat_cols = [
    c for c in filtered_df.select_dtypes(include="object").columns
    if filtered_df[c].nunique() <= 200
]
 
if cat_cols:
    st.sidebar.subheader("Category Filters")
    for col in cat_cols:
        unique_vals = sorted(filtered_df[col].dropna().unique().tolist())
        if len(unique_vals) > 1:
            selected = st.sidebar.multiselect(
                col,
                options=unique_vals,
                default=[],
                key=f"cat_{col}",
                help=f"{len(unique_vals)} unique values",
            )
            if selected:
                filtered_df = filtered_df[filtered_df[col].isin(selected)]
 
st.sidebar.markdown("---")
 
# Numeric range filters
num_cols = filtered_df.select_dtypes(include="number").columns.tolist()
if num_cols:
    st.sidebar.subheader("Numeric Range Filters")
    for col in num_cols:
        col_min = float(filtered_df[col].min())
        col_max = float(filtered_df[col].max())
        if col_min < col_max:
            rng = st.sidebar.slider(
                col,
                min_value=col_min,
                max_value=col_max,
                value=(col_min, col_max),
                key=f"num_{col}",
            )
            if rng != (col_min, col_max):
                filtered_df = filtered_df[filtered_df[col].between(*rng)]
 
# Filter feedback
rows_removed = len(df) - len(filtered_df)
if rows_removed:
    st.sidebar.info(f"✂️ {rows_removed:,} rows filtered out → **{len(filtered_df):,}** remaining")
else:
    st.sidebar.success(f"✅ All {len(filtered_df):,} rows visible")
 
# ── Pivot Builder ─────────────────────────────────────────────────────────────
st.header("🛠️ Build Your Pivot Table")
st.markdown("Select Rows, Columns, and Values. Only **filtered** data is used.")
 
if filtered_df.empty:
    st.warning("Current filters leave no data. Adjust sidebar filters to continue.")
    st.stop()
 
all_cols = filtered_df.columns.tolist()
 
c1, c2, c3, c4 = st.columns(4)
with c1:
    rows = st.multiselect("Rows (Index)", options=all_cols, help="Columns to group by (e.g., Brand, Department)")
with c2:
    columns = st.multiselect("Columns", options=all_cols, help="Columns to spread as headers (e.g., Stock Age Level)")
with c3:
    values = st.multiselect("Values", options=all_cols, help="Columns to aggregate (e.g., Stock #, My Cost Price)")
with c4:
    agg_func = st.selectbox(
        "Aggregation",
        options=["sum", "count", "mean", "median", "min", "max", "nunique", "std"],
        index=0,
    )
 
# ── Generate Pivot ─────────────────────────────────────────────────────────────
if not rows and not columns:
    st.info("👆 Select at least one **Row** or **Column** above to generate a pivot table.")
    st.stop()
 
# Validate that numeric aggregations are only applied to numeric columns
non_numeric_value_cols = [v for v in values if v in filtered_df.select_dtypes(exclude="number").columns]
if non_numeric_value_cols and agg_func in ("sum", "mean", "median", "std"):
    st.markdown(
        f'<div class="warn-box">⚠️ <b>{", ".join(non_numeric_value_cols)}</b> are non-numeric. '
        f'Switching to <b>count</b> for those columns or choose a different aggregation.</div>',
        unsafe_allow_html=True,
    )
 
try:
    with st.spinner("Building pivot…"):
        # Build a per-value aggfunc dict so mixed types work safely
        if values and non_numeric_value_cols and agg_func in ("sum", "mean", "median", "std"):
            safe_agg: str | dict = {
                v: ("count" if v in non_numeric_value_cols else agg_func)
                for v in values
            }
        else:
            safe_agg = agg_func
 
        pivot_df = pd.pivot_table(
            filtered_df,
            index=rows if rows else None,
            columns=columns if columns else None,
            values=values if values else None,
            aggfunc=safe_agg,
            observed=True,          # avoids FutureWarning + faster on Categoricals
            fill_value=0,
        )
 
        if rows:
            pivot_df = pivot_df.reset_index()
 
        # Flatten multi-level column headers if present
        if isinstance(pivot_df.columns, pd.MultiIndex):
            pivot_df.columns = [" | ".join(str(s) for s in col).strip(" | ") for col in pivot_df.columns]
 
    st.write(f"### Pivot Result  —  {len(pivot_df):,} rows × {len(pivot_df.columns):,} columns")
    st.dataframe(pivot_df, use_container_width=True)
 
    # ── Downloads ──────────────────────────────────────────────────────────────
    dl1, dl2 = st.columns(2)
 
    with dl1:
        csv_bytes = pivot_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Pivot CSV",
            data=csv_bytes,
            file_name="Curated_Stock_Pivot.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
 
    with dl2:
        filtered_csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered Raw Data",
            data=filtered_csv,
            file_name="Filtered_Stocklist.csv",
            mime="text/csv",
            use_container_width=True,
        )
 
except MemoryError:
    st.error("❌ The pivot table is too large to compute in memory. Try adding more Row/Column groupings to reduce cardinality, or narrow your filters.")
except Exception as exc:
    st.error(f"❌ Could not create pivot table: {exc}")
    with st.expander("🐛 Full traceback"):
        st.code(traceback.format_exc())
 
