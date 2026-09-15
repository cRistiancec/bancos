Nota: Este changelog incluye entradas historicas de modulos y archivos que ya no existen en el repo actual.

# Changelog - Sistema Financiero Privado

Registro de cambios y mejoras de la plataforma.

## [Sin publicar]

### Rebranding a DATA METRICS y preparación para Codespaces/Streamlit Cloud

- **Logo institucional reemplazado**: `assets/logo_cosede.png` se elimina y
  se incorpora `assets/logo-datametrics.png` (provisto por DATA METRICS —
  Business Intelligence and Analytics), referenciado desde `ui/header.py` y
  agregado también vía `st.logo()` en `ui/layout.py`.
- **Atribución institucional actualizada**: todas las menciones a "COSEDE" /
  "Coordinación Técnica de Riesgos y Estudios" en la interfaz en vivo
  (header, `pages/configuracion.py`, pie de página de reportes PDF en
  `utils/pdf_export.py`) y en la documentación (`README.md`, `QUICKSTART.md`,
  `docs/`) se reemplazan por "DATA METRICS — Business Intelligence and
  Analytics". No se modificó ningún cálculo, indicador ni lógica de negocio.
- **Validado para GitHub Codespaces** (`.devcontainer/devcontainer.json`,
  Python 3.11) y **Streamlit Community Cloud** (entry point `app.py`, sin
  rutas absolutas ni secretos hardcodeados).

### Integración con la línea de automatización de datos (upstream)

Reconciliación entre dos líneas de desarrollo divergentes construidas sobre
el mismo commit inicial: el refactor institucional "Sistema Financiero
Privado" (Fases 1-3, ver `[7.0.0]` y anteriores) y la línea de datos/
automatización desarrollada en paralelo en el repositorio original
(`jp1309/bancos`, rama `main`).

- **Automatización mensual adoptada del repositorio original**: workflow
  `.github/workflows/actualizar-datos.yml` (reintentos días 6-20),
  orquestador transaccional `scripts/actualizar_datos.py` (descarga,
  valida, respalda, procesa, publica o revierte), puerta de calidad
  `scripts/validar_actualizacion.py`, y `master_data/metadata.json` +
  `update_status.json` como bitácora de cada publicación. Ver
  `docs/AUTOMATIZACION.md`.
- **`.gitignore` corregido**: la versión heredada del refactor institucional
  tenía reglas `*.txt` y `*.json` sin acotar, lo que impedía que
  `requirements.txt` y `requirements-dev.txt` quedaran versionados (nunca
  se detectó porque `git status` simplemente no los mostraba). Se adopta el
  `.gitignore` de la línea de automatización, que acota estas reglas
  correctamente (`/*.json` con excepción explícita para
  `master_data/*.json`) y se añade una excepción equivalente para
  `assets/*.png` (el logo institucional tampoco se había commiteado nunca
  por la regla `*.png` heredada de la limpieza de capturas de depuración).
- **`requirements.txt` fusionado**: se adopta el set de versiones fijadas
  del repositorio original (`streamlit==1.53.1`, `pandas==2.3.0`,
  `numpy==2.3.1`, `pyarrow==23.0.0` — fijadas tras un incidente de
  segmentation fault en Streamlit Cloud) y se agregan las dependencias
  propias de los módulos de Fase 2/3 (`scikit-learn`, `statsmodels`,
  `reportlab`).
- **Datos actualizados**: ver sección de datos más abajo para el corte
  vigente tras esta integración.
- **Entry point**: se mantiene `app.py` (`st.navigation`, Fase 1) como
  único punto de entrada; `Inicio.py` y las 4 páginas numeradas originales
  se eliminan (superadas por la arquitectura de Fase 1).
- **Bug de "Top 5" en Pérdidas y Ganancias**: se verificó que el
  repositorio original tampoco lo corrigió en su propia línea de
  desarrollo (mismo `sort_values(ascending=True)` seguido de `head(5)`
  etiquetado "Top 5"). Se mantiene preservado y documentado tal como
  decidió la auditoría de Fase 1 (`docs/AUDITORIA_COMPLETA.md` sección
  5.1) — sigue pendiente de aprobación de negocio antes de corregir una
  cifra que los usuarios ya vieron en producción.

## [7.0.0] - 2026-07-27

### Fase 3 — Forecasting Riguroso, Alertas Predictivas y Calificación de Riesgo

3 capacidades nuevas, todas construidas sobre analítica ya existente (sin
datos nuevos, sin fabricar cifras):

- **Backtesting de Forecasting** (`models/forecasting.py::backtest_serie`):
  reporta MAE/RMSE/MAPE reales comparando la proyección contra los últimos
  6 meses ya conocidos, en vez de solo mostrar una banda de incertidumbre
  aproximada. Integrado en **Modelos Predictivos → Forecasting**.
- **Alertas Predictivas** (`analytics/predictive_alerts.py`,
  `pages/alertas_predictivas.py`): proyecta los indicadores del sistema (y,
  bajo demanda, de cada banco) hacia adelante y avisa cuáles cruzarían el
  umbral de alerta/crítico antes de que ocurra. El detalle por banco (144
  combinaciones, ~15-20s) se calcula solo bajo demanda vía botón — nunca en
  la carga automática de la página.
- **Calificación de Riesgo Consolidada** (`analytics/risk_rating.py`,
  `pages/calificacion_riesgo.py`): rating A-E por banco (70% score CAMEL +
  30% resiliencia bajo el escenario "Adverso" de stress testing).
  Deliberadamente NO incluye la contribución al Índice Sistémico — se
  documenta por qué en `docs/ManualTecnico.md` (mezclar tamaño del banco
  con su salud individual sería engañoso).
- Se verificó empíricamente, antes de implementar, qué escenario de stress
  testing sirve como discriminador de resiliencia: "Severo" y "Crisis
  Sistémica" saturan (21/24 y 24/24 bancos en CRÍTICO respectivamente) y no
  diferencian bancos entre sí; "Adverso" sí (3 OK / 11 ALERTA / 10 CRÍTICO).
- 9 tests nuevos en `tests/test_phase3.py` (37 tests totales en el
  proyecto).

## [6.1.0] - 2026-07-27

### Pulido y deuda técnica

Pase de optimización sobre lo construido en Fase 1 y 2 (sin datos ni
módulos nuevos). Verificado con `pytest` (28 tests nuevos en `tests/`) y
`streamlit.testing.v1.AppTest` sobre las 21 páginas + `app.py`.

- **Bug de nombres de banco corregido**: `config/indicator_mapping.py`
  tenía 3 nombres de banco desalineados con los datos reales
  (`Atlantida`→`Atlantida (antes DMiro)`, `Comercial Manabi`→`Comercial
  Manabí`, `Ruminahui`→`Rumiñahui`). Esto hacía que esos 3 bancos
  recibieran el color gris de respaldo en todas las visualizaciones, y que
  la página Calidad de Datos los reportara falsamente como "sin datos". Se
  confirmó que **los 24 bancos de `BANCOS_SISTEMA` tienen datos completos**
  (incluido Amazonas, contra lo que decía la documentación heredada del
  proyecto original). Ver `docs/AUDITORIA_COMPLETA.md` sección 7.3.
- **Bug de rendimiento corregido**: la evolución de 36 meses del Índice
  Sistémico (Fase 2) tardaba ~94s por re-filtrar `camel.parquet`/
  `balance.parquet` completos en cada iteración; ahora usa pivotes
  pre-calculados una sola vez — 1.6s, mismo resultado numérico verificado.
- **Deprecaciones de Streamlit**: reemplazado `use_container_width=True`
  por `width='stretch'` en 18 archivos (42 ocurrencias) antes de que
  Streamlit elimine el parámetro.
- **`FutureWarning` de pandas resueltos**: se agregó `observed=True` a los
  `groupby`/`pivot_table` sobre la columna categórica `banco`, eliminando
  filas fantasma (con `NaN`) que aparecían en algunos rankings de Balance
  General para períodos donde no todos los bancos habían reportado.
- **Caché agregada** a `utils/data_quality.py` (`@st.cache_data` en 7
  funciones que no la tenían — hallazgo pendiente desde la auditoría de
  Fase 1).
- **Exportación a PDF** (`utils/pdf_export.py`, `reportlab`): reporte
  ejecutivo institucional (KPIs + alertas) y exportación de cualquier tabla
  filtrada, ambos agregados a `pages/reportes.py`.
- **Suite de pruebas automatizadas** (`tests/`, `pytest`): 28 tests sobre
  `analytics/`, `models/` y `services/`, corriendo contra los datos reales
  de `master_data/` (sin mocks).
- **Preparación para despliegue**: `Dockerfile`, `.dockerignore`,
  `.streamlit/secrets.toml.example`, `docs/DESPLIEGUE.md`,
  `requirements-dev.txt`.

## [6.0.0] - 2026-07-27

### Fase 2 — Analítica Avanzada

Se agregan 4 páginas nuevas, siguiendo el mismo principio de la Fase 1
(cero cifras inventadas): donde no hay datos reales, no se implementa.
Ver `docs/AUDITORIA_COMPLETA.md` sección 6/7 y `docs/ManualTecnico.md`
para el detalle metodológico completo de cada uno.

- **Logo institucional**: se incorpora `assets/logo_cosede.png` (provisto
  por el usuario); el header ya no usa el wordmark de texto de respaldo.
- **Riesgo Sistémico** (`pages/riesgo_sistemico.py`): índice de contribución
  sistémica propio (tamaño de mercado × estrés en morosidad/solvencia).
  Reactiva y extiende `analytics/concentracion.py` de Fase 1. La red de
  interconexión/contagio interbancario sigue fuera de alcance (sin datos de
  contraparte).
- **Stress Testing** (`pages/stress_testing.py`): escenarios hipotéticos
  configurables (Adverso/Severo/Crisis Sistémica, con sliders editables)
  aplicados a Morosidad/Solvencia/ROA reales, reclasificados con el mismo
  semáforo de umbral de toda la plataforma. No es un VaR de mercado ni
  estima impacto en dólares del Seguro de Depósitos.
- **Modelos Predictivos** (`pages/modelos_predictivos.py`): forecasting
  (Holt, `statsmodels`), detección de anomalías (Isolation Forest,
  `scikit-learn`) y clustering de bancos (K-Means + PCA) sobre series
  reales de indicadores CAMEL. Primer código funcional en `models/`
  (antes solo un README de preparación de arquitectura).
- **Asistente Inteligente de Riesgos** (`pages/asistente_riesgos.py`):
  motor determinístico (`services/assistant_engine.py`) que responde
  preguntas sobre banco/indicador/intención con cálculos reales — sin LLM
  conectado. Interfaz `ProveedorAsistente` pluggable, con `ProveedorLLM`
  como stub documentado para una integración futura.
- **Dependencias**: se agregan `scikit-learn>=1.9` y `statsmodels>=0.14` a
  `requirements.txt` (ya estaban disponibles en el entorno de desarrollo).

## [5.0.0] - 2026-07-27

### Refactorización institucional (Fase 1)

Transformación integral de "Radar Bancario Ecuador" en **Sistema Financiero
Privado** — plataforma institucional de DATA METRICS. Ver
`docs/AUDITORIA_COMPLETA.md` para el detalle completo del análisis previo y
`docs/ARQUITECTURA.md` / `docs/ManualTecnico.md` para la arquitectura
resultante. No se alteró ningún cálculo ni resultado existente (con una
excepción documentada y deliberadamente preservada: el bug de "Concentración
Top 5" en Pérdidas y Ganancias, ver auditoría sección 5.1).

**Rebranding**: nuevo nombre, subtítulo institucional y autoría (Eco.
Cristian Coronel Quezada, MBA — DATA METRICS, Business Intelligence and
Analytics).

**Arquitectura**: nuevo entry point único `app.py` (`st.navigation`),
reemplaza `Inicio.py` + `pages/N_*.py` numerados. Nuevas capas `ui/`,
`components/`, `charts/`, `analytics/`, `services/` — ver `docs/ARQUITECTURA.md`.
Tema oscuro institucional (`.streamlit/config.toml` + `styles/institutional.css`).

**Deduplicación**: el selector jerárquico de cuentas (triplicado en Balance
General) y el patrón Absoluto/Indexado/Participación (duplicado entre
páginas) ahora son componentes compartidos (`components/account_selector.py`,
`components/mode_selector.py`).

**Código reactivado** (antes definido pero nunca conectado a la UI):
`calcular_concentracion_hhi` (ahora en `analytics/concentracion.py`, con
CR5/CR10 añadidos), `crear_radar_camel`, `crear_gauge`, `crear_heatmap`,
`crear_linea_temporal`, `crear_scatter_posicionamiento`,
`crear_barras_apiladas_100` (todas en `charts/builders.py`), y el módulo de
Calidad de Datos (antes archivado, ahora en `pages/calidad_datos.py`, con el
bug de la columna `hoja` inexistente corregido).

### Pestañas nuevas (100% datos reales)
Resumen Ejecutivo, Monitoreo Prudencial, Riesgo de Crédito, Riesgo de
Liquidez, Riesgo de Solvencia, Riesgo de Concentración, Ranking de Bancos,
Comparativos entre Bancos, Evolución Histórica, Alertas Tempranas, Reportes,
Configuración.

### Explícitamente fuera de alcance de esta fase
LCR/NSFR, VaR/CVaR, red de interconexión interbancaria, vintage/roll-rate de
cartera, Riesgo Operacional, Riesgo de Tasas, Stress Testing, Modelos
Predictivos/ML, Asistente de IA, Mapas Interactivos — sin fuente de datos
real en el pipeline actual. Ver matriz de factibilidad en
`docs/AUDITORIA_COMPLETA.md` sección 6 y `models/README.md`.

### Verificación
17 páginas + `app.py` ejecutadas sin excepciones con
`streamlit.testing.v1.AppTest`; valores numéricos y trazas de gráficos
comparados contra las páginas originales (coinciden exactamente).

## [4.3.0] - 2026-07-18

### Datos y automatización (repositorio original, `jp1309/bancos`)

- Publicado y validado el corte de junio de 2026 para Balance, PyG y CAMEL.
- La descarga valida 23 ZIP/XLSX, las tres hojas requeridas y la fecha interna uniforme.
- El pipeline trata la fuente sin avance como no-op mediante código de salida `2`.
- Los tres procesadores usan escritura atómica y el orquestador restaura los artefactos anteriores ante fallos.
- Nueva puerta de publicación para esquema, fecha, continuidad mensual, cobertura, duplicados, metadata e historia.
- Workflow con permisos explícitos de escritura y reintentos del 6 al 20 de cada mes.
- Portada alimentada por `metadata.json`, sin cifras mensuales escritas a mano.
- Cobertura visible y validada de 23 bancos hasta junio de 2026.
- Reducción de memoria mediante categorías y `groupby(observed=True)`.

## [4.2.0] - 2026-01-28

### Rediseño de Interfaz
- **Nuevo nombre**: Sistema de Inteligencia Financiera - Banca Ecuador
- **Página principal rediseñada** (`app.py` → `Inicio.py`):
  - KPIs principales visibles en la portada (bancos, años, meses, última actualización)
  - Introducción más amigable para usuarios finales
  - Botones de acceso rápido a módulos principales
  - Footer mejorado con información técnica (emoji 🧠 en lugar de ❤️)
  - Eliminada referencia al módulo de Calidad de Datos
  - Renombrado archivo principal a `Inicio.py` para mejor identificación en sidebar

- **Módulo Calidad de Datos archivado**: Movido a `archived_pages/` para uso técnico interno

### Agregado
- **Módulo Panorama - Nueva sección de Pasivos**:
  - Treemap jerárquico de Pasivos y Patrimonio con drill-down por banco
  - Ranking de bancos por Pasivos Totales (código '2')
  - Composición detallada: Obligaciones con el Público, Obligaciones Financieras, Valores en Circulación, Otros Pasivos, Patrimonio
  - Misma estructura visual que sección de Activos para consistencia

### Removido
- **Módulo Panorama**:
  - Eliminados gráficos de pastel de "Composición del Sistema"
  - Removida visualización de Estructura de Activos (pie chart)
  - Removida visualización de Estructura de Pasivos y Patrimonio (pie chart)
  - Los treemaps proporcionan información más detallada y navegable

### Optimizado
- **Reducción del tamaño de datos**: De 37.3 MB a 29.1 MB (ahorro del 22%)
  - Eliminados archivos parquet innecesarios: `indicadores.parquet`, `cartera.parquet`, `fuentes_usos.parquet`
  - Solo se mantienen las 3 hojas esenciales: BAL, PYG, CAMEL

- **Simplificación de scripts**:
  - Eliminado `crear_master.py` (procesaba 8 hojas)
  - Solo 3 scripts de procesamiento necesarios:
    - `procesar_balance.py` → balance.parquet (18 MB)
    - `procesar_pyg.py` → pyg.parquet (9.5 MB)
    - `procesar_camel.py` → camel.parquet (1.6 MB)

- **Código más limpio**:
  - Eliminadas funciones no utilizadas en `data_loader.py`
  - Simplificada página `0_Calidad.py` para cargar solo datos esenciales
  - Actualizada toda la documentación

### Mejorado
- **Heatmap CAMEL mensual**: Ahora muestra todos los meses con selector de rango de fechas
- **Ordenamiento por tamaño**: Bancos ordenados por activos totales (Pichincha en la parte superior)
- **Formato de indicadores**: Todos los indicadores con 1 decimal
- **Sistema de colores consistentes**:
  - Cada banco tiene un color único asignado permanentemente
  - Los colores se mantienen consistentes en todas las visualizaciones de todos los módulos
  - Paleta de 24 colores distinguibles basada en mejores prácticas de accesibilidad
  - Implementado en: rankings, gráficos de línea, treemaps, y todas las visualizaciones

### Técnico
- Los archivos Excel contienen muchas hojas, pero el dashboard solo usa 3: BAL, PYG, CAMEL
- Las hojas INDICAD, INDIC CARTERA, ESTRUC CART, FUENTES USOS, REFINA REES no se utilizan
- Procesamiento más rápido al leer solo las hojas necesarias
- Dashboard enfocado en 4 módulos principales para usuarios finales

---

## [4.1.0] - 2026-01-26

### Agregado
- **Nuevo Módulo: Indicadores CAMEL** (`pages/4_CAMEL.py`)
  - 5 visualizaciones implementadas:
    1. **KPIs del Sistema**: Solvencia, Morosidad, Cobertura, ROE, Liquidez
    2. **Análisis por Indicador**: Ranking de bancos por categoría CAMEL
    3. **Composición de Cartera**: Treemap por banco y pie chart del sistema
    4. **Evolución Temporal**: Comparación multi-banco de indicadores
    5. **Heatmap Anual**: Evolución histórica de indicadores por banco

- **Procesamiento de Hoja CAMEL** (`procesar_camel.py`)
  - Extracción de 39 indicadores financieros
  - Categorización por dimensiones CAMEL:
    - C: Capital (Solvencia)
    - A: Activos (Morosidad, Cobertura, Composición)
    - M: Management (Eficiencia operativa)
    - E: Earnings (ROA, ROE)
    - L: Liquidity (Índice de liquidez)
  - Composición de cartera por tipo de crédito (8 categorías)

### Datos Generados
- **`master_data/camel.parquet`**
  - 233,680 registros
  - 24 bancos
  - 276 fechas (enero 2003 - diciembre 2025)
  - 39 indicadores únicos
  - 6 categorías CAMEL

---

## [4.0.0] - 2026-01-26

### Reestructuración del Dashboard
- **Simplificación de módulos**: Reducción de 8 a 4 módulos principales
- **Estructura final**:
  - **Módulo 0**: Calidad de Datos
  - **Módulo 1**: Panorama del Sistema
  - **Módulo 2**: Balance General (anteriormente Series Temporales)
  - **Módulo 3**: Perdidas y Ganancias (anteriormente Rentabilidad)

### Removido
- **Módulo CAMEL**: Eliminado análisis por dimensiones CAMEL
- **Módulo Comparador**: Eliminado benchmarking entre bancos
- **Módulo Evolución**: Eliminado series temporales básicas
- **Módulo Perfil**: Eliminado fichas individuales por banco

### Mejorado
- Renombrado módulo "Series Temporales" a "Balance General" para mayor claridad
- Renombrado módulo "Rentabilidad y Resultados" a "Perdidas y Ganancias"
- Actualización de íconos y títulos en módulos

---

## [3.3.0] - 2026-01-26

### Agregado
- **Nuevo Módulo: Rentabilidad y Resultados** (`pages/7_Rentabilidad.py`)
  - 6 visualizaciones implementadas:
    1. **KPIs del Sistema**: 4 métricas principales (MNI, MOP, GAI, GDE)
    2. **Ranking de Rentabilidad**: Top bancos por ganancia del ejercicio
    3. **Crecimiento Anual**: Variación YoY de GDE y MOP por banco
    4. **Cascada de Márgenes**: Formación del resultado por banco
    5. **Evolución Temporal**: Comparación de múltiples bancos en el tiempo
    6. **Distribución**: Participación en ganancia del sistema (pie chart)
  - Usa datos de suma móvil 12 meses (valor_12m) para comparabilidad
  - Selector de fecha y banco
  - Comparación automática vs año anterior

- **Procesamiento de Hoja PYG (Pérdidas y Ganancias)** (`procesar_pyg.py`)
  - Extracción de datos acumulados de los archivos Excel
  - Lógica de desacumulación mensual (valor de cada mes individual)
  - Cálculo de suma móvil de 12 meses para comparabilidad
  - Códigos personalizados para cuentas resumen:
    - MNI: Margen Neto de Intereses
    - MBF: Margen Bruto Financiero
    - MNF: Margen Neto Financiero
    - MDI: Margen de Intermediación
    - MOP: Margen Operacional
    - GAI: Ganancia/Pérdida Antes de Impuestos
    - GDE: Ganancia/Pérdida del Ejercicio

### Datos Generados
- **`master_data/pyg.parquet`**
  - 769,792 registros
  - 24 bancos
  - 276 fechas (enero 2003 - diciembre 2025)
  - 128 cuentas únicas
  - Columnas: banco, fecha, codigo, cuenta, valor_acumulado, valor_mes, valor_12m
  - 95.6% de registros con valor_12m calculado

### Técnico
- Función `desacumular_valores()`: Convierte valores acumulados a mensuales
- Función `calcular_suma_movil_12m()`: Rolling sum de 12 meses por banco/código
- Manejo de filas resumen sin código (filas 30, 80, 97, 107, 120, 133, 140)

---

## [3.2.0] - 2026-01-25

### Agregado
- **Nuevo Módulo: Series Temporales Avanzadas** (`pages/6_Series_Temporales.py`)
  - 5 visualizaciones interactivas implementadas:
    1. **Evolución Comparativa**: Líneas múltiples para hasta 10 bancos
       - Modos: Valores Absolutos, Indexado (Base 100), Participación %
       - Opción de incluir Total Sistema
    2. **Heatmap Temporal**: Matriz Año × Mes de crecimiento mensual
       - Escala de colores RdYlGn centrada en 0
       - Selección de banco o sistema completo
    3. **Correlación entre Variables**: Scatter plot con regresión
       - Color por año (gradiente temporal)
       - Métricas: R, R², interpretación
    4. **Velocidad de Crecimiento**: Barras por período
       - Trimestral o anual
       - Estadísticas: promedio, max, min, volatilidad
    5. **Ranking Dinámico**: Race chart animado
       - Top 10 bancos por año
       - Control de reproducción

### Documentación
- Actualizado `docs/MODULO_SERIES_TEMPORALES.md` con estado de implementación
- Actualizado índice de documentación

---

## [3.1.0] - 2026-01-25

### Agregado
- **Visualización de Crecimiento Anual por Banco** en módulo Panorama
  - Barras horizontales ordenadas de mayor a menor crecimiento
  - Comparación del mes seleccionado vs mismo mes del año anterior
  - Escala de colores RdYlGn (Rojo-Amarillo-Verde)
  - Aplicado a:
    - Cartera de Créditos
    - Depósitos del Público
  - Altura dinámica según número de bancos
  - Línea de referencia en 0% para identificar crecimiento/decrecimiento

### Documentación
- Creada carpeta `docs/` para documentación técnica
- Agregado `docs/VISUALIZACION_CRECIMIENTO.md` con especificación completa
- Agregado `docs/README.md` como índice de documentación
- Actualizado README principal con nueva estructura

### Mejorado
- Ranking de bancos ahora muestra todos los bancos (antes solo top 10)
- Altura del ranking ajustada dinámicamente según cantidad de bancos

### Técnico
- Implementado merge de DataFrames para calcular variaciones anuales
- Uso de `fecha_anterior` (12 meses atrás) para comparaciones
- Ordenamiento ascendente en eje Y para barras horizontales
- Configuración de escala de colores: cmin=-10, cmax=30

---

## [3.0.0] - 2026-01-24

### Agregado
- Dashboard multipage con 6 módulos
- Procesamiento de datos de Balance General
- Sistema de carga con validación
- Visualizaciones interactivas con Plotly

### Módulos Implementados
1. **Calidad de Datos** - Validación y métricas
2. **Panorama** - Vista general del sistema
3. **CAMEL** - Análisis por dimensiones
4. **Comparador** - Benchmarking entre bancos
5. **Evolución** - Series temporales
6. **Perfil** - Fichas individuales

### Infraestructura
- Arquitectura basada en Streamlit
- Almacenamiento en formato Parquet
- Sistema de caché para optimización
- Mapeo de códigos contables

---

## [2.0.0] - 2026-01-23

### Agregado
- Script `crear_master.py` para consolidar datos
- Procesamiento de 4 hojas Excel:
  - Balance General (BAL)
  - Indicadores (INDICAD)
  - Estructura de Cartera (CARTERA)
  - Fuentes y Usos (FUENTES_USOS)

### Mejorado
- Sistema de descarga automática
- Detección de archivos duplicados
- Validación de estructura de datos

---

## [1.0.0] - 2026-01-20

### Primera Versión
- Script de descarga `descargar.py`
- Descarga automática desde Superintendencia de Bancos
- Organización por año y mes
- 276 archivos históricos (enero 2003 - diciembre 2025)

---

## Formato

Este changelog sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y el proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

### Tipos de Cambios
- `Agregado` - Nuevas funcionalidades
- `Mejorado` - Mejoras en funcionalidades existentes
- `Cambiado` - Cambios en funcionalidades existentes
- `Deprecado` - Funcionalidades que serán removidas
- `Removido` - Funcionalidades eliminadas
- `Corregido` - Corrección de bugs
- `Seguridad` - Vulnerabilidades corregidas
