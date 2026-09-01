#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Financiero Privado
Sistema Inteligente para el Monitoreo Integral del Sistema Bancario Privado del Ecuador

Autor institucional: Eco. Cristian Coronel Quezada, MBA
Coordinación Técnica de Riesgos y Estudios — COSEDE

Punto de entrada unico de la plataforma (reemplaza a Inicio.py + pages/N_*.py).
Ejecutar con: streamlit run app.py
"""

from config.nav_registry import construir_navegacion

pagina_actual = construir_navegacion()
pagina_actual.run()
