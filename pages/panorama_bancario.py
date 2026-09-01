# -*- coding: utf-8 -*-
"""
Panorama Bancario — vision general del sistema bancario ecuatoriano.

Migrado desde pages/1_Panorama.py (Fase 1 del refactor institucional).
Todas las formulas de calculo (KPIs, treemap jerarquico, ranking, crecimiento
YoY) se preservan sin cambios; unicamente se parametriza el bloque de
crecimiento anual (antes duplicado para cartera y depositos) y se conecta a
la nueva arquitectura compartida (services/components/charts/ui).
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from ui.layout import render_page
from services.data_service import cargar_balance, obtener_fechas_disponibles, calcular_metricas_sistema
from components.kpi_card import render_kpi_card
from charts.builders import crear_ranking_barras, crear_treemap
from config.indicator_mapping import CODIGOS_BALANCE
from config.theme_tokens import COLORES

render_page("Panorama Bancario", icono="📊")


# =============================================================================
# FUNCIONES DE CALCULO (migradas sin cambios desde 1_Panorama.py)
# =============================================================================

@st.cache_data
def obtener_ranking_bancos(df: pd.DataFrame, fecha, codigo: str, top_n: int = 10) -> pd.DataFrame:
    """Obtiene ranking de bancos por cuenta especifica."""
    df_fecha = df[(df['fecha'] == fecha) & (df['codigo'] == codigo)]

    if df_fecha.empty:
        return pd.DataFrame()

    ranking = df_fecha[['banco', 'valor']].copy()
    ranking['valor_millones'] = ranking['valor'] / 1000
    ranking = ranking.sort_values('valor', ascending=False).head(top_n)

    return ranking


@st.cache_data
def obtener_datos_treemap_jerarquico(df: pd.DataFrame, fecha, tipo='activos') -> pd.DataFrame:
    """Prepara datos jerarquicos para treemap con drill-down de 2 niveles."""
    df_fecha = df[(df['fecha'] == fecha)]

    registros = []

    if tipo == 'activos':
        cuentas_nivel2 = {
            '11': 'Fondos Disponibles', '13': 'Inversiones', '14': 'Cartera de Creditos',
            '16': 'Cuentas por Cobrar', '17': 'Bienes Realizables',
            '18': 'Propiedades y Equipo', '19': 'Otros Activos'
        }

        activos_totales = df_fecha[df_fecha['codigo'] == '1']
        for _, row in activos_totales.iterrows():
            if pd.notna(row['valor']) and row['valor'] > 0:
                registros.append({'labels': row['banco'], 'parents': '', 'values': row['valor'] / 1000,
                                   'tipo': 'banco', 'id': row['banco']})

        for codigo, nombre in cuentas_nivel2.items():
            df_cuenta = df_fecha[df_fecha['codigo'] == codigo]
            for _, row in df_cuenta.iterrows():
                if pd.notna(row['valor']) and row['valor'] > 0:
                    registros.append({'labels': nombre, 'parents': row['banco'], 'values': row['valor'] / 1000,
                                       'tipo': 'cuenta_nivel2', 'id': f"{row['banco']}_{nombre}"})

    elif tipo == 'pasivos':
        cuentas_nivel2 = {
            '21': 'Obligaciones con el Publico', '25': 'Cuentas por Pagar',
            '26': 'Obligaciones Financieras', '27': 'Valores en Circulacion',
            '29': 'Otros Pasivos', '3': 'Patrimonio'
        }

        for _, row_banco in df_fecha[df_fecha['codigo'] == '1'].iterrows():
            banco = row_banco['banco']
            valor_pasivo = df_fecha[(df_fecha['banco'] == banco) & (df_fecha['codigo'] == '2')]['valor'].sum()
            valor_patrimonio = df_fecha[(df_fecha['banco'] == banco) & (df_fecha['codigo'] == '3')]['valor'].sum()
            valor_total = valor_pasivo + valor_patrimonio

            if valor_total > 0:
                registros.append({'labels': banco, 'parents': '', 'values': valor_total / 1000,
                                   'tipo': 'banco', 'id': banco})

        for codigo, nombre in cuentas_nivel2.items():
            df_cuenta = df_fecha[df_fecha['codigo'] == codigo]
            for _, row in df_cuenta.iterrows():
                if pd.notna(row['valor']) and row['valor'] > 0:
                    registros.append({'labels': nombre, 'parents': row['banco'], 'values': row['valor'] / 1000,
                                       'tipo': 'cuenta_nivel2', 'id': f"{row['banco']}_{nombre}"})

    df_tree = pd.DataFrame(registros)

    if not df_tree.empty:
        total_sistema = df_tree[df_tree['parents'] == '']['values'].sum()
        df_tree['participacion'] = (df_tree['values'] / total_sistema) * 100 if total_sistema > 0 else 0

    return df_tree


@st.cache_data
def calcular_crecimiento_anual(df: pd.DataFrame, codigo: str, fecha_actual, fecha_anterior) -> pd.DataFrame:
    """Crecimiento YoY por banco para una cuenta especifica.

    Antes duplicado casi identico para 'Cartera de Creditos' y 'Depositos del
    Publico' en 1_Panorama.py; ahora es una sola funcion parametrizada por
    codigo de cuenta (mismo calculo exacto).
    """
    df_actual = df[(df['fecha'] == fecha_actual) & (df['codigo'] == codigo)][['banco', 'valor']].copy()
    df_anterior = df[(df['fecha'] == fecha_anterior) & (df['codigo'] == codigo)][['banco', 'valor']].copy()

    df_crec = df_actual.merge(df_anterior, on='banco', suffixes=('_actual', '_anterior'))
    df_crec['crecimiento'] = (
        (df_crec['valor_actual'] - df_crec['valor_anterior']) / df_crec['valor_anterior'] * 100
    )
    return df_crec.sort_values('crecimiento', ascending=True)


def render_grafico_crecimiento(df_crec: pd.DataFrame):
    fig = go.Figure(go.Bar(
        x=df_crec['crecimiento'], y=df_crec['banco'], orientation='h',
        marker=dict(color=df_crec['crecimiento'], colorscale='RdYlGn', cmin=-10, cmax=30),
        text=df_crec['crecimiento'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside'
    ))
    fig.update_layout(
        title="Crecimiento Anual (%)", height=max(400, len(df_crec) * 20),
        xaxis_title="Crecimiento (%)", yaxis_title="", showlegend=False,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLORES['texto_primario']),
    )
    fig.add_vline(x=0, line_dash="dash", line_color=COLORES['texto_secundario'], line_width=1)
    st.plotly_chart(fig, width='stretch')


# =============================================================================
# PAGINA
# =============================================================================

st.title("Panorama Bancario")
st.markdown("Visión general del sistema financiero ecuatoriano.")

try:
    df_balance, calidad = cargar_balance()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

st.sidebar.markdown("### Configuración")
fechas = obtener_fechas_disponibles(df_balance)
fecha_seleccionada = st.sidebar.selectbox(
    "Fecha de análisis", options=fechas, format_func=lambda x: x.strftime('%B %Y').title(), index=0
)

idx_fecha = list(fechas).index(fecha_seleccionada)
fecha_anterior = fechas[idx_fecha + 12] if idx_fecha + 12 < len(fechas) else None

st.sidebar.markdown("---")
st.sidebar.markdown("**Datos disponibles:**")
st.sidebar.markdown(f"- {calidad.get('bancos', 0)} bancos")
st.sidebar.markdown(f"- {calidad.get('fechas', 0)} meses")

# --- SECCION 1: KPIs ---
st.markdown("### Indicadores del Sistema")

metricas = calcular_metricas_sistema(df_balance, fecha_seleccionada)

deltas = {}
if fecha_anterior:
    metricas_ant = calcular_metricas_sistema(df_balance, fecha_anterior)
    for key in ['total_activos', 'total_cartera', 'total_depositos', 'total_patrimonio']:
        if metricas_ant.get(key, 0) > 0:
            deltas[key] = ((metricas[key] - metricas_ant[key]) / metricas_ant[key]) * 100

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    render_kpi_card(f"${metricas['total_activos']:,.0f}M", "Total Activos",
                     delta=deltas.get('total_activos'), delta_label="vs año ant.")
with col2:
    render_kpi_card(f"${metricas['total_cartera']:,.0f}M", "Cartera Créditos",
                     delta=deltas.get('total_cartera'), delta_label="vs año ant.")
with col3:
    render_kpi_card(f"${metricas['total_depositos']:,.0f}M", "Depósitos Público",
                     delta=deltas.get('total_depositos'), delta_label="vs año ant.")
with col4:
    render_kpi_card(f"${metricas['total_patrimonio']:,.0f}M", "Patrimonio",
                     delta=deltas.get('total_patrimonio'), delta_label="vs año ant.")
with col5:
    render_kpi_card(f"{metricas['num_bancos']}", "Bancos Activos", color=COLORES['azul_info'])

st.markdown("---")

# --- SECCION 2: MAPA DE ACTIVOS ---
col_left, col_right = st.columns([2, 1])
with col_left:
    st.markdown("### Mapa de Activos por Banco")
    st.caption("Haz clic en un banco para ver la composición de sus activos")
    df_tree = obtener_datos_treemap_jerarquico(df_balance, fecha_seleccionada, tipo='activos')
    if not df_tree.empty and df_tree['values'].sum() > 0:
        st.plotly_chart(crear_treemap(df_tree, jerarquico=True, altura=500), width='stretch')
    else:
        st.warning("No hay datos de activos disponibles para esta fecha.")

with col_right:
    st.markdown("### Ranking por Activos")
    st.caption("Todos los bancos del sistema")
    ranking = obtener_ranking_bancos(df_balance, fecha_seleccionada, CODIGOS_BALANCE['activo_total'], 50)
    if not ranking.empty:
        fig_rank = crear_ranking_barras(ranking, x_col='valor_millones', y_col='banco', formato_valor="${:,.0f}M")
        fig_rank.update_layout(height=max(400, len(ranking) * 25))
        st.plotly_chart(fig_rank, width='stretch')

st.markdown("---")

# --- SECCION 3: MAPA DE PASIVOS ---
col_left2, col_right2 = st.columns([2, 1])
with col_left2:
    st.markdown("### Mapa de Pasivos y Patrimonio por Banco")
    st.caption("Haz clic en un banco para ver la composición de sus pasivos")
    df_tree_pasivos = obtener_datos_treemap_jerarquico(df_balance, fecha_seleccionada, tipo='pasivos')
    if not df_tree_pasivos.empty and df_tree_pasivos['values'].sum() > 0:
        st.plotly_chart(crear_treemap(df_tree_pasivos, jerarquico=True, altura=500), width='stretch')
    else:
        st.warning("No hay datos de pasivos disponibles para esta fecha.")

with col_right2:
    st.markdown("### Ranking por Pasivos Totales")
    st.caption("Pasivo total (sin patrimonio)")
    ranking_pasivos = obtener_ranking_bancos(df_balance, fecha_seleccionada, CODIGOS_BALANCE['pasivo_total'], 50)
    if not ranking_pasivos.empty:
        fig_rank_pas = crear_ranking_barras(ranking_pasivos, x_col='valor_millones', y_col='banco', formato_valor="${:,.0f}M")
        fig_rank_pas.update_layout(height=max(400, len(ranking_pasivos) * 25))
        st.plotly_chart(fig_rank_pas, width='stretch')

st.markdown("---")

# --- SECCION 4: CRECIMIENTO ANUAL ---
st.markdown("### Crecimiento Anual por Banco")
st.caption(f"Variación vs mismo mes del año anterior ({fecha_seleccionada.strftime('%B %Y')})")

col_cartera, col_depositos = st.columns(2)

if fecha_anterior:
    with col_cartera:
        st.markdown("**Cartera de Créditos**")
        render_grafico_crecimiento(
            calcular_crecimiento_anual(df_balance, CODIGOS_BALANCE['cartera_creditos'], fecha_seleccionada, fecha_anterior)
        )
    with col_depositos:
        st.markdown("**Depósitos del Público**")
        render_grafico_crecimiento(
            calcular_crecimiento_anual(df_balance, CODIGOS_BALANCE['obligaciones_publico'], fecha_seleccionada, fecha_anterior)
        )
else:
    st.info("No hay datos del año anterior para comparar.")
