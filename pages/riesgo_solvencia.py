# -*- coding: utf-8 -*-
"""
Riesgo de Solvencia — Índice de Solvencia (camel.parquet) y Patrimonio/Activos
+ Apalancamiento (calculados de balance.parquet).

Pagina nueva (Fase 1), 100% datos reales.
"""

import streamlit as st
import pandas as pd

from ui.layout import render_page
from services.data_service import cargar_camel, cargar_balance, obtener_fechas_disponibles
from analytics.camel_explorer import serie_promedio_sistema
from analytics.camel_scoring import clasificar_semaforo
from components.indicator_panel import render_panel_indicador
from components.semaforo import render_badge_severidad
from charts.builders import crear_ranking_barras
from config.indicator_mapping import CODIGOS_BALANCE

render_page("Riesgo de Solvencia", icono="🏛️")

st.title("Riesgo de Solvencia")
st.markdown("Índice de Solvencia regulatorio, Patrimonio/Activos y Apalancamiento del sistema.")

try:
    df_camel, _ = cargar_camel()
    df_balance, _ = cargar_balance()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

bancos_disponibles = sorted(df_camel['banco'].unique())
fechas_camel = obtener_fechas_disponibles(df_camel)
fecha_sel = st.selectbox("Fecha", options=fechas_camel, format_func=lambda x: x.strftime('%B %Y').title(), index=0)

serie = serie_promedio_sistema(df_camel, 'SOL')
val = serie['valor_pct'].iloc[-1] if not serie.empty else None

col1, col2 = st.columns([1, 3])
with col1:
    st.metric("Solvencia promedio del sistema", f"{val:.2f}%" if val is not None else "N/D")
    st.caption("Mínimo regulatorio de referencia: 9% (ver config.indicator_mapping.RANGOS_INDICADORES).")
    if val is not None:
        st.markdown(render_badge_severidad(clasificar_semaforo(val, 'SOL')), unsafe_allow_html=True)

st.markdown("---")
render_panel_indicador(df_camel, 'SOL', "Índice de Solvencia", fecha_sel, bancos_disponibles,
                        key_prefix="sol", colorscale_heatmap='RdYlGn')

st.markdown("---")
st.markdown("### Patrimonio / Activos y Apalancamiento (calculado de balance.parquet)")


@st.cache_data
def calcular_patrimonio_apalancamiento(df_balance: pd.DataFrame, fecha) -> pd.DataFrame:
    df_fecha = df_balance[df_balance['fecha'] == fecha]
    activos = df_fecha[df_fecha['codigo'] == CODIGOS_BALANCE['activo_total']][['banco', 'valor']].rename(columns={'valor': 'activo'})
    patrimonio = df_fecha[df_fecha['codigo'] == CODIGOS_BALANCE['patrimonio']][['banco', 'valor']].rename(columns={'valor': 'patrimonio'})
    df = activos.merge(patrimonio, on='banco')
    df = df[df['activo'] > 0]
    df['patrimonio_activos_pct'] = (df['patrimonio'] / df['activo']) * 100
    df['apalancamiento_x'] = df['activo'] / df['patrimonio']
    return df.sort_values('patrimonio_activos_pct', ascending=False)


fechas_balance = obtener_fechas_disponibles(df_balance)
fecha_balance_sel = min(fechas_balance, key=lambda f: abs((f - fecha_sel).days)) if fecha_sel in fechas_camel else fechas_balance[0]

df_solv = calcular_patrimonio_apalancamiento(df_balance, fecha_balance_sel)

if not df_solv.empty:
    col_a, col_b = st.columns(2)
    with col_a:
        fig1 = crear_ranking_barras(df_solv, x_col='patrimonio_activos_pct', y_col='banco',
                                     titulo="Patrimonio / Activos (%)", formato_valor="{:.1f}%")
        fig1.update_layout(height=max(400, len(df_solv) * 25))
        st.plotly_chart(fig1, width='stretch')
    with col_b:
        df_apalancamiento = df_solv.sort_values('apalancamiento_x', ascending=False)
        fig2 = crear_ranking_barras(df_apalancamiento, x_col='apalancamiento_x', y_col='banco',
                                     titulo="Apalancamiento (Activos / Patrimonio, veces)", formato_valor="{:.1f}x")
        fig2.update_layout(height=max(400, len(df_apalancamiento) * 25))
        st.plotly_chart(fig2, width='stretch')
else:
    st.warning("No hay datos suficientes para calcular Patrimonio/Activos en la fecha seleccionada.")
