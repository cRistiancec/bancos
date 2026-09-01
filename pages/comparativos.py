# -*- coding: utf-8 -*-
"""
Comparativos entre Bancos — radar CAMEL superpuesto y tabla comparativa de
indicadores clave para bancos seleccionados.

Pagina nueva (Fase 1), 100% datos reales.
"""

import streamlit as st
import pandas as pd

from ui.layout import render_page
from services.data_service import cargar_camel, obtener_fechas_disponibles
from analytics.camel_scoring import calcular_score_camel, obtener_valor_indicador, CODIGO_A_TIPO_RANGO
from charts.builders import crear_radar_camel
from config.indicator_mapping import ETIQUETAS_INDICADORES

render_page("Comparativos entre Bancos", icono="🔀")

st.title("Comparativos entre Bancos")
st.markdown("Comparación lado a lado de bancos seleccionados: radar CAMEL y tabla de indicadores clave.")

try:
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

bancos_disponibles = sorted(df_camel['banco'].unique())
fechas = obtener_fechas_disponibles(df_camel)

col1, col2 = st.columns([3, 1])
with col1:
    default = [b for b in ['Pichincha', 'Guayaquil', 'Pacifico'] if b in bancos_disponibles] or bancos_disponibles[:2]
    bancos_sel = st.multiselect("Bancos a comparar (hasta 4)", options=bancos_disponibles, default=default, max_selections=4)
with col2:
    fecha_sel = st.selectbox("Fecha", options=fechas, format_func=lambda x: x.strftime('%B %Y').title(), index=0)

if not bancos_sel:
    st.info("Selecciona al menos un banco para comparar.")
    st.stop()

st.markdown("### Radar CAMEL")
st.caption("Score 0-100 por dimensión (metodología interna de normalización — ver docs/ManualTecnico.md).")

cols_radar = st.columns(len(bancos_sel))
for col, banco in zip(cols_radar, bancos_sel):
    with col:
        score = calcular_score_camel(df_camel, banco, fecha_sel)
        fig = crear_radar_camel(score, titulo=banco, altura=320)
        st.plotly_chart(fig, width='stretch')

st.markdown("---")
st.markdown("### Tabla comparativa de indicadores clave")

codigos = list(CODIGO_A_TIPO_RANGO.keys())  # SOL, MOR_TOT, COB_TOT, ROE, ROA, LIQ

filas = []
for banco in bancos_sel:
    fila = {'Banco': banco}
    for codigo in codigos:
        valor = obtener_valor_indicador(df_camel, banco, codigo, fecha_sel)
        fila[ETIQUETAS_INDICADORES.get(codigo, codigo)] = f"{valor * 100:.2f}%" if valor is not None else "N/D"
    filas.append(fila)

st.dataframe(pd.DataFrame(filas), hide_index=True, width='stretch')
