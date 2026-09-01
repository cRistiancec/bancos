# -*- coding: utf-8 -*-
"""Wrapper de arranque de pagina: page_config + tema + header + sidebar.

Cada pagina en pages/ debe llamar render_page(...) como primera instruccion
Streamlit (equivalente a st.set_page_config, que debe ser lo primero).
"""

import streamlit as st

from ui.theme import aplicar_tema
from ui.header import render_header
from ui.sidebar import render_sidebar_extra


def render_page(titulo: str, icono: str = "📊", layout: str = "wide", mostrar_header: bool = True):
    st.set_page_config(
        page_title=f"{titulo} | Sistema Financiero Privado",
        page_icon=icono,
        layout=layout,
        initial_sidebar_state="expanded",
    )

    aplicar_tema()
    render_sidebar_extra()

    if mostrar_header:
        render_header()


def render_modulo_en_preparacion(nombre_modulo: str, motivo: str):
    """Aviso institucional estandar para pestañas sin fuente de datos aun.
    Usado en vez de inventar cifras cuando no existe informacion real."""
    st.markdown(f"""
        <div class="sfp-en-preparacion">
            <strong>{nombre_modulo} — Módulo en preparación</strong>
            {motivo}
        </div>
    """, unsafe_allow_html=True)
