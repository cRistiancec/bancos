# -*- coding: utf-8 -*-
"""
Procesa la hoja PYG (Perdidas y Ganancias) de los archivos Excel.

Logica especial:
- Los datos son acumulados mes a mes dentro de cada anno
- Se desacumulan para obtener el valor de cada mes individual
- Se calcula suma movil de 12 meses para comparabilidad

Estructura de la hoja PYG:
- Codigos de cuenta: columna A, desde fila 6
- Nombres de cuenta: columna B
- Datos: desde columna C
- Fechas: fila 5, desde columna C
"""

import pandas as pd
import numpy as np
import re
import unicodedata
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
CARPETA_DATOS = Path(config.get_carpeta_salida()) / "archivos_excel"
CARPETA_SALIDA = Path("master_data")


def extraer_nombre_banco(carpeta: str) -> str:
    """Extrae nombre del banco de la carpeta, quitando el sufijo MES ANNO."""
    nombre = re.sub(
        r'\s+(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)\s+\d{4}$',
        '', carpeta, flags=re.IGNORECASE
    )
    return nombre.strip()

# Codigos para cuentas resumen (filas con "--")
CODIGOS_RESUMEN = {
    'MARGEN NETO DE INTERESES': 'MNI',
    'MARGEN BRUTO FINANCIERO': 'MBF',
    'MARGEN NETO FINANCIERO': 'MNF',
    'MARGEN DE INTERMEDIACION': 'MDI',
    'MARGEN OPERACIONAL': 'MOP',
    'GANANCIA O PERDIDA ANTES DE IMPUESTOS': 'GAI',
    'GANANCIA O PERDIDA DEL EJERCICIO': 'GDE',
}


def limpiar_nombre_cuenta(nombre: str) -> str:
    """Limpia el nombre de la cuenta para usar como clave."""
    if pd.isna(nombre):
        return ''
    nombre = str(nombre).upper()
    nombre = nombre.replace('A\u0301', 'A').replace('E\u0301', 'E').replace('I\u0301', 'I')
    nombre = nombre.replace('O\u0301', 'O').replace('U\u0301', 'U').replace('N\u0303', 'N')
    nombre = nombre.replace('\u00C1', 'A').replace('\u00C9', 'E').replace('\u00CD', 'I')
    nombre = nombre.replace('\u00D3', 'O').replace('\u00DA', 'U').replace('\u00D1', 'N')
    return nombre


def obtener_codigo_resumen(nombre: str) -> str:
    """Obtiene el codigo para una cuenta resumen."""
    nombre_limpio = limpiar_nombre_cuenta(nombre)
    for clave, codigo in CODIGOS_RESUMEN.items():
        if clave in nombre_limpio:
            return codigo
    return None


def procesar_archivo_pyg(ruta_excel: Path) -> pd.DataFrame:
    """Procesa la hoja PYG de un archivo Excel."""
    try:
        # Extraer nombre del banco de la ruta
        nombre_banco = unicodedata.normalize('NFC', extraer_nombre_banco(ruta_excel.parent.name))

        # Leer hoja PYG sin encabezado
        df_raw = pd.read_excel(ruta_excel, sheet_name='PYG', header=None)

        if df_raw.shape[0] < 10 or df_raw.shape[1] < 5:
            print(f"  [WARN] Archivo muy pequeno: {ruta_excel.name}")
            return pd.DataFrame()

        # Extraer fechas de la fila 5 (indice 4), desde columna C (indice 2)
        fechas_raw = df_raw.iloc[4, 2:].values
        fechas = []
        for f in fechas_raw:
            if pd.notna(f):
                if isinstance(f, datetime):
                    fechas.append(f)
                elif isinstance(f, str):
                    try:
                        fechas.append(pd.to_datetime(f))
                    except:
                        break
                else:
                    break
            else:
                break

        if len(fechas) == 0:
            print(f"  [WARN] Sin fechas validas: {ruta_excel.name}")
            return pd.DataFrame()

        # Procesar filas de datos (desde fila 6, indice 5)
        registros = []

        for idx in range(5, min(140, len(df_raw))):
            codigo_raw = df_raw.iloc[idx, 0]
            nombre = df_raw.iloc[idx, 1]

            # Determinar codigo
            if pd.isna(codigo_raw):
                continue

            codigo_str = str(codigo_raw).strip()

            if codigo_str == '--':
                # Cuenta resumen
                codigo = obtener_codigo_resumen(nombre)
                if codigo is None:
                    continue
            elif codigo_str == 'nan':
                continue
            else:
                codigo = codigo_str

            # Limpiar nombre
            if pd.isna(nombre):
                continue
            nombre_limpio = str(nombre).strip()

            # Extraer valores
            valores = df_raw.iloc[idx, 2:2+len(fechas)].values

            for i, (fecha, valor) in enumerate(zip(fechas, valores)):
                if pd.notna(valor):
                    try:
                        valor_num = float(valor)
                        registros.append({
                            'banco': nombre_banco,
                            'fecha': pd.Timestamp(fecha),
                            'codigo': codigo,
                            'cuenta': nombre_limpio,
                            'valor_acumulado': valor_num
                        })
                    except (ValueError, TypeError):
                        pass

        if len(registros) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(registros)
        return df

    except Exception as e:
        print(f"  [ERROR] {ruta_excel.name}: {e}")
        return pd.DataFrame()


def desacumular_valores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Desacumula los valores para obtener el valor de cada mes individual.

    Logica:
    - Enero: valor_mes = valor_acumulado (primer mes del anno)
    - Feb-Dic: valor_mes = valor_acumulado - valor_acumulado_mes_anterior
    """
    if df.empty:
        return df

    df = df.sort_values(['banco', 'codigo', 'fecha']).copy()
    df['ano'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month

    # Calcular valor del mes anterior (dentro del mismo banco, codigo y anno)
    df['valor_anterior'] = df.groupby(
        ['banco', 'codigo', 'ano'], observed=True
    )['valor_acumulado'].shift(1)

    # Desacumular: para enero (mes=1) o si no hay anterior, usar valor acumulado directamente
    # Para otros meses, restar el valor anterior
    df['valor_mes'] = np.where(
        (df['mes'] == 1) | (df['valor_anterior'].isna()),
        df['valor_acumulado'],
        df['valor_acumulado'] - df['valor_anterior']
    )

    return df


def calcular_suma_movil_12m(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la suma movil de 12 meses para cada banco/codigo.
    Esto permite comparar cualquier mes con cualquier otro.
    """
    if df.empty:
        return df

    df = df.sort_values(['banco', 'codigo', 'fecha']).copy()

    # Calcular suma movil de 12 meses
    df['valor_12m'] = df.groupby(
        ['banco', 'codigo'], observed=True
    )['valor_mes'].transform(
        lambda x: x.rolling(window=12, min_periods=12).sum()
    )

    return df


def main():
    print("=" * 60)
    print("PROCESAMIENTO DE HOJA PYG (PERDIDAS Y GANANCIAS)")
    print("=" * 60)

    # Crear carpeta de salida
    CARPETA_SALIDA.mkdir(exist_ok=True)

    # Buscar archivos Excel
    archivos = list(CARPETA_DATOS.glob("**/*.xlsx"))
    print(f"\nArchivos encontrados: {len(archivos)}")

    if len(archivos) == 0:
        raise RuntimeError("No se encontraron archivos Excel para PyG")

    # Procesar cada archivo
    dataframes = []
    archivos_error = []

    for i, archivo in enumerate(archivos):
        print(f"\n[{i+1}/{len(archivos)}] {archivo.parent.name}")
        df = procesar_archivo_pyg(archivo)
        if not df.empty:
            dataframes.append(df)
            print(f"  -> {len(df):,} registros")
        else:
            archivos_error.append(archivo.parent.name)

    if len(dataframes) == 0:
        raise RuntimeError("No se procesaron datos de PyG")

    if archivos_error:
        raise RuntimeError(
            f"PyG incompleto; archivos con error: {', '.join(archivos_error)}"
        )

    # Combinar todos los DataFrames
    print("\n" + "-" * 40)
    print("Combinando datos...")
    df_combinado = pd.concat(dataframes, ignore_index=True)
    print(f"Total registros acumulados: {len(df_combinado):,}")

    # Desacumular valores
    print("\nDesacumulando valores mensuales...")
    df_desacumulado = desacumular_valores(df_combinado)
    print(f"Registros despues de desacumular: {len(df_desacumulado):,}")

    # Calcular suma movil de 12 meses
    print("\nCalculando suma movil de 12 meses...")
    df_final = calcular_suma_movil_12m(df_desacumulado)

    # Seleccionar columnas finales
    columnas_finales = ['banco', 'fecha', 'codigo', 'cuenta',
                        'valor_acumulado', 'valor_mes', 'valor_12m']
    df_final = df_final[columnas_finales]
    for columna in ['banco', 'codigo', 'cuenta']:
        df_final[columna] = df_final[columna].astype('category')

    # Estadisticas
    print("\n" + "=" * 40)
    print("RESUMEN")
    print("=" * 40)
    print(f"Bancos: {df_final['banco'].nunique()}")
    print(f"Fechas: {df_final['fecha'].nunique()}")
    print(f"Cuentas unicas: {df_final['codigo'].nunique()}")
    print(f"Registros totales: {len(df_final):,}")

    # Fechas disponibles
    print(f"\nRango de fechas: {df_final['fecha'].min()} a {df_final['fecha'].max()}")

    # Verificar suma movil
    registros_con_12m = df_final['valor_12m'].notna().sum()
    print(f"Registros con valor_12m: {registros_con_12m:,} ({registros_con_12m/len(df_final)*100:.1f}%)")

    # Guardar
    ruta_salida = CARPETA_SALIDA / "pyg.parquet"
    ruta_temporal = ruta_salida.with_suffix(".parquet.tmp")
    df_final.to_parquet(ruta_temporal, index=False)
    ruta_temporal.replace(ruta_salida)
    print(f"\n[OK] Guardado: {ruta_salida}")
    print(f"    Tamano: {ruta_salida.stat().st_size / 1024 / 1024:.1f} MB")

    # Mostrar muestra de cuentas principales
    print("\n" + "-" * 40)
    print("Cuentas principales procesadas:")
    cuentas_principales = df_final[
        (df_final['codigo'].str.len() <= 3) |
        (df_final['codigo'].isin(['MNI', 'MBF', 'MNF', 'MDI', 'MOP', 'GAI', 'GDE']))
    ]['codigo'].unique()
    for c in sorted(cuentas_principales):
        nombre = df_final[df_final['codigo'] == c]['cuenta'].iloc[0]
        print(f"  {c}: {nombre}")


if __name__ == "__main__":
    main()
