# -*- coding: utf-8 -*-
"""
Registro unico de navegacion, usado por app.py via st.navigation()/st.Page().

Agrupado en secciones al estilo de plataformas institucionales (Bloomberg,
BIS): General, Monitoreo Prudencial, Riesgos, Estados Financieros, Analisis
Comparativo, Calidad y Reportes.
"""

import streamlit as st


def construir_navegacion():
    paginas = {
        "General": [
            st.Page("pages/resumen_ejecutivo.py", title="Resumen Ejecutivo", icon="🏠", default=True),
            st.Page("pages/panorama_bancario.py", title="Panorama Bancario", icon="📊"),
        ],
        "Monitoreo Prudencial": [
            st.Page("pages/monitoreo_prudencial.py", title="Monitoreo Prudencial", icon="🛡️"),
            st.Page("pages/indicadores_camel.py", title="Indicadores CAMEL", icon="📈"),
            st.Page("pages/alertas_tempranas.py", title="Alertas Tempranas", icon="🚨"),
            st.Page("pages/alertas_predictivas.py", title="Alertas Predictivas", icon="🔭"),
            st.Page("pages/calificacion_riesgo.py", title="Calificación de Riesgo", icon="🏅"),
        ],
        "Riesgos": [
            st.Page("pages/riesgo_credito.py", title="Riesgo de Crédito", icon="💳"),
            st.Page("pages/riesgo_liquidez.py", title="Riesgo de Liquidez", icon="💧"),
            st.Page("pages/riesgo_solvencia.py", title="Riesgo de Solvencia", icon="🏛️"),
            st.Page("pages/riesgo_concentracion.py", title="Riesgo de Concentración", icon="🧩"),
            st.Page("pages/riesgo_sistemico.py", title="Riesgo Sistémico", icon="🌐"),
        ],
        "Estados Financieros": [
            st.Page("pages/balance_general.py", title="Balance General", icon="⚖️"),
            st.Page("pages/perdidas_ganancias.py", title="Pérdidas y Ganancias", icon="💰"),
        ],
        "Análisis Comparativo": [
            st.Page("pages/ranking_bancos.py", title="Ranking de Bancos", icon="🏆"),
            st.Page("pages/comparativos.py", title="Comparativos entre Bancos", icon="🔀"),
            st.Page("pages/evolucion_historica.py", title="Evolución Histórica", icon="📉"),
        ],
        "Analítica Avanzada": [
            st.Page("pages/stress_testing.py", title="Stress Testing", icon="🧪"),
            st.Page("pages/modelos_predictivos.py", title="Modelos Predictivos", icon="🔮"),
            st.Page("pages/asistente_riesgos.py", title="Asistente de Riesgos", icon="💬"),
        ],
        "Calidad y Reportes": [
            st.Page("pages/calidad_datos.py", title="Calidad de Datos", icon="🔍"),
            st.Page("pages/reportes.py", title="Reportes", icon="📤"),
            st.Page("pages/configuracion.py", title="Configuración", icon="⚙️"),
        ],
    }

    return st.navigation(paginas)
