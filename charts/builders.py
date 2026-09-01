# -*- coding: utf-8 -*-
"""
Componentes graficos reutilizables (Plotly), tema oscuro institucional.

Migrado de utils/charts.py sin alterar ninguna formula/estructura de datos
de las figuras. Los unicos cambios son de estilo (fondo transparente, tipografia
y paleta institucional en vez de fondo blanco) para adaptarse al tema oscuro,
y la incorporacion de crear_sparkline() (pieza nueva, solicitada para KPIs
ejecutivos con mini-tendencia).
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Optional, Dict, Any

from config.indicator_mapping import obtener_color_banco
from config.theme_tokens import COLORES

COLORES_CHART = {
    'primario': COLORES['azul_institucional'],
    'secundario': COLORES['azul_petroleo'],
    'acento': COLORES['azul_info'],
    'exito': COLORES['verde'],
    'advertencia': COLORES['naranja'],
    'error': COLORES['rojo'],
    'neutro': COLORES['texto_secundario'],
    'fondo': COLORES['fondo_panel'],
}

PALETA_BANCOS = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel1

LAYOUT_BASE = {
    'font': {'family': 'Inter, sans-serif', 'color': COLORES['texto_primario']},
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'margin': {'l': 10, 'r': 10, 't': 40, 'b': 10},
}


# =============================================================================
# FUNCIONES DE COLORES
# =============================================================================

def obtener_colores_para_bancos(bancos: List[str]) -> Dict[str, str]:
    """Diccionario {banco: color} para una lista de bancos."""
    return {banco: obtener_color_banco(banco) for banco in bancos}


def aplicar_colores_bancos(fig, bancos: List[str], trace_index: int = 0):
    """Aplica colores consistentes a las trazas de un grafico Plotly."""
    colores = [obtener_color_banco(banco) for banco in bancos]

    if trace_index == 0:
        for i, trace in enumerate(fig.data):
            if i < len(colores):
                trace.marker.color = colores[i]
    else:
        fig.data[trace_index].marker.color = colores


# =============================================================================
# GRAFICOS DE RANKING
# =============================================================================

def crear_ranking_barras(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    titulo: str = "",
    color_col: Optional[str] = None,
    formato_valor: str = "${:,.0f}M",
    altura: int = 400,
    usar_colores_bancos: bool = True
) -> go.Figure:
    """Grafico de barras horizontales para ranking."""
    df_sorted = df.sort_values(x_col, ascending=True)

    if usar_colores_bancos and y_col == 'banco':
        colors = [obtener_color_banco(banco) for banco in df_sorted[y_col]]
        marker_dict = dict(color=colors)
    elif color_col:
        colors = df_sorted[color_col]
        marker_dict = dict(color=colors, colorscale='Blues')
    else:
        colors = df_sorted[x_col]
        marker_dict = dict(color=colors, colorscale='Blues')

    fig = go.Figure(go.Bar(
        y=df_sorted[y_col],
        x=df_sorted[x_col],
        orientation='h',
        marker=marker_dict,
        text=[formato_valor.format(v) for v in df_sorted[x_col]],
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>Valor: %{x:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=titulo,
        height=altura,
        xaxis_title="",
        yaxis_title="",
        yaxis=dict(categoryorder='total ascending'),
        showlegend=False
    )

    return fig


# =============================================================================
# TREEMAP
# =============================================================================

def crear_treemap(
    df: pd.DataFrame,
    path_col: str = None,
    values_col: str = None,
    color_col: Optional[str] = None,
    titulo: str = "",
    altura: int = 450,
    jerarquico: bool = False
) -> go.Figure:
    """Treemap de composicion. jerarquico=True espera columnas
    'labels','parents','values'; jerarquico=False usa path_col/values_col.
    """
    df_clean = df.copy()

    if jerarquico:
        required_cols = ['labels', 'parents', 'values']
        if not all(col in df_clean.columns for col in required_cols):
            fig = go.Figure()
            fig.add_annotation(text="Estructura de datos incorrecta", xref="paper", yref="paper",
                                x=0.5, y=0.5, showarrow=False, font=dict(size=16))
            fig.update_layout(height=altura, title=titulo)
            return fig

        df_clean = df_clean.dropna(subset=['values'])
        df_clean = df_clean[df_clean['values'] > 0]

        if df_clean.empty:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos disponibles", xref="paper", yref="paper",
                                x=0.5, y=0.5, showarrow=False, font=dict(size=16))
            fig.update_layout(height=altura, title=titulo)
            return fig

        labels = df_clean['labels'].tolist()
        parents = df_clean['parents'].tolist()
        values = df_clean['values'].tolist()
        ids = df_clean['id'].tolist() if 'id' in df_clean.columns else None
        colors = df_clean['participacion'].tolist() if 'participacion' in df_clean.columns else values

        customdata = []
        for i, row in df_clean.iterrows():
            if row['parents'] == '':
                customdata.append([row['participacion']] if 'participacion' in df_clean.columns else [0])
            else:
                customdata.append([0])

        texttemplate = "%{label}<br>$%{value:,.0f}M"
        if 'participacion' in df_clean.columns:
            hovertemplate = "<b>%{label}</b><br>Valor: $%{value:,.0f}M<br>Participación: %{customdata[0]:.1f}%<extra></extra>"
        else:
            hovertemplate = "<b>%{label}</b><br>Valor: $%{value:,.0f}M<extra></extra>"

        fig = go.Figure(go.Treemap(
            labels=labels, ids=ids, parents=parents, values=values,
            marker=dict(colors=colors, colorscale='Blues', showscale=False, line=dict(width=2, color=COLORES['fondo_base'])),
            texttemplate=texttemplate,
            customdata=customdata if 'participacion' in df_clean.columns else None,
            hovertemplate=hovertemplate,
            branchvalues="total"
        ))

    else:
        df_clean = df_clean.dropna(subset=[values_col, path_col])
        df_clean = df_clean[df_clean[values_col] > 0]

        if df_clean.empty:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos disponibles", xref="paper", yref="paper",
                                x=0.5, y=0.5, showarrow=False, font=dict(size=16))
            fig.update_layout(height=altura, title=titulo)
            return fig

        labels = df_clean[path_col].tolist()
        parents = [''] * len(labels)
        values = df_clean[values_col].tolist()
        colors = df_clean[color_col].tolist() if color_col and color_col in df_clean.columns else values

        texts = []
        for i, row in df_clean.iterrows():
            texto = f"<b>{row[path_col]}</b><br>${row[values_col]:,.0f}M"
            if color_col and color_col in df_clean.columns:
                texto += f"<br>{row[color_col]:.1f}%"
            texts.append(texto)

        fig = go.Figure(go.Treemap(
            labels=labels, parents=parents, values=values,
            marker=dict(colors=colors, colorscale='Blues', showscale=True),
            text=texts, textposition='middle center',
            hovertemplate="<b>%{label}</b><br>Valor: $%{value:,.0f}M<extra></extra>"
        ))

    fig.update_layout(**LAYOUT_BASE, title=titulo, height=altura)
    return fig


# =============================================================================
# GRAFICO DE LINEAS (SERIES TEMPORALES)
# =============================================================================

def crear_linea_temporal(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    titulo: str = "",
    y_label: str = "Valor",
    altura: int = 400,
    mostrar_area: bool = False,
    usar_colores_bancos: bool = True
) -> go.Figure:
    """Grafico de lineas para series temporales."""
    if color_col:
        if usar_colores_bancos and color_col == 'banco':
            bancos = df[color_col].unique().tolist()
            color_map = obtener_colores_para_bancos(bancos)
            fig = px.line(df, x=x_col, y=y_col, color=color_col, markers=True,
                          line_shape='spline', color_discrete_map=color_map)
        else:
            fig = px.line(df, x=x_col, y=y_col, color=color_col, markers=True,
                          line_shape='spline', color_discrete_sequence=PALETA_BANCOS)
    else:
        fig = px.line(df, x=x_col, y=y_col, markers=True, line_shape='spline')
        if mostrar_area:
            fig.update_traces(fill='tozeroy', line_color=COLORES_CHART['acento'])

    fig.update_layout(
        **LAYOUT_BASE, title=titulo, height=altura, xaxis_title="", yaxis_title=y_label,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(showgrid=True, gridcolor=COLORES['borde'])
    fig.update_yaxes(showgrid=True, gridcolor=COLORES['borde'])

    return fig


def crear_sparkline(serie: pd.Series, color: str = None, altura: int = 60) -> go.Figure:
    """Mini-grafico de tendencia sin ejes, para acompañar tarjetas KPI.
    Componente nuevo (no existia en utils/charts.py original).
    """
    color = color or COLORES_CHART['acento']
    fig = go.Figure(go.Scatter(
        y=serie, mode='lines', line=dict(width=2, color=color),
        fill='tozeroy', fillcolor='rgba(49, 130, 206, 0.15)',
        hoverinfo='skip',
    ))
    fig.update_layout(
        height=altura, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


# =============================================================================
# GRAFICO RADAR (CAMEL)
# =============================================================================

def crear_radar_camel(
    valores: Dict[str, float],
    titulo: str = "",
    valores_benchmark: Optional[Dict[str, float]] = None,
    altura: int = 400
) -> go.Figure:
    """Radar de indicadores CAMEL. valores: dict con keys C,A,M,E,L (0-100)."""
    categorias = ['Capital (C)', 'Activos (A)', 'Management (M)', 'Earnings (E)', 'Liquidity (L)']
    keys = ['C', 'A', 'M', 'E', 'L']

    r_valores = [valores.get(k, 0) for k in keys]
    r_valores.append(r_valores[0])
    categorias_cerradas = categorias + [categorias[0]]

    fig = go.Figure()

    if valores_benchmark:
        r_bench = [valores_benchmark.get(k, 0) for k in keys]
        r_bench.append(r_bench[0])
        fig.add_trace(go.Scatterpolar(
            r=r_bench, theta=categorias_cerradas, fill='toself',
            fillcolor='rgba(49, 130, 206, 0.12)',
            line=dict(color=COLORES_CHART['acento'], width=1, dash='dash'),
            name='Promedio Sistema'
        ))

    fig.add_trace(go.Scatterpolar(
        r=r_valores, theta=categorias_cerradas, fill='toself',
        fillcolor='rgba(27, 138, 90, 0.28)',
        line=dict(color=COLORES_CHART['exito'], width=2),
        name='Banco'
    ))

    fig.update_layout(
        **LAYOUT_BASE, title=titulo, height=altura,
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=COLORES['borde']),
            angularaxis=dict(gridcolor=COLORES['borde']),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )

    return fig


# =============================================================================
# GAUGE (INDICADOR TIPO VELOCIMETRO)
# =============================================================================

def crear_gauge(
    valor: float,
    titulo: str = "",
    min_val: float = 0,
    max_val: float = 100,
    umbrales: Optional[List[Dict]] = None,
    altura: int = 250
) -> go.Figure:
    """Indicador tipo gauge. umbrales: lista de dicts {'rango': (a,b), 'color': hex}."""
    if umbrales is None:
        umbrales = [
            {'rango': (0, 33), 'color': 'rgba(193,39,45,0.35)'},
            {'rango': (33, 66), 'color': 'rgba(232,135,30,0.35)'},
            {'rango': (66, 100), 'color': 'rgba(27,138,90,0.35)'},
        ]

    color_barra = COLORES_CHART['neutro']
    for umbral in umbrales:
        if umbral['rango'][0] <= valor <= umbral['rango'][1]:
            if 'rgba(27,138,90' in umbral['color']:
                color_barra = COLORES_CHART['exito']
            elif 'rgba(232,135,30' in umbral['color']:
                color_barra = COLORES_CHART['advertencia']
            else:
                color_barra = COLORES_CHART['error']

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        title={'text': titulo, 'font': {'size': 14, 'color': COLORES['texto_primario']}},
        number={'font': {'color': COLORES['texto_primario']}},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickcolor': COLORES['texto_secundario']},
            'bar': {'color': color_barra},
            'bgcolor': 'rgba(0,0,0,0)',
            'steps': [{'range': u['rango'], 'color': u['color']} for u in umbrales],
        }
    ))

    fig.update_layout(**LAYOUT_BASE, height=altura)
    return fig


# =============================================================================
# HEATMAP
# =============================================================================

def crear_heatmap(
    df: pd.DataFrame,
    titulo: str = "",
    color_scale: str = 'Blues',
    altura: int = 400,
    mostrar_valores: bool = True
) -> go.Figure:
    """Heatmap a partir de un DataFrame pivotado."""
    fig = px.imshow(df, color_continuous_scale=color_scale, aspect='auto')

    if mostrar_valores:
        fig.update_traces(text=df.values, texttemplate="%{text:.1f}", textfont={"size": 10})

    fig.update_layout(**LAYOUT_BASE, title=titulo, height=altura)
    return fig


# =============================================================================
# SCATTER PLOT (MATRIZ DE POSICIONAMIENTO)
# =============================================================================

def crear_scatter_posicionamiento(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    size_col: str,
    label_col: str,
    x_label: str = "",
    y_label: str = "",
    titulo: str = "",
    altura: int = 500
) -> go.Figure:
    """Dispersion para posicionamiento estrategico."""
    fig = px.scatter(
        df, x=x_col, y=y_col, size=size_col, text=label_col, color=size_col,
        color_continuous_scale='Blues', size_max=60,
    )

    fig.update_traces(
        textposition='top center', textfont=dict(size=10, color=COLORES['texto_primario']),
        hovertemplate=(f"<b>%{{text}}</b><br>{x_label}: %{{x:.2f}}<br>{y_label}: %{{y:.2f}}<br>"
                       f"Tamaño: %{{marker.size:,.0f}}<extra></extra>")
    )

    x_mean = df[x_col].mean()
    y_mean = df[y_col].mean()
    fig.add_hline(y=y_mean, line_dash="dash", line_color=COLORES_CHART['neutro'], opacity=0.5)
    fig.add_vline(x=x_mean, line_dash="dash", line_color=COLORES_CHART['neutro'], opacity=0.5)

    fig.update_layout(**LAYOUT_BASE, title=titulo, height=altura, xaxis_title=x_label, yaxis_title=y_label)
    return fig


# =============================================================================
# BARRAS APILADAS (ESTRUCTURA DE BALANCE)
# =============================================================================

def crear_barras_apiladas_100(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str,
    titulo: str = "",
    altura: int = 300
) -> go.Figure:
    """Barras apiladas al 100%."""
    fig = px.bar(df, x=x_col, y=y_col, color=color_col, barmode='stack',
                 color_discrete_sequence=PALETA_BANCOS, text_auto='.1f')

    fig.update_layout(
        **LAYOUT_BASE, title=titulo, height=altura, xaxis_title="", yaxis_title="Porcentaje (%)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    return fig
