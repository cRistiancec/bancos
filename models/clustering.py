# -*- coding: utf-8 -*-
"""
Clustering de bancos por perfil de indicadores CAMEL, usando K-Means sobre
valores estandarizados (sklearn.cluster.KMeans) y PCA a 2 componentes solo
para visualizar (sklearn.decomposition.PCA). Metodologia exploratoria, no
una clasificacion regulatoria de riesgo.
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from analytics.camel_scoring import obtener_valor_indicador


def clusterizar_bancos(df_camel: pd.DataFrame, fecha, codigos: list, n_clusters: int = 3) -> pd.DataFrame:
    """Agrupa bancos con dato disponible en TODOS los `codigos` en la fecha
    dada (no se imputan valores faltantes -- un banco sin dato completo
    simplemente no entra en el análisis, no se asume un valor para él).

    Returns: DataFrame [banco, <codigos...>, cluster, pc1, pc2]
    """
    bancos = sorted(df_camel['banco'].unique())
    filas = []

    for banco in bancos:
        valores = {}
        completo = True
        for codigo in codigos:
            v = obtener_valor_indicador(df_camel, banco, codigo, fecha)
            if v is None:
                completo = False
                break
            valores[codigo] = v * 100
        if completo:
            valores['banco'] = banco
            filas.append(valores)

    if len(filas) < n_clusters + 1:
        return pd.DataFrame()

    df = pd.DataFrame(filas).set_index('banco')
    X = StandardScaler().fit_transform(df[codigos])

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X)

    coords = PCA(n_components=2, random_state=42).fit_transform(X)

    resultado = df.reset_index()
    resultado['cluster'] = clusters.astype(str)
    resultado['pc1'] = coords[:, 0]
    resultado['pc2'] = coords[:, 1]

    return resultado
