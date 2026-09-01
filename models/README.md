# Modelos Predictivos / IA — Fase 2

## Implementado

- **`forecasting.py`** — suavizado exponencial de Holt (`statsmodels.tsa.holtwinters.ExponentialSmoothing`,
  tendencia aditiva, sin estacionalidad) sobre indicadores CAMEL, por banco o promedio del sistema.
  Usado en `pages/modelos_predictivos.py` (pestaña Forecasting).
- **`anomaly_detection.py`** — `sklearn.ensemble.IsolationForest` sobre nivel +
  variación mes a mes de la serie. Usado en la pestaña Detección de Anomalías.
- **`clustering.py`** — `sklearn.cluster.KMeans` + `PCA` (solo para
  visualizar) sobre el vector de indicadores CAMEL de cada banco en una
  fecha. Usado en la pestaña Clustering de Bancos.

Los tres son herramientas **exploratorias** sobre datos reales, no modelos
regulatorios ni predicciones garantizadas — cada página los etiqueta como
tales. Metodología detallada en `docs/ManualTecnico.md`.

## Pendiente (requiere trabajo previo de definición)

- **Modelos supervisados** (XGBoost / LightGBM / Random Forest / LSTM) para
  predecir eventos (p. ej. deterioro de mora, quiebra) — requieren definir y
  validar una variable objetivo histórica, ausente en el pipeline actual.
  No implementar sin esa definición explícita.

## No implementar sin nueva fuente de datos

- Cualquier modelo que dependa de datos de mercado (tasas, tipo de cambio,
  precios de instrumentos), datos a nivel de depositante/contraparte, o
  eventos de pérdida operacional — ver `docs/AUDITORIA_COMPLETA.md`,
  sección 6 (matriz de factibilidad).
