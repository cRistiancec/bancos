# -*- coding: utf-8 -*-
"""
Selector y calculo de modo de visualizacion: Absoluto / Indexado (Base 100) /
Participacion (%).

Extrae el patron que estaba duplicado entre pages/2_Balance_General.py y
pages/3_Perdidas_Ganancias.py. Las 3 formulas se preservan exactamente:
- Absoluto: valor tal cual.
- Indexado: valor / valor[primer periodo] * 100.
- Participacion: valor_banco / valor_sistema(mismo periodo) * 100.
"""

from typing import Optional, Tuple
import pandas as pd
import streamlit as st

MODOS = ["Valores Absolutos", "Indexado (Base 100)", "Participación %"]


def render_selector_modo(key_prefix: str) -> Tuple[str, bool]:
    """Renderiza el radio de modo + checkbox de incluir sistema.

    Returns:
        (modo, incluir_sistema)
    """
    modo = st.radio("Modo", options=MODOS, index=0, key=f"{key_prefix}_modo")
    incluir_sistema = st.checkbox("Incluir Total Sistema", value=False, key=f"{key_prefix}_sistema")
    return modo, incluir_sistema


def calcular_serie_modo(
    serie_banco: pd.DataFrame,
    serie_sistema: Optional[pd.DataFrame],
    modo: str,
    value_col: str = 'valor_millones',
) -> Tuple[pd.Series, pd.Series, str]:
    """Calcula (eje_x_fecha, eje_y_valor, etiqueta_y) para un banco segun el
    modo seleccionado.

    Args:
        serie_banco: DataFrame con columnas ['fecha', value_col], ordenado por fecha.
        serie_sistema: DataFrame con columnas ['fecha', value_col] (agregado
            del sistema). Requerido solo si modo == 'Participación %'.
        modo: uno de MODOS.
        value_col: columna de valor a usar (p.ej. 'valor_millones').
    """
    if modo == "Valores Absolutos":
        return serie_banco['fecha'], serie_banco[value_col], "Millones USD"

    if modo == "Indexado (Base 100)":
        base = serie_banco[value_col].iloc[0]
        y = (serie_banco[value_col] / base) * 100 if base and base > 0 else serie_banco[value_col]
        return serie_banco['fecha'], y, "Índice (Base 100)"

    # Participación %
    merged = serie_banco.merge(
        serie_sistema[['fecha', value_col]], on='fecha', suffixes=('', '_sistema')
    )
    y = (merged[value_col] / merged[f'{value_col}_sistema']) * 100
    return merged['fecha'], y, "Participación (%)"
