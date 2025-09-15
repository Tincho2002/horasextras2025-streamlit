with tab2:
    if filtered_df.empty: st.warning("No hay datos para mostrar.")
    else:
        with st.spinner("Generando desgloses organizacionales..."):
            # Gerencia y Ministerio
            with st.container(border=True):
                df_grouped_gm = calculate_grouped_aggregation(filtered_df, ['Gerencia', 'Ministerio'], cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                if not df_grouped_gm.empty:
                    total_gm = df_grouped_gm.sum(numeric_only=True).to_frame().T
                    total_gm['Gerencia'] = 'TOTAL'
                    total_gm['Ministerio'] = ''
                    df_grouped_gm = pd.concat([df_grouped_gm, total_gm], ignore_index=True)
                
                st.header('Distribución por Gerencia y Ministerio')
                col1, col2 = st.columns(2)
                chart_data_gm = df_grouped_gm[df_grouped_gm['Gerencia'] != 'TOTAL']
                with col1:
                    chart_costos_gm = alt.Chart(chart_data_gm).mark_bar().encode(x='Total_Costos', y=alt.Y('Gerencia:N', sort='-x'), color=alt.Color('Ministerio', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Costos por Gerencia y Ministerio', anchor='middle'))
                    st.altair_chart(chart_costos_gm, use_container_width=True)
                with col2:
                    chart_cantidades_gm = alt.Chart(chart_data_gm).mark_bar().encode(x='Total_Cantidades', y=alt.Y('Gerencia:N', sort='-x'), color=alt.Color('Ministerio', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Cantidades por Gerencia y Ministerio', anchor='middle'))
                    st.altair_chart(chart_cantidades_gm, use_container_width=True)
                st.subheader('Tabla de Distribución')
                st.dataframe(format_st_dataframe(df_grouped_gm), use_container_width=True)
                generate_download_buttons(df_grouped_gm, 'distribucion_gerencia_ministerio')

            # Gerencia y Sexo
            with st.container(border=True):
                df_grouped_gs = calculate_grouped_aggregation(filtered_df, ['Gerencia', 'Sexo'], cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                if not df_grouped_gs.empty:
                    total_gs = df_grouped_gs.sum(numeric_only=True).to_frame().T
                    total_gs['Gerencia'] = 'TOTAL'
                    total_gs['Sexo'] = ''
                    df_grouped_gs = pd.concat([df_grouped_gs, total_gs], ignore_index=True)

                st.header('Distribución por Gerencia y Sexo')
                col1, col2 = st.columns(2)
                chart_data_gs = df_grouped_gs[df_grouped_gs['Gerencia'] != 'TOTAL']
                with col1:
                    chart_costos_gs = alt.Chart(chart_data_gs).mark_bar().encode(x='Total_Costos', y=alt.Y('Gerencia:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Costos por Gerencia y Sexo', anchor='middle')).interactive()
                    st.altair_chart(chart_costos_gs, use_container_width=True)
                with col2:
                    chart_cantidades_gs = alt.Chart(chart_data_gs).mark_bar().encode(x='Total_Cantidades', y=alt.Y('Gerencia:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Cantidades por Gerencia y Sexo', anchor='middle')).interactive()
                    st.altair_chart(chart_cantidades_gs, use_container_width=True)
                st.subheader('Tabla de Distribución')
                st.dataframe(format_st_dataframe(df_grouped_gs), use_container_width=True)
                generate_download_buttons(df_grouped_gs, 'distribucion_gerencia_sexo')

            # Ministerio y Sexo
            with st.container(border=True):
                df_grouped_ms = calculate_grouped_aggregation(filtered_df, ['Ministerio', 'Sexo'], cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                if not df_grouped_ms.empty:
                    total_ms = df_grouped_ms.sum(numeric_only=True).to_frame().T
                    total_ms['Ministerio'] = 'TOTAL'
                    total_ms['Sexo'] = ''
                    df_grouped_ms = pd.concat([df_grouped_ms, total_ms], ignore_index=True)

                st.header('Distribución por Ministerio y Sexo')
                col1, col2 = st.columns(2)
                chart_data_ms = df_grouped_ms[df_grouped_ms['Ministerio'] != 'TOTAL']
                with col1:
                    chart_costos_ms = alt.Chart(chart_data_ms).mark_bar().encode(x='Total_Costos', y=alt.Y('Ministerio:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Costos por Ministerio y Sexo', anchor='middle')).interactive()
                    st.altair_chart(chart_costos_ms, use_container_width=True)
                with col2:
                    chart_cantidades_ms = alt.Chart(chart_data_ms).mark_bar().encode(x='Total_Cantidades', y=alt.Y('Ministerio:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Cantidades por Ministerio y Sexo', anchor='middle')).interactive()
                    st.altair_chart(chart_cantidades_ms, use_container_width=True)
                st.subheader('Tabla de Distribución')
                st.dataframe(format_st_dataframe(df_grouped_ms), use_container_width=True)
                generate_download_buttons(df_grouped_ms, 'distribucion_ministerio_sexo')

            # Nivel y Sexo
            with st.container(border=True):
                df_grouped_ns = calculate_grouped_aggregation(filtered_df, ['Nivel', 'Sexo'], cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                if not df_grouped_ns.empty:
                    total_ns = df_grouped_ns.sum(numeric_only=True).to_frame().T
                    total_ns['Nivel'] = 'TOTAL'
                    total_ns['Sexo'] = ''
                    df_grouped_ns = pd.concat([df_grouped_ns, total_ns], ignore_index=True)

                st.header('Distribución por Nivel y Sexo')
                col1, col2 = st.columns(2)
                chart_data_ns = df_grouped_ns[df_grouped_ns['Nivel'] != 'TOTAL']
                with col1:
                    chart_costos_ns = alt.Chart(chart_data_ns).mark_bar().encode(x='Total_Costos', y=alt.Y('Nivel:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Costos por Nivel y Sexo', anchor='middle')).interactive()
                    st.altair_chart(chart_costos_ns, use_container_width=True)
                with col2:
                    chart_cantidades_ns = alt.Chart(chart_data_ns).mark_bar().encode(x='Total_Cantidades', y=alt.Y('Nivel:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Cantidades por Nivel y Sexo', anchor='middle')).interactive()
                    st.altair_chart(chart_cantidades_ns, use_container_width=True)
                st.subheader('Tabla de Distribución')
                st.dataframe(format_st_dataframe(df_grouped_ns), use_container_width=True)
                generate_download_buttons(df_grouped_ns, 'distribucion_nivel_sexo')

            # Función y Sexo
            with st.container(border=True):
                df_grouped_fs = calculate_grouped_aggregation(filtered_df, ['Función', 'Sexo'], cost_columns_options, quantity_columns_options, selected_cost_types_display, selected_quantity_types_display)
                if not df_grouped_fs.empty:
                    total_fs = df_grouped_fs.sum(numeric_only=True).to_frame().T
                    total_fs['Función'] = 'TOTAL'
                    total_fs['Sexo'] = ''
                    df_grouped_fs = pd.concat([df_grouped_fs, total_fs], ignore_index=True)

                st.header('Distribución por Función y Sexo')
                col1, col2 = st.columns(2)
                chart_data_fs = df_grouped_fs[df_grouped_fs['Función'] != 'TOTAL']
                with col1:
                    chart_costos_fs = alt.Chart(chart_data_fs).mark_bar().encode(x='Total_Costos', y=alt.Y('Función:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Costos por Función y Sexo', anchor='middle')).interactive()
                    st.altair_chart(chart_costos_fs, use_container_width=True)
                with col2:
                    chart_cantidades_fs = alt.Chart(chart_data_fs).mark_bar().encode(x='Total_Cantidades', y=alt.Y('Función:N', sort='-x'), color=alt.Color('Sexo', legend=alt.Legend(orient='bottom', title=None, columns=2, labelLimit=300))).properties(title=alt.TitleParams('Cantidades por Función y Sexo', anchor='middle')).interactive()
                    st.altair_chart(chart_cantidades_fs, use_container_width=True)
                st.subheader('Tabla de Distribución')
                st.dataframe(format_st_dataframe(df_grouped_fs), use_container_width=True)
                generate_download_buttons(df_grouped_fs, 'distribucion_funcion_sexo')
