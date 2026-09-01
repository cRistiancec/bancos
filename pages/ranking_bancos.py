# -*- coding: utf-8 -*-
"""
Ranking de Bancos — ranking generico sobre cualquier indicador de los 3
datasets (Balance, P&G, CAMEL), para un periodo y todos los bancos.

Pagina nueva (Fase 1). Generaliza el patron de ranking que estaba repetido
de forma independiente en Balance General, Perdidas y Ganancias y CAMEL.
"""

import streamlit as st
import pandas as pd
import calendar

from ui.layout import render_page
from services.data_service import cargar_balance, cargar_pyg, cargar_camel, obtener_fechas_disponibles
from components.account_selector import construir_jerarquia_cuentas, seleccionar_cuenta_jerarquica
from analytics.camel_explorer import obtener_ranking
from charts.builders import crear_ranking_barras
from config.indicator_mapping import INDICADORES_PRINCIPALES

render_page("Ranking de Bancos", icono="🏆")

st.title("Ranking de Bancos")
st.markdown("Ranking de todos los bancos del sistema para un indicador y período específicos.")

MESES = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
         7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}

CUENTAS_PYG = {
    'MNI': 'Margen Neto de Intereses', 'MBF': 'Margen Bruto Financiero', 'MNF': 'Margen Neto Financiero',
    'MDI': 'Margen de Intermediación', 'MOP': 'Margen Operacional', 'GAI': 'Ganancia Antes de Impuestos',
    'GDE': 'Ganancia del Ejercicio',
}

dataset_sel = st.radio("Fuente de datos", options=["Balance General", "Pérdidas y Ganancias", "Indicadores CAMEL"], horizontal=True)
st.markdown("---")

if dataset_sel == "Balance General":
    try:
        df_balance, _ = cargar_balance()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.stop()

    jerarquia = construir_jerarquia_cuentas(df_balance)
    st.markdown("**Cuenta:**")
    codigo = seleccionar_cuenta_jerarquica(jerarquia, key_prefix="rankgen_bal")

    fecha_max = df_balance['fecha'].max()
    fecha_min = df_balance['fecha'].min()
    col1, col2 = st.columns(2)
    with col1:
        mes = st.selectbox("Mes", options=list(MESES.keys()), format_func=lambda x: MESES[x], index=fecha_max.month - 1)
    with col2:
        ano = st.selectbox("Año", options=range(fecha_min.year, fecha_max.year + 1), index=fecha_max.year - fecha_min.year)

    fecha_sel = pd.Timestamp(year=ano, month=mes, day=1)
    df_filtrado = df_balance[(df_balance['codigo'] == codigo) &
                              (df_balance['fecha'].dt.year == ano) & (df_balance['fecha'].dt.month == mes)].copy()
    if not df_filtrado.empty:
        df_filtrado['valor_millones'] = df_filtrado['valor'] / 1000
        df_filtrado = df_filtrado[df_filtrado['valor_millones'] > 0]
        ranking = df_filtrado.groupby('banco', as_index=False, observed=True).agg({'valor_millones': 'first'}).sort_values('valor_millones', ascending=False)
        cuenta_nombre = df_balance[df_balance['codigo'] == codigo]['cuenta'].iloc[0] if not df_balance[df_balance['codigo'] == codigo].empty else codigo
        titulo = f"{cuenta_nombre} — {MESES[mes]} {ano}"
        x_col, formato = 'valor_millones', "${:,.0f}M"
    else:
        ranking = pd.DataFrame()

elif dataset_sel == "Pérdidas y Ganancias":
    try:
        df_pyg, _ = cargar_pyg()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.stop()

    df_pyg = df_pyg[df_pyg['valor_12m'].notna()]
    fechas = obtener_fechas_disponibles(df_pyg)
    fecha_max, fecha_min = max(fechas), min(fechas)

    col1, col2, col3 = st.columns(3)
    with col1:
        cuenta_label = st.selectbox("Indicador", options=[f"{k} - {v}" for k, v in CUENTAS_PYG.items()], index=6)
        codigo = cuenta_label.split(' - ')[0]
    with col2:
        mes = st.selectbox("Mes", options=list(MESES.keys()), format_func=lambda x: MESES[x], index=fecha_max.month - 1)
    with col3:
        ano = st.selectbox("Año", options=range(fecha_min.year, fecha_max.year + 1), index=fecha_max.year - fecha_min.year)

    last_day = calendar.monthrange(ano, mes)[1]
    fecha_sel = pd.Timestamp(year=ano, month=mes, day=last_day)
    df_filtrado = df_pyg[(df_pyg['codigo'] == codigo) & (df_pyg['fecha'] == fecha_sel)].copy()
    if not df_filtrado.empty:
        df_filtrado['valor_millones'] = df_filtrado['valor_12m'] / 1000
        ranking = df_filtrado[['banco', 'valor_millones']].sort_values('valor_millones', ascending=False)
        titulo = f"{CUENTAS_PYG[codigo]} — {MESES[mes]} {ano}"
        x_col, formato = 'valor_millones', "${:,.0f}M"
    else:
        ranking = pd.DataFrame()

else:  # CAMEL
    try:
        df_camel, _ = cargar_camel()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        categoria = st.selectbox("Categoría", options=list(INDICADORES_PRINCIPALES.keys()))
        opciones = {nombre: cod for cod, nombre in INDICADORES_PRINCIPALES[categoria]}
        indicador_nombre = st.selectbox("Indicador", options=list(opciones.keys()))
        codigo = opciones[indicador_nombre]
    with col2:
        fechas = obtener_fechas_disponibles(df_camel)
        fecha_sel = st.selectbox("Fecha", options=fechas, format_func=lambda x: x.strftime('%B %Y').title(), index=0)

    ranking = obtener_ranking(df_camel, codigo, fecha_sel)
    if not ranking.empty:
        titulo = f"{indicador_nombre} — {fecha_sel.strftime('%B %Y').title()}"
        x_col, formato = 'valor_pct', "{:.2f}%"

if not ranking.empty:
    fig = crear_ranking_barras(ranking, x_col=x_col, y_col='banco', titulo=titulo, formato_valor=formato)
    fig.update_layout(height=max(400, len(ranking) * 25))
    st.plotly_chart(fig, width='stretch')

    total = ranking[x_col].sum()
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Bancos con datos", len(ranking))
    with col_s2:
        top1 = (ranking[x_col].max() / total * 100) if total else 0
        st.metric("Participación líder (sobre total mostrado)", f"{top1:.1f}%")
    with col_s3:
        top5 = (ranking.head(5)[x_col].sum() / total * 100) if total and len(ranking) >= 5 else 0
        st.metric("Concentración Top 5", f"{top5:.1f}%")
else:
    st.warning("No hay datos disponibles para la selección actual.")
