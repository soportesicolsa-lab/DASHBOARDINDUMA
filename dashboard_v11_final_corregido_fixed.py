import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px

# --- Utilidad para máscaras alineadas ---
def _has_col_notna(df: pd.DataFrame, col: str) -> pd.Series:
    """Devuelve una Serie booleana alineada al índice de df.
    True si la columna existe y el valor no es NA; False si no existe.
    """
    if col in df.columns:
        return df[col].notna()
    return pd.Series(False, index=df.index, dtype=bool)



st.set_page_config(page_title="Dashboard de Talento 9-Box", layout="wide")

# --- Cargar y preprocesar datos ---
@st.cache_data
def load_data():
    # CORRECCIÓN: La ruta del archivo Excel debe ser relativa al script en el entorno de despliegue
    excel_file = 'Tactico_9box (1).xlsx'
    df_niveles_medios = pd.read_excel(excel_file, sheet_name='Niveles medios')
    df_jefes = pd.read_excel(excel_file, sheet_name='Jefes')
    df_competencias_jefes = pd.read_excel(excel_file, sheet_name='Competencias Jefes 2025')
    
    # Combinar ambos dataframes para tener todos los empleados
    df_all = pd.concat([df_niveles_medios, df_jefes], ignore_index=True, sort=False)
    
    return df_niveles_medios, df_jefes, df_competencias_jefes, df_all

df_niveles_medios, df_jefes, df_competencias_jefes, df_all = load_data()

# --- Diccionario 9Box ---
box_descriptions = {
    "1": {"titulo": "Cuadrante 1 – TALENTO TOP", "descripcion": "Líder que tiene un desempeño extraordinario y alto potencial. Demuestra constantemente cualidades para desempeñar un rol de mayor responsabilidad dentro de INDUMA. Contagia a los demás, genera pasión y es ejemplo de cultura INDUMA."},
    "2": {"titulo": "Cuadrante 2 – TALENTO EMERGENTE", "descripcion": "Muestra todas las cualidades para ser un líder dentro de INDUMA, es ejemplo de la cultura. Su desempeño es satisfactorio pero no es extraordinario."},
    "3": {"titulo": "Cuadrante 3 – DESEMPEÑO ALTO IMPACTO", "descripcion": "Entrega constantemente resultados de manera extraordinaria. Cuenta con las habilidades para desarrollarse en un rol de mayor liderazgo en INDUMA, pero aún tiene algunas oportunidades que debe desarrollar para poder hacerlo."},
    "4": {"titulo": "Cuadrante 4 – DESEMPEÑO EXTRAORDINARIO", "descripcion": "Entrega resultados extraordinarios, excede las expectativas. Es parte clave en asegurar los objetivos dentro de su área. No muestra cualidades para ocupar una posición de mayor liderazgo en INDUMA."},
    "5": {"titulo": "Cuadrante 5 – TALENTO FUNDAMENTAL", "descripcion": "Entrega resultados satisfactoriamente, muestra potencial para asumir un rol de mayor liderazgo dentro de INDUMA pero aún tiene algunas oportunidades que debe desarrollar para poder hacerlo."},
    "6": {"titulo": "Cuadrante 6 – TALENTO MAL ENFOCADO", "descripcion": "Tiene potencial pero presenta debilidades en su desempeño. Puede que no haya tenido el tiempo suficiente para demostrar lo que puede hacer."},
    "7": {"titulo": "Cuadrante 7 – DESEMPEÑO SATISFACTORIO", "descripcion": "Entrega resultados satisfactoriamente pero no excede la expectativa. No muestra cualidades para ocupar una posición de mayor liderazgo en INDUMA."},
    "8": {"titulo": "Cuadrante 8 – INCONSISTENTE", "descripcion": "Muestra algo de potencial para desarrollarse dentro de INDUMA, pero su desempeño es bajo, no está entregando resultados conforme a las expectativas."},
    "9": {"titulo": "Cuadrante 9 – DESEMPEÑO BAJO", "descripcion": "No entrega resultados conforme a la expectativa y no se adapta a la cultura de INDUMA."}
}

# Mapeo de colores
color_map = {
    1: '#28a745', 2: '#28a745', 3: '#28a745',  # Verde
    4: '#ffc107', 7: '#ffc107',  # Amarillo
    5: '#fd7e14', 6: '#fd7e14',  # Naranja
    8: '#dc3545', 9: '#dc3545'   # Rojo
}

def calcular_cuadrante(potencial, desempeño):
    """Calcula el cuadrante 9-Box basado en potencial y desempeño"""
    if potencial == 3 and desempeño == 3:
        return 1
    elif potencial == 3 and desempeño == 2:
        return 2
    elif potencial == 3 and desempeño == 1:
        return 6
    elif potencial == 2 and desempeño == 3:
        return 3
    elif potencial == 2 and desempeño == 2:
        return 5
    elif potencial == 2 and desempeño == 1:
        return 8
    elif potencial == 1 and desempeño == 3:
        return 4
    elif potencial == 1 and desempeño == 2:
        return 7
    else:  # potencial == 1 and desempeño == 1
        return 9

def obtener_equipo_jefe(nombre_jefe):
    """Obtiene el equipo a cargo de un jefe específico - VERSIÓN CORREGIDA"""
    # CORRECCIÓN: Buscar en AMBAS hojas de manera completa
    
    # 1. Buscar equipo directo en niveles medios
    equipo_directo_nm = df_niveles_medios[df_niveles_medios['JEFE DIRECTO'] == nombre_jefe]
    
    # 2. Buscar equipo directo en jefes
    equipo_directo_j = df_jefes[df_jefes['JEFE DIRECTO'] == nombre_jefe]
    
    # 3. Combinar ambos equipos directos
    equipos_directos = []
    
    if len(equipo_directo_nm) > 0:
        equipos_directos.append(equipo_directo_nm)
    
    if len(equipo_directo_j) > 0:
        equipos_directos.append(equipo_directo_j)
    
    # 4. Si hay equipos directos, combinarlos
    if equipos_directos:
        equipo_completo = pd.concat(equipos_directos, ignore_index=True, sort=False)
        return equipo_completo
    
    # 5. Si no hay equipo directo, retornar DataFrame vacío
    return pd.DataFrame()

def es_jefe(nombre_empleado):
    """Verifica si un empleado es jefe basado en múltiples criterios"""
    # Criterio 1: Está en la hoja de Jefes
    en_hoja_jefes = nombre_empleado in df_jefes['NOMBRE'].values
    
    # Criterio 2: Tiene PROMEDIO EQUIPO en cualquiera de las hojas
    tiene_promedio_equipo = False
    
    # Buscar en niveles medios
    empleado_nm = df_niveles_medios[df_niveles_medios['NOMBRE'] == nombre_empleado]
    if not empleado_nm.empty and pd.notna(empleado_nm.iloc[0].get('PROMEDIO EQUIPO')):
        tiene_promedio_equipo = True
    
    # Buscar en jefes
    empleado_j = df_jefes[df_jefes['NOMBRE'] == nombre_empleado]
    if not empleado_j.empty and pd.notna(empleado_j.iloc[0].get('PROMEDIO EQUIPO')):
        tiene_promedio_equipo = True
    
    # Criterio 3: Aparece como JEFE DIRECTO de alguien
    es_jefe_directo = (nombre_empleado in df_niveles_medios['JEFE DIRECTO'].values) or (nombre_empleado in df_jefes['JEFE DIRECTO'].values)
    
    return en_hoja_jefes or tiene_promedio_equipo or es_jefe_directo

def mostrar_informacion_empleado(empleado_seleccionado):
    """Función para mostrar la información detallada de un empleado"""
    if empleado_seleccionado and empleado_seleccionado != "Seleccione un empleado...":
        # Buscar datos del empleado seleccionado en ambas hojas
        empleado_data_nm = df_niveles_medios[df_niveles_medios['NOMBRE'] == empleado_seleccionado]
        empleado_data_j = df_jefes[df_jefes['NOMBRE'] == empleado_seleccionado]
        
        # Usar el registro que tenga más información
        if not empleado_data_nm.empty:
            empleado = empleado_data_nm.iloc[0]
            fuente_datos = "niveles_medios"
        elif not empleado_data_j.empty:
            empleado = empleado_data_j.iloc[0]
            fuente_datos = "jefes"
        else:
            st.error("No se encontraron datos para este empleado.")
            return
        
        # Información básica
        st.markdown(f"**👤 Nombre:** {empleado['NOMBRE']}")
        st.markdown(f"**💼 Cargo:** {empleado['CARGO']}")
        if pd.notna(empleado.get('JEFE DIRECTO')):
            st.markdown(f"**👨‍💼 Jefe Directo:** {empleado['JEFE DIRECTO']}")
        
        if pd.notna(empleado.get('RESULTADO INDIVIDUAL')):
            st.markdown(f"**📊 Resultado Individual:** {empleado['RESULTADO INDIVIDUAL']:.3f}")
        
        # Verificar si es un jefe usando la función mejorada
        es_jefe_empleado = es_jefe(empleado_seleccionado)
        
        if es_jefe_empleado:
            st.markdown("---")
            st.markdown("**👑 INFORMACIÓN DE JEFE**")
            
            # Buscar promedio de equipo en ambas hojas
            promedio_equipo = None
            if pd.notna(empleado.get('PROMEDIO EQUIPO')):
                promedio_equipo = empleado['PROMEDIO EQUIPO']
            else:
                # Buscar en la otra hoja
                if fuente_datos == "niveles_medios":
                    empleado_otra_hoja = df_jefes[df_jefes['NOMBRE'] == empleado_seleccionado]
                else:
                    empleado_otra_hoja = df_niveles_medios[df_niveles_medios['NOMBRE'] == empleado_seleccionado]
                
                if not empleado_otra_hoja.empty and pd.notna(empleado_otra_hoja.iloc[0].get('PROMEDIO EQUIPO')):
                    promedio_equipo = empleado_otra_hoja.iloc[0]['PROMEDIO EQUIPO']
            
            if promedio_equipo is not None:
                st.markdown(f"**👥 Promedio Equipo:** {promedio_equipo:.3f}")
            
            # Mostrar competencias
            competencias = df_competencias_jefes[
                df_competencias_jefes['Nombre del participante'] == empleado_seleccionado
            ]
            
            if not competencias.empty:
                st.markdown("**🎯 Competencias 2025:**")
                for _, comp in competencias.iterrows():
                    porcentaje = comp['%'] * 100 if comp['%'] <= 1 else comp['%']
                    st.markdown(f"• **{comp['Competencia']}:** {porcentaje:.1f}% (Impacto: {comp['IMPACTO ESPERADO ']:.2f})")
            else:
                st.info("No se encontraron competencias registradas para este jefe.")
            
            # CORRECCIÓN: Mostrar equipo a cargo usando la función corregida
            st.markdown("---")
            st.markdown("**👥 EQUIPO A CARGO**")
            equipo = obtener_equipo_jefe(empleado_seleccionado)
            
            if not equipo.empty:
                st.markdown(f"**Total miembros del equipo:** {len(equipo)}")
                
                # Crear tabla del equipo
                equipo_display = []
                for _, miembro in equipo.iterrows():
                    cuadrante_texto = "Sin evaluación"
                    # CORRECCIÓN: Verificar que las columnas existan antes de acceder
                    if 'Potencial' in miembro.index and 'Desempeño' in miembro.index:
                        if pd.notna(miembro.get('Potencial')) and pd.notna(miembro.get('Desempeño')):
                            cuadrante = calcular_cuadrante(miembro['Potencial'], miembro['Desempeño'])
                            cuadrante_texto = f"Cuadrante {cuadrante}"
                    
                    equipo_display.append({
                        "Nombre": miembro['NOMBRE'],
                        "Cargo": miembro['CARGO'],
                        "Evaluación 9-Box": cuadrante_texto,
                        "Resultado Individual": f"{miembro['RESULTADO INDIVIDUAL']:.3f}" if pd.notna(miembro.get('RESULTADO INDIVIDUAL')) else "N/A"
                    })
                
                # Mostrar tabla
                df_equipo_display = pd.DataFrame(equipo_display)
                st.dataframe(df_equipo_display, use_container_width=True, hide_index=True)
                
                # Estadísticas del equipo - CORRECCIÓN: Verificar que las columnas existan
                st.markdown("**📊 Estadísticas del Equipo:**")
                col_eq1, col_eq2 = st.columns(2)
                
                # Filtrar solo empleados con evaluación válida
                equipo_con_evaluacion = equipo[
                    _has_col_notna(equipo, 'Potencial') & _has_col_notna(equipo, 'Desempeño')
                ]
                
                with col_eq1:
                    if len(equipo_con_evaluacion) > 0 and 'Potencial' in equipo_con_evaluacion.columns:
                        promedio_potencial_equipo = equipo_con_evaluacion['Potencial'].mean()
                        st.metric("Promedio Potencial", f"{promedio_potencial_equipo:.2f}/3")
                
                with col_eq2:
                    if len(equipo_con_evaluacion) > 0 and 'Desempeño' in equipo_con_evaluacion.columns:
                        promedio_desempeño_equipo = equipo_con_evaluacion['Desempeño'].mean()
                        st.metric("Promedio Desempeño", f"{promedio_desempeño_equipo:.2f}/3")
                
                # Distribución por cuadrantes del equipo
                if len(equipo_con_evaluacion) > 0 and 'Potencial' in equipo_con_evaluacion.columns and 'Desempeño' in equipo_con_evaluacion.columns:
                    st.markdown("**📈 Distribución del Equipo por Cuadrantes:**")
                    cuadrante_counts_equipo = {}
                    for _, miembro in equipo_con_evaluacion.iterrows():
                        cuadrante = calcular_cuadrante(miembro['Potencial'], miembro['Desempeño'])
                        cuadrante_counts_equipo[cuadrante] = cuadrante_counts_equipo.get(cuadrante, 0) + 1
                    
                    for cuadrante, count in cuadrante_counts_equipo.items():
                        st.markdown(f"• **{box_descriptions[str(cuadrante)]['titulo']}:** {count} miembro(s)")
            
            else:
                st.info("Este jefe no tiene equipo directo registrado en el sistema.")
        
        # Información de evaluación 9-Box (solo si tiene datos)
        # CORRECCIÓN: Verificar que las columnas existan antes de acceder
        if 'Potencial' in empleado.index and 'Desempeño' in empleado.index:
            if pd.notna(empleado.get('Potencial')) and pd.notna(empleado.get('Desempeño')):
                potencial = int(empleado['Potencial'])
                desempeño = int(empleado['Desempeño'])
                
                cuadrante = calcular_cuadrante(potencial, desempeño)
                
                st.markdown("---")
                st.markdown("**📊 EVALUACIÓN 9-BOX**")
                st.markdown(f"**🎯 Potencial:** {potencial}/3")
                st.markdown(f"**⚡ Desempeño:** {desempeño}/3")
                
                # Mostrar cuadrante con color
                color = color_map[cuadrante]
                st.markdown(f"**📍 {box_descriptions[str(cuadrante)]['titulo']}**")
                st.markdown(f"<div style='background-color:{color}; padding:15px; border-radius:8px; color:white; font-weight:bold; margin:10px 0;'>{box_descriptions[str(cuadrante)]['descripcion']}</div>", unsafe_allow_html=True)
            else:
                if es_jefe_empleado:
                    st.markdown("---")
                    st.info("📝 Este jefe no tiene evaluación 9-Box registrada en el sistema.")
        else:
            if es_jefe_empleado:
                st.markdown("---")
                st.info("📝 Este jefe no tiene evaluación 9-Box registrada en el sistema.")
    else:
        st.info("👆 Seleccione un empleado del menú desplegable para ver sus detalles.")

# --- Título principal ---
st.title("🎯 Dashboard de Talento 9-Box - INDUMA")

# --- Sidebar para navegación jerárquica ---
st.sidebar.title("🔍 Navegación Jerárquica")

# NUEVA FUNCIONALIDAD: Acceso rápido a Mesa Gerencial
st.sidebar.markdown("---")
st.sidebar.markdown("### 👑 Acceso Rápido - Mesa Gerencial")

# Obtener integrantes de Mesa Gerencial
mesa_gerencial = df_all[df_all['ÁREA'] == 'MESA GERENCIAL'].drop_duplicates(subset=['NOMBRE'])

# Crear botones para cada integrante de la Mesa Gerencial
mesa_gerencial_seleccionado = None
for _, integrante in mesa_gerencial.iterrows():
    nombre_completo = integrante['NOMBRE']
    nombre_corto = nombre_completo.split()[0] + " " + nombre_completo.split()[1]
    cargo_corto = integrante['CARGO'].replace('GERENTE', 'GTE').replace('SUBGERENTE', 'SUBGTE')
    
    if st.sidebar.button(f"🎯 {nombre_corto}", key=f"mesa_{nombre_completo}", help=f"{cargo_corto}"):
        mesa_gerencial_seleccionado = nombre_completo

st.sidebar.markdown("---")

# Filtros jerárquicos tradicionales
gerencias_disponibles = sorted(df_all['GERENCIA'].dropna().unique())
gerencia_seleccionada = st.sidebar.selectbox("📊 Seleccione una Gerencia", gerencias_disponibles)

# Filtrar áreas por gerencia seleccionada
areas_disponibles = sorted(df_all[df_all['GERENCIA'] == gerencia_seleccionada]['ÁREA'].dropna().unique())
area_seleccionada = st.sidebar.selectbox("🏢 Seleccione un Área", areas_disponibles)

# Filtrar empleados por gerencia y área
empleados_filtrados = df_all[
    (df_all['GERENCIA'] == gerencia_seleccionada) & 
    (df_all['ÁREA'] == area_seleccionada)
].drop_duplicates(subset=['NOMBRE'])  # Eliminar duplicados por nombre

# Separar empleados con y sin datos de evaluación 9-Box
# CORRECCIÓN: Verificar que las columnas existan antes de filtrar
empleados_con_evaluacion = empleados_filtrados[
    _has_col_notna(empleados_filtrados, 'Potencial') & _has_col_notna(empleados_filtrados, 'Desempeño')
]

empleados_sin_evaluacion = empleados_filtrados[
    empleados_filtrados.get('Potencial', pd.Series()).isna() | 
    empleados_filtrados.get('Desempeño', pd.Series()).isna()
]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Total empleados en {area_seleccionada}:** {len(empleados_filtrados)}")
st.sidebar.markdown(f"**Con evaluación 9-Box:** {len(empleados_con_evaluacion)}")
st.sidebar.markdown(f"**Jefes sin evaluación:** {len(empleados_sin_evaluacion)}")

# --- Layout principal ---
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📈 Matriz 9-Box Interactiva")
    
    if len(empleados_con_evaluacion) > 0:
        # Crear la matriz 9-Box con Plotly
        fig = go.Figure()
        
        # Agregar puntos para cada empleado con evaluación
        for _, empleado in empleados_con_evaluacion.iterrows():
            potencial = empleado['Potencial']
            desempeño = empleado['Desempeño']
            nombre = empleado['NOMBRE']
            
            cuadrante = calcular_cuadrante(potencial, desempeño)
            
            fig.add_trace(go.Scatter(
                x=[desempeño],
                y=[potencial],
                mode='markers+text',
                text=[nombre.split()[0]],  # Solo primer nombre
                textposition="middle center",
                marker=dict(
                    size=25,
                    color=color_map[cuadrante],
                    line=dict(width=2, color='white'),
                    opacity=0.8
                ),
                name=nombre,
                hovertemplate=f"<b>{nombre}</b><br>" +
                             f"Desempeño: {desempeño}<br>" +
                             f"Potencial: {potencial}<br>" +
                             f"Haga clic para ver detalles<br>" +
                             "<extra></extra>",
                customdata=[nombre]
            ))
        
        # Configurar el layout de la matriz
        fig.update_layout(
            title="Matriz 9-Box por Desempeño vs Potencial",
            xaxis=dict(
                title="Desempeño",
                tickmode='array',
                tickvals=[1, 2, 3],
                ticktext=['Bajo (1)', 'Medio (2)', 'Alto (3)'],
                range=[0.5, 3.5],
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title="Potencial",
                tickmode='array',
                tickvals=[1, 2, 3],
                ticktext=['Bajo (1)', 'Medio (2)', 'Alto (3)'],
                range=[0.5, 3.5],
                gridcolor='lightgray'
            ),
            showlegend=False,
            height=500,
            plot_bgcolor='rgba(248,249,250,1)',
            font=dict(size=12)
        )
        
        # Agregar líneas de cuadrícula para separar cuadrantes
        for i in [1.5, 2.5]:
            fig.add_hline(y=i, line_dash="dash", line_color="gray", opacity=0.7, line_width=2)
            fig.add_vline(x=i, line_dash="dash", line_color="gray", opacity=0.7, line_width=2)
        
        # Agregar etiquetas de cuadrantes (solo números)
        cuadrante_positions = {
            (1, 3): "6", (2, 3): "2", (3, 3): "1",
            (1, 2): "8", (2, 2): "5", (3, 2): "3",
            (1, 1): "9", (2, 1): "7", (3, 1): "4"
        }
        
        for (x, y), label in cuadrante_positions.items():
            fig.add_annotation(
                x=x, y=y,
                text=f"<b>{label}</b>",
                showarrow=False,
                font=dict(size=16, color="gray"),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="gray",
                borderwidth=1,
                xshift=40,
                yshift=40
            )
        
        # Mostrar el gráfico
        selected_points = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
        
    else:
        st.warning("No hay empleados con datos de evaluación 9-Box en esta área.")
    
    # Selector de empleado (incluyendo TODOS los empleados filtrados)
    st.subheader("👤 Seleccionar Empleado")
    
    # CORRECCIÓN: Asegurar que todos los empleados filtrados aparezcan en el dropdown
    todos_empleados = sorted(empleados_filtrados['NOMBRE'].unique().tolist())
    
    # Debug: Mostrar cuántos empleados hay
    st.caption(f"Total empleados disponibles: {len(todos_empleados)}")
    
    empleado_seleccionado = st.selectbox(
        "Elija un empleado para ver detalles:",
        ["Seleccione un empleado..."] + todos_empleados,
        key="empleado_selector"
    )

with col2:
    st.header("📋 Detalles del Evaluado")
    
    # Si se seleccionó alguien de la Mesa Gerencial, mostrar su información
    if mesa_gerencial_seleccionado:
        mostrar_informacion_empleado(mesa_gerencial_seleccionado)
    else:
        mostrar_informacion_empleado(empleado_seleccionado)

# --- Información adicional sobre jefes sin evaluación ---
if len(empleados_sin_evaluacion) > 0:
    st.markdown("---")
    st.header("👑 Jefes en esta Área")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Lista de Jefes")
        for _, jefe in empleados_sin_evaluacion.iterrows():
            if es_jefe(jefe['NOMBRE']):
                st.markdown(f"• **{jefe['NOMBRE']}** - {jefe['CARGO']}")
    
    with col2:
        st.subheader("📊 Estadísticas de Jefes")
        jefes_con_promedio = empleados_sin_evaluacion[empleados_sin_evaluacion.apply(lambda x: es_jefe(x['NOMBRE']), axis=1)]
        if len(jefes_con_promedio) > 0:
            # Calcular promedio de equipos
            promedios_equipos = []
            for _, jefe in jefes_con_promedio.iterrows():
                if pd.notna(jefe.get('PROMEDIO EQUIPO')):
                    promedios_equipos.append(jefe['PROMEDIO EQUIPO'])
                else:
                    # Buscar en la otra hoja
                    jefe_otra_hoja = df_jefes[df_jefes['NOMBRE'] == jefe['NOMBRE']]
                    if not jefe_otra_hoja.empty and pd.notna(jefe_otra_hoja.iloc[0].get('PROMEDIO EQUIPO')):
                        promedios_equipos.append(jefe_otra_hoja.iloc[0]['PROMEDIO EQUIPO'])
            
            if promedios_equipos:
                promedio_equipos = sum(promedios_equipos) / len(promedios_equipos)
                st.metric("Promedio de Equipos", f"{promedio_equipos:.3f}")
            
            # Mostrar jefes con competencias
            jefes_con_competencias = df_competencias_jefes[
                df_competencias_jefes['Nombre del participante'].isin(empleados_sin_evaluacion['NOMBRE'])
            ]['Nombre del participante'].nunique()
            st.metric("Jefes con Competencias", jefes_con_competencias)

# --- Resumen estadístico ---
st.markdown("---")
st.header("📊 Resumen Estadístico")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Empleados", len(empleados_filtrados))

with col2:
    if len(empleados_con_evaluacion) > 0 and 'Potencial' in empleados_con_evaluacion.columns:
        promedio_potencial = empleados_con_evaluacion['Potencial'].mean()
        st.metric("Promedio Potencial", f"{promedio_potencial:.2f}/3")

with col3:
    if len(empleados_con_evaluacion) > 0 and 'Desempeño' in empleados_con_evaluacion.columns:
        promedio_desempeño = empleados_con_evaluacion['Desempeño'].mean()
        st.metric("Promedio Desempeño", f"{promedio_desempeño:.2f}/3")

# Distribución por cuadrantes
if len(empleados_con_evaluacion) > 0 and 'Potencial' in empleados_con_evaluacion.columns and 'Desempeño' in empleados_con_evaluacion.columns:
    st.subheader("📈 Distribución por Cuadrantes")
    
    # Calcular distribución
    cuadrante_counts = {}
    for _, empleado in empleados_con_evaluacion.iterrows():
        potencial = empleado['Potencial']
        desempeño = empleado['Desempeño']
        cuadrante = calcular_cuadrante(potencial, desempeño)
        cuadrante_counts[cuadrante] = cuadrante_counts.get(cuadrante, 0) + 1
    
    # Crear gráfico de barras
    if cuadrante_counts:
        cuadrantes = list(cuadrante_counts.keys())
        counts = list(cuadrante_counts.values())
        labels = [f"{box_descriptions[str(c)]['titulo']}" for c in cuadrantes]
        colors = [color_map[c] for c in cuadrantes]
        
        fig_bar = go.Figure(data=[
            go.Bar(x=labels, y=counts, marker_color=colors, text=counts, textposition='auto')
        ])
        
        fig_bar.update_layout(
            title="Distribución de Empleados por Cuadrante 9-Box",
            xaxis_title="Cuadrante",
            yaxis_title="Número de Empleados",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

