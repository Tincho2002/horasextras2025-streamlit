import streamlit as st
import pandas as pd
import altair as alt
import io
import numpy as np
from datetime import datetime
import streamlit.components.v1 as components
import plotly.express as px

# --- Configuración de la página ---
st.set_page_config(layout="wide")

# --- CSS Personalizado para un Estilo Profesional ---
st.markdown("""
<style>
/* --- TEMA PERSONALIZADO PARA CONSISTENCIA VISUAL --- */
:root {
    --primary-color: #6C5CE7;
    --background-color: #f0f2f6;
    --secondary-background-color: #f8f7fc;
    --text-color: #1a1a2e;
    --font: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Forzar un fondo claro y color de texto oscuro para evitar el modo oscuro del sistema */
body, .stApp {
    background-color: var(--background-color) !important;
    color: var(--text-color) !important;
}

/* --- GENERAL Y TIPOGRAFÍA --- */
.stApp {
    font-size: 0.92rem;
    font-family: var(--font);
}

/* Forzar color de texto oscuro en elementos genéricos que Streamlit pueda cambiar */
p, div, span, label, li, h1, h2, h3, h4, h5, h6 {
    color: var(--text-color);
}

/* --- COLORES BASE DEL TEMA --- */
[data-testid="stSidebar"],
.stTabs [data-basweb="tab"][aria-selected="true"] {
    background-color: var(--secondary-background-color);
}

/* Estilo para Contenedores (las 'tarjetas') */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: var(--secondary-background-color);
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    padding: 1rem;
}

/* --- Redondear esquinas de los gráficos --- */
[data-testid="stAltairChart"], [data-testid="stPlotlyChart"] {
    border-radius: 8px;
    overflow: hidden;
}

/* Estilo consistente para títulos y subtítulos */
h1 { font-size: 2.2rem; border-bottom: 2px solid var(--primary-color); padding-bottom: 10px; margin-bottom: 20px;}
h2 { font-size: 1.6rem; color: #4a4a4a;}
h3 { font-size: 1.3rem; color: #5a5a5a;}

/* --- LAYOUT Y CONTENEDORES (FLEXBOX RESPONSIVE) --- */
@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 100% !important;
        min-width: calc(100% - 1rem) !important;
    }
}

/* --- VISUALIZACIÓN DE TABLAS ELABORADA --- */
.stDataFrame {
    width: 100%;
    border: none;
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}
.stDataFrame thead th {
    background-color: var(--primary-color);
    color: white;
    font-weight: bold;
    text-align: left;
    padding: 14px 16px;
    font-size: 0.98rem;
    border-bottom: 2px solid #5A4ADF;
}
.stDataFrame tbody tr:nth-of-type(even) {
    background-color: #f8f7fc;
}
.stDataFrame tbody tr:hover {
    background-color: #e9e6ff;
}
.stDataFrame tbody td {
    padding: 12px 16px;
    text-align: right;
    border-bottom: 1px solid #e0e0e0;
    color: #333;
}
.stDataFrame tbody td:first-child {
    text-align: left;
    font-weight: 500;
}

/* --- BOTONES DE DESCARGA --- */
div[data-testid="stDownloadButton"] button {
    background-color: var(--primary-color);
    color: white;
    font-weight: bold;
    padding: 0.6rem 1rem;
    border-radius: 0.5rem;
    border: 1px solid #5A4ADF;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease-in-out;
    font-size: 0.9rem;
}
div[data-testid="stDownloadButton"] button:hover {
    background-color: #5A4ADF;
    transform: translateY(-2px);
    box-shadow: 0 5px 10px rgba(0, 0, 0, 0.15);
}

/* --- PESTAÑAS (TABS) --- */
.stTabs [data-basweb="tab"] {
    border-radius: 6px 6px 0 0;
    padding: 10px 20px;
    font-weight: 600;
}
.stTabs [data-basweb="tab"][aria-selected="true"] {
    border-bottom: 3px solid var(--primary-color);
}

/* --- KPI Metrics Card --- */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
[data-testid="stMetricLabel"] {
    font-weight: 600;
    font-size: 0.95rem;
}
[data-testid="stMetricValue"] {
    font-size: 1.75rem;
    color: var(--primary-color);
}
</style>
""", unsafe_allow_html=True)


# --- INICIO CORRECCIÓN: Funciones y configuración de formato ---
custom_format_locale = {
    "decimal": ",",
    "thousands": ".",
    "grouping": [3],
    "currency": ["$", ""]
}
alt.renderers.set_embed_options(formatLocale=custom_format_locale)

def format_number_es(num, decimals=2):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)):
        return ""
    s = f"{num:,.{decimals}f}"
    return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def format_currency_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"$ {num:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def create_format_dict(df):
    numeric_cols = df.select_dtypes(include=np.number).columns
    formatters = {}
    for col in numeric_cols:
        if any(keyword in col for keyword in ['Cant', 'Q', 'Total_Cantidades', 'Cantidad Total']) or ('int' in str(df[col].dtype)):
            formatters[col] = lambda x: format_number_es(x, 0)
        else:
            formatters[col] = lambda x: format_number_es(x, 2)
    return formatters
# --- FIN CORRECCIÓN ---


# --- FUNCIONES DE CÁLCULO OPTIMIZADAS CON CACHÉ ---
def apply_filters(full_df, selections):
    _df = full_df.copy()
    for col, values in selections.items():
        if values:
            _df = _df[_df[col].isin(values)]
    return _df

@st.cache_data
def load_coords_from_url(url):
    try:
        df = pd.read_csv(url, encoding='latin-1')
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo de coordenadas desde GitHub: {e}")
        return pd.DataFrame()

@st.cache_data
def calculate_monthly_trends(full_df, selections, cost_cols_map, quant_cols_map, selected_cost_keys, selected_quant_keys):
    _df = apply_filters(full_df, selections)
    if _df.empty: return pd.DataFrame()
    cost_cols = [cost_cols_map[k] for k in selected_cost_keys if k in cost_cols_map]
    quant_cols = [quant_cols_map[k] for k in selected_quant_keys if k in quant_cols_map]
    agg_dict = {col: pd.NamedAgg(column=col, aggfunc='sum') for col in cost_cols + quant_cols if col in _df.columns}
    if not agg_dict: return pd.DataFrame()
    monthly_trends_agg = _df.groupby('Mes').agg(**agg_dict).reset_index().sort_values(by='Mes')
    monthly_trends_agg['Total_Costos'] = monthly_trends_agg[[col for col in cost_cols if col in monthly_trends_agg.columns]].sum(axis=1)
    monthly_trends_agg['Total_Cantidades'] = monthly_trends_agg[[col for col in quant_cols if col in monthly_trends_agg.columns]].sum(axis=1)
    return monthly_trends_agg

@st.cache_data
def calculate_monthly_variations(_df_trends):
    if _df_trends.empty: return pd.DataFrame()
    df_var = _df_trends[['Mes', 'Total_Costos', 'Total_Cantidades']].copy()
    df_var['Variacion_Costos_Abs'] = df_var['Total_Costos'].diff().fillna(0)
    df_var['Variacion_Cantidades_Abs'] = df_var['Total_Cantidades'].diff().fillna(0)
    df_var['Variacion_Costos_Pct'] = df_var['Total_Costos'].pct_change().fillna(0) * 100
    df_var['Variacion_Cantidades_Pct'] = df_var['Total_Cantidades'].pct_change().fillna(0) * 100
    return df_var

@st.cache_data
def calculate_grouped_aggregation(full_df, selections, group_cols, cost_cols_map, quant_cols_map, selected_cost_keys, selected_quant_keys):
    _df = apply_filters(full_df, selections)
    if _df.empty: return pd.DataFrame()
    cost_cols = [cost_cols_map[k] for k in selected_cost_keys if k in cost_cols_map]
    quant_cols = [quant_cols_map[k] for k in selected_quant_keys if k in quant_cols_map]
    agg_dict = {col: pd.NamedAgg(column=col, aggfunc='sum') for col in cost_cols + quant_cols if col in _df.columns}
    if not agg_dict: return pd.DataFrame()
    df_grouped = _df.groupby(group_cols).agg(**agg_dict).reset_index()
    df_grouped['Total_Costos'] = df_grouped[[col for col in cost_cols if col in df_grouped.columns]].sum(axis=1)
    df_grouped['Total_Cantidades'] = df_grouped[[col for col in quant_cols if col in df_grouped.columns]].sum(axis=1)
    return df_grouped

@st.cache_data
def calculate_employee_overtime(full_df, selections, cost_cols_map, quant_cols_map, selected_cost_keys, selected_quant_keys):
    _df = apply_filters(full_df, selections)
    if _df.empty: return pd.DataFrame()
    cost_cols = [cost_cols_map[k] for k in selected_cost_keys if k in cost_cols_map]
    quant_cols = [quant_cols_map[k] for k in selected_quant_keys if k in quant_cols_map]
    agg_cols = {}
    for col_name in cost_cols:
        if col_name in _df.columns: agg_cols[f'{col_name}_costo_agg'] = pd.NamedAgg(column=col_name, aggfunc='sum')
    for col_name in quant_cols:
        if col_name in _df.columns: agg_cols[f'{col_name}_cant_agg'] = pd.NamedAgg(column=col_name, aggfunc='sum')
    if not agg_cols: return pd.DataFrame()
    employee_overtime = _df.groupby(['Legajo', 'Apellido y nombre']).agg(**agg_cols).reset_index()
    total_cost_cols_for_sum = [f'{col}_costo_agg' for col in cost_cols if f'{col}_costo_agg' in employee_overtime.columns]
    employee_overtime['Total_Costos'] = employee_overtime[total_cost_cols_for_sum].sum(axis=1)
    total_quantity_cols_for_sum = [f'{col}_cant_agg' for col in quant_cols if f'{col}_cant_agg' in employee_overtime.columns]
    employee_overtime['Total_Cantidades'] = employee_overtime[total_quantity_cols_for_sum].sum(axis=1)
    return employee_overtime

@st.cache_data
def calculate_average_hourly_rate(full_df, selections, dimension):
    _df = apply_filters(full_df, selections)
    if _df.empty: return pd.DataFrame()
    valor_hora_cols = [col for col in ['Hora Normal', 'Hora Extra al 50%', 'Hora Extra al 50% Sabados', 'Hora Extra al 100%', 'HE FC'] if col in _df.columns]
    if not valor_hora_cols: return pd.DataFrame()
    return _df.groupby(dimension)[valor_hora_cols].mean().reset_index()

# --- Funciones Auxiliares ---
def generate_download_buttons(df_to_download, filename_prefix, key_suffix):
    st.markdown("<h6>Opciones de Descarga:</h6>", unsafe_allow_html=True)
    col_dl1, col_dl2, _ = st.columns([1,1,2])
    csv_buffer = io.StringIO()
    df_to_download.to_csv(csv_buffer, index=False)
    with col_dl1:
        st.download_button(label="⬇️ Descargar CSV", data=csv_buffer.getvalue(), file_name=f"{filename_prefix}.csv", mime="text/csv", key=f"csv_{key_suffix}")
    excel_buffer = io.BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    with col_dl2:
        st.download_button(label="📊 Descargar Excel", data=excel_buffer.getvalue(), file_name=f"{filename_prefix}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"excel_{key_suffix}")

@st.cache_data
def load_and_clean_data(uploaded_file):
    df_excel = pd.DataFrame()
    try:
        df_excel = pd.read_excel(uploaded_file, sheet_name='Datos', dtype={'Legajo': str, 'CECO': str, 'Nivel': str}, engine='openpyxl')
    except Exception:
        try:
            df_excel = pd.read_excel(uploaded_file, dtype={'Legajo': str, 'CECO': str, 'Nivel': str}, engine='openpyxl')
        except Exception as e_no_sheet:
            st.error(f"ERROR CRÍTICO: No se pudo leer el archivo Excel. Mensaje: {e_no_sheet}")
            return pd.DataFrame()
    if df_excel.empty: return pd.DataFrame()
    if 'Legajo' in df_excel.columns:
        df_excel['Legajo'] = df_excel['Legajo'].astype(str).str.strip()
        def clean_legajo_value(val):
            if pd.isna(val) or val in ['', 'None', 'nan', 'nan.0']: return 'no disponible'
            s_val = str(val).strip()
            if s_val.endswith('.0') and s_val[:-2].isdigit(): return s_val[:-2]
            return s_val
        df_excel['Legajo'] = df_excel['Legajo'].apply(clean_legajo_value)
    else: df_excel['Legajo'] = 'no disponible'
    if 'Período' in df_excel.columns:
        df_excel['Período'] = pd.to_datetime(df_excel['Período'], errors='coerce')
        df_excel['Mes'] = df_excel['Período'].dt.strftime('%Y-%m')
        df_excel.dropna(subset=['Período'], inplace=True)
    else: df_excel['Mes'] = 'no disponible'
    cols_to_convert = ['Horas extras al 50 %', 'Horas extras al 50 % Sabados', 'Horas extras al 100%', 'Cantidad HE 50', 'Cant HE al 50 Sabados', 'Cantidad HE 100', 'Cantidad HE FC', 'Importe HE Fc', 'Total (Q)', 'Hora Normal', 'Hora Extra al 50%', 'Hora Extra al 50% Sabados', 'Hora Extra al 100%', 'HE FC', 'Total ($)']
    for col in cols_to_convert:
        if col in df_excel.columns: df_excel[col] = pd.to_numeric(df_excel[col], errors='coerce').fillna(0)
        else: df_excel[col] = 0
    cols_for_filters = ['Gerencia', 'Ministerio', 'CECO', 'Ubicación', 'Nivel', 'Función', 'Sexo', 'Liquidación', 'Apellido y nombre', 'Legajo']
    for col in cols_for_filters:
        if col not in df_excel.columns: df_excel[col] = 'no disponible'
        df_excel[col] = df_excel[col].astype(str).str.strip().replace(['None', 'nan', ''], 'no disponible')
    
    if 'Sexo' in df_excel.columns:
        valid_sexo = ['Masculino', 'Femenino']
        df_excel['Sexo'] = df_excel['Sexo'].apply(lambda x: x if x in valid_sexo else 'no disponible')

    for col_to_int in ['CECO', 'Nivel']:
        if col_to_int in df_excel.columns:
            df_excel[col_to_int] = df_excel[col_to_int].replace('no disponible', pd.NA)
            df_excel[col_to_int] = pd.to_numeric(df_excel[col_to_int], errors='coerce').astype(pd.Int64Dtype()).astype(str).replace('<NA>', 'no disponible')
            def clean_numeric_string(s):
                if isinstance(s, str) and s.endswith('.0') and s[:-2].isdigit(): return s[:-2]
                return s
            df_excel[col_to_int] = df_excel[col_to_int].apply(clean_numeric_string)
    return df_excel

# --- INICIO DE LA APLICACIÓN ---
st.title('📊 Dashboard de Horas Extras HE_2025')
st.subheader('Análisis Interactivo de Costos y Cantidades de Horas Extras')

uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel de Horas Extras", type=["xlsx"])
COORDS_URL = "https://raw.githubusercontent.com/Tincho2002/dotacion_assa_2025/main/coordenadas.csv"

if uploaded_file is not None:
    with st.spinner('Procesando archivo...'):
        df = load_and_clean_data(uploaded_file)
        df_coords = load_coords_from_url(COORDS_URL)

    if df.empty:
        st.error("El archivo cargado está vacío o no se pudo procesar. Verifique el contenido y el formato.")
        st.stop()

    st.success(f"Se ha cargado un total de **{format_number_es(len(df), 0)}** registros de horas extras.")

    # --- DEFINICIÓN Y ESTADO DE FILTROS ---
    st.sidebar.header('Filtros del Dashboard')
    cost_columns_options = {'Horas extras al 50 %': 'Horas extras al 50 %', 'Horas extras al 50 % Sabados': 'Horas extras al 50 % Sabados', 'Horas extras al 100%': 'Horas extras al 100%', 'Importe HE Fc': 'Importe HE Fc'}
    quantity_columns_options = {'Cantidad HE 50': 'Cantidad HE 50', 'Cant HE al 50 Sabados': 'Cant HE al 50 Sabados', 'Cantidad HE 100': 'Cantidad HE 100', 'Cantidad HE FC': 'Cantidad HE FC'}
    filter_cols = ['Gerencia', 'Ministerio', 'CECO', 'Ubicación', 'Función', 'Nivel', 'Sexo', 'Liquidación', 'Legajo', 'Mes']
    
    if 'selections' not in st.session_state:
        st.session_state.selections = {col: [] for col in filter_cols}
    if 'cost_types' not in st.session_state:
        st.session_state.cost_types = list(cost_columns_options.keys())
    if 'quantity_types' not in st.session_state:
        st.session_state.quantity_types = list(quantity_columns_options.keys())

    col1, col2 = st.sidebar.columns(2)
    if col1.button('🧹 Limpiar Filtros', use_container_width=True):
        st.session_state.selections = {col: [] for col in filter_cols}
        st.session_state.cost_types = []
        st.session_state.quantity_types = []
        st.rerun()

    if col2.button('📥 Cargar Todo', use_container_width=True):
        for col in filter_cols:
            all_options = sorted(df[col].dropna().unique().tolist())
            st.session_state.selections[col] = [opt for opt in all_options if opt != 'no disponible']
        st.session_state.cost_types = list(cost_columns_options.keys())
        st.session_state.quantity_types = list(quantity_columns_options.keys())
        st.rerun()
    
    st.sidebar.markdown("---")

    for col in filter_cols:
        options = sorted(df[col].dropna().unique().tolist())
        options = [opt for opt in options if opt != 'no disponible']
        st.session_state.selections[col] = st.sidebar.multiselect(f'Selecciona {col}(s):', options, default=st.session_state.selections.get(col, []))

    filtered_df = apply_filters(df, st.session_state.selections)
    
    top_n_employees = st.sidebar.slider('Mostrar Top N Empleados:', 5, 50, 10)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Selección de Tipos de Horas Extras")
    
    st.session_state.cost_types = st.sidebar.multiselect(
        'Selecciona Tipos de Costo de HE:', 
        options=list(cost_columns_options.keys()), 
        default=st.session_state.get('cost_types', [])
    )
    st.session_state.quantity_types = st.sidebar.multiselect(
        'Selecciona Tipos de Cantidad de HE:', 
        options=list(quantity_columns_options.keys()), 
        default=st.session_state.get('quantity_types', [])
    )
    
    st.info(f"Mostrando **{format_number_es(len(filtered_df), 0)}** registros según los filtros aplicados.")

    # --- INICIO: SECCIÓN DE TARJETA DE RESUMEN MODIFICADA ---
    if not filtered_df.empty and 'Mes' in filtered_df.columns:
        try:
            latest_month_str = filtered_df['Mes'].dropna().max()
            if pd.notna(latest_month_str):
                df_last_month = filtered_df[filtered_df['Mes'] == latest_month_str].copy()
                
                # --- Lógica dinámica para calcular totales según la selección ---
                costo_50 = df_last_month['Horas extras al 50 %'].sum() if 'Horas extras al 50 %' in st.session_state.cost_types else 0
                cantidad_50 = df_last_month['Cantidad HE 50'].sum() if 'Cantidad HE 50' in st.session_state.quantity_types else 0
                
                costo_50_sab = df_last_month['Horas extras al 50 % Sabados'].sum() if 'Horas extras al 50 % Sabados' in st.session_state.cost_types else 0
                cantidad_50_sab = df_last_month['Cant HE al 50 Sabados'].sum() if 'Cant HE al 50 Sabados' in st.session_state.quantity_types else 0

                costo_100 = df_last_month['Horas extras al 100%'].sum() if 'Horas extras al 100%' in st.session_state.cost_types else 0
                cantidad_100 = df_last_month['Cantidad HE 100'].sum() if 'Cantidad HE 100' in st.session_state.quantity_types else 0

                costo_fc = df_last_month['Importe HE Fc'].sum() if 'Importe HE Fc' in st.session_state.cost_types else 0
                cantidad_fc = df_last_month['Cantidad HE FC'].sum() if 'Cantidad HE FC' in st.session_state.quantity_types else 0
                
                total_costo_mes = costo_50 + costo_50_sab + costo_100 + costo_fc
                total_cantidad_mes = cantidad_50 + cantidad_50_sab + cantidad_100 + cantidad_fc
                
                month_dt = datetime.strptime(latest_month_str, '%Y-%m')
                meses_espanol = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
                month_name = f"{meses_espanol.get(month_dt.month, '')} {month_dt.year}"

                card_html = f"""
                <style>
                    /* Estilos CSS (sin cambios) */
                </style>
                <div class="summary-card">
                    <div class="summary-header">RESUMEN MENSUAL: {month_name}</div>
                    <div class="summary-totals">
                        <div class="summary-main-kpi">
                            <div class="value" data-target="{total_costo_mes}" data-type="currency" data-decimals="2"></div>
                            <div class="label">Costo Total</div>
                        </div>
                        <div class="summary-main-kpi">
                            <div class="value" data-target="{total_cantidad_mes}" data-type="number" data-suffix=" hs" data-decimals="0"></div>
                            <div class="label">Cantidad Total</div>
                        </div>
                    </div>
                    <div class="summary-breakdown">
                        <div class="summary-sub-kpi">
                            <div class="type">HE 50%</div>
                            <div class="value-cost" data-target="{costo_50}" data-type="currency" data-decimals="2"></div>
                            <div class="value-qty" data-target="{cantidad_50}" data-type="number" data-suffix=" hs" data-decimals="0"></div>
                        </div>
                        <div class="summary-sub-kpi">
                            <div class="type">HE 50% Sábados</div>
                            <div class="value-cost" data-target="{costo_50_sab}" data-type="currency" data-decimals="2"></div>
                            <div class="value-qty" data-target="{cantidad_50_sab}" data-type="number" data-suffix=" hs" data-decimals="0"></div>
                        </div>
                        <div class="summary-sub-kpi">
                            <div class="type">HE 100%</div>
                            <div class="value-cost" data-target="{costo_100}" data-type="currency" data-decimals="2"></div>
                            <div class="value-qty" data-target="{cantidad_100}" data-type="number" data-suffix=" hs" data-decimals="0"></div>
                        </div>
                        <div class="summary-sub-kpi">
                            <div class="type">HE FC</div>
                            <div class="value-cost" data-target="{costo_fc}" data-type="currency" data-decimals="2"></div>
                            <div class="value-qty" data-target="{cantidad_fc}" data-type="number" data-suffix=" hs" data-decimals="0"></div>
                        </div>
                    </div>
                </div>
                <script>
                    /* Script de animación (sin cambios) */
                </script>
                """
                components.html(card_html, height=420)
                st.markdown("<br>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"No se pudo generar el resumen del último mes. Error: {e}")
    # --- FIN: SECCIÓN DE TARJETA DE RESUMEN MODIFICADA ---


    # --- ESTRUCTURA DE PESTAÑAS (CON MAPA) ---
    tab_list = st.tabs(["📈 Resumen y Tendencias", "🗺️ Mapa de Distribución", "🏢 Desglose Organizacional", "👤 Empleados Destacados", "⚖️ Valor Hora", "📋 Datos Brutos"])
    
    tab_resumen, tab_mapa, tab_desglose_org, tab_empleados, tab_valor_hora, tab_datos_brutos = tab_list

    with tab_resumen:
        # ... (código sin cambios)
        pass

    # --- INICIO: PESTAÑA DE MAPA MODIFICADA ---
    with tab_mapa:
        st.header("Distribución Geográfica de Horas Extras")
        if filtered_df.empty:
            st.warning("No hay datos para mostrar en el mapa con los filtros seleccionados.")
        else:
            df_mapa_display = filtered_df.copy()
            
            latest_month_map = ""
            if st.session_state.selections.get('Mes'):
                all_months_sorted = sorted(df['Mes'].dropna().unique())
                selected_months_sorted = [m for m in all_months_sorted if m in st.session_state.selections['Mes']]
                if selected_months_sorted:
                    latest_month_map = selected_months_sorted[-1]
            else:
                latest_month_map = df['Mes'].dropna().max()

            if pd.notna(latest_month_map):
                df_mapa_display = df_mapa_display[df_mapa_display['Mes'] == latest_month_map].copy()
                month_dt_map = datetime.strptime(latest_month_map, '%Y-%m')
                meses_espanol = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
                month_name_map = f"{meses_espanol.get(month_dt_map.month, '')} {month_dt_map.year}"
                st.subheader(f"Mostrando datos para el período: {month_name_map}")
            
            map_style_options = {"Satélite con Calles": "satellite-streets", "Mapa de Calles": "open-street-map", "Estilo Claro": "carto-positron"}
            selected_style_name = st.selectbox("Selecciona el estilo del mapa:", options=list(map_style_options.keys()), key="map_style_selector")
            selected_mapbox_style = map_style_options[selected_style_name]
            
            # --- Lógica dinámica para calcular totales del mapa ---
            selected_cost_cols = [cost_columns_options[k] for k in st.session_state.cost_types if k in cost_columns_options]
            selected_quant_cols = [quantity_columns_options[k] for k in st.session_state.quantity_types if k in quantity_columns_options]
            
            existing_cost_cols = [col for col in selected_cost_cols if col in df_mapa_display.columns]
            existing_quant_cols = [col for col in selected_quant_cols if col in df_mapa_display.columns]

            if existing_cost_cols:
                df_mapa_display['Costo_Total_Dinamico'] = df_mapa_display[existing_cost_cols].sum(axis=1)
            else:
                df_mapa_display['Costo_Total_Dinamico'] = 0

            if existing_quant_cols:
                df_mapa_display['Cantidad_Total_Dinamica'] = df_mapa_display[existing_quant_cols].sum(axis=1)
            else:
                df_mapa_display['Cantidad_Total_Dinamica'] = 0

            df_mapa_agg = df_mapa_display.groupby('Ubicación').agg(
                Costo_Total=('Costo_Total_Dinamico', 'sum'), 
                Cantidad_Total=('Cantidad_Total_Dinamica', 'sum')
            ).reset_index()
            # --- Fin lógica dinámica ---
            
            col_map, col_table = st.columns([3, 2])
            with col_map:
                df_mapa_data = pd.merge(df_mapa_agg, df_coords, left_on='Ubicación', right_on="Distrito", how="left")
                df_mapa_data.dropna(subset=['Latitud', 'Longitud'], inplace=True)
                if df_mapa_data.empty:
                    st.warning("No se encontraron coordenadas para las ubicaciones seleccionadas.")
                else:
                    mapbox_access_token = "pk.eyJ1Ijoic2FuZHJhcXVldmVkbyIsImEiOiJjbWYzOGNkZ2QwYWg0MnFvbDJucWc5d3VwIn0.bz6E-qxAwk6ZFPYohBsdMw"
                    px.set_mapbox_access_token(mapbox_access_token)
                    fig = px.scatter_mapbox(
                        df_mapa_data, lat="Latitud", lon="Longitud", 
                        size="Cantidad_Total", color="Costo_Total", 
                        hover_name="Distrito", 
                        hover_data={"Latitud": False, "Longitud": False, "Cantidad_Total": ':.0f', "Costo_Total": ':$,.2f'}, 
                        color_continuous_scale=px.colors.sequential.Plasma, 
                        size_max=50, mapbox_style=selected_mapbox_style, zoom=6, 
                        center={"lat": -32.5, "lon": -61.5}
                    )
                    fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
                    st.plotly_chart(fig, use_container_width=True)
            with col_table:
                st.markdown("##### Costos y Cantidades por Distrito")
                table_data = df_mapa_agg.rename(columns={'Ubicación': 'Distrito', 'Costo_Total': 'Costo Total', 'Cantidad_Total': 'Cantidad Total'})
                table_data.sort_values(by='Costo Total', ascending=False, inplace=True)
                total_row = pd.DataFrame({'Distrito': ['**TOTAL GENERAL**'], 'Costo Total': [table_data['Costo Total'].sum()], 'Cantidad Total': [table_data['Cantidad Total'].sum()]})
                df_final_table = pd.concat([table_data, total_row], ignore_index=True)
                st.dataframe(df_final_table.style.format({'Costo Total': format_currency_es, 'Cantidad Total': lambda x: format_number_es(x, 0)}), use_container_width=True, height=500, hide_index=True)
    # --- FIN: PESTAÑA DE MAPA MODIFICADA ---

    with tab_desglose_org:
        # ... (código sin cambios, ya corregido en el paso anterior)
        pass

    with tab_empleados:
        # ... (código sin cambios)
        pass

    with tab_valor_hora:
        # ... (código sin cambios)
        pass

    with tab_datos_brutos:
        # ... (código sin cambios)
        pass
else:
    st.info("Por favor, cargue un archivo Excel para comenzar el análisis.")

# Nota: Para mantener el código más corto, he omitido las secciones internas de las pestañas que no cambiaron, 
# pero en tu archivo final debes asegurarte de que todo el código esté presente.
# El código completo de las secciones no modificadas se encuentra en la versión anterior.
