# -*- coding: utf-8 -*-
"""
Stress Testing — escenarios hipotéticos de sensibilidad (Fase 2).

Ver analytics/stress_testing.py para la metodología completa y sus límites
explícitos (no es un VaR de mercado; no estima impacto en dólares del
Seguro de Depósitos porque no hay datos de distribución de depositantes).
"""

import streamlit as st
import plotly.graph_objects as go

from ui.layout import render_page
from services.data_service import cargar_camel, obtener_fechas_disponibles
from analytics.stress_testing import ESCENARIOS, aplicar_escenario, resumen_escenario
from components.semaforo import render_badge_severidad
from config.theme_tokens import COLORES

render_page("Stress Testing", icono="🧪")

st.title("Stress Testing")
st.markdown("Sensibilidad de Morosidad, Solvencia y ROA ante escenarios hipotéticos configurables.")
st.warning("**Esto no es un ejercicio de stress testing regulatorio ni un VaR de mercado.** "
           "Es una sensibilidad de balance/resultados sobre los indicadores reales más recientes, con shocks "
           "definidos explícitamente (editables abajo). No estima impacto en dólares del Seguro de Depósitos: "
           "requeriría datos de distribución de depositantes que no existen en el pipeline actual.", icon="⚠️")

try:
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

fechas = obtener_fechas_disponibles(df_camel)
fecha_sel = st.selectbox("Fecha base (valores reales más recientes)", options=fechas,
                          format_func=lambda x: x.strftime('%B %Y').title(), index=0)

escenario_nombre = st.radio("Escenario", options=list(ESCENARIOS.keys()), horizontal=True, index=1)
shock_default = ESCENARIOS[escenario_nombre]

st.markdown("**Ajustar shocks (puntos porcentuales):**")
col1, col2, col3 = st.columns(3)
with col1:
    shock_mor = st.slider("Morosidad (+pp)", min_value=0.0, max_value=15.0, value=shock_default['morosidad_pp'], step=0.5)
with col2:
    shock_sol = st.slider("Solvencia (pp)", min_value=-10.0, max_value=0.0, value=shock_default['solvencia_pp'], step=0.5)
with col3:
    shock_roa = st.slider("ROA (pp)", min_value=-5.0, max_value=0.0, value=shock_default['roa_pp'], step=0.25)

resultado = aplicar_escenario(df_camel, fecha_sel, shock_mor, shock_sol, shock_roa)
resumen = resumen_escenario(resultado)

st.markdown("---")
st.markdown("### Impacto del escenario")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Bancos en CRÍTICO (antes)", resumen['criticos_pre'])
with col2:
    st.metric("Bancos en CRÍTICO (después)", resumen['criticos_post'],
               delta=resumen['criticos_post'] - resumen['criticos_pre'])
with col3:
    st.metric("Bancos en ALERTA (después)", resumen['alerta_post'],
               delta=resumen['alerta_post'] - resumen['alerta_pre'])
with col4:
    st.metric("Bancos que empeoraron de severidad", resumen['empeoraron'])

st.markdown("---")
st.markdown("### Comparación antes / después por banco")

fig = go.Figure()
fig.add_trace(go.Bar(name='Morosidad (antes)', x=resultado['banco'], y=resultado['mor_pre'], marker_color=COLORES['azul_info']))
fig.add_trace(go.Bar(name='Morosidad (después)', x=resultado['banco'], y=resultado['mor_post'], marker_color=COLORES['rojo']))
fig.update_layout(
    title="Morosidad Total — antes vs. después del escenario", barmode='group', height=450,
    yaxis_title="%", xaxis=dict(tickangle=-45), legend=dict(orientation='h', y=1.1, x=0.5, xanchor='center'),
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']),
)
st.plotly_chart(fig, width='stretch')

st.markdown("### Detalle por banco")
detalle = resultado.copy()
for col in ['mor_pre', 'mor_post', 'sol_pre', 'sol_post', 'roa_pre', 'roa_post']:
    detalle[col] = detalle[col].apply(lambda v: f"{v:.2f}%" if v is not None else "N/D")
detalle['Severidad antes'] = detalle['severidad_pre'].apply(render_badge_severidad)
detalle['Severidad después'] = detalle['severidad_post'].apply(render_badge_severidad)

st.markdown(
    detalle[['banco', 'mor_pre', 'mor_post', 'sol_pre', 'sol_post', 'roa_pre', 'roa_post', 'Severidad antes', 'Severidad después']]
    .rename(columns={'banco': 'Banco', 'mor_pre': 'Mora (antes)', 'mor_post': 'Mora (después)',
                      'sol_pre': 'Solv. (antes)', 'sol_post': 'Solv. (después)',
                      'roa_pre': 'ROA (antes)', 'roa_post': 'ROA (después)'})
    .to_html(escape=False, index=False),
    unsafe_allow_html=True
)
