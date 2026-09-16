# -*- coding: utf-8 -*-
"""
Evolución Histórica — explorador temporal unificado sobre los 3 datasets
(Balance, P&G, CAMEL), con modos Absoluto/Indexado/Participación donde aplica.

Pagina nueva (Fase 1). Consolida en un solo lugar el patron de "Evolucion
Comparativa" que estaba implementado de forma independiente en Balance
General y Perdidas y Ganancias.
"""

import streamlit as st
import plotly.graph_objects as go

from ui.layout import render_page
from services.data_service import cargar_balance, cargar_pyg, cargar_camel
from components.account_selector import construir_jerarquia_cuentas, seleccionar_cuenta_jerarquica
from components.mode_selector import render_selector_modo, calcular_serie_modo
from analytics.camel_explorer import obtener_evolucion
from config.indicator_mapping import obtener_color_banco, INDICADORES_PRINCIPALES
from config.theme_tokens import COLORES

render_page("Evolución Histórica", icono="📉")

st.title("Evolución Histórica")
st.markdown("Explorador temporal unificado sobre Balance, Pérdidas y Ganancias e Indicadores CAMEL.")

CUENTAS_PYG = {
    'MNI': 'Margen Neto de Intereses', 'MBF': 'Margen Bruto Financiero', 'MNF': 'Margen Neto Financiero',
    'MDI': 'Margen de Intermediación', 'MOP': 'Margen Operacional', 'GAI': 'Ganancia Antes de Impuestos',
    'GDE': 'Ganancia del Ejercicio',
}
BANCOS_DEFAULT = ['Pichincha', 'Pacifico', 'Guayaquil', 'Produbanco']

dataset_sel = st.radio("Fuente de datos", options=["Balance General", "Pérdidas y Ganancias", "Indicadores CAMEL"], horizontal=True)
st.markdown("---")


def _selector_bancos(bancos_disponibles, key):
    default = [b for b in BANCOS_DEFAULT if b in bancos_disponibles] or bancos_disponibles[:4]
    return st.multiselect("Bancos a comparar (hasta 10)", options=bancos_disponibles, default=default, max_selections=10, key=key)


if dataset_sel == "Balance General":
    try:
        df_balance, _ = cargar_balance()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.stop()

    jerarquia = construir_jerarquia_cuentas(df_balance)
    st.markdown("**Cuenta:**")
    codigo = seleccionar_cuenta_jerarquica(jerarquia, key_prefix="evolhist_bal")

    bancos = sorted(df_balance['banco'].unique())
    bancos_sel = _selector_bancos(bancos, "evolhist_bal_bancos")
    modo, incluir_sistema = render_selector_modo("evolhist_bal")

    if bancos_sel:
        fig = go.Figure()
        serie_sistema = None
        if modo == "Participación %" or incluir_sistema:
            serie_sistema = df_balance[df_balance['codigo'] == codigo].groupby('fecha')['valor'].sum().reset_index()
            serie_sistema['valor_millones'] = serie_sistema['valor'] / 1000

        for banco in bancos_sel:
            serie = df_balance[(df_balance['banco'] == banco) & (df_balance['codigo'] == codigo)].copy().sort_values('fecha')
            if serie.empty:
                continue
            serie['valor_millones'] = serie['valor'] / 1000
            x, y, y_label = calcular_serie_modo(serie, serie_sistema, modo, value_col='valor_millones')
            fig.add_trace(go.Scatter(x=x, y=y, name=banco, mode='lines', line=dict(width=2, color=obtener_color_banco(banco))))

        fig.update_layout(height=480, yaxis_title=y_label if bancos_sel else "", hovermode='x unified',
                           legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
                           paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']))
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Selecciona al menos un banco.")

elif dataset_sel == "Pérdidas y Ganancias":
    try:
        df_pyg, _ = cargar_pyg()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.stop()

    df_pyg = df_pyg[df_pyg['valor_12m'].notna()]
    cuenta_label = st.selectbox("Indicador", options=[f"{k} - {v}" for k, v in CUENTAS_PYG.items()], index=6)
    codigo = cuenta_label.split(' - ')[0]

    bancos = sorted(df_pyg['banco'].unique())
    bancos_sel = _selector_bancos(bancos, "evolhist_pyg_bancos")
    modo, incluir_sistema = render_selector_modo("evolhist_pyg")

    if bancos_sel:
        fig = go.Figure()
        serie_sistema = None
        if modo == "Participación %" or incluir_sistema:
            serie_sistema = df_pyg[df_pyg['codigo'] == codigo].groupby('fecha')['valor_12m'].sum().reset_index()
            serie_sistema['valor_millones'] = serie_sistema['valor_12m'] / 1000

        for banco in bancos_sel:
            serie = df_pyg[(df_pyg['banco'] == banco) & (df_pyg['codigo'] == codigo)].copy().sort_values('fecha')
            if serie.empty:
                continue
            serie['valor_millones'] = serie['valor_12m'] / 1000
            x, y, y_label = calcular_serie_modo(serie, serie_sistema, modo, value_col='valor_millones')
            fig.add_trace(go.Scatter(x=x, y=y, name=banco, mode='lines', line=dict(width=2, color=obtener_color_banco(banco))))

        fig.update_layout(height=480, yaxis_title=y_label if bancos_sel else "", hovermode='x unified',
                           legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
                           paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']))
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Selecciona al menos un banco.")

else:  # CAMEL
    try:
        df_camel, _ = cargar_camel()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.stop()

    categoria = st.selectbox("Categoría", options=list(INDICADORES_PRINCIPALES.keys()))
    opciones = {nombre: cod for cod, nombre in INDICADORES_PRINCIPALES[categoria]}
    indicador_nombre = st.selectbox("Indicador", options=list(opciones.keys()))
    codigo = opciones[indicador_nombre]

    bancos = sorted(df_camel['banco'].unique())
    bancos_sel = _selector_bancos(bancos, "evolhist_camel_bancos")

    if bancos_sel:
        df_evol = obtener_evolucion(df_camel, codigo, bancos_sel)
        fig = go.Figure()
        for banco in bancos_sel:
            serie = df_evol[df_evol['banco'] == banco]
            fig.add_trace(go.Scatter(x=serie['fecha'], y=serie['valor_pct'], name=banco, mode='lines',
                                      line=dict(width=2, color=obtener_color_banco(banco))))
        fig.update_layout(height=480, yaxis_title="%", hovermode='x unified',
                           legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
                           paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']))
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Selecciona al menos un banco.")
