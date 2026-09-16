# -*- coding: utf-8 -*-
"""
Alertas Predictivas (Fase 3): proyecta los indicadores prudenciales N meses
hacia adelante (models.forecasting.proyectar_serie, mismo modelo ya
validado con backtesting en pages/modelos_predictivos.py) y avisa cuáles
cruzarían el umbral de alerta/crítico antes de que ocurra.

Solo se reportan casos donde la severidad PROYECTADA es peor que la
severidad ACTUAL (mismo criterio de "solo mostrar lo que cambia" que ya usa
analytics/stress_testing.py) -- no es una prediccion garantizada, es una
proyeccion estadistica sobre la misma serie que ya se valida en la pestaña
de Forecasting.
"""

import pandas as pd
import streamlit as st

from analytics.camel_scoring import clasificar_semaforo, CODIGO_A_TIPO_RANGO
from analytics.camel_explorer import obtener_evolucion, serie_promedio_sistema
from analytics.stress_testing import ORDEN_SEVERIDAD
from models.forecasting import proyectar_serie, SerieInsuficiente
from config.indicator_mapping import ETIQUETAS_INDICADORES

INDICADORES_MONITOREADOS = list(CODIGO_A_TIPO_RANGO.keys())  # SOL, MOR_TOT, COB_TOT, ROE, ROA, LIQ


def _empeora(severidad_actual: str, severidad_proyectada: str) -> bool:
    if severidad_actual == 'SIN_DATO' or severidad_proyectada == 'SIN_DATO':
        return False
    return ORDEN_SEVERIDAD[severidad_proyectada] > ORDEN_SEVERIDAD[severidad_actual]


@st.cache_data
def resumen_predictivo_sistema(df_camel: pd.DataFrame, n_periodos: int = 6) -> pd.DataFrame:
    """Proyección rápida (6 series, promedio del sistema) — para la vista
    por defecto de la página, sin el costo del detalle por banco.

    Returns: DataFrame [codigo, indicador, valor_actual, valor_proyectado,
    severidad_actual, severidad_proyectada, empeora]
    """
    filas = []
    for codigo in INDICADORES_MONITOREADOS:
        serie = serie_promedio_sistema(df_camel, codigo)
        try:
            proy = proyectar_serie(serie['fecha'], serie['valor_pct'], n_periodos=n_periodos)
        except SerieInsuficiente:
            continue

        actual = float(serie['valor_pct'].iloc[-1])
        proyectado = float(proy[proy['tipo'] == 'proyeccion']['valor'].iloc[-1])
        sev_actual = clasificar_semaforo(actual, codigo)
        sev_proy = clasificar_semaforo(proyectado, codigo)

        filas.append({
            'codigo': codigo, 'indicador': ETIQUETAS_INDICADORES.get(codigo, codigo),
            'valor_actual': actual, 'valor_proyectado': proyectado,
            'severidad_actual': sev_actual, 'severidad_proyectada': sev_proy,
            'empeora': _empeora(sev_actual, sev_proy),
        })

    return pd.DataFrame(filas)


@st.cache_data
def detalle_predictivo_bancos(df_camel: pd.DataFrame, n_periodos: int = 6) -> pd.DataFrame:
    """Proyección por banco x indicador (24 x 6 = 144 combinaciones, ~15-20s
    la primera vez). Solo se llama bajo demanda desde la UI (botón
    explícito), nunca en la carga por defecto de la página.

    Returns: DataFrame con solo los casos donde la severidad proyectada
    empeora respecto a la actual (mismos campos que resumen_predictivo_sistema
    + columna 'banco').
    """
    bancos = sorted(df_camel['banco'].unique())
    filas = []

    for banco in bancos:
        for codigo in INDICADORES_MONITOREADOS:
            serie = obtener_evolucion(df_camel, codigo, [banco])
            if serie.empty:
                continue
            try:
                proy = proyectar_serie(serie['fecha'], serie['valor_pct'], n_periodos=n_periodos)
            except SerieInsuficiente:
                continue

            actual = float(serie['valor_pct'].iloc[-1])
            proyectado = float(proy[proy['tipo'] == 'proyeccion']['valor'].iloc[-1])
            sev_actual = clasificar_semaforo(actual, codigo)
            sev_proy = clasificar_semaforo(proyectado, codigo)

            if _empeora(sev_actual, sev_proy):
                filas.append({
                    'banco': banco, 'codigo': codigo, 'indicador': ETIQUETAS_INDICADORES.get(codigo, codigo),
                    'valor_actual': actual, 'valor_proyectado': proyectado,
                    'severidad_actual': sev_actual, 'severidad_proyectada': sev_proy,
                })

    df = pd.DataFrame(filas)
    if not df.empty:
        df['orden'] = df['severidad_proyectada'].map(ORDEN_SEVERIDAD)
        df = df.sort_values(['orden', 'banco'], ascending=[False, True]).drop(columns='orden')
    return df
