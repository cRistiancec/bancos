# -*- coding: utf-8 -*-
"""
Deteccion de anomalias sobre series reales de indicadores, usando
Isolation Forest (sklearn.ensemble.IsolationForest) sobre el nivel y la
variacion mes a mes de la serie -- captura tanto niveles atipicos como
cambios abruptos. No es un sistema de alertas regulatorio; es una
herramienta exploratoria sobre los datos historicos reales.
"""

import pandas as pd
from sklearn.ensemble import IsolationForest

MINIMO_PUNTOS = 12


class SerieInsuficiente(Exception):
    pass


def detectar_anomalias(fechas: pd.Series, valores: pd.Series, contaminacion: float = 0.05) -> pd.DataFrame:
    """Returns: DataFrame [fecha, valor, variacion, anomalia (bool)]"""
    df = pd.DataFrame({'fecha': pd.to_datetime(fechas), 'valor': valores}).dropna().sort_values('fecha')
    df = df.drop_duplicates(subset='fecha').reset_index(drop=True)

    if len(df) < MINIMO_PUNTOS:
        raise SerieInsuficiente(f"Se requieren al menos {MINIMO_PUNTOS} periodos con dato; hay {len(df)}.")

    df['variacion'] = df['valor'].diff().fillna(0)

    modelo = IsolationForest(contamination=contaminacion, random_state=42)
    df['anomalia'] = modelo.fit_predict(df[['valor', 'variacion']].values) == -1

    return df
