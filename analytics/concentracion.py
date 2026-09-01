# -*- coding: utf-8 -*-
"""
Indicadores de concentracion de mercado (HHI, CR5, CR10).

calcular_hhi() migra sin cambios la formula de
pages/1_Panorama.py::calcular_concentracion_hhi (antes definida pero nunca
renderizada). CR5/CR10 usan la misma base de participacion de mercado.
"""

import pandas as pd
import streamlit as st


@st.cache_data
def calcular_participacion_mercado(df: pd.DataFrame, fecha, codigo: str, top_n: int = 50) -> pd.DataFrame:
    """Ranking de bancos por una cuenta, con participacion de mercado (%).

    Misma base de calculo que obtener_ranking_bancos() en 1_Panorama.py:
    ordena por valor descendente y limita a top_n (por defecto 50, es decir
    practicamente todos los bancos del sistema).
    """
    df_fecha = df[(df['fecha'] == fecha) & (df['codigo'] == codigo)]

    if df_fecha.empty:
        return pd.DataFrame()

    ranking = df_fecha[['banco', 'valor']].copy()
    ranking['valor_millones'] = ranking['valor'] / 1000
    ranking = ranking.sort_values('valor', ascending=False).head(top_n)

    total = ranking['valor'].sum()
    ranking['participacion'] = (ranking['valor'] / total) * 100 if total > 0 else 0

    return ranking


def calcular_hhi(ranking: pd.DataFrame) -> float:
    """Indice Herfindahl-Hirschman sobre una tabla de participacion de mercado.

    Formula identica a la de 1_Panorama.py::calcular_concentracion_hhi:
    suma de las participaciones (en %) al cuadrado.
    """
    if ranking.empty or 'participacion' not in ranking.columns:
        return 0.0
    return float((ranking['participacion'] ** 2).sum())


def calcular_cr_n(ranking: pd.DataFrame, n: int) -> float:
    """Ratio de concentracion CR-N: suma de participacion de los N bancos
    mas grandes (ranking ya debe venir ordenado descendente por valor).
    """
    if ranking.empty or 'participacion' not in ranking.columns:
        return 0.0
    return float(ranking.head(n)['participacion'].sum())


def clasificar_hhi(hhi: float) -> str:
    """Clasificacion estandar de mercado segun HHI (umbrales de referencia
    usados habitualmente en analisis de competencia: <1500 no concentrado,
    1500-2500 moderadamente concentrado, >2500 altamente concentrado).
    """
    if hhi < 1500:
        return "No concentrado"
    if hhi < 2500:
        return "Moderadamente concentrado"
    return "Altamente concentrado"
