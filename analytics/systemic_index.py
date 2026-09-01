# -*- coding: utf-8 -*-
"""
Indice Sistemico propio (metodologia interna, no regulatoria).

Fase 2. No existe en el repo una fuente de datos de exposiciones
interbancarias por contraparte, por lo que no se puede construir un mapa de
contagio real (ver docs/AUDITORIA_COMPLETA.md seccion 6). En su lugar se
construye un indice de "contribucion al riesgo sistemico" transparente:

    tamaño_banco_i   = participacion de mercado en activos totales (%)
    estres_banco_i   = promedio de:
                         - estres por morosidad  (100 - salud_morosidad)
                         - estres por solvencia   (100 - salud_solvencia)
                       usando la misma normalizacion 0-100 ya definida en
                       analytics.camel_scoring (mismos rangos de referencia
                       que el score CAMEL del radar)
    contribucion_i    = tamaño_banco_i * estres_banco_i / 100
    indice_sistema     = suma de contribucion_i sobre todos los bancos con dato

Es un indice RELATIVO (no acotado a un maximo regulatorio tipo Basilea/BIS):
sirve para comparar bancos entre si y el sistema a lo largo del tiempo, no
para compararse contra un estandar internacional.
"""

import pandas as pd
import streamlit as st

from analytics.concentracion import calcular_participacion_mercado
from analytics.camel_scoring import obtener_valor_indicador, _normalizar_0_100
from config.indicator_mapping import CODIGOS_BALANCE

RANGO_MOROSIDAD = (0, 10)   # mismo rango de referencia que camel_scoring.DIMENSIONES_CAMEL['A']
RANGO_SOLVENCIA = (0, 20)   # mismo rango de referencia que camel_scoring.DIMENSIONES_CAMEL['C']


@st.cache_data
def calcular_contribucion_sistemica(df_balance: pd.DataFrame, df_camel: pd.DataFrame, fecha_balance, fecha_camel) -> pd.DataFrame:
    """Contribucion al indice sistemico por banco, para una fecha.

    Returns: DataFrame [banco, tamaño_pct, estres, contribucion] ordenado
    descendente por contribucion.
    """
    tamaños = calcular_participacion_mercado(df_balance, fecha_balance, CODIGOS_BALANCE['activo_total'], top_n=50)
    if tamaños.empty:
        return pd.DataFrame(columns=['banco', 'tamaño_pct', 'estres', 'contribucion'])

    filas = []
    for _, row in tamaños.iterrows():
        banco = row['banco']
        tamaño_pct = row['participacion']

        mor = obtener_valor_indicador(df_camel, banco, 'MOR_TOT', fecha_camel)
        sol = obtener_valor_indicador(df_camel, banco, 'SOL', fecha_camel)

        estres_componentes = []
        if mor is not None:
            salud_mor = _normalizar_0_100(mor * 100, RANGO_MOROSIDAD, mayor_es_mejor=False)
            estres_componentes.append(100.0 - salud_mor)
        if sol is not None:
            salud_sol = _normalizar_0_100(sol * 100, RANGO_SOLVENCIA, mayor_es_mejor=True)
            estres_componentes.append(100.0 - salud_sol)

        if not estres_componentes:
            continue

        estres = sum(estres_componentes) / len(estres_componentes)
        contribucion = tamaño_pct * estres / 100

        filas.append({'banco': banco, 'tamaño_pct': tamaño_pct, 'estres': estres, 'contribucion': contribucion})

    df = pd.DataFrame(filas)
    return df.sort_values('contribucion', ascending=False)


@st.cache_data
def _pivotear_indicador(df_camel: pd.DataFrame, codigo: str) -> pd.DataFrame:
    """Pivote fecha x banco para un indicador, construido una sola vez (en
    vez de que cada fecha de la serie filtre el df_camel completo de nuevo).
    """
    df_ind = df_camel[df_camel['codigo'] == codigo]
    return df_ind.pivot_table(index='fecha', columns='banco', values='valor', aggfunc='first', observed=True)


@st.cache_data
def _pivotear_activos(df_balance: pd.DataFrame) -> pd.DataFrame:
    """Pivote fecha x banco de activo total, construido una sola vez.

    balance.parquet tiene ~8 millones de filas -- filtrarlo fecha por fecha
    dentro de un bucle (como hacia calcular_participacion_mercado, pensada
    para una sola fecha a la vez) es la razon por la que la serie de 36
    meses del indice sistemico tardaba ~90s. Aqui se filtra una sola vez.
    """
    df_act = df_balance[df_balance['codigo'] == CODIGOS_BALANCE['activo_total']]
    return df_act.pivot_table(index='fecha', columns='banco', values='valor', aggfunc='first', observed=True)


@st.cache_data
def calcular_indice_sistema_serie(df_balance: pd.DataFrame, df_camel: pd.DataFrame, fechas: list) -> pd.DataFrame:
    """Serie temporal del indice sistemico agregado (suma de contribuciones),
    una fecha por punto. Misma formula que calcular_contribucion_sistemica,
    pero pivotando los 3 insumos (activos, morosidad, solvencia) una sola
    vez en vez de re-filtrar los datasets completos en cada iteracion.
    """
    pivote_activos = _pivotear_activos(df_balance)
    pivote_mor = _pivotear_indicador(df_camel, 'MOR_TOT')
    pivote_sol = _pivotear_indicador(df_camel, 'SOL')

    puntos = []
    for fecha in fechas:
        if fecha not in pivote_activos.index:
            continue
        fila_activos = pivote_activos.loc[fecha].dropna()
        total_activos = fila_activos.sum()
        if total_activos <= 0:
            continue

        # Fila mas reciente <= fecha (maneja el rezago de reporte de SOL,
        # igual que analytics.camel_scoring.obtener_valor_indicador).
        fila_mor = pivote_mor.loc[:fecha].iloc[-1] if not pivote_mor.loc[:fecha].empty else None
        fila_sol = pivote_sol.loc[:fecha].iloc[-1] if not pivote_sol.loc[:fecha].empty else None

        indice = 0.0
        for banco, valor_activo in fila_activos.items():
            tamaño_pct = valor_activo / total_activos * 100
            estres_componentes = []

            if fila_mor is not None and banco in fila_mor.index and pd.notna(fila_mor[banco]):
                salud_mor = _normalizar_0_100(fila_mor[banco] * 100, RANGO_MOROSIDAD, mayor_es_mejor=False)
                estres_componentes.append(100.0 - salud_mor)
            if fila_sol is not None and banco in fila_sol.index and pd.notna(fila_sol[banco]):
                salud_sol = _normalizar_0_100(fila_sol[banco] * 100, RANGO_SOLVENCIA, mayor_es_mejor=True)
                estres_componentes.append(100.0 - salud_sol)

            if estres_componentes:
                estres = sum(estres_componentes) / len(estres_componentes)
                indice += tamaño_pct * estres / 100

        puntos.append({'fecha': fecha, 'indice': indice})

    return pd.DataFrame(puntos).sort_values('fecha')
