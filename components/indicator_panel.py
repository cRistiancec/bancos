# -*- coding: utf-8 -*-
"""
Panel estandar Ranking + Evolucion + Heatmap para un indicador de
camel.parquet. Usado por las paginas de Riesgo de Credito/Liquidez/Solvencia
para no repetir la misma disposicion de UI en cada una.
"""

import streamlit as st
import plotly.graph_objects as go

from analytics.camel_explorer import obtener_ranking, obtener_evolucion, obtener_heatmap
from charts.builders import crear_ranking_barras
from config.indicator_mapping import obtener_color_banco
from config.theme_tokens import COLORES


def render_panel_indicador(df_camel, codigo: str, nombre_indicador: str, fecha_sel, bancos_disponibles: list,
                            key_prefix: str, bancos_default: list = None, colorscale_heatmap: str = 'RdYlGn_r'):
    """Renderiza 3 pestañas: Ranking / Evolución / Heatmap para `codigo`."""
    tab_rank, tab_evol, tab_heat = st.tabs(["Ranking", "Evolución", "Heatmap"])

    with tab_rank:
        ranking = obtener_ranking(df_camel, codigo, fecha_sel)
        if ranking.empty:
            st.warning("No hay datos disponibles para la fecha seleccionada.")
        else:
            fig = crear_ranking_barras(ranking, x_col='valor_pct', y_col='banco',
                                        titulo=f"{nombre_indicador} — {fecha_sel.strftime('%B %Y').title()}",
                                        formato_valor="{:.2f}%")
            fig.update_layout(height=max(400, len(ranking) * 25))
            st.plotly_chart(fig, width='stretch')

    with tab_evol:
        bancos_sel = st.multiselect("Bancos a comparar", bancos_disponibles,
                                     default=bancos_default or bancos_disponibles[:4],
                                     max_selections=8, key=f"{key_prefix}_bancos_evol")
        if bancos_sel:
            df_evol = obtener_evolucion(df_camel, codigo, bancos_sel)
            fig = go.Figure()
            for banco in bancos_sel:
                serie = df_evol[df_evol['banco'] == banco]
                fig.add_trace(go.Scatter(x=serie['fecha'], y=serie['valor_pct'], name=banco, mode='lines',
                                          line=dict(width=2, color=obtener_color_banco(banco))))
            fig.update_layout(
                title=f"Evolución: {nombre_indicador}", height=420, yaxis_title="%", hovermode='x unified',
                legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']),
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Selecciona al menos un banco.")

    with tab_heat:
        heatmap_data = obtener_heatmap(df_camel, codigo)
        if heatmap_data.empty:
            st.warning("No hay datos suficientes para el heatmap.")
        else:
            fig = go.Figure(go.Heatmap(
                z=heatmap_data.values, x=heatmap_data.columns, y=heatmap_data.index, colorscale=colorscale_heatmap,
                hovertemplate='Banco: %{y}<br>Periodo: %{x}<br>Valor: %{z:.2f}%<extra></extra>',
            ))
            fig.update_layout(
                title=f"Evolución mensual: {nombre_indicador}", height=max(400, len(heatmap_data) * 22),
                xaxis=dict(tickangle=-45), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=COLORES['texto_primario']),
            )
            st.plotly_chart(fig, width='stretch')
