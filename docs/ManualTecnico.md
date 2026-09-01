# Manual Técnico — Sistema Financiero Privado

## Datasets

| Archivo | Columnas | Contenido |
|---|---|---|
| `master_data/balance.parquet` | `banco, fecha, codigo, cuenta, valor, nivel` | Saldos contables mensuales (Catálogo Único de Cuentas), en miles de USD |
| `master_data/pyg.parquet` | `banco, fecha, codigo, cuenta, valor_acumulado, valor_mes, valor_12m` | Estado de resultados: acumulado del año, desacumulado mensual, y suma móvil 12 meses |
| `master_data/camel.parquet` | `banco, fecha, codigo, indicador, valor, categoria` | ~50 ratios CAMEL, `valor` como fracción (0-1); las páginas multiplican por 100 para mostrar `%` |

Ninguno de los 3 tiene columna `hoja` — cada parquet ya corresponde a una
única hoja del Excel fuente (ver `docs/AUDITORIA_COMPLETA.md` sección 5 para
el bug histórico que asumía lo contrario).

## Metodologías propias (no regulatorias — documentadas explícitamente)

### Semáforo de severidad (`analytics/camel_scoring.py::clasificar_semaforo`)

Usa los umbrales `alerta`/`critico` ya definidos en
`config/indicator_mapping.py::RANGOS_INDICADORES` (preexistentes al
refactor, nunca antes conectados a la UI):

| Indicador | Alerta | Crítico | Dirección |
|---|---|---|---|
| Morosidad (`MOR_TOT`) | ≥ 5% | ≥ 10% | mayor es peor |
| Cobertura (`COB_TOT`) | ≤ 100% | ≤ 80% | menor es peor |
| ROE | ≤ 5% | ≤ 0% | menor es peor |
| ROA | ≤ 0.5% | ≤ 0% | menor es peor |
| Solvencia (`SOL`) | ≤ 12% | ≤ 9% | menor es peor (9% = mínimo regulatorio de referencia) |
| Liquidez (`LIQ`) | ≤ 20% | ≤ 15% | menor es peor |

### Score CAMEL 0-100 (`analytics/camel_scoring.py::calcular_score_camel`)

Para el radar comparativo (`pages/comparativos.py`, pestaña "Radar CAMEL" de
`pages/indicadores_camel.py`). Normaliza un indicador representativo por
dimensión a una escala 0-100, usando los mismos rangos de referencia visual
que ya usaba `pages/4_CAMEL.py` para colorear sus heatmaps (no son cifras
regulatorias):

| Dimensión | Indicador | Rango de referencia | Dirección |
|---|---|---|---|
| C (Capital) | SOL | [0, 20]% | mayor es mejor |
| A (Activos) | MOR_TOT | [0, 10]% | menor es mejor |
| M (Management) | GO_MNF | [0, 200]% | menor es mejor |
| E (Earnings) | ROE | [-20, 30]% | mayor es mejor |
| L (Liquidez) | LIQ | [0, 50]% | mayor es mejor |

`score = clip((valor - min)/(max - min) * 100, 0, 100)`, invertido si
"menor es mejor".

### HHI / CR5 / CR10 (`analytics/concentracion.py`)

- **HHI**: suma de las participaciones de mercado (%) al cuadrado, sobre
  todos los bancos con dato en la fecha. Fórmula idéntica a la que ya estaba
  definida (pero nunca visualizada) en `pages/1_Panorama.py`.
- **CR5 / CR10**: suma de la participación de mercado de los 5/10 bancos más
  grandes.
- Clasificación de referencia: HHI < 1,500 no concentrado; 1,500–2,500
  moderadamente concentrado; > 2,500 altamente concentrado (convención
  estándar de análisis de competencia, no específica de este sistema).

### Alertas Tempranas (`analytics/early_warning.py`)

Motor de reglas — **no es un modelo predictivo ni de machine learning**.
Aplica `clasificar_semaforo()` a los 6 indicadores monitoreados (SOL,
MOR_TOT, COB_TOT, ROE, ROA, LIQ) en la fecha más reciente disponible *por
indicador* (o una fecha específica si el usuario la elige), y lista todos los
casos en ALERTA o CRÍTICO.

## Metodologías propias — Fase 2

### Índice Sistémico (`analytics/systemic_index.py`)

Metodología interna, no regulatoria (no hay datos de exposición
interbancaria por contraparte para un índice tipo BIS/Basilea — ver sección
siguiente):

```
tamaño_banco_i  = participación de mercado en activos totales (%)
estrés_banco_i  = promedio de (100 - salud_morosidad) y (100 - salud_solvencia),
                  usando la misma normalización 0-100 de analytics.camel_scoring
                  (rangos de referencia: morosidad [0,10]%, solvencia [0,20]%)
contribución_i  = tamaño_banco_i × estrés_banco_i / 100
índice_sistema  = Σ contribución_i sobre todos los bancos con dato
```

Es un índice **relativo** (sirve para comparar bancos entre sí y el sistema
en el tiempo), no está acotado a un máximo regulatorio internacional.

### Stress Testing (`analytics/stress_testing.py`)

Sensibilidad de balance/resultados, no un stress test regulatorio ni un VaR
de mercado. Se aplican shocks (puntos porcentuales, editables en la UI) a
los valores reales más recientes de Morosidad, Solvencia y ROA por banco, y
se reclasifica con `clasificar_semaforo` (mismos umbrales que el resto de
la plataforma). Escenarios preconfigurados (calibrados sobre la
distribución real de indicadores a 2025-11, para que efectivamente muevan
bancos entre severidades):

| Escenario | Morosidad | Solvencia | ROA |
|---|---|---|---|
| Adverso | +2.0 pp | −1.0 pp | −0.5 pp |
| Severo | +5.0 pp | −2.5 pp | −1.5 pp |
| Crisis Sistémica | +8.0 pp | −4.0 pp | −3.0 pp |

**Limitación explícita**: no se estima impacto en dólares del Seguro de
Depósitos — requeriría la distribución de depositantes por banco (montos y
número de cuentas bajo el límite de cobertura), dato que no existe en
`master_data/` ni en el pipeline de `scripts/`.

### Forecasting, Anomalías y Clustering (`models/`)

Ver `models/README.md` para el detalle método por método. Resumen: Holt
(tendencia aditiva) para proyección, Isolation Forest para anomalías,
K-Means + PCA para clustering — los tres sobre series/indicadores reales de
`camel.parquet`, sin variable objetivo ni datos sintéticos. Requieren
`statsmodels>=0.14` y `scikit-learn>=1.9` (agregados a `requirements.txt`).

### Asistente Inteligente de Riesgos (`services/assistant_engine.py`)

Motor determinístico, sin LLM. Reconoce banco + indicador + intención por
palabras clave (ver `SINONIMOS_INDICADOR`, `PALABRAS_MEJOR/PEOR/PROMEDIO/
EVOLUCION/COMPARAR` en el módulo) y delega el cálculo a
`analytics/camel_explorer.py` y `analytics/camel_scoring.py` — toda
respuesta cita un número real y la fecha de corte usada; si no reconoce la
pregunta, lo dice explícitamente en vez de adivinar. `ProveedorLLM` es un
stub documentado (no implementado) para conectar un modelo real más
adelante sin rediseñar la interfaz (`ProveedorAsistente.responder`).

## Metodologías propias — Fase 3

### Backtesting de Forecasting (`models/forecasting.py::backtest_serie`)

Mide qué tan bien el mismo modelo de Holt (usado en `proyectar_serie`)
habría predicho los últimos 6 meses ya conocidos: entrena solo sobre el
resto de la serie, proyecta esos 6 meses, y compara contra el valor real.
Reporta MAE y RMSE siempre; MAPE solo si ningún valor real del período de
prueba está cerca de cero (evita una división por ~0 que dispara el error
a un número sin sentido). No garantiza nada sobre el futuro — mide
desempeño histórico del método sobre esa serie específica. Integrado en
**Modelos Predictivos → Forecasting**, debajo de cada proyección.

### Alertas Predictivas (`analytics/predictive_alerts.py`)

Aplica el mismo modelo de forecasting (ya validado arriba) a los 6
indicadores prudenciales monitoreados (`analytics.camel_scoring.CODIGO_A_TIPO_RANGO`),
proyecta N meses adelante, y clasifica el valor proyectado con
`clasificar_semaforo` (mismos umbrales de siempre). Solo se reporta cuando
la severidad proyectada es **peor** que la actual — no es una lista de
"todo lo que se proyectó", es específicamente una señal de alerta temprana.

Dos niveles de cálculo por costo computacional (medido empíricamente):
- **Resumen del sistema** (6 proyecciones, promedio entre bancos): ~0.5s,
  se calcula siempre al cargar la página.
- **Detalle por banco** (24 bancos × 6 indicadores = 144 proyecciones):
  ~15-20s la primera vez (se verificó con timing directo antes de
  implementar). Solo se calcula si el usuario presiona el botón explícito
  "Calcular detalle por banco" — nunca en la carga automática de la
  página, siguiendo la misma lección del bug de rendimiento del Índice
  Sistémico corregido en el pulido anterior.

### Calificación de Riesgo Consolidada (`analytics/risk_rating.py`)

Rating A–E por banco, compuesto de **2 factores, no 3**:

```
score_final = 0.7 × score_camel + 0.3 × score_resiliencia
```

- `score_camel` (70%): promedio de las 5 dimensiones de
  `analytics.camel_scoring.calcular_score_camel` — salud actual del banco.
- `score_resiliencia` (30%): severidad del banco bajo el escenario
  **Adverso** de `analytics.stress_testing` (OK=100, ALERTA=50, CRITICO=0).

**Por qué "Adverso" y no "Severo" o "Crisis Sistémica"**: se verificó
empíricamente la distribución de severidad de cada escenario sobre los
datos reales antes de decidir —

| Escenario | OK | ALERTA | CRITICO |
|---|---|---|---|
| Adverso | 3 | 11 | 10 |
| Severo | 0 | 3 | 21 |
| Crisis Sistémica | 0 | 0 | 24 |

"Severo" y "Crisis Sistémica" saturan (casi todos los bancos caen en
CRITICO), lo que los vuelve inútiles como *discriminador* para comparar
resiliencia relativa entre bancos — todos terminarían con el mismo puntaje.
"Adverso" reparte los bancos entre las 3 severidades y sí aporta
información real para diferenciar.

**Por qué NO se incluye la contribución al Índice Sistémico** (a pesar de
que la propuesta original de Fase 3 la mencionaba): esa métrica
(`analytics/systemic_index.py`) responde "¿qué tanto le importaría al
sistema si este banco cae?", que depende directamente del **tamaño** del
banco — no de su salud. Sumarla a la calificación individual penalizaría a
bancos grandes por ser grandes, no por estar en peor estado. El Índice
Sistémico se mantiene como página separada porque mide algo distinto y
igual de válido, solo que no debe mezclarse con "qué tan sano está este
banco en particular".

Bandas: A ≥80 · B ≥60 · C ≥40 · D ≥20 · E <20 (sobre 0-100). Bancos sin
dato suficiente para calcular resiliencia se excluyen del rating (no se
les asigna un valor supuesto).

## Lo que NO se implementó y por qué (Fase 1)

Ver la matriz de factibilidad completa en `docs/AUDITORIA_COMPLETA.md`
sección 6. Resumen:

- **LCR, NSFR, brecha de vencimientos**: `balance.parquet` no tiene
  dimensión de plazo/madurez.
- **VaR, CVaR, riesgo cambiario**: no hay tasas de mercado, precios de
  instrumentos ni serie cambiaria en el pipeline.
- **Vintage, roll-rate, curvas de transición, recovery**: no hay datos de
  cohortes de originación de crédito.
- **Concentración por depositante**: no hay datos a nivel de depositante
  individual.
- **Red de interconexión / contagio interbancario**: solo existe el saldo
  agregado de operaciones interbancarias (códigos `12`/`22`), no una matriz
  de contrapartes.
- **Riesgo Operacional, Riesgo de Tasa de Interés, Mapas Interactivos,
  Modelos Predictivos/ML, Asistente de IA**: sin fuente de datos o sin
  definición de alcance — ver `models/README.md` para el detalle de qué es
  viable con los datos actuales y qué requiere una fuente nueva.

Estas pestañas, cuando existen, muestran un aviso institucional
(`ui.layout.render_modulo_en_preparacion`) en vez de un valor calculado.

## Convenciones de código

- Toda carga de datos pasa por `services/data_service.py` (con
  `@st.cache_data(ttl=3600)`).
- Toda página empieza con `ui.layout.render_page(titulo, icono)` — hace
  `st.set_page_config`, inyecta el tema y renderiza header/sidebar.
- Los selectores repetidos en más de una página (jerarquía de cuentas, modo
  Absoluto/Indexado/Participación) viven en `components/`, no se copian.
- Los colores usan siempre `config/theme_tokens.py` o
  `config/indicator_mapping.py::obtener_color_banco()` — no se hardcodean
  hex sueltos en las páginas.

## Verificación de este refactor

Se usó `streamlit.testing.v1.AppTest` (ejecución headless server-side) para
correr las 17 páginas + `app.py` sin lanzar navegador: 0 excepciones. Además
se comparó numéricamente, para las páginas migradas desde el dashboard
original, la salida (valores exactos de KPIs y de las trazas de los gráficos
Plotly) contra las páginas originales — coinciden exactamente donde no se
declaró un cambio deliberado (ver el bug de PyG Top-5 documentado en la
auditoría, preservado a propósito).
