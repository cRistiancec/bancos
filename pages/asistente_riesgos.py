# -*- coding: utf-8 -*-
"""
Asistente Inteligente de Riesgos — interfaz de chat (Fase 2).

Usa services/assistant_engine.py::AsistenteDeterministico. No hay ningún LLM
conectado: cada respuesta viene de un cálculo real sobre camel.parquet. Ver
ProveedorLLM en assistant_engine.py para cómo conectar uno real más adelante.
"""

import streamlit as st

from ui.layout import render_page
from services.data_service import cargar_camel
from services.assistant_engine import AsistenteDeterministico, PREGUNTAS_SUGERIDAS

render_page("Asistente de Riesgos", icono="💬")

st.title("Asistente Inteligente de Riesgos")
st.info("Asistente **determinístico**: responde con cálculos reales sobre los indicadores cargados, "
        "reconociendo patrones simples de banco + indicador + intención. No hay un modelo de lenguaje "
        "conectado en esta fase — ver `services/assistant_engine.py::ProveedorLLM` para cómo integrar uno.", icon="🤖")

try:
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

if "asistente_historial" not in st.session_state:
    st.session_state.asistente_historial = []

asistente = AsistenteDeterministico(df_camel)

st.markdown("**Preguntas sugeridas:**")
cols = st.columns(3)
pregunta_click = None
for i, sugerida in enumerate(PREGUNTAS_SUGERIDAS):
    with cols[i % 3]:
        if st.button(sugerida, key=f"sugerida_{i}", width='stretch'):
            pregunta_click = sugerida

st.markdown("---")

for rol, mensaje in st.session_state.asistente_historial:
    with st.chat_message(rol):
        st.markdown(mensaje)

pregunta_input = st.chat_input("Escribe tu pregunta sobre un banco o indicador...")
pregunta = pregunta_click or pregunta_input

if pregunta:
    st.session_state.asistente_historial.append(("user", pregunta))
    respuesta = asistente.responder(pregunta)
    st.session_state.asistente_historial.append(("assistant", respuesta))
    st.rerun()

if st.session_state.asistente_historial and st.button("🗑️ Limpiar conversación"):
    st.session_state.asistente_historial = []
    st.rerun()
