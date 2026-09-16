# -*- coding: utf-8 -*-
"""
Riesgo de Crédito — morosidad, cobertura y participación por segmento de
cartera, usando los codigos MOR_*/COB_*/PART_* de camel.parquet.

Pagina nueva (Fase 1), 100% datos reales. Vintage, roll-rate, curvas de
transicion y recovery NO estan disponibles (no hay datos de cohortes de
originacion en el pipeline) -- se declara explicitamente, sin inventar cifras.
"""

import streamlit as st

from ui.layout import render_page, render_modulo_en_preparacion
from services.data_service import cargar_camel, obtener_fechas_disponibles
from analytics.camel_explorer import serie_promedio_sistema
from components.indicator_panel import render_panel_indicador

render_page("Riesgo de Crédito", icono="💳")

st.title("Riesgo de Crédito")
st.markdown("Morosidad, cobertura y participación de cartera por segmento — fuente: indicadores CAMEL.")

try:
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

SEGMENTOS = {
    'Total': {'mor': 'MOR_TOT', 'cob': 'COB_TOT'},
    'Consumo': {'mor': 'MOR_CONS', 'cob': 'COB_CONS'},
    'Inmobiliaria': {'mor': 'MOR_INMOB', 'cob': 'COB_INMOB'},
    'Vivienda de Interés Público': {'mor': 'MOR_INMOB_VIP', 'cob': 'COB_INMOB_VIP'},
    'Vivienda de Interés Social': {'mor': 'MOR_VIS', 'cob': 'COB_VIS'},
    'Microcrédito': {'mor': 'MOR_MICRO', 'cob': 'COB_MICRO'},
    'Educativo': {'mor': 'MOR_EDU', 'cob': 'COB_EDU'},
    'Productivo': {'mor': 'MOR_PROD', 'cob': 'COB_PROD'},
    'Inversión Pública': {'mor': 'MOR_INV_PUB', 'cob': 'COB_INV_PUB'},
}

bancos_disponibles = sorted(df_camel['banco'].unique())
fechas = obtener_fechas_disponibles(df_camel)

col_seg, col_fecha = st.columns(2)
with col_seg:
    segmento = st.selectbox("Segmento de cartera", options=list(SEGMENTOS.keys()))
with col_fecha:
    fecha_sel = st.selectbox("Fecha", options=fechas, format_func=lambda x: x.strftime('%B %Y').title(), index=0)

cod_mor = SEGMENTOS[segmento]['mor']
cod_cob = SEGMENTOS[segmento]['cob']

st.markdown("### Indicadores del sistema")
serie_mor = serie_promedio_sistema(df_camel, cod_mor)
serie_cob = serie_promedio_sistema(df_camel, cod_cob)

col1, col2 = st.columns(2)
with col1:
    val = serie_mor['valor_pct'].iloc[-1] if not serie_mor.empty else None
    st.metric(f"Morosidad promedio — {segmento}", f"{val:.2f}%" if val is not None else "N/D")
with col2:
    val = serie_cob['valor_pct'].iloc[-1] if not serie_cob.empty else None
    st.metric(f"Cobertura promedio — {segmento}", f"{val:.2f}%" if val is not None else "N/D")

st.markdown("---")
st.markdown(f"### Morosidad — {segmento}")
render_panel_indicador(df_camel, cod_mor, f"Morosidad {segmento}", fecha_sel, bancos_disponibles,
                        key_prefix="mor", colorscale_heatmap='RdYlGn_r')

st.markdown("---")
st.markdown(f"### Cobertura — {segmento}")
render_panel_indicador(df_camel, cod_cob, f"Cobertura {segmento}", fecha_sel, bancos_disponibles,
                        key_prefix="cob", colorscale_heatmap='RdYlGn')

st.markdown("---")
render_modulo_en_preparacion(
    "Vintage, Roll Rate, Curvas de Transición y Recovery",
    "Estos análisis requieren datos de cohortes de originación de crédito (fecha de desembolso, "
    "estado mes a mes) que no existen en el pipeline actual (solo se procesan ratios agregados "
    "mensuales por banco). Pendiente de una fuente de datos adicional."
)
