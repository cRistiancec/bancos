# -*- coding: utf-8 -*-
"""
Semaforo prudencial y score CAMEL 0-100 para radar comparativo.

El semaforo (clasificar_semaforo) reutiliza directamente los umbrales
'alerta'/'critico' ya definidos en config.indicator_mapping.RANGOS_INDICADORES
(sin inventar nuevos limites regulatorios).

El score 0-100 por dimension CAMEL (para el radar de analytics/../charts
crear_radar_camel) es una normalizacion interna transparente sobre el mismo
rango de referencia [min, max] que ya usaba pages/4_CAMEL.py en
RANGOS_HEATMAP para colorear sus heatmaps -- no son cifras regulatorias,
son una escala de lectura visual documentada aqui.
"""

import pandas as pd
from typing import Optional

from config.indicator_mapping import RANGOS_INDICADORES

# Codigo CAMEL -> clave de RANGOS_INDICADORES
CODIGO_A_TIPO_RANGO = {
    'SOL': 'solvencia',
    'MOR_TOT': 'morosidad',
    'COB_TOT': 'cobertura',
    'ROE': 'roe',
    'ROA': 'roa',
    'LIQ': 'liquidez',
}

# Direccion: para estos codigos, un valor MAYOR es PEOR (el resto: mayor es mejor)
MAYOR_ES_PEOR = {'MOR_TOT'}

# Rango de referencia [min, max] y direccion para el score 0-100 por dimension
# CAMEL, reutilizando los mismos rangos de referencia visual que pages/4_CAMEL.py
# (RANGOS_HEATMAP) usaba para SOL, MOR_TOT, GO_MNF, ROE, LIQ.
DIMENSIONES_CAMEL = {
    'C': {'codigo': 'SOL', 'rango': (0, 20), 'mayor_es_mejor': True},
    'A': {'codigo': 'MOR_TOT', 'rango': (0, 10), 'mayor_es_mejor': False},
    'M': {'codigo': 'GO_MNF', 'rango': (0, 200), 'mayor_es_mejor': False},
    'E': {'codigo': 'ROE', 'rango': (-20, 30), 'mayor_es_mejor': True},
    'L': {'codigo': 'LIQ', 'rango': (0, 50), 'mayor_es_mejor': True},
}


def clasificar_semaforo(valor: Optional[float], codigo: str) -> str:
    """Clasifica un valor de indicador CAMEL en OK / ALERTA / CRITICO segun
    los umbrales ya definidos en config.indicator_mapping.RANGOS_INDICADORES.

    IMPORTANTE: `valor` debe venir en escala porcentual (valor * 100), igual
    que los umbrales de RANGOS_INDICADORES -- camel.parquet almacena los
    indicadores como fraccion (0-1).

    Retorna 'SIN_DATO' si no hay valor o no hay umbral definido para el codigo.
    """
    if valor is None or pd.isna(valor):
        return 'SIN_DATO'

    tipo = CODIGO_A_TIPO_RANGO.get(codigo)
    if tipo is None or tipo not in RANGOS_INDICADORES:
        return 'SIN_DATO'

    umbral = RANGOS_INDICADORES[tipo]
    alerta, critico = umbral['alerta'], umbral['critico']

    if codigo in MAYOR_ES_PEOR:
        if valor >= critico:
            return 'CRITICO'
        if valor >= alerta:
            return 'ALERTA'
        return 'OK'
    else:
        if valor <= critico:
            return 'CRITICO'
        if valor <= alerta:
            return 'ALERTA'
        return 'OK'


def _normalizar_0_100(valor: float, rango: tuple, mayor_es_mejor: bool) -> float:
    minimo, maximo = rango
    normalizado = (valor - minimo) / (maximo - minimo) * 100
    normalizado = max(0.0, min(100.0, normalizado))
    return normalizado if mayor_es_mejor else 100.0 - normalizado


def obtener_valor_indicador(df_camel: pd.DataFrame, banco: str, codigo: str, fecha) -> Optional[float]:
    """Valor de un indicador CAMEL para un banco en una fecha (o la fecha
    disponible mas cercana anterior, para manejar indicadores con rezago
    como Solvencia -- misma logica que 4_CAMEL.py::obtener_fecha_disponible).
    """
    df_ind = df_camel[(df_camel['banco'] == banco) & (df_camel['codigo'] == codigo)]
    if df_ind.empty:
        return None

    exacto = df_ind[df_ind['fecha'] == fecha]
    if not exacto.empty:
        return float(exacto['valor'].iloc[0])

    anteriores = df_ind[df_ind['fecha'] <= fecha].sort_values('fecha', ascending=False)
    if not anteriores.empty:
        return float(anteriores['valor'].iloc[0])

    return None


def calcular_score_camel(df_camel: pd.DataFrame, banco: str, fecha) -> dict:
    """Score 0-100 por dimension (C, A, M, E, L) para un banco en una fecha,
    listo para alimentar charts.crear_radar_camel.
    """
    scores = {}
    for dimension, cfg in DIMENSIONES_CAMEL.items():
        valor = obtener_valor_indicador(df_camel, banco, cfg['codigo'], fecha)
        if valor is None:
            scores[dimension] = 0.0
            continue
        # Los indicadores de camel.parquet estan en fraccion (0-1); los
        # rangos de referencia estan en unidades porcentuales, igual que en
        # pages/4_CAMEL.py (valor_pct = valor * 100).
        valor_pct = valor * 100
        scores[dimension] = _normalizar_0_100(valor_pct, cfg['rango'], cfg['mayor_es_mejor'])
    return scores


def calcular_score_promedio_sistema(df_camel: pd.DataFrame, fecha) -> dict:
    """Score 0-100 promedio del sistema por dimension, para usar como
    benchmark en el radar comparativo (charts.crear_radar_camel).
    """
    scores = {}
    for dimension, cfg in DIMENSIONES_CAMEL.items():
        df_ind = df_camel[df_camel['codigo'] == cfg['codigo']]
        if df_ind.empty:
            scores[dimension] = 0.0
            continue

        df_fecha = df_ind[df_ind['fecha'] == fecha]
        if df_fecha.empty:
            anteriores = df_ind[df_ind['fecha'] <= fecha]
            if anteriores.empty:
                scores[dimension] = 0.0
                continue
            fecha_usar = anteriores['fecha'].max()
            df_fecha = df_ind[df_ind['fecha'] == fecha_usar]

        promedio_pct = df_fecha['valor'].mean() * 100
        scores[dimension] = _normalizar_0_100(promedio_pct, cfg['rango'], cfg['mayor_es_mejor'])
    return scores
