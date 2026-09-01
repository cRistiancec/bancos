# -*- coding: utf-8 -*-
"""Badge visual de severidad (semaforo prudencial). Componente nuevo,
puramente de presentacion sobre clasificaciones ya calculadas en
analytics.camel_scoring / analytics.early_warning.
"""

import streamlit as st

from config.theme_tokens import COLOR_SEVERIDAD, ICONO_SEVERIDAD

ETIQUETA_SEVERIDAD = {
    'OK': 'Normal',
    'ALERTA': 'Alerta',
    'CRITICO': 'Crítico',
    'SIN_DATO': 'Sin dato',
}


def render_badge_severidad(severidad: str, texto: str = None) -> str:
    """Retorna el HTML de un badge de severidad (no lo renderiza)."""
    color = COLOR_SEVERIDAD.get(severidad, COLOR_SEVERIDAD['SIN_DATO'])
    icono = ICONO_SEVERIDAD.get(severidad, ICONO_SEVERIDAD['SIN_DATO'])
    etiqueta = texto or ETIQUETA_SEVERIDAD.get(severidad, severidad)

    return (
        f'<span class="sfp-badge" style="color:{color}; border-color:{color};">'
        f'{icono} {etiqueta}</span>'
    )


def render_semaforo_general(criticas: int, alertas: int):
    """Semaforo agregado para el header/resumen ejecutivo, a partir de los
    conteos de analytics.early_warning.resumen_alertas().
    """
    if criticas > 0:
        severidad, mensaje = 'CRITICO', f'{criticas} indicador(es) en nivel crítico'
    elif alertas > 0:
        severidad, mensaje = 'ALERTA', f'{alertas} indicador(es) en alerta'
    else:
        severidad, mensaje = 'OK', 'Sistema dentro de parámetros normales'

    st.markdown(
        f'<div class="sfp-semaforo-general">{render_badge_severidad(severidad, mensaje)}</div>',
        unsafe_allow_html=True
    )
