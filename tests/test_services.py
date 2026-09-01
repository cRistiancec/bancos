# -*- coding: utf-8 -*-
"""Tests de services/ (carga de datos y motor del asistente) sobre datos reales."""

from services.assistant_engine import AsistenteDeterministico, ProveedorLLM


class TestDataService:
    def test_balance_tiene_columnas_esperadas(self, df_balance):
        assert set(['banco', 'fecha', 'codigo', 'cuenta', 'valor']).issubset(df_balance.columns)
        assert len(df_balance) > 0

    def test_camel_tiene_columnas_esperadas(self, df_camel):
        assert set(['banco', 'fecha', 'codigo', 'indicador', 'valor', 'categoria']).issubset(df_camel.columns)
        assert len(df_camel) > 0

    def test_valores_camel_son_fraccion(self, df_camel):
        # camel.parquet almacena los indicadores como fraccion (0-1) tipico, no ya multiplicado por 100
        sol = df_camel[df_camel['codigo'] == 'SOL']['valor']
        assert sol.median() < 1.0


class TestAsistenteDeterministico:
    def test_responde_valor_puntual_con_numero_real(self, df_camel):
        asistente = AsistenteDeterministico(df_camel)
        banco = df_camel['banco'].iloc[0]
        respuesta = asistente.responder(f"¿Cuál es la solvencia de {banco}?")
        assert banco in respuesta
        assert "%" in respuesta

    def test_pregunta_sin_indicador_no_inventa_respuesta(self, df_camel):
        asistente = AsistenteDeterministico(df_camel)
        respuesta = asistente.responder("cuéntame un chiste")
        assert "no reconocí" in respuesta.lower()

    def test_pregunta_vacia(self, df_camel):
        asistente = AsistenteDeterministico(df_camel)
        respuesta = asistente.responder("")
        assert isinstance(respuesta, str) and len(respuesta) > 0

    def test_proveedor_llm_no_implementado(self):
        proveedor = ProveedorLLM(proveedor="openai")
        try:
            proveedor.responder("cualquier pregunta")
            assert False, "ProveedorLLM deberia levantar NotImplementedError"
        except NotImplementedError:
            pass
