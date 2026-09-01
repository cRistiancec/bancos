# Mapa de Visualizaciones - Radar Bancario Ecuador

Este documento define las visualizaciones y dashboards planificados para la aplicación "Radar Bancario". El objetivo es cubrir las dimensiones clave del análisis financiero bancario, alineado con la metodología CAMEL y el análisis de competencia.

## 1. Dashboard Ejecutivo (Panorama del Sistema)
*Visión "Big Picture" del sistema financiero en su conjunto.*

| Visualización | Tipo de Gráfico | Fuente de Datos | Descripción |
|---|---|---|---|
| **KPIs Agregados** | Tarjetas (Scorecards) | Balance General | Total Activos, Cartera Bruta, Depósitos, Patrimonio, Utilidad Neta del sistema. Muestra variación % vs año anterior. |
| **Mapa de Mercado** | Treemap | Balance General | Distribución de los bancos por tamaño de Activos. Permite ver rápidamente quién domina el mercado. |
| **Ranking Top 10** | Barras Horizontales | Balance General | Ranking de las 10 entidades más grandes por Activos (o métrica seleccionable). |
| **Concentración de Mercado** | Gauge (Medidor) / KPI | Balance General | Índice Herfindahl-Hirschman (HHI) para evaluar si el mercado es competitivo o concentrado. |
| **Evolución de Activos** | Línea de Tiempo | Balance (Histórico) | Tendencia de crecimiento del sistema en los últimos 12-24 meses. |

## 2. Análisis CAMEL (Salud Financiera)
*Indicadores clave de desempeño basados en la metodología CAMEL (Capital, Assets, Management, Earnings, Liquidity).*

### C - Capital (Patrimonio)
- **Suficiencia Patrimonial**: Relación entre Patrimonio y Activos.
- **Evolución del Patrimonio**: Crecimiento de las reservas y capital social.

### A - Assets (Calidad de Activos)
- **Índice de Morosidad**: (Cartera Improductiva / Cartera Bruta). *Crítico para evaluar riesgo.*
- **Cobertura de Morosidad**: (Provisiones / Cartera Improductiva). Capacidad del banco para absorber pérdidas.
- **Composición de Cartera**: Gráfico de pastel/barras apiladas mostrando Cartera Comercial vs. Consumo vs. Vivienda vs. Microcrédito.

### M - Management (Eficiencia)
- **Eficiencia Operativa**: (Gastos Operativos / Activo Total). Cuánto cuesta administrar cada dólar de activo.
- **Gastos vs. Ingresos**: Relación entre el gasto administrativo y el margen financiero.

### E - Earnings (Rentabilidad)
- **ROA (Return on Assets)**: (Utilidad / Activos). Rentabilidad sobre los activos totales.
- **ROE (Return on Equity)**: (Utilidad / Patrimonio). Rentabilidad para los accionistas.
- **Margen de Intermediación**: Diferencia entre tasas activas y pasivas implícitas.

### L - Liquidity (Liquidez)
- **Liquidez Corriente**: (Fondos Disponibles / Obligaciones con el Público). Capacidad de respuesta ante retiros.
- **Relación Cartera/Depósitos**: Qué porcentaje de los depósitos está colocado en créditos.

## 3. Comparador Competitivo
*Herramientas para "Benchmarking" directo entre entidades.*

- **Comparativa "Head-to-Head"**: Selección de 2 o más bancos para comparar cualquier cuenta del balance o indicador lado a lado (Barras agrupadas).
- **Ranking Completo**: Tabla ordenable con todos los bancos y múltiples indicadores (Activos, ROE, Morosidad, etc.) simultáneamente.
- **Matriz de Posicionamiento**: Gráfico de dispersión (Scatter Plot). Ej: Eje X = ROE, Eje Y = Morosidad. Tamaño burbuja = Activos. Ideal para ver "mapas estratégicos".

## 4. Evolución Histórica (Tendencias)
- **Análisis de Tendencias**: Gráfico de líneas multiseries para ver la evolución de un indicador (ej. Morosidad) a lo largo del tiempo para bancos seleccionados.
- **Estacionalidad (Opcional)**: Detección de patrones mensuales en depósitos o créditos.

## 5. Perfil Individual del Banco (Ficha)
*Vista detallada de una sola entidad.*

- **Resumen Ejecutivo**: KPIs principales del banco seleccionado.
- **Estructura de Balance**: Gráfico de barras apiladas 100% (Activos, Pasivos+Patrimonio).
- **Radar de Desempeño**: Gráfico de araña comparando al banco vs. el Promedio del Sistema en 5 ejes (Liquidez, Solvencia, Rentabilidad, Calidad Activos, Eficiencia).

---
*Este documento es dinámico y se actualizará conforme se implementen nuevas métricas en `Inicio.py`.*
