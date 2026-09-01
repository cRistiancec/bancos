# -*- coding: utf-8 -*-
"""
Forecasting sobre series reales (indicadores CAMEL o cuentas de balance).

Usa suavizado exponencial de Holt (tendencia aditiva, sin estacionalidad --
la mayoria de indicadores prudenciales no tienen un patron estacional claro
y forzar estacionalidad sobre series cortas/ruidosas produce proyecciones
menos confiables). Es una PROYECCION ESTADISTICA sobre datos historicos,
no una prediccion garantizada -- se etiqueta asi en la UI.

La banda de incertidumbre es una aproximacion tipo caminata aleatoria
(desviacion estandar del residuo * raiz(horizonte)), no un intervalo de
confianza formal del modelo de Holt -- se documenta explicitamente.
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

MINIMO_PUNTOS = 12  # al menos 1 año de historia mensual para proyectar con algo de confianza


class SerieInsuficiente(Exception):
    """La serie no tiene suficientes puntos para un forecast confiable."""


def proyectar_serie(fechas: pd.Series, valores: pd.Series, n_periodos: int = 6) -> pd.DataFrame:
    """Proyecta n_periodos meses hacia adelante.

    Returns: DataFrame [fecha, valor, tipo ('historico'|'proyeccion'), banda_inf, banda_sup]
    """
    df = pd.DataFrame({'fecha': pd.to_datetime(fechas), 'valor': valores}).dropna().sort_values('fecha')
    df = df.drop_duplicates(subset='fecha')

    if len(df) < MINIMO_PUNTOS:
        raise SerieInsuficiente(f"Se requieren al menos {MINIMO_PUNTOS} periodos con dato; hay {len(df)}.")

    serie = pd.Series(df['valor'].values, index=pd.DatetimeIndex(df['fecha'])).asfreq('ME')
    serie = serie.interpolate(limit_direction='both')

    modelo = ExponentialSmoothing(serie, trend='add', seasonal=None, initialization_method='estimated').fit()
    residual_std = float((serie - modelo.fittedvalues).std())
    if pd.isna(residual_std):
        residual_std = 0.0

    forecast = modelo.forecast(n_periodos)
    horizontes = np.arange(1, n_periodos + 1)
    banda = 1.96 * residual_std * np.sqrt(horizontes)

    df_hist = pd.DataFrame({
        'fecha': serie.index, 'valor': serie.values, 'tipo': 'historico',
        'banda_inf': np.nan, 'banda_sup': np.nan,
    })
    df_fore = pd.DataFrame({
        'fecha': forecast.index, 'valor': forecast.values, 'tipo': 'proyeccion',
        'banda_inf': forecast.values - banda, 'banda_sup': forecast.values + banda,
    })

    return pd.concat([df_hist, df_fore], ignore_index=True)


def backtest_serie(fechas: pd.Series, valores: pd.Series, n_periodos_test: int = 6) -> dict:
    """Mide que tan bueno habria sido el modelo de proyectar_serie() sobre
    el pasado reciente: separa los ultimos `n_periodos_test` meses como
    conjunto de prueba, ajusta Holt SOLO sobre el resto (mismo modelo que
    proyectar_serie), y compara la proyeccion contra los valores reales que
    ya conocemos de ese periodo.

    No garantiza nada sobre el futuro -- mide desempeño historico del mismo
    metodo, para que el usuario pueda decidir cuanto confiar en la
    proyeccion de esa serie especifica (unos indicadores son mas
    predecibles que otros).

    Returns: dict con mae, rmse, mape (None si algun valor real de prueba
    esta practicamente en cero, donde MAPE no esta definido), y las series
    de fecha/valor real/valor predicho del periodo de prueba.
    """
    df = pd.DataFrame({'fecha': pd.to_datetime(fechas), 'valor': valores}).dropna().sort_values('fecha')
    df = df.drop_duplicates(subset='fecha')

    if len(df) < MINIMO_PUNTOS + n_periodos_test:
        raise SerieInsuficiente(
            f"Se requieren al menos {MINIMO_PUNTOS + n_periodos_test} periodos con dato "
            f"({MINIMO_PUNTOS} para entrenar + {n_periodos_test} para probar); hay {len(df)}."
        )

    df_train = df.iloc[:-n_periodos_test]
    df_test = df.iloc[-n_periodos_test:]

    proyeccion = proyectar_serie(df_train['fecha'], df_train['valor'], n_periodos=n_periodos_test)
    predicho = proyeccion[proyeccion['tipo'] == 'proyeccion'].reset_index(drop=True)

    real = df_test['valor'].reset_index(drop=True)
    error = real - predicho['valor']

    mae = float(error.abs().mean())
    rmse = float(np.sqrt((error ** 2).mean()))
    mape = None
    if (real.abs() > 1e-6).all():
        mape = float((error.abs() / real.abs()).mean() * 100)

    return {
        'mae': mae, 'rmse': rmse, 'mape': mape,
        'fecha_test': df_test['fecha'].reset_index(drop=True),
        'valor_real_test': real,
        'valor_predicho_test': predicho['valor'],
    }
