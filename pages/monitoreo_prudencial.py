# -*- coding: utf-8 -*-
"""
Monitoreo Prudencial — tablero de ratios prudenciales clave por banco, con
semaforo de umbral (analytics.camel_scoring, mismos umbrales ya definidos en
config.indicator_mapping.RANGOS_INDICADORES).

Pagina nueva (Fase 1), 100% datos reales de camel.parquet.
"""

import streamlit as st
import pandas as pd

from ui.layout import render_page
from services.data_service import cargar_camel, obtener_fechas_disponibles
from analytics.camel_scoring import obtener_valor_indicador, clasificar_semaforo, CODIGO_A_TIPO_RANGO
from config.indicator_mapping import ETIQUETAS_INDICADORES

render_page("Monitoreo Prudencial", icono="🛡️")

st.title("Monitoreo Prudencial")
st.markdown("Ratios prudenciales centrales por banco, clasificados con los umbrales de alerta/crítico "
            "ya definidos en `config/indicator_mapping.py`.")

try:
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

fechas = obtener_fechas_disponibles(df_camel)
fecha_sel = st.selectbox("Fecha de análisis", options=fechas, format_func=lambda x: x.strftime('%B %Y').title(), index=0)

bancos = sorted(df_camel['banco'].unique())
codigos = list(CODIGO_A_TIPO_RANGO.keys())  # SOL, MOR_TOT, COB_TOT, ROE, ROA, LIQ


@st.cache_data
def construir_tablero(df_camel: pd.DataFrame, bancos: list, codigos: list, fecha) -> pd.DataFrame:
    filas = []
    for banco in bancos:
        fila = {'Banco': banco}
        for codigo in codigos:
            valor = obtener_valor_indicador(df_camel, banco, codigo, fecha)
            valor_pct = valor * 100 if valor is not None else None
            fila[codigo] = valor_pct
            fila[f"{codigo}_sev"] = clasificar_semaforo(valor_pct, codigo)
        filas.append(fila)
    return pd.DataFrame(filas)


tablero = construir_tablero(df_camel, bancos, codigos, fecha_sel)

# --- Resumen de severidad ---
st.markdown("### Resumen del sistema")
cols = st.columns(len(codigos))
for col, codigo in zip(cols, codigos):
    with col:
        criticos = (tablero[f"{codigo}_sev"] == 'CRITICO').sum()
        alertas = (tablero[f"{codigo}_sev"] == 'ALERTA').sum()
        st.metric(ETIQUETAS_INDICADORES.get(codigo, codigo), f"{criticos} crít. / {alertas} alerta")

st.markdown("---")
st.markdown("### Tablero por banco")

tabla_display = tablero[['Banco'] + codigos].copy()
for codigo in codigos:
    tabla_display[codigo] = tablero[codigo].apply(lambda v: f"{v:.2f}%" if pd.notna(v) else "N/D")
tabla_display.columns = ['Banco'] + [ETIQUETAS_INDICADORES.get(c, c) for c in codigos]


def _color_por_severidad(row):
    estilos = ['']
    for codigo in codigos:
        sev = tablero.loc[row.name, f"{codigo}_sev"]
        color = {'OK': 'background-color: rgba(27,138,90,0.25)',
                 'ALERTA': 'background-color: rgba(232,135,30,0.25)',
                 'CRITICO': 'background-color: rgba(193,39,45,0.30)',
                 'SIN_DATO': ''}.get(sev, '')
        estilos.append(color)
    return estilos


st.dataframe(
    tabla_display.style.apply(_color_por_severidad, axis=1),
    hide_index=True, width='stretch', height=min(700, 60 + 35 * len(tabla_display))
)

st.caption("🟢 Normal · 🟠 Alerta · 🔴 Crítico — según umbrales de config/indicator_mapping.RANGOS_INDICADORES. "
           "N/D indica que el banco no reporta ese indicador en la fecha seleccionada.")
