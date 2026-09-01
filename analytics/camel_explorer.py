# -*- coding: utf-8 -*-
"""
Consultas genericas reutilizables sobre camel.parquet: ranking, evolucion y
heatmap para un codigo de indicador dado. Usado por las paginas de Riesgo de
Credito/Liquidez/Solvencia/Concentracion y Ranking de Bancos, para no
reimplementar el mismo patron de consulta en cada pagina.
"""

import pandas as pd
import streamlit as st


@st.cache_data
def obtener_ranking(df_camel: pd.DataFrame, codigo: str, fecha) -> pd.DataFrame:
    """Ranking de bancos para un indicador en una fecha exacta.
    Returns: DataFrame [banco, valor_pct] ordenado descendente.
    """
    df_filtrado = df_camel[(df_camel['codigo'] == codigo) & (df_camel['fecha'] == fecha)].copy()
    if df_filtrado.empty:
        return pd.DataFrame(columns=['banco', 'valor_pct'])
    df_filtrado['valor_pct'] = df_filtrado['valor'] * 100
    return df_filtrado[['banco', 'valor_pct']].sort_values('valor_pct', ascending=False)


@st.cache_data
def obtener_evolucion(df_camel: pd.DataFrame, codigo: str, bancos: list) -> pd.DataFrame:
    """Serie temporal de un indicador para varios bancos.
    Returns: DataFrame [banco, fecha, valor_pct]
    """
    df_filtrado = df_camel[(df_camel['codigo'] == codigo) & (df_camel['banco'].isin(bancos))].copy()
    df_filtrado['valor_pct'] = df_filtrado['valor'] * 100
    return df_filtrado[['banco', 'fecha', 'valor_pct']].sort_values(['banco', 'fecha'])


@st.cache_data
def obtener_heatmap(df_camel: pd.DataFrame, codigo: str, fecha_inicio=None, fecha_fin=None) -> pd.DataFrame:
    """Matriz banco x periodo (Año-Mes) para un indicador."""
    df_filtrado = df_camel[df_camel['codigo'] == codigo].copy()
    if fecha_inicio is not None:
        df_filtrado = df_filtrado[df_filtrado['fecha'] >= fecha_inicio]
    if fecha_fin is not None:
        df_filtrado = df_filtrado[df_filtrado['fecha'] <= fecha_fin]
    if df_filtrado.empty:
        return pd.DataFrame()

    df_filtrado['periodo'] = df_filtrado['fecha'].dt.strftime('%Y-%m')
    return df_filtrado.pivot_table(index='banco', columns='periodo', values='valor', aggfunc='first', observed=True) * 100


@st.cache_data
def serie_promedio_sistema(df_camel: pd.DataFrame, codigo: str) -> pd.DataFrame:
    """Promedio simple entre bancos de un indicador, por fecha."""
    df_ind = df_camel[df_camel['codigo'] == codigo]
    serie = df_ind.groupby('fecha')['valor'].mean().reset_index()
    serie['valor_pct'] = serie['valor'] * 100
    return serie.sort_values('fecha')
