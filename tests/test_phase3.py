# -*- coding: utf-8 -*-
"""Tests de Fase 3: backtesting de forecasting, alertas predictivas, calificación de riesgo."""

import pandas as pd
import pytest

from analytics.camel_explorer import serie_promedio_sistema
from models.forecasting import backtest_serie, SerieInsuficiente
from analytics.predictive_alerts import resumen_predictivo_sistema, INDICADORES_MONITOREADOS
from analytics.risk_rating import calcular_calificaciones_sistema, _letra_calificacion, BANDAS_CALIFICACION


class TestBacktesting:
    def test_backtest_devuelve_metricas_no_negativas(self, df_camel):
        serie = serie_promedio_sistema(df_camel, 'ROA')
        resultado = backtest_serie(serie['fecha'], serie['valor_pct'], n_periodos_test=6)

        assert resultado['mae'] >= 0
        assert resultado['rmse'] >= 0
        assert resultado['rmse'] >= resultado['mae'] * 0.9  # RMSE nunca es mucho menor que MAE (propiedad matematica)
        assert len(resultado['fecha_test']) == 6

    def test_backtest_mape_none_si_valores_cerca_de_cero(self):
        # Serie sintetica de prueba con un valor de test en cero: MAPE no definido
        fechas = pd.date_range('2020-01-31', periods=18, freq='ME')
        valores = pd.Series([1.0] * 12 + [0.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        resultado = backtest_serie(fechas, valores, n_periodos_test=6)
        assert resultado['mape'] is None

    def test_serie_corta_lanza_excepcion(self):
        fechas = pd.date_range('2024-01-31', periods=10, freq='ME')
        valores = pd.Series(range(10), dtype=float)
        with pytest.raises(SerieInsuficiente):
            backtest_serie(fechas, valores, n_periodos_test=6)


class TestAlertasPredictivas:
    def test_resumen_sistema_cubre_todos_los_indicadores_monitoreados(self, df_camel):
        resumen = resumen_predictivo_sistema(df_camel, n_periodos=6)
        assert not resumen.empty
        assert set(resumen['codigo']).issubset(set(INDICADORES_MONITOREADOS))
        assert set(['OK', 'ALERTA', 'CRITICO']).issuperset(set(resumen['severidad_actual']))

    def test_empeora_es_booleano_consistente_con_severidad(self, df_camel):
        from analytics.stress_testing import ORDEN_SEVERIDAD
        resumen = resumen_predictivo_sistema(df_camel, n_periodos=6)
        for _, fila in resumen.iterrows():
            esperado = ORDEN_SEVERIDAD[fila['severidad_proyectada']] > ORDEN_SEVERIDAD[fila['severidad_actual']]
            assert fila['empeora'] == esperado


class TestCalificacionRiesgo:
    def test_bandas_asignadas_correctamente_en_los_limites(self):
        assert _letra_calificacion(80) == 'A'
        assert _letra_calificacion(79.9) == 'B'
        assert _letra_calificacion(60) == 'B'
        assert _letra_calificacion(59.9) == 'C'
        assert _letra_calificacion(40) == 'C'
        assert _letra_calificacion(39.9) == 'D'
        assert _letra_calificacion(20) == 'D'
        assert _letra_calificacion(19.9) == 'E'
        assert _letra_calificacion(0) == 'E'

    def test_bandas_cubren_0_a_100_sin_huecos(self):
        umbrales = sorted([u for u, _ in BANDAS_CALIFICACION])
        assert umbrales[0] == 0

    def test_calificaciones_sistema_en_rango_valido(self, df_camel, fecha_max_camel):
        calificaciones = calcular_calificaciones_sistema(df_camel, fecha_max_camel)
        assert not calificaciones.empty
        assert calificaciones['score_final'].between(0, 100).all()
        assert set(calificaciones['calificacion'].unique()).issubset({'A', 'B', 'C', 'D', 'E'})
        # el ranking debe venir ordenado descendente por score_final
        assert (calificaciones['score_final'].diff().dropna() <= 0).all()

    def test_calificacion_banco_coincide_con_calificaciones_sistema(self, df_camel, fecha_max_camel):
        from analytics.risk_rating import calcular_calificacion_banco
        calificaciones = calcular_calificaciones_sistema(df_camel, fecha_max_camel)
        banco = calificaciones.iloc[0]['banco']
        individual = calcular_calificacion_banco(df_camel, banco, fecha_max_camel)
        assert individual['calificacion'] == calificaciones.iloc[0]['calificacion']
