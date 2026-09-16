# -*- coding: utf-8 -*-
"""
Capa de acceso a datos: carga centralizada con validacion y limpieza.

Migrado de utils/data_loader.py sin alterar ninguna formula ni logica de
limpieza existente. Unicamente se centraliza aqui y se agregan agregaciones
de sistema que antes estaban duplicadas dentro de paginas individuales.
"""

import pandas as pd
import streamlit as st
import unicodedata
from pathlib import Path
from typing import Tuple, Dict, Any
import json

from config.indicator_mapping import CODIGOS_BALANCE

# Ruta base de datos
MASTER_DATA_DIR = Path(__file__).parent.parent / "master_data"


def _normalizar_banco(serie: pd.Series) -> pd.Series:
    """Normaliza la columna 'banco' a NFC.

    El pipeline de origen no es consistente: al menos una entidad
    ('General Rumiñahui') llega en algunos cortes con la eñe en forma NFD
    (n + tilde combinante U+0303) en vez de NFC (ñ precompuesta, U+00F1).
    Visualmente son indistinguibles pero no son la misma cadena de bytes,
    lo que rompe cualquier comparación exacta contra config/indicator_mapping.py
    (BANCOS_SISTEMA, COLORES_BANCOS) -- color gris de respaldo y falsos
    "banco sin datos" en Calidad de Datos. Se normaliza una sola vez aqui,
    en el punto central de carga, para que todo lo que consume estos
    DataFrames vea siempre la misma forma.
    """
    return serie.map(lambda v: unicodedata.normalize('NFC', v) if isinstance(v, str) else v)


def _mascara_texto_valido(serie: pd.Series) -> pd.Series:
    """True donde la serie tiene texto no vacio, sin fillna('') sobre la serie.

    Parquet puede devolver columnas de texto muy repetitivas (banco, codigo,
    cuenta, indicador) como dtype category cuando el archivo fue escrito con
    dictionary encoding -- pyarrow decide esto por archivo, no es algo que
    esta capa controle. `serie.fillna('').str.strip() != ''` revienta con
    "Cannot setitem on a Categorical with a new category" en cuanto la
    cadena vacia no es ya una categoria existente. Se evita el fillna por
    completo: NaN se trata directamente como invalido.

    Para columnas categoricas se evalua sobre `cat.categories` (unas pocas
    decenas/cientos de valores) y se usa `isin`, no `astype(str)` sobre la
    serie completa: con pandas 2.3.0/numpy 2.3.1, `astype(str)` en una
    Categorical de mas de ~5 millones de filas (balance.parquet tiene 8.1M)
    degrada de forma abrupta y no llega a terminar en un tiempo razonable.
    """
    if isinstance(serie.dtype, pd.CategoricalDtype):
        categorias_validas = {
            c for c in serie.cat.categories if isinstance(c, str) and c.strip() != ''
        }
        return serie.isin(categorias_validas)
    return serie.notna() & (serie.astype(str).str.strip() != '')


@st.cache_data(ttl=3600)
def cargar_balance() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Carga balance.parquet con limpieza y metricas de calidad.

    Returns:
        Tuple[DataFrame, Dict]: DataFrame limpio y metricas de calidad
    """
    filepath = MASTER_DATA_DIR / "balance.parquet"

    if not filepath.exists():
        raise FileNotFoundError(f"No se encontro {filepath}")

    df_original = pd.read_parquet(filepath)
    registros_originales = len(df_original)

    # Limpieza
    df = df_original.copy()

    # 1. Filtrar cuentas vacias
    mask_cuenta_valida = _mascara_texto_valido(df['cuenta'])
    df = df[mask_cuenta_valida]

    # 2. Filtrar valores nulos en columnas clave
    df = df.dropna(subset=['banco', 'fecha'])
    df['banco'] = _normalizar_banco(df['banco'])

    # 3. Convertir fecha a datetime si no lo es
    if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
        df['fecha'] = pd.to_datetime(df['fecha'])

    # Metricas de calidad
    calidad = {
        'registros_originales': registros_originales,
        'registros_limpios': len(df),
        'registros_eliminados': registros_originales - len(df),
        'pct_eliminados': round((registros_originales - len(df)) / registros_originales * 100, 2),
        'bancos': df['banco'].nunique(),
        'fechas': df['fecha'].nunique(),
        'fecha_min': df['fecha'].min(),
        'fecha_max': df['fecha'].max(),
        'nulos_valor': df['valor'].isna().sum(),
        'nulos_codigo': df['codigo'].isna().sum(),
    }

    return df, calidad


@st.cache_data(ttl=3600)
def cargar_pyg() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Carga pyg.parquet (Perdidas y Ganancias) con metricas de calidad.

    Los datos de PYG tienen una estructura especial:
    - valor_acumulado: Valor acumulado en el año (como viene en el Excel)
    - valor_mes: Valor desacumulado del mes individual
    - valor_12m: Suma movil de 12 meses (para comparabilidad)

    Returns:
        Tuple[DataFrame, Dict]: DataFrame y metricas de calidad
    """
    filepath = MASTER_DATA_DIR / "pyg.parquet"

    if not filepath.exists():
        raise FileNotFoundError(f"No se encontro {filepath}")

    df_original = pd.read_parquet(filepath)
    registros_originales = len(df_original)

    df = df_original.copy()

    # Filtrar cuentas vacias
    mask_cuenta_valida = _mascara_texto_valido(df['cuenta'])
    df = df[mask_cuenta_valida]

    # Filtrar valores nulos en columnas clave
    df = df.dropna(subset=['banco', 'fecha'])
    df['banco'] = _normalizar_banco(df['banco'])

    # Convertir fecha a datetime si no lo es
    if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
        df['fecha'] = pd.to_datetime(df['fecha'])

    # Metricas de calidad
    calidad = {
        'registros_originales': registros_originales,
        'registros_limpios': len(df),
        'registros_eliminados': registros_originales - len(df),
        'pct_eliminados': round((registros_originales - len(df)) / registros_originales * 100, 2),
        'bancos': df['banco'].nunique(),
        'fechas': df['fecha'].nunique(),
        'fecha_min': df['fecha'].min(),
        'fecha_max': df['fecha'].max(),
        'cuentas_unicas': df['codigo'].nunique(),
        'registros_con_12m': df['valor_12m'].notna().sum(),
        'pct_con_12m': round(df['valor_12m'].notna().sum() / len(df) * 100, 1),
    }

    return df, calidad


@st.cache_data(ttl=3600)
def cargar_camel() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Carga camel.parquet (Indicadores CAMEL) con metricas de calidad.

    Los datos de CAMEL incluyen indicadores financieros categorizados por:
    - C: Capital (solvencia)
    - A: Assets (activos, morosidad, cobertura)
    - M: Management (eficiencia operativa)
    - E: Earnings (rentabilidad)
    - L: Liquidity (liquidez)
    - Composicion Cartera (participacion por tipo de credito)

    Returns:
        Tuple[DataFrame, Dict]: DataFrame y metricas de calidad
    """
    filepath = MASTER_DATA_DIR / "camel.parquet"

    if not filepath.exists():
        raise FileNotFoundError(f"No se encontro {filepath}")

    df_original = pd.read_parquet(filepath)
    registros_originales = len(df_original)

    df = df_original.copy()

    # Filtrar indicadores vacios
    mask_indicador_valido = _mascara_texto_valido(df['indicador'])
    df = df[mask_indicador_valido]

    # Filtrar valores nulos en columnas clave
    df = df.dropna(subset=['banco', 'fecha'])
    df['banco'] = _normalizar_banco(df['banco'])

    # Convertir fecha a datetime si no lo es
    if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
        df['fecha'] = pd.to_datetime(df['fecha'])

    # Metricas de calidad
    calidad = {
        'registros_originales': registros_originales,
        'registros_limpios': len(df),
        'registros_eliminados': registros_originales - len(df),
        'pct_eliminados': round((registros_originales - len(df)) / registros_originales * 100, 2),
        'bancos': df['banco'].nunique(),
        'fechas': df['fecha'].nunique(),
        'fecha_min': df['fecha'].min(),
        'fecha_max': df['fecha'].max(),
        'indicadores_unicos': df['codigo'].nunique(),
        'categorias': df['categoria'].unique().tolist(),
    }

    return df, calidad


@st.cache_data(ttl=3600)
def cargar_metadata() -> Dict[str, Any]:
    """
    Carga metadata.json con informacion de la ultima actualizacion.
    """
    filepath = MASTER_DATA_DIR / "metadata.json"

    if not filepath.exists():
        return {'error': 'metadata.json no encontrado'}

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


@st.cache_data(ttl=3600)
def cargar_todos_los_datos() -> Dict[str, Any]:
    """
    Carga todos los datasets de una vez con sus metricas de calidad.

    Returns:
        Dict con DataFrames y metricas consolidadas
    """
    resultado = {
        'dataframes': {},
        'calidad': {},
        'metadata': None,
        'errores': []
    }

    try:
        df_balance, cal_balance = cargar_balance()
        resultado['dataframes']['balance'] = df_balance
        resultado['calidad']['balance'] = cal_balance
    except Exception as e:
        resultado['errores'].append(f"balance: {str(e)}")

    try:
        df_pyg, cal_pyg = cargar_pyg()
        resultado['dataframes']['pyg'] = df_pyg
        resultado['calidad']['pyg'] = cal_pyg
    except Exception as e:
        resultado['errores'].append(f"pyg: {str(e)}")

    try:
        df_camel, cal_camel = cargar_camel()
        resultado['dataframes']['camel'] = df_camel
        resultado['calidad']['camel'] = cal_camel
    except Exception as e:
        resultado['errores'].append(f"camel: {str(e)}")

    try:
        resultado['metadata'] = cargar_metadata()
    except Exception as e:
        resultado['errores'].append(f"metadata: {str(e)}")

    if resultado['dataframes']:
        total_registros = sum(
            cal.get('registros_limpios', 0)
            for cal in resultado['calidad'].values()
        )
        resultado['resumen'] = {
            'total_registros': total_registros,
            'datasets_cargados': len(resultado['dataframes']),
            'errores_carga': len(resultado['errores']),
        }

    return resultado


def obtener_fechas_disponibles(df: pd.DataFrame) -> list:
    """
    Obtiene lista de fechas unicas ordenadas (mas reciente primero).
    """
    fechas = df['fecha'].dropna().unique()
    return sorted(fechas, reverse=True)


def obtener_bancos_disponibles(df: pd.DataFrame) -> list:
    """
    Obtiene lista de bancos unicos ordenados alfabeticamente.
    """
    return sorted(df['banco'].unique())


def filtrar_por_fecha(df: pd.DataFrame, fecha) -> pd.DataFrame:
    """
    Filtra DataFrame por fecha especifica.
    """
    return df[df['fecha'] == fecha].copy()


def filtrar_por_banco(df: pd.DataFrame, banco: str) -> pd.DataFrame:
    """
    Filtra DataFrame por banco especifico.
    """
    return df[df['banco'] == banco].copy()


def filtrar_por_codigo(df: pd.DataFrame, codigo: str) -> pd.DataFrame:
    """
    Filtra DataFrame por codigo contable.
    """
    return df[df['codigo'] == codigo].copy()


def obtener_valor_cuenta(
    df: pd.DataFrame,
    banco: str,
    fecha,
    codigo: str,
    hoja: str = 'BAL'
) -> float:
    """
    Obtiene el valor de una cuenta especifica para un banco y fecha.
    """
    mask = (
        (df['banco'] == banco) &
        (df['fecha'] == fecha) &
        (df['codigo'] == codigo) &
        (df['hoja'] == hoja)
    )
    resultado = df.loc[mask, 'valor']

    if resultado.empty:
        return None
    return resultado.iloc[0]


# =============================================================================
# AGREGACIONES DE SISTEMA (antes duplicadas inline en paginas individuales)
# =============================================================================

@st.cache_data
def calcular_metricas_sistema(df: pd.DataFrame, fecha) -> dict:
    """Calcula metricas agregadas del sistema para una fecha.

    Migrado sin cambios desde pages/1_Panorama.py::calcular_metricas_sistema.
    """
    df_fecha = df[df['fecha'] == fecha]

    metricas = {}

    activos = df_fecha[df_fecha['codigo'] == CODIGOS_BALANCE['activo_total']]
    metricas['total_activos'] = activos['valor'].sum() / 1000 if not activos.empty else 0

    cartera = df_fecha[df_fecha['codigo'] == CODIGOS_BALANCE['cartera_creditos']]
    metricas['total_cartera'] = cartera['valor'].sum() / 1000 if not cartera.empty else 0

    depositos = df_fecha[df_fecha['codigo'] == CODIGOS_BALANCE['obligaciones_publico']]
    metricas['total_depositos'] = depositos['valor'].sum() / 1000 if not depositos.empty else 0

    patrimonio = df_fecha[df_fecha['codigo'] == CODIGOS_BALANCE['patrimonio']]
    metricas['total_patrimonio'] = patrimonio['valor'].sum() / 1000 if not patrimonio.empty else 0

    fondos = df_fecha[df_fecha['codigo'] == CODIGOS_BALANCE['fondos_disponibles']]
    metricas['fondos_disponibles'] = fondos['valor'].sum() / 1000 if not fondos.empty else 0

    metricas['num_bancos'] = df_fecha['banco'].nunique()

    return metricas


def obtener_contexto_sistema() -> Dict[str, Any]:
    """Contexto agregado para el header institucional: bancos, registros,
    fecha de corte y ultima actualizacion. No calcula indicadores de riesgo,
    solo metadatos operativos de la plataforma.
    """
    contexto = {
        'num_bancos': None,
        'total_registros': None,
        'fecha_corte': None,
        'fecha_actualizacion': None,
        'datos_disponibles': False,
    }

    try:
        df_balance, calidad_balance = cargar_balance()
        contexto['num_bancos'] = calidad_balance.get('bancos')
        contexto['fecha_corte'] = calidad_balance.get('fecha_max')
        contexto['datos_disponibles'] = True

        total = calidad_balance.get('registros_limpios', 0)
        try:
            _, calidad_pyg = cargar_pyg()
            total += calidad_pyg.get('registros_limpios', 0)
        except Exception:
            pass
        try:
            _, calidad_camel = cargar_camel()
            total += calidad_camel.get('registros_limpios', 0)
        except Exception:
            pass
        contexto['total_registros'] = total
    except Exception:
        pass

    metadata = cargar_metadata()
    if metadata and 'error' not in metadata:
        contexto['fecha_actualizacion'] = metadata.get('fecha_actualizacion')

    return contexto
