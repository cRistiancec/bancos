# -*- coding: utf-8 -*-
"""
Motor de alertas tempranas basado en reglas.

Aplica los umbrales alerta/critico ya definidos en
config.indicator_mapping.RANGOS_INDICADORES (via analytics.camel_scoring)
a la ultima fecha disponible de cada banco, para los 6 indicadores
prudenciales centrales que ya existen en camel.parquet. No usa modelos
predictivos ni datos sinteticos: es una lectura directa de reglas de umbral
sobre datos reales, equivalente a un semaforo de supervision.
"""

import pandas as pd
import streamlit as st
from typing import Optional

from config.indicator_mapping import ETIQUETAS_INDICADORES
from analytics.camel_scoring import clasificar_semaforo, CODIGO_A_TIPO_RANGO

INDICADORES_MONITOREADOS = list(CODIGO_A_TIPO_RANGO.keys())  # SOL, MOR_TOT, COB_TOT, ROE, ROA, LIQ


@st.cache_data
def generar_alertas(df_camel: pd.DataFrame, fecha: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """Genera la lista de alertas (ALERTA/CRITICO) para todos los bancos en
    la fecha indicada (o la mas reciente disponible por banco/indicador si
    fecha=None).

    Returns:
        DataFrame con columnas: banco, codigo, indicador, fecha, valor_pct, severidad
    """
    filas = []

    for codigo in INDICADORES_MONITOREADOS:
        df_ind = df_camel[df_camel['codigo'] == codigo]
        if df_ind.empty:
            continue

        if fecha is not None:
            df_fecha = df_ind[df_ind['fecha'] == fecha]
        else:
            # Ultima fecha disponible para este indicador especifico
            ultima_fecha = df_ind['fecha'].max()
            df_fecha = df_ind[df_ind['fecha'] == ultima_fecha]

        for _, row in df_fecha.iterrows():
            valor_pct = row['valor'] * 100
            severidad = clasificar_semaforo(valor_pct, codigo)
            if severidad in ('ALERTA', 'CRITICO'):
                filas.append({
                    'banco': row['banco'],
                    'codigo': codigo,
                    'indicador': ETIQUETAS_INDICADORES.get(codigo, codigo),
                    'fecha': row['fecha'],
                    'valor_pct': valor_pct,
                    'severidad': severidad,
                })

    if not filas:
        return pd.DataFrame(columns=['banco', 'codigo', 'indicador', 'fecha', 'valor_pct', 'severidad'])

    df_alertas = pd.DataFrame(filas)
    orden_severidad = {'CRITICO': 0, 'ALERTA': 1}
    df_alertas['orden'] = df_alertas['severidad'].map(orden_severidad)
    df_alertas = df_alertas.sort_values(['orden', 'banco']).drop(columns='orden')

    return df_alertas


def resumen_alertas(df_alertas: pd.DataFrame) -> dict:
    """Conteo de alertas por severidad, para KPIs/semaforo general."""
    if df_alertas.empty:
        return {'criticas': 0, 'alertas': 0, 'total': 0, 'bancos_afectados': 0}

    return {
        'criticas': int((df_alertas['severidad'] == 'CRITICO').sum()),
        'alertas': int((df_alertas['severidad'] == 'ALERTA').sum()),
        'total': len(df_alertas),
        'bancos_afectados': df_alertas['banco'].nunique(),
    }
