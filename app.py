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