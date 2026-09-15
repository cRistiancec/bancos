# Manual de Usuario — Sistema Financiero Privado

Sistema Inteligente para el Monitoreo Integral del Sistema Bancario Privado del Ecuador
DATA METRICS — Business Intelligence and Analytics

## Cómo ejecutar la plataforma

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre en `http://localhost:8501`. Usa `streamlit run app.py --server.port 8502`
para un puerto distinto.

## Navegación

El menú lateral está agrupado en 6 secciones:

1. **General** — Resumen Ejecutivo (página de inicio) y Panorama Bancario.
2. **Monitoreo Prudencial** — Tablero prudencial, Indicadores CAMEL, Alertas Tempranas.
3. **Riesgos** — Crédito, Liquidez, Solvencia, Concentración, Sistémico.
   La sección **Monitoreo Prudencial** también incluye Alertas Predictivas
   y Calificación de Riesgo (ver Fase 3 abajo).
4. **Estados Financieros** — Balance General, Pérdidas y Ganancias.
5. **Análisis Comparativo** — Ranking de Bancos, Comparativos entre Bancos, Evolución Histórica.
6. **Analítica Avanzada** — Stress Testing, Modelos Predictivos, Asistente de Riesgos.
7. **Calidad y Reportes** — Calidad de Datos, Reportes, Configuración.

El header superior siempre muestra: fecha/hora, corte de datos, última
actualización, número de bancos, registros totales, estado operativo y un
semáforo general de riesgo (basado en las Alertas Tempranas del momento).

## Módulos

### Resumen Ejecutivo
Vista de inicio: KPIs del sistema con mini-tendencias (sparklines), un
resumen ejecutivo generado automáticamente a partir de los indicadores
reales del último corte, y un vistazo a las alertas activas.

### Panorama Bancario
KPIs del sistema, mapas de mercado (treemap de activos y de pasivos+patrimonio
por banco, con drill-down), rankings y crecimiento anual por banco.

### Monitoreo Prudencial
Tablero de 6 ratios prudenciales centrales (Solvencia, Morosidad, Cobertura,
ROE, ROA, Liquidez) por banco, coloreado según los umbrales de alerta/crítico.

### Indicadores CAMEL
Evaluación C-A-M-E-L clásica (Capital, Assets, Management, Earnings,
Liquidity) en 4 pestañas: Análisis por Indicador, Evolución Temporal, Heatmap
Mensual y Radar CAMEL (comparación banco vs. promedio del sistema).
*Nota: se usa "CAMEL", no "CAMELS" — el componente de Sensibilidad al riesgo
de mercado no tiene datos que lo respalden (ver Manual Técnico).*

### Riesgo de Crédito / Liquidez / Solvencia / Concentración
Cada uno con ranking, evolución temporal y heatmap del/los indicador(es)
correspondiente(s), calculados sobre datos reales. Donde el análisis
solicitado requiere datos que no existen en el sistema (p. ej. vintage de
cartera, LCR/NSFR, concentración por depositante), la página lo indica
explícitamente en un recuadro de "módulo en preparación" — nunca se muestra
un número inventado.

### Riesgo Sistémico
Índice de "contribución sistémica" por banco (tamaño de mercado × estrés en
morosidad y solvencia) — metodología interna, no regulatoria. Ranking por
banco, evolución del índice agregado, y aviso explícito de que la red de
interconexión/contagio interbancario no está disponible (sin datos de
contraparte).

### Ranking de Bancos / Comparativos entre Bancos / Evolución Histórica
Herramientas transversales: ranking genérico sobre cualquier indicador de
los 3 datasets, comparación lado a lado (radar CAMEL + tabla) de hasta 4
bancos, y un explorador temporal unificado.

### Alertas Tempranas
Lista de bancos e indicadores que cruzan los umbrales de alerta/crítico
definidos para el sistema (ver Manual Técnico para los umbrales exactos).

### Stress Testing
Escenarios hipotéticos configurables (Adverso/Severo/Crisis Sistémica, con
sliders editables) aplicados como shocks a Morosidad/Solvencia/ROA reales de
cada banco, mostrando cuántos bancos cambiarían de severidad. **No es un
stress test regulatorio ni un VaR de mercado**, y no estima impacto en
dólares del Seguro de Depósitos (sin datos de depositantes).

### Modelos Predictivos
Tres herramientas exploratorias sobre series reales: **Forecasting**
(proyección estadística de un indicador, con banda de incertidumbre),
**Detección de Anomalías** (períodos atípicos marcados sobre la serie), y
**Clustering de Bancos** (agrupación por perfil de indicadores CAMEL). Ver
metodología en `docs/ManualTecnico.md`.

### Asistente de Riesgos
Chat que responde preguntas sobre los indicadores cargados (p. ej. "¿Cuál es
la solvencia de Pichincha?", "¿Qué banco tiene mejor ROE?") usando reglas
sobre datos reales — **no hay un LLM conectado en esta fase**. Si no
reconoce la pregunta, lo dice explícitamente; usa los botones de preguntas
sugeridas para una respuesta garantizada.

### Alertas Predictivas (Fase 3)
Proyecta los indicadores del sistema (y, bajo demanda, de cada banco) unos
meses hacia adelante y avisa cuáles cruzarían el umbral de alerta/crítico
**antes** de que ocurra — usando el mismo modelo de forecasting validado
con backtesting en Modelos Predictivos. El detalle por banco (144
combinaciones) se calcula solo al presionar el botón correspondiente, no
automáticamente, porque toma ~15-20 segundos.

### Calificación de Riesgo (Fase 3)
Rating **A–E** por banco: 70% salud actual (score CAMEL) + 30% resiliencia
ante un escenario de estrés adverso. **No es una calificación crediticia
oficial** — es una metodología interna, documentada en
`docs/ManualTecnico.md`, y deliberadamente no incluye el Índice Sistémico
(que mide algo distinto: importancia para el sistema, no salud individual).

### Calidad de Datos
Completitud, cobertura por banco/año, validación de la ecuación contable
(Activo = Pasivo + Patrimonio) y exportación de un reporte Excel de calidad.

### Reportes
Exporta cualquiera de los 3 datasets (filtrado por banco/fecha) a CSV o Excel.

### Configuración
Información de versión, estado de los datos cargados, y botón para limpiar
la caché tras actualizar los archivos Parquet.

## Modos de visualización (Balance General, Pérdidas y Ganancias, Evolución Histórica)

- **Valores Absolutos**: cifra en millones de USD.
- **Indexado (Base 100)**: la serie se reescala para que el primer período
  visible valga 100 — útil para comparar crecimiento relativo entre bancos
  de tamaños distintos.
- **Participación %**: valor del banco sobre el total del sistema, en el
  mismo período.

## Interpretación de colores

- 🟢 Verde: indicador dentro de parámetros normales.
- 🟠 Naranja: alerta (cerca del umbral de atención).
- 🔴 Rojo: crítico (cruza el umbral definido para el sistema).

Los umbrales exactos están documentados en el Manual Técnico y en
`config/indicator_mapping.py::RANGOS_INDICADORES`.
