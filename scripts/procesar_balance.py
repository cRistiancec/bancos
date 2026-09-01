#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador de Balance General (Hoja BAL)

Estructura del Excel:
- Fila 5, desde columna C: Fechas (ene-2003 a dic-2025)
- Columna A, desde fila 7: Codigos de cuenta
- Columna B, desde fila 7: Nombres de cuenta
- Desde C7: Valores en miles de dolares

Genera: master_data/balance.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
import json
import sys

if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Agregar directorio de scripts al path para importar config
sys.path.insert(0, str(Path(__file__).parent))
import config

# =============================================================================
# CONFIGURACION
# =============================================================================

EXCEL_DIR = Path(config.get_carpeta_salida()) / "archivos_excel"
MASTER_DIR = Path("master_data")

# Crear directorio si no existe
MASTER_DIR.mkdir(exist_ok=True)


def extraer_nombre_banco(carpeta: str) -> str:
    """Extrae nombre del banco de la carpeta."""
    nombre = re.sub(
        r'\s+(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)\s+\d{4}$',
        '', carpeta, flags=re.IGNORECASE
    )
    return nombre.strip()


def calcular_nivel(codigo: str) -> int:
    """Calcula nivel jerarquico segun cantidad de digitos."""
    if pd.isna(codigo) or codigo == '':
        return 0

    codigo_limpio = str(codigo).strip().replace('.', '').replace(' ', '')

    if not codigo_limpio.isdigit():
        return 0

    longitud = len(codigo_limpio)

    if longitud <= 1:
        return 1
    elif longitud <= 2:
        return 2
    elif longitud <= 4:
        return 3
    elif longitud <= 6:
        return 4
    else:
        return 5


def procesar_banco(ruta_excel: Path, nombre_banco: str) -> pd.DataFrame:
    """
    Procesa la hoja BAL de un banco.

    Returns:
        DataFrame con columnas: banco, fecha, codigo, cuenta, valor, nivel
    """
    try:
        # Leer hoja BAL sin header (lo procesamos manualmente)
        df_raw = pd.read_excel(ruta_excel, sheet_name='BAL', header=None)

        # Extraer fechas de fila 5 (indice 4), desde columna C (indice 2)
        fechas_raw = df_raw.iloc[4, 2:].values

        # Convertir fechas
        fechas = []
        for f in fechas_raw:
            if pd.isna(f):
                continue
            try:
                if isinstance(f, datetime):
                    fechas.append(f)
                else:
                    fechas.append(pd.to_datetime(f))
            except:
                continue

        if not fechas:
            print(f"  [ERROR] No se encontraron fechas validas en {nombre_banco}")
            return pd.DataFrame()

        # Extraer datos desde fila 7 (indice 6)
        df_datos = df_raw.iloc[6:].copy()

        # Columna A = codigos, Columna B = cuentas, Columnas C+ = valores
        codigos = df_datos.iloc[:, 0].values
        cuentas = df_datos.iloc[:, 1].values
        valores = df_datos.iloc[:, 2:2+len(fechas)].values

        # Crear DataFrame en formato largo
        registros = []

        for i in range(len(codigos)):
            codigo = codigos[i]
            cuenta = cuentas[i]

            # Saltar filas vacias
            if pd.isna(codigo) and pd.isna(cuenta):
                continue

            codigo_str = str(codigo).strip() if pd.notna(codigo) else ''
            cuenta_str = str(cuenta).strip() if pd.notna(cuenta) else ''

            # Saltar si ambos estan vacios
            if not codigo_str and not cuenta_str:
                continue

            nivel = calcular_nivel(codigo_str)

            for j, fecha in enumerate(fechas):
                valor = valores[i, j] if j < valores.shape[1] else None

                # Convertir valor a float
                if pd.notna(valor):
                    try:
                        valor_float = float(valor)
                    except:
                        valor_float = None
                else:
                    valor_float = None

                registros.append({
                    'banco': nombre_banco,
                    'fecha': fecha,
                    'codigo': codigo_str,
                    'cuenta': cuenta_str,
                    'valor': valor_float,
                    'nivel': nivel
                })

        df_resultado = pd.DataFrame(registros)
        return df_resultado

    except Exception as e:
        print(f"  [ERROR] {nombre_banco}: {e}")
        return pd.DataFrame()


def main():
    print("=" * 70)
    print("PROCESADOR DE BALANCE GENERAL (HOJA BAL)")
    print("=" * 70)

    # Buscar carpetas de bancos
    carpetas = [d for d in EXCEL_DIR.iterdir() if d.is_dir()]

    if not carpetas:
        raise RuntimeError(f"No se encontraron carpetas en {EXCEL_DIR}")

    print(f"\n[INFO] Encontrados {len(carpetas)} bancos\n")

    todos_los_dfs = []
    bancos_procesados = []
    bancos_error = []

    for i, carpeta in enumerate(sorted(carpetas), 1):
        nombre_banco = extraer_nombre_banco(carpeta.name)
        print(f"[{i:2}/{len(carpetas)}] {nombre_banco}...", end=" ")

        # Buscar archivo Excel
        excels = list(carpeta.glob("*.xlsx")) + list(carpeta.glob("*.xls"))

        if not excels:
            print("[ERROR] No se encontro archivo Excel")
            bancos_error.append(nombre_banco)
            continue

        ruta_excel = excels[0]

        # Procesar
        df = procesar_banco(ruta_excel, nombre_banco)

        if df.empty:
            bancos_error.append(nombre_banco)
            print("[ERROR]")
        else:
            todos_los_dfs.append(df)
            bancos_procesados.append(nombre_banco)
            print(f"[OK] {len(df):,} registros")

    # Consolidar
    print("\n" + "=" * 70)
    print("CONSOLIDANDO DATOS")
    print("=" * 70)

    if not todos_los_dfs:
        raise RuntimeError("No se procesaron datos de Balance")

    if bancos_error:
        raise RuntimeError(
            f"Balance incompleto; bancos con error: {', '.join(bancos_error)}"
        )

    df_consolidado = pd.concat(todos_los_dfs, ignore_index=True)

    # Optimizar tipos
    df_consolidado['banco'] = df_consolidado['banco'].astype('category')
    df_consolidado['codigo'] = df_consolidado['codigo'].astype('category')
    df_consolidado['cuenta'] = df_consolidado['cuenta'].astype('category')
    df_consolidado['nivel'] = df_consolidado['nivel'].astype('int8')

    # Guardar Parquet
    ruta_parquet = MASTER_DIR / "balance.parquet"
    ruta_temporal = ruta_parquet.with_suffix(".parquet.tmp")
    df_consolidado.to_parquet(ruta_temporal, index=False, compression='snappy')
    ruta_temporal.replace(ruta_parquet)

    tamano_mb = ruta_parquet.stat().st_size / (1024 * 1024)

    print(f"\n[OK] Guardado: {ruta_parquet}")
    print(f"    - Registros: {len(df_consolidado):,}")
    print(f"    - Tamano: {tamano_mb:.2f} MB")
    print(f"    - Bancos: {df_consolidado['banco'].nunique()}")
    print(f"    - Fechas: {df_consolidado['fecha'].nunique()}")
    print(f"    - Cuentas unicas: {df_consolidado['cuenta'].nunique()}")

    # Guardar metadata
    metadata = {
        'ultima_actualizacion': datetime.now().isoformat(),
        'bancos_procesados': bancos_procesados,
        'bancos_error': bancos_error,
        'total_bancos': len(bancos_procesados),
        'total_registros': len(df_consolidado),
        'fecha_min': str(df_consolidado['fecha'].min()),
        'fecha_max': str(df_consolidado['fecha'].max()),
        'hojas_procesadas': ['BAL']
    }

    ruta_metadata = MASTER_DIR / "metadata.json"
    ruta_metadata_temporal = ruta_metadata.with_suffix(".json.tmp")
    with open(ruta_metadata_temporal, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    ruta_metadata_temporal.replace(ruta_metadata)

    print(f"\n[OK] Metadata guardada en {MASTER_DIR / 'metadata.json'}")

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"  Bancos procesados: {len(bancos_procesados)}")
    print(f"  Bancos con error: {len(bancos_error)}")
    if bancos_error:
        print(f"    -> {', '.join(bancos_error)}")
    print(f"  Rango de fechas: {df_consolidado['fecha'].min()} a {df_consolidado['fecha'].max()}")

    # Muestra de datos
    print("\n[MUESTRA] Primeras filas:")
    print(df_consolidado.head(10).to_string(index=False))

    print("\n[MUESTRA] Cuentas nivel 1:")
    nivel1 = df_consolidado[df_consolidado['nivel'] == 1]['cuenta'].unique()[:10]
    for c in nivel1:
        print(f"  - {c}")


if __name__ == "__main__":
    main()
