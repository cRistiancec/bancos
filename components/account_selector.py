# -*- coding: utf-8 -*-
"""
Selector jerarquico de cuentas contables (1 -> 2 -> 4 -> 6 digitos).

Extraido de pages/2_Balance_General.py, donde este mismo bloque (~150
lineas) estaba copiado 3 veces (Evolucion Comparativa, Heatmap, Ranking).
Misma logica de construccion de jerarquia y de cascada de selectbox; unico
cambio es que ahora recibe un key_prefix para poder usarse varias veces en
una misma pagina sin colisionar.
"""

import pandas as pd
import streamlit as st


@st.cache_data
def construir_jerarquia_cuentas(df: pd.DataFrame) -> dict:
    """
    Construye un diccionario jerarquico de cuentas.
    Retorna: {codigo_1d: {nombre, subcuentas: {codigo_2d: {nombre, subcuentas: {codigo_4d: {nombre, subcuentas: {codigo_6d: nombre}}}}}}}

    Migrado sin cambios desde 2_Balance_General.py::obtener_jerarquia_cuentas.
    """
    cuentas = df[['codigo', 'cuenta']].drop_duplicates()
    cuentas = cuentas[cuentas['codigo'].str.match(r'^[0-9]+$', na=False)]

    jerarquia = {}

    for _, row in cuentas[cuentas['codigo'].str.len() == 1].iterrows():
        if row['codigo'] in ['1', '2', '3', '6', '7']:
            jerarquia[row['codigo']] = {'nombre': row['cuenta'], 'subcuentas': {}}

    for _, row in cuentas[cuentas['codigo'].str.len() == 2].iterrows():
        parent = row['codigo'][0]
        if parent in jerarquia:
            jerarquia[parent]['subcuentas'][row['codigo']] = {'nombre': row['cuenta'], 'subcuentas': {}}

    for _, row in cuentas[cuentas['codigo'].str.len() == 4].iterrows():
        parent_1d = row['codigo'][0]
        parent_2d = row['codigo'][:2]
        if parent_1d in jerarquia and parent_2d in jerarquia[parent_1d]['subcuentas']:
            jerarquia[parent_1d]['subcuentas'][parent_2d]['subcuentas'][row['codigo']] = {
                'nombre': row['cuenta'], 'subcuentas': {}
            }

    for _, row in cuentas[cuentas['codigo'].str.len() == 6].iterrows():
        parent_1d = row['codigo'][0]
        parent_2d = row['codigo'][:2]
        parent_4d = row['codigo'][:4]
        if (parent_1d in jerarquia and
                parent_2d in jerarquia[parent_1d]['subcuentas'] and
                parent_4d in jerarquia[parent_1d]['subcuentas'][parent_2d]['subcuentas']):
            jerarquia[parent_1d]['subcuentas'][parent_2d]['subcuentas'][parent_4d]['subcuentas'][row['codigo']] = row['cuenta']

    return jerarquia


def seleccionar_cuenta_jerarquica(jerarquia: dict, key_prefix: str, columnas=None) -> str:
    """Renderiza la cascada Categoria -> Grupo -> Subcuenta -> Detalle y
    retorna el codigo contable final seleccionado (1, 2, 4 o 6 digitos).

    Args:
        jerarquia: salida de construir_jerarquia_cuentas()
        key_prefix: prefijo unico de widget key para poder repetir este
            selector varias veces en la misma pagina sin colisionar.
        columnas: lista de 4 st.columns ya creadas, o None para crearlas aqui.
    """
    if columnas is None:
        columnas = st.columns(4)
    col_n1, col_n2, col_n3, col_n4 = columnas

    opciones_nivel1 = {f"{k} - {v['nombre']}": k for k, v in jerarquia.items()}

    with col_n1:
        nivel1_label = st.selectbox(
            "Categoría", options=list(opciones_nivel1.keys()), index=0, key=f"{key_prefix}_n1"
        )
        codigo_nivel1 = opciones_nivel1[nivel1_label]

    subcuentas_nivel2 = jerarquia[codigo_nivel1]['subcuentas']
    opciones_nivel2 = {"Todas (agregado)": codigo_nivel1}
    for k, v in subcuentas_nivel2.items():
        opciones_nivel2[f"{k} - {v['nombre']}"] = k

    with col_n2:
        nivel2_label = st.selectbox(
            "Grupo", options=list(opciones_nivel2.keys()), index=0, key=f"{key_prefix}_n2"
        )
        codigo_nivel2 = opciones_nivel2[nivel2_label]

    codigo_cuenta_final = codigo_nivel2

    with col_n3:
        if codigo_nivel2 != codigo_nivel1 and codigo_nivel2 in subcuentas_nivel2:
            subcuentas_nivel3 = subcuentas_nivel2[codigo_nivel2]['subcuentas']
            if subcuentas_nivel3:
                opciones_nivel3 = {"Todas (agregado)": codigo_nivel2}
                for k, v in subcuentas_nivel3.items():
                    label = f"{k} - {v['nombre']}" if isinstance(v, dict) else f"{k} - {str(v)}"
                    opciones_nivel3[label] = k

                nivel3_label = st.selectbox(
                    "Subcuenta", options=list(opciones_nivel3.keys()), index=0, key=f"{key_prefix}_n3"
                )
                codigo_nivel3 = opciones_nivel3[nivel3_label]
                codigo_cuenta_final = codigo_nivel3
            else:
                codigo_nivel3 = codigo_nivel2
                st.selectbox("Subcuenta", options=["N/A"], disabled=True, key=f"{key_prefix}_n3_disabled")
        else:
            codigo_nivel3 = codigo_nivel2
            st.selectbox("Subcuenta", options=["N/A"], disabled=True, key=f"{key_prefix}_n3_disabled2")

    with col_n4:
        if (codigo_nivel3 != codigo_nivel2 and
                codigo_nivel2 != codigo_nivel1 and
                codigo_nivel2 in subcuentas_nivel2 and
                codigo_nivel3 in subcuentas_nivel2[codigo_nivel2]['subcuentas'] and
                isinstance(subcuentas_nivel2[codigo_nivel2]['subcuentas'][codigo_nivel3], dict)):
            subcuentas_nivel4 = subcuentas_nivel2[codigo_nivel2]['subcuentas'][codigo_nivel3]['subcuentas']
            if subcuentas_nivel4:
                opciones_nivel4 = {"Todas (agregado)": codigo_nivel3}
                for k, v in subcuentas_nivel4.items():
                    opciones_nivel4[f"{k} - {str(v)}"] = k

                nivel4_label = st.selectbox(
                    "Detalle", options=list(opciones_nivel4.keys()), index=0, key=f"{key_prefix}_n4"
                )
                codigo_cuenta_final = opciones_nivel4[nivel4_label]
            else:
                st.selectbox("Detalle", options=["N/A"], disabled=True, key=f"{key_prefix}_n4_disabled")
        else:
            st.selectbox("Detalle", options=["N/A"], disabled=True, key=f"{key_prefix}_n4_disabled2")

    return codigo_cuenta_final
