import streamlit as st
import pandas as pd
import altair as alt
import io

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
[data-testid="stAltairChart"] {
    border-radius: 8px;
    overflow: hidden; /* Esto es clave para que el contenido del gráfico no se salga de los bordes redondeados */
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
    color: white; /* El texto aquí sí debe ser blanco */
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
    color: #333; /* Asegurar color oscuro en celdas */
}
.stDataFrame tbody td:first-child {
    text-align: left;
    font-weight: 500;
}

/* --- BOTONES DE DESCARGA --- */
div[data-testid="stDownloadButton"] button {
    background-color: var(--primary-color);
    color: white; /* El texto aquí sí debe ser blanco */
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

</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE CÁLCULO OPTIMIZADAS CON CACHÉ ---
def apply_filters(full_df, selections):
    """Aplica el diccionario de selecciones a un dataframe."""
    _df = full_df.copy()
    for col, values in selections.items():
        if values:
            _df = _df[_df[col].isin(values)]
    return _df

@st.cache_data
def calculate_monthly_trends(full_df, selections, cost_cols_map, quant_cols_map, selected_cost_keys, selected_quant_keys):
    """Calcula las tendencias mensuales para la Pestaña 1."""
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
    """Calcula las variaciones mensuales para la Pestaña 1."""
    if _df_trends.empty: return pd.DataFrame()
    df_var = _df_trends[['Mes', 'Total_Costos', 'Total_Cantidades']].copy()
    df_var['Variacion_Costos_Abs'] = df_var['Total_Costos'].diff().fillna(0)
    df_var['Variacion_Cantidades_Abs'] = df_var['Total_Cantidades'].diff().fillna(0)
    df_var['Variacion_Costos_Pct'] = df_var['Total_Costos'].pct_change().fillna(0) * 100
    df_var['Variacion_Cantidades_Pct'] = df_var['Total_Cantidades'].pct_change().fillna(0) * 100
    return df_var

@st.cache_data
def calculate_grouped_aggregation(full_df, selections, group_cols, cost_cols_map, quant_cols_map, selected_cost_keys, selected_quant_keys):
    """Función genérica para calcular agregaciones para la Pestaña 2."""
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
    """Calcula los totales por empleado para la Pestaña 3."""
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
    """Calcula el valor promedio de hora para la Pestaña 4."""
    _df = apply_filters(full_df, selections)
    if _df.empty: return pd.DataFrame()

    valor_hora_cols = [col for col in ['Hora Normal', 'Hora Extra al 50%', 'Hora Extra al 50% Sabados', 'Hora Extra al 100%', 'HE FC'] if col in _df.columns]
    if not valor_hora_cols:
        return pd.DataFrame()
    return _df.groupby(dimension)[valor_hora_cols].mean().reset_index()

# --- Título de la Aplicación ---
st.title('📊 Dashboard de Horas Extras HE_2025')
st.subheader('Análisis Interactivo de Costos y Cantidades de Horas Extras')

# --- Funciones Auxiliares ---
def format_st_dataframe(df_to_style):
    numeric_cols = df_to_style.select_dtypes(include='number').columns
    format_dict = {col: '{:,.2f}' for col in numeric_cols}
    return df_to_style.style.format(format_dict)

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
def load_and_clean_data(file_upload_obj):
    df_excel = pd.DataFrame()
    try:
        df_excel = pd.read_excel(file_upload_obj, sheet_name='Datos', dtype={'Legajo': str, 'CECO': str, 'Nivel': str})
    except Exception:
        try:
            df_excel = pd.read_excel(file_upload_obj, dtype={'Legajo': str, 'CECO': str, 'Nivel': str})
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

    # --- DEFINICIÓN Y ESTADO DE FILTROS ---
    st.sidebar.header('Filtros del Dashboard')
    cost_columns_options = {'Horas extras al 50 %': 'Horas extras al 50 %', 'Horas extras al 50 % Sabados': 'Horas extras al 50 % Sabados', 'Horas extras al 100%': 'Horas extras al 100%', 'Importe HE Fc': 'Importe HE Fc'}
    quantity_columns_options = {'Cantidad HE 50': 'Cantidad HE 50', 'Cant HE al 50 Sabados': 'Cant HE al 50 Sabados', 'Cantidad HE 100': 'Cantidad HE 100', 'Cantidad HE FC': 'Cantidad HE FC'}
    filter_cols_cascade = ['Gerencia', 'Ministerio', 'CECO', 'Ubicación', 'Función', 'Nivel', 'Sexo', 'Liquidación', 'Legajo', 'Mes']

    # Inicialización del estado de la sesión
    if 'final_selections' not in st.session_state:
        st.session_state.final_selections = {col: [] for col in filter_cols_cascade}
    if 'cost_types_ms' not in st.session_state:
        st.session_state.cost_types_ms = list(cost_columns_options.keys())
    if 'quantity_types_ms' not in st.session_state:
        st.session_state.quantity_types_ms = list(quantity_columns_options.keys())
    if 'cargar_todo_clicked' not in st.session_state:
        st.session_state.cargar_todo_clicked = False
    
    # --- BOTONES DE ACCIÓN ---
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button('🧹 Limpiar Filtros', use_container_width=True):
            st.session_state.final_selections = {col: [] for col in filter_cols_cascade}
            st.session_state.cost_types_ms = list(cost_columns_options.keys())
            st.session_state.quantity_types_ms = list(quantity_columns_options.keys())
            st.rerun()
    with col2:
        if st.button('📥 Cargar Todo', use_container_width=True):
            st.session_state.cargar_todo_clicked = True
            st.rerun()
    st.sidebar.markdown("---") 

    def get_sorted_unique_options(dataframe, column_name):
        if column_name in dataframe.columns:
            unique_values = dataframe[column_name].dropna().unique().tolist()
            if not unique_values: return []
            try:
                return sorted(unique_values, key=lambda x: int(x) if isinstance(x, str) and x.isdigit() else float('inf'))
            except (ValueError, TypeError):
                return sorted(unique_values)
        return []

    # --- LÓGICA DE FILTROS PRINCIPALES ---
    temp_selections = st.session_state.final_selections.copy()
    for col in filter_cols_cascade:
        df_options = df.copy()
        for other_col in filter_cols_cascade:
            if other_col != col and temp_selections.get(other_col):
                df_options = df_options[df_options[other_col].isin(temp_selections[other_col])]
        options = get_sorted_unique_options(df_options, col)
        
        default_selection = [s for s in temp_selections.get(col, []) if s in options]
        if st.session_state.cargar_todo_clicked:
            default_selection = options

        selection = st.sidebar.multiselect(f'Selecciona {col}(s):', options, default=default_selection, key=f"ms_{col}")
        temp_selections[col] = selection
    st.session_state.final_selections = temp_selections
    
    filtered_df = apply_filters(df, st.session_state.final_selections)
    
    # --- LÓGICA DE FILTROS DE TIPOS DE HORA (DINÁMICOS) ---
    top_n_employees = st.sidebar.slider('Mostrar Top N Empleados:', 5, 50, 10)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Selección de Tipos de Horas Extras")

    available_cost_options = [opt for opt, col in cost_columns_options.items() if col in filtered_df.columns and filtered_df[col].sum() > 0]
    available_quantity_options = [opt for opt, col in quantity_columns_options.items() if col in filtered_df.columns and filtered_df[col].sum() > 0]
    
    if st.session_state.cargar_todo_clicked:
        st.session_state.cost_types_ms = available_cost_options
        st.session_state.quantity_types_ms = available_quantity_options

    st.session_state.cost_types_ms = [s for s in st.session_state.cost_types_ms if s in available_cost_options]
    st.session_state.quantity_types_ms = [s for s in st.session_state.quantity_types_ms if s in available_quantity_options]

    st.sidebar.multiselect('Selecciona Tipos de Costo de HE:', options=available_cost_options, key='cost_types_ms')
    st.sidebar.multiselect('Selecciona Tipos de Cantidad de HE:', options=available_quantity_options, key='quantity_types_ms')
    
    if st.session_state.cargar_todo_clicked:
        st.session_state.cargar_todo_clicked = False
        st.rerun()

    st.info(f"Mostrando **{len(filtered_df)}** registros según los filtros aplicados.")
    
    # --- PESTAÑAS (Tabs) ---
    tab1, tab2, tab3, tab_valor_hora, tab4 = st.tabs(["📈 Resumen y Tendencias", "🏢 Desglose Organizacional", "👤 Empleados Destacados", "⚖️ Valor Hora", "📋 Datos Brutos"])
    
    with tab1:
        with st.container(border=True):
            with st.spinner("Generando análisis de tendencias..."):
                monthly_trends_agg = calculate_monthly_trends(df, st.session_state.final_selections, cost_columns_options, quantity_columns_options, st.session_state.cost_types_ms, st.session_state.quantity_types_ms)
                
                if monthly_trends_agg.empty:
                    st.warning("No hay datos para mostrar con los filtros seleccionados.")
                else:
                    total_row = monthly_trends_agg.sum(numeric_only=True).to_frame().T
                    total_row['Mes'] = 'TOTAL'
                    monthly_trends_agg_with_total = pd.concat([monthly_trends_agg, total_row], ignore_index=True)
                    st.header('Tendencias Mensuales de Horas Extras')
                    
                    cost_color_domain = list(cost_columns_options.keys())
                    quantity_color_domain = list(quantity_columns_options.keys())
                    color_range = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

                    col1, col2 = st.columns(2)
                    with col1:
                        chart_data = monthly_trends_agg 
                        max_cost = chart_data['Total_Costos'].max()
                        y_scale_cost = alt.Scale(domain=[0, max_cost * 1.15]) if max_cost > 0 else alt.Scale()
                        
                        cost_bars_vars = [cost_columns_options[k] for k in st.session_state.cost_types_ms]
                        monthly_trends_costos_melted_bars = chart_data.melt('Mes', value_vars=cost_bars_vars, var_name='Tipo de Costo HE', value_name='Costo ($)')
                        
                        bars_costos = alt.Chart(monthly_trends_costos_melted_bars).mark_bar().encode(x='Mes', y=alt.Y('Costo ($):Q', stack='zero', scale=y_scale_cost), color=alt.Color('Tipo de Costo HE', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300), scale=alt.Scale(domain=cost_color_domain, range=color_range)))
                        line_costos = alt.Chart(chart_data).mark_line(color='black', point=alt.OverlayMarkDef(filled=False, fill='white', color='black'), strokeWidth=2).encode(x='Mes', y=alt.Y('Total_Costos:Q', title='Costo ($)', scale=y_scale_cost), tooltip=[alt.Tooltip('Mes'), alt.Tooltip('Total_Costos', title='Total', format=',.2f')])
                        
                        text_costos = line_costos.mark_text(
                            align='center',
                            baseline='bottom',
                            dy=-10,
                            color='black'
                        ).encode(
                            text=alt.Text('Total_Costos:Q', format=',.0f')
                        )

                        chart_costos_mensual = alt.layer(bars_costos, line_costos, text_costos).resolve_scale(y='shared').properties(title=alt.TitleParams('Costos Mensuales', anchor='middle')).interactive()
                        st.altair_chart(chart_costos_mensual, use_container_width=True)

                    with col2:
                        chart_data = monthly_trends_agg
                        max_quant = chart_data['Total_Cantidades'].max()
                        y_scale_quant = alt.Scale(domain=[0, max_quant * 1.15]) if max_quant > 0 else alt.Scale()

                        quantity_bars_vars = [quantity_columns_options[k] for k in st.session_state.quantity_types_ms]
                        monthly_trends_cantidades_melted_bars = chart_data.melt('Mes', value_vars=quantity_bars_vars, var_name='Tipo de Cantidad HE', value_name='Cantidad')
                        
                        bars_cantidades = alt.Chart(monthly_trends_cantidades_melted_bars).mark_bar().encode(x='Mes', y=alt.Y('Cantidad:Q', stack='zero', scale=y_scale_quant), color=alt.Color('Tipo de Cantidad HE', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300), scale=alt.Scale(domain=quantity_color_domain, range=color_range)))
                        line_cantidades = alt.Chart(chart_data).mark_line(color='black', point=alt.OverlayMarkDef(filled=False, fill='white', color='black'), strokeWidth=2).encode(x='Mes', y=alt.Y('Total_Cantidades:Q', title='Cantidad', scale=y_scale_quant), tooltip=[alt.Tooltip('Mes'), alt.Tooltip('Total_Cantidades', title='Total', format=',.0f')])
                        
                        text_cantidades = line_cantidades.mark_text(
                            align='center',
                            baseline='bottom',
                            dy=-10,
                            color='black'
                        ).encode(
                            text=alt.Text('Total_Cantidades:Q', format=',.0f')
                        )
                        
                        chart_cantidades_mensual = alt.layer(bars_cantidades, line_cantidades, text_cantidades).resolve_scale(y='shared').properties(title=alt.TitleParams('Cantidades Mensuales', anchor='middle')).interactive()
                        st.altair_chart(chart_cantidades_mensual, use_container_width=True)
                    
                    st.subheader('Tabla de Tendencias Mensuales')
                    st.dataframe(format_st_dataframe(monthly_trends_agg_with_total), use_container_width=True)
                    generate_download_buttons(monthly_trends_agg_with_total, 'tendencias_mensuales', 'tab1_trends')

        with st.container(border=True):
            monthly_trends_agg = calculate_monthly_trends(df, st.session_state.final_selections, cost_columns_options, quantity_columns_options, st.session_state.cost_types_ms, st.session_state.quantity_types_ms)
            if not monthly_trends_agg.empty and len(monthly_trends_agg) > 1:
                with st.spinner("Calculando variaciones mensuales..."):
                    monthly_trends_for_var = calculate_monthly_variations(monthly_trends_agg)
                    st.header('Análisis de Variaciones Mensuales')
                    col1, col2 = st.columns(2)
                    with col1:
                        base_var_costos = alt.Chart(monthly_trends_for_var).properties(title=alt.TitleParams('Variación Mensual de Costos', anchor='middle'))
                        bars_var_costos = base_var_costos.mark_bar().encode(
                            x=alt.X('Mes'), 
                            y=alt.Y('Variacion_Costos_Abs', title='Variación de Costos ($)'), 
                            color=alt.condition(alt.datum.Variacion_Costos_Abs > 0, alt.value('#2ca02c'), alt.value('#d62728'))
                        )
                        text_pos_costos = bars_var_costos.mark_text(align='center', baseline='bottom', dy=-4, color='#333').encode(text=alt.Text('Variacion_Costos_Abs:Q', format=',.0f')).transform_filter(alt.datum.Variacion_Costos_Abs >= 0)
                        text_neg_costos = bars_var_costos.mark_text(align='center', baseline='top', dy=4, color='#333').encode(text=alt.Text('Variacion_Costos_Abs:Q', format=',.0f')).transform_filter(alt.datum.Variacion_Costos_Abs < 0)
                        st.altair_chart((bars_var_costos + text_pos_costos + text_neg_costos).interactive(), use_container_width=True)

                    with col2:
                        base_var_cant = alt.Chart(monthly_trends_for_var).properties(title=alt.TitleParams('Variación Mensual de Cantidades', anchor='middle'))
                        bars_var_cant = base_var_cant.mark_bar().encode(
                            x=alt.X('Mes'), 
                            y=alt.Y('Variacion_Cantidades_Abs', title='Variación de Cantidades'), 
                            color=alt.condition(alt.datum.Variacion_Cantidades_Abs > 0, alt.value('#2ca02c'), alt.value('#d62728'))
                        )
                        text_pos_cant = bars_var_cant.mark_text(align='center', baseline='bottom', dy=-4, color='#333').encode(text=alt.Text('Variacion_Cantidades_Abs:Q', format=',.0f')).transform_filter(alt.datum.Variacion_Cantidades_Abs >= 0)
                        text_neg_cant = bars_var_cant.mark_text(align='center', baseline='top', dy=4, color='#333').encode(text=alt.Text('Variacion_Cantidades_Abs:Q', format=',.0f')).transform_filter(alt.datum.Variacion_Cantidades_Abs < 0)
                        st.altair_chart((bars_var_cant + text_pos_cant + text_neg_cant).interactive(), use_container_width=True)

                    st.subheader('Tabla de Variaciones Mensuales')
                    df_variaciones = monthly_trends_for_var[['Mes', 'Total_Costos', 'Variacion_Costos_Abs', 'Variacion_Costos_Pct', 'Total_Cantidades', 'Variacion_Cantidades_Abs', 'Variacion_Cantidades_Pct']]
                    st.dataframe(format_st_dataframe(df_variaciones), use_container_width=True)
                    generate_download_buttons(df_variaciones, 'variaciones_mensuales', 'tab1_var')
    
    with tab2:
        with st.spinner("Generando desgloses organizacionales..."):
            # Gerencia y Ministerio
            with st.container(border=True):
                df_grouped_gm = calculate_grouped_aggregation(df, st.session_state.final_selections, ['Gerencia', 'Ministerio'], cost_columns_options, quantity_columns_options, st.session_state.cost_types_ms, st.session_state.quantity_types_ms)
                st.header('Distribución por Gerencia y Ministerio')
                if df_grouped_gm.empty: st.warning("No hay datos para 'Gerencia y Ministerio' con los filtros seleccionados.")
                else:
                    total_gm = df_grouped_gm.sum(numeric_only=True).to_frame().T; total_gm['Gerencia'], total_gm['Ministerio'] = 'TOTAL', ''
                    df_grouped_gm_with_total = pd.concat([df_grouped_gm, total_gm], ignore_index=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        bars = alt.Chart(df_grouped_gm).mark_bar().encode(x=alt.X('Total_Costos:Q', title="Total Costos ($)"), y=alt.Y('Gerencia:N', sort=alt.SortField(field="Total_Costos", op="sum", order="descending"), title="Gerencia"), color='Ministerio')
                        text_total = alt.Chart(df_grouped_gm).transform_aggregate(total_cost='sum(Total_Costos)', groupby=['Gerencia']).mark_text(align='left', baseline='middle', dx=3).encode(x='total_cost:Q', y=alt.Y('Gerencia:N', sort=alt.SortField(field="Total_Costos", op="sum", order="descending")), text=alt.Text('total_cost:Q', format=',.0f'))
                        st.altair_chart((bars + text_total).properties(title='Costos').interactive(), use_container_width=True)
                    with col2:
                        bars = alt.Chart(df_grouped_gm).mark_bar().encode(x=alt.X('Total_Cantidades:Q', title="Total Cantidades"), y=alt.Y('Gerencia:N', sort=alt.SortField(field="Total_Cantidades", op="sum", order="descending"), title="Gerencia"), color='Ministerio')
                        text_total = alt.Chart(df_grouped_gm).transform_aggregate(total_quant='sum(Total_Cantidades)', groupby=['Gerencia']).mark_text(align='left', baseline='middle', dx=3).encode(x='total_quant:Q', y=alt.Y('Gerencia:N', sort=alt.SortField(field="Total_Cantidades", op="sum", order="descending")), text=alt.Text('total_quant:Q', format=',.0f'))
                        st.altair_chart((bars + text_total).properties(title='Cantidades').interactive(), use_container_width=True)
                    st.subheader('Tabla de Distribución'); st.dataframe(format_st_dataframe(df_grouped_gm_with_total), use_container_width=True)
                    generate_download_buttons(df_grouped_gm_with_total, 'dist_gerencia_ministerio', 'tab2_gm')
            
            # Gerencia y Sexo
            with st.container(border=True):
                df_grouped_gs = calculate_grouped_aggregation(df, st.session_state.final_selections, ['Gerencia', 'Sexo'], cost_columns_options, quantity_columns_options, st.session_state.cost_types_ms, st.session_state.quantity_types_ms)
                st.header('Distribución por Gerencia y Sexo')
                if not df_grouped_gs.empty:
                    total_gs = df_grouped_gs.sum(numeric_only=True).to_frame().T; total_gs['Gerencia'], total_gs['Sexo'] = 'TOTAL', ''
                    df_grouped_gs_with_total = pd.concat([df_grouped_gs, total_gs], ignore_index=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        bars = alt.Chart(df_grouped_gs).mark_bar().encode(x=alt.X('Total_Costos:Q', title="Total Costos ($)"), y=alt.Y('Gerencia:N', sort=alt.SortField(field="Total_Costos", op="sum", order="descending"), title="Gerencia"), color='Sexo')
                        text_total = alt.Chart(df_grouped_gs).transform_aggregate(total_cost='sum(Total_Costos)', groupby=['Gerencia']).mark_text(align='left', baseline='middle', dx=3).encode(x='total_cost:Q', y=alt.Y('Gerencia:N', sort=alt.SortField(field="Total_Costos", op="sum", order="descending")), text=alt.Text('total_cost:Q', format=',.0f'))
                        st.altair_chart((bars + text_total).properties(title='Costos').interactive(), use_container_width=True)
                    with col2:
                        bars = alt.Chart(df_grouped_gs).mark_bar().encode(x=alt.X('Total_Cantidades:Q', title="Total Cantidades"), y=alt.Y('Gerencia:N', sort=alt.SortField(field="Total_Cantidades", op="sum", order="descending"), title="Gerencia"), color='Sexo')
                        text_total = alt.Chart(df_grouped_gs).transform_aggregate(total_quant='sum(Total_Cantidades)', groupby=['Gerencia']).mark_text(align='left', baseline='middle', dx=3).encode(x='total_quant:Q', y=alt.Y('Gerencia:N', sort=alt.SortField(field="Total_Cantidades", op="sum", order="descending")), text=alt.Text('total_quant:Q', format=',.0f'))
                        st.altair_chart((bars + text_total).properties(title='Cantidades').interactive(), use_container_width=True)
                    st.subheader('Tabla de Distribución'); st.dataframe(format_st_dataframe(df_grouped_gs_with_total), use_container_width=True)
                    generate_download_buttons(df_grouped_gs_with_total, 'dist_gerencia_sexo', 'tab2_gs')

            # Ministerio y Sexo
            with st.container(border=True):
                df_grouped_ms = calculate_grouped_aggregation(df, st.session_state.final_selections, ['Ministerio', 'Sexo'], cost_columns_options, quantity_columns_options, st.session_state.cost_types_ms, st.session_state.quantity_types_ms)
                st.header('Distribución por Ministerio y Sexo')
                if not df_grouped_ms.empty:
                    total_ms = df_grouped_ms.sum(numeric_only=True).to_frame().T; total_ms['Ministerio'], total_ms['Sexo'] = 'TOTAL', ''
                    df_grouped_ms_with_total = pd.concat([df_grouped_ms, total_ms], ignore_index=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        bars = alt.Chart(df_grouped_ms).mark_bar().encode(x=alt.X('Total_Costos:Q', title="Total Costos ($)"), y=alt.Y('Ministerio:N', sort=alt.SortField(field="Total_Costos", op="sum", order="descending"), title="Ministerio"), color='Sexo')
                        text_total = alt.Chart(df_grouped_ms).transform_aggregate(total_cost='sum(Total_Costos)', groupby=['Ministerio']).mark_text(align='left', baseline='middle', dx=3).encode(x='total_cost:Q', y=alt.Y('Ministerio:N', sort=alt.SortField(field="Total_Costos", op="sum", order="descending")), text=alt.Text('total_cost:Q', format=',.0f'))
                        st.altair_chart((bars + text_total).properties(title='Costos').interactive(), use_container_width=True)
                    with col2:
                        bars = alt.Chart(df_grouped_ms).mark_bar().encode(x=alt.X('Total_Cantidades:Q', title="Total Cantidades"), y=alt.Y('Ministerio:N', sort=alt.SortField(field="Total_Cantidades", op="sum", order="descending"), title="Ministerio"), color='Sexo')
                        text_total = alt.Chart(df_grouped_ms).transform_aggregate(total_quant='sum(Total_Cantidades)', groupby=['Ministerio']).mark_text(align='left', baseline='middle', dx=3).encode(x='total_quant:Q', y=alt.Y('Ministerio:N', sort=alt.SortField(field="Total_Cantidades", op="sum", order="descending")), text=alt.Text('total_quant:Q', format=',.0f'))
                        st.altair_chart((bars + text_total).properties(title='Cantidades').interactive(), use_container_width=True)
                    st.subheader('Tabla de Distribución'); st.dataframe(format_st_dataframe(df_grouped_ms_with_total), use_container_width=True)
                    generate_download_buttons(df_grouped_ms_with_total, 'dist_ministerio_sexo', 'tab2_ms')

            # Nivel y Sexo
            with st.container(border=True):
                df_grouped_ns = calculate_grouped_aggregation(df, st.session_state.final_selections, ['Nivel', 'Sexo'], cost_columns_options, quantity_columns_options, st.session_state.cost_types_ms, st.session_state.quantity_types_ms)
                st.header('Distribución por Nivel y Sexo')
                if not df_grouped_ns.empty:
                    total_ns = df_grouped_ns.sum(numeric_only=True).to_frame().T; total_ns['Nivel'], total_ns['Sexo'] = 'TOTAL', ''
                    df_grouped_ns_with_total = pd.concat([df_grouped_ns, total_ns], ignore_index=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        bars = alt.Chart(df_grouped_ns).mark_bar().encode(x=alt.X('Total_Costos:Q', title="Total Costos ($)"), y=alt.Y('Nivel:N', sort=alt.SortField(field="Total_Costos", op="sum", order="descending"), title="Nivel"), color='Sexo')
                        text_total = alt.Chart(df_grouped_ns).transform_aggregate(total_cost='sum(Total_Costos)', groupby=['Nivel']).mark_text(align='left', baseline='middle', dx=3).encode(x='total_cost:Q', y=alt.Y('Nivel:N', sort=alt.SortField(field="Total_Costos", op="sum", order="descending")), text=alt.Text('total_cost:Q', format=',.0f'))
                        st.altair_chart((bars + text_total).properties(title='Costos').interactive(), use_container_width=True)
                    with col2:
                        bars = alt.Chart(df_grouped_ns).mark_bar().encode(x=alt.X('Total_Cantidades:Q', title="Total Cantidades"), y=alt.Y('Nivel:N', sort=alt.SortField(field="Total_Cantidades", op="sum", order="descending"), title="Nivel"), color='Sexo')
                        text_total = alt.Chart(df_grouped_ns).transform_aggregate(total_quant='sum(Total_Cantidades)', groupby=['Nivel']).mark_text(align='left', baseline='middle', dx=3).encode(x='total_quant:Q', y=alt.Y('Nivel:N', sort=alt.SortField(field="Total_Cantidades", op="sum", order="descending")), text=alt.Text('total_quant:Q', format=',.0f'))
                        st.altair_chart((bars + text_total).properties(title='Cantidades').interactive(), use_container_width=True)
                    st.subheader('Tabla de Distribución'); st.dataframe(format_st_dataframe(df_grouped_ns_with_total), use_container_width=True)
                    generate_download_buttons(df_grouped_ns_with_total, 'dist_nivel_sexo', 'tab2_ns')

            # Función y Sexo
            with st.container(border=True):
                df_grouped_fs = calculate_grouped_aggregation(df, st.session_state.final_selections, ['Función', 'Sexo'], cost_columns_options, quantity_columns_options, st.session_state.cost_types_ms, st.session_state.quantity_types_ms)
                st.header('Distribución por Función y Sexo')
                if not df_grouped_fs.empty:
                    total_fs = df_grouped_fs.sum(numeric_only=True).to_frame().T; total_fs['Función'], total_fs['Sexo'] = 'TOTAL', ''
                    df_grouped_fs_with_total = pd.concat([df_grouped_fs, total_fs], ignore_index=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        bars = alt.Chart(df_grouped_fs).mark_bar().encode(x=alt.X('Total_Costos:Q', title="Total Costos ($)"), y=alt.Y('Función:N', sort=alt.SortField(field="Total_Costos", op="sum", order="descending"), title="Función"), color='Sexo')
                        text_total = alt.Chart(df_grouped_fs).transform_aggregate(total_cost='sum(Total_Costos)', groupby=['Función']).mark_text(align='left', baseline='middle', dx=3).encode(x='total_cost:Q', y=alt.Y('Función:N', sort=alt.SortField(field="Total_Costos", op="sum", order="descending")), text=alt.Text('total_cost:Q', format=',.0f'))
                        st.altair_chart((bars + text_total).properties(title='Costos').interactive(), use_container_width=True)
                    with col2:
                        bars = alt.Chart(df_grouped_fs).mark_bar().encode(x=alt.X('Total_Cantidades:Q', title="Total Cantidades"), y=alt.Y('Función:N', sort=alt.SortField(field="Total_Cantidades", op="sum", order="descending"), title="Función"), color='Sexo')
                        text_total = alt.Chart(df_grouped_fs).transform_aggregate(total_quant='sum(Total_Cantidades)', groupby=['Función']).mark_text(align='left', baseline='middle', dx=3).encode(x='total_quant:Q', y=alt.Y('Función:N', sort=alt.SortField(field="Total_Cantidades", op="sum", order="descending")), text=alt.Text('total_quant:Q', format=',.0f'))
                        st.altair_chart((bars + text_total).properties(title='Cantidades').interactive(), use_container_width=True)
                    st.subheader('Tabla de Distribución'); st.dataframe(format_st_dataframe(df_grouped_fs_with_total), use_container_width=True)
                    generate_download_buttons(df_grouped_fs_with_total, 'dist_funcion_sexo', 'tab2_fs')

    with tab3:
        with st.container(border=True):
            with st.spinner("Calculando ranking de empleados..."):
                employee_overtime = calculate_employee_overtime(df, st.session_state.final_selections, cost_columns_options, quantity_columns_options, st.session_state.cost_types_ms, st.session_state.quantity_types_ms)
                if employee_overtime.empty:
                    st.warning("No hay datos para mostrar con los filtros seleccionados.")
                else:
                    st.header(f'Top {top_n_employees} Empleados con Mayor Horas Extras')
                    top_costo_empleados = employee_overtime.nlargest(top_n_employees, 'Total_Costos')
                    top_cantidad_empleados = employee_overtime.nlargest(top_n_employees, 'Total_Cantidades')
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader('Top por Costo')
                        if not top_costo_empleados.empty:
                            base = alt.Chart(top_costo_empleados).encode(
                                y=alt.Y('Apellido y nombre:N', sort='-x', title='Empleado'), 
                                x=alt.X('Total_Costos:Q', title="Total Costos ($)")
                            )
                            bars = base.mark_bar(color='#6C5CE7')
                            text = base.mark_text(
                                align='right', 
                                baseline='middle', 
                                dx=-5, 
                                color='white'
                            ).encode(text=alt.Text('Total_Costos:Q', format='$,.0f'))
                            st.altair_chart((bars + text).properties(title=f'Top {top_n_employees} por Costo').interactive(), use_container_width=True)
                    with col2:
                        st.subheader('Top por Cantidad')
                        if not top_cantidad_empleados.empty:
                            base = alt.Chart(top_cantidad_empleados).encode(
                                y=alt.Y('Apellido y nombre:N', sort='-x', title='Empleado'), 
                                x=alt.X('Total_Cantidades:Q', title="Total Cantidades")
                            )
                            bars = base.mark_bar(color='#6C5CE7')
                            text = base.mark_text(
                                align='right', 
                                baseline='middle', 
                                dx=-5, 
                                color='white'
                            ).encode(text=alt.Text('Total_Cantidades:Q', format=',.0f'))
                            st.altair_chart((bars + text).properties(title=f'Top {top_n_employees} por Cantidad').interactive(), use_container_width=True)
                    st.subheader('Tabla de Top Empleados por Costo')
                    st.dataframe(format_st_dataframe(top_costo_empleados), use_container_width=True)
                    generate_download_buttons(top_costo_empleados, f'top_{top_n_employees}_costo', 'tab3_costo')
                    st.subheader('Tabla de Top Empleados por Cantidad')
                    st.dataframe(format_st_dataframe(top_cantidad_empleados), use_container_width=True)
                    generate_download_buttons(top_cantidad_empleados, f'top_{top_n_employees}_cantidad', 'tab3_cant')

    with tab_valor_hora:
        with st.container(border=True):
            with st.spinner("Calculando valores promedio por hora..."):
                st.header('Valores Promedio por Hora')
                grouping_dimension = st.selectbox('Selecciona la dimensión de desglose:', ['Gerencia', 'Legajo', 'Función', 'CECO', 'Ubicación', 'Nivel', 'Sexo'], key='valor_hora_grouping')
                df_valor_hora = calculate_average_hourly_rate(df, st.session_state.final_selections, grouping_dimension)
                if not df_valor_hora.empty:
                    st.dataframe(format_st_dataframe(df_valor_hora), use_container_width=True)
                    generate_download_buttons(df_valor_hora, f'valores_promedio_hora_por_{grouping_dimension}', 'tab_valor_hora')
                else:
                    st.warning("No hay datos de valor por hora con los filtros actuales o las columnas no existen.")

    with tab4:
        with st.container(border=True):
            st.header('Tabla de Datos Brutos Filtrados')
            st.dataframe(format_st_dataframe(filtered_df), use_container_width=True)
            generate_download_buttons(filtered_df, 'datos_brutos_filtrados', 'tab4_brutos')
else:
    st.info("⬆️ Esperando a que se suba un archivo Excel.")

