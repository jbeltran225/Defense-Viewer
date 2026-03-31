import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO

# -------------------------------------------------------------------
# App setup
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Defense Viewer",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# Custom styles
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
        .main {
            background-color: #ffffff;
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }

        h1 {
            font-size: 1.8rem !important;
            font-weight: 600 !important;
            margin-bottom: 0.15rem !important;
            color: #1f2937;
        }

        .app-subtitle {
            font-size: 0.98rem;
            color: #6b7280;
            margin-bottom: 1rem;
        }

        .stDataFrame {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
        }

        div[data-testid="stSidebar"] {
            border-right: 1px solid #e5e7eb;
        }

        .filter-tag {
            display: inline-block;
            padding: 0.32rem 0.7rem;
            margin-right: 0.4rem;
            margin-bottom: 0.45rem;
            border-radius: 999px;
            background-color: #f3f4f6;
            color: #374151;
            font-size: 0.84rem;
            border: 1px solid #d1d5db;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# File settings
# -------------------------------------------------------------------
DATA_FILE = Path("VISA_CHECK.xlsx")
SHEET_NAME = "VISA CHECK"

# -------------------------------------------------------------------
# Data loading
# -------------------------------------------------------------------
@st.cache_data
def load_data(file_path: Path, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df.columns = [str(col).strip() for col in df.columns]

    required_columns = [
        "Industry",
        "Brand",
        "Dispute_Condition",
        "Condition_Category",
        "Required_Documents",
        "Transaction Type",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    for col in required_columns:
        df[col] = df[col].astype(str).str.strip()

    df = df.replace("nan", "")
    df = df.reset_index(drop=True)
    df.insert(1, "ID", df.index + 1)

    return df


# -------------------------------------------------------------------
# Filtering helpers
# -------------------------------------------------------------------
def apply_filters(
    df: pd.DataFrame,
    selected_industry,
    selected_brand,
    selected_dispute,
    search_text: str,
) -> pd.DataFrame:
    result = df.copy()

    if selected_industry:
        result = result[result["Industry"].isin(selected_industry)]

    if selected_brand:
        result = result[result["Brand"].isin(selected_brand)]

    if selected_dispute:
        result = result[result["Dispute_Condition"].isin(selected_dispute)]

    if search_text:
        query = search_text.strip().lower()

        mask = (
            result["Industry"].str.lower().str.contains(query, na=False)
            | result["Brand"].str.lower().str.contains(query, na=False)
            | result["Dispute_Condition"].str.lower().str.contains(query, na=False)
            | result["Condition_Category"].str.lower().str.contains(query, na=False)
            | result["Required_Documents"].str.lower().str.contains(query, na=False)
            | result["Transaction Type"].str.lower().str.contains(query, na=False)
        )

        result = result[mask]

    return result


def render_active_filters(industry_list, brand_list, dispute_list) -> None:
    active_tags = []

    for item in industry_list:
        active_tags.append(f"<span class='filter-tag'>Industry: {item}</span>")

    for item in brand_list:
        active_tags.append(f"<span class='filter-tag'>Brand: {item}</span>")

    for item in dispute_list:
        active_tags.append(f"<span class='filter-tag'>Dispute Condition: {item}</span>")

    if active_tags:
        st.markdown("".join(active_tags), unsafe_allow_html=True)
    else:
        st.caption("No active filters")


# -------------------------------------------------------------------
# App header
# -------------------------------------------------------------------
st.title("Defense Viewer")
st.markdown(
    "<div class='app-subtitle'>Reference table for dispute conditions and required supporting documents</div>",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# Load source file
# -------------------------------------------------------------------
if not DATA_FILE.exists():
    st.error(f"File not found: {DATA_FILE.resolve()}")
    st.stop()

try:
    df = load_data(DATA_FILE, SHEET_NAME)
except Exception as e:
    st.error(f"Error reading source file: {e}")
    st.stop()

# -------------------------------------------------------------------
# Sidebar filters
# -------------------------------------------------------------------
st.sidebar.header("Filters")

industry_options = sorted(
    [x for x in df["Industry"].dropna().unique() if str(x).strip() != ""]
)
brand_options = sorted(
    [x for x in df["Brand"].dropna().unique() if str(x).strip() != ""]
)
dispute_options = sorted(
    [x for x in df["Dispute_Condition"].dropna().unique() if str(x).strip() != ""]
)

selected_industry = st.sidebar.multiselect(
    "Industry",
    options=industry_options,
    default=[],
)

brand_df = df.copy()
if selected_industry:
    brand_df = brand_df[brand_df["Industry"].isin(selected_industry)]

brand_options_dynamic = sorted(
    [x for x in brand_df["Brand"].dropna().unique() if str(x).strip() != ""]
)

selected_brand = st.sidebar.multiselect(
    "Brand",
    options=brand_options_dynamic,
    default=[],
)

dispute_df = brand_df.copy()
if selected_brand:
    dispute_df = dispute_df[dispute_df["Brand"].isin(selected_brand)]

dispute_options_dynamic = sorted(
    [x for x in dispute_df["Dispute_Condition"].dropna().unique() if str(x).strip() != ""]
)

selected_dispute = st.sidebar.multiselect(
    "Dispute Condition",
    options=dispute_options_dynamic,
    default=[],
)

clear_filters = st.sidebar.button("Clear filters", use_container_width=True)
if clear_filters:
    st.rerun()

# -------------------------------------------------------------------
# Search
# -------------------------------------------------------------------
search_text = st.text_input(
    "Search",
    placeholder="Search across industries, conditions, categories, and documents",
)

# -------------------------------------------------------------------
# Apply filters
# -------------------------------------------------------------------
filtered_df = apply_filters(
    df=df,
    selected_industry=selected_industry,
    selected_brand=selected_brand,
    selected_dispute=selected_dispute,
    search_text=search_text,
)

# -------------------------------------------------------------------
# Active filters
# -------------------------------------------------------------------
st.markdown("### Active filters")
render_active_filters(selected_industry, selected_brand, selected_dispute)

# -------------------------------------------------------------------
# Main table
# -------------------------------------------------------------------
display_columns = [
    "Industry",
    "ID",
    "Brand",
    "Dispute_Condition",
    "Condition_Category",
    "Required_Documents",
]

st.dataframe(
    filtered_df[display_columns],
    use_container_width=True,
    hide_index=True,
    height=620,
    column_config={
        "Industry": st.column_config.TextColumn("Industry", width="medium"),
        "ID": st.column_config.NumberColumn("ID", width="small"),
        "Brand": st.column_config.TextColumn("Brand", width="small"),
        "Dispute_Condition": st.column_config.TextColumn("Dispute Condition", width="medium"),
        "Condition_Category": st.column_config.TextColumn("Condition Category", width="medium"),
        "Required_Documents": st.column_config.TextColumn("Required Documents", width="large"),
    },
)

# -------------------------------------------------------------------
# Download section
# -------------------------------------------------------------------
csv_data = filtered_df.to_csv(
    index=False,
    sep=";",
    encoding="utf-8-sig",
).encode("utf-8-sig")

excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    filtered_df.to_excel(writer, index=False, sheet_name="Filtered_Data")

excel_data = excel_buffer.getvalue()

download_col_csv, download_col_xlsx = st.columns(2)

with download_col_csv:
    st.download_button(
        label="Download filtered data as CSV",
        data=csv_data,
        file_name="defense_viewer_filtered.csv",
        mime="text/csv",
    )

with download_col_xlsx:
    st.download_button(
        label="Download filtered data as Excel",
        data=excel_data,
        file_name="defense_viewer_filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )