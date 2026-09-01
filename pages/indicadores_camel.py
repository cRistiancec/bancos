# -*- coding: utf-8 -*-
"""
Indicadores CAMEL — Capital, Assets, Management, Earnings, Liquidity.

Migrado desde pages/4_CAMEL.py (Fase 1 del refactor institucional). Formulas
sin cambios. La taxonomia de indicadores (antes duplicada localmente en 3
diccionarios) ahora se centraliza en config/indicator_mapping.py
(INDICADORES_PRINCIPALES se deriva de GRUPOS_INDICADORES + ETIQUETAS_INDICADORES,
que ya existian). Se corrige el bug inofensivo del @st.cache_data duplicado.
Se agrega una 4a pestaña de Radar CAMEL (antes muerta en utils/charts.py)
como vista adicional.

Se mantiene el nombre CAMEL (no "CAMELS"): el componente de Sensibilidad al
riesgo de mercado no tiene datos que lo respalden -- ver AUDITORIA_COMPLETA.md.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ui.layout import render_page
from services.data_service import cargar_camel, cargar_balance, obtener_fechas_disponibles
from config.indicator_mapping import (
    obtener_color_banco, INDICADORES_PRINCIPALES, ESCALAS_COLORES_HEATMAP, RANGOS_HEATMAP,
)
from config.theme_tokens import COLORES
from charts.builders import crear_radar_camel
from analytics.camel_scoring import calcular_score_camel, calcular_score_promedio_sistema

render_page("Indicadores CAMEL", icono="📈")


# =============================================================================
# FUNCIONES DE DATOS (migradas sin cambios desde 4_CAMEL.py)
# =============================================================================

@st.cache_data
def obtener_fecha_disponible(df: pd.DataFrame, codigo: str, fecha_objetivo) -> pd.Timestamp:
    df_fecha = df[(df['codigo'] == codigo) & (df['fecha'] == fecha_objetivo)]
    if not df_fecha.empty:
        return fecha_objetivo

    df_codigo = df[df['codigo'] == codigo]
    fechas_disponibles = df_codigo['fecha'].sort_values(ascending=False)
    for fecha in fechas_disponibles:
        if fecha <= fecha_objetivo:
            return fecha
    return fechas_disponibles.iloc[0] if len(fechas_disponibles) > 0 else fecha_objetivo


@st.cache_data
def obtener_ranking_indicador(df: pd.DataFrame, codigo: str, fecha, excluir_bancos: list = None) -> tuple:
    fecha_real = obtener_fecha_disponible(df, codigo, fecha)
    df_filtrado = df[(df['codigo'] == codigo) & (df['fecha'] == fecha_real)].copy()
    if excluir_bancos:
        df_filtrado = df_filtrado[~df_filtrado['banco'].isin(excluir_bancos)]
    df_filtrado['valor_pct'] = df_filtrado['valor'] * 100
    df_filtrado = df_filtrado.sort_values('valor', ascending=False)
    return df_filtrado[['banco', 'valor', 'valor_pct']], fecha_real


@st.cache_data
def obtener_evolucion_indicador(df: pd.DataFrame, codigo: str, bancos: list) -> pd.DataFrame:
    df_filtrado = df[(df['codigo'] == codigo) & (df['banco'].isin(bancos))].copy()
    df_filtrado = df_filtrado.sort_values(['banco', 'fecha'])
    df_filtrado['valor_pct'] = df_filtrado['valor'] * 100
    return df_filtrado


@st.cache_data
def obtener_heatmap_indicador(df: pd.DataFrame, codigo: str, fecha_inicio=None, fecha_fin=None) -> pd.DataFrame:
    df_filtrado = df[df['codigo'] == codigo].copy()
    if fecha_inicio is not None:
        df_filtrado = df_filtrado[df_filtrado['fecha'] >= fecha_inicio]
    if fecha_fin is not None:
        df_filtrado = df_filtrado[df_filtrado['fecha'] <= fecha_fin]
    if df_filtrado.empty:
        return pd.DataFrame()

    df_filtrado['periodo'] = df_filtrado['fecha'].dt.strftime('%Y-%m')
    heatmap_data = df_filtrado.pivot(index='banco', columns='periodo', values='valor')

    try:
        df_balance, _ = cargar_balance()
        fecha_max = df_balance['fecha'].max()
        df_activos = df_balance[(df_balance['codigo'] == '1') & (df_balance['fecha'] == fecha_max)][['banco', 'valor']].copy()
        df_activos = df_activos.set_index('banco')
        bancos_ordenados = df_activos.sort_values('valor', ascending=True).index
        bancos_en_heatmap = [b for b in bancos_ordenados if b in heatmap_data.index]
        if bancos_en_heatmap:
            heatmap_data = heatmap_data.reindex(bancos_en_heatmap)
    except Exception:
        if len(heatmap_data.columns) > 0:
            ultima_col = heatmap_data.columns[-1]
            heatmap_data = heatmap_data.sort_values(ultima_col, ascending=False, na_position='last')

    return heatmap_data * 100


# =============================================================================
# VISUALIZACIONES
# =============================================================================

def crear_grafico_evolucion(df: pd.DataFrame, codigo: str, bancos: list, nombre_indicador: str, fecha_inicio=None):
    df_evol = obtener_evolucion_indicador(df, codigo, bancos)
    if df_evol.empty:
        st.warning("No hay datos disponibles para los bancos seleccionados")
        return
    if fecha_inicio is not None:
        df_evol = df_evol[df_evol['fecha'] >= fecha_inicio]

    color_map = {banco: obtener_color_banco(banco) for banco in bancos}
    fig = px.line(df_evol, x='fecha', y='valor_pct', color='banco', title=f"Evolución: {nombre_indicador}",
                  labels={'fecha': 'Fecha', 'valor_pct': 'Valor (%)', 'banco': 'Banco'},
                  color_discrete_map=color_map)
    fig.update_layout(
        height=450, legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
        hovermode='x unified', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLORES['texto_primario']),
    )
    st.plotly_chart(fig, width='stretch')


def crear_ranking_barras_camel(df: pd.DataFrame, codigo: str, fecha, nombre_indicador: str, excluir_bancos: list = None):
    df_ranking, fecha_real = obtener_ranking_indicador(df, codigo, fecha, excluir_bancos)
    if df_ranking.empty:
        st.warning("No hay datos disponibles")
        return

    colors = [obtener_color_banco(banco) for banco in df_ranking['banco']]
    fig = go.Figure(go.Bar(
        x=df_ranking['valor_pct'], y=df_ranking['banco'], orientation='h', marker=dict(color=colors),
        text=df_ranking['valor_pct'].apply(lambda x: f"{x:.1f}%"), textposition='outside',
        hovertemplate='<b>%{y}</b><br>Valor: %{x:.1f}%<extra></extra>'
    ))
    fig.update_layout(
        title=f"Ranking: {nombre_indicador}", xaxis_title='Valor (%)', yaxis_title='',
        height=max(400, len(df_ranking) * 25), showlegend=False, yaxis=dict(categoryorder='total ascending'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']),
    )
    st.plotly_chart(fig, width='stretch')

    if fecha_real != fecha:
        st.info(f"Datos de {fecha_real.strftime('%B %Y')} (fecha más reciente disponible)")
    if excluir_bancos:
        st.caption(f"Excluidos del ranking: {', '.join(excluir_bancos)} (valores atípicos)")


def crear_heatmap_indicador_camel(df: pd.DataFrame, codigo: str, nombre_indicador: str, fecha_inicio=None, fecha_fin=None):
    heatmap_data = obtener_heatmap_indicador(df, codigo, fecha_inicio, fecha_fin)
    if heatmap_data.empty:
        st.warning("No hay datos suficientes para el heatmap en el rango seleccionado")
        return

    colorscale = ESCALAS_COLORES_HEATMAP.get(codigo, 'RdYlGn')
    rango = RANGOS_HEATMAP.get(codigo, None)

    zmid = None
    if rango:
        zmid = 0 if codigo in ['ROA', 'ROE'] else (rango[0] + rango[1]) / 2

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values, x=heatmap_data.columns, y=heatmap_data.index, colorscale=colorscale,
        zmid=zmid, zmin=rango[0] if rango else None, zmax=rango[1] if rango else None,
        hovertemplate='Banco: %{y}<br>Periodo: %{x}<br>Valor: %{z:.1f}%<extra></extra>',
    ))
    fig.update_layout(
        title=f"Evolución Mensual: {nombre_indicador} (%)", height=max(400, len(heatmap_data) * 22),
        xaxis_title='Periodo (Año-Mes)', yaxis_title='Banco', xaxis={'tickangle': -45},
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']),
    )
    st.plotly_chart(fig, width='stretch')


# =============================================================================
# PAGINA
# =============================================================================

st.title("Indicadores CAMEL")

try:
    df_camel, calidad = cargar_camel()
except FileNotFoundError as e:
    st.error(f"No se encontró el archivo de datos CAMEL: {e}")
    st.info("Ejecuta `python scripts/procesar_camel.py` para generar los datos")
    st.stop()

st.sidebar.header("Filtros")
fechas = obtener_fechas_disponibles(df_camel)
fecha_seleccionada = st.sidebar.selectbox(
    "Fecha de análisis", options=fechas, index=0 if fechas else None,
    format_func=lambda x: x.strftime('%B %Y') if pd.notna(x) else str(x)
)
bancos_disponibles = sorted(df_camel['banco'].unique())

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Indicadores:** {calidad['indicadores_unicos']}")
st.sidebar.markdown(f"**Bancos:** {calidad['bancos']}")
st.sidebar.markdown(f"**Registros:** {calidad['registros_limpios']:,}")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Análisis por Indicador", "📈 Evolución Temporal", "🗺️ Heatmap Mensual", "🎯 Radar CAMEL",
])

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        categorias = list(INDICADORES_PRINCIPALES.keys())
        categoria_sel = st.selectbox("Categoría", categorias)
        indicadores_cat = INDICADORES_PRINCIPALES[categoria_sel]
        indicador_opciones = {nombre: codigo for codigo, nombre in indicadores_cat}
        indicador_nombre = st.selectbox("Indicador", list(indicador_opciones.keys()))
        indicador_codigo = indicador_opciones[indicador_nombre]

    with col2:
        excluir_bancos = ['Citibank', 'Coopnacional'] if indicador_codigo == 'COB_TOT' else None
        crear_ranking_barras_camel(df_camel, indicador_codigo, fecha_seleccionada, indicador_nombre, excluir_bancos)

with tab2:
    col1, col2 = st.columns([1, 3])
    with col1:
        categoria_evol = st.selectbox("Categoría", list(INDICADORES_PRINCIPALES.keys()), key='cat_evol')
        indicadores_evol = INDICADORES_PRINCIPALES[categoria_evol]
        indicador_opciones_evol = {nombre: codigo for codigo, nombre in indicadores_evol}
        indicador_nombre_evol = st.selectbox("Indicador", list(indicador_opciones_evol.keys()), key='ind_evol')
        indicador_codigo_evol = indicador_opciones_evol[indicador_nombre_evol]

        bancos_evol = st.multiselect(
            "Bancos a comparar", bancos_disponibles,
            default=['Pichincha', 'Guayaquil', 'Pacifico'] if all(b in bancos_disponibles for b in ['Pichincha', 'Guayaquil', 'Pacifico']) else bancos_disponibles[:3],
            max_selections=8
        )

        st.markdown("---")
        fecha_min_sistema = df_camel['fecha'].min()
        fecha_max_sistema = df_camel['fecha'].max()
        fecha_default_inicio = pd.Timestamp(year=2015, month=1, day=1)
        if fecha_default_inicio < fecha_min_sistema:
            fecha_default_inicio = fecha_min_sistema

        fecha_inicio_evol = st.date_input("Fecha de inicio", value=fecha_default_inicio,
                                           min_value=fecha_min_sistema, max_value=fecha_max_sistema, key='fecha_inicio_evol')
        fecha_inicio_evol = pd.Timestamp(fecha_inicio_evol)

    with col2:
        if bancos_evol:
            crear_grafico_evolucion(df_camel, indicador_codigo_evol, bancos_evol, indicador_nombre_evol, fecha_inicio_evol)
        else:
            st.info("Selecciona al menos un banco para ver la evolución")

with tab3:
    col1, col2 = st.columns([1, 3])
    with col1:
        categoria_heat = st.selectbox("Categoría", list(INDICADORES_PRINCIPALES.keys()), key='cat_heat')
        indicadores_heat = INDICADORES_PRINCIPALES[categoria_heat]
        indicador_opciones_heat = {nombre: codigo for codigo, nombre in indicadores_heat}
        indicador_nombre_heat = st.selectbox("Indicador", list(indicador_opciones_heat.keys()), key='ind_heat')
        indicador_codigo_heat = indicador_opciones_heat[indicador_nombre_heat]

        st.markdown("---")
        st.subheader("Rango de Fechas")
        anos_disponibles = sorted(df_camel['fecha'].dt.year.unique())

        col_a, col_b = st.columns(2)
        with col_a:
            ano_inicio = st.selectbox("Año inicio", anos_disponibles,
                                       index=max(0, len(anos_disponibles) - 5) if len(anos_disponibles) > 5 else 0, key='ano_inicio_heat')
        with col_b:
            ano_fin = st.selectbox("Año fin", anos_disponibles, index=len(anos_disponibles) - 1, key='ano_fin_heat')

        meses = [('Enero', 1), ('Febrero', 2), ('Marzo', 3), ('Abril', 4), ('Mayo', 5), ('Junio', 6),
                 ('Julio', 7), ('Agosto', 8), ('Septiembre', 9), ('Octubre', 10), ('Noviembre', 11), ('Diciembre', 12)]
        meses_nombres = [m[0] for m in meses]
        meses_numeros = [m[1] for m in meses]

        col_c, col_d = st.columns(2)
        with col_c:
            mes_inicio_idx = st.selectbox("Mes inicio", range(len(meses)), index=0, format_func=lambda x: meses_nombres[x], key='mes_inicio_heat')
            mes_inicio = meses_numeros[mes_inicio_idx]
        with col_d:
            mes_fin_idx = st.selectbox("Mes fin", range(len(meses)), index=11, format_func=lambda x: meses_nombres[x], key='mes_fin_heat')
            mes_fin = meses_numeros[mes_fin_idx]

        fecha_inicio_heat = pd.Timestamp(year=ano_inicio, month=mes_inicio, day=1)
        fecha_fin_heat = pd.Timestamp(year=ano_fin, month=mes_fin, day=1)
        if fecha_inicio_heat > fecha_fin_heat:
            st.warning("La fecha de inicio debe ser anterior a la fecha de fin")
            fecha_inicio_heat, fecha_fin_heat = fecha_fin_heat, fecha_inicio_heat

    with col2:
        crear_heatmap_indicador_camel(df_camel, indicador_codigo_heat, indicador_nombre_heat, fecha_inicio_heat, fecha_fin_heat)

with tab4:
    st.caption("Score 0-100 por dimensión CAMEL (metodología interna de normalización — ver docs/ManualTecnico.md), "
               "comparado contra el promedio del sistema.")
    col1, col2 = st.columns([1, 3])
    with col1:
        banco_radar = st.selectbox("Banco", bancos_disponibles, key='banco_radar')

    with col2:
        score_banco = calcular_score_camel(df_camel, banco_radar, fecha_seleccionada)
        score_sistema = calcular_score_promedio_sistema(df_camel, fecha_seleccionada)
        fig_radar = crear_radar_camel(score_banco, titulo=f"CAMEL — {banco_radar}", valores_benchmark=score_sistema)
        st.plotly_chart(fig_radar, width='stretch')
