#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script maestro para actualización automática de datos.

Este script orquesta todo el proceso:
1. Verifica si hay nuevos datos disponibles
2. Descarga los datos del mes anterior
3. Procesa Balance, PyG y CAMEL
4. Actualiza los archivos parquet
5. Genera reporte de actualización

USO:
    python scripts/actualizar_datos.py

En GitHub Actions se ejecuta automáticamente el día 10 de cada mes.
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Agregar directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

# Importar configuración
import config
from validar_actualizacion import capturar_estado, validar_actualizacion

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

MASTER_DATA_DIR = ROOT_DIR / "master_data"
SCRIPTS_DIR = ROOT_DIR / "scripts"
STATUS_FILE = MASTER_DATA_DIR / "update_status.json"


def log(mensaje: str, nivel: str = "INFO"):
    """Imprime mensaje con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        print(f"[{timestamp}] [{nivel}] {mensaje}")
    except UnicodeEncodeError:
        # Fallback para consolas Windows con encoding cp1252
        mensaje_ascii = mensaje.encode('ascii', errors='replace').decode('ascii')
        print(f"[{timestamp}] [{nivel}] {mensaje_ascii}")


def cargar_estado() -> dict:
    """Carga el estado de la última actualización."""
    if STATUS_FILE.exists():
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def guardar_estado(estado: dict):
    """Guarda el estado de actualización."""
    MASTER_DATA_DIR.mkdir(exist_ok=True)
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)


def verificar_datos_ya_actualizados() -> bool:
    """
    Verifica si los datos del mes objetivo ya fueron descargados.
    Compara contra la fecha_max real del parquet, no contra update_status.json,
    para evitar falsos positivos cuando el portal no publicó el mes aún.

    Returns:
        bool: True si ya están actualizados, False si necesita actualizar.
    """
    periodo_actual = config.PERIODO_DESCARGA

    # Verificar contra la fecha_max real del parquet
    parquet_path = MASTER_DATA_DIR / "balance.parquet"
    if parquet_path.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(parquet_path, columns=["fecha"])
            fecha_max = df["fecha"].max()
            meses = {1:'ENERO',2:'FEBRERO',3:'MARZO',4:'ABRIL',5:'MAYO',6:'JUNIO',
                     7:'JULIO',8:'AGOSTO',9:'SEPTIEMBRE',10:'OCTUBRE',11:'NOVIEMBRE',12:'DICIEMBRE'}
            periodo_real = f"{meses[fecha_max.month]} {fecha_max.year}"
            log(f"  Datos actuales en parquet hasta: {periodo_real}")
            log(f"  Periodo objetivo: {periodo_actual}")
            if periodo_real == periodo_actual:
                log(f"Los datos de {periodo_actual} ya están en el parquet")
                return True
        except Exception as e:
            log(f"  No se pudo leer parquet para verificar: {e}", "WARNING")

    log(f"Datos pendientes de descargar: {periodo_actual}")
    return False


def verificar_publicacion_completa() -> bool:
    """Comprueba los tres datasets, no solo la fecha maxima de Balance."""
    try:
        validar_actualizacion(bancos_esperados=config.NUMERO_ESPERADO_BANCOS)
        log(f"La publicacion completa ya contiene {config.PERIODO_DESCARGA}")
        return True
    except Exception as exc:
        primera_linea = str(exc).splitlines()[0]
        log(f"La publicacion requiere actualizacion: {primera_linea}", "WARNING")
        return False


def ejecutar_script(script_name: str) -> int:
    """
    Ejecuta un script Python y retorna si fue exitoso.

    Args:
        script_name: Nombre del script a ejecutar

    Returns:
        int: Codigo de salida del proceso
    """
    script_path = SCRIPTS_DIR / script_name
    log(f"Ejecutando: {script_name}")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos máximo
        )

        if result.returncode == 0:
            log(f"[OK] {script_name} completado exitosamente")
            return 0
        else:
            log(f"[FAIL] {script_name} fallo con codigo {result.returncode}", "ERROR")
            if result.stdout:
                log(f"  Salida: {result.stdout[-1000:]}", "ERROR")
            if result.stderr:
                log(f"  Error: {result.stderr[-1000:]}", "ERROR")
            return result.returncode

    except subprocess.TimeoutExpired:
        log(f"[FAIL] {script_name} excedio el tiempo limite", "ERROR")
        return 1
    except Exception as e:
        log(f"[FAIL] Error ejecutando {script_name}: {e}", "ERROR")
        return 1


def descargar_datos() -> int:
    """
    Ejecuta el script de descarga.

    Returns:
        bool: True si la descarga fue exitosa
    """
    log("=" * 60)
    log("PASO 1: DESCARGA DE DATOS")
    log("=" * 60)

    return ejecutar_script("descargar.py")


def procesar_balance() -> bool:
    """Procesa los datos de Balance General."""
    log("=" * 60)
    log("PASO 2: PROCESAMIENTO DE BALANCE")
    log("=" * 60)

    return ejecutar_script("procesar_balance.py") == 0


def procesar_pyg() -> bool:
    """Procesa los datos de Pérdidas y Ganancias."""
    log("=" * 60)
    log("PASO 3: PROCESAMIENTO DE P&G")
    log("=" * 60)

    return ejecutar_script("procesar_pyg.py") == 0


def procesar_camel() -> bool:
    """Procesa los indicadores CAMEL."""
    log("=" * 60)
    log("PASO 4: PROCESAMIENTO DE CAMEL")
    log("=" * 60)

    return ejecutar_script("procesar_camel.py") == 0


def verificar_archivos_generados() -> bool:
    """
    Verifica que se hayan generado los archivos parquet correctamente.

    Returns:
        bool: True si todos los archivos existen y tienen datos
    """
    log("=" * 60)
    log("PASO 5: VERIFICACIÓN DE ARCHIVOS")
    log("=" * 60)

    archivos_requeridos = [
        "balance.parquet",
        "pyg.parquet",
        "camel.parquet"
    ]

    todos_ok = True

    for archivo in archivos_requeridos:
        ruta = MASTER_DATA_DIR / archivo
        if ruta.exists():
            tamano_mb = ruta.stat().st_size / (1024 * 1024)
            log(f"  [OK] {archivo}: {tamano_mb:.2f} MB")
        else:
            log(f"  [FAIL] {archivo}: NO ENCONTRADO", "ERROR")
            todos_ok = False

    return todos_ok


def limpiar_datos_temporales():
    """Limpia archivos temporales de descarga."""
    log("Limpiando archivos temporales...")

    carpeta_descarga = ROOT_DIR / config.get_carpeta_salida()
    if carpeta_descarga.exists():
        try:
            shutil.rmtree(carpeta_descarga)
            log(f"  Eliminada carpeta: {carpeta_descarga.name}")
        except Exception as e:
            log(f"  No se pudo eliminar {carpeta_descarga.name}: {e}", "WARNING")


def respaldar_master(directorio_respaldo: Path) -> list[str]:
    """Copia los artefactos publicados para poder revertir un ETL parcial."""
    nombres = [
        "balance.parquet", "pyg.parquet", "camel.parquet",
        "metadata.json", "update_status.json",
    ]
    respaldados = []
    for nombre in nombres:
        origen = MASTER_DATA_DIR / nombre
        if origen.exists():
            shutil.copy2(origen, directorio_respaldo / nombre)
            respaldados.append(nombre)
    return respaldados


def restaurar_master(directorio_respaldo: Path, respaldados: list[str]):
    """Restaura el estado publicado si cualquier etapa o validacion falla."""
    log("Restaurando master_data tras un fallo del ETL...", "WARNING")
    for nombre in respaldados:
        respaldo = directorio_respaldo / nombre
        if respaldo.exists():
            shutil.copy2(respaldo, MASTER_DATA_DIR / nombre)


def generar_reporte(exitoso: bool, pasos_completados: list):
    """
    Genera un reporte de la actualización.

    Args:
        exitoso: Si la actualización fue exitosa
        pasos_completados: Lista de pasos completados
    """
    log("=" * 60)
    log("REPORTE DE ACTUALIZACIÓN")
    log("=" * 60)

    estado = {
        'fecha_ejecucion': datetime.now().isoformat(),
        'periodo_objetivo': config.PERIODO_DESCARGA,
        'exitoso': exitoso,
        'pasos_completados': pasos_completados,
    }

    if exitoso:
        # Verificar la fecha máxima real del parquet generado
        periodo_real = config.PERIODO_DESCARGA
        try:
            import pandas as pd
            df = pd.read_parquet(MASTER_DATA_DIR / "balance.parquet", columns=["fecha"])
            fecha_max = df["fecha"].max()
            meses = {1:'ENERO',2:'FEBRERO',3:'MARZO',4:'ABRIL',5:'MAYO',6:'JUNIO',
                     7:'JULIO',8:'AGOSTO',9:'SEPTIEMBRE',10:'OCTUBRE',11:'NOVIEMBRE',12:'DICIEMBRE'}
            periodo_real = f"{meses[fecha_max.month]} {fecha_max.year}"
            log(f"  Fecha máxima real en parquet: {fecha_max.strftime('%Y-%m-%d')} → {periodo_real}")
        except Exception as e:
            log(f"  No se pudo leer fecha_max del parquet: {e}", "WARNING")

        estado['ultimo_periodo_descargado'] = periodo_real
        log(f"[OK] ACTUALIZACION EXITOSA")
        log(f"  Periodo objetivo: {config.PERIODO_DESCARGA}")
        log(f"  Periodo real en datos: {periodo_real}")
        if periodo_real != config.PERIODO_DESCARGA:
            log(f"  AVISO: Los datos solo llegan hasta {periodo_real}, no hasta {config.PERIODO_DESCARGA}", "WARNING")
    else:
        log(f"[FAIL] ACTUALIZACION FALLIDA", "ERROR")
        log(f"  Pasos completados: {pasos_completados}")

    guardar_estado(estado)

    return estado


def main() -> int:
    """Ejecuta una actualizacion transaccional y devuelve un codigo semantico."""
    log("=" * 60)
    log("INICIANDO ACTUALIZACION AUTOMATICA DE DATOS")
    log("=" * 60)
    config.mostrar_configuracion()

    if verificar_publicacion_completa():
        log("No es necesario actualizar. Saliendo.")
        return 0

    pasos_completados = []
    estado_anterior = capturar_estado()
    codigo_descarga = descargar_datos()

    if codigo_descarga == 2:
        log("La fuente todavia no contiene el mes objetivo. Sin cambios.")
        estado = cargar_estado()
        estado['ultimo_intento'] = datetime.now().isoformat()
        estado['ultimo_intento_periodo'] = config.PERIODO_DESCARGA
        estado['ultimo_intento_exitoso'] = True
        estado['sin_datos_nuevos'] = True
        guardar_estado(estado)
        return 2
    if codigo_descarga != 0:
        log("La descarga o validacion de la fuente fallo.", "ERROR")
        return 1
    pasos_completados.append("descarga")

    with tempfile.TemporaryDirectory(prefix="bancos-master-backup-") as temporal:
        directorio_respaldo = Path(temporal)
        respaldados = respaldar_master(directorio_respaldo)
        try:
            if not procesar_balance():
                raise RuntimeError("Fallo el procesamiento de Balance")
            pasos_completados.append("balance")

            if not procesar_pyg():
                raise RuntimeError("Fallo el procesamiento de PyG")
            pasos_completados.append("pyg")

            if not procesar_camel():
                raise RuntimeError("Fallo el procesamiento CAMEL")
            pasos_completados.append("camel")

            if not verificar_archivos_generados():
                raise RuntimeError("Faltan artefactos del ETL")

            validar_actualizacion(
                estado_anterior=estado_anterior,
                bancos_esperados=config.NUMERO_ESPERADO_BANCOS,
            )
            pasos_completados.append("verificacion")
            generar_reporte(True, pasos_completados)
        except Exception as exc:
            log(str(exc), "ERROR")
            restaurar_master(directorio_respaldo, respaldados)
            generar_reporte(False, pasos_completados)
            return 1

    limpiar_datos_temporales()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("Actualización cancelada por el usuario", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Error inesperado: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
