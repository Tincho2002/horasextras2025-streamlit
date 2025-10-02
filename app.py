import streamlit as st
import pandas as pd
import altair as alt
import io
from datetime import datetime
import numpy as np
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import re
from streamlit_image_comparison import image_comparison
from PIL import Image

# --- Configuración de la página y Estilos CSS ---
st.set_page_config(layout="wide")
st.markdown("""
<style>
/* Estilo para los botones de control (Resetear) */
div[data-testid="stSidebar"] div[data-testid="stButton"] button {
    border-radius: 0.5rem;
    font-weight: bold;
    width: 100%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Estilo general para los botones de descarga */
div.stDownloadButton button {
    background-color: #28a745;
    color: white;
    font-weight: bold;
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    border: none;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
div.stDownloadButton button:hover {
    background-color: #218838;
}

/* Ajuste general de las etiquetas para que sean más grandes */
.st-emotion-cache-ue6h4q {
    font-size: 1.1em; 
}

</style>
""", unsafe_allow_html=True)


# --- Funciones de Formato de Números ---
custom_format_locale = {
    "decimal": ",", "thousands": ".", "grouping": [3], "currency": ["", ""]
}
alt.renderers.set_embed_options(formatLocale=custom_format_locale)

def format_integer_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{int(num):,}".replace(",", ".")

def format_decimal_es(num, decimals=2):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{num:,.{decimals}f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def format_time_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    hours = int(num)
    minutes = int((num * 60) % 60)
    return f"{hours}:{minutes:02d}"

def format_percentage_es(num, decimals=1):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    return f"{num:,.{decimals}f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

# --- Título de la Aplicación ---
st.title('⏱️ Dashboard de Horas Extras 2025')
st.subheader('Análisis Interactivo del Gasto y Distribución de Horas Extras')

# --- Funciones Auxiliares ---
def generate_download_buttons(df_to_download, filename_prefix, key_suffix=""):
    st.markdown("##### Opciones de Descarga:")
    col_dl1, col_dl2 = st.columns(2)
    csv_buffer = io.StringIO()
    df_to_download.to_csv(csv_buffer, index=False)
    with col_dl1:
        st.download_button(label="⬇️ Descargar como CSV", data=csv_buffer.getvalue(), file_name=f"{filename_prefix}.csv", mime="text/csv", key=f"csv_download_{filename_prefix}{key_suffix}")
    excel_buffer = io.BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    with col_dl2:
        st.download_button(label="📊 Descargar como Excel", data=excel_buffer.getvalue(), file_name=f"{filename_prefix}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"excel_download_{filename_prefix}{key_suffix}")

def apply_all_filters(df, selections):
    _df = df.copy()
    for col, values in selections.items():
        if values:
            _df = _df[_df[col].isin(values)]
    return _df

def get_sorted_unique_options(dataframe, column_name):
    if column_name in dataframe.columns:
        unique_values = dataframe[column_name].dropna().unique().tolist()
        unique_values = [v for v in unique_values if v != 'no disponible']
        if column_name == 'Periodo':
            month_order = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}
            return sorted(unique_values, key=lambda x: month_order.get(x, 99))
        return sorted(unique_values)
    return []
    
def get_available_options(df, selections, target_column):
    _df = df.copy()
    for col, values in selections.items():
        if col != target_column and values:
            _df = _df[_df[col].isin(values)]
    return get_sorted_unique_options(_df, target_column)

@st.cache_data
def load_coords_from_url(url):
    try:
        df = pd.read_csv(url, encoding='latin-1')
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo de coordenadas desde GitHub: {e}")
        return pd.DataFrame()

@st.cache_data
def load_and_clean_data(uploaded_file):
    df_excel = pd.DataFrame()
    try:
        df_excel = pd.read_excel(uploaded_file, sheet_name='Horas_Extras', engine='openpyxl')
    except Exception as e:
        # El código busca 'Horas_Extras'
        st.error(f"ERROR CRÍTICO: No se pudo leer la hoja 'Horas_Extras' del archivo cargado. Mensaje: {e}")
        return pd.DataFrame()
    if df_excel.empty: return pd.DataFrame()

    # Mapeo y limpieza de nombres de columnas
    col_mapping = {
        'LEGAJO': 'Legajo', 'Período': 'Periodo', 'Gerencia': 'Gerencia', 'Distrito': 'Distrito',
        'Ministerio': 'Ministerio', 'Relación': 'Relación', 'Función': 'Función', 
        'HORAS HE-50': 'HE-50 (Horas)', 'HORAS HE-100': 'HE-100 (Horas)', 
        'COSTO HE-50': 'HE-50 (Costo)', 'COSTO HE-100': 'HE-100 (Costo)'
    }
    df_excel.rename(columns=col_mapping, inplace=True)

    # Conversión de Periodo
    if 'Periodo' in df_excel.columns:
        try:
            temp_periodo = pd.to_datetime(df_excel['Periodo'], errors='coerce')
            if temp_periodo.notna().any():
                spanish_months_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
                df_excel['Periodo'] = temp_periodo.dt.month.map(spanish_months_map).astype(str)
            else: df_excel['Periodo'] = df_excel['Periodo'].astype(str).str.strip().str.capitalize()
        except Exception: df_excel['Periodo'] = df_excel['Periodo'].astype(str).str.strip().str.capitalize()
    
    # Conversión de Legajo a texto limpio
    if 'Legajo' in df_excel.columns:
        df_excel['Legajo'] = pd.to_numeric(df_excel['Legajo'], errors='coerce').fillna(0).astype(int).astype(str)

    # Conversión de Horas y Costos a numérico
    numeric_cols = ['HE-50 (Horas)', 'HE-100 (Horas)', 'HE-50 (Costo)', 'HE-100 (Costo)']
    for col in numeric_cols:
        if col in df_excel.columns:
            df_excel[col] = pd.to_numeric(df_excel[col], errors='coerce').fillna(0)
    
    # Cálculo de Totales
    df_excel['Horas Totales'] = df_excel['HE-50 (Horas)'] + df_excel['HE-100 (Horas)']
    df_excel['Costo Total'] = df_excel['HE-50 (Costo)'] + df_excel['HE-100 (Costo)']
    
    # Limpieza de columnas de texto para filtros
    text_cols_for_filters_charts = ['Gerencia', 'Distrito', 'Ministerio', 'Relación', 'Función', 'Periodo']
    for col in text_cols_for_filters_charts:
        if col not in df_excel.columns: df_excel[col] = 'no disponible'
        df_excel[col] = df_excel[col].astype(str).replace(['None', 'nan', ''], 'no disponible').str.strip()
        if col == 'Periodo': df_excel[col] = df_excel[col].str.capitalize()
    
    # Filtrar registros donde las horas o costos totales son > 0
    df_excel = df_excel[df_excel['Horas Totales'] > 0]

    return df_excel

# --- Cuerpo Principal de la Aplicación ---
uploaded_file = st.file_uploader("📂 Cargue aquí su archivo Excel de Horas Extras", type=["xlsx"])
st.markdown("---")

COORDS_URL = "https://raw.githubusercontent.com/Tincho2002/dotacion_assa_2025/main/coordenadas.csv"
df_coords = load_coords_from_url(COORDS_URL)

if uploaded_file is not None:
    with st.spinner('Procesando archivo...'):
        df = load_and_clean_data(uploaded_file)
    if df.empty:
        st.error("El archivo cargado está vacío o no se pudo procesar correctamente. Asegúrese de que la hoja 'Horas_Extras' tenga datos válidos.")
        st.stop()
        
    total_registros_inicial = len(df)
    total_horas_inicial = df['Horas Totales'].sum()
    total_costo_inicial = df['Costo Total'].sum()

    st.success(f"Se ha cargado un total de **{format_integer_es(total_registros_inicial)}** registros de horas extras, sumando **{format_time_es(total_horas_inicial)}** horas y **${format_integer_es(total_costo_inicial)}** en costo.")
    st.markdown("---")

    # --- INICIO: LÓGICA DE FILTROS TIPO SLICER ---
    st.sidebar.header('Filtros del Dashboard')
    
    filter_cols_config = {
        'Periodo': 'Período', 'Gerencia': 'Gerencia', 'Relación': 'Relación', 
        'Función': 'Función', 'Distrito': 'Distrito', 'Ministerio': 'Ministerio'
    }
    filter_cols = list(filter_cols_config.keys())

    # 1. INICIALIZACIÓN DEL ESTADO: Si es la primera vez, llena todos los filtros.
    if 'selections' not in st.session_state:
        initial_selections = {col: get_sorted_unique_options(df, col) for col in filter_cols}
        st.session_state.selections = initial_selections
        st.rerun()
    
    # Clave de sesión del checkbox del mapa (para resetearlo)
    map_checkbox_key = 'show_map_comp_check_he'

    # 2. BOTÓN DE RESETEO: Restablece el estado al inicial (todo seleccionado).
    if st.sidebar.button("🔄 Resetear Filtros", use_container_width=True, key="reset_filters"):
        initial_selections = {col: get_sorted_unique_options(df, col) for col in filter_cols}
        st.session_state.selections = initial_selections
        
        # Reseteo del checkbox del mapa al resetear filtros
        if map_checkbox_key in st.session_state:
            st.session_state[map_checkbox_key] = False
            
        st.rerun()

    st.sidebar.markdown("---")

    # 3. LÓGICA DE RENDERIZADO Y ACTUALIZACIÓN (SLICER)
    old_selections = {k: list(v) for k, v in st.session_state.selections.items()}

    for col, title in filter_cols_config.items():
        available_options = get_available_options(df, st.session_state.selections, col)
        current_selection = [sel for sel in st.session_state.selections.get(col, []) if sel in available_options]
        
        selected = st.sidebar.multiselect(
            title,
            options=available_options,
            default=current_selection,
            key=f"multiselect_{col}"
        )
        
        st.session_state.selections[col] = selected

    # 4. DETECCIÓN DE CAMBIOS: Si el estado cambió, recargamos la app.
    if old_selections != st.session_state.selections:
        # Reseteo del checkbox del mapa al cambiar cualquier filtro
        if map_checkbox_key in st.session_state:
            st.session_state[map_checkbox_key] = False
            
        st.rerun()
    # --- FIN: LÓGICA DE FILTROS ---

    filtered_df = apply_all_filters(df, st.session_state.selections)
    
    st.write(f"Después de aplicar los filtros, se muestran **{format_integer_es(len(filtered_df))}** registros.")
    st.markdown("---")
    
    period_to_display = None
    all_periodos = get_sorted_unique_options(df, 'Periodo')
    selected_periodos = st.session_state.selections.get('Periodo', [])
    
    if selected_periodos:
        sorted_selected_periods = [p for p in all_periodos if p in selected_periodos]
        if sorted_selected_periods:
            period_to_display = sorted_selected_periods[-1]

    if not filtered_df.empty and period_to_display:
        df_display = filtered_df[filtered_df['Periodo'] == period_to_display].copy()
        total_registros = len(df_display)
        horas_50 = df_display['HE-50 (Horas)'].sum()
        horas_100 = df_display['HE-100 (Horas)'].sum()
        costo_total = df_display['Costo Total'].sum()
        
        total_horas_periodo = horas_50 + horas_100
        pct_h50 = (horas_50 / total_horas_periodo * 100) if total_horas_periodo > 0 else 0
        pct_h100 = (horas_100 / total_horas_periodo * 100) if total_horas_periodo > 0 else 0
        
        costo_h50 = df_display['HE-50 (Costo)'].sum()
        costo_h100 = df_display['HE-100 (Costo)'].sum()
        
        card_html = f"""
        <style>
            .summary-container-he {{ display: flex; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); align-items: center; gap: 20px; border: 1px solid #e0e0e0; }}
            .summary-main-kpi-he {{ text-align: center; border-right: 2px solid #f0f2f6; padding-right: 20px; flex-grow: 1; }}
            .summary-main-kpi-he .title {{ font-size: 1.1rem; font-weight: bold; color: #2C3E50; margin-bottom: 5px; }}
            .summary-main-kpi-he .value {{ font-size: 2.5rem; font-weight: bold; color: #2C3E50; }}
            .summary-breakdown-he {{ display: flex; flex-direction: column; gap: 15px; flex-grow: 2; }}
            .summary-row-he {{ display: flex; justify-content: space-around; align-items: center; }}
            .summary-sub-kpi-he {{ text-align: left; display: flex; align-items: center; gap: 10px; width: 200px; }}
            .summary-sub-kpi-he .icon {{ font-size: 2rem; }}
            .summary-sub-kpi-he .details {{ display: flex; flex-direction: column; }}
            .summary-sub-kpi-he .value {{ font-size: 1.5rem; font-weight: bold; color: #34495E; }}
            .summary-sub-kpi-he .label {{ font-size: 0.9rem; color: #7F8C8D; }}
        </style>
        <div class="summary-container-he">
            <div class="summary-main-kpi-he">
                <div class="title">COSTO TOTAL ({period_to_display.upper()})</div>
                <div class="value" data-target="{costo_total}">💵 $0</div>
            </div>
            <div class="summary-breakdown-he">
                <div class="summary-row-he">
                    <div class="summary-sub-kpi-he"><div class="icon">🕒</div><div class="details"><div class="value" data-target="{total_horas_periodo}">0</div><div class="label">Horas Totales ({format_time_es(total_horas_periodo)})</div></div></div>
                    <div class="summary-sub-kpi-he"><div class="icon">📊</div><div class="details"><div class="value" data-target="{total_registros}">0</div><div class="label">Registros Afectados</div></div></div>
                </div>
                <div class="summary-row-he">
                    <div class="summary-sub-kpi-he"><div class="icon">50%</div><div class="details"><div class="value" data-target="{horas_50}">0</div><div class="label">HE 50% ({format_percentage_es(pct_h50)})</div></div></div>
                    <div class="summary-sub-kpi-he"><div class="icon">100%</div><div class="details"><div class="value" data-target="{horas_100}">0</div><div class="label">HE 100% ({format_percentage_es(pct_h100)})</div></div></div>
                </div>
            </div>
        </div>
        <script>
            function animateValue(obj, start, end, duration) {{
                let startTimestamp = null;
                const step = (timestamp) => {{
                    if (!startTimestamp) startTimestamp = timestamp;
                    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                    const currentVal = Math.floor(progress * (end - start) + start);
                    let formattedVal = currentVal.toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ".");
                    
                    if (obj.innerHTML.includes("💵")) {{ 
                        // Formato de costo para el KPI principal
                        obj.innerHTML = `💵 $${formattedVal}`; 
                    }} else if (obj.innerHTML.includes("🕒")) {{
                        // Formato de tiempo para las Horas Totales
                        let hours = Math.floor(currentVal);
                        let minutes = Math.floor((currentVal % 1) * 60);
                        obj.innerHTML = `🕒 ${hours}:${minutes.toString().padStart(2, '0')}`;
                    }} else {{ 
                        // Formato de número simple para el resto
                        obj.innerHTML = formattedVal; 
                    }}
                    
                    if (progress < 1) {{ window.requestAnimationFrame(step); }}
                }};
                window.requestAnimationFrame(step);
            }}
            const counters = document.querySelectorAll('.value[data-target]');
            counters.forEach(counter => {{ 
                const target = +counter.getAttribute('data-target'); 
                // Usamos un valor de inicio diferente para horas totales para la animación
                const start_value = counter.innerHTML.includes("🕒") ? 0 : 0;
                setTimeout(() => animateValue(counter, start_value, target, 1500), 100); 
            }});
        </script>
        """
        components.html(card_html, height=220)
        st.markdown("<br>", unsafe_allow_html=True)

    tab_names = ["📊 Resumen General", "💰 Costo", "🕒 Horas", "📈 Desglose por Categoría", "📋 Datos Brutos"]
    if not df_coords.empty:
        tab_names.insert(1, "🗺️ Mapa Geográfico")
        tab_names.insert(1, "🗺️ Comparador de Mapas")
    
    tabs = st.tabs(tab_names)
    tab_map_comparador, tab_map_individual = (None, None)
    
    tab_resumen = tabs[0]
    tab_index = 1
    if not df_coords.empty:
        tab_map_comparador = tabs[tab_index]
        tab_index += 1
        tab_map_individual = tabs[tab_index]
        tab_index += 1
    tab_costo = tabs[tab_index]
    tab_horas = tabs[tab_index + 1]
    tab_desglose = tabs[tab_index + 2]
    tab_brutos = tabs[tab_index + 3]

    with tab_resumen:
        st.header('Resumen General de Horas Extras')
        if filtered_df.empty:
            st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            st.subheader('Horas y Costo Total por Período')
            col_table_periodo, col_chart_periodo = st.columns([1, 2])
            periodo_agg = filtered_df.groupby('Periodo').agg(
                {'Horas Totales': 'sum', 'Costo Total': 'sum'}
            ).reset_index()
            periodo_agg['Periodo'] = pd.Categorical(periodo_agg['Periodo'], categories=all_periodos, ordered=True)
            periodo_agg = periodo_agg.sort_values('Periodo').reset_index(drop=True)
            
            with col_chart_periodo:
                # Gráfico de Horas Totales por Periodo
                line_horas = alt.Chart(periodo_agg).mark_line(point=True, color='#4472c4').encode(
                    x=alt.X('Periodo', sort=all_periodos, title='Período'), 
                    y=alt.Y('Horas Totales', title='Horas Totales (H:MM)', axis=alt.Axis(format='d')), 
                    tooltip=['Periodo', alt.Tooltip('Horas Totales', format=',.2f', title='Horas')]
                )
                text_horas = line_horas.mark_text(align='center', baseline='bottom', dy=-10, color='#4472c4').encode(
                    text=alt.Text('Horas Totales', format=',.2f')
                )
                st.altair_chart((line_horas + text_horas).properties(title='Horas Totales por Período'), use_container_width=True)
                
                # Gráfico de Costo Total por Periodo
                bar_costo = alt.Chart(periodo_agg).mark_bar(color='#ed7d31').encode(
                    x=alt.X('Periodo', sort=all_periodos, title='Período'), 
                    y=alt.Y('Costo Total:Q', title='Costo Total ($)', axis=alt.Axis(format='$,d')), 
                    tooltip=['Periodo', alt.Tooltip('Costo Total', format='$,.0f')]
                )
                text_costo = bar_costo.mark_text(align='center', baseline='bottom', dy=-10).encode(
                    text=alt.Text('Costo Total', format='$,.0f')
                )
                st.altair_chart((bar_costo + text_costo).properties(title='Costo Total por Período'), use_container_width=True)
                
            with col_table_periodo:
                st.dataframe(periodo_agg.style.format({
                    "Horas Totales": format_decimal_es, 
                    "Costo Total": lambda x: f"${format_integer_es(x)}"
                }))
                generate_download_buttons(periodo_agg, 'resumen_periodo_he', key_suffix="_resumen1")
            st.markdown('---')
            
            st.subheader('Distribución por Tipo de Hora Extra')
            col_table_tipo, col_chart_tipo = st.columns([1, 2])
            tipo_agg = filtered_df.groupby('Periodo').agg(
                {'HE-50 (Horas)': 'sum', 'HE-100 (Horas)': 'sum'}
            ).reset_index()
            tipo_agg['Periodo'] = pd.Categorical(tipo_agg['Periodo'], categories=all_periodos, ordered=True)
            tipo_agg = tipo_agg.sort_values('Periodo').reset_index(drop=True)
            tipo_agg_melted = tipo_agg.melt(id_vars='Periodo', var_name='Tipo HE', value_name='Horas')
            
            with col_chart_tipo:
                bars_tipo = alt.Chart(tipo_agg_melted).mark_bar().encode(
                    x=alt.X('Horas:Q', stack="normalize", title='Proporción de Horas'),
                    y=alt.Y('Periodo:N', sort=all_periodos),
                    color=alt.Color('Tipo HE:N'),
                    tooltip=['Periodo', 'Tipo HE', alt.Tooltip('Horas:Q', format=',.2f')]
                ).properties(title='Proporción de Horas HE-50 vs HE-100')
                st.altair_chart(bars_tipo, use_container_width=True)
                
            with col_table_tipo:
                tipo_agg['Horas Totales'] = tipo_agg['HE-50 (Horas)'] + tipo_agg['HE-100 (Horas)']
                st.dataframe(tipo_agg.style.format({
                    "HE-50 (Horas)": format_decimal_es, 
                    "HE-100 (Horas)": format_decimal_es, 
                    "Horas Totales": format_decimal_es
                }))
                generate_download_buttons(tipo_agg, 'distribucion_tipo_he', key_suffix="_resumen2")

    if tab_map_comparador and period_to_display:
        with tab_map_comparador:
            st.header(f"Comparador de Mapas por Horas Extras para el Período: {period_to_display}")
            map_style_options = {
                "Satélite con Calles": "satellite-streets",
                "Mapa de Calles": "open-street-map",
                "Estilo Claro": "carto-positron",
            }
            c1, c2 = st.columns(2)
            with c1:
                style1_name = st.selectbox("Selecciona el estilo del mapa izquierdo:", options=list(map_style_options.keys()), index=0, key="map_style1_he")
            with c2:
                style2_name = st.selectbox("Selecciona el estilo del mapa derecho:", options=list(map_style_options.keys()), index=1, key="map_style2_he")

            st.markdown("---")
            
            # Checkbox de activación con la clave de sesión única
            show_map_comparison = st.checkbox("✅ Mostrar Comparación de Mapas", value=st.session_state.get(map_checkbox_key, False), key=map_checkbox_key)
            
            def generate_map_figure_he(df, mapbox_style):
                # Agregación por Distrito para Horas Totales
                df_mapa_data = pd.merge(df, df_coords, on="Distrito", how="left")
                df_mapa_agg = df_mapa_data.groupby(['Distrito', 'Latitud', 'Longitud']).agg(
                    {'Horas Totales': 'sum'}
                ).reset_index()
                df_mapa_agg.dropna(subset=['Latitud', 'Longitud'], inplace=True)
                if df_mapa_agg.empty or df_mapa_agg['Horas Totales'].sum() == 0:
                    return None
                
                df_mapa_agg = df_mapa_agg[df_mapa_agg['Horas Totales'] > 0]
                
                mapbox_access_token = "pk.eyJ1Ijoic2FuZHJhcXVldmVkbyIsImEiOiJjbWYzOGNkZ2QwYWg0MnFvbDJucWc5d3VwIn0.bz6E-qxAwk6ZFPYohBsdMw"
                px.set_mapbox_access_token(mapbox_access_token)
                fig = px.scatter_mapbox(
                    df_mapa_agg,
                    lat="Latitud", lon="Longitud",
                    size="Horas Totales", color="Horas Totales",
                    hover_name="Distrito",
                    hover_data={"Latitud": False, "Longitud": False, "Horas Totales": True},
                    color_continuous_scale=px.colors.sequential.Inferno, 
                    size_max=50,
                    mapbox_style=mapbox_style, 
                    zoom=6, center={"lat": -32.5, "lon": -61.5}
                )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                return fig

            # 3. LÓGICA CONDICIONAL: Solo si el usuario quiere ver el mapa.
            if show_map_comparison:
                df_mapa_display = filtered_df[filtered_df['Periodo'] == period_to_display]
                
                if 'Distrito' not in df_mapa_display.columns or 'Distrito' not in df_coords.columns:
                    st.warning("La columna 'Distrito' no se encuentra en los datos o en el archivo de coordenadas.")
                else:
                    # Columnas para Mapa y Tabla (3:2)
                    comp_col1, comp_col2 = st.columns([3, 2]) 
                    with comp_col1:
                        with st.spinner(f"Generando mapas ({style1_name} vs {style2_name})..."):
                            try:
                                fig1 = generate_map_figure_he(df_mapa_display, map_style_options[style1_name])
                                fig2 = generate_map_figure_he(df_mapa_display, map_style_options[style2_name])
                                if fig1 and fig2:
                                    img1_bytes = fig1.to_image(format="png", scale=2, engine="kaleido")
                                    img2_bytes = fig2.to_image(format="png", scale=2, engine="kaleido")
                                    img1_pil = Image.open(io.BytesIO(img1_bytes))
                                    img2_pil = Image.open(io.BytesIO(img2_bytes))
                                    
                                    image_comparison(
                                        img1=img1_pil,
                                        img2=img2_pil,
                                        label1=style1_name,
                                        label2=style2_name,
                                        width=850, # Ancho ajustado para la columna 3/5
                                    )
                                else:
                                    st.warning("No hay horas extras con ubicación válida para mostrar en el mapa para el período seleccionado.")
                            except Exception as e:
                                st.error(f"Ocurrió un error al generar las imágenes del mapa: {e}")
                                st.info("Intente recargar la página o seleccionar un período con menos datos.")
                    
                    with comp_col2:
                            # Código de la tabla de pivot: Horas por Distrito y Relación
                            pivot_table = pd.pivot_table(
                                data=df_mapa_display, 
                                index='Distrito', 
                                columns='Relación', 
                                values='Horas Totales', 
                                aggfunc='sum', 
                                fill_value=0
                            )
                            if 'Convenio' not in pivot_table.columns: pivot_table['Convenio'] = 0
                            if 'FC' not in pivot_table.columns: pivot_table['FC'] = 0
                            pivot_table['Horas Totales'] = pivot_table['Convenio'] + pivot_table['FC']
                            pivot_table.sort_values(by='Horas Totales', ascending=False, inplace=True)
                            
                            # Fila Total
                            total_row = pd.DataFrame({
                                'Distrito': ['**TOTAL GENERAL**'], 
                                'Convenio': [pivot_table['Convenio'].sum()], 
                                'FC': [pivot_table['FC'].sum()], 
                                'Horas Totales': [pivot_table['Horas Totales'].sum()]
                            })
                            df_final_table = pd.concat([pivot_table.reset_index(), total_row], ignore_index=True)
                            
                            st.dataframe(df_final_table.style.format({
                                'Convenio': format_decimal_es, 
                                'FC': format_decimal_es, 
                                'Horas Totales': format_decimal_es
                            }).set_properties(**{'text-align': 'right'}), use_container_width=True, height=500, hide_index=True)

            else:
                # 4. Mensaje que se muestra si el checkbox NO está marcado.
                st.info("Seleccione los estilos de mapa deseados y marque la casilla 'Mostrar Comparación de Mapas' para visualizar y generar la comparación.")
    # --- FIN CORRECCIÓN DEL BLOQUE tab_map_comparador ---

    if tab_map_individual and period_to_display:
        with tab_map_individual:
            st.header(f"Distribución Geográfica de Horas Extras para el Período: {period_to_display}")
            map_style_options = {"Satélite con Calles": "satellite-streets", "Mapa de Calles": "open-street-map", "Estilo Claro": "carto-positron"}
            selected_style_name = st.selectbox("Selecciona el estilo del mapa:", list(map_style_options.keys()), key="map_style_individual_he")
            selected_mapbox_style = map_style_options[selected_style_name]
            df_mapa_display = filtered_df[filtered_df['Periodo'] == period_to_display]
            col_map, col_table = st.columns([3, 2])
            with col_map:
                if 'Distrito' not in df_mapa_display.columns or 'Distrito' not in df_coords.columns:
                    st.warning("La columna 'Distrito' es necesaria para la visualización del mapa.")
                else:
                    df_mapa_data = pd.merge(df_mapa_display, df_coords, on="Distrito", how="left").dropna(subset=['Latitud', 'Longitud'])
                    df_mapa_agg = df_mapa_data.groupby(['Distrito', 'Latitud', 'Longitud']).agg(
                        {'Horas Totales': 'sum'}
                    ).reset_index()
                    df_mapa_agg.dropna(subset=['Latitud', 'Longitud'], inplace=True)

                    if df_mapa_agg.empty or df_mapa_agg['Horas Totales'].sum() == 0: 
                        st.warning("No hay horas extras con ubicación válida para mostrar en el mapa para la selección actual.")
                    else:
                        df_mapa_agg = df_mapa_agg[df_mapa_agg['Horas Totales'] > 0]
                        mapbox_access_token = "pk.eyJ1Ijoic2FuZHJhcXVldmVkbyIsImEiOiJjbWYzOGNkZ2QwYWg0MnFvbDJucWc5d3VwIn0.bz6E-qxAwk6ZFPYohBsdMw"
                        px.set_mapbox_access_token(mapbox_access_token)
                        fig = px.scatter_mapbox(df_mapa_agg, lat="Latitud", lon="Longitud", size="Horas Totales", color="Horas Totales", hover_name="Distrito", color_continuous_scale=px.colors.sequential.Inferno, size_max=50, mapbox_style=selected_mapbox_style, zoom=6, center={"lat": -32.5, "lon": -61.5})
                        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                        st.plotly_chart(fig, use_container_width=True, key="map_individual_chart_he")
            
            with col_table:
                # Tabla de Horas Totales por Distrito y Relación (igual que en el comparador, pero en otra pestaña)
                pivot_table = pd.pivot_table(
                    data=df_mapa_display, 
                    index='Distrito', 
                    columns='Relación', 
                    values='Horas Totales', 
                    aggfunc='sum', 
                    fill_value=0
                )
                if 'Convenio' not in pivot_table.columns: pivot_table['Convenio'] = 0
                if 'FC' not in pivot_table.columns: pivot_table['FC'] = 0
                pivot_table['Horas Totales'] = pivot_table['Convenio'] + pivot_table['FC']
                pivot_table.sort_values(by='Horas Totales', ascending=False, inplace=True)
                total_row = pd.DataFrame({
                    'Distrito': ['**TOTAL GENERAL**'], 
                    'Convenio': [pivot_table['Convenio'].sum()], 
                    'FC': [pivot_table['FC'].sum()], 
                    'Horas Totales': [pivot_table['Horas Totales'].sum()]
                })
                df_final_table = pd.concat([pivot_table.reset_index(), total_row], ignore_index=True)
                st.dataframe(df_final_table.style.format({
                    'Convenio': format_decimal_es, 
                    'FC': format_decimal_es, 
                    'Horas Totales': format_decimal_es
                }).set_properties(**{'text-align': 'right'}), use_container_width=True, height=460, hide_index=True)


    with tab_costo:
        st.header('Análisis de Costo Total de Horas Extras')
        if filtered_df.empty or not selected_periodos: st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            periodo_a_mostrar_costo = st.selectbox('Selecciona un Período:', selected_periodos, index=len(selected_periodos) - 1 if selected_periodos else 0, key='periodo_selector_costo')
            df_periodo_costo = filtered_df[filtered_df['Periodo'] == periodo_a_mostrar_costo]
            
            st.subheader(f'Costo Total por Gerencia para {periodo_a_mostrar_costo}'); col_table_gerencia, col_chart_gerencia = st.columns([1, 2])
            with col_chart_gerencia:
                gerencia_agg = df_periodo_costo.groupby('Gerencia')['Costo Total'].sum().reset_index()
                gerencia_agg = gerencia_agg.sort_values('Costo Total', ascending=False).head(10) # Top 10
                
                chart_costo_gerencia = alt.Chart(gerencia_agg).mark_bar().encode(
                    x=alt.X('Gerencia:N', sort='-y'), 
                    y=alt.Y('Costo Total:Q', title='Costo Total ($)', axis=alt.Axis(format='$,d')), 
                    color=alt.Color('Gerencia:N', legend=None),
                    tooltip=['Gerencia', alt.Tooltip('Costo Total', format='$,.0f')]
                )
                text_costo_gerencia = chart_costo_gerencia.mark_text(align='center', baseline='middle', dy=-10).encode(
                    text=alt.Text('Costo Total', format='$,.0f')
                )
                st.altair_chart(chart_costo_gerencia + text_costo_gerencia, use_container_width=True)
                
            with col_table_gerencia:
                st.dataframe(gerencia_agg.style.format({"Costo Total": lambda x: f"${format_integer_es(x)}"}))
                generate_download_buttons(gerencia_agg, f'costo_gerencia_{periodo_a_mostrar_costo}', key_suffix="_costo1")
                
            st.markdown('---')
            
            st.subheader(f'Costo por Tipo de Hora Extra para {periodo_a_mostrar_costo}')
            costo_tipo = pd.DataFrame({
                'Tipo HE': ['HE-50 (Costo)', 'HE-100 (Costo)'],
                'Costo': [df_periodo_costo['HE-50 (Costo)'].sum(), df_periodo_costo['HE-100 (Costo)'].sum()]
            })
            costo_tipo['Costo %'] = costo_tipo['Costo'] / costo_tipo['Costo'].sum() * 100
            
            col_table_tipo_costo, col_chart_tipo_costo = st.columns([1, 2])
            with col_chart_tipo_costo:
                pie_costo = alt.Chart(costo_tipo).mark_arc(outerRadius=120).encode(
                    theta=alt.Theta("Costo:Q", stack=True),
                    color=alt.Color("Tipo HE:N"),
                    order=alt.Order("Costo:Q", sort="descending"),
                    tooltip=['Tipo HE', alt.Tooltip('Costo', format='$,.0f'), alt.Tooltip('Costo %', format='.1f')]
                ).properties(title='Distribución de Costo por Tipo de HE')
                text_pie_costo = pie_costo.mark_text(radius=140).encode(
                    text=alt.Text('Costo %', format='.1f'),
                    order=alt.Order("Costo:Q", sort="descending"),
                    color=alt.value("black")
                )
                st.altair_chart(pie_costo + text_pie_costo, use_container_width=True)

            with col_table_tipo_costo:
                st.dataframe(costo_tipo.style.format({
                    "Costo": lambda x: f"${format_integer_es(x)}",
                    "Costo %": lambda x: f"{format_decimal_es(x)}%"
                }))
                generate_download_buttons(costo_tipo, f'costo_tipo_he_{periodo_a_mostrar_costo}', key_suffix="_costo2")
                

    with tab_horas:
        st.header('Análisis de Horas Totales de Horas Extras')
        if filtered_df.empty or not selected_periodos: st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            periodo_a_mostrar_horas = st.selectbox('Selecciona un Período:', selected_periodos, index=len(selected_periodos) - 1 if selected_periodos else 0, key='periodo_selector_horas')
            df_periodo_horas = filtered_df[filtered_df['Periodo'] == periodo_a_mostrar_horas]
            
            st.subheader(f'Horas Totales por Funció para {periodo_a_mostrar_horas}'); col_table_funcion, col_chart_funcion = st.columns([1, 2])
            with col_chart_funcion:
                funcion_agg = df_periodo_horas.groupby('Función')['Horas Totales'].sum().reset_index()
                funcion_agg = funcion_agg.sort_values('Horas Totales', ascending=False).head(10) # Top 10
                
                chart_horas_funcion = alt.Chart(funcion_agg).mark_bar().encode(
                    x=alt.X('Función:N', sort='-y'), 
                    y=alt.Y('Horas Totales:Q', title='Horas Totales (H:MM)', axis=alt.Axis(format='d')), 
                    color=alt.Color('Función:N', legend=None),
                    tooltip=['Función', alt.Tooltip('Horas Totales', format=',.2f')]
                )
                text_horas_funcion = chart_horas_funcion.mark_text(align='center', baseline='middle', dy=-10).encode(
                    text=alt.Text('Horas Totales', format=',.2f')
                )
                st.altair_chart(chart_horas_funcion + text_horas_funcion, use_container_width=True)
                
            with col_table_funcion:
                st.dataframe(funcion_agg.style.format({"Horas Totales": format_decimal_es}))
                generate_download_buttons(funcion_agg, f'horas_funcion_{periodo_a_mostrar_horas}', key_suffix="_horas1")
                
            st.markdown('---')
            
            st.subheader(f'Distribución de Horas por Relación para {periodo_a_mostrar_horas}')
            relacion_agg = df_periodo_horas.groupby('Relación')['Horas Totales'].sum().reset_index()
            relacion_agg['Horas %'] = relacion_agg['Horas Totales'] / relacion_agg['Horas Totales'].sum() * 100
            
            col_table_relacion_horas, col_chart_relacion_horas = st.columns([1, 2])
            with col_chart_relacion_horas:
                pie_relacion = alt.Chart(relacion_agg).mark_arc(outerRadius=120).encode(
                    theta=alt.Theta("Horas Totales:Q", stack=True),
                    color=alt.Color("Relación:N"),
                    order=alt.Order("Horas Totales:Q", sort="descending"),
                    tooltip=['Relación', alt.Tooltip('Horas Totales', format=',.2f'), alt.Tooltip('Horas %', format='.1f')]
                ).properties(title='Distribución de Horas por Relación')
                text_pie_relacion = pie_relacion.mark_text(radius=140).encode(
                    text=alt.Text('Horas %', format='.1f'),
                    order=alt.Order("Horas Totales:Q", sort="descending"),
                    color=alt.value("black")
                )
                st.altair_chart(pie_relacion + text_pie_relacion, use_container_width=True)

            with col_table_relacion_horas:
                st.dataframe(relacion_agg.style.format({
                    "Horas Totales": format_decimal_es,
                    "Horas %": lambda x: f"{format_decimal_es(x)}%"
                }))
                generate_download_buttons(relacion_agg, f'horas_relacion_{periodo_a_mostrar_horas}', key_suffix="_horas2")

    with tab_desglose:
        st.header('Desglose Detallado de Horas y Costo por Categoría')
        if filtered_df.empty or not selected_periodos: st.warning("No hay datos para mostrar.")
        else:
            periodo_a_mostrar_desglose = st.selectbox('Seleccionar Período:', selected_periodos, index=len(selected_periodos) - 1 if selected_periodos else 0, key='periodo_selector_desglose_he')
            cat_seleccionada = st.selectbox('Seleccionar Categoría:', ['Gerencia', 'Distrito', 'Ministerio', 'Función', 'Relación'], key='cat_selector_desglose_he')
            df_periodo_desglose = filtered_df[filtered_df['Periodo'] == periodo_a_mostrar_desglose]
            
            st.subheader(f'Horas y Costo por {cat_seleccionada} para {periodo_a_mostrar_desglose}')
            
            table_data = df_periodo_desglose.groupby(cat_seleccionada).agg({
                'Horas Totales': 'sum',
                'Costo Total': 'sum'
            }).reset_index().sort_values('Costo Total', ascending=False)
            
            table_data['Horas %'] = table_data['Horas Totales'] / table_data['Horas Totales'].sum() * 100
            table_data['Costo %'] = table_data['Costo Total'] / table_data['Costo Total'].sum() * 100
            
            st.dataframe(table_data.style.format({
                "Horas Totales": format_decimal_es,
                "Costo Total": lambda x: f"${format_integer_es(x)}",
                "Horas %": lambda x: f"{format_decimal_es(x)}%",
                "Costo %": lambda x: f"{format_decimal_es(x)}%"
            }))
            
            generate_download_buttons(table_data, f'desglose_{cat_seleccionada.lower()}_{periodo_a_mostrar_desglose}', key_suffix="_desglose_he")

    with tab_brutos:
        st.header('Tabla de Datos Filtrados (Horas Extras)')
        display_df = filtered_df.copy()
        
        display_df = display_df.drop(columns=['Legajo']) # Ocultar Legajo por privacidad, si es sensible
        
        st.dataframe(display_df.style.format({
            'HE-50 (Horas)': format_decimal_es, 
            'HE-100 (Horas)': format_decimal_es, 
            'Horas Totales': format_decimal_es,
            'HE-50 (Costo)': lambda x: f"${format_integer_es(x)}",
            'HE-100 (Costo)': lambda x: f"${format_integer_es(x)}",
            'Costo Total': lambda x: f"${format_integer_es(x)}"
        }))
        generate_download_buttons(filtered_df, 'datos_filtrados_horas_extras', key_suffix="_brutos_he")

else:
    st.info("Por favor, cargue un archivo Excel para comenzar el análisis.")