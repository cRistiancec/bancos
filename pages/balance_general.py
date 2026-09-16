# -*- coding: utf-8 -*-
"""
Balance General — analisis temporal de las cuentas de balance.

Migrado desde pages/2_Balance_General.py (Fase 1 del refactor institucional).
Todas las formulas se preservan sin cambios. El cambio estructural principal:
el selector jerarquico de 4 niveles, que estaba copiado 3 veces en el
archivo original, ahora usa components.account_selector una sola
implementacion; y el patron Absoluto/Indexado/Participacion ahora usa
components.mode_selector en vez de estar duplicado.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from ui.layout import render_page
from services.data_service import cargar_balance
from components.account_selector import construir_jerarquia_cuentas, seleccionar_cuenta_jerarquica
from components.mode_selector import render_selector_modo, calcular_serie_modo
from charts.builders import crear_ranking_barras
from config.indicator_mapping import obtener_color_banco
from config.theme_tokens import COLORES

render_page("Balance General", icono="⚖️")

BANCOS_DEFAULT = ['Pichincha', 'Pacifico', 'Guayaquil', 'Produbanco']
MESES = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
         7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}


# =============================================================================
# FUNCIONES DE DATOS (migradas sin cambios desde 2_Balance_General.py)
# =============================================================================

@st.cache_data
def obtener_serie_banco(df: pd.DataFrame, banco: str, codigo: str) -> pd.DataFrame:
    df_filtrado = df[(df['banco'] == banco) & (df['codigo'] == codigo)].copy()
    df_filtrado = df_filtrado.sort_values('fecha')
    df_filtrado['valor_millones'] = df_filtrado['valor'] / 1000
    return df_filtrado[['fecha', 'valor', 'valor_millones']]


@st.cache_data
def obtener_serie_sistema(df: pd.DataFrame, codigo: str) -> pd.DataFrame:
    df_filtrado = df[df['codigo'] == codigo].copy()
    serie = df_filtrado.groupby('fecha')['valor'].sum().reset_index()
    serie['valor_millones'] = serie['valor'] / 1000
    serie = serie.sort_values('fecha')
    return serie


@st.cache_data
def obtener_datos_heatmap_mensual(df_completo: pd.DataFrame, codigo: str, bancos: list = None,
                                   fecha_inicio: pd.Timestamp = None, fecha_fin: pd.Timestamp = None) -> pd.DataFrame:
    df_filtrado = df_completo[df_completo['codigo'] == codigo].copy()
    if bancos:
        df_filtrado = df_filtrado[df_filtrado['banco'].isin(bancos)]
    if df_filtrado.empty:
        return pd.DataFrame()

    df_filtrado['ano'] = df_filtrado['fecha'].dt.year
    df_filtrado['mes'] = df_filtrado['fecha'].dt.month
    df_filtrado['valor_millones'] = df_filtrado['valor'] / 1000
    df_filtrado['fecha_str'] = df_filtrado['fecha'].dt.strftime('%Y-%m')
    df_filtrado = df_filtrado.sort_values(['banco', 'ano', 'mes'])
    df_filtrado['valor_ano_anterior'] = df_filtrado.groupby(['banco', 'mes'], observed=True)['valor_millones'].shift(1)
    df_filtrado['crecimiento_yoy'] = ((df_filtrado['valor_millones'] / df_filtrado['valor_ano_anterior']) - 1) * 100

    if fecha_inicio is not None:
        df_filtrado = df_filtrado[df_filtrado['fecha'] >= fecha_inicio]
    if fecha_fin is not None:
        df_filtrado = df_filtrado[df_filtrado['fecha'] <= fecha_fin]
    if df_filtrado.empty:
        return pd.DataFrame()

    heatmap_data = df_filtrado.pivot_table(index='banco', columns='fecha_str', values='crecimiento_yoy', aggfunc='first', observed=True)

    ultima_fecha = df_filtrado['fecha'].max()
    valores_ultima_fecha = df_filtrado[df_filtrado['fecha'] == ultima_fecha].set_index('banco')['valor_millones']
    orden_bancos = valores_ultima_fecha.sort_values(ascending=True).index
    heatmap_data = heatmap_data.reindex(orden_bancos)

    return heatmap_data


@st.cache_data
def obtener_valores_bancos_mes(df: pd.DataFrame, codigo: str, fecha: pd.Timestamp) -> pd.DataFrame:
    df_filtrado = df[
        (df['codigo'] == codigo) & (df['fecha'].dt.year == fecha.year) & (df['fecha'].dt.month == fecha.month)
    ].copy()
    if df_filtrado.empty:
        return pd.DataFrame()

    df_filtrado['valor_millones'] = df_filtrado['valor'] / 1000
    df_filtrado = df_filtrado[(df_filtrado['valor_millones'].notna()) & (df_filtrado['valor_millones'] > 0)]
    if df_filtrado.empty:
        return pd.DataFrame()

    # observed=True: evita filas fantasma para bancos sin dato ese mes (categoria
    # 'banco' incluye los 24 bancos aunque algunos no reporten en periodos tempranos).
    resultado = df_filtrado.groupby('banco', as_index=False, observed=True).agg({'valor_millones': 'first'})
    return resultado.sort_values('valor_millones', ascending=False)


# =============================================================================
# PAGINA
# =============================================================================

st.title("Balance General")
st.markdown("Análisis temporal avanzado del sistema bancario ecuatoriano.")

try:
    df_balance, calidad = cargar_balance()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

bancos = sorted(df_balance['banco'].unique().tolist())
fecha_min = df_balance['fecha'].min()
fecha_max = df_balance['fecha'].max()

st.sidebar.markdown("### Información del Módulo")
st.sidebar.markdown(f"**Datos disponibles:** {fecha_min.strftime('%b %Y')} - {fecha_max.strftime('%b %Y')}")
st.sidebar.markdown(f"**Bancos:** {len(bancos)}")

jerarquia = construir_jerarquia_cuentas(df_balance)

# --- SECCION 1: EVOLUCION COMPARATIVA ---
st.markdown("---")
st.markdown("### 1. Evolución Comparativa")
st.caption("Compara la evolución temporal de múltiples bancos")

st.markdown("**Seleccionar Cuenta:**")
codigo_cuenta_final = seleccionar_cuenta_jerarquica(jerarquia, key_prefix="evol")

st.markdown("**Bancos a Comparar:**")
bancos_default = [b for b in BANCOS_DEFAULT if b in bancos]
bancos_seleccionados = st.multiselect("Selecciona hasta 10 bancos", options=bancos, default=bancos_default,
                                       max_selections=10, key="bancos_evol", label_visibility="collapsed")

col_chart, col_tiempo = st.columns([4, 1])
with col_tiempo:
    st.markdown("**Periodo**")
    mes_inicio = st.selectbox("Mes desde", options=list(range(1, 13)), format_func=lambda x: MESES[x], index=0, key="mes_inicio_evol")
    ano_inicio_evol = st.selectbox("Año desde", options=range(fecha_min.year, fecha_max.year + 1),
                                    index=max(0, 2015 - fecha_min.year), key="ano_inicio_evol")
    st.markdown("---")
    mes_fin = st.selectbox("Mes hasta", options=list(range(1, 13)), format_func=lambda x: MESES[x], index=11, key="mes_fin_evol")
    ano_fin_evol = st.selectbox("Año hasta", options=range(fecha_min.year, fecha_max.year + 1),
                                 index=fecha_max.year - fecha_min.year, key="ano_fin_evol")
    st.markdown("---")
    modo_viz, incluir_sistema = render_selector_modo("evol")

fecha_inicio_evol = pd.Timestamp(f"{ano_inicio_evol}-{mes_inicio:02d}-01")
if mes_fin == 12:
    fecha_fin_evol = pd.Timestamp(f"{ano_fin_evol}-12-31")
else:
    fecha_fin_evol = pd.Timestamp(f"{ano_fin_evol}-{mes_fin + 1:02d}-01") - pd.Timedelta(days=1)

df_evol = df_balance[(df_balance['fecha'] >= fecha_inicio_evol) & (df_balance['fecha'] <= fecha_fin_evol)]

cuenta_info = df_balance[df_balance['codigo'] == codigo_cuenta_final]['cuenta'].iloc[0] if \
    not df_balance[df_balance['codigo'] == codigo_cuenta_final].empty else codigo_cuenta_final

with col_chart:
    if bancos_seleccionados:
        fig_evol = go.Figure()
        y_title = "Millones USD"

        serie_sistema = None
        if modo_viz == "Participación %" or incluir_sistema:
            serie_sistema = obtener_serie_sistema(df_evol, codigo_cuenta_final)

        for banco in bancos_seleccionados:
            serie = obtener_serie_banco(df_evol, banco, codigo_cuenta_final)
            if serie.empty:
                continue

            x_vals, y_values, y_title = calcular_serie_modo(serie, serie_sistema, modo_viz, value_col='valor_millones')
            color_banco = obtener_color_banco(banco)
            fig_evol.add_trace(go.Scatter(
                x=x_vals, y=y_values, name=banco, mode='lines', line=dict(width=2, color=color_banco),
                hovertemplate=f'<b>{banco}</b><br>Fecha: %{{x|%b %Y}}<br>Valor: %{{y:,.1f}}<extra></extra>'
            ))

        if incluir_sistema and modo_viz != "Participación %":
            serie_sis = serie_sistema if serie_sistema is not None else obtener_serie_sistema(df_evol, codigo_cuenta_final)
            if modo_viz == "Indexado (Base 100)":
                base = serie_sis['valor_millones'].iloc[0]
                y_values = (serie_sis['valor_millones'] / base) * 100 if base > 0 else serie_sis['valor_millones']
            else:
                y_values = serie_sis['valor_millones']
            fig_evol.add_trace(go.Scatter(x=serie_sis['fecha'], y=y_values, name="SISTEMA", mode='lines',
                                           line=dict(width=3, color=COLORES['texto_primario'], dash='dash')))

        titulo_cuenta = str(cuenta_info) if len(str(cuenta_info)) < 50 else str(cuenta_info)[:47] + "..."
        fig_evol.update_layout(
            title=f"Evolución: {titulo_cuenta}", height=450, xaxis_title="Fecha", yaxis_title=y_title,
            hovermode="x unified", legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
            margin=dict(l=10, r=10, t=40, b=80), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORES['texto_primario']),
        )
        st.plotly_chart(fig_evol, width='stretch')
    else:
        st.info("Selecciona al menos un banco para visualizar.")

# --- SECCION 2: HEATMAP TEMPORAL ---
st.markdown("---")
st.markdown("### 2. Heatmap de Variación Porcentual Anual")
st.caption("Matriz Banco x Mes mostrando crecimiento YoY (cada mes vs mismo mes del año anterior)")

codigo_cuenta_heat = seleccionar_cuenta_jerarquica(jerarquia, key_prefix="heat")

col_heat_chart, col_heat_tiempo = st.columns([4, 1])
with col_heat_tiempo:
    st.markdown("**Periodo**")
    mes_inicio_heat = st.selectbox("Mes desde", options=list(range(1, 13)), format_func=lambda x: MESES[x], index=0, key="mes_inicio_heat")
    ano_inicio_heat = st.selectbox("Año desde", options=range(fecha_min.year, fecha_max.year + 1),
                                    index=max(0, 2015 - fecha_min.year), key="ano_inicio_heat")
    st.markdown("---")
    mes_fin_heat = st.selectbox("Mes hasta", options=list(range(1, 13)), format_func=lambda x: MESES[x], index=11, key="mes_fin_heat")
    ano_fin_heat = st.selectbox("Año hasta", options=range(fecha_min.year, fecha_max.year + 1),
                                 index=fecha_max.year - fecha_min.year, key="ano_fin_heat")

fecha_inicio_heat = pd.Timestamp(f"{ano_inicio_heat}-{mes_inicio_heat:02d}-01")
if mes_fin_heat == 12:
    fecha_fin_heat = pd.Timestamp(f"{ano_fin_heat}-12-31")
else:
    fecha_fin_heat = pd.Timestamp(f"{ano_fin_heat}-{mes_fin_heat + 1:02d}-01") - pd.Timedelta(days=1)

cuenta_heat_info = df_balance[df_balance['codigo'] == codigo_cuenta_heat]['cuenta'].iloc[0] if \
    not df_balance[df_balance['codigo'] == codigo_cuenta_heat].empty else codigo_cuenta_heat

heatmap_data = obtener_datos_heatmap_mensual(df_balance, codigo_cuenta_heat, None, fecha_inicio_heat, fecha_fin_heat)

with col_heat_chart:
    if not heatmap_data.empty:
        etiquetas_x = [f"{MESES[int(col.split('-')[1])][:3]} {col.split('-')[0][2:]}" for col in heatmap_data.columns]
        colorscale_divergente = [
            [0.0, 'rgb(165, 0, 38)'], [0.25, 'rgb(215, 48, 39)'], [0.4, 'rgb(244, 109, 67)'],
            [0.5, 'rgb(255, 255, 255)'], [0.6, 'rgb(166, 217, 106)'], [0.75, 'rgb(102, 189, 99)'],
            [1.0, 'rgb(0, 104, 55)'],
        ]
        fig_heat = go.Figure(data=go.Heatmap(
            z=heatmap_data.values, x=etiquetas_x, y=heatmap_data.index, colorscale=colorscale_divergente,
            zmid=0, zmin=-30, zmax=30,
            hovertemplate='Banco: %{y}<br>Periodo: %{x}<br>Variacion YoY: %{z:.1f}%<extra></extra>',
            colorbar=dict(title="Variacion %", ticksuffix="%")
        ))
        titulo_cuenta_h = str(cuenta_heat_info) if len(str(cuenta_heat_info)) < 50 else str(cuenta_heat_info)[:47] + "..."
        fig_heat.update_layout(
            title=f"Variación YoY: {titulo_cuenta_h}", height=max(400, len(heatmap_data) * 22),
            xaxis_title="Periodo", yaxis_title="", xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
            margin=dict(l=10, r=10, t=40, b=80), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORES['texto_primario']),
        )
        st.plotly_chart(fig_heat, width='stretch')
    else:
        st.warning("No hay datos suficientes para el heatmap.")

# --- SECCION 3: RANKING POR BANCO ---
st.markdown("---")
st.markdown("### 3. Ranking de Bancos por Cuenta")
st.caption("Comparación de valores de todos los bancos para una cuenta y mes específicos")

codigo_r = seleccionar_cuenta_jerarquica(jerarquia, key_prefix="rank")

col_f5, col_f6 = st.columns(2)
with col_f5:
    mes_r = st.selectbox("Mes", options=list(MESES.keys()), format_func=lambda x: MESES[x], index=fecha_max.month - 1, key="mes_r")
with col_f6:
    ano_r = st.selectbox("Año", options=range(fecha_min.year, fecha_max.year + 1), index=fecha_max.year - fecha_min.year, key="ano_r")

fecha_r = pd.Timestamp(year=ano_r, month=mes_r, day=1)
cuenta_info_r = df_balance[df_balance['codigo'] == codigo_r]['cuenta'].iloc[0] if len(df_balance[df_balance['codigo'] == codigo_r]) > 0 else codigo_r
titulo_cuenta_r = f"{codigo_r} - {cuenta_info_r}" if cuenta_info_r != codigo_r else codigo_r

datos_ranking = obtener_valores_bancos_mes(df_balance, codigo_r, fecha_r)

if not datos_ranking.empty:
    fig_ranking = crear_ranking_barras(datos_ranking, x_col='valor_millones', y_col='banco',
                                        titulo=f"Ranking: {titulo_cuenta_r} ({MESES[mes_r]} {ano_r})",
                                        formato_valor="${:,.0f}M")
    fig_ranking.update_layout(height=max(400, len(datos_ranking) * 25))
    st.plotly_chart(fig_ranking, width='stretch')

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Total Sistema", f"${datos_ranking['valor_millones'].sum():,.0f}M")
    with col_s2:
        participacion_top = (datos_ranking.iloc[0]['valor_millones'] / datos_ranking['valor_millones'].sum() * 100) if len(datos_ranking) > 0 else 0
        st.metric("Participación #1", f"{participacion_top:.1f}%")
    with col_s3:
        participacion_top5 = (datos_ranking.head(5)['valor_millones'].sum() / datos_ranking['valor_millones'].sum() * 100) if len(datos_ranking) >= 5 else 0
        st.metric("Concentración Top 5", f"{participacion_top5:.1f}%")
else:
    st.warning("No hay datos disponibles para el periodo seleccionado.")
