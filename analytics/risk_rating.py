# -*- coding: utf-8 -*-
"""
Calificación de Riesgo Consolidada (Fase 3) — rating A-E por banco.

Metodología propia (no regulatoria, no es una calificación crediticia
oficial), compuesta de 2 factores -- deliberadamente NO 3:

    score_final = 0.7 * score_camel + 0.3 * score_resiliencia

- score_camel (70%): salud actual del banco, promedio de las 5 dimensiones
  de analytics.camel_scoring.calcular_score_camel (ya validado, reutilizado
  tal cual).
- score_resiliencia (30%): colchón ante estrés, usando el escenario
  "Adverso" de analytics.stress_testing (severidad_post mapeada a numero:
  OK=100, ALERTA=50, CRITICO=0). Se eligió "Adverso" y no "Severo"/"Crisis
  Sistémica" tras verificar empíricamente la distribución de severidad de
  cada escenario sobre los datos reales: "Severo" deja a 21/24 bancos en
  CRITICO (satura, casi no discrimina entre bancos) y "Crisis Sistémica" a
  los 24/24 (no discrimina nada); "Adverso" reparte los bancos entre OK/
  ALERTA/CRITICO de forma mucho más informativa (11/10/3 en los datos
  verificados) -- es el que realmente sirve para comparar resiliencia
  relativa entre bancos, que es el propósito de este componente.

Se excluye a propósito la "contribución al índice sistémico"
(analytics.systemic_index): esa métrica responde una pregunta distinta
("¿qué tanto le importaría al sistema si este banco cae?", que depende del
TAMAÑO del banco) y mezclarla en la calificación individual penalizaría a
bancos grandes por su tamaño, no por su salud. El Índice Sistémico sigue
disponible como página separada. Ver docs/ManualTecnico.md.
"""

import pandas as pd
import streamlit as st

from analytics.camel_scoring import calcular_score_camel
from analytics.stress_testing import ESCENARIOS, aplicar_escenario

PESO_CAMEL = 0.7
PESO_RESILIENCIA = 0.3
ESCENARIO_RESILIENCIA = 'Adverso'

SEVERIDAD_A_SCORE = {'OK': 100.0, 'ALERTA': 50.0, 'CRITICO': 0.0}

BANDAS_CALIFICACION = [
    (80, 'A'), (60, 'B'), (40, 'C'), (20, 'D'), (0, 'E'),
]


def _letra_calificacion(score: float) -> str:
    for umbral, letra in BANDAS_CALIFICACION:
        if score >= umbral:
            return letra
    return 'E'


@st.cache_data
def calcular_calificaciones_sistema(df_camel: pd.DataFrame, fecha) -> pd.DataFrame:
    """Calificación A-E para todos los bancos en una fecha.

    Returns: DataFrame [banco, score_camel, score_resiliencia, score_final,
    calificacion], ordenado descendente por score_final.
    """
    shock = ESCENARIOS[ESCENARIO_RESILIENCIA]
    df_stress = aplicar_escenario(df_camel, fecha, shock['morosidad_pp'], shock['solvencia_pp'], shock['roa_pp'])
    resiliencia_por_banco = dict(zip(df_stress['banco'], df_stress['severidad_post']))

    bancos = sorted(df_camel['banco'].unique())
    filas = []

    for banco in bancos:
        scores_camel = calcular_score_camel(df_camel, banco, fecha)
        score_camel = sum(scores_camel.values()) / len(scores_camel)

        severidad_resiliencia = resiliencia_por_banco.get(banco, 'SIN_DATO')
        score_resiliencia = SEVERIDAD_A_SCORE.get(severidad_resiliencia)
        if score_resiliencia is None:
            continue  # sin dato suficiente para evaluar resiliencia -- no se inventa un valor

        score_final = PESO_CAMEL * score_camel + PESO_RESILIENCIA * score_resiliencia

        filas.append({
            'banco': banco,
            'score_camel': round(score_camel, 1),
            'score_resiliencia': round(score_resiliencia, 1),
            'score_final': round(score_final, 1),
            'calificacion': _letra_calificacion(score_final),
        })

    return pd.DataFrame(filas).sort_values('score_final', ascending=False)


def calcular_calificacion_banco(df_camel: pd.DataFrame, banco: str, fecha) -> dict:
    """Calificación de un solo banco (reutiliza el cálculo por lotes)."""
    df = calcular_calificaciones_sistema(df_camel, fecha)
    fila = df[df['banco'] == banco]
    if fila.empty:
        return {}
    return fila.iloc[0].to_dict()
