# Módulo: Series Temporales Avanzadas

## Descripción General

Módulo especializado en análisis temporal del sistema bancario ecuatoriano con visualizaciones de series de tiempo que permiten identificar tendencias, estacionalidad, anomalías y relaciones entre variables.

## Estado: ✅ IMPLEMENTADO

- **Archivo**: `archived_pages/6_Series_Temporales.py (no existe en repo)`
- **Nombre**: "⏱️ Series Temporales"
- **Posición**: Después del módulo Perfil
- **Fecha de Implementación**: 25 de enero de 2026
- **Versión**: 1.0

## Objetivos

1. **Análisis de Tendencias**: Identificar patrones de largo plazo
2. **Estacionalidad**: Detectar ciclos mensuales/anuales
3. **Comparaciones Múltiples**: Visualizar múltiples bancos simultáneamente
4. **Correlaciones**: Analizar relaciones entre variables
5. **Anomalías**: Detectar comportamientos atípicos

---

## Sección 1: Panel de Control Temporal

### Filtros Globales
```
┌─────────────────────────────────────────────────────┐
│ CONFIGURACIÓN TEMPORAL                               │
├─────────────────────────────────────────────────────┤
│ Rango de Fechas:  [====|-----------|====] 2003-2025 │
│                   2015              2025             │
│                                                      │
│ Granularidad:     ○ Mensual  ● Trimestral  ○ Anual │
│                                                      │
│ Bancos:           [x] Pichincha  [x] Guayaquil      │
│                   [x] Pacifico   [ ] Produbanco     │
│                   [Seleccionar todos] [Limpiar]     │
└─────────────────────────────────────────────────────┘
```

---

## Sección 2: Evolución Comparativa (Multi-Línea)

### Visualización Principal
**Tipo**: Gráfico de líneas múltiples con área sombreada

**Características**:
- Hasta 10 bancos simultáneos
- Toggle para normalizar valores (base 100 en fecha inicial)
- Selección de métrica (Activos, Cartera, Depósitos, etc.)
- Modo de visualización:
  - **Valores Absolutos**: Millones USD
  - **Valores Indexados**: Base 100 = fecha inicial
  - **Participación de Mercado**: % del total sistema

**Interacciones**:
- Click en leyenda para ocultar/mostrar banco
- Doble click para aislar un banco
- Zoom temporal con selección de área
- Tooltip comparativo al pasar cursor

### Código Ejemplo
```python
fig = go.Figure()

for banco in bancos_seleccionados:
    df_banco = obtener_serie_banco(df, banco, codigo_cuenta)

    fig.add_trace(go.Scatter(
        x=df_banco['fecha'],
        y=df_banco['valor'],
        name=banco,
        mode='lines',
        line=dict(width=2),
        hovertemplate='<b>%{fullData.name}</b><br>' +
                      'Fecha: %{x|%b %Y}<br>' +
                      'Valor: $%{y:,.0f}M<br>' +
                      '<extra></extra>'
    ))

fig.update_layout(
    title="Evolución Comparativa",
    xaxis_title="Tiempo",
    yaxis_title="Millones USD",
    hovermode="x unified",
    legend=dict(orientation="h", y=-0.2)
)
```

---

## Sección 3: Análisis de Tendencia con Descomposición

### Panel de Tres Gráficos
```
┌──────────────────────────────────────────────────────┐
│ DESCOMPOSICIÓN DE SERIE TEMPORAL                     │
├──────────────────────────────────────────────────────┤
│                                                       │
│ ┌─────────────────────────────────────────────────┐  │
│ │ 1. SERIE ORIGINAL                               │  │
│ │    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      │  │
│ └─────────────────────────────────────────────────┘  │
│                                                       │
│ ┌─────────────────────────────────────────────────┐  │
│ │ 2. TENDENCIA (Media Móvil 12 meses)             │  │
│ │    ──────────────────────────────               │  │
│ └─────────────────────────────────────────────────┘  │
│                                                       │
│ ┌─────────────────────────────────────────────────┐  │
│ │ 3. COMPONENTE ESTACIONAL                        │  │
│ │    ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿                  │  │
│ └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

**Características**:
- Media móvil configurable (3, 6, 12, 24 meses)
- Detección de estacionalidad mensual
- Identificación de valores atípicos (outliers)

**Implementación**:
```python
# Media móvil
df['tendencia'] = df['valor'].rolling(window=12, center=True).mean()

# Componente estacional (promedio por mes)
df['mes'] = df['fecha'].dt.month
estacionalidad = df.groupby('mes')['valor'].mean()

# Residuos
df['residuo'] = df['valor'] - df['tendencia']
```

---

## Sección 4: Heatmap Temporal

### Matriz Año × Mes
```
           Ene  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec
2015       ██   ██   ██   ██   ██   ██   ██   ██   ██   ██   ██   ██
2016       ██   ██   ██   ██   ██   ██   ██   ██   ██   ██   ██   ██
2017       ██   ██   ██   ██   ██   ██   ██   ██   ██   ██   ██   ██
...
2025       ██   ██   ██   ██   ██   ██   ██   ██   ██   ██   ██   ░░

Escala: Crecimiento mensual (%)
        [-10%]  [0%]  [10%]  [20%]  [30%]
          ██     ░░     ░░     ░░     ░░
```

**Métricas para Heatmap**:
- Crecimiento mes a mes (%)
- Valor absoluto (millones USD)
- Participación de mercado (%)
- Indicadores CAMEL

**Ventajas**:
- Identifica estacionalidad visual
- Detecta años anómalos rápidamente
- Compara patrones entre períodos

---

## Sección 5: Correlación entre Variables

### Gráfico de Dispersión Temporal
**Tipo**: Scatter plot con línea de regresión + histograma marginal

**Ejemplo**: Cartera vs Depósitos
```
┌───────────────────────────────────────────────┐
│    Relación: Cartera de Créditos vs Depósitos│
│                                                │
│ Dep│                                     ●●●   │
│    │                               ●●●●●       │
│    │                         ●●●●●             │
│    │                   ●●●●●                   │
│    │             ●●●●●                         │
│    │       ●●●●●                               │
│    └────────────────────────────────── Cartera│
│                                                │
│    R² = 0.94   Correlación = 0.97             │
└───────────────────────────────────────────────┘
```

**Características**:
- Colorear puntos por año (gradiente temporal)
- Tamaño de punto = Total Activos
- Línea de tendencia con ecuación
- Coeficiente de correlación

**Variables a Correlacionar**:
1. Cartera vs Depósitos
2. Activos vs Patrimonio
3. Morosidad vs Cobertura
4. ROE vs Solvencia

---

## Sección 6: Análisis de Velocidad de Cambio

### Gráfico de Derivada (Aceleración)
**Tipo**: Barras + línea de variación porcentual

```
┌──────────────────────────────────────────────┐
│ VELOCIDAD DE CRECIMIENTO                     │
│                                               │
│  30%│        ██                               │
│     │     ██ ██                               │
│  20%│  ██ ██ ██ ██                            │
│     │  ██ ██ ██ ██ ██                         │
│  10%│  ██ ██ ██ ██ ██ ██                      │
│     │  ██ ██ ██ ██ ██ ██ ██                   │
│   0%├──██─██─██─██─██─██─██─██────────────────│
│     │     ── ── ── ──                          │
│ -10%│        ██    ██                          │
│     └─────────────────────────────────────────│
│      Q1  Q2  Q3  Q4  Q1  Q2  Q3  Q4           │
│      2024         2025                        │
└──────────────────────────────────────────────┘
```

**Métricas**:
- Crecimiento trimestral (QoQ)
- Crecimiento anual (YoY)
- Aceleración (cambio en la tasa de crecimiento)

---

## Sección 7: Ranking Dinámico (Race Chart)

### Animación de Posiciones
**Tipo**: Barras horizontales animadas en el tiempo

```
Diciembre 2015              Diciembre 2020
Banco A  ████████████       Banco B  ██████████████
Banco B  ██████████         Banco A  ████████████
Banco C  ████████           Banco D  ███████████
                            Banco C  ████████

[▶ Play] [⏸ Pause] Velocidad: [1x ▼]
```

**Características**:
- Animación mes a mes o año a año
- Control de velocidad de reproducción
- Pausar en fechas específicas
- Exportar como GIF o video

**Implementación con Plotly**:
```python
fig = px.bar(
    df_ranking,
    x='valor',
    y='banco',
    orientation='h',
    animation_frame='fecha',
    range_x=[0, df_ranking['valor'].max() * 1.1]
)
```

---

## Sección 8: Forecasting Simple

### Proyección a Corto Plazo
**Tipo**: Línea histórica + banda de proyección

```
┌──────────────────────────────────────────────┐
│ PROYECCIÓN: Próximos 12 meses                │
│                                               │
│    │                          ········        │
│    │                      ····    ····        │
│    │                  ····            ····    │
│    │              ────                    ···· │
│    │          ────                             │
│    │      ────                                 │
│    │  ────                                     │
│    └──────────────────────────────────────────│
│    2023      2024      2025      2026         │
│                        ▲                       │
│                      Hoy                       │
│                                               │
│    ──── Histórico   ···· Proyección ±10%     │
└──────────────────────────────────────────────┘
```

**Métodos**:
- Media móvil simple
- Tendencia lineal
- Crecimiento promedio histórico

**Advertencia**: Incluir disclaimer sobre limitaciones del modelo

---

## Sección 9: Comparación Multi-Período

### Small Multiples (Facet Grid)
```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 2015-2017    │ │ 2018-2020    │ │ 2021-2023    │
│   ~~~        │ │   ~~~        │ │   ~~~        │
│  ~   ~       │ │  ~   ~       │ │  ~   ~       │
│ ~     ~      │ │ ~     ~      │ │ ~     ~      │
└──────────────┘ └──────────────┘ └──────────────┘

┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Banco A      │ │ Banco B      │ │ Banco C      │
│   ~~~        │ │   ~~~        │ │   ~~~        │
│  ~   ~       │ │  ~   ~       │ │  ~   ~       │
│ ~     ~      │ │ ~     ~      │ │ ~     ~      │
└──────────────┘ └──────────────┘ └──────────────┘
```

**Tipos de Facets**:
- Por período temporal
- Por banco
- Por cuenta contable
- Por indicador

---

## Sección 10: Métricas de Volatilidad

### Panel de Estadísticas Temporales
```
┌──────────────────────────────────────────────┐
│ ANÁLISIS DE VOLATILIDAD                      │
├──────────────────────────────────────────────┤
│                                               │
│ Desviación Estándar (12m):    $1,234M        │
│ Coeficiente de Variación:     8.5%           │
│ Rango Intercuartil:           $890M          │
│ Máximo Drawdown:              -15.3%         │
│                                               │
│ ┌──────────────────────────────────────────┐ │
│ │ DISTRIBUCIÓN DE VARIACIONES MENSUALES    │ │
│ │      ██                                   │ │
│ │    ████                                   │ │
│ │  ████████                                 │ │
│ │████████████                               │ │
│ └──────────────────────────────────────────┘ │
│  -10%  -5%   0%   5%  10%  15%              │
└──────────────────────────────────────────────┘
```

---

## Resumen de Visualizaciones

| # | Visualización | Tipo Gráfico | Objetivo | Estado |
|---|---------------|--------------|----------|--------|
| 1 | Evolución Comparativa | Líneas múltiples | Comparar bancos en el tiempo | ✅ Implementado |
| 2 | Descomposición Temporal | 3 líneas apiladas | Identificar tendencia y estacionalidad | ⏳ Pendiente |
| 3 | Heatmap Temporal | Mapa de calor | Detectar patrones mensuales/anuales | ✅ Implementado |
| 4 | Correlación Variables | Scatter + regresión | Analizar relaciones entre métricas | ✅ Implementado |
| 5 | Velocidad de Cambio | Barras + línea | Medir aceleración del crecimiento | ✅ Implementado |
| 6 | Ranking Dinámico | Barras animadas | Ver evolución de posiciones | ✅ Implementado |
| 7 | Forecasting | Línea + banda | Proyectar tendencias futuras | ⏳ Pendiente |
| 8 | Small Multiples | Grilla de gráficos | Comparar múltiples períodos/bancos | ⏳ Pendiente |
| 9 | Volatilidad | Histograma + métricas | Evaluar estabilidad temporal | ⏳ Pendiente |

---

## Ventajas del Módulo

1. **Profundidad Temporal**: Aprovecha los 23 años de historia
2. **Comparaciones Robustas**: Múltiples bancos y variables simultáneamente
3. **Detección de Patrones**: Estacionalidad, tendencias, anomalías
4. **Flexibilidad**: Múltiples granularidades (mensual, trimestral, anual)
5. **Interactividad**: Zoom, selección, hover, animaciones

---

## Librerías Adicionales Requeridas

```python
# Para descomposición de series
from statsmodels.tsa.seasonal import seasonal_decompose

# Para correlaciones
from scipy.stats import pearsonr

# Ya incluidas
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
```

---

## Visualizaciones Implementadas (v1.0)

### 1. Evolución Comparativa
- Hasta 10 bancos simultáneos
- 3 modos: Valores Absolutos, Indexado (Base 100), Participación %
- Opción de incluir Total Sistema
- Tooltip unificado por fecha

### 2. Heatmap de Crecimiento Mensual
- Matriz Año × Mes con colores RdYlGn
- Muestra crecimiento % mes a mes
- Selección de banco individual o sistema

### 3. Correlación entre Variables
- Scatter plot con color por año
- Línea de tendencia con regresión lineal
- Métricas: R, R², interpretación

### 4. Velocidad de Crecimiento
- Barras de crecimiento trimestral o anual
- Línea de promedio histórico
- Estadísticas: promedio, máximo, mínimo, volatilidad

### 5. Ranking Dinámico (Race Chart)
- Animación de Top 10 bancos por año
- Control de reproducción (Play/Pause)
- Colores por banco

---

## Próximos Pasos

Visualizaciones pendientes para futuras versiones:
- Descomposición Temporal (tendencia + estacionalidad)
- Forecasting (proyecciones simples)
- Small Multiples (grilla comparativa)
- Métricas de Volatilidad

---

**Autor**: Dashboard Radar Bancario Ecuador
**Fecha**: 25 de enero de 2026
**Versión**: 1.0
**Estado**: ✅ Implementado (5 de 9 visualizaciones)
