# -*- coding: utf-8 -*-
"""
Asistente Inteligente de Riesgos — motor determinístico (Fase 2).

Arquitectura pluggable: `ProveedorAsistente` es la interfaz; hoy solo existe
`AsistenteDeterministico`, que reconoce patrones simples (banco + indicador +
intención) sobre palabras clave y responde SIEMPRE con un número calculado
en vivo desde camel.parquet vía analytics/ (nunca un valor inventado). No
hay ningún modelo de lenguaje involucrado. `ProveedorLLM` queda como stub
documentado para conectar OpenAI/Claude/Gemini más adelante, sin fingir una
integración que no existe.
"""

import unicodedata
from typing import Optional

import pandas as pd

from analytics.camel_scoring import obtener_valor_indicador, MAYOR_ES_PEOR
from analytics.camel_explorer import obtener_ranking, obtener_evolucion, serie_promedio_sistema
from config.indicator_mapping import BANCOS_SISTEMA, ETIQUETAS_INDICADORES

SINONIMOS_INDICADOR = {
    'solvencia': 'SOL', 'capital': 'SOL',
    'morosidad': 'MOR_TOT', 'mora': 'MOR_TOT', 'cartera vencida': 'MOR_TOT',
    'cobertura': 'COB_TOT',
    'roe': 'ROE', 'rentabilidad sobre patrimonio': 'ROE',
    'roa': 'ROA', 'rentabilidad sobre activos': 'ROA', 'rentabilidad': 'ROA',
    'liquidez': 'LIQ',
}

PALABRAS_MEJOR = ['mejor', 'mayor', 'más alto', 'maximo', 'máximo', 'top', 'lider', 'líder']
PALABRAS_PEOR = ['peor', 'menor', 'más bajo', 'minimo', 'mínimo']
PALABRAS_PROMEDIO = ['promedio', 'sistema en general', 'en general', 'del sistema']
PALABRAS_EVOLUCION = ['evolucion', 'evolución', 'tendencia', 'historico', 'histórico', 'como ha variado', 'cómo ha variado']
PALABRAS_COMPARAR = ['compara', 'comparar', 'comparacion', 'comparación', ' vs ', ' versus ']

PREGUNTAS_SUGERIDAS = [
    "¿Cuál es la solvencia de Pichincha?",
    "¿Qué banco tiene mejor ROE?",
    "¿Qué banco tiene peor morosidad?",
    "¿Cuál es la morosidad promedio del sistema?",
    "¿Cómo ha evolucionado la liquidez del sistema?",
    "Compara la solvencia de Pichincha y Guayaquil",
]


def _sin_acentos(texto: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')


def _normalizar(texto: str) -> str:
    return _sin_acentos(texto.lower())


class ProveedorAsistente:
    """Interfaz que debe implementar cualquier proveedor del asistente."""

    def responder(self, pregunta: str, contexto: Optional[dict] = None) -> str:
        raise NotImplementedError


class ProveedorLLM(ProveedorAsistente):
    """Stub documentado para conectar un LLM real (OpenAI/Claude/Gemini).

    No implementado en esta fase -- ver docs/ManualTecnico.md. Para
    activarlo: 1) instalar el SDK correspondiente, 2) guardar la API key en
    `.streamlit/secrets.toml` (nunca en el código), 3) implementar
    `responder()` armando un prompt con el contexto de indicadores reales
    (mismo patrón de acceso a datos que usa AsistenteDeterministico más
    abajo: analytics.camel_explorer / analytics.camel_scoring), nunca
    dejando que el modelo invente cifras que no vengan del contexto real.
    """

    def __init__(self, proveedor: str = "openai", api_key: Optional[str] = None):
        self.proveedor = proveedor
        self.api_key = api_key

    def responder(self, pregunta: str, contexto: Optional[dict] = None) -> str:
        raise NotImplementedError(
            f"Proveedor LLM '{self.proveedor}' no implementado en esta fase. "
            "Usa AsistenteDeterministico, o implementa este método siguiendo la guía en su docstring."
        )


class AsistenteDeterministico(ProveedorAsistente):
    """Responde preguntas sobre los indicadores reales cargados, con
    reconocimiento de patrones por palabras clave (banco + indicador +
    intención). No usa NLP ni modelos de lenguaje: si no reconoce la
    pregunta, lo dice explícitamente y sugiere ejemplos, en vez de adivinar.
    """

    def __init__(self, df_camel: pd.DataFrame):
        self.df_camel = df_camel
        self.fecha_max = df_camel['fecha'].max()
        self._bancos_normalizados = {_normalizar(b): b for b in BANCOS_SISTEMA if b in df_camel['banco'].unique()}

    def _detectar_bancos(self, texto_norm: str) -> list:
        return [original for norm, original in self._bancos_normalizados.items() if norm in texto_norm]

    def _detectar_indicador(self, texto_norm: str) -> Optional[str]:
        candidatos = sorted(SINONIMOS_INDICADOR.keys(), key=len, reverse=True)
        for palabra in candidatos:
            if _normalizar(palabra) in texto_norm:
                return SINONIMOS_INDICADOR[palabra]
        return None

    def responder(self, pregunta: str, contexto: Optional[dict] = None) -> str:
        if not pregunta or not pregunta.strip():
            return "Escribe una pregunta sobre algún banco o indicador (ver preguntas sugeridas)."

        texto_norm = _normalizar(pregunta)
        bancos = self._detectar_bancos(texto_norm)
        codigo = self._detectar_indicador(texto_norm)
        indicador_label = ETIQUETAS_INDICADORES.get(codigo, codigo) if codigo else None
        fecha_str = self.fecha_max.strftime('%B %Y')

        if codigo is None:
            return ("No reconocí ningún indicador en tu pregunta (solvencia, morosidad, cobertura, ROE, ROA, "
                    "liquidez). Prueba con una de las preguntas sugeridas.")

        es_comparar = any(p in texto_norm for p in PALABRAS_COMPARAR)
        es_mejor = any(_normalizar(p) in texto_norm for p in PALABRAS_MEJOR)
        es_peor = any(_normalizar(p) in texto_norm for p in PALABRAS_PEOR)
        es_promedio = any(_normalizar(p) in texto_norm for p in PALABRAS_PROMEDIO)
        es_evolucion = any(_normalizar(p) in texto_norm for p in PALABRAS_EVOLUCION)

        if es_comparar and len(bancos) >= 2:
            banco_a, banco_b = bancos[0], bancos[1]
            v_a = obtener_valor_indicador(self.df_camel, banco_a, codigo, self.fecha_max)
            v_b = obtener_valor_indicador(self.df_camel, banco_b, codigo, self.fecha_max)
            if v_a is None or v_b is None:
                return f"No tengo dato completo de {indicador_label} para {banco_a} y/o {banco_b} en {fecha_str}."
            mejor = banco_a if (v_a > v_b) != (codigo in MAYOR_ES_PEOR) else banco_b
            return (f"Al {fecha_str}, {indicador_label} de {banco_a} es {v_a*100:.2f}% y de {banco_b} es "
                    f"{v_b*100:.2f}%. En este indicador, {mejor} está en mejor posición.")

        if es_mejor or es_peor:
            ranking = obtener_ranking(self.df_camel, codigo, self.fecha_max)
            if ranking.empty:
                return f"No tengo datos de {indicador_label} para {fecha_str}."
            quiere_mayor_valor = es_mejor != (codigo in MAYOR_ES_PEOR)  # XOR: mejor+mayor_es_mejor, o peor+mayor_es_peor -> valor mas alto
            fila = ranking.iloc[0] if quiere_mayor_valor else ranking.iloc[-1]
            calificativo = "mejor" if es_mejor else "peor"
            return (f"El banco con {calificativo} {indicador_label} al {fecha_str} es **{fila['banco']}** "
                    f"({fila['valor_pct']:.2f}%).")

        if es_promedio:
            serie = serie_promedio_sistema(self.df_camel, codigo)
            if serie.empty:
                return f"No tengo datos de {indicador_label} para calcular el promedio del sistema."
            ultimo = serie.iloc[-1]
            return (f"El {indicador_label} promedio del sistema al {ultimo['fecha'].strftime('%B %Y')} "
                    f"es **{ultimo['valor_pct']:.2f}%** (promedio simple entre bancos).")

        if es_evolucion:
            if bancos:
                serie = obtener_evolucion(self.df_camel, codigo, [bancos[0]]).tail(12)
                sujeto = bancos[0]
            else:
                serie = serie_promedio_sistema(self.df_camel, codigo).tail(12)
                sujeto = "el sistema"
            if len(serie) < 2:
                return f"No hay suficiente historia de {indicador_label} para describir una tendencia."
            inicio, fin = serie['valor_pct'].iloc[0], serie['valor_pct'].iloc[-1]
            direccion = "subió" if fin > inicio else "bajó" if fin < inicio else "se mantuvo estable"
            return (f"En los últimos {len(serie)} meses con dato, {indicador_label} de {sujeto} {direccion} "
                    f"de {inicio:.2f}% a {fin:.2f}%.")

        if bancos:
            banco = bancos[0]
            valor = obtener_valor_indicador(self.df_camel, banco, codigo, self.fecha_max)
            if valor is None:
                return f"No tengo dato de {indicador_label} para {banco} en {fecha_str}."
            return f"{indicador_label} de **{banco}** al {fecha_str} es **{valor*100:.2f}%**."

        return (f"Detecté el indicador '{indicador_label}' pero no un banco ni una intención clara "
                f"(mejor/peor/promedio/evolución/comparar). Prueba con una pregunta más específica.")
