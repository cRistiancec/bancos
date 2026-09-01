# -*- coding: utf-8 -*-
"""Tests de models/ (forecasting, anomaly_detection, clustering) sobre datos reales."""

import pandas as pd
import pytest

from analytics.camel_explorer import serie_promedio_sistema
from models.forecasting import proyectar_serie, SerieInsuficiente as ForecastInsuficiente
from models.anomaly_detection import detectar_anomalias, SerieInsuficiente as AnomaliaInsuficiente
from models.clustering import clusterizar_bancos


class TestForecasting:
    def test_proyeccion_devuelve_historico_y_proyeccion(self, df_camel):
        serie = serie_promedio_sistema(df_camel, 'ROA')
        resultado = proyectar_serie(serie['fecha'], serie['valor_pct'], n_periodos=6)

        assert (resultado['tipo'] == 'historico').sum() == len(serie)
        assert (resultado['tipo'] == 'proyeccion').sum() == 6

    def test_banda_se_ensancha_con_el_horizonte(self, df_camel):
        serie = serie_promedio_sistema(df_camel, 'ROA')
        resultado = proyectar_serie(serie['fecha'], serie['valor_pct'], n_periodos=6)
        fore = resultado[resultado['tipo'] == 'proyeccion'].reset_index(drop=True)

        anchos = (fore['banda_sup'] - fore['banda_inf']).tolist()
        assert anchos == sorted(anchos)  # no decrece con el horizonte

    def test_serie_corta_lanza_excepcion(self):
        fechas = pd.date_range('2024-01-31', periods=5, freq='ME')
        valores = pd.Series([1.0, 1.1, 1.2, 1.1, 1.0])
        with pytest.raises(ForecastInsuficiente):
            proyectar_serie(fechas, valores, n_periodos=3)


class TestAnomalyDetection:
    def test_deteccion_produce_subconjunto_minoritario(self, df_camel):
        serie = serie_promedio_sistema(df_camel, 'ROA')
        resultado = detectar_anomalias(serie['fecha'], serie['valor_pct'], contaminacion=0.05)

        assert 'anomalia' in resultado.columns
        assert resultado['anomalia'].sum() > 0
        assert resultado['anomalia'].sum() < len(resultado) * 0.5

    def test_serie_corta_lanza_excepcion(self):
        fechas = pd.date_range('2024-01-31', periods=5, freq='ME')
        valores = pd.Series([1.0, 1.1, 1.2, 1.1, 1.0])
        with pytest.raises(AnomaliaInsuficiente):
            detectar_anomalias(fechas, valores)


class TestClustering:
    def test_clustering_produce_multiples_grupos(self, df_camel, fecha_max_camel):
        resultado = clusterizar_bancos(df_camel, fecha_max_camel, ['SOL', 'MOR_TOT', 'ROA', 'LIQ'], n_clusters=3)
        assert not resultado.empty
        assert resultado['cluster'].nunique() > 1
        assert resultado['cluster'].nunique() <= 3

    def test_pocos_bancos_con_dato_devuelve_vacio(self, df_camel, fecha_max_camel):
        # Codigo que no existe en camel.parquet -> ningun banco tiene dato completo
        resultado = clusterizar_bancos(df_camel, fecha_max_camel, ['CODIGO_INEXISTENTE'], n_clusters=3)
        assert resultado.empty
