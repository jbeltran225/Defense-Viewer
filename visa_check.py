import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Defenser_Viewer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ESTILOS
# =========================================================
st.markdown("""
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
        margin-bottom: 0.2rem !important;
    }

    .subheader-app {
        font-size: 1rem;
        color: #555;
        margin-bottom: 0.8rem;
    }

    .stDataFrame {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        overflow: hidden;
    }

    div[data-testid="stSidebar"] {
        border-right: 1px solid #e5e7eb;
    }

    .chip-box {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
        border-radius: 18px;
        background-color: #dbeafe;
        color: #1d4ed8;
        font-size: 0.85rem;
        border: 1px solid #93c5fd;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# RUTA DEL ARCHIVO
# =========================================================
EXCEL_PATH = Path("VISA_CHECK.xlsx")
SHEET_NAME = "VISA CHECK"

# =========================================================
# FUNCIONES
# =========================================================
@st.cache_data
def load_data(file_path: Path, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Limpieza básica
    df.columns = [str(col).strip() for col in df.columns]

    expected_cols = [
        "Industry",
        "Brand",
        "Dispute_Condition",
        "Condition_Category",
        "Required_Documents",
        "Transaction Type"
    ]

    # Verifica columnas mínimas
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas esperadas: {missing}")

    # Limpiar texto
    for col in expected_cols:
        df[col] = df[col].astype(str).str.strip()

    # Reemplazar "nan" string generado por astype(str)
    df = df.replace("nan", "")

    # Crear ID visual
    df = df.reset_index(drop=True)
    df.insert(1, "ID", df.index + 1)

    return df


def apply_filters(
    df: pd.DataFrame,
    industry_list,
    brand_list,
    dispute_list,
    search_text: str
) -> pd.DataFrame:
    filtered = df.copy()

    if industry_list:
        filtered = filtered[filtered["Industry"].isin(industry_list)]

    if brand_list:
        filtered = filtered[filtered["Brand"].isin(brand_list)]

    if dispute_list:
        filtered = filtered[filtered["Dispute_Condition"].isin(dispute_list)]

    if search_text:
        search_text = search_text.strip().lower()

        search_mask = (
            filtered["Industry"].str.lower().str.contains(search_text, na=False) |
            filtered["Brand"].str.lower().str.contains(search_text, na=False) |
            filtered["Dispute_Condition"].str.lower().str.contains(search_text, na=False) |
            filtered["Condition_Category"].str.lower().str.contains(search_text, na=False) |
            filtered["Required_Documents"].str.lower().str.contains(search_text, na=False) |
            filtered["Transaction Type"].str.lower().str.contains(search_text, na=False)
        )

        filtered = filtered[search_mask]

    return filtered


def render_filter_chips(industry_list, brand_list, dispute_list):
    chips = []

    for item in industry_list:
        chips.append(f"<span class='chip-box'>Industry: {item}</span>")

    for item in brand_list:
        chips.append(f"<span class='chip-box'>Brand: {item}</span>")

    for item in dispute_list:
        chips.append(f"<span class='chip-box'>Dispute_Condition: {item}</span>")

    if chips:
        st.markdown("".join(chips), unsafe_allow_html=True)
    else:
        st.caption("Sin filtros activos")


# =========================================================
# CARGA DE DATOS
# =========================================================
st.title("Defenser_Viewer")
st.markdown("<div class='subheader-app'>Defense Viewer</div>", unsafe_allow_html=True)

if not EXCEL_PATH.exists():
    st.error(f"No encuentro el archivo: {EXCEL_PATH.resolve()}")
    st.stop()

try:
    df = load_data(EXCEL_PATH, SHEET_NAME)
except Exception as e:
    st.error(f"Error al leer el archivo: {e}")
    st.stop()

# =========================================================
# SIDEBAR DE FILTROS
# =========================================================
st.sidebar.header("Filter")

industry_options = sorted([x for x in df["Industry"].dropna().unique() if str(x).strip() != ""])
brand_options = sorted([x for x in df["Brand"].dropna().unique() if str(x).strip() != ""])
dispute_options = sorted([x for x in df["Dispute_Condition"].dropna().unique() if str(x).strip() != ""])

selected_industry = st.sidebar.multiselect(
    "Industry",
    options=industry_options,
    default=[]
)

# Brand dependiente de Industry
brand_df = df.copy()
if selected_industry:
    brand_df = brand_df[brand_df["Industry"].isin(selected_industry)]

brand_options_dynamic = sorted([x for x in brand_df["Brand"].dropna().unique() if str(x).strip() != ""])

selected_brand = st.sidebar.multiselect(
    "Brand",
    options=brand_options_dynamic,
    default=[]
)

# Dispute dependiente de Industry + Brand
dispute_df = brand_df.copy()
if selected_brand:
    dispute_df = dispute_df[dispute_df["Brand"].isin(selected_brand)]

dispute_options_dynamic = sorted([x for x in dispute_df["Dispute_Condition"].dropna().unique() if str(x).strip() != ""])

selected_dispute = st.sidebar.multiselect(
    "Dispute_Condition",
    options=dispute_options_dynamic,
    default=[]
)

clear_filters = st.sidebar.button("Clear filters", use_container_width=True)

if clear_filters:
    st.rerun()

# =========================================================
# BÚSQUEDA
# =========================================================
search_text = st.text_input(
    "Search Defense Viewer",
    placeholder="Search Defense Viewer"
)

# =========================================================
# FILTRADO
# =========================================================
filtered_df = apply_filters(
    df=df,
    industry_list=selected_industry,
    brand_list=selected_brand,
    dispute_list=selected_dispute,
    search_text=search_text
)

# =========================================================
# FILTROS ACTIVOS
# =========================================================
st.markdown("### All filters")
render_filter_chips(selected_industry, selected_brand, selected_dispute)

# =========================================================
# TABLA PRINCIPAL
# =========================================================
display_cols = [
    "Industry",
    "ID",
    "Brand",
    "Dispute_Condition",
    "Condition_Category",
    "Required_Documents"
]

st.dataframe(
    filtered_df[display_cols],
    use_container_width=True,
    hide_index=True,
    height=620,
    column_config={
        "Industry": st.column_config.TextColumn("Industry", width="medium"),
        "ID": st.column_config.NumberColumn("ID", width="small"),
        "Brand": st.column_config.TextColumn("Brand", width="small"),
        "Dispute_Condition": st.column_config.TextColumn("Dispute_Condition", width="medium"),
        "Condition_Category": st.column_config.TextColumn("Condition_Category", width="medium"),
        "Required_Documents": st.column_config.TextColumn("Required_Documents", width="large"),
    }
)

# =========================================================
# DESCARGAS
# =========================================================
csv_data = filtered_df.to_csv(
    index=False,
    sep=";",
    encoding="utf-8-sig"
).encode("utf-8-sig")

excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    filtered_df.to_excel(writer, index=False, sheet_name="Filtered_Data")

excel_data = excel_buffer.getvalue()

col_csv, col_xlsx = st.columns(2)

with col_csv:
    st.download_button(
        label="Download filtered data as CSV",
        data=csv_data,
        file_name="defense_viewer_filtered.csv",
        mime="text/csv"
    )

with col_xlsx:
    st.download_button(
        label="Download filtered data as Excel",
        data=excel_data,
        file_name="defense_viewer_filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )