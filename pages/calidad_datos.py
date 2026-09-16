# -*- coding: utf-8 -*-
"""
Calidad de Datos — validacion y transparencia sobre los datos antes del
analisis.

Revivido desde archived_pages/0_Calidad_old.py (Fase 1 del refactor
institucional). Fue archivado por simplicidad de navegacion, no por estar
roto -- ver CHANGELOG.md. Se corrige un bug latente en
validar_ecuacion_contable() (filtraba por una columna 'hoja' inexistente en
balance.parquet, ver utils/data_quality.py) y se adapta al tema institucional.
"""

import streamlit as st

from ui.layout import render_page
from services.data_service import cargar_balance, cargar_pyg, cargar_camel, obtener_fechas_disponibles
from utils.data_quality import (
    validar_cobertura_bancos, calcular_cobertura_por_fecha,
    detectar_bancos_faltantes, validar_ecuacion_contable,
    generar_resumen_calidad, exportar_reporte_calidad,
)
from config.indicator_mapping import BANCOS_SISTEMA
from components.semaforo import render_badge_severidad
from charts.builders import crear_heatmap

render_page("Calidad de Datos", icono="🔍")

ESTADO_A_SEVERIDAD = {'OK': 'OK', 'ADVERTENCIA': 'ALERTA', 'REVISAR': 'CRITICO', 'ERROR': 'CRITICO'}

st.title("Calidad de Datos")
st.markdown("Validación y transparencia sobre los datos antes del análisis.")

with st.spinner("Cargando y validando datos..."):
    datos = {'dataframes': {}, 'calidad': {}, 'errores': []}

    try:
        df_balance, cal_balance = cargar_balance()
        datos['dataframes']['balance'] = df_balance
        datos['calidad']['balance'] = cal_balance
    except Exception as e:
        datos['errores'].append(f"balance: {str(e)}")

    try:
        df_pyg, cal_pyg = cargar_pyg()
        datos['dataframes']['pyg'] = df_pyg
        datos['calidad']['pyg'] = cal_pyg
    except Exception as e:
        datos['errores'].append(f"pyg: {str(e)}")

    try:
        df_camel, cal_camel = cargar_camel()
        datos['dataframes']['camel'] = df_camel
        datos['calidad']['camel'] = cal_camel
    except Exception as e:
        datos['errores'].append(f"camel: {str(e)}")

if datos.get('errores'):
    for error in datos['errores']:
        st.warning(f"Advertencia: {error}")

if not datos['dataframes']:
    st.error("No se pudieron cargar los datos.")
    st.info("Asegúrate de haber ejecutado los scripts de procesamiento (procesar_balance.py, procesar_pyg.py, procesar_camel.py)")
    st.stop()

resumen = generar_resumen_calidad(datos)

# --- RESUMEN EJECUTIVO ---
st.markdown("### Resumen Ejecutivo")
st.markdown(render_badge_severidad(ESTADO_A_SEVERIDAD.get(resumen['estado_general'], 'SIN_DATO'),
                                    f"Estado general: {resumen['estado_general']}"), unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
completitud = resumen['metricas'].get('completitud', {})
cal_balance = datos['calidad'].get('balance', {})

with col1:
    st.metric("Completitud de Datos", f"{completitud.get('pct_completitud', 0)}%")
with col2:
    bancos = cal_balance.get('bancos', 0)
    st.metric("Bancos Activos", f"{bancos}/{len(BANCOS_SISTEMA)}")
with col3:
    st.metric("Meses de Datos", f"{cal_balance.get('fechas', 0)}")
with col4:
    st.metric("Alertas Activas", len(resumen.get('alertas', [])))

# --- ALERTAS ---
st.markdown("### Alertas")
if resumen.get('alertas'):
    for alerta in resumen['alertas']:
        st.warning(alerta)
else:
    st.success("No hay alertas. Los datos están en buen estado.")

st.markdown("---")

# --- COBERTURA TEMPORAL ---
st.markdown("### Cobertura de Bancos por Año")

if 'balance' in datos['dataframes']:
    df_balance = datos['dataframes']['balance']
    cobertura = validar_cobertura_bancos(df_balance)
    anos_recientes = sorted(cobertura.columns)[-15:]
    cobertura_reciente = cobertura[anos_recientes]

    st.plotly_chart(crear_heatmap(cobertura_reciente, color_scale='Greens', altura=600, mostrar_valores=False),
                     width='stretch')

    bancos_faltantes = detectar_bancos_faltantes(df_balance)
    if bancos_faltantes:
        st.warning(f"**Bancos no encontrados en los datos:** {', '.join(bancos_faltantes)}")

    cobertura_por_fecha = calcular_cobertura_por_fecha(df_balance)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Cobertura por año (promedio de bancos)**")
        cob_anual = cobertura_por_fecha.groupby('ano')['bancos_con_datos'].mean().round(1)
        st.bar_chart(cob_anual)
    with col2:
        st.markdown("**Meses con menor cobertura**")
        peor_cobertura = cobertura_por_fecha.nsmallest(10, 'bancos_con_datos').copy()
        peor_cobertura['fecha_str'] = peor_cobertura['fecha'].dt.strftime('%Y-%m')
        st.dataframe(
            peor_cobertura[['fecha_str', 'bancos_con_datos']].rename(columns={'fecha_str': 'Fecha', 'bancos_con_datos': 'Bancos'}),
            hide_index=True, width='stretch'
        )

st.markdown("---")

# --- VALIDACION CAMEL ---
st.markdown("### Calidad de Datos — Indicadores CAMEL")
if 'camel' in datos['dataframes']:
    cal_camel = datos['calidad'].get('camel', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Indicadores Únicos", cal_camel.get('indicadores_unicos', 'N/A'))
    with col2:
        st.metric("Registros Procesados", f"{cal_camel.get('registros_limpios', 0):,}")
    with col3:
        st.metric("Categorías CAMEL", len(cal_camel.get('categorias', [])))
    if cal_camel.get('categorias'):
        st.markdown("**Categorías procesadas**: " + ", ".join(cal_camel['categorias']))
else:
    st.warning("Datos CAMEL no disponibles")

st.markdown("---")

# --- VALIDACION CONTABLE ---
st.markdown("### Validación de Ecuación Contable")
st.markdown("Verifica que **Activo = Pasivo + Patrimonio** para cada banco.")

if 'balance' in datos['dataframes']:
    df_balance = datos['dataframes']['balance']
    fechas = obtener_fechas_disponibles(df_balance)
    fecha_validar = st.selectbox("Selecciona fecha a validar", options=fechas[:24],
                                  format_func=lambda x: x.strftime('%B %Y'), index=0)

    validacion = validar_ecuacion_contable(df_balance, fecha=fecha_validar)

    bancos_ok = len(validacion[validacion['estado'] == 'OK'])
    bancos_warn = len(validacion[validacion['estado'] == 'Advertencia'])
    bancos_error = len(validacion[validacion['estado'] == 'Error'])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bancos OK", bancos_ok)
    with col2:
        st.metric("Advertencias", bancos_warn)
    with col3:
        st.metric("Errores", bancos_error)

    validacion_display = validacion.copy()
    validacion_display['activo'] = validacion_display['activo'].apply(lambda x: f"${x/1000:,.0f}M")
    validacion_display['pasivo_patrimonio'] = validacion_display['pasivo_patrimonio'].apply(lambda x: f"${x/1000:,.0f}M")
    validacion_display['diferencia'] = validacion_display['diferencia'].apply(lambda x: f"${x/1000:,.2f}M")

    def highlight_estado(row):
        color = {'OK': 'background-color: rgba(27,138,90,0.25)',
                 'Advertencia': 'background-color: rgba(232,135,30,0.25)',
                 'Error': 'background-color: rgba(193,39,45,0.30)'}.get(row['estado'], '')
        return [color] * len(row)

    st.dataframe(
        validacion_display[['banco', 'activo', 'pasivo_patrimonio', 'diferencia', 'pct_diferencia', 'estado']]
        .style.apply(highlight_estado, axis=1),
        hide_index=True, width='stretch'
    )

st.markdown("---")

# --- EXPORTAR ---
st.markdown("### Exportar Reporte de Calidad")
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("📥 Generar Reporte Excel", type="primary"):
        with st.spinner("Generando reporte..."):
            excel_buffer = exportar_reporte_calidad(datos)
            st.download_button(
                label="⬇️ Descargar Reporte", data=excel_buffer, file_name="reporte_calidad_datos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
with col2:
    st.markdown("""
    El reporte incluye:
    - Resumen ejecutivo de calidad
    - Lista de alertas activas
    - Matriz de cobertura bancos x años
    - Validación contable por banco
    """)
