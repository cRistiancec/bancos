# -*- coding: utf-8 -*-
"""
Tarjetas KPI institucionales (modo oscuro).

Migrado de utils/charts.py::render_kpi_card / render_kpi_row. Se conserva
exactamente el mismo calculo de delta (variacion %); solo cambia la paleta
de colores para el tema oscuro institucional.
"""

from typing import List, Optional, Dict, Any
import streamlit as st

from config.theme_tokens import COLORES

COLOR_ACENTO_DEFAULT = COLORES['azul_institucional']


def render_kpi_card(
    valor: str,
    label: str,
    delta: Optional[float] = None,
    delta_label: str = "",
    color: str = COLOR_ACENTO_DEFAULT
):
    """Renderiza una tarjeta KPI individual con estilo institucional oscuro."""
    delta_html = ""
    if delta is not None:
        signo = "+" if delta >= 0 else ""
        delta_color = COLORES['verde'] if delta >= 0 else COLORES['rojo']
        flecha = "▲" if delta >= 0 else "▼"
        delta_html = (
            f'<div style="color: {delta_color}; font-size: 0.85rem; margin-top: 4px;">'
            f'{flecha} {signo}{delta:.1f}% {delta_label}</div>'
        )

    st.markdown(f"""
        <div class="sfp-kpi-card" style="border-left: 4px solid {color};">
            <div class="sfp-kpi-value">{valor}</div>
            <div class="sfp-kpi-label">{label}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


def render_kpi_row(kpis: List[Dict[str, Any]]):
    """Renderiza una fila de KPIs.

    Args:
        kpis: Lista de dicts con keys: valor, label, delta (opcional), color (opcional)
    """
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        with col:
            render_kpi_card(
                valor=kpi['valor'],
                label=kpi['label'],
                delta=kpi.get('delta'),
                delta_label=kpi.get('delta_label', ''),
                color=kpi.get('color', COLOR_ACENTO_DEFAULT)
            )
