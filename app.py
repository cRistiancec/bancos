#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Financiero Privado
Punto de entrada con diagnostico de errores de inicio.
"""

import streamlit as st
import traceback

try:
    from config.nav_registry import construir_navegacion
    pagina_actual = construir_navegacion()
    pagina_actual.run()
except Exception as e:
    st.error(f"**ERROR DE INICIO: {type(e).__name__}**")
    st.error(str(e))
    st.code(traceback.format_exc(), language="python")
    st.warning("Revisa los logs de la app para mas detalles.")
