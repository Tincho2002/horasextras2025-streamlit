import streamlit as st
import pandas as pd
import altair as alt
import io

# --- Configuración de la página ---
st.set_page_config(layout="wide")

# --- Custom CSS para estilo ---
st.markdown("""
<style>
div.stDownloadButton button {
    background-color: #6C5CE7; color: white; font-weight: bold; padding: 0.75rem 1.25rem;
    border-radius: 0.5rem; border: none; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease; cursor: pointer; display: inline-flex;
    align-items: center; gap: 8px;
}
div.stDownloadButton button:hover {
    background-color: #5A4ADF; transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
}
.stMultiSelect div[data-baseweb="select"] {
    border: 1px solid #adb5bd; border-radius: 0.5rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); background-color: #f8f9fa;
    transition: all 0.2s ease-in-out;
}
.stMultiSelect div[data-baseweb="select"]:hover { border-color: #6c757d; }
</style>
""", unsafe_allow_html=True)

# --- Título de la Aplicación ---
st.title('📊 Dashboard de Horas Extras HE_2025')
st.subheader('Análisis Interactivo de Costos y Cantidades de Horas Extras')

# --- Funciones Auxiliares ---
def format_st_dataframe(df_to_style):
    numeric_cols = df_to_style.select_dtypes(include='number').columns
    format_dict = {col: '{:,.2f}' for col in numeric_cols}
    return df_to_style.style.format(format_dict)

def generate_download_buttons(df_to_download, filename_prefix):
    st.markdown("##### Opciones de Descarga:")
    col_dl1, col_dl2 = st.columns(2)
    csv_buffer = io.StringIO()
    df_to_download.to_csv(csv_buffer, index=False)
    with col_dl1:
        st.download_button(label="⬇️ Descargar como CSV", data=csv_buffer.getvalue(), file_name=f"{filename_prefix}.csv", mime="text/csv", key=f"csv_download_{filename_prefix}")
    excel_buffer = io.BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    with col_dl2:
        st.download_button(label="📊 Descargar como Excel", data=excel_buffer.getvalue(), file_name=f"{filename_prefix}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"excel_download_{filename_prefix}")

def add_total_row(df, group_cols, value_cols, total_label='Total'):
    if not isinstance(group_cols, list): group_cols = [group_cols]
    total_row_dict = {col: total_label for col in group_cols if col in df.columns}
    for col in value_cols:
        if col in df.columns: total_row_dict[col] = df[col].sum()
    total_df = pd.DataFrame([total_row_dict])
    return pd.concat([df, total_df], ignore_index=True)

# --- Función para cargar y limpiar datos ---
@st.cache_data
def load_and_clean_data(file_upload_obj):
    df_excel = pd.DataFrame()
    try:
        df_excel = pd.read_excel(file_upload_obj, sheet_name='Datos', dtype={'Legajo': str, 'CECO': str, 'Nivel': str})
    except Exception:
        try:
            df_excel = pd.read_excel(file_upload_obj, dtype={'Legajo': str, 'CECO': str, 'Nivel': str})
            st.warning("No se encontró la hoja 'Datos'. Se cargó la primera hoja del Excel.")
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
uploaded_file = st.file_uploader("📂 Por favor, sube tu archivo Excel para comenzar", type="xlsx")

if uploaded_file is not None:
    df = load_and_clean_data(uploaded_file)
    if df.empty:
        st.error("No se pudieron cargar o limpiar los datos. Verifica el archivo.")
        st.stop()
    st.success(f"Se ha cargado un total de **{len(df)}** registros de horas extras.")
    st.markdown('---')

    # --- FILTROS INTERACTIVOS ---
    st.sidebar.header('Filtros del Dashboard')
    def get_sorted_unique_options(dataframe, column_name):
        if column_name in dataframe.columns:
            unique_values = dataframe[column_name].dropna().unique().tolist()
            if column_name == 'Mes': return sorted(unique_values)
            if column_name == 'Legajo':
                numeric_vals, non_numeric_vals = [], []
                for val in unique_values:
                    try: numeric_vals.append(int(val))
                    except (ValueError, TypeError): non_numeric_vals.append(val)
                return [str(x) for x in sorted(numeric_vals)] + sorted(non_numeric_vals)
            return sorted(unique_values)
        return []

    filter_cols = ['Gerencia', 'Ministerio', 'Legajo', 'CECO', 'Ubicación', 'Nivel', 'Función', 'Sexo', 'Mes', 'Liquidación']
    selections = {}
    for col in filter_cols:
        options = get_sorted_unique_options(df, col)
        selections[col] = st.sidebar.multiselect(f'Selecciona {col}(s):', options, default=options)

    top_n_employees = st.sidebar.slider('Mostrar Top N Empleados:', 5, 50, 10)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Selección de Tipos de Horas Extras")
    cost_columns_options = {'Horas extras al 50 %': 'Horas extras al 50 %', 'Horas extras al 50 % Sabados': 'Horas extras al 50 % Sabados', 'Horas extras al 100%': 'Horas extras al 100%', 'Importe HE Fc': 'Importe HE Fc'}
    quantity_columns_options = {'Cantidad HE 50': 'Cantidad HE 50', 'Cant HE al 50 Sabados': 'Cant HE al 50 Sabados', 'Cantidad HE 100': 'Cantidad HE 100', 'Cantidad HE FC': 'Cantidad HE FC'}
    selected_cost_types_display = st.sidebar.multiselect('Tipos de Costo:', list(cost_columns_options.keys()), default=list(cost_columns_options.keys()))
    selected_quantity_types_display = st.sidebar.multiselect('Tipos de Cantidad:', list(quantity_columns_options.keys()), default=list(quantity_columns_options.keys()))
    selected_cost_types_internal = [cost_columns_options[key] for key in selected_cost_types_display]
    selected_quantity_types_internal = [quantity_columns_options[key] for key in selected_quantity_types_display]

    filtered_df = df.copy()
    for col, selected_values in selections.items():
        if selected_values: filtered_df = filtered_df[filtered_df[col].isin(selected_values)]

    st.write(f"Mostrando **{len(filtered_df)}** registros según los filtros aplicados.")
    st.markdown('---')

    # --- PESTAÑAS ---
    tab1, tab2, tab3, tab_valor_hora, tab4 = st.tabs(["📈 Resumen", "🏢 Desglose", "👤 Empleados", "⚖️ Valor Hora", "📋 Datos Brutos"])
    
    with tab1:
        # Aquí va toda la lógica de la Pestaña 1 de tu código original
        st.header('Tendencias Mensuales de Horas Extras')
        # ... y así sucesivamente para todos los gráficos y tablas de esta pestaña
        
    with tab2:
        # Aquí va toda la lógica de la Pestaña 2
        st.header('Desglose Organizacional')

    with tab3:
        # Aquí va toda la lógica de la Pestaña 3
        st.header(f'Top {top_n_employees} Empleados')

    with tab_valor_hora:
        # Aquí va toda la lógica de la Pestaña Valor Hora
        st.header('Valores Promedio por Hora')

    with tab4:
        st.header('Tabla de Datos Brutos Filtrados')
        st.dataframe(format_st_dataframe(filtered_df))
        generate_download_buttons(filtered_df, 'datos_brutos_filtrados')
else:
    st.info("⬆️ Esperando a que se suba un archivo Excel.")
