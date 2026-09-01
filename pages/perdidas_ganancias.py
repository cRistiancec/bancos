# -*- coding: utf-8 -*-
"""
Pérdidas y Ganancias — análisis de resultados y rentabilidad.

Migrado desde pages/3_Perdidas_Ganancias.py (Fase 1 del refactor
institucional). Formulas sin cambios; el patron Absoluto/Indexado/
Participacion ahora usa components.mode_selector (compartido con Balance
General) en vez de estar duplicado.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import calendar

from ui.layout import render_page
from services.data_service import cargar_pyg, obtener_fechas_disponibles
from components.mode_selector import render_selector_modo, calcular_serie_modo
from charts.builders import crear_ranking_barras
from config.indicator_mapping import obtener_color_banco
from config.theme_tokens import COLORES

render_page("Pérdidas y Ganancias", icono="💰")

CUENTAS_PYG = {
    'MNI': 'Margen Neto de Intereses', 'MBF': 'Margen Bruto Financiero',
    'MNF': 'Margen Neto Financiero', 'MDI': 'Margen de Intermediación',
    'MOP': 'Margen Operacional', 'GAI': 'Ganancia Antes de Impuestos',
    'GDE': 'Ganancia del Ejercicio',
}

MESES = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
         7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}

st.title("Pérdidas y Ganancias")
st.markdown("Análisis de pérdidas y ganancias del sistema bancario ecuatoriano.")

try:
    df_pyg, calidad = cargar_pyg()
except Exception as e:
    st.error(f"Error al cargar datos de PYG: {e}")
    st.stop()

bancos = sorted(df_pyg['banco'].unique().tolist())
df_pyg = df_pyg[df_pyg['valor_12m'].notna()]
fechas = obtener_fechas_disponibles(df_pyg)
fecha_min = min(fechas)
fecha_max = max(fechas)

BANCOS_DEFAULT = ['Pichincha', 'Pacifico', 'Guayaquil', 'Produbanco']
bancos_exactos = [b for b in BANCOS_DEFAULT if b in bancos] or bancos[:4]

# --- SECCION 1: EVOLUCION COMPARATIVA ---
st.markdown("---")
st.markdown("### 1. Evolución Comparativa")
st.caption("Compara la evolución temporal de múltiples bancos para un indicador de P&G")

st.markdown("**Seleccionar Indicador:**")
cuenta_label = st.selectbox("Indicador", options=[f"{k} - {v}" for k, v in CUENTAS_PYG.items()], index=6, key="cuenta_pyg")
codigo_cuenta = cuenta_label.split(' - ')[0]

st.markdown("**Bancos a Comparar:**")
bancos_seleccionados = st.multiselect("Selecciona hasta 10 bancos", options=bancos, default=bancos_exactos,
                                       max_selections=10, key="bancos_evol_pyg", label_visibility="collapsed")

col_chart, col_tiempo = st.columns([4, 1])
with col_tiempo:
    st.markdown("**Periodo**")
    mes_inicio = st.selectbox("Mes desde", options=list(range(1, 13)), format_func=lambda x: MESES[x], index=0, key="mes_inicio_pyg")
    ano_inicio = st.selectbox("Año desde", options=range(fecha_min.year, fecha_max.year + 1),
                               index=max(0, 2015 - fecha_min.year), key="ano_inicio_pyg")
    mes_fin = st.selectbox("Mes hasta", options=list(range(1, 13)), format_func=lambda x: MESES[x], index=fecha_max.month - 1, key="mes_fin_pyg")
    ano_fin = st.selectbox("Año hasta", options=range(fecha_min.year, fecha_max.year + 1),
                            index=fecha_max.year - fecha_min.year, key="ano_fin_pyg")
    modo, incluir_sistema = render_selector_modo("pyg")

with col_chart:
    fecha_inicio_sel = pd.Timestamp(year=ano_inicio, month=mes_inicio, day=1)
    last_day_fin = calendar.monthrange(ano_fin, mes_fin)[1]
    fecha_fin_sel = pd.Timestamp(year=ano_fin, month=mes_fin, day=last_day_fin)

    if bancos_seleccionados:
        fig_evol = go.Figure()

        df_rango = df_pyg[
            (df_pyg['codigo'] == codigo_cuenta) & (df_pyg['fecha'] >= fecha_inicio_sel) & (df_pyg['fecha'] <= fecha_fin_sel)
        ]

        serie_sistema = None
        if modo == "Participación %" or incluir_sistema:
            serie_sistema = df_rango.groupby('fecha')['valor_12m'].sum().reset_index()
            serie_sistema['valor_millones'] = serie_sistema['valor_12m'] / 1000

        for banco in bancos_seleccionados:
            df_banco = df_rango[df_rango['banco'] == banco].copy().sort_values('fecha')
            if df_banco.empty:
                continue
            df_banco['valor_millones'] = df_banco['valor_12m'] / 1000

            x_vals, y_data, y_label = calcular_serie_modo(df_banco, serie_sistema, modo, value_col='valor_millones')

            color_banco = obtener_color_banco(banco)
            fig_evol.add_trace(go.Scatter(
                x=x_vals, y=y_data, name=banco, mode='lines', line=dict(width=2, color=color_banco),
                hovertemplate='<b>%{fullData.name}</b><br>Fecha: %{x|%b %Y}<br>Valor: %{y:,.1f}<extra></extra>'
            ))

        if incluir_sistema and modo == "Valores Absolutos":
            fig_evol.add_trace(go.Scatter(
                x=serie_sistema['fecha'], y=serie_sistema['valor_millones'], name='TOTAL SISTEMA', mode='lines',
                line=dict(width=3, dash='dash', color=COLORES['texto_primario']),
                hovertemplate='<b>%{fullData.name}</b><br>Fecha: %{x|%b %Y}<br>Valor: %{y:,.1f}M<extra></extra>'
            ))

        fig_evol.update_layout(
            title=f"Evolución: {CUENTAS_PYG[codigo_cuenta]}", height=450, xaxis_title="Fecha", yaxis_title=y_label,
            hovermode="x unified", legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            margin=dict(l=10, r=10, t=40, b=80), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORES['texto_primario']),
        )
        st.plotly_chart(fig_evol, width='stretch')
    else:
        st.info("Selecciona al menos un banco para visualizar.")

st.markdown("---")

# --- SECCION 2: RANKING ---
st.markdown("### 2. Ranking de Bancos por Indicador")
st.caption("Comparación de valores de todos los bancos para un indicador y mes específicos")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    cuenta_label_rank = st.selectbox("Indicador", options=[f"{k} - {v}" for k, v in CUENTAS_PYG.items()], index=6, key="cuenta_rank_pyg")
    codigo_rank = cuenta_label_rank.split(' - ')[0]
with col_f2:
    mes_rank = st.selectbox("Mes", options=list(MESES.keys()), format_func=lambda x: MESES[x], index=fecha_max.month - 1, key="mes_rank_pyg")
with col_f3:
    ano_rank = st.selectbox("Año", options=range(fecha_min.year, fecha_max.year + 1), index=fecha_max.year - fecha_min.year, key="ano_rank_pyg")

last_day_rank = calendar.monthrange(ano_rank, mes_rank)[1]
fecha_rank = pd.Timestamp(year=ano_rank, month=mes_rank, day=last_day_rank)

df_rank = df_pyg[(df_pyg['fecha'] == fecha_rank) & (df_pyg['codigo'] == codigo_rank)].copy()

if not df_rank.empty:
    df_rank['valor_millones'] = df_rank['valor_12m'] / 1000
    # NOTA: se ordena ascendente aqui porque asi lo hacia 3_Perdidas_Ganancias.py
    # original antes de calcular las metricas de abajo -- ver comentario junto
    # a "Concentracion Top 5".
    df_rank = df_rank.sort_values('valor_millones', ascending=True)

    fig_rank = crear_ranking_barras(df_rank, x_col='valor_millones', y_col='banco',
                                     titulo=f"{CUENTAS_PYG[codigo_rank]} - {MESES[mes_rank]} {ano_rank}",
                                     formato_valor="${:,.0f}M")
    fig_rank.update_layout(height=max(400, len(df_rank) * 25))
    st.plotly_chart(fig_rank, width='stretch')

    col_s1, col_s2, col_s3 = st.columns(3)
    total_sistema = df_rank['valor_millones'].sum()
    with col_s1:
        st.metric("Total Sistema", f"${total_sistema:,.0f}M")
    with col_s2:
        participacion_top1 = (df_rank['valor_millones'].max() / total_sistema * 100) if total_sistema > 0 else 0
        st.metric("Participación #1", f"{participacion_top1:.1f}%")
    with col_s3:
        # Preserva textualmente el comportamiento del dashboard original: al
        # estar df_rank ordenado ascendente, head(5) toma los 5 bancos MAS
        # PEQUEÑOS, no los mas grandes. Es un bug preexistente documentado en
        # docs/AUDITORIA_COMPLETA.md; no se corrige en este refactor para no
        # alterar resultados sin aprobacion explicita.
        participacion_top5 = (df_rank.head(5)['valor_millones'].sum() / total_sistema * 100) if len(df_rank) >= 5 else 0
        st.metric("Concentración Top 5", f"{participacion_top5:.1f}%")
else:
    st.warning("No hay datos disponibles para el periodo seleccionado.")
