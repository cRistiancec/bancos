#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuración para descarga de boletines de la Superintendencia de Bancos.

Este archivo configura los parámetros para el scraping automático.
Los valores de año y mes se calculan automáticamente basándose en la fecha actual.
"""

import os
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURACIÓN AUTOMÁTICA DE PERIODO
# =============================================================================

def obtener_periodo_objetivo():
    """
    Calcula el periodo objetivo para descarga.
    El día 10 de cada mes se publican los datos del mes anterior.

    Returns:
        tuple: (año, mes, nombre_periodo)
    """
    hoy = datetime.now()

    # Obtener el mes anterior
    primer_dia_mes_actual = hoy.replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)

    ano = ultimo_dia_mes_anterior.year
    mes = ultimo_dia_mes_anterior.month

    meses_espanol = {
        1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
        5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
        9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
    }

    nombre_periodo = f"{meses_espanol[mes]} {ano}"

    return ano, mes, nombre_periodo


# Obtener periodo objetivo automáticamente
ANO_OBJETIVO, MES_OBJETIVO, PERIODO_DESCARGA = obtener_periodo_objetivo()

# Año a buscar en el portal (carpeta del año)
ANO_BUSCAR = ANO_OBJETIVO

# =============================================================================
# URLs Y RUTAS
# =============================================================================

# URL del portal de la Superintendencia de Bancos
URL_PORTAL = "https://www.superbancos.gob.ec/estadisticas/portalestudios/bancos-2/"

# Texto para buscar la carpeta de boletines
CARPETA_BOLETINES_TEXTO = "Boletines de Series por Entidad"

# =============================================================================
# CONFIGURACIÓN DE DESCARGA
# =============================================================================

# Número esperado de bancos (puede variar por fusiones/cierres)
NUMERO_ESPERADO_BANCOS = 23

# Timeout para descargas (en segundos)
TIMEOUT_DESCARGA = 120

# Tamaño del chunk para descarga
CHUNK_SIZE = 8192

# =============================================================================
# CONFIGURACIÓN DE SELENIUM
# =============================================================================

# Ejecutar Chrome en modo headless (sin ventana visible)
# En GitHub Actions siempre debe ser True
CHROME_HEADLESS = os.environ.get('GITHUB_ACTIONS', 'false').lower() == 'true' or True

# Maximizar ventana (solo aplica si no es headless)
CHROME_MAXIMIZADO = True

# =============================================================================
# TIEMPOS DE ESPERA (en segundos)
# =============================================================================

# En GitHub Actions se necesitan tiempos más largos por el headless y la red
_EN_CI = os.environ.get('GITHUB_ACTIONS', 'false').lower() == 'true'

TIEMPO_CARGA_PAGINA = 20 if _EN_CI else 10
TIEMPO_ENTRE_SCROLL = 3 if _EN_CI else 2
TIEMPO_DESPUES_CLIC = 8 if _EN_CI else 5
TIEMPO_CARGA_ARCHIVOS = 15 if _EN_CI else 10

# =============================================================================
# CARPETAS DE SALIDA
# =============================================================================

def get_carpeta_salida():
    """Genera nombre de carpeta basado en el periodo."""
    meses_espanol = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    return f"datos_bancos_{meses_espanol[MES_OBJETIVO]}_{ANO_OBJETIVO}"


def get_ano_xpath():
    """Genera XPath para buscar la carpeta del año."""
    return f"//*[contains(text(), 'Año {ANO_BUSCAR}')]"


# =============================================================================
# FUNCIONES DE VALIDACIÓN
# =============================================================================

def validar_configuracion():
    """Valida la configuración antes de ejecutar."""
    errores = []

    if ANO_BUSCAR < 2003 or ANO_BUSCAR > datetime.now().year + 1:
        errores.append(f"ANO_BUSCAR inválido: {ANO_BUSCAR}")

    if MES_OBJETIVO < 1 or MES_OBJETIVO > 12:
        errores.append(f"MES_OBJETIVO inválido: {MES_OBJETIVO}")

    if errores:
        print("ERRORES DE CONFIGURACIÓN:")
        for e in errores:
            print(f"  - {e}")
        return False

    return True


def mostrar_configuracion():
    """Muestra la configuración actual."""
    print("=" * 60)
    print("CONFIGURACIÓN DE DESCARGA")
    print("=" * 60)
    print(f"  Periodo objetivo: {PERIODO_DESCARGA}")
    print(f"  Año a buscar: {ANO_BUSCAR}")
    print(f"  Carpeta salida: {get_carpeta_salida()}")
    print(f"  URL Portal: {URL_PORTAL}")
    print(f"  Chrome Headless: {CHROME_HEADLESS}")
    print(f"  Bancos esperados: {NUMERO_ESPERADO_BANCOS}")
    print("=" * 60)


if __name__ == "__main__":
    mostrar_configuracion()
    print(f"\nValidación: {'OK' if validar_configuracion() else 'ERRORES'}")
