# -*- coding: utf-8 -*-
"""
Stress Testing — sensibilidad de morosidad/solvencia/ROA a escenarios
hipotéticos (Fase 2).

Esto NO es un VaR de mercado ni un stress test regulatorio (requeriría
datos de mercado y modelos de capital que no existen en el pipeline — ver
docs/AUDITORIA_COMPLETA.md sección 6). Es un ejercicio de sensibilidad de
balance/resultados: se toma el valor real más reciente de cada banco y se le
aplica un shock (en puntos porcentuales) definido explícitamente por el
usuario, reclasificando con los mismos umbrales de
analytics.camel_scoring.clasificar_semaforo ya usados en toda la plataforma.

Los escenarios preconfigurados (ESCENARIOS) son supuestos de trabajo, no
cifras oficiales, y se calibraron sobre la distribución real de los
indicadores (ver docs/ManualTecnico.md) para que efectivamente muevan
bancos entre severidades -- son editables en la UI.
"""

import pandas as pd
import streamlit as st

from analytics.camel_scoring import obtener_valor_indicador, clasificar_semaforo

ESCENARIOS = {
    'Adverso': {'morosidad_pp': 2.0, 'solvencia_pp': -1.0, 'roa_pp': -0.5},
    'Severo': {'morosidad_pp': 5.0, 'solvencia_pp': -2.5, 'roa_pp': -1.5},
    'Crisis Sistémica': {'morosidad_pp': 8.0, 'solvencia_pp': -4.0, 'roa_pp': -3.0},
}

ORDEN_SEVERIDAD = {'CRITICO': 3, 'ALERTA': 2, 'OK': 1, 'SIN_DATO': 0}


def _peor_severidad(severidades: list) -> str:
    validas = [s for s in severidades if s != 'SIN_DATO']
    if not validas:
        return 'SIN_DATO'
    return max(validas, key=lambda s: ORDEN_SEVERIDAD[s])


@st.cache_data
def aplicar_escenario(df_camel: pd.DataFrame, fecha, shock_morosidad_pp: float,
                       shock_solvencia_pp: float, shock_roa_pp: float) -> pd.DataFrame:
    """Aplica el shock a MOR_TOT/SOL/ROA de cada banco y compara severidad
    antes vs. despues.

    Returns: DataFrame [banco, mor_pre, mor_post, sol_pre, sol_post,
    roa_pre, roa_post, severidad_pre, severidad_post]
    """
    bancos = sorted(df_camel['banco'].unique())
    filas = []

    for banco in bancos:
        mor = obtener_valor_indicador(df_camel, banco, 'MOR_TOT', fecha)
        sol = obtener_valor_indicador(df_camel, banco, 'SOL', fecha)
        roa = obtener_valor_indicador(df_camel, banco, 'ROA', fecha)

        mor_pre = mor * 100 if mor is not None else None
        sol_pre = sol * 100 if sol is not None else None
        roa_pre = roa * 100 if roa is not None else None

        mor_post = mor_pre + shock_morosidad_pp if mor_pre is not None else None
        sol_post = sol_pre + shock_solvencia_pp if sol_pre is not None else None
        roa_post = roa_pre + shock_roa_pp if roa_pre is not None else None

        severidad_pre = _peor_severidad([
            clasificar_semaforo(mor_pre, 'MOR_TOT'),
            clasificar_semaforo(sol_pre, 'SOL'),
            clasificar_semaforo(roa_pre, 'ROA'),
        ])
        severidad_post = _peor_severidad([
            clasificar_semaforo(mor_post, 'MOR_TOT'),
            clasificar_semaforo(sol_post, 'SOL'),
            clasificar_semaforo(roa_post, 'ROA'),
        ])

        filas.append({
            'banco': banco,
            'mor_pre': mor_pre, 'mor_post': mor_post,
            'sol_pre': sol_pre, 'sol_post': sol_post,
            'roa_pre': roa_pre, 'roa_post': roa_post,
            'severidad_pre': severidad_pre, 'severidad_post': severidad_post,
        })

    return pd.DataFrame(filas)


def resumen_escenario(df_resultado: pd.DataFrame) -> dict:
    """Conteo de bancos por severidad antes/despues, y cuantos empeoraron."""
    conteo_pre = df_resultado['severidad_pre'].value_counts().to_dict()
    conteo_post = df_resultado['severidad_post'].value_counts().to_dict()

    empeoraron = (
        df_resultado['severidad_post'].map(ORDEN_SEVERIDAD) >
        df_resultado['severidad_pre'].map(ORDEN_SEVERIDAD)
    ).sum()

    return {
        'criticos_pre': conteo_pre.get('CRITICO', 0), 'criticos_post': conteo_post.get('CRITICO', 0),
        'alerta_pre': conteo_pre.get('ALERTA', 0), 'alerta_post': conteo_post.get('ALERTA', 0),
        'empeoraron': int(empeoraron),
    }
