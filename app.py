
import streamlit as st
import pandas as pd
import altair as alt
import os
import io

# Nombre del archivo Excel subido, será inyectado por el script de Colab
EXCEL_FILE_NAME = "HE_2025 (2).xlsx" # Marcador de posición que será reemplazado

# --- Custom CSS para estilo e íconos ---
st.markdown("""
<style>
/* Estilo general para los botones de descarga */
div.stDownloadButton button {
    background-color: #6C5CE7; /* Un morado elegante */
    color: white;
    font-weight: bold;
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    border: none;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px; /* Espacio entre el ícono y el texto */
}

div.stDownloadButton button:hover {
    background-color: #5A4ADF; /* Morado ligeramente más oscuro al pasar el ratón */
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
}

/* Estilo para los selectores múltiples (filtros) */
.stMultiSelect div[data-baseweb="select"] {
    border: 1px solid #adb5bd; /* Borde gris claro */
    border-radius: 0.5rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    background-color: #f8f9fa; /* Fondo más claro */
    transition: all 0.2s ease-in-out;
}
.stMultiSelect div[data-baseweb="select"]:hover {
    border-color: #6c757d; /* Gris más oscuro al pasar el ratón */
}
.stMultiSelect label {
    font-weight: bold;
    color: #343a40; /* Texto más oscuro para las etiquetas */
    margin-bottom: 0.5rem;
}
.stMultiSelect div[role="listbox"] { /* Para el menú desplegable */
    background-color: #ffffff;
    border: 1px solid #e9ecef;
    border-radius: 0.5rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
/* Estilo para los elementos seleccionados dentro del multiselect */
.stMultiSelect .st-cm { /* Clase común para los tokens/elementos seleccionados */
    background-color: #e0eaff; /* Azul claro de selección */
    border-radius: 0.25rem;
    padding: 0.2rem 0.5rem;
    margin: 0.1rem;
    color: #495057;
}

</style>
""", unsafe_allow_html=True)

# --- Configuración global de Pandas (para la visualización de DataFrames) ---
pd.options.display.float_format = '{{:,.2f}}'.format

# --- Función auxiliar para formatear DataFrames para visualización ---
def format_st_dataframe(df_to_style):
    # Selecciona solo las columnas numéricas para aplicar el formato
    numeric_cols = df_to_style.select_dtypes(include='number').columns
    # Crea un diccionario de formato para estas columnas
    format_dict = {col: '{:,.2f}' for col in numeric_cols}
    # Aplica el estilo y lo devuelve para ser usado en st.dataframe
    return df_to_style.style.format(format_dict)

# --- Función auxiliar para generar botones de descarga ---
def generate_download_buttons(df_to_download, filename_prefix):
    st.markdown("##### Opciones de Descarga:")
    col_dl1, col_dl2 = st.columns(2)

    # Descarga CSV con ícono
    csv_buffer = io.StringIO()
    df_to_download.to_csv(csv_buffer, index=False)
    with col_dl1:
        st.download_button(
            label="⬇️ Descargar como CSV", # Ícono añadido
            data=csv_buffer.getvalue(),
            file_name=f"{filename_prefix}.csv",
            mime="text/csv",
            key=f"csv_download_{filename_prefix}" # Clave única
        )

    # Descarga Excel con ícono
    excel_buffer = io.BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0) # Rebobinar el buffer a la posición inicial
    with col_dl2:
        st.download_button(
            label="📊 Descargar como Excel", # Ícono añadido
            data=excel_buffer.getvalue(),
            file_name=f"{filename_prefix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"excel_download_{filename_prefix}" # Clave única
        )
    st.info("La descarga en PDF para tablas directamente desde Streamlit es compleja y generalmente requiere configuraciones de servidor adicionales. Se recomienda usar las opciones CSV o Excel.")

# --- Función auxiliar para añadir fila de total ---
def add_total_row(df, group_cols, value_cols, total_label='Total'):
    # Asegúrate de que las columnas de grupo existen y son una lista
    if not isinstance(group_cols, list):
        group_cols = [group_cols]

    total_row_dict = dict()
    for col in group_cols:
        total_row_dict[col] = total_label
    for col in value_cols:
        if col in df.columns:
            # Para promedios, el "total" no es la suma, sino el promedio general si es relevante.
            # Aquí, para mantener consistencia con la función original, sumamos.
            # Si se desea el promedio del promedio, se necesitaría una lógica más compleja
            # o una función `add_average_row`. Para 'Valor Hora', la suma de promedios no tiene sentido.
            # Por ahora, para esta función genérica, sumaremos.
            # Para 'Valor Hora', la "fila total" podría mostrar NaN o ser omitida,
            # o un promedio de los promedios, lo cual es matemáticamente dudoso.
            # La mejor opción para "Valor Hora" es mostrar el promedio general del dataframe filtrado.
            total_row_dict[col] = df[col].sum()

    for col in group_cols:
        if col not in total_row_dict:
            total_row_dict[col] = total_label if col == 'Mes' else 'Total'

    total_df = pd.DataFrame([total_row_dict])
    return pd.concat([df, total_df], ignore_index=True)


# --- Título de la Aplicación ---
st.set_page_config(layout="wide")
st.title('📊 Dashboard de Horas Extras HE_2025')
st.subheader('Análisis Interactivo de Costos y Cantidades de Horas Extras')

# --- Función para cargar y limpiar datos (para reutilizar y cachear) ---
@st.cache_data
def load_and_clean_data(file_path_param):
    df_excel = pd.DataFrame()
    try:
        # Cargar 'Legajo' directamente como string para evitar problemas de formato numérico
        # Se asume que la hoja de datos se llama 'Datos'
        # Añadimos CECO y Nivel al dtype para cargarlos como string inicialmente si es necesario,
        # para luego limpiarlos y convertirlos a Int64
        df_excel = pd.read_excel(file_path_param, sheet_name='Datos', dtype={'Legajo': str, 'CECO': str, 'Nivel': str})
    except Exception as e:
        st.error(f"Error al leer la hoja 'Datos', intentando la primera hoja por defecto: {e}")
        try:
            # Si no encuentra 'Datos', intenta leer la primera hoja
            df_excel = pd.read_excel(file_path_param, dtype={'Legajo': str, 'CECO': str, 'Nivel': str})
            st.warning("Se cargó la primera hoja del Excel ya que 'Datos' no fue encontrada.")
        except Exception as e_no_sheet:
            st.error(f"ERROR CRÍTICO: No se pudo leer el archivo Excel '{file_path_param}'. Mensaje: {e_no_sheet}")
            st.warning("Asegúrate de que el archivo esté subido en Colab y que la hoja 'Datos' (o la primera hoja) contenga la información.")
            return pd.DataFrame()

    if df_excel.empty:
        return pd.DataFrame()

    # st.write(f"Columnas encontradas en el archivo: {df_excel.columns.tolist()}")

    # --- Manejo de la columna 'Legajo' ---
    # Limpieza robusta del Legajo para asegurar formato string sin decimales ni espacios extra
    if 'Legajo' in df_excel.columns:
        df_excel['Legajo'] = df_excel['Legajo'].astype(str).str.strip() # Asegurarse de que sea string y sin espacios

        def clean_legajo_value(val):
            if pd.isna(val) or val in ['', 'None', 'nan', 'nan.0']: # Añadir 'nan.0' a los que se reemplazan
                return 'no disponible'
            s_val = str(val).strip()
            # Si termina en '.0' y el resto es un dígito, convertir a entero (string)
            if s_val.endswith('.0') and s_val[:-2].isdigit():
                return s_val[:-2] # Elimina el ".0"
            return s_val

        df_excel['Legajo'] = df_excel['Legajo'].apply(clean_legajo_value)
        st.info("Columna 'Legajo' procesada.")
    else:
        st.warning("Columna 'Legajo' no encontrada. Algunas funcionalidades (como el filtro por Legajo y el Top 10 por Legajo) podrían estar limitadas.")
        df_excel['Legajo'] = 'no disponible' # Asegurar que la columna existe para evitar KeyErrors

    # --- Procesamiento de la columna 'Período' y creación de 'Mes' ---
    if 'Período' in df_excel.columns:
        df_excel['Período'] = pd.to_datetime(df_excel['Período'], errors='coerce')
        df_excel['Mes'] = df_excel['Período'].dt.strftime('%Y-%m') # Formato YYYY-MM para orden y visualización
        df_excel.dropna(subset=['Período'], inplace=True) # Eliminar filas con 'Período' inválido
        st.info("Columna 'Período' procesada y 'Mes' creada.")
    else:
        st.warning("Columna 'Período' no encontrada. Las funcionalidades de tendencia mensual no estarán disponibles.")
        df_excel['Mes'] = 'no disponible' # Para evitar errores en agrupaciones por 'Mes'

    # --- Conversión a numérico de las columnas de horas y costos (sin cambios aquí) ---
    # Es CRÍTICO que estos nombres de columna coincidan EXACTAMENTE con los de tu Excel
    columns_to_convert_to_numeric = [
        'Horas extras al 50 %', 'Horas extras al 50 % Sabados', 'Horas extras al 100%',
        'Cantidad HE 50', 'Cant HE al 50 Sabados', 'Cantidad HE 100',
        'Cantidad HE FC', 'Importe HE Fc', 'Total (Q)', # Asumido que estas son las columnas totales si existen
        'Hora Normal', 'Hora Extra al 50%', 'Hora Extra al 50% Sabados',
        'Hora Extra al 100%', 'HE FC', 'Total ($)' # Asumido que estas son las columnas totales si existen
    ]
    for col in columns_to_convert_to_numeric:
        if col in df_excel.columns:
            df_excel[col] = pd.to_numeric(df_excel[col], errors='coerce').fillna(0)
        else:
            # st.warning(f"Columna '{col}' no encontrada en el Excel. Se usará 0 si es necesario. ¡Verifica el nombre de la columna en tu archivo!")
            df_excel[col] = 0 # Asegurarse de que la columna existe como 0

    # --- Asegurar que otras columnas para filtros existan y sean strings ---
    # Estos nombres de columna también deben coincidir con tu Excel
    columns_for_filters_str = ['Gerencia', 'Ministerio', 'CECO', 'Ubicación', 'Nivel', 'Función', 'Sexo', 'Liquidación', 'Apellido y nombre'] # Añadido 'Apellido y nombre'
    if 'Legajo' not in columns_for_filters_str: # Asegurarse de añadir 'Legajo' si no está
        columns_for_filters_str.insert(0, 'Legajo') # Insertar al principio para filtros si se necesitan

    for col in columns_for_filters_str:
        if col not in df_excel.columns:
            df_excel[col] = 'no disponible'
            # st.warning(f"Columna '{col}' necesaria para filtros/gráficos no encontrada, se creó con 'no disponible'.")
        df_excel[col] = df_excel[col].astype(str).str.strip().replace(['None', 'nan', ''], 'no disponible')

    # --- Convertir CECO y Nivel a enteros si es posible, manejando NaNs ---
    for col_to_int in ['CECO', 'Nivel']:
        if col_to_int in df_excel.columns:
            # Primero, intentar convertir a numérico (float) para capturar NaNs correctamente
            temp_col = pd.to_numeric(df_excel[col_to_int], errors='coerce')
            # Luego, convertir a Int64 si no hay NaNs o si se desea manejar los NaNs con el tipo de dato de Pandas.
            # Convertimos a Int64Dtype que permite NaNs, luego a string para la visualización y filtrado uniforme.
            # Manejo de valores "no disponible" antes de la conversión a Int64
            df_excel[col_to_int] = df_excel[col_to_int].replace('no disponible', pd.NA) # Reemplazar para que pd.to_numeric lo vea como NA
            df_excel[col_to_int] = pd.to_numeric(df_excel[col_to_int], errors='coerce').astype(pd.Int64Dtype()).astype(str).replace('<NA>', 'no disponible')

            # Una limpieza final para asegurar que números enteros como "123.0" se muestren como "123"
            def clean_numeric_string(s):
                if isinstance(s, str) and s.endswith('.0') and s[:-2].isdigit():
                    return s[:-2]
                return s
            df_excel[col_to_int] = df_excel[col_to_int].apply(clean_numeric_string)

            st.info(f"Columna '{col_to_int}' procesada para mostrarse sin decimales.")
        else:
            st.warning(f"Columna '{col_to_int}' no encontrada. Podría afectar la visualización de promedios.")
            df_excel[col_to_int] = 'no disponible' # Asegurar que exista


    # Display unique values for debugging
    # st.write(f"Valores únicos (normalizados) de 'Mes' después del procesamiento: {df_excel['Mes'].dropna().unique().tolist()}")
    # st.write(f"Valores únicos (normalizados) de 'Legajo' después del procesamiento: {df_excel['Legajo'].dropna().unique().tolist()}")
    # st.write(f"Valores únicos (normalizados) de 'CECO' después del procesamiento: {df_excel['CECO'].dropna().unique().tolist()}")
    # st.write(f"Valores únicos (normalizados) de 'Nivel' después del procesamiento: {df_excel['Nivel'].dropna().unique().tolist()}")

    return df_excel

# --- Cargar y limpiar tus datos ---
df = load_and_clean_data(EXCEL_FILE_NAME)

if df.empty:
    st.error("No se pudieron cargar o limpiar los datos. Por favor, verifica la subida del archivo y su nombre/hoja.")
    st.stop()

st.write(f"Se ha cargado un total de **{len(df)}** registros de horas extras.")
st.markdown('---')

# --- FILTROS INTERACTIVOS ---
st.sidebar.header('Filtros del Dashboard')

# Función auxiliar para obtener opciones únicas y ordernarlas (mejorada para números/strings)
def get_sorted_unique_options(dataframe, column_name):
    if column_name in dataframe.columns:
        unique_values = dataframe[column_name].dropna().unique().tolist()

        # Ordenación especial para el Mes (YYYY-MM)
        if column_name == 'Mes':
            return sorted(unique_values) # Ya está en YYYY-MM, así que el orden lexicográfico funciona

        # Ordenación especial para Legajo: numérico si es posible, sino alfabético
        if column_name == 'Legajo':
            numeric_vals = []
            non_numeric_vals = []
            for val in unique_values:
                if val == 'no disponible':
                    non_numeric_vals.append(val)
                    continue
                try:
                    numeric_vals.append(int(val))
                except ValueError:
                    non_numeric_vals.append(val)

            sorted_numeric_str = [str(x) for x in sorted(numeric_vals)]
            sorted_non_numeric_vals = sorted(non_numeric_vals)
            return sorted_numeric_str + sorted_non_numeric_vals

        # Para otras columnas, ordenar alfabéticamente
        return sorted(unique_values)
    return []

# Filtro de Gerencia (Multiselect)
all_gerencias = get_sorted_unique_options(df, 'Gerencia')
selected_gerencias = st.sidebar.multiselect('Selecciona Gerencia(s):', all_gerencias, default=all_gerencias)

# Filtro de Ministerio (Multiselect)
all_ministerios = get_sorted_unique_options(df, 'Ministerio')
selected_ministerios = st.sidebar.multiselect('Selecciona Ministerio(s):', all_ministerios, default=all_ministerios)

# Nuevos filtros
all_legajos = get_sorted_unique_options(df, 'Legajo')
selected_legajos = st.sidebar.multiselect('Selecciona Legajo(s):', all_legajos, default=all_legajos)

all_cecos = get_sorted_unique_options(df, 'CECO')
selected_cecos = st.sidebar.multiselect('Selecciona CECO(s):', all_cecos, default=all_cecos)

all_ubicaciones = get_sorted_unique_options(df, 'Ubicación')
selected_ubicaciones = st.sidebar.multiselect('Selecciona Ubicación(es):', all_ubicaciones, default=all_ubicaciones)

all_niveles = get_sorted_unique_options(df, 'Nivel')
selected_niveles = st.sidebar.multiselect('Selecciona Nivel(es):', all_niveles, default=all_niveles)

all_funciones = get_sorted_unique_options(df, 'Función')
selected_funciones = st.sidebar.multiselect('Selecciona Función(es):', all_funciones, default=all_funciones)

all_sexos = get_sorted_unique_options(df, 'Sexo')
selected_sexos = st.sidebar.multiselect('Selecciona Sexo(s):', all_sexos, default=all_sexos)

# Filtro de Mes
all_meses = get_sorted_unique_options(df, 'Mes') # Usamos la función con lógica YYYY-MM
selected_meses = st.sidebar.multiselect('Selecciona Mes(es):', all_meses, default=all_meses)

all_liquidaciones = get_sorted_unique_options(df, 'Liquidación')
selected_liquidaciones = st.sidebar.multiselect('Selecciona Liquidación(es):', all_liquidaciones, default=all_liquidaciones)

top_n_employees = st.sidebar.slider('Mostrar Top N Empleados:', 5, 50, 10)

# --- Nuevos filtros para tipos de HE (costos y cantidades) ---
st.sidebar.markdown("---")
st.sidebar.subheader("Selección de Tipos de Horas Extras")

# Definición de las columnas disponibles para selección
# Los valores de los diccionarios deben ser los nombres de las columnas REALES en tu DataFrame
# Los NamedAgg más abajo usarán estos mismos nombres.
cost_columns_options = {
    'Horas extras al 50 %': 'Horas extras al 50 %',
    'Horas extras al 50 % Sabados': 'Horas extras al 50 % Sabados',
    'Horas extras al 100%': 'Horas extras al 100%',
    'Importe HE Fc': 'Importe HE Fc'
}
quantity_columns_options = {
    'Cantidad HE 50': 'Cantidad HE 50',
    'Cant HE al 50 Sabados': 'Cant HE al 50 Sabados',
    'Cantidad HE 100': 'Cantidad HE 100',
    'Cantidad HE FC': 'Cantidad HE FC'
}

# Crear multiselect para costos
selected_cost_types_display = st.sidebar.multiselect(
    'Selecciona Tipos de Costo de HE:',
    list(cost_columns_options.keys()),
    default=list(cost_columns_options.keys()),
    key='filter_cost_types'
)
# Mapear los nombres de display a los nombres de columna reales
selected_cost_types_internal = [cost_columns_options[key] for key in selected_cost_types_display]


# Crear multiselect para cantidades
selected_quantity_types_display = st.sidebar.multiselect(
    'Selecciona Tipos de Cantidad de HE:',
    list(quantity_columns_options.keys()),
    default=list(quantity_columns_options.keys()),
    key='filter_quantity_types'
)
# Mapear los nombres de display a los nombres de columna reales
selected_quantity_types_internal = [quantity_columns_options[key] for key in selected_quantity_types_display]


# Aplicar filtros
filtered_df = df.copy()

if selected_gerencias:
    filtered_df = filtered_df[filtered_df['Gerencia'].isin(selected_gerencias)]
if selected_ministerios:
    filtered_df = filtered_df[filtered_df['Ministerio'].isin(selected_ministerios)]
if selected_legajos:
    filtered_df = filtered_df[filtered_df['Legajo'].isin(selected_legajos)]
if selected_cecos:
    filtered_df = filtered_df[filtered_df['CECO'].isin(selected_cecos)]
if selected_ubicaciones:
    filtered_df = filtered_df[filtered_df['Ubicación'].isin(selected_ubicaciones)]
if selected_niveles:
    filtered_df = filtered_df[filtered_df['Nivel'].isin(selected_niveles)]
if selected_funciones:
    filtered_df = filtered_df[filtered_df['Función'].isin(selected_funciones)]
if selected_sexos:
    filtered_df = filtered_df[filtered_df['Sexo'].isin(selected_sexos)]
if selected_meses:
    filtered_df = filtered_df[filtered_df['Mes'].isin(selected_meses)]
if selected_liquidaciones:
    filtered_df = filtered_df[filtered_df['Liquidación'].isin(selected_liquidaciones)]


st.write(f"Después de aplicar los filtros, se muestran **{len(filtered_df)}** registros de horas extras.")
st.markdown('---')

# --- DEFINICIÓN DE SOLAPAS (con íconos) ---
# AÑADIR LA NUEVA PESTAÑA "VALOR HORA" AQUÍ
tab1, tab2, tab3, tab_valor_hora, tab4 = st.tabs([
    "📈 Resumen y Tendencias", # Ícono para Tendencias
    "🏢 Desglose Organizacional", # Ícono para Organización
    "👤 Empleados Destacados", # Ícono para Empleados
    "⚖️ Valor Hora", # NUEVA PESTAÑA CON ÍCONO
    "📋 Datos Brutos" # Ícono para Datos
])

with tab1:
    # --- VISUALIZACIÓN 1: Tendencias Mensuales ---
    st.header('Tendencias Mensuales de Horas Extras')

    if filtered_df.empty:
        st.warning("No hay datos para mostrar con los filtros seleccionados.")
    else:
        # Asegurarse de agrupar por el Mes correcto (YYYY-MM) para la tendencia
        # Los NamedAgg usan los nombres de columna directos
        monthly_trends_agg = filtered_df.groupby('Mes').agg(
            **{col_name: pd.NamedAgg(column=col_name, aggfunc='sum')
               for col_name in set(list(cost_columns_options.values()) + list(quantity_columns_options.values()))
               if col_name in filtered_df.columns} # Solo agregar columnas que existan
        ).reset_index().sort_values(by='Mes')

        # Recalcular Total_Costos y Total_Cantidades basados en los tipos de HE seleccionados
        # Esto asegura que los totales reflejen solo lo que el usuario ha elegido ver
        if selected_cost_types_internal:
            # Asegurarse que las columnas existan en monthly_trends_agg antes de sumarlas
            cols_to_sum_cost = [col for col in selected_cost_types_internal if col in monthly_trends_agg.columns]
            monthly_trends_agg['Total_Costos'] = monthly_trends_agg[cols_to_sum_cost].sum(axis=1)
        else:
            monthly_trends_agg['Total_Costos'] = 0 # Si no hay tipos seleccionados, el total es 0

        if selected_quantity_types_internal:
            # Asegurarse que las columnas existan en monthly_trends_agg antes de sumarlas
            cols_to_sum_qty = [col for col in selected_quantity_types_internal if col in monthly_trends_agg.columns]
            monthly_trends_agg['Total_Cantidades'] = monthly_trends_agg[cols_to_sum_qty].sum(axis=1)
        else:
            monthly_trends_agg['Total_Cantidades'] = 0 # Si no hay tipos seleccionados, el total es 0


        # Preparar datos para gráficos de Costos (melt)
        # Incluir 'Total_Costos' siempre para que la línea del total se muestre,
        # pero también los tipos de costos seleccionados para las barras.
        dynamic_cost_cols_to_melt_for_chart = ['Total_Costos'] + [col for col in selected_cost_types_internal if col in monthly_trends_agg.columns] # Solo columnas que existen
        monthly_trends_costos_melted = monthly_trends_agg[['Mes'] + dynamic_cost_cols_to_melt_for_chart].melt('Mes', var_name='Tipo de Costo HE', value_name='Costo ($)')
        monthly_trends_costos_melted['Tipo de Costo HE'] = monthly_trends_costos_melted['Tipo de Costo HE'].replace({
            original_name: display_name for display_name, original_name in cost_columns_options.items() # Usar el mapeo original
        })
        monthly_trends_costos_melted['Tipo de Costo HE'] = monthly_trends_costos_melted['Tipo de Costo HE'].replace({'Total_Costos': 'Total ($)'}) # Reemplazar el nombre del total
        dynamic_cost_legend_order = ['Total ($)'] + selected_cost_types_display


        # Preparar datos para gráficos de Cantidades (melt)
        # Incluir 'Total_Cantidades' siempre para que la línea del total se muestre,
        # pero también los tipos de cantidades seleccionados para las barras.
        dynamic_quantity_cols_to_melt_for_chart = ['Total_Cantidades'] + [col for col in selected_quantity_types_internal if col in monthly_trends_agg.columns] # Solo columnas que existen
        monthly_trends_cantidades_melted = monthly_trends_agg[['Mes'] + dynamic_quantity_cols_to_melt_for_chart].melt('Mes', var_name='Tipo de Cantidad HE', value_name='Cantidad')
        monthly_trends_cantidades_melted['Tipo de Cantidad HE'] = monthly_trends_cantidades_melted['Tipo de Cantidad HE'].replace({
            original_name: display_name for display_name, original_name in quantity_columns_options.items() # Usar el mapeo original
        })
        monthly_trends_cantidades_melted['Tipo de Cantidad HE'] = monthly_trends_cantidades_melted['Tipo de Cantidad HE'].replace({'Total_Cantidades': 'Total (Q)'}) # Reemplazar el nombre del total
        dynamic_quantity_legend_order = ['Total (Q)'] + selected_quantity_types_display


        col1, col2 = st.columns(2)

        with col1:
            # Costos Mensuales - Línea para Total, Barras para componentes
            base_costos = alt.Chart(monthly_trends_costos_melted).encode(
                x=alt.X('Mes', title='Mes')
            )

            # Gráfico de línea para Total_Costos
            line_total_costos_chart = base_costos.mark_line(point=True).encode(
                y=alt.Y('Costo ($)', title='Costo ($)', axis=alt.Axis(format='$,.2f')),
                color=alt.value('blue'), # Color específico para la línea total
                tooltip=['Mes', alt.Tooltip('Tipo de Costo HE', title='Tipo'), alt.Tooltip('Costo ($)', format='$,.2f')]
            ).transform_filter(
                alt.datum['Tipo de Costo HE'] == 'Total ($)' # Usar el nombre de display aquí
            )

            # Gráficos de barras para los componentes
            # Usar 'selected_cost_types_display' para filtrar y para la leyenda
            bar_components_costos_chart = base_costos.mark_bar().encode(
                y=alt.Y('Costo ($)', title='Costo ($)', axis=alt.Axis(format='$,.2f')),
                color=alt.Color('Tipo de Costo HE',
                                sort=dynamic_cost_legend_order, # Ordenar la leyenda
                                legend=alt.Legend(title="Detalle Costo HE", orient='bottom') # Leyenda al pie
                               ),
                tooltip=['Mes', alt.Tooltip('Tipo de Costo HE', title='Tipo'), alt.Tooltip('Costo ($)', format='$,.2f')]
            ).transform_filter(
                alt.FieldOneOfPredicate(field='Tipo de Costo HE', oneOf=selected_cost_types_display) # Filtrar por los componentes seleccionados
            )

            # Combinar línea y barras, resolviendo la escala Y de forma independiente para permitir diferentes rangos
            chart_costos_mensual = alt.layer(line_total_costos_chart, bar_components_costos_chart).resolve_scale(y='independent').properties(title='Costos Mensuales').interactive()
            st.altair_chart(chart_costos_mensual, use_container_width=True)


        with col2:
            # Cantidades Mensuales - Línea para Total, Barras para componentes
            base_cantidades = alt.Chart(monthly_trends_cantidades_melted).encode(
                x=alt.X('Mes', title='Mes')
            )

            # Gráfico de línea para Total_Cantidades
            line_total_cantidades_chart = base_cantidades.mark_line(point=True).encode(
                y=alt.Y('Cantidad', title='Cantidad', axis=alt.Axis(format=',.2f')),
                color=alt.value('blue'), # Color específico para la línea total
                tooltip=['Mes', alt.Tooltip('Tipo de Cantidad HE', title='Tipo'), alt.Tooltip('Cantidad', format=',.2f')]
            ).transform_filter(
                alt.datum['Tipo de Cantidad HE'] == 'Total (Q)' # Usar el nombre de display aquí
            )

            # Gráficos de barras para los componentes
            # Usar 'selected_quantity_types_display' para filtrar y para la leyenda
            bar_components_cantidades_chart = base_cantidades.mark_bar().encode(
                y=alt.Y('Cantidad', title='Cantidad', axis=alt.Axis(format=',.2f')),
                color=alt.Color('Tipo de Cantidad HE',
                                sort=dynamic_quantity_legend_order, # Ordenar la leyenda
                                legend=alt.Legend(title="Detalle Cantidad HE", orient='bottom') # Leyenda al pie
                               ),
                tooltip=['Mes', alt.Tooltip('Tipo de Cantidad HE', title='Tipo'), alt.Tooltip('Cantidad', format=',.2f')]
            ).transform_filter(
                alt.FieldOneOfPredicate(field='Tipo de Cantidad HE', oneOf=selected_quantity_types_display) # Filtrar por los componentes seleccionados
            )

            # Combinar línea y barras, resolviendo la escala Y de forma independiente para permitir diferentes rangos
            chart_cantidades_mensual = alt.layer(line_total_cantidades_chart, bar_components_cantidades_chart).resolve_scale(y='independent').properties(title='Cantidades Mensuales').interactive()
            st.altair_chart(chart_cantidades_mensual, use_container_width=True)

        # --- Tabla y Descarga para Tendencias Mensuales ---
        st.subheader('Tabla de Tendencias Mensuales')
        # La tabla debe mostrar monthly_trends_agg, que es el DataFrame agregado original (no el derretido)
        # Filtrar las columnas para la tabla para que coincidan con la selección
        # Se asegura que las columnas seleccionadas existan en monthly_trends_agg antes de la selección
        valid_selected_cost_types_internal = [col for col in selected_cost_types_internal if col in monthly_trends_agg.columns]
        valid_selected_quantity_types_internal = [col for col in selected_quantity_types_internal if col in monthly_trends_agg.columns]

        cols_for_monthly_table = ['Mes', 'Total_Costos', 'Total_Cantidades'] + valid_selected_cost_types_internal + valid_selected_quantity_types_internal
        # Asegurarse de que todas las columnas en cols_for_monthly_table existan en monthly_trends_agg
        cols_for_monthly_table = [col for col in cols_for_monthly_table if col in monthly_trends_agg.columns]

        monthly_trends_with_total = add_total_row(monthly_trends_agg[cols_for_monthly_table], ['Mes'], cols_for_monthly_table[1:])
        st.dataframe(format_st_dataframe(monthly_trends_with_total))
        generate_download_buttons(monthly_trends_with_total, 'tendencias_mensuales')

    st.markdown('---')

    # --- NUEVA SECCIÓN: Análisis de Variaciones Mensuales ---
    st.header('Análisis de Variaciones Mensuales')
    if filtered_df.empty:
        st.warning("No hay datos para mostrar el análisis de variaciones mensuales con los filtros seleccionados.")
    else:
        # Los NamedAgg usan los nombres de columna directos
        monthly_trends_for_var_raw = filtered_df.groupby('Mes').agg(
            **{col_name: pd.NamedAgg(column=col_name, aggfunc='sum')
               for col_name in set(list(cost_columns_options.values()) + list(quantity_columns_options.values()))
               if col_name in filtered_df.columns} # Solo agregar columnas que existan
        ).reset_index().sort_values(by='Mes')

        # Recalcular Total_Costos y Total_Cantidades para el análisis de variación
        if selected_cost_types_internal:
            monthly_trends_for_var_raw['Total_Costos'] = monthly_trends_for_var_raw[[col for col in selected_cost_types_internal if col in monthly_trends_for_var_raw.columns]].sum(axis=1)
        else:
            monthly_trends_for_var_raw['Total_Costos'] = 0

        if selected_quantity_types_internal:
            monthly_trends_for_var_raw['Total_Cantidades'] = monthly_trends_for_var_raw[[col for col in selected_quantity_types_internal if col in monthly_trends_for_var_raw.columns]].sum(axis=1)
        else:
            monthly_trends_for_var_raw['Total_Cantidades'] = 0

        # Copiar para evitar SettingWithCopyWarning
        monthly_trends_for_var = monthly_trends_for_var_raw[['Mes', 'Total_Costos', 'Total_Cantidades']].copy()

        # Calcular variaciones
        monthly_trends_for_var['Variacion_Costos_Abs'] = monthly_trends_for_var['Total_Costos'].diff().fillna(0)
        monthly_trends_for_var['Variacion_Cantidades_Abs'] = monthly_trends_for_var['Total_Cantidades'].diff().fillna(0)

        # Calcular variaciones porcentuales (para el texto, no necesariamente para el gráfico)
        # Evitar división por cero
        monthly_trends_for_var['Variacion_Costos_Pct'] = monthly_trends_for_var['Total_Costos'].pct_change().fillna(0) * 100
        monthly_trends_for_var['Variacion_Cantidades_Pct'] = monthly_trends_for_var['Total_Cantidades'].pct_change().fillna(0) * 100

        col_var1, col_var2 = st.columns(2)

        with col_var1:
            chart_var_costos = alt.Chart(monthly_trends_for_var).mark_bar().encode(
                x=alt.X('Mes', title='Mes'),
                y=alt.Y('Variacion_Costos_Abs', title='Variación de Costos ($)', axis=alt.Axis(format='$,.2f')),
                color=alt.condition(
                    alt.datum.Variacion_Costos_Abs > 0,
                    alt.value('green'),    # Verde si el cambio es positivo
                    alt.value('red')       # Rojo si el cambio es negativo
                ),
                tooltip=[
                    'Mes',
                    alt.Tooltip('Variacion_Costos_Abs', title='Variación Costos ($)', format='$,.2f')
                ]
            ).properties(title='Variación Mensual de Costos').interactive()
            st.altair_chart(chart_var_costos, use_container_width=True)

        with col_var2:
            chart_var_cantidades = alt.Chart(monthly_trends_for_var).mark_bar().encode(
                x=alt.X('Mes', title='Mes'),
                y=alt.Y('Variacion_Cantidades_Abs', title='Variación de Cantidades de HE', axis=alt.Axis(format=',.2f')),
                color=alt.condition(
                    alt.datum.Variacion_Cantidades_Abs > 0,
                    alt.value('green'),    # Verde si el cambio es positivo
                    alt.value('red')       # Rojo si el cambio es negativo
                ),
                tooltip=[
                    'Mes',
                    alt.Tooltip('Variacion_Cantidades_Abs', title='Variación Cantidades HE', format=',.2f')
                ]
            ).properties(title='Variación Mensual de Cantidades').interactive()
            st.altair_chart(chart_var_cantidades, use_container_width=True)

        # --- Tabla y Descarga para Variaciones Mensuales ---
        st.subheader('Tabla de Variaciones Mensuales')
        df_variaciones = monthly_trends_for_var[['Mes', 'Total_Costos', 'Variacion_Costos_Abs', 'Variacion_Costos_Pct', 'Total_Cantidades', 'Variacion_Cantidades_Abs', 'Variacion_Cantidades_Pct']]
        st.dataframe(format_st_dataframe(df_variaciones))
        generate_download_buttons(monthly_trends_for_var, 'variaciones_mensuales')
    st.markdown('---')


with tab2:
    # --- VISUALIZACIÓN 2: Distribución por Gerencia y Ministerio ---
    st.header('Distribución por Gerencia y Ministerio')

    if filtered_df.empty:
        st.warning("No hay datos para mostrar la distribución por Gerencia y Ministerio con los filtros seleccionados.")
    else:
        # Los NamedAgg usan los nombres de columna directos
        df_grouped_gm = filtered_df.groupby(['Gerencia', 'Ministerio']).agg(
            **{col_name: pd.NamedAgg(column=col_name, aggfunc='sum')
               for col_name in set(list(cost_columns_options.values()) + list(quantity_columns_options.values()))
               if col_name in filtered_df.columns} # Solo agregar columnas que existan
        ).reset_index().sort_values(by='Gerencia', ascending=True)

        # Recalcular Total_Costos y Total_Cantidades basados en los tipos de HE seleccionados
        if selected_cost_types_internal:
            df_grouped_gm['Total_Costos'] = df_grouped_gm[[col for col in selected_cost_types_internal if col in df_grouped_gm.columns]].sum(axis=1)
        else:
            df_grouped_gm['Total_Costos'] = 0

        if selected_quantity_types_internal:
            df_grouped_gm['Total_Cantidades'] = df_grouped_gm[[col for col in selected_quantity_types_internal if col in df_grouped_gm.columns]].sum(axis=1)
        else:
            df_grouped_gm['Total_Cantidades'] = 0

        df_grouped_gm_sorted_by_cost = df_grouped_gm.sort_values(by='Total_Costos', ascending=False)


        col3, col4 = st.columns(2)

        with col3:
            chart_costos_gm = alt.Chart(df_grouped_gm_sorted_by_cost).mark_bar().encode(
                x=alt.X('Total_Costos', title='Total de Costos ($)', axis=alt.Axis(format='$,.2f')),
                y=alt.Y('Gerencia:N', sort='-x', title='Gerencia'),
                color=alt.Color('Ministerio', legend=alt.Legend(title="Ministerio", orient='bottom')), # Leyenda al pie
                tooltip=[
                    'Gerencia', 'Ministerio',
                    alt.Tooltip('Total_Costos', title='Total Costos ($)', format='$,.2f')
                ]
            ).properties(title='Costos por Gerencia y Ministerio').interactive()
            st.altair_chart(chart_costos_gm, use_container_width=True)

        with col4:
            chart_cantidades_gm = alt.Chart(df_grouped_gm_sorted_by_cost).mark_bar().encode(
                x=alt.X('Total_Cantidades', title='Total de Cantidades de HE', axis=alt.Axis(format=',.2f')),
                y=alt.Y('Gerencia:N', sort='-x', title='Gerencia'),
                color=alt.Color('Ministerio', legend=alt.Legend(title="Ministerio", orient='bottom')), # Leyenda al pie
                tooltip=[
                    'Gerencia', 'Ministerio',
                    alt.Tooltip('Total_Cantidades', title='Total Cantidades HE', format=',.2f')
                ]
            ).properties(title='Cantidades por Gerencia y Ministerio').interactive()
            st.altair_chart(chart_cantidades_gm, use_container_width=True)

        st.subheader('Tabla de Distribución por Gerencia y Ministerio')
        valid_selected_cost_types_internal_gm = [col for col in selected_cost_types_internal if col in df_grouped_gm.columns]
        valid_selected_quantity_types_internal_gm = [col for col in selected_quantity_types_internal if col in df_grouped_gm.columns]
        cols_for_gm_table = ['Gerencia', 'Ministerio', 'Total_Costos', 'Total_Cantidades'] + valid_selected_cost_types_internal_gm + valid_selected_quantity_types_internal_gm
        df_grouped_gm_with_total = add_total_row(df_grouped_gm[cols_for_gm_table], ['Gerencia', 'Ministerio'], cols_for_gm_table[2:])
        st.dataframe(format_st_dataframe(df_grouped_gm_with_total))
        generate_download_buttons(df_grouped_gm_with_total, 'distribucion_gerencia_ministerio')

    st.markdown('---')

    # --- NUEVA SECCIÓN: Distribución por Gerencia y Sexo ---
    st.header('Distribución por Gerencia y Sexo')
    if filtered_df.empty:
        st.warning("No hay datos para mostrar la distribución por Gerencia y Sexo con los filtros seleccionados.")
    else:
        # Los NamedAgg usan los nombres de columna directos
        df_grouped_gs = filtered_df.groupby(['Gerencia', 'Sexo']).agg(
            **{col_name: pd.NamedAgg(column=col_name, aggfunc='sum')
               for col_name in set(list(cost_columns_options.values()) + list(quantity_columns_options.values()))
               if col_name in filtered_df.columns} # Solo agregar columnas que existan
        ).reset_index().sort_values(by='Gerencia', ascending=True)

        # Recalcular Total_Costos y Total_Cantidades basados en los tipos de HE seleccionados
        if selected_cost_types_internal:
            df_grouped_gs['Total_Costos'] = df_grouped_gs[[col for col in selected_cost_types_internal if col in df_grouped_gs.columns]].sum(axis=1)
        else:
            df_grouped_gs['Total_Costos'] = 0

        if selected_quantity_types_internal:
            df_grouped_gs['Total_Cantidades'] = df_grouped_gs[[col for col in selected_quantity_types_internal if col in df_grouped_gs.columns]].sum(axis=1)
        else:
            df_grouped_gs['Total_Cantidades'] = 0

        df_grouped_gs_sorted_by_cost = df_grouped_gs.sort_values(by='Total_Costos', ascending=False)

        col_gs1, col_gs2 = st.columns(2)
        with col_gs1:
            chart_costos_gs = alt.Chart(df_grouped_gs_sorted_by_cost).mark_bar().encode(
                x=alt.X('Total_Costos', title='Total de Costos ($)', axis=alt.Axis(format='$,.2f')),
                y=alt.Y('Gerencia:N', sort='-x', title='Gerencia'),
                color=alt.Color('Sexo', legend=alt.Legend(title="Sexo", orient='bottom')), # Leyenda al pie
                tooltip=[
                    'Gerencia', 'Sexo',
                    alt.Tooltip('Total_Costos', title='Total Costos ($)', format='$,.2f')
                ]
            ).properties(title='Costos por Gerencia y Sexo').interactive()
            st.altair_chart(chart_costos_gs, use_container_width=True)

        with col_gs2:
            chart_cantidades_gs = alt.Chart(df_grouped_gs_sorted_by_cost).mark_bar().encode(
                x=alt.X('Total_Cantidades', title='Total de Cantidades de HE', axis=alt.Axis(format=',.2f')),
                y=alt.Y('Gerencia:N', sort='-x', title='Gerencia'),
                color=alt.Color('Sexo', legend=alt.Legend(title="Sexo", orient='bottom')), # Leyenda al pie
                tooltip=[
                    'Gerencia', 'Sexo',
                    alt.Tooltip('Total_Cantidades', title='Total Cantidades HE', format=',.2f')
                ]
            ).properties(title='Cantidades por Gerencia y Sexo').interactive()
            st.altair_chart(chart_cantidades_gs, use_container_width=True)

        st.subheader('Tabla de Distribución por Gerencia y Sexo')
        valid_selected_cost_types_internal_gs = [col for col in selected_cost_types_internal if col in df_grouped_gs.columns]
        valid_selected_quantity_types_internal_gs = [col for col in selected_quantity_types_internal if col in df_grouped_gs.columns]
        cols_for_gs_table = ['Gerencia', 'Sexo', 'Total_Costos', 'Total_Cantidades'] + valid_selected_cost_types_internal_gs + valid_selected_quantity_types_internal_gs
        df_grouped_gs_with_total = add_total_row(df_grouped_gs[cols_for_gs_table], ['Gerencia', 'Sexo'], cols_for_gs_table[2:])
        st.dataframe(format_st_dataframe(df_grouped_gs_with_total))
        generate_download_buttons(df_grouped_gs_with_total, 'distribucion_gerencia_sexo')
    st.markdown('---')

    # --- NUEVA SECCIÓN: Distribución por Ministerio y Sexo ---
    st.header('Distribución por Ministerio y Sexo')
    if filtered_df.empty:
        st.warning("No hay datos para mostrar la distribución por Ministerio y Sexo con los filtros seleccionados.")
    else:
        # Los NamedAgg usan los nombres de columna directos
        df_grouped_ms = filtered_df.groupby(['Ministerio', 'Sexo']).agg(
            **{col_name: pd.NamedAgg(column=col_name, aggfunc='sum')
               for col_name in set(list(cost_columns_options.values()) + list(quantity_columns_options.values()))
               if col_name in filtered_df.columns} # Solo agregar columnas que existan
        ).reset_index().sort_values(by='Ministerio', ascending=True)

        # Recalcular Total_Costos y Total_Cantidades basados en los tipos de HE seleccionados
        if selected_cost_types_internal:
            df_grouped_ms['Total_Costos'] = df_grouped_ms[[col for col in selected_cost_types_internal if col in df_grouped_ms.columns]].sum(axis=1)
        else:
            df_grouped_ms['Total_Costos'] = 0

        if selected_quantity_types_internal:
            df_grouped_ms['Total_Cantidades'] = df_grouped_ms[[col for col in selected_quantity_types_internal if col in df_grouped_ms.columns]].sum(axis=1)
        else:
            df_grouped_ms['Total_Cantidades'] = 0

        df_grouped_ms_sorted_by_cost = df_grouped_ms.sort_values(by='Total_Costos', ascending=False)

        col_ms1, col_ms2 = st.columns(2)
        with col_ms1:
            chart_costos_ms = alt.Chart(df_grouped_ms_sorted_by_cost).mark_bar().encode(
                x=alt.X('Total_Costos', title='Total de Costos ($)', axis=alt.Axis(format='$,.2f')),
                y=alt.Y('Ministerio:N', sort='-x', title='Ministerio'),
                color=alt.Color('Sexo', legend=alt.Legend(title="Sexo", orient='bottom')), # Leyenda al pie
                tooltip=[
                    'Ministerio', 'Sexo',
                    alt.Tooltip('Total_Costos', title='Total Costos ($)', format='$,.2f')
                ]
            ).properties(title='Costos por Ministerio y Sexo').interactive()
            st.altair_chart(chart_costos_ms, use_container_width=True)

        with col_ms2:
            chart_cantidades_ms = alt.Chart(df_grouped_ms_sorted_by_cost).mark_bar().encode(
                x=alt.X('Total_Cantidades', title='Total de Cantidades de HE', axis=alt.Axis(format=',.2f')),
                y=alt.Y('Ministerio:N', sort='-x', title='Ministerio'),
                color=alt.Color('Sexo', legend=alt.Legend(title="Sexo", orient='bottom')), # Leyenda al pie
                tooltip=[
                    'Ministerio', 'Sexo',
                    alt.Tooltip('Total_Cantidades', title='Total Cantidades HE', format=',.2f')
                ]
            ).properties(title='Cantidades por Ministerio y Sexo').interactive()
            st.altair_chart(chart_cantidades_ms, use_container_width=True)

        st.subheader('Tabla de Distribución por Ministerio y Sexo')
        valid_selected_cost_types_internal_ms = [col for col in selected_cost_types_internal if col in df_grouped_ms.columns]
        valid_selected_quantity_types_internal_ms = [col for col in selected_quantity_types_internal if col in df_grouped_ms.columns]
        cols_for_ms_table = ['Ministerio', 'Sexo', 'Total_Costos', 'Total_Cantidades'] + valid_selected_cost_types_internal_ms + valid_selected_quantity_types_internal_ms
        df_grouped_ms_with_total = add_total_row(df_grouped_ms[cols_for_ms_table], ['Ministerio', 'Sexo'], cols_for_ms_table[2:])
        st.dataframe(format_st_dataframe(df_grouped_ms_with_total))
        generate_download_buttons(df_grouped_ms_with_total, 'distribucion_ministerio_sexo')
    st.markdown('---')

    # --- NUEVA SECCIÓN: Distribución por Nivel y Sexo ---
    st.header('Distribución por Nivel y Sexo')
    if filtered_df.empty:
        st.warning("No hay datos para mostrar la distribución por Nivel y Sexo con los filtros seleccionados.")
    else:
        # Los NamedAgg usan los nombres de columna directos
        df_grouped_ns = filtered_df.groupby(['Nivel', 'Sexo']).agg(
            **{col_name: pd.NamedAgg(column=col_name, aggfunc='sum')
               for col_name in set(list(cost_columns_options.values()) + list(quantity_columns_options.values()))
               if col_name in filtered_df.columns} # Solo agregar columnas que existan
        ).reset_index().sort_values(by='Nivel', ascending=True)

        # Recalcular Total_Costos y Total_Cantidades basados en los tipos de HE seleccionados
        if selected_cost_types_internal:
            df_grouped_ns['Total_Costos'] = df_grouped_ns[[col for col in selected_cost_types_internal if col in df_grouped_ns.columns]].sum(axis=1)
        else:
            df_grouped_ns['Total_Costos'] = 0

        if selected_quantity_types_internal:
            df_grouped_ns['Total_Cantidades'] = df_grouped_ns[[col for col in selected_quantity_types_internal if col in df_grouped_ns.columns]].sum(axis=1)
        else:
            df_grouped_ns['Total_Cantidades'] = 0

        df_grouped_ns_sorted_by_cost = df_grouped_ns.sort_values(by='Total_Costos', ascending=False)

        col_ns1, col_ns2 = st.columns(2)
        with col_ns1:
            chart_costos_ns = alt.Chart(df_grouped_ns_sorted_by_cost).mark_bar().encode(
                x=alt.X('Total_Costos', title='Total de Costos ($)', axis=alt.Axis(format='$,.2f')),
                y=alt.Y('Nivel:N', sort='-x', title='Nivel'),
                color=alt.Color('Sexo', legend=alt.Legend(title="Sexo", orient='bottom')), # Leyenda al pie
                tooltip=[
                    'Nivel', 'Sexo',
                    alt.Tooltip('Total_Costos', title='Total Costos ($)', format='$,.2f')
                ]
            ).properties(title='Costos por Nivel y Sexo').interactive()
            st.altair_chart(chart_costos_ns, use_container_width=True)

        with col_ns2:
            chart_cantidades_ns = alt.Chart(df_grouped_ns_sorted_by_cost).mark_bar().encode(
                x=alt.X('Total_Cantidades', title='Total de Cantidades de HE', axis=alt.Axis(format=',.2f')),
                y=alt.Y('Nivel:N', sort='-x', title='Nivel'),
                color=alt.Color('Sexo', legend=alt.Legend(title="Sexo", orient='bottom')), # Leyenda al pie
                tooltip=[
                    'Nivel', 'Sexo',
                    alt.Tooltip('Total_Cantidades', title='Total Cantidades HE', format=',.2f')
                ]
            ).properties(title='Cantidades por Nivel y Sexo').interactive()
            st.altair_chart(chart_cantidades_ns, use_container_width=True)

        st.subheader('Tabla de Distribución por Nivel y Sexo')
        valid_selected_cost_types_internal_ns = [col for col in selected_cost_types_internal if col in df_grouped_ns.columns]
        valid_selected_quantity_types_internal_ns = [col for col in selected_quantity_types_internal if col in df_grouped_ns.columns]
        cols_for_ns_table = ['Nivel', 'Sexo', 'Total_Costos', 'Total_Cantidades'] + valid_selected_cost_types_internal_ns + valid_selected_quantity_types_internal_ns
        df_grouped_ns_with_total = add_total_row(df_grouped_ns[cols_for_ns_table], ['Nivel', 'Sexo'], cols_for_ns_table[2:])
        st.dataframe(format_st_dataframe(df_grouped_ns_with_total))
        generate_download_buttons(df_grouped_ns_with_total, 'distribucion_nivel_sexo')
    st.markdown('---')

    # --- NUEVA SECCIÓN: Distribución por Función y Sexo ---
    st.header('Distribución por Función y Sexo')
    if filtered_df.empty:
        st.warning("No hay datos para mostrar la distribución por Función y Sexo con los filtros seleccionados.")
    else:
        # Los NamedAgg usan los nombres de columna directos
        df_grouped_fs = filtered_df.groupby(['Función', 'Sexo']).agg(
            **{col_name: pd.NamedAgg(column=col_name, aggfunc='sum')
               for col_name in set(list(cost_columns_options.values()) + list(quantity_columns_options.values()))
               if col_name in filtered_df.columns} # Solo agregar columnas que existan
        ).reset_index().sort_values(by='Función', ascending=True)

        # Recalcular Total_Costos y Total_Cantidades basados en los tipos de HE seleccionados
        if selected_cost_types_internal:
            df_grouped_fs['Total_Costos'] = df_grouped_fs[[col for col in selected_cost_types_internal if col in df_grouped_fs.columns]].sum(axis=1)
        else:
            df_grouped_fs['Total_Costos'] = 0

        if selected_quantity_types_internal:
            df_grouped_fs['Total_Cantidades'] = df_grouped_fs[[col for col in selected_quantity_types_internal if col in df_grouped_fs.columns]].sum(axis=1)
        else:
            df_grouped_fs['Total_Cantidades'] = 0

        df_grouped_fs_sorted_by_cost = df_grouped_fs.sort_values(by='Total_Costos', ascending=False)

        col_fs1, col_fs2 = st.columns(2)
        with col_fs1:
            chart_costos_fs = alt.Chart(df_grouped_fs_sorted_by_cost).mark_bar().encode(
                x=alt.X('Total_Costos', title='Total de Costos ($)', axis=alt.Axis(format='$,.2f')),
                y=alt.Y('Función:N', sort='-x', title='Función'),
                color=alt.Color('Sexo', legend=alt.Legend(title="Sexo", orient='bottom')), # Leyenda al pie
                tooltip=[
                    'Función', 'Sexo',
                    alt.Tooltip('Total_Costos', title='Total Costos ($)', format='$,.2f')
                ]
            ).properties(title='Costos por Función y Sexo').interactive()
            st.altair_chart(chart_costos_fs, use_container_width=True)

        with col_fs2:
            chart_cantidades_fs = alt.Chart(df_grouped_fs_sorted_by_cost).mark_bar().encode(
                x=alt.X('Total_Cantidades', title='Total de Cantidades de HE', axis=alt.Axis(format=',.2f')),
                y=alt.Y('Función:N', sort='-x', title='Función'),
                color=alt.Color('Sexo', legend=alt.Legend(title="Sexo", orient='bottom')), # Leyenda al pie
                tooltip=[
                    'Función', 'Sexo',
                    alt.Tooltip('Total_Cantidades', title='Total Cantidades HE', format=',.2f')
                ]
            ).properties(title='Cantidades por Función y Sexo').interactive()
            st.altair_chart(chart_cantidades_fs, use_container_width=True)

        st.subheader('Tabla de Distribución por Función y Sexo')
        valid_selected_cost_types_internal_fs = [col for col in selected_cost_types_internal if col in df_grouped_fs.columns]
        valid_selected_quantity_types_internal_fs = [col for col in selected_quantity_types_internal if col in df_grouped_fs.columns]
        cols_for_fs_table = ['Función', 'Sexo', 'Total_Costos', 'Total_Cantidades'] + valid_selected_cost_types_internal_fs + valid_selected_quantity_types_internal_fs
        df_grouped_fs_with_total = add_total_row(df_grouped_fs[cols_for_fs_table], ['Función', 'Sexo'], cols_for_fs_table[2:])
        st.dataframe(format_st_dataframe(df_grouped_fs_with_total))
        generate_download_buttons(df_grouped_fs_with_total, 'distribucion_funcion_sexo')
    st.markdown('---')

with tab3:
    # --- VISUALIZACIÓN 3: Top N Empleados ---
    st.header(f'Top {top_n_employees} Empleados con Mayor Horas Extras')

    if filtered_df.empty:
        st.warning("No hay datos para mostrar el Top N de empleados con los filtros seleccionados.")
    else:
        # Agrupar por Legajo y Apellido y nombre para el Top N
        agg_cols = {}
        for col_name in cost_columns_options.values():
            if col_name in filtered_df.columns:
                agg_cols[f'{col_name}_costo_agg'] = pd.NamedAgg(column=col_name, aggfunc='sum')
        for col_name in quantity_columns_options.values():
            if col_name in filtered_df.columns:
                agg_cols[f'{col_name}_cant_agg'] = pd.NamedAgg(column=col_name, aggfunc='sum')

        employee_overtime = filtered_df.groupby(['Legajo', 'Apellido y nombre']).agg(
            **agg_cols
        ).reset_index()

        # Recalcular Total_Costos y Total_Cantidades basados en las *nuevas* columnas agregadas
        total_cost_cols_for_sum = []
        for original_col in selected_cost_types_internal:
            agg_col_name = f'{original_col}_costo_agg'
            if agg_col_name in employee_overtime.columns:
                total_cost_cols_for_sum.append(agg_col_name)

        if total_cost_cols_for_sum:
            employee_overtime['Total_Costos'] = employee_overtime[total_cost_cols_for_sum].sum(axis=1)
        else:
            employee_overtime['Total_Costos'] = 0

        total_quantity_cols_for_sum = []
        for original_col in selected_quantity_types_internal:
            agg_col_name = f'{original_col}_cant_agg'
            if agg_col_name in employee_overtime.columns:
                total_quantity_cols_for_sum.append(agg_col_name)

        if total_quantity_cols_for_sum:
            employee_overtime['Total_Cantidades'] = employee_overtime[total_quantity_cols_for_sum].sum(axis=1)
        else:
            employee_overtime['Total_Cantidades'] = 0

        # --- Gráficos Top N Empleados ---
        col_top_charts_1, col_top_charts_2 = st.columns(2)

        with col_top_charts_1:
            st.subheader('Top por Costo')
            top_costo_empleados = employee_overtime.nlargest(top_n_employees, 'Total_Costos')

            if not top_costo_empleados.empty:
                chart_top_costo = alt.Chart(top_costo_empleados).mark_bar().encode(
                    y=alt.Y('Apellido y nombre:N', sort='-x', title='Empleado'),
                    x=alt.X('Total_Costos:Q', title='Total Costos ($)', axis=alt.Axis(format='$,.2f')),
                    tooltip=['Apellido y nombre', alt.Tooltip('Total_Costos', title='Total Costos ($)', format='$,.2f')]
                ).properties(
                    title=f'Top {top_n_employees} Empleados por Costo de HE'
                ).interactive()
                st.altair_chart(chart_top_costo, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar el Top por Costo.")

        with col_top_charts_2:
            st.subheader('Top por Cantidad')
            top_cantidad_empleados = employee_overtime.nlargest(top_n_employees, 'Total_Cantidades')

            if not top_cantidad_empleados.empty:
                chart_top_cantidad = alt.Chart(top_cantidad_empleados).mark_bar().encode(
                    y=alt.Y('Apellido y nombre:N', sort='-x', title='Empleado'),
                    x=alt.X('Total_Cantidades:Q', title='Total Cantidades HE', axis=alt.Axis(format=',.2f')),
                    tooltip=['Apellido y nombre', alt.Tooltip('Total_Cantidades', title='Total Cantidades HE', format=',.2f')]
                ).properties(
                    title=f'Top {top_n_employees} Empleados por Cantidad de HE'
                ).interactive()
                st.altair_chart(chart_top_cantidad, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar el Top por Cantidad.")

        st.markdown('---') # Separador entre gráficos y tablas

        # --- Top 10 por Importe de Horas Extras (Tabla) --- (AHORA PRIMERO)
        st.subheader('Tabla de Top Importe Horas Extras')
        top10_imp_he = employee_overtime.nlargest(top_n_employees, 'Total_Costos')

        display_cols_imp = ['Legajo', 'Apellido y nombre', 'Total_Costos', 'Total_Cantidades']
        for original_col in selected_cost_types_internal:
            agg_col_name = f'{original_col}_costo_agg'
            if agg_col_name in top10_imp_he.columns and agg_col_name not in display_cols_imp:
                display_cols_imp.append(agg_col_name)
        for original_col in selected_quantity_types_internal:
            agg_col_name = f'{original_col}_cant_agg'
            if agg_col_name in top10_imp_he.columns and agg_col_name not in display_cols_imp:
                display_cols_imp.append(agg_col_name)

        st.dataframe(format_st_dataframe(top10_imp_he[display_cols_imp]))
        generate_download_buttons(top10_imp_he[display_cols_imp], f'top_{top_n_employees}_importe_horas_extras')
        st.markdown('---')

        # --- Top 10 por Cantidad de Horas Extras (Tabla) --- (AHORA SEGUNDO)
        st.subheader('Tabla de Top Cantidad Horas Extras')
        top10_cant_he = employee_overtime.nlargest(top_n_employees, 'Total_Cantidades')

        display_cols_cant = ['Legajo', 'Apellido y nombre', 'Total_Cantidades', 'Total_Costos']
        for original_col in selected_quantity_types_internal:
            agg_col_name = f'{original_col}_cant_agg'
            if agg_col_name in top10_cant_he.columns and agg_col_name not in display_cols_cant:
                display_cols_cant.append(agg_col_name)
        for original_col in selected_cost_types_internal:
            agg_col_name = f'{original_col}_costo_agg'
            if agg_col_name in top10_cant_he.columns and agg_col_name not in display_cols_cant:
                display_cols_cant.append(agg_col_name)

        st.dataframe(format_st_dataframe(top10_cant_he[display_cols_cant]))
        generate_download_buttons(top10_cant_he[display_cols_cant], f'top_{top_n_employees}_cantidad_horas_extras')
        st.markdown('---')

# --- INICIO DE LA NUEVA PESTAÑA: VALOR HORA ---
with tab_valor_hora:
    st.header('Valores Promedio por Hora')
    st.write("Analiza el valor promedio por hora (Normal y Extra) desglosado por diferentes dimensiones.")

    if filtered_df.empty:
        st.warning("No hay datos para mostrar los valores promedio por hora con los filtros seleccionados.")
    else:
        # Definir las columnas de "Valor Hora"
        valor_hora_cols = [
            'Hora Normal', 'Hora Extra al 50%', 'Hora Extra al 50% Sabados',
            'Hora Extra al 100%', 'HE FC'
        ]

        # Asegurarse de que las columnas existan en el DataFrame filtrado, si no, se llenaron con 0 en load_and_clean_data
        # Filtrar solo las columnas que realmente existen en filtered_df
        available_valor_hora_cols = [col for col in valor_hora_cols if col in filtered_df.columns]

        if not available_valor_hora_cols:
            st.warning("No se encontraron columnas de 'Valor Hora' en los datos filtrados. Por favor, verifica tu archivo Excel y los nombres de las columnas.")
        else:
            # Selector de la dimensión de agrupación
            grouping_dimension_options = ['Gerencia', 'Legajo', 'Función', 'CECO', 'Ubicación', 'Nivel', 'Sexo']
            selected_grouping_dimension = st.selectbox(
                'Selecciona la dimensión de desglose:',
                grouping_dimension_options,
                key='valor_hora_grouping'
            )

            # Verificar que la dimensión seleccionada existe en el DataFrame
            if selected_grouping_dimension not in filtered_df.columns:
                st.error(f"La columna '{selected_grouping_dimension}' no se encontró en los datos. Por favor, revisa tu archivo Excel.")
            else:
                # Agrupar por Mes y la dimensión seleccionada, calculando el promedio
                # Es crucial que las columnas en `available_valor_hora_cols` sean sumables (numéricas)
                # y que se aplique la media (mean) ya que buscamos un valor promedio por hora.
                group_cols_for_valor_hora = ['Mes', selected_grouping_dimension]

                # Crear las agregaciones dinámicamente para el promedio
                agg_dict_valor_hora = {
                    col: pd.NamedAgg(column=col, aggfunc='mean')
                    for col in available_valor_hora_cols
                }

                df_valor_hora_grouped = filtered_df.groupby(group_cols_for_valor_hora).agg(
                    **agg_dict_valor_hora
                ).reset_index()

                # Melt el DataFrame para usarlo en gráficos de línea con múltiples tipos de valor hora
                # Esto es útil si quieres visualizar cada tipo de hora por separado en un gráfico
                df_valor_hora_melted = df_valor_hora_grouped.melt(
                    id_vars=['Mes', selected_grouping_dimension],
                    value_vars=available_valor_hora_cols,
                    var_name='Tipo de Hora',
                    value_name='Valor Promedio por Hora ($)'
                )

                st.subheader(f'Valores Promedio por Hora por Mes y {selected_grouping_dimension}')

                # Gráfico de líneas para la tendencia del valor promedio total por mes
                # Calculamos un "Total Promedio" para el gráfico de línea general
                # Esto es el promedio de los promedios de los tipos de hora por mes, no la suma, ya que son valores de hora.
                # Si quisieras un "promedio del promedio", tendrías que reconsiderar la matemática.
                # Aquí, calculamos el promedio de cada columna de valor_hora y luego los sumamos para un "valor promedio total por mes"
                # o podrías simplemente promediar solo la columna 'Hora Normal' para una visión simple de tendencia.
                # Para un "valor promedio total" que combine todos los tipos de hora, lo más sensato sería
                # un promedio ponderado si tuvieras las cantidades de horas de cada tipo, o simplemente
                # el promedio general del importe total de horas dividido por el total de horas si esas columnas estuvieran disponibles.
                # Dado que solo tenemos los "valores por hora", un simple promedio de esos valores
                # no es un "total" sino un promedio del promedio, lo cual puede ser engañoso.
                # Una opción más robusta para el "total" es sumar los promedios de los tipos de hora si representan el valor monetario
                # de la hora para diferentes conceptos, o mostrar cada tipo de hora por separado.
                # Para este gráfico de "tendencia mensual del valor promedio total", sumaremos los promedios de cada tipo de hora
                # para obtener un valor "total" por mes. Esto asume que todos los tipos de hora son igualmente relevantes para el "total".

                # Calcular el promedio de cada columna de valor_hora por mes y luego sumarlos para un "total" por mes
                df_valor_hora_monthly_total_avg = filtered_df.groupby('Mes')[available_valor_hora_cols].mean().sum(axis=1).reset_index(name='Valor Promedio Total por Hora ($)')

                chart_total_avg_valor_hora = alt.Chart(df_valor_hora_monthly_total_avg).mark_line(point=True).encode(
                    x=alt.X('Mes', title='Mes'),
                    y=alt.Y('Valor Promedio Total por Hora ($)', title='Valor Promedio Total por Hora ($)', axis=alt.Axis(format='$,.2f')),
                    tooltip=['Mes', alt.Tooltip('Valor Promedio Total por Hora ($)', format='$,.2f')]
                ).properties(
                    title='Tendencia Mensual del Valor Promedio Total por Hora'
                ).interactive()
                st.altair_chart(chart_total_avg_valor_hora, use_container_width=True)


                st.markdown('---')
                st.subheader(f'Valores Promedio por Hora (Desglose por {selected_grouping_dimension})')

                # Gráfico de barras para el desglose por la dimensión seleccionada
                # Muestra el valor promedio de cada tipo de hora (Hora Normal, HE 50%, etc.) por la dimensión seleccionada.
                # Para visualizar esto bien, es mejor usar df_valor_hora_melted.
                # Creamos un gráfico de barras para cada "Tipo de Hora" en columnas separadas o apiladas.
                # Para un gráfico que muestre la contribución de cada tipo de hora por dimensión:

                # Primero, sumar los promedios de los diferentes tipos de hora para cada combinación de Mes y Dimensión
                # para tener un valor total por barra en el gráfico principal
                df_valor_hora_for_bar_chart = df_valor_hora_grouped.copy()
                df_valor_hora_for_bar_chart['Total_Valor_Promedio'] = df_valor_hora_for_bar_chart[available_valor_hora_cols].sum(axis=1)

                # Gráfico de barras principales: Dimensión vs. Valor Promedio Total
                chart_valor_hora_dimension_total = alt.Chart(df_valor_hora_for_bar_chart).mark_bar().encode(
                    x=alt.X('Total_Valor_Promedio:Q', title='Valor Promedio Total por Hora ($)', axis=alt.Axis(format='$,.2f')),
                    y=alt.Y(f'{selected_grouping_dimension}:N', sort='-x', title=selected_grouping_dimension),
                    color=alt.Color('Mes', title='Mes'), # Usar Mes como color para diferenciar por mes dentro de cada dimensión
                    tooltip=[
                        selected_grouping_dimension, 'Mes',
                        alt.Tooltip('Total_Valor_Promedio', title='Valor Promedio Total ($)', format='$,.2f')
                    ]
                ).properties(
                    title=f'Valor Promedio Total por Hora por {selected_grouping_dimension} y Mes'
                ).interactive()
                st.altair_chart(chart_valor_hora_dimension_total, use_container_width=True)

                st.markdown('---')
                st.subheader(f'Detalle del Valor Promedio por Tipo de Hora y {selected_grouping_dimension}')

                # Gráfico de barras apiladas para el detalle de cada Tipo de Hora dentro de la dimensión
                # Este gráfico es más informativo para ver la composición del valor por hora.
                chart_valor_hora_detail = alt.Chart(df_valor_hora_melted).mark_bar().encode(
                    x=alt.X('Valor Promedio por Hora ($):Q', title='Valor Promedio por Hora ($)', axis=alt.Axis(format='$,.2f')),
                    y=alt.Y(f'{selected_grouping_dimension}:N', sort='-x', title=selected_grouping_dimension),
                    color=alt.Color('Tipo de Hora:N', title='Tipo de Hora'), # Color por el tipo de hora
                    order=alt.Order('Tipo de Hora:N', sort='ascending'), # Ordenar las pilas
                    tooltip=[
                        selected_grouping_dimension, 'Mes', 'Tipo de Hora',
                        alt.Tooltip('Valor Promedio por Hora ($)', format='$,.2f')
                    ]
                ).properties(
                    title=f'Composición del Valor Promedio por Hora por {selected_grouping_dimension}'
                ).interactive()
                st.altair_chart(chart_valor_hora_detail, use_container_width=True)


                st.markdown('---')
                st.subheader(f'Tabla de Valores Promedio por Hora por Mes y {selected_grouping_dimension}')

                # La tabla debe mostrar las columnas de agrupación y los promedios de valor hora
                cols_for_valor_hora_table = group_cols_for_valor_hora + available_valor_hora_cols

                # Para la fila "Total" en tablas de promedios, un promedio de los promedios agrupados
                # no es matemáticamente correcto. Lo más útil es mostrar el promedio general
                # de cada tipo de hora de todo el DataFrame filtrado (sin la agrupación por mes/dimensión).
                # Reemplazaremos la función add_total_row por una lógica específica aquí para promedios.
                valor_hora_total_row_dict = {dim: 'Total' for dim in group_cols_for_valor_hora}
                for col_val_hora in available_valor_hora_cols:
                    if col_val_hora in filtered_df.columns:
                        valor_hora_total_row_dict[col_val_hora] = filtered_df[col_val_hora].mean()

                # Asegurar que 'Mes' en la fila Total sea 'Total'
                valor_hora_total_row_dict['Mes'] = 'Total'

                total_valor_hora_df_for_display = pd.DataFrame([valor_hora_total_row_dict])

                # Reorganizar columnas para la visualización
                df_valor_hora_table_display = pd.concat([df_valor_hora_grouped[cols_for_valor_hora_table],
                                                         total_valor_hora_df_for_display[cols_for_valor_hora_table]],
                                                         ignore_index=True)


                st.dataframe(format_st_dataframe(df_valor_hora_table_display))
                generate_download_buttons(df_valor_hora_table_display, f'valores_promedio_hora_por_{selected_grouping_dimension}')

# --- PESTAÑA: DATOS BRUTOS (SIN CAMBIOS RELEVANTES AQUÍ) ---
with tab4:
    st.header('Tabla de Datos Brutos Filtrados') # Cambiado el título
    # Reordenar las columnas para mostrar 'Legajo' primero en datos brutos
    if 'Legajo' in filtered_df.columns:
        cols_raw = filtered_df.columns.tolist()
        # Mover 'Legajo' al principio si existe
        if 'Legajo' in cols_raw:
            cols_raw.remove('Legajo')
            filtered_df_display = filtered_df[['Legajo'] + cols_raw]
        else: # Si no existe Legajo después de la remoción (no debería pasar si se comprobó antes), no reorganizar
            filtered_df_display = filtered_df
    else: # Si 'Legajo' no está en el DataFrame original
        filtered_df_display = filtered_df

    st.dataframe(format_st_dataframe(filtered_df_display)) # Mostrar todo el DataFrame filtrado
    generate_download_buttons(filtered_df_display, 'datos_brutos_filtrados') # Añadidos botones de descarga aquí
