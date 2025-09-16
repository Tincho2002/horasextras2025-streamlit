import streamlit as st
import pandas as pd
import altair as alt
import io

# --- Configuración de la página ---
st.set_page_config(layout="wide")

# --- CSS Personalizado para un Estilo Profesional ---
st.markdown("""
<style>
/* --- GENERAL Y TIPOGRAFÍA --- */
.stApp {
    background-color: #f0f2f6; 
    font-size: 0.92rem;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #333;
}

/* --- COLORES BASE DEL TEMA --- */
[data-testid="stSidebar"],
[data-testid="stVerticalBlockBorderWrapper"],
.stTabs [data-basweb="tab"][aria-selected="true"] {
    background-color: #f8f7fc;
}

/* Estilo consistente para títulos y subtítulos */
h1, h2, h3 {
    font-weight: 600;
    color: #1a1a2e;
}
h1 { font-size: 2.2rem; border-bottom: 2px solid #6C5CE7; padding-bottom: 10px; margin-bottom: 20px;}
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
    background-color: #6C5CE7;
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
}
.stDataFrame tbody td:first-child {
    text-align: left;
    font-weight: 500;
}

/* --- BOTONES DE DESCARGA --- */
div[data-testid="stDownloadButton"] button {
    background-color: #6C5CE7;
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
    border-bottom: 3px solid #6C5CE7;
}

</style>
""", unsafe_allow_html=True)


# --- FUNCIONES DE CÁLCULO OPTIMIZADAS CON CACHÉ ---

@st.cache_data
def calculate_monthly_trends(_df, cost_cols_map, quant_cols_map, selected_cost_keys, selected_quant_keys):
    """Calcula las tendencias mensuales para la Pestaña 1."""
    cost_cols = [cost_cols_map[k] for k in selected_cost_keys]
    quant_cols = [quant_cols_map[k] for k in selected_quant_keys]
    
    agg_dict = {col: pd.NamedAgg(column=col, aggfunc='sum') for col in cost_cols + quant_cols if col in _df.columns}
    monthly_trends_agg = _df.groupby('Mes').agg(**agg_dict).reset_index().sort_values(by='Mes')
    
    monthly_trends_agg['Total_Costos'] = monthly_trends_agg[[col for col in cost_cols if col in monthly_trends_agg.columns]].sum(axis=1)
    monthly_trends_agg['Total_Cantidades'] = monthly_trends_agg[[col for col in quant_cols if col in monthly_trends_agg.columns]].sum(axis=1)
    return monthly_trends_agg

@st.cache_data
def calculate_monthly_variations(_df_trends):
    """Calcula las variaciones mensuales para la Pestaña 1."""
    df_var = _df_trends[['Mes', 'Total_Costos', 'Total_Cantidades']].copy()
    df_var['Variacion_Costos_Abs'] = df_var['Total_Costos'].diff().fillna(0)
    df_var['Variacion_Cantidades_Abs'] = df_var['Total_Cantidades'].diff().fillna(0)
    df_var['Variacion_Costos_Pct'] = df_var['Total_Costos'].pct_change().fillna(0) * 100
    df_var['Variacion_Cantidades_Pct'] = df_var['Total_Cantidades'].pct_change().fillna(0) * 100
    return df_var

@st.cache_data
def calculate_grouped_aggregation(_df, group_cols, cost_cols_map, quant_cols_map, selected_cost_keys, selected_quant_keys):
    """Función genérica para calcular agregaciones para la Pestaña 2."""
    cost_cols = [cost_cols_map[k] for k in selected_cost_keys]
    quant_cols = [quant_cols_map[k] for k in selected_quant_keys]

    agg_dict = {col: pd.NamedAgg(column=col, aggfunc='sum') for col in cost_cols + quant_cols if col in _df.columns}
    df_grouped = _df.groupby(group_cols).agg(**agg_dict).reset_index()

    df_grouped['Total_Costos'] = df_grouped[[col for col in cost_cols if col in df_grouped.columns]].sum(axis=1)
    df_grouped['Total_Cantidades'] = df_grouped[[col for col in quant_cols if col in df_grouped.columns]].sum(axis=1)
    return df_grouped

@st.cache_data
def calculate_employee_overtime(_df, cost_cols_map, quant_cols_map, selected_cost_keys, selected_quant_keys):
    """Calcula los totales por empleado para la Pestaña 3."""
    cost_cols = [cost_cols_map[k] for k in selected_cost_keys]
    quant_cols = [quant_cols_map[k] for k in selected_quant_keys]
    
    agg_cols = {}
    for col_name in cost_cols:
        if col_name in _df.columns: agg_cols[f'{col_name}_costo_agg'] = pd.NamedAgg(column=col_name, aggfunc='sum')
    for col_name in quant_cols:
        if col_name in _df.columns: agg_cols[f'{col_name}_cant_agg'] = pd.NamedAgg(column=col_name, aggfunc='sum')
    
    employee_overtime = _df.groupby(['Legajo', 'Apellido y nombre']).agg(**agg_cols).reset_index()

    total_cost_cols_for_sum = [f'{col}_costo_agg' for col in cost_cols if f'{col}_costo_agg' in employee_overtime.columns]
    employee_overtime['Total_Costos'] = employee_overtime[total_cost_cols_for_sum].sum(axis=1)

    total_quantity_cols_for_sum = [f'{col}_cant_agg' for col in quant_cols if f'{col}_cant_agg' in employee_overtime.columns]
    employee_overtime['Total_Cantidades'] = employee_overtime[total_quantity_cols_for_sum].sum(axis=1)
    return employee_overtime

@st.cache_data
def calculate_average_hourly_rate(_df, dimension):
    """Calcula el valor promedio de hora para la Pestaña 4."""
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

def generate_download_buttons(df_to_download, filename_prefix):
    st.markdown("<h6>Opciones de Descarga:</h6>", unsafe_allow_html=True)
    col_dl1, col_dl2, _ = st.columns([1,1,2])
    csv_buffer = io.StringIO()
    df_to_download.to_csv(csv_buffer, index=False)
    with col_dl1:
        st.download_button(label="⬇️ Descargar CSV", data=csv_buffer.getvalue(), file_name=f"{filename_prefix}.csv", mime="text/csv", key=f"csv_download_{filename_prefix}")
    excel_buffer = io.BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    with col_dl2:
        st.download_button(label="📊 Descargar Excel", data=excel_buffer.getvalue(), file_name=f"{filename_prefix}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"excel_download_{filename_prefix}")

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

    # --- INICIO SECCIÓN CORREGIDA ---
    st.sidebar.header('Filtros del Dashboard')

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button('🧹 Limpiar Filtros', use_container_width=True):
            st.session_state.final_selections = {}
            if 'cargar_todos' in st.session_state:
                st.session_state.cargar_todos = False
            st.rerun()
    with col2:
        if st.button('📥 Cargar Todo', use_container_width=True):
            st.session_state.cargar_todos = True
            st.rerun()

    st.sidebar.markdown("---")

    def get_sorted_unique_options(dataframe, column_name):
        if column_name in dataframe.columns:
            unique_values = dataframe[column_name].dropna().unique().tolist()
            if not unique_values: return []
            if column_name in ['Legajo', 'CECO']:
                numeric_vals, non_numeric_vals = [], []
                for val in unique_values:
                    try: numeric_vals.append(int(val))
                    except (ValueError, TypeError): non_numeric_vals.append(val)
                return [str(x) for x in sorted(numeric_vals)] + sorted(non_numeric_vals)
            return sorted(unique_values)
        return []

    filter_cols_cascade = ['Gerencia', 'Ministerio', 'CECO', 'Ubicación', 'Función', 'Nivel', 'Sexo', 'Liquidación', 'Legajo', 'Mes']

    if 'final_selections' not in st.session_state: st.session_state.final_selections = {}
    if 'cargar_todos' not in st.session_state: st.session_state.cargar_todos = False

    df_options_scope = df.copy()
    parent_changed = False
    new_selections = {}

    # PASO 1: Crear los widgets y recolectar las selecciones del usuario
    for col in filter_cols_cascade:
        options = get_sorted_unique_options(df_options_scope, col)
        last_selection = st.session_state.final_selections.get(col, [])
        
        if st.session_state.cargar_todos:
            default_value = options
        elif parent_changed:
            default_value = [] # Se resetea el hijo si el padre cambió
        else:
            default_value = [item for item in last_selection if item in options]
        
        selection = st.sidebar.multiselect(f'Selecciona {col}(s):', options, default=default_value, key=f"multiselect_{col}")
        
        if not parent_changed and set(selection) != set(default_value):
            parent_changed = True
            
        new_selections[col] = selection
        
        if selection:
            df_options_scope = df_options_scope[df_options_scope[col].isin(selection)]

    st.session_state.final_selections = new_selections
    if st.session_state.cargar_todos: st.session_state.cargar_todos = False

    # PASO 2: Aplicar todas las selecciones al dataframe principal
    filtered_df = df.copy()
    for col, selection in st.session_state.final_selections.items():
        if selection:
            filtered_df = filtered_df[filtered_df[col].isin(selection)]
            
    # --- FIN SECCIÓN CORREGIDA ---

    top_n_employees = st.sidebar.slider('Mostrar Top N Empleados:', 5, 50, 10)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Selección de Tipos de Horas Extras")
    cost_columns_options = {'Horas extras al 50 %': 'Horas extras al 50 %', 'Horas extras al 50 % Sabados': 'Horas extras al 50 % Sabados', 'Horas extras al 100%': 'Horas extras al 100%', 'Importe HE Fc': 'Importe HE Fc'}
    quantity_columns_options = {'Cantidad HE 50': 'Cantidad HE 50', 'Cant HE al 50 Sabados': 'Cant HE al 50 Sabados', 'Cantidad HE 100': 'Cantidad HE 100', 'Cantidad HE FC': 'Cantidad HE FC'}
    selected_cost_types_display = st.sidebar.multiselect('Selecciona Tipos de Costo de HE:', list(cost_columns_options.keys()), default=list(cost_columns_options.keys()), key='filter_cost_types')
    selected_quantity_types_display = st.sidebar.multiselect('Selecciona Tipos de Cantidad de HE:', list(quantity_columns_options.keys()), default=list(quantity_columns_options.keys()), key='filter_quantity_types')

    st.info(f"Mostrando **{len(filtered_df)}** registros según los filtros aplicados.")
    
    # --- PESTAÑAS (Tabs) ---
    tab1, tab2, tab3, tab_valor_hora, tab4 = st.tabs(["📈 Resumen y Tendencias", "🏢 Desglose Organizacional", "👤 Empleados Destacados", "⚖️ Valor Hora", "📋 Datos Brutos"])
    
    color_domain = ['Horas extras al 50 %', 'Horas extras al 50 % Sabados', 'Horas extras al 100%', 'Importe HE Fc', 'Cantidad HE 50', 'Cant HE al 50 Sabados', 'Cantidad HE 100', 'Cantidad HE FC']
    color_range = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    # ... (El resto del código para las pestañas permanece exactamente igual) ...
    with tab1:
        if filtered_df.empty:
            st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            with st.container(border=True):
                with st.spinner("Generando análisis de tendencias..."):
                    monthly_trends_agg = calculate_monthly_trends(filtered_df, cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                    
                    if not monthly_trends_agg.empty:
                        total_row = monthly_trends_agg.sum(numeric_only=True).to_frame().T
                        total_row['Mes'] = 'TOTAL'
                        monthly_trends_agg_with_total = pd.concat([monthly_trends_agg, total_row], ignore_index=True)
                    else:
                        monthly_trends_agg_with_total = monthly_trends_agg
    
                    st.header('Tendencias Mensuales de Horas Extras')
                    col1, col2 = st.columns(2)
                    with col1:
                        chart_data = monthly_trends_agg
                        cost_bars_vars = [cost_columns_options[k] for k in selected_cost_types_display]
                        monthly_trends_costos_melted_bars = chart_data.melt('Mes', value_vars=cost_bars_vars, var_name='Tipo de Costo HE', value_name='Costo ($)')
                        bars_costos = alt.Chart(monthly_trends_costos_melted_bars).mark_bar().encode(x='Mes', y=alt.Y('Costo ($):Q', stack='zero'), color=alt.Color('Tipo de Costo HE', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300), scale=alt.Scale(domain=color_domain, range=color_range)))
                        line_costos = alt.Chart(chart_data).mark_line(color='black', point=alt.OverlayMarkDef(filled=False, fill='white', color='black'), strokeWidth=2).encode(x='Mes', y=alt.Y('Total_Costos:Q', title='Costo ($)'), tooltip=[alt.Tooltip('Mes'), alt.Tooltip('Total_Costos', title='Total', format=',.2f')])
                        chart_costos_mensual = alt.layer(bars_costos, line_costos).resolve_scale(y='shared').properties(title=alt.TitleParams('Costos Mensuales', anchor='middle')).interactive()
                        st.altair_chart(chart_costos_mensual, use_container_width=True)
                    with col2:
                        chart_data = monthly_trends_agg
                        quantity_bars_vars = [quantity_columns_options[k] for k in selected_quantity_types_display]
                        monthly_trends_cantidades_melted_bars = chart_data.melt('Mes', value_vars=quantity_bars_vars, var_name='Tipo de Cantidad HE', value_name='Cantidad')
                        bars_cantidades = alt.Chart(monthly_trends_cantidades_melted_bars).mark_bar().encode(x='Mes', y=alt.Y('Cantidad:Q', stack='zero'), color=alt.Color('Tipo de Cantidad HE', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300), scale=alt.Scale(domain=color_domain, range=color_range)))
                        line_cantidades = alt.Chart(chart_data).mark_line(color='black', point=alt.OverlayMarkDef(filled=False, fill='white', color='black'), strokeWidth=2).encode(x='Mes', y=alt.Y('Total_Cantidades:Q', title='Cantidad'), tooltip=[alt.Tooltip('Mes'), alt.Tooltip('Total_Cantidades', title='Total', format=',.0f')])
                        chart_cantidades_mensual = alt.layer(bars_cantidades, line_cantidades).resolve_scale(y='shared').properties(title=alt.TitleParams('Cantidades Mensuales', anchor='middle')).interactive()
                        st.altair_chart(chart_cantidades_mensual, use_container_width=True)
                    
                    st.subheader('Tabla de Tendencias Mensuales')
                    st.dataframe(format_st_dataframe(monthly_trends_agg_with_total), use_container_width=True)
                    generate_download_buttons(monthly_trends_agg_with_total, 'tendencias_mensuales')

            with st.container(border=True):
                with st.spinner("Calculando variaciones mensuales..."):
                    monthly_trends_for_var = calculate_monthly_variations(monthly_trends_agg)
                    st.header('Análisis de Variaciones Mensuales')
                    col1, col2 = st.columns(2)
                    with col1:
                        chart_var_costos = alt.Chart(monthly_trends_for_var).mark_bar().encode(x=alt.X('Mes'), y=alt.Y('Variacion_Costos_Abs', title='Variación de Costos ($)'), color=alt.condition(alt.datum.Variacion_Costos_Abs > 0, alt.value('green'), alt.value('red'))).properties(title=alt.TitleParams('Variación Mensual de Costos', anchor='middle')).interactive()
                        st.altair_chart(chart_var_costos, use_container_width=True)
                    with col2:
                        chart_var_cantidades = alt.Chart(monthly_trends_for_var).mark_bar().encode(x=alt.X('Mes'), y=alt.Y('Variacion_Cantidades_Abs', title='Variación de Cantidades'), color=alt.condition(alt.datum.Variacion_Cantidades_Abs > 0, alt.value('green'), alt.value('red'))).properties(title=alt.TitleParams('Variación Mensual de Cantidades', anchor='middle')).interactive()
                        st.altair_chart(chart_var_cantidades, use_container_width=True)

                    st.subheader('Tabla de Variaciones Mensuales')
                    df_variaciones = monthly_trends_for_var[['Mes', 'Total_Costos', 'Variacion_Costos_Abs', 'Variacion_Costos_Pct', 'Total_Cantidades', 'Variacion_Cantidades_Abs', 'Variacion_Cantidades_Pct']]
                    st.dataframe(format_st_dataframe(df_variaciones), use_container_width=True)
                    generate_download_buttons(monthly_trends_for_var, 'variaciones_mensuales')
    
    with tab2:
        if filtered_df.empty: st.warning("No hay datos para mostrar.")
        else:
            with st.spinner("Generando desgloses organizacionales..."):
                with st.container(border=True):
                    df_grouped_gm = calculate_grouped_aggregation(filtered_df, ['Gerencia', 'Ministerio'], cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                    if not df_grouped_gm.empty:
                        total_gm = df_grouped_gm.sum(numeric_only=True).to_frame().T
                        total_gm['Gerencia'] = 'TOTAL'
                        total_gm['Ministerio'] = ''
                        df_grouped_gm_with_total = pd.concat([df_grouped_gm, total_gm], ignore_index=True)
                    else:
                        df_grouped_gm_with_total = df_grouped_gm
                    st.header('Distribución por Gerencia y Ministerio')
                    col1, col2 = st.columns(2)
                    with col1:
                        chart_costos_gm = alt.Chart(df_grouped_gm).mark_bar().encode(x='Total_Costos', y=alt.Y('Gerencia:N', sort='-x'), color=alt.Color('Ministerio', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Costos por Gerencia y Ministerio', anchor='middle'))
                        st.altair_chart(chart_costos_gm, use_container_width=True)
                    with col2:
                        chart_cantidades_gm = alt.Chart(df_grouped_gm).mark_bar().encode(x='Total_Cantidades', y=alt.Y('Gerencia:N', sort='-x'), color=alt.Color('Ministerio', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Cantidades por Gerencia y Ministerio', anchor='middle'))
                        st.altair_chart(chart_cantidades_gm, use_container_width=True)
                    st.subheader('Tabla de Distribución')
                    st.dataframe(format_st_dataframe(df_grouped_gm_with_total), use_container_width=True)
                    generate_download_buttons(df_grouped_gm_with_total, 'distribucion_gerencia_ministerio')

                with st.container(border=True):
                    df_grouped_gs = calculate_grouped_aggregation(filtered_df, ['Gerencia', 'Sexo'], cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                    if not df_grouped_gs.empty:
                        total_gs = df_grouped_gs.sum(numeric_only=True).to_frame().T
                        total_gs['Gerencia'] = 'TOTAL'
                        total_gs['Sexo'] = ''
                        df_grouped_gs_with_total = pd.concat([df_grouped_gs, total_gs], ignore_index=True)
                    else:
                        df_grouped_gs_with_total = df_grouped_gs
                    st.header('Distribución por Gerencia y Sexo')
                    col1, col2 = st.columns(2)
                    with col1:
                        chart_costos_gs = alt.Chart(df_grouped_gs).mark_bar().encode(x='Total_Costos', y=alt.Y('Gerencia:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Costos por Gerencia y Sexo', anchor='middle')).interactive()
                        st.altair_chart(chart_costos_gs, use_container_width=True)
                    with col2:
                        chart_cantidades_gs = alt.Chart(df_grouped_gs).mark_bar().encode(x='Total_Cantidades', y=alt.Y('Gerencia:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Cantidades por Gerencia y Sexo', anchor='middle')).interactive()
                        st.altair_chart(chart_cantidades_gs, use_container_width=True)
                    st.subheader('Tabla de Distribución')
                    st.dataframe(format_st_dataframe(df_grouped_gs_with_total), use_container_width=True)
                    generate_download_buttons(df_grouped_gs_with_total, 'distribucion_gerencia_sexo')

                with st.container(border=True):
                    df_grouped_ms = calculate_grouped_aggregation(filtered_df, ['Ministerio', 'Sexo'], cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                    if not df_grouped_ms.empty:
                        total_ms = df_grouped_ms.sum(numeric_only=True).to_frame().T
                        total_ms['Ministerio'] = 'TOTAL'
                        total_ms['Sexo'] = ''
                        df_grouped_ms_with_total = pd.concat([df_grouped_ms, total_ms], ignore_index=True)
                    else:
                        df_grouped_ms_with_total = df_grouped_ms
                    st.header('Distribución por Ministerio y Sexo')
                    col1, col2 = st.columns(2)
                    with col1:
                        chart_costos_ms = alt.Chart(df_grouped_ms).mark_bar().encode(x='Total_Costos', y=alt.Y('Ministerio:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Costos por Ministerio y Sexo', anchor='middle')).interactive()
                        st.altair_chart(chart_costos_ms, use_container_width=True)
                    with col2:
                        chart_cantidades_ms = alt.Chart(df_grouped_ms).mark_bar().encode(x='Total_Cantidades', y=alt.Y('Ministerio:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Cantidades por Ministerio y Sexo', anchor='middle')).interactive()
                        st.altair_chart(chart_cantidades_ms, use_container_width=True)
                    st.subheader('Tabla de Distribución')
                    st.dataframe(format_st_dataframe(df_grouped_ms_with_total), use_container_width=True)
                    generate_download_buttons(df_grouped_ms_with_total, 'distribucion_ministerio_sexo')

                with st.container(border=True):
                    df_grouped_ns = calculate_grouped_aggregation(filtered_df, ['Nivel', 'Sexo'], cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                    if not df_grouped_ns.empty:
                        total_ns = df_grouped_ns.sum(numeric_only=True).to_frame().T
                        total_ns['Nivel'] = 'TOTAL'
                        total_ns['Sexo'] = ''
                        df_grouped_ns_with_total = pd.concat([df_grouped_ns, total_ns], ignore_index=True)
                    else:
                        df_grouped_ns_with_total = df_grouped_ns
                    st.header('Distribución por Nivel y Sexo')
                    col1, col2 = st.columns(2)
                    with col1:
                        chart_costos_ns = alt.Chart(df_grouped_ns).mark_bar().encode(x='Total_Costos', y=alt.Y('Nivel:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Costos por Nivel y Sexo', anchor='middle')).interactive()
                        st.altair_chart(chart_costos_ns, use_container_width=True)
                    with col2:
                        chart_cantidades_ns = alt.Chart(df_grouped_ns).mark_bar().encode(x='Total_Cantidades', y=alt.Y('Nivel:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Cantidades por Nivel y Sexo', anchor='middle')).interactive()
                        st.altair_chart(chart_cantidades_ns, use_container_width=True)
                    st.subheader('Tabla de Distribución')
                    st.dataframe(format_st_dataframe(df_grouped_ns_with_total), use_container_width=True)
                    generate_download_buttons(df_grouped_ns_with_total, 'distribucion_nivel_sexo')

                with st.container(border=True):
                    df_grouped_fs = calculate_grouped_aggregation(filtered_df, ['Función', 'Sexo'], cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                    if not df_grouped_fs.empty:
                        total_fs = df_grouped_fs.sum(numeric_only=True).to_frame().T
                        total_fs['Función'] = 'TOTAL'
                        total_fs['Sexo'] = ''
                        df_grouped_fs_with_total = pd.concat([df_grouped_fs, total_fs], ignore_index=True)
                    else:
                        df_grouped_fs_with_total = df_grouped_fs
                    st.header('Distribución por Función y Sexo')
                    col1, col2 = st.columns(2)
                    with col1:
                        chart_costos_fs = alt.Chart(df_grouped_fs).mark_bar().encode(x='Total_Costos', y=alt.Y('Función:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Costos por Función y Sexo', anchor='middle')).interactive()
                        st.altair_chart(chart_costos_fs, use_container_width=True)
                    with col2:
                        chart_cantidades_fs = alt.Chart(df_grouped_fs).mark_bar().encode(x='Total_Cantidades', y=alt.Y('Función:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Cantidades por Función y Sexo', anchor='middle')).interactive()
                        st.altair_chart(chart_cantidades_fs, use_container_width=True)
                    st.subheader('Tabla de Distribución')
                    st.dataframe(format_st_dataframe(df_grouped_fs_with_total), use_container_width=True)
                    generate_download_buttons(df_grouped_fs_with_total, 'distribucion_funcion_sexo')

    with tab3:
        if filtered_df.empty:
            st.warning("No hay datos para mostrar.")
        else:
            with st.container(border=True):
                with st.spinner("Calculando ranking de empleados..."):
                    employee_overtime = calculate_employee_overtime(filtered_df, cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                    
                    st.header(f'Top {top_n_employees} Empleados con Mayor Horas Extras')
                    
                    top_costo_empleados = employee_overtime.nlargest(top_n_employees, 'Total_Costos')
                    top_cantidad_empleados = employee_overtime.nlargest(top_n_employees, 'Total_Cantidades')

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader('Top por Costo')
                        if not top_costo_empleados.empty:
                            chart_top_costo = alt.Chart(top_costo_empleados).mark_bar().encode(y=alt.Y('Apellido y nombre:N', sort='-x', title='Empleado'), x=alt.X('Total_Costos:Q', title='Total Costos ($)')).properties(title=alt.TitleParams(f'Top {top_n_employees} Empleados por Costo de HE', anchor='middle')).interactive()
                            st.altair_chart(chart_top_costo, use_container_width=True)
                    with col2:
                        st.subheader('Top por Cantidad')
                        if not top_cantidad_empleados.empty:
                            chart_top_cantidad = alt.Chart(top_cantidad_empleados).mark_bar().encode(y=alt.Y('Apellido y nombre:N', sort='-x', title='Empleado'), x=alt.X('Total_Cantidades:Q', title='Total Cantidades HE')).properties(title=alt.TitleParams(f'Top {top_n_employees} Empleados por Cantidad de HE', anchor='middle')).interactive()
                            st.altair_chart(chart_top_cantidad, use_container_width=True)
                    
                    st.subheader('Tabla de Top Empleados por Costo')
                    st.dataframe(format_st_dataframe(top_costo_empleados), use_container_width=True)
                    generate_download_buttons(top_costo_empleados, f'top_{top_n_employees}_importe_horas_extras')
                    
                    st.subheader('Tabla de Top Empleados por Cantidad')
                    st.dataframe(format_st_dataframe(top_cantidad_empleados), use_container_width=True)
                    generate_download_buttons(top_cantidad_empleados, f'top_{top_n_employees}_cantidad_horas_extras')

    with tab_valor_hora:
        if filtered_df.empty:
            st.warning("No hay datos para mostrar.")
        else:
            with st.container(border=True):
                with st.spinner("Calculando valores promedio por hora..."):
                    st.header('Valores Promedio por Hora')
                    grouping_dimension = st.selectbox('Selecciona la dimensión de desglose:', ['Gerencia', 'Legajo', 'Función', 'CECO', 'Ubicación', 'Nivel', 'Sexo'], key='valor_hora_grouping')
                    df_valor_hora = calculate_average_hourly_rate(filtered_df, grouping_dimension)
                    
                    if not df_valor_hora.empty:
                        st.dataframe(format_st_dataframe(df_valor_hora), use_container_width=True)
                        generate_download_buttons(df_valor_hora, f'valores_promedio_hora_por_{grouping_dimension}')
                    else:
                        st.warning("Columnas de valor por hora no encontradas en los datos.")

    with tab4:
        with st.container(border=True):
            st.header('Tabla de Datos Brutos Filtrados')
            st.dataframe(format_st_dataframe(filtered_df), use_container_width=True)
            generate_download_buttons(filtered_df, 'datos_brutos_filtrados')
else:
    st.info("⬆️ Esperando a que se suba un archivo Excel.")
