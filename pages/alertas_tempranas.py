# -*- coding: utf-8 -*-
"""
Alertas Tempranas — motor de reglas sobre los umbrales alerta/critico ya
definidos en config.indicator_mapping.RANGOS_INDICADORES.

Pagina nueva (Fase 1), 100% datos reales y reglas explicitas (no modelos
predictivos). Ver analytics/early_warning.py.
"""

import streamlit as st

from ui.layout import render_page
from services.data_service import cargar_camel, obtener_fechas_disponibles
from analytics.early_warning import generar_alertas, resumen_alertas
from components.semaforo import render_badge_severidad

render_page("Alertas Tempranas", icono="🚨")

st.title("Alertas Tempranas")
st.markdown("Bancos e indicadores que cruzan los umbrales de alerta/crítico definidos para el sistema.")

try:
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

fechas = obtener_fechas_disponibles(df_camel)
usar_fecha_especifica = st.checkbox("Usar una fecha específica (por defecto: última fecha disponible por indicador)", value=False)
fecha_sel = None
if usar_fecha_especifica:
    fecha_sel = st.selectbox("Fecha", options=fechas, format_func=lambda x: x.strftime('%B %Y').title(), index=0)

df_alertas = generar_alertas(df_camel, fecha=fecha_sel)
resumen = resumen_alertas(df_alertas)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de alertas", resumen['total'])
with col2:
    st.metric("Críticas", resumen['criticas'])
with col3:
    st.metric("En alerta", resumen['alertas'])
with col4:
    st.metric("Bancos afectados", resumen['bancos_afectados'])

st.markdown("---")

if df_alertas.empty:
    st.success("No hay bancos fuera de los umbrales definidos en este momento.")
else:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        bancos_filtro = st.multiselect("Filtrar por banco", options=sorted(df_alertas['banco'].unique()))
    with col_f2:
        severidad_filtro = st.multiselect("Filtrar por severidad", options=['CRITICO', 'ALERTA'], default=['CRITICO', 'ALERTA'])

    df_mostrar = df_alertas.copy()
    if bancos_filtro:
        df_mostrar = df_mostrar[df_mostrar['banco'].isin(bancos_filtro)]
    if severidad_filtro:
        df_mostrar = df_mostrar[df_mostrar['severidad'].isin(severidad_filtro)]

    df_mostrar_display = df_mostrar.copy()
    df_mostrar_display['Severidad'] = df_mostrar_display['severidad'].apply(lambda s: render_badge_severidad(s))
    df_mostrar_display['Valor'] = df_mostrar_display['valor_pct'].apply(lambda v: f"{v:.2f}%")
    df_mostrar_display['Fecha'] = df_mostrar_display['fecha'].dt.strftime('%B %Y')

    st.markdown(
        df_mostrar_display[['banco', 'indicador', 'Valor', 'Fecha', 'Severidad']]
        .rename(columns={'banco': 'Banco', 'indicador': 'Indicador'})
        .to_html(escape=False, index=False),
        unsafe_allow_html=True
    )
