# -*- coding: utf-8 -*-
"""
Riesgo de Concentración — HHI, CR5, CR10 de activos y depósitos, y
participación de cartera por segmento (PART_*).

Pagina nueva (Fase 1), 100% datos reales. HHI reactiva
analytics.concentracion.calcular_hhi (migrado desde 1_Panorama.py, donde
estaba definido pero nunca visualizado). Concentración por depositante NO
esta disponible (no hay datos a nivel de depositante individual).
"""

import streamlit as st

from ui.layout import render_page, render_modulo_en_preparacion
from services.data_service import cargar_balance, cargar_camel, obtener_fechas_disponibles
from analytics.concentracion import calcular_participacion_mercado, calcular_hhi, calcular_cr_n, clasificar_hhi
from analytics.camel_explorer import obtener_ranking
from charts.builders import crear_ranking_barras
from config.indicator_mapping import CODIGOS_BALANCE, ETIQUETAS_INDICADORES

render_page("Riesgo de Concentración", icono="🧩")

st.title("Riesgo de Concentración")
st.markdown("Índice Herfindahl-Hirschman (HHI) y ratios de concentración CR5/CR10 del sistema bancario.")

try:
    df_balance, _ = cargar_balance()
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

fechas = obtener_fechas_disponibles(df_balance)
fecha_sel = st.selectbox("Fecha", options=fechas, format_func=lambda x: x.strftime('%B %Y').title(), index=0)

CUENTAS_CONCENTRACION = {
    'Activos Totales': CODIGOS_BALANCE['activo_total'],
    'Cartera de Créditos': CODIGOS_BALANCE['cartera_creditos'],
    'Depósitos del Público': CODIGOS_BALANCE['obligaciones_publico'],
}

cuenta_label = st.radio("Variable de concentración", options=list(CUENTAS_CONCENTRACION.keys()), horizontal=True)
codigo_sel = CUENTAS_CONCENTRACION[cuenta_label]

ranking = calcular_participacion_mercado(df_balance, fecha_sel, codigo_sel, top_n=50)

if ranking.empty:
    st.warning("No hay datos disponibles para la fecha seleccionada.")
    st.stop()

hhi = calcular_hhi(ranking)
cr5 = calcular_cr_n(ranking, 5)
cr10 = calcular_cr_n(ranking, 10)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("HHI", f"{hhi:,.0f}")
    st.caption(clasificar_hhi(hhi))
with col2:
    st.metric("CR5 (Top 5 bancos)", f"{cr5:.1f}%")
with col3:
    st.metric("CR10 (Top 10 bancos)", f"{cr10:.1f}%")
with col4:
    st.metric("Bancos con datos", f"{len(ranking)}")

st.caption("HHI calculado sobre participación de mercado (%) al cuadrado, sumado entre todos los bancos con datos. "
           "Clasificación de referencia: <1,500 no concentrado · 1,500–2,500 moderadamente concentrado · >2,500 altamente concentrado.")

st.markdown("---")
st.markdown(f"### Participación de mercado — {cuenta_label}")
fig = crear_ranking_barras(ranking, x_col='participacion', y_col='banco',
                            titulo=f"Participación de mercado (%) — {cuenta_label}", formato_valor="{:.1f}%")
fig.update_layout(height=max(400, len(ranking) * 25))
st.plotly_chart(fig, width='stretch')

st.markdown("---")
st.markdown("### Concentración de cartera por segmento")
st.caption("Participación de cada segmento crediticio sobre la cartera total, por banco (indicadores PART_*).")

SEGMENTOS_PART = {
    'Consumo': 'PART_CONS', 'Inmobiliaria': 'PART_INMOB', 'Vivienda VIP': 'PART_INMOB_VIP',
    'Vivienda Social': 'PART_VIS', 'Microcrédito': 'PART_MICRO', 'Educativo': 'PART_EDU',
    'Productivo': 'PART_PROD', 'Inversión Pública': 'PART_INV_PUB',
}
segmento_sel = st.selectbox("Segmento de cartera", options=list(SEGMENTOS_PART.keys()))
codigo_part = SEGMENTOS_PART[segmento_sel]

fechas_camel = obtener_fechas_disponibles(df_camel)
fecha_camel_sel = min(fechas_camel, key=lambda f: abs((f - fecha_sel).days))
ranking_part = obtener_ranking(df_camel, codigo_part, fecha_camel_sel)

if not ranking_part.empty:
    fig2 = crear_ranking_barras(ranking_part, x_col='valor_pct', y_col='banco',
                                 titulo=f"{ETIQUETAS_INDICADORES.get(codigo_part, segmento_sel)} — participación en cartera propia (%)",
                                 formato_valor="{:.1f}%")
    fig2.update_layout(height=max(400, len(ranking_part) * 25))
    st.plotly_chart(fig2, width='stretch')
else:
    st.info("No hay datos disponibles para este segmento en la fecha seleccionada.")

st.markdown("---")
render_modulo_en_preparacion(
    "Concentración de Depósitos por Depositante (25 mayores depositantes, etc.)",
    "Requiere datos a nivel de depositante individual, que no se procesan en el pipeline actual "
    "(los datos disponibles son saldos agregados por banco). Pendiente de una fuente de datos adicional."
)
