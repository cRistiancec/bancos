# -*- coding: utf-8 -*-
"""
Calificación de Riesgo Consolidada (Fase 3) — rating A-E por banco.

Ver analytics/risk_rating.py para la metodología completa (por qué es un
compuesto de 2 factores, no 3) y docs/ManualTecnico.md.
"""

import streamlit as st

from ui.layout import render_page
from services.data_service import cargar_camel, obtener_fechas_disponibles
from analytics.risk_rating import calcular_calificaciones_sistema, PESO_CAMEL, PESO_RESILIENCIA, ESCENARIO_RESILIENCIA
from config.theme_tokens import COLORES

render_page("Calificación de Riesgo", icono="🏅")

st.title("Calificación de Riesgo Consolidada")
st.markdown(f"Rating **A–E** por banco: `{PESO_CAMEL:.0%}` salud actual (score CAMEL) + "
            f"`{PESO_RESILIENCIA:.0%}` resiliencia ante el escenario de estrés **{ESCENARIO_RESILIENCIA}**.")
st.warning("**Metodología interna, no una calificación crediticia oficial ni regulatoria.** "
           "Deliberadamente NO incluye la contribución al Índice Sistémico (esa mide el impacto en el sistema "
           "si el banco cae, no la salud del banco — ver página **Riesgo Sistémico** para esa métrica por separado).",
           icon="🏅")

try:
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

fechas = obtener_fechas_disponibles(df_camel)
fecha_sel = st.selectbox("Fecha", options=fechas, format_func=lambda x: x.strftime('%B %Y').title(), index=0)

calificaciones = calcular_calificaciones_sistema(df_camel, fecha_sel)

if calificaciones.empty:
    st.warning("No hay datos suficientes para calcular calificaciones en esta fecha.")
    st.stop()

COLOR_CALIFICACION = {
    'A': COLORES['verde'], 'B': COLORES['verde'],
    'C': COLORES['naranja'], 'D': COLORES['naranja'],
    'E': COLORES['rojo'],
}

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Mejor calificación", f"{calificaciones.iloc[0]['banco']} ({calificaciones.iloc[0]['calificacion']})")
with col2:
    st.metric("Bancos en D o E", len(calificaciones[calificaciones['calificacion'].isin(['D', 'E'])]))
with col3:
    st.metric("Bancos calificados", len(calificaciones))

st.markdown("---")
st.markdown("### Ranking de calificaciones")

tabla = calificaciones.copy()
tabla['Calificación'] = tabla['calificacion'].apply(
    lambda letra: f'<span class="sfp-badge" style="color:{COLOR_CALIFICACION[letra]}; border-color:{COLOR_CALIFICACION[letra]};">{letra}</span>'
)
tabla['Score Final'] = tabla['score_final'].apply(lambda v: f"{v:.1f}")
tabla['Score CAMEL'] = tabla['score_camel'].apply(lambda v: f"{v:.1f}")
tabla['Score Resiliencia'] = tabla['score_resiliencia'].apply(lambda v: f"{v:.1f}")

st.markdown(
    tabla[['banco', 'Calificación', 'Score Final', 'Score CAMEL', 'Score Resiliencia']]
    .rename(columns={'banco': 'Banco'})
    .to_html(escape=False, index=False),
    unsafe_allow_html=True
)

st.caption("Bandas: A ≥80 · B ≥60 · C ≥40 · D ≥20 · E <20 (sobre el score final 0-100).")
