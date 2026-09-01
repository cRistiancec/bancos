# -*- coding: utf-8 -*-
"""
Riesgo de Liquidez — indicador LIQ (Fondos Disponibles / Depósitos a Corto
Plazo) de camel.parquet.

Pagina nueva (Fase 1), 100% datos reales. LCR, NSFR y brechas de vencimiento
NO estan disponibles (balance.parquet no tiene dimension de plazo/madurez) --
se declara explicitamente, sin inventar cifras.
"""

import streamlit as st

from ui.layout import render_page, render_modulo_en_preparacion
from services.data_service import cargar_camel, obtener_fechas_disponibles
from analytics.camel_explorer import serie_promedio_sistema
from analytics.camel_scoring import clasificar_semaforo
from components.indicator_panel import render_panel_indicador
from components.semaforo import render_badge_severidad

render_page("Riesgo de Liquidez", icono="💧")

st.title("Riesgo de Liquidez")
st.markdown("Indicador de liquidez inmediata del sistema: Fondos Disponibles / Depósitos a Corto Plazo.")

try:
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

bancos_disponibles = sorted(df_camel['banco'].unique())
fechas = obtener_fechas_disponibles(df_camel)
fecha_sel = st.selectbox("Fecha", options=fechas, format_func=lambda x: x.strftime('%B %Y').title(), index=0)

serie = serie_promedio_sistema(df_camel, 'LIQ')
val = serie['valor_pct'].iloc[-1] if not serie.empty else None

col1, col2 = st.columns([1, 3])
with col1:
    st.metric("Liquidez promedio del sistema", f"{val:.2f}%" if val is not None else "N/D")
    if val is not None:
        st.markdown(render_badge_severidad(clasificar_semaforo(val, 'LIQ')), unsafe_allow_html=True)

st.markdown("---")
render_panel_indicador(df_camel, 'LIQ', "Liquidez (Fondos Disponibles / Depósitos CP)", fecha_sel,
                        bancos_disponibles, key_prefix="liq", colorscale_heatmap='RdYlGn')

st.markdown("---")
render_modulo_en_preparacion(
    "Cobertura de Liquidez (LCR), Fondeo Estable Neto (NSFR) y Brecha de Vencimientos",
    "Estos indicadores requieren un calendario de vencimientos de activos y pasivos por bandas "
    "temporales, que no existe en balance.parquet (solo saldos contables punto-en-tiempo). "
    "Pendiente de una fuente de datos adicional."
)
