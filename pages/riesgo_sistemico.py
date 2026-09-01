# -*- coding: utf-8 -*-
"""
Riesgo Sistémico — índice de contribución sistémica propio (Fase 2).

Metodología interna transparente (tamaño de mercado × estrés en morosidad y
solvencia), documentada en docs/ManualTecnico.md. No es una metodología
regulatoria (BIS/Basilea) ni incluye red de interconexión/contagio
interbancario — no existen datos de exposición por contraparte en el
pipeline (ver docs/AUDITORIA_COMPLETA.md sección 6).
"""

import streamlit as st
import plotly.graph_objects as go

from ui.layout import render_page, render_modulo_en_preparacion
from services.data_service import cargar_balance, cargar_camel, obtener_fechas_disponibles
from analytics.systemic_index import calcular_contribucion_sistemica, calcular_indice_sistema_serie
from charts.builders import crear_ranking_barras
from config.theme_tokens import COLORES

render_page("Riesgo Sistémico", icono="🌐")

st.title("Riesgo Sistémico")
st.markdown("Índice de contribución sistémica por banco — metodología interna: "
            "**tamaño de mercado × estrés en morosidad y solvencia**. No es una metodología regulatoria (BIS/Basilea).")
st.caption("Ver metodología completa en docs/ManualTecnico.md.")

try:
    df_balance, _ = cargar_balance()
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

fechas_balance = obtener_fechas_disponibles(df_balance)
fecha_sel = st.selectbox("Fecha", options=fechas_balance, format_func=lambda x: x.strftime('%B %Y').title(), index=0)

df_contrib = calcular_contribucion_sistemica(df_balance, df_camel, fecha_sel, fecha_sel)

if df_contrib.empty:
    st.warning("No hay datos suficientes para calcular el índice en la fecha seleccionada.")
    st.stop()

indice_total = df_contrib['contribucion'].sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Índice Sistémico Agregado", f"{indice_total:,.1f}")
with col2:
    st.metric("Banco con mayor contribución", df_contrib.iloc[0]['banco'])
with col3:
    st.metric("Bancos evaluados", len(df_contrib))

st.markdown("---")
st.markdown("### Contribución sistémica por banco")
fig = crear_ranking_barras(df_contrib, x_col='contribucion', y_col='banco',
                            titulo=f"Contribución al Índice Sistémico — {fecha_sel.strftime('%B %Y').title()}",
                            formato_valor="{:.2f}")
fig.update_layout(height=max(400, len(df_contrib) * 25))
st.plotly_chart(fig, width='stretch')

with st.expander("Ver detalle: tamaño de mercado y estrés por banco"):
    detalle = df_contrib.copy()
    detalle['tamaño_pct'] = detalle['tamaño_pct'].apply(lambda v: f"{v:.2f}%")
    detalle['estres'] = detalle['estres'].apply(lambda v: f"{v:.1f}")
    detalle['contribucion'] = detalle['contribucion'].apply(lambda v: f"{v:.2f}")
    st.dataframe(
        detalle.rename(columns={'banco': 'Banco', 'tamaño_pct': 'Tamaño (part. mercado)',
                                 'estres': 'Estrés (0-100)', 'contribucion': 'Contribución'}),
        hide_index=True, width='stretch'
    )

st.markdown("---")
st.markdown("### Evolución del índice agregado")
fechas_camel = obtener_fechas_disponibles(df_camel)
fechas_recientes = sorted(fechas_camel)[-36:]  # ultimos 36 meses para mantener el calculo agil

serie = calcular_indice_sistema_serie(df_balance, df_camel, fechas_recientes)
if not serie.empty:
    fig2 = go.Figure(go.Scatter(x=serie['fecha'], y=serie['indice'], mode='lines+markers',
                                 line=dict(width=2, color=COLORES['rojo'])))
    fig2.update_layout(height=400, yaxis_title="Índice Sistémico Agregado", hovermode='x unified',
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']))
    st.plotly_chart(fig2, width='stretch')
    st.caption("Últimos 36 meses (se limita el rango para mantener el cálculo ágil).")
else:
    st.info("No hay suficiente historia para graficar la evolución del índice.")

st.markdown("---")
render_modulo_en_preparacion(
    "Red de Interconexión y Contagio Interbancario",
    "Requiere una matriz de exposiciones bilaterales entre bancos (quién le debe a quién y por cuánto), "
    "que no existe en el pipeline actual — solo se dispone del saldo agregado de operaciones interbancarias "
    "por banco (códigos 12/22 de balance.parquet), no un desglose por contraparte. Pendiente de una fuente de datos adicional."
)
