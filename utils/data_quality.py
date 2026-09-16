# -*- coding: utf-8 -*-
"""
Funciones de validacion y analisis de calidad de datos.
"""

import pandas as pd
from typing import Dict, List, Any
import streamlit as st

# Importar configuracion
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.indicator_mapping import BANCOS_SISTEMA


@st.cache_data
def calcular_completitud_general(calidad_dict: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Calcula metricas de completitud consolidadas.

    Args:
        calidad_dict: Diccionario con metricas de calidad por dataset

    Returns:
        Dict con metricas consolidadas
    """
    total_originales = sum(
        cal.get('registros_originales', 0)
        for cal in calidad_dict.values()
    )
    total_limpios = sum(
        cal.get('registros_limpios', 0)
        for cal in calidad_dict.values()
    )

    if total_originales == 0:
        return {'pct_completitud': 0, 'total_registros': 0}

    return {
        'pct_completitud': round(total_limpios / total_originales * 100, 2),
        'total_registros': total_limpios,
        'registros_eliminados': total_originales - total_limpios,
        'datasets': len(calidad_dict),
    }


@st.cache_data
def validar_cobertura_bancos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera matriz de cobertura bancos x anos.

    Args:
        df: DataFrame con columnas 'banco' y 'fecha'

    Returns:
        DataFrame pivotado con bancos en filas y anos en columnas
    """
    df_temp = df.copy()
    df_temp['ano'] = df_temp['fecha'].dt.year

    # Contar registros por banco y ano
    cobertura = df_temp.groupby(['banco', 'ano'], observed=True).size().unstack(fill_value=0)

    # Convertir a binario (tiene datos o no)
    cobertura_binaria = (cobertura > 0).astype(int)

    return cobertura_binaria


@st.cache_data
def calcular_cobertura_por_fecha(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula cuantos bancos tienen datos por cada fecha.

    Returns:
        DataFrame con fecha y conteo de bancos
    """
    cobertura = df.groupby('fecha')['banco'].nunique().reset_index()
    cobertura.columns = ['fecha', 'bancos_con_datos']
    cobertura = cobertura.sort_values('fecha')

    # Agregar columna de ano para facilitar visualizacion
    cobertura['ano'] = cobertura['fecha'].dt.year
    cobertura['mes'] = cobertura['fecha'].dt.month

    return cobertura


@st.cache_data
def detectar_bancos_faltantes(df: pd.DataFrame) -> List[str]:
    """
    Identifica bancos que deberian estar pero no estan en los datos.

    Returns:
        Lista de bancos faltantes
    """
    bancos_presentes = set(df['banco'].unique())
    bancos_esperados = set(BANCOS_SISTEMA)

    faltantes = bancos_esperados - bancos_presentes
    return sorted(list(faltantes))


@st.cache_data
def detectar_fechas_faltantes(df: pd.DataFrame) -> List:
    """
    Identifica gaps en la serie temporal mensual.

    Returns:
        Lista de fechas faltantes
    """
    fechas = df['fecha'].dropna().unique()
    if len(fechas) == 0:
        return []

    fecha_min = pd.Timestamp(min(fechas))
    fecha_max = pd.Timestamp(max(fechas))

    # Generar rango mensual esperado
    rango_esperado = pd.date_range(
        start=fecha_min,
        end=fecha_max,
        freq='ME'  # Month End
    )

    # Convertir fechas existentes a set para comparacion
    fechas_existentes = set(pd.to_datetime(fechas).normalize())
    fechas_esperadas = set(rango_esperado.normalize())

    faltantes = fechas_esperadas - fechas_existentes
    return sorted(list(faltantes))


@st.cache_data
def analizar_nulos_por_indicador(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Analiza indicadores con mayor porcentaje de valores nulos.

    Args:
        df: DataFrame de indicadores
        top_n: Numero de indicadores a retornar

    Returns:
        DataFrame con indicador, nulos y porcentaje
    """
    nulos_por_cuenta = df.groupby('cuenta').agg({
        'valor': [
            ('total', 'count'),
            ('nulos', lambda x: x.isna().sum()),
        ]
    })

    nulos_por_cuenta.columns = ['total', 'nulos']
    nulos_por_cuenta['pct_nulos'] = round(
        nulos_por_cuenta['nulos'] / nulos_por_cuenta['total'] * 100, 2
    )
    nulos_por_cuenta = nulos_por_cuenta.sort_values('pct_nulos', ascending=False)

    return nulos_por_cuenta.head(top_n).reset_index()


@st.cache_data
def validar_rangos_indicadores(
    df: pd.DataFrame,
    indicador_col: str = 'cuenta',
    valor_col: str = 'valor'
) -> pd.DataFrame:
    """
    Detecta valores fuera de rangos esperados para indicadores.

    Returns:
        DataFrame con alertas de valores anomalos
    """
    alertas = []

    # Validar morosidad (0-100%)
    mask_morosidad = df[indicador_col].str.contains('MOROSIDAD', case=False, na=False)
    if mask_morosidad.any():
        df_mor = df[mask_morosidad]
        anomalos = df_mor[(df_mor[valor_col] < 0) | (df_mor[valor_col] > 100)]
        if len(anomalos) > 0:
            alertas.append({
                'indicador': 'Morosidad',
                'tipo': 'Fuera de rango [0-100%]',
                'registros_afectados': len(anomalos),
                'valores_ejemplo': anomalos[valor_col].head(3).tolist()
            })

    # Validar ROE/ROA (rangos razonables)
    for ratio in ['ROE', 'ROA']:
        mask = df[indicador_col].str.contains(ratio, case=False, na=False)
        if mask.any():
            df_ratio = df[mask]
            anomalos = df_ratio[(df_ratio[valor_col] < -100) | (df_ratio[valor_col] > 100)]
            if len(anomalos) > 0:
                alertas.append({
                    'indicador': ratio,
                    'tipo': 'Fuera de rango [-100, 100%]',
                    'registros_afectados': len(anomalos),
                    'valores_ejemplo': anomalos[valor_col].head(3).tolist()
                })

    return pd.DataFrame(alertas)


@st.cache_data
def validar_ecuacion_contable(
    df: pd.DataFrame,
    fecha=None,
    tolerancia: float = 0.01
) -> pd.DataFrame:
    """
    Valida que Activo = Pasivo + Patrimonio para cada banco.

    Args:
        df: DataFrame de balance
        fecha: Fecha especifica a validar (None = ultima fecha)
        tolerancia: Porcentaje de tolerancia permitido

    Returns:
        DataFrame con resultados de validacion por banco
    """
    if fecha is None:
        fecha = df['fecha'].max()

    # NOTA: la version original filtraba tambien por (df['hoja']=='BAL'),
    # columna que no existe en balance.parquet (columnas reales: banco,
    # fecha, codigo, cuenta, valor, nivel) -- cada parquet ya corresponde a
    # una unica hoja, por lo que el filtro era redundante e incorrecto
    # (habria lanzado KeyError). Ver docs/AUDITORIA_COMPLETA.md seccion 5.
    df_fecha = df[df['fecha'] == fecha]

    resultados = []

    for banco in df_fecha['banco'].unique():
        df_banco = df_fecha[df_fecha['banco'] == banco]

        # Obtener valores por codigo
        activo = df_banco[df_banco['codigo'] == '1']['valor'].sum()
        pasivo = df_banco[df_banco['codigo'] == '2']['valor'].sum()
        patrimonio = df_banco[df_banco['codigo'] == '3']['valor'].sum()

        # Calcular diferencia
        diferencia = activo - (pasivo + patrimonio)
        pct_diferencia = abs(diferencia) / activo * 100 if activo > 0 else 0

        # Determinar estado
        if pct_diferencia <= tolerancia * 100:
            estado = 'OK'
        elif pct_diferencia <= 1:
            estado = 'Advertencia'
        else:
            estado = 'Error'

        resultados.append({
            'banco': banco,
            'activo': activo,
            'pasivo': pasivo,
            'patrimonio': patrimonio,
            'pasivo_patrimonio': pasivo + patrimonio,
            'diferencia': diferencia,
            'pct_diferencia': round(pct_diferencia, 4),
            'estado': estado
        })

    return pd.DataFrame(resultados).sort_values('pct_diferencia', ascending=False)


def generar_resumen_calidad(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera un resumen ejecutivo de calidad de datos.

    Args:
        datos: Resultado de cargar_todos_los_datos()

    Returns:
        Dict con resumen de calidad
    """
    resumen = {
        'estado_general': 'OK',
        'alertas': [],
        'metricas': {},
    }

    if not datos.get('dataframes'):
        resumen['estado_general'] = 'ERROR'
        resumen['alertas'].append('No se pudieron cargar los datos')
        return resumen

    # Metricas de completitud
    completitud = calcular_completitud_general(datos.get('calidad', {}))
    resumen['metricas']['completitud'] = completitud

    # Verificar bancos faltantes
    if 'balance' in datos['dataframes']:
        df_balance = datos['dataframes']['balance']
        bancos_faltantes = detectar_bancos_faltantes(df_balance)
        if bancos_faltantes:
            resumen['alertas'].append(
                f"Bancos faltantes: {', '.join(bancos_faltantes)}"
            )
            resumen['metricas']['bancos_faltantes'] = bancos_faltantes

        # Verificar fechas faltantes
        fechas_faltantes = detectar_fechas_faltantes(df_balance)
        if fechas_faltantes:
            resumen['alertas'].append(
                f"Hay {len(fechas_faltantes)} fechas faltantes en la serie temporal"
            )
            resumen['metricas']['fechas_faltantes'] = len(fechas_faltantes)

    # Verificar nulos en indicadores
    if 'indicadores' in datos['dataframes']:
        cal_ind = datos['calidad'].get('indicadores', {})
        pct_nulos = cal_ind.get('pct_nulos_valor', 0)
        if pct_nulos > 20:
            resumen['alertas'].append(
                f"Alto porcentaje de valores nulos en indicadores: {pct_nulos}%"
            )

    # Determinar estado general
    if len(resumen['alertas']) > 3:
        resumen['estado_general'] = 'REVISAR'
    elif len(resumen['alertas']) > 0:
        resumen['estado_general'] = 'ADVERTENCIA'

    return resumen


def exportar_reporte_calidad(
    datos: Dict[str, Any],
    filepath: str = 'reporte_calidad.xlsx'
) -> str:
    """
    Exporta reporte completo de calidad a Excel.

    Returns:
        Ruta del archivo generado
    """
    import io

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Resumen general
        resumen = generar_resumen_calidad(datos)
        df_resumen = pd.DataFrame([{
            'Metrica': k,
            'Valor': str(v)
        } for k, v in resumen['metricas'].items()])
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)

        # Alertas
        df_alertas = pd.DataFrame({'Alerta': resumen['alertas']})
        df_alertas.to_excel(writer, sheet_name='Alertas', index=False)

        # Cobertura por banco
        if 'balance' in datos['dataframes']:
            cobertura = validar_cobertura_bancos(datos['dataframes']['balance'])
            cobertura.to_excel(writer, sheet_name='Cobertura_Bancos')

        # Indicadores con nulos
        if 'indicadores' in datos['dataframes']:
            nulos = analizar_nulos_por_indicador(datos['dataframes']['indicadores'])
            nulos.to_excel(writer, sheet_name='Nulos_Indicadores', index=False)

        # Validacion contable
        if 'balance' in datos['dataframes']:
            ecuacion = validar_ecuacion_contable(datos['dataframes']['balance'])
            ecuacion.to_excel(writer, sheet_name='Validacion_Contable', index=False)

    output.seek(0)
    return output
