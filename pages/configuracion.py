# -*- coding: utf-8 -*-
"""Configuración — información del sistema, caché y estado de datos."""

import streamlit as st

from ui.layout import render_page
from services.data_service import obtener_contexto_sistema, cargar_metadata

render_page("Configuración", icono="⚙️")

st.title("Configuración")

st.markdown("### Información del Sistema")
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **Sistema:** Sistema Financiero Privado
    **Versión:** 2.0.0 (Fase 1 — Refactor Institucional)
    **Autor:** Eco. Cristian Coronel Quezada, MBA
    **Solución:** DATAMETRICS — Business Intelligence and Analytics
    """)
with col2:
    st.markdown("""
    **Fuente de datos:** Superintendencia de Bancos del Ecuador
    **Tecnologías:** Python, Streamlit, Plotly, Pandas
    **Manual de usuario:** `docs/ManualUsuario.md`
    **Manual técnico:** `docs/ManualTecnico.md`
    """)

st.markdown("---")
st.markdown("### Estado de Datos")

contexto = obtener_contexto_sistema()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Bancos", contexto.get('num_bancos') or "N/D")
with col2:
    fecha_corte = contexto.get('fecha_corte')
    st.metric("Corte de datos", fecha_corte.strftime('%b %Y') if fecha_corte is not None else "N/D")
with col3:
    st.metric("Registros totales", f"{contexto.get('total_registros'):,}" if contexto.get('total_registros') else "N/D")

metadata = cargar_metadata()
if metadata and 'error' not in metadata:
    st.json(metadata)
else:
    st.info("`master_data/metadata.json` no está presente en este entorno. Se regenera automáticamente al "
            "ejecutar `scripts/procesar_balance.py` (queda excluido de git por `.gitignore`).")

st.markdown("---")
st.markdown("### Caché")
st.caption("Los datos se cargan con `st.cache_data` (TTL 1 hora). Usa este botón si actualizaste los "
           "archivos Parquet en `master_data/` y quieres forzar una recarga inmediata.")
if st.button("🔄 Limpiar caché de datos"):
    st.cache_data.clear()
    st.success("Caché limpiada. Recarga la página para ver los datos actualizados.")
