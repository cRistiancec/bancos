# -*- coding: utf-8 -*-
"""Tests de analytics/ sobre datos reales de master_data/."""

import pytest

from analytics.concentracion import calcular_participacion_mercado, calcular_hhi, calcular_cr_n, clasificar_hhi
from analytics.camel_scoring import clasificar_semaforo, calcular_score_camel, obtener_valor_indicador
from analytics.early_warning import generar_alertas, resumen_alertas
from analytics.systemic_index import calcular_contribucion_sistemica
from analytics.stress_testing import ESCENARIOS, aplicar_escenario, resumen_escenario
from config.indicator_mapping import CODIGOS_BALANCE


class TestConcentracion:
    def test_participacion_suma_100(self, df_balance, fecha_max_balance):
        ranking = calcular_participacion_mercado(df_balance, fecha_max_balance, CODIGOS_BALANCE['activo_total'], top_n=50)
        assert not ranking.empty
        assert ranking['participacion'].sum() == pytest.approx(100.0, abs=0.1)

    def test_hhi_en_rango_valido(self, df_balance, fecha_max_balance):
        ranking = calcular_participacion_mercado(df_balance, fecha_max_balance, CODIGOS_BALANCE['activo_total'], top_n=50)
        hhi = calcular_hhi(ranking)
        # HHI teorico: minimo ~0 (mercado infinitamente fragmentado), maximo 10000 (monopolio)
        assert 0 < hhi <= 10000

    def test_cr5_menor_o_igual_cr10(self, df_balance, fecha_max_balance):
        ranking = calcular_participacion_mercado(df_balance, fecha_max_balance, CODIGOS_BALANCE['activo_total'], top_n=50)
        cr5 = calcular_cr_n(ranking, 5)
        cr10 = calcular_cr_n(ranking, 10)
        assert cr5 <= cr10

    def test_clasificar_hhi_umbrales(self):
        assert clasificar_hhi(1000) == "No concentrado"
        assert clasificar_hhi(2000) == "Moderadamente concentrado"
        assert clasificar_hhi(3000) == "Altamente concentrado"


class TestCamelScoring:
    def test_semaforo_solvencia_critico(self):
        assert clasificar_semaforo(8.0, 'SOL') == 'CRITICO'   # <= 9
        assert clasificar_semaforo(10.0, 'SOL') == 'ALERTA'   # <= 12
        assert clasificar_semaforo(15.0, 'SOL') == 'OK'

    def test_semaforo_morosidad_direccion_invertida(self):
        # Para morosidad, mayor valor = peor (a diferencia de solvencia)
        assert clasificar_semaforo(12.0, 'MOR_TOT') == 'CRITICO'  # >= 10
        assert clasificar_semaforo(6.0, 'MOR_TOT') == 'ALERTA'    # >= 5
        assert clasificar_semaforo(1.0, 'MOR_TOT') == 'OK'

    def test_semaforo_sin_dato(self):
        assert clasificar_semaforo(None, 'SOL') == 'SIN_DATO'
        assert clasificar_semaforo(10.0, 'CODIGO_INEXISTENTE') == 'SIN_DATO'

    def test_score_camel_en_rango_0_100(self, df_camel, fecha_max_camel):
        banco = df_camel['banco'].iloc[0]
        scores = calcular_score_camel(df_camel, banco, fecha_max_camel)
        assert set(scores.keys()) == {'C', 'A', 'M', 'E', 'L'}
        for v in scores.values():
            assert 0 <= v <= 100

    def test_obtener_valor_indicador_banco_inexistente(self, df_camel, fecha_max_camel):
        assert obtener_valor_indicador(df_camel, 'Banco Que No Existe', 'SOL', fecha_max_camel) is None


class TestEarlyWarning:
    def test_alertas_solo_incluyen_alerta_y_critico(self, df_camel):
        df_alertas = generar_alertas(df_camel)
        if not df_alertas.empty:
            assert set(df_alertas['severidad'].unique()).issubset({'ALERTA', 'CRITICO'})

    def test_resumen_alertas_consistente(self, df_camel):
        df_alertas = generar_alertas(df_camel)
        resumen = resumen_alertas(df_alertas)
        assert resumen['total'] == resumen['criticas'] + resumen['alertas']
        assert resumen['total'] == len(df_alertas)


class TestSystemicIndex:
    def test_contribucion_no_negativa(self, df_balance, df_camel, fecha_max_balance, fecha_max_camel):
        df_contrib = calcular_contribucion_sistemica(df_balance, df_camel, fecha_max_balance, fecha_max_camel)
        assert not df_contrib.empty
        assert (df_contrib['contribucion'] >= 0).all()
        assert (df_contrib['tamaño_pct'] >= 0).all() & (df_contrib['tamaño_pct'] <= 100).all()
        assert (df_contrib['estres'] >= 0).all() & (df_contrib['estres'] <= 100).all()


class TestStressTesting:
    def test_escenarios_escalan_severidad(self, df_camel, fecha_max_camel):
        """Crisis Sistemica debe producir al menos tantos bancos en CRITICO
        como Severo, que a su vez debe producir al menos tantos como Adverso."""
        conteos = {}
        for nombre, shock in ESCENARIOS.items():
            resultado = aplicar_escenario(df_camel, fecha_max_camel, shock['morosidad_pp'], shock['solvencia_pp'], shock['roa_pp'])
            conteos[nombre] = resumen_escenario(resultado)['criticos_post']

        assert conteos['Adverso'] <= conteos['Severo'] <= conteos['Crisis Sistémica']

    def test_shock_cero_no_cambia_severidad(self, df_camel, fecha_max_camel):
        resultado = aplicar_escenario(df_camel, fecha_max_camel, 0.0, 0.0, 0.0)
        assert (resultado['severidad_pre'] == resultado['severidad_post']).all()
