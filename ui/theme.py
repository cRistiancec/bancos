# -*- coding: utf-8 -*-
"""Inyeccion del CSS institucional (styles/institutional.css)."""

from pathlib import Path
import streamlit as st

CSS_PATH = Path(__file__).parent.parent / "styles" / "institutional.css"


def aplicar_tema():
    """Inyecta el CSS institucional. Seguro de llamar en cada pagina
    (Streamlit deduplica los <style> identicos en el DOM del navegador)."""
    if CSS_PATH.exists():
        css = CSS_PATH.read_text(encoding='utf-8')
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
