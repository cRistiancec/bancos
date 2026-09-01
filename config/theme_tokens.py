# -*- coding: utf-8 -*-
"""
Tokens de diseno institucional (paleta modo oscuro).

Unica fuente de verdad para colores usados por ui/theme.py, styles/*.css y
components/*. Mantener sincronizado con .streamlit/config.toml.
"""

COLORES = {
    # Fondo
    'fondo_base': '#0E1420',
    'fondo_panel': '#151C2C',
    'fondo_panel_alt': '#1B2436',
    'borde': '#2A3550',

    # Marca
    'azul_institucional': '#1B4C8C',
    'azul_petroleo': '#0D3B4A',
    'gris_grafito': '#2B2F33',

    # Texto
    'texto_primario': '#F5F7FA',
    'texto_secundario': '#9AA5B8',

    # Semantica de riesgo
    'verde': '#1B8A5A',
    'naranja': '#E8871E',
    'rojo': '#C1272D',
    'azul_info': '#3182CE',

    'blanco': '#FFFFFF',
}

# Semaforo de severidad (analytics.camel_scoring / analytics.early_warning)
COLOR_SEVERIDAD = {
    'OK': COLORES['verde'],
    'ALERTA': COLORES['naranja'],
    'CRITICO': COLORES['rojo'],
    'SIN_DATO': COLORES['texto_secundario'],
}

ICONO_SEVERIDAD = {
    'OK': '●',
    'ALERTA': '▲',
    'CRITICO': '■',
    'SIN_DATO': '○',
}
