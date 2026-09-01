# -*- coding: utf-8 -*-
"""
Procesamiento de hoja CAMEL de archivos Excel de la Superintendencia de Bancos.

Estructura de la hoja CAMEL:
- Fila 5: Fechas (columna D en adelante)
- Filas 6-54: Indicadores CAMEL
- Columna B o C: Nombre del indicador (varía según fila)

Este script genera: master_data/camel.parquet
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime
import sys
import warnings

warnings.filterwarnings('ignore')

if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Agregar directorio de scripts al path para importar config
sys.path.insert(0, str(Path(__file__).parent))
import config

# Configuracion
DATOS_DIR = Path(config.get_carpeta_salida()) / "archivos_excel"
OUTPUT_DIR = Path("master_data")
OUTPUT_DIR.mkdir(exist_ok=True)

# Mapeo de indicadores CAMEL
# Formato: fila_excel: (codigo, nombre, columna_nombre, categoria)
INDICADORES_CAMEL = {
    # Fila 6-11: Indicadores de solvencia y estructura (columna B)
    6: ('SOL', 'Indice de Solvencia PTC/APPR', 'B', 'C - Capital'),
    9: ('AIN', 'Activos Improductivos Netos / Total Activos', 'B', 'A - Activos'),
    10: ('CAR_ACT', 'Cartera Total / Activo Total', 'B', 'A - Activos'),
    11: ('INV_ACT', 'Inversiones / Total Activo', 'B', 'A - Activos'),

    # Filas 12-19: Participación de crédito (columna C) - Para treemap
    12: ('PART_INMOB_VIP', 'Participacion Credito Inmobiliario y Vivienda Interes Publico', 'C', 'Composicion Cartera'),
    13: ('PART_PROD', 'Participacion Credito Productivo Nuevo', 'C', 'Composicion Cartera'),
    14: ('PART_CONS', 'Participacion Credito de Consumo', 'C', 'Composicion Cartera'),
    15: ('PART_INMOB', 'Participacion Credito Inmobiliario', 'C', 'Composicion Cartera'),
    16: ('PART_MICRO', 'Participacion Credito Microcredito', 'C', 'Composicion Cartera'),
    17: ('PART_VIS', 'Participacion Credito Vivienda Interes Social y Publico', 'C', 'Composicion Cartera'),
    18: ('PART_EDU', 'Participacion Credito Educativo', 'C', 'Composicion Cartera'),
    19: ('PART_INV_PUB', 'Participacion Credito Inversion Publica', 'C', 'Composicion Cartera'),

    # Filas 22-31: Morosidad (columna C) - excepto fila 29
    22: ('MOR_TOT', 'Morosidad Total', 'C', 'A - Activos'),
    23: ('MOR_INMOB_VIP', 'Morosidad Credito Inmobiliario y Vivienda Interes Publico', 'C', 'A - Activos'),
    24: ('MOR_PROD', 'Morosidad Credito Productivo Nuevo', 'C', 'A - Activos'),
    25: ('MOR_CONS', 'Morosidad Credito de Consumo', 'C', 'A - Activos'),
    26: ('MOR_INMOB', 'Morosidad Credito Inmobiliaria', 'C', 'A - Activos'),
    27: ('MOR_MICRO', 'Morosidad Credito Microcredito', 'C', 'A - Activos'),
    28: ('MOR_VIS', 'Morosidad Credito Vivienda Interes Social', 'C', 'A - Activos'),
    # Fila 29 esta vacia
    30: ('MOR_EDU', 'Morosidad Credito Educativo', 'C', 'A - Activos'),
    31: ('MOR_INV_PUB', 'Morosidad Credito Inversion Publica', 'C', 'A - Activos'),

    # Filas 33-41: Cobertura (columna C)
    33: ('COB_TOT', 'Cobertura Total Cartera', 'C', 'A - Activos'),
    34: ('COB_INMOB_VIP', 'Cobertura Credito Inmobiliario y Vivienda Interes Publico', 'C', 'A - Activos'),
    35: ('COB_PROD', 'Cobertura Credito Productivo Nuevo', 'C', 'A - Activos'),
    36: ('COB_CONS', 'Cobertura Credito de Consumo', 'C', 'A - Activos'),
    37: ('COB_INMOB', 'Cobertura Credito Inmobiliaria', 'C', 'A - Activos'),
    38: ('COB_MICRO', 'Cobertura Credito Microcredito', 'C', 'A - Activos'),
    39: ('COB_VIS', 'Cobertura Credito Vivienda Interes Social', 'C', 'A - Activos'),
    40: ('COB_EDU', 'Cobertura Credito Educativo', 'C', 'A - Activos'),
    41: ('COB_INV_PUB', 'Cobertura Credito Inversion Publica', 'C', 'A - Activos'),

    # Filas 43-46: Management (columna B)
    43: ('AP_PC', 'Activos Productivos / Pasivos con Costo', 'B', 'M - Management'),
    44: ('GO_MNF', 'Gastos Operacion / Margen Neto Financiero', 'B', 'M - Management'),
    45: ('GP_ACT', 'Gastos Personal / Total Activo Promedio', 'B', 'M - Management'),
    46: ('GO_ACT', 'Gastos Operacion / Total Activo Promedio', 'B', 'M - Management'),

    # Filas 48-52: Earnings (columna B)
    48: ('ROA', 'Rendimiento Operativo sobre Activo (ROA)', 'B', 'E - Earnings'),
    49: ('ROE', 'Rendimiento sobre Patrimonio (ROE)', 'B', 'E - Earnings'),
    51: ('DEP_SPREAD', 'Dependencia Spread', 'B', 'E - Earnings'),
    52: ('DEP_BRECHA', 'Dependencia Brecha', 'B', 'E - Earnings'),

    # Fila 54: Liquidez (columna B)
    54: ('LIQ', 'Indice de Liquidez Fondos Disponibles / Total Depositos', 'B', 'L - Liquidity'),
}


def extraer_nombre_banco(ruta_archivo: Path) -> str:
    """Extrae el nombre del banco de la ruta del archivo, quitando el sufijo MES AÑO."""
    nombre_carpeta = ruta_archivo.parent.name
    nombre = re.sub(
        r'\s+(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)\s+\d{4}$',
        '', nombre_carpeta, flags=re.IGNORECASE
    )
    return nombre.strip()


def procesar_archivo_camel(ruta_archivo: Path) -> pd.DataFrame:
    """
    Procesa la hoja CAMEL de un archivo Excel.

    Args:
        ruta_archivo: Path al archivo Excel

    Returns:
        DataFrame con columnas: banco, fecha, codigo, indicador, valor, categoria
    """
    try:
        # Leer hoja CAMEL sin headers
        df_excel = pd.read_excel(ruta_archivo, sheet_name='CAMEL', header=None)

        banco = extraer_nombre_banco(ruta_archivo)

        # Obtener fechas de la fila 5 (indice 4), columna D en adelante (indice 3)
        fechas_row = df_excel.iloc[4, 3:]

        # Filtrar fechas validas
        fechas_validas = []
        col_indices = []
        for col_idx, fecha in enumerate(fechas_row):
            if pd.notna(fecha):
                try:
                    if isinstance(fecha, datetime):
                        fechas_validas.append(fecha)
                        col_indices.append(col_idx + 3)  # Ajustar indice (columna D = indice 3)
                    elif isinstance(fecha, str):
                        fecha_parsed = pd.to_datetime(fecha)
                        fechas_validas.append(fecha_parsed)
                        col_indices.append(col_idx + 3)
                except:
                    continue

        if not fechas_validas:
            print(f"  No se encontraron fechas validas en {ruta_archivo.name}")
            return pd.DataFrame()

        registros = []

        # Procesar cada indicador
        for fila_excel, (codigo, nombre, col_nombre, categoria) in INDICADORES_CAMEL.items():
            fila_idx = fila_excel - 1  # Convertir a indice base 0

            if fila_idx >= len(df_excel):
                continue

            # Obtener valores para todas las fechas
            for fecha, col_idx in zip(fechas_validas, col_indices):
                try:
                    valor = df_excel.iloc[fila_idx, col_idx]

                    # Convertir a float si es posible
                    if pd.notna(valor):
                        if isinstance(valor, (int, float)):
                            valor_float = float(valor)
                        else:
                            try:
                                valor_float = float(str(valor).replace(',', '.'))
                            except:
                                continue

                        registros.append({
                            'banco': banco,
                            'fecha': fecha,
                            'codigo': codigo,
                            'indicador': nombre,
                            'valor': valor_float,
                            'categoria': categoria,
                        })
                except Exception as e:
                    continue

        df_resultado = pd.DataFrame(registros)
        return df_resultado

    except Exception as e:
        print(f"  Error procesando {ruta_archivo.name}: {str(e)}")
        return pd.DataFrame()


def main():
    """Funcion principal de procesamiento."""
    print("=" * 60)
    print("PROCESAMIENTO DE HOJA CAMEL")
    print("=" * 60)

    # Buscar archivos Excel
    archivos = list(DATOS_DIR.glob("**/*.xlsx"))
    print(f"\nArchivos encontrados: {len(archivos)}")

    if not archivos:
        raise RuntimeError("No se encontraron archivos Excel para CAMEL")

    # Procesar cada archivo
    dataframes = []
    bancos_procesados = set()
    archivos_error = []

    for i, archivo in enumerate(archivos, 1):
        banco = extraer_nombre_banco(archivo)
        print(f"\n[{i}/{len(archivos)}] Procesando: {banco}")

        df = procesar_archivo_camel(archivo)

        if not df.empty:
            dataframes.append(df)
            bancos_procesados.add(banco)
            print(f"  -> {len(df):,} registros")
        else:
            print(f"  -> Sin datos CAMEL")
            archivos_error.append(archivo.parent.name)

    if not dataframes:
        raise RuntimeError("No se procesaron datos CAMEL")

    if archivos_error:
        raise RuntimeError(
            f"CAMEL incompleto; archivos con error: {', '.join(archivos_error)}"
        )

    # Consolidar
    print("\n" + "=" * 60)
    print("CONSOLIDANDO DATOS")
    print("=" * 60)

    df_final = pd.concat(dataframes, ignore_index=True)

    # Asegurar tipos de datos
    df_final['fecha'] = pd.to_datetime(df_final['fecha'])
    df_final['valor'] = pd.to_numeric(df_final['valor'], errors='coerce')

    # Eliminar duplicados
    df_final = df_final.drop_duplicates(subset=['banco', 'fecha', 'codigo'], keep='first')

    # Ordenar
    df_final = df_final.sort_values(['banco', 'codigo', 'fecha'])

    for columna in ['banco', 'codigo', 'indicador', 'categoria']:
        df_final[columna] = df_final[columna].astype('category')

    # Estadisticas
    print(f"\nRegistros totales: {len(df_final):,}")
    print(f"Bancos: {df_final['banco'].nunique()}")
    print(f"Indicadores: {df_final['codigo'].nunique()}")
    print(f"Fechas: {df_final['fecha'].nunique()}")
    print(f"Fecha min: {df_final['fecha'].min()}")
    print(f"Fecha max: {df_final['fecha'].max()}")

    # Indicadores por categoria
    print("\nIndicadores por categoria:")
    for cat in df_final['categoria'].unique():
        n_ind = df_final[df_final['categoria'] == cat]['codigo'].nunique()
        print(f"  {cat}: {n_ind} indicadores")

    # Guardar
    output_file = OUTPUT_DIR / "camel.parquet"
    output_temporal = output_file.with_suffix(".parquet.tmp")
    df_final.to_parquet(output_temporal, index=False)
    output_temporal.replace(output_file)
    print(f"\nArchivo guardado: {output_file}")
    print(f"Tamano: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

    # Mostrar muestra
    print("\nMuestra de datos:")
    print(df_final.head(10).to_string())

    print("\n" + "=" * 60)
    print("PROCESAMIENTO COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
