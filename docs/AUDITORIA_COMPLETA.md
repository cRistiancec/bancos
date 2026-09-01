# Auditoría Completa del Proyecto

**Sistema Financiero Privado — COSEDE**
Auditoría previa a la refactorización institucional (Fase 1)
Fecha de auditoría: 2026-07-27

---

## 1. Resumen ejecutivo

El proyecto ("Radar Bancario Ecuador") es un dashboard Streamlit funcional de 4 páginas sobre 3 datasets Parquet reales del sistema bancario ecuatoriano (balance, pérdidas y ganancias, indicadores CAMEL). El código es correcto y produce resultados válidos, pero tiene tres problemas estructurales principales:

1. **Duplicación severa**: el selector jerárquico de cuentas (4 niveles) está copiado 3 veces dentro de una sola página (`2_Balance_General.py`); la lógica Absoluto/Indexado/Participación se repite en 3 páginas distintas.
2. **Biblioteca de gráficos infrautilizada**: `utils/charts.py` define 11 funciones reutilizables; 8 de ellas no se usan en ninguna página activa (código muerto), mientras que las páginas reimplementan gráficos equivalentes con `go.Figure` directo.
3. **Ambición del nuevo alcance vs. datos disponibles**: gran parte de la lista de módulos solicitados para la plataforma institucional (LCR/NSFR, VaR/CVaR, red de interconexión interbancaria, vintage/roll-rate de cartera, tasas de mercado, tipo de cambio) no tiene ninguna fuente de datos en este repositorio. Se detalla la matriz de factibilidad en la sección 6.

No se detectaron vulnerabilidades de seguridad relevantes (no hay inputs de usuario que lleguen a `eval`, `exec`, SQL o rutas de archivo sin sanear). El mayor riesgo no funcional es un bug latente: `validar_ecuacion_contable()` filtra por una columna `hoja` que **no existe** en `balance.parquet` (columnas reales: `banco, fecha, codigo, cuenta, valor, nivel`), lo que haría fallar esa función en cuanto se invoque.

---

## 2. Arquitectura actual

```
bancos/
├── Inicio.py                      # entry point (multipage clásico de Streamlit)
├── app.py                         # archivo vacío (0 bytes) — intento de migración no completado
├── pages/
│   ├── 1_Panorama.py
│   ├── 2_Balance_General.py
│   ├── 3_Perdidas_Ganancias.py
│   ├── 3_Perdidas_Ganancias.py.bak   # archivo huérfano, no debería estar en pages/
│   └── 4_CAMEL.py
├── archived_pages/
│   └── 0_Calidad_old.py           # módulo completo, archivado deliberadamente (no roto)
├── utils/
│   ├── data_loader.py             # carga+limpieza con @st.cache_data
│   ├── charts.py                  # 11 builders de gráficos Plotly
│   └── data_quality.py            # validaciones (sin caching)
├── config/
│   └── indicator_mapping.py       # códigos contables, indicadores CAMEL, colores, umbrales
├── master_data/
│   ├── balance.parquet            # 18.7 MB — banco,fecha,codigo,cuenta,valor,nivel
│   ├── pyg.parquet                # 9.9 MB — banco,fecha,codigo,cuenta,valor_acumulado,valor_mes,valor_12m
│   └── camel.parquet              # 1.6 MB — banco,fecha,codigo,indicador,valor,categoria
└── scripts/                       # pipeline: descargar.py → descomprimir_zips.py → procesar_{balance,pyg,camel}.py
```

Streamlit instalado: **1.59.2** (soporta `st.navigation()`/`st.Page()` de sobra, permitiendo una navegación agrupada por secciones en vez del mecanismo clásico de `pages/` con prefijos numéricos).

`master_data/metadata.json` (usado por `cargar_metadata()` en `Inicio.py` y `data_loader.py`) **no existe actualmente** — está en `.gitignore` (`*.json`) y solo se regenera al re-ejecutar `procesar_balance.py` localmente. El código ya maneja su ausencia con gracia (retorna `None`/dict de error).

---

## 3. Inventario de código muerto

| Símbolo | Ubicación | Estado |
|---|---|---|
| `crear_linea_temporal()` | `utils/charts.py` | Importado en `1_Panorama.py` pero nunca invocado |
| `crear_gauge()` | `utils/charts.py` | Importado en `1_Panorama.py` pero nunca invocado |
| `crear_radar_camel()` | `utils/charts.py` | No importado en ninguna página activa |
| `crear_heatmap()` | `utils/charts.py` | No importado; Balance General y CAMEL reimplementan heatmaps con `go.Heatmap` manual |
| `crear_scatter_posicionamiento()` | `utils/charts.py` | No usado en ninguna página |
| `crear_barras_apiladas_100()` | `utils/charts.py` | No usado en ninguna página |
| `render_kpi_row()` | `utils/charts.py` | No usado (solo se usa `render_kpi_card()` individualmente) |
| `aplicar_colores_bancos()` | `utils/charts.py` | No usado |
| `calcular_concentracion_hhi()` | `1_Panorama.py` | Definida y correcta, pero nunca renderizada en la UI |
| `obtener_orden_bancos_por_activos()` | `3_Perdidas_Ganancias.py` | Definida, nunca invocada |
| `pages/3_Perdidas_Ganancias.py.bak` | `pages/` | Archivo de respaldo huérfano (no afecta a Streamlit por la extensión `.bak`, pero es basura de repositorio) |

**Decisión de refactor**: en vez de eliminar estas funciones, la mayoría se **reactivan** conectándolas a las nuevas pestañas reales (p. ej. `crear_radar_camel` → pestaña Comparativos; `calcular_concentracion_hhi` → Riesgo de Concentración), ya que su lógica es correcta y hoy solo falta la UI que las invoque.

---

## 4. Duplicación y otros hallazgos de mantenibilidad

- **Selector jerárquico de 4 niveles triplicado**: `2_Balance_General.py` repite ~150 líneas de lógica de cascada (categoría → grupo → subcuenta → detalle) tres veces, una por sección, con sufijos de key distintos (`_heat`, `_r`). Es el mayor foco de duplicación del proyecto.
- **Patrón Absoluto/Indexado/Participación repetido** en `2_Balance_General.py` y `3_Perdidas_Ganancias.py` con la misma estructura de cálculo pero copiada, no compartida.
- **Doble decorador `@st.cache_data`** aplicado accidentalmente sobre `obtener_heatmap_indicador()` en `4_CAMEL.py` (línea duplicada, inofensivo pero descuidado).
- **Tabs `tab1, tab3, tab4`** en `4_CAMEL.py` sin `tab2` — sugiere una pestaña eliminada en el pasado sin renombrar variables; no rompe nada pero confunde a futuros mantenedores.
- **Taxonomía CAMEL duplicada**: `4_CAMEL.py` define localmente `INDICADORES_PRINCIPALES`, `ESCALAS_COLORES_HEATMAP` y `RANGOS_HEATMAP` (~200 líneas) que se solapan con `GRUPOS_INDICADORES`/`ETIQUETAS_INDICADORES`/`RANGOS_INDICADORES` ya definidos en `config/indicator_mapping.py` — dos fuentes de verdad para la misma taxonomía.
- **Exclusión de bancos hardcodeada** (`['Citibank', 'Coopnacional']` para `COB_TOT`) embebida en la lógica de la página en vez de en configuración.
- **`utils/data_quality.py` no usa `@st.cache_data` en ninguna función**, a diferencia de `data_loader.py`; las validaciones se recalculan en cada rerun.
- **Página CAMEL no usa `utils/charts.py`**: define sus propias `crear_grafico_evolucion`, `crear_ranking_barras`, `crear_heatmap_indicador` locales — y su `crear_ranking_barras` local **tiene el mismo nombre pero distinta firma** que la de `utils/charts.py`, un riesgo real de confusión para quien intente reutilizar código entre páginas.
- **Balance General y P&G no usan `utils/charts.py` en absoluto** — todos sus gráficos son `go.Figure` inline, duplicando lo que ya existe en la librería compartida.

## 5. Bug confirmado

`utils/data_quality.py::validar_ecuacion_contable()` (línea 225) ejecuta:
```python
df_fecha = df[(df['fecha'] == fecha) & (df['hoja'] == 'BAL')]
```
Se verificó el esquema real de `balance.parquet` (`banco, fecha, codigo, cuenta, valor, nivel`) — **la columna `hoja` no existe**. Esta función lanzaría `KeyError` en cuanto se invocara. Como hoy solo se usa desde el módulo archivado `archived_pages/0_Calidad_old.py` (fuera de navegación), el bug nunca se manifestó en producción. Al revivir el módulo de Calidad de Datos en esta refactorización, se corrige eliminando ese filtro (cada parquet ya corresponde a una sola hoja, por lo que el filtro es innecesario, no solo incorrecto).

## 5.1 Segundo bug confirmado (preservado intencionalmente en Fase 1)

`pages/3_Perdidas_Ganancias.py`, sección "Ranking de Bancos por Indicador": el
DataFrame `df_rank` se ordena **ascendente** (`sort_values('valor_millones',
ascending=True)`) antes de calcular la métrica "Concentración Top 5" con
`df_rank.head(5)`. Como el orden es ascendente, `head(5)` toma los **5 bancos
más pequeños**, no los más grandes — la etiqueta "Top 5" es engañosa. Se
verificó que `2_Balance_General.py` no tiene este problema (ahí el ranking se
ordena descendente antes del mismo cálculo).

Se decidió **preservar el bug tal cual** en la página migrada
`pages/perdidas_ganancias.py` (con un comentario explícito en el código),
en cumplimiento estricto de "no alterar resultados" de esta fase. Corregirlo
es una decisión de negocio que debe aprobarse explícitamente antes de
cambiar una cifra que los usuarios ya han visto en producción.

## 6. Matriz de factibilidad — módulos solicitados vs. datos disponibles

Verificado contra el pipeline completo (`scripts/descargar.py` → `procesar_balance/pyg/camel.py`) y el esquema real de los 3 parquets.

| Categoría solicitada | Dato base disponible | Factible con datos reales |
|---|---|---|
| Panorama, Rankings, Comparativos, Evolución Histórica | balance/pyg/camel completos | ✅ Sí |
| CAMEL (Capital, Activos, Management, Earnings, Liquidez) | `camel.parquet`, ~50 indicadores | ✅ Sí — se mantiene el nombre **CAMEL**, no "CAMELS": el 6º componente (Sensibilidad, S) no tiene datos de mercado que lo respalden |
| Riesgo de Crédito (mora, cobertura, participación por segmento) | `MOR_*`, `COB_*`, `PART_*` en `camel.parquet` | ✅ Sí — vintage/roll-rate/recovery: ❌ no hay datos de cohortes de originación |
| Riesgo de Liquidez (ratio LIQ) | `LIQ` en `camel.parquet` | ✅ Sí (ratio agregado) — LCR/NSFR/gap de vencimientos: ❌ no hay datos de plazos/madurez |
| Riesgo de Solvencia | `SOL` en `camel.parquet` + patrimonio/activos en `balance.parquet` | ✅ Sí |
| Riesgo de Concentración (HHI, CR5, CR10) | Participación de mercado calculable de `balance.parquet` | ✅ Sí — concentración por depositante: ❌ no hay datos a nivel de depositante |
| Riesgo Sistémico (índice propio) | Combinable de tamaño + indicadores de estrés existentes | ✅ **Implementado en Fase 2** (`analytics/systemic_index.py`, `pages/riesgo_sistemico.py`) — índice compuesto transparente (tamaño × estrés), metodología interna documentada en `docs/ManualTecnico.md`; red de interconexión/contagio interbancario sigue ❌ (solo existe el saldo agregado de operaciones interbancarias, códigos `12`/`22`, no una matriz de contrapartes) |
| Riesgo de Mercado (VaR, CVaR, duración, riesgo cambiario) | — | ❌ No hay tasas de mercado, precios de instrumentos ni serie cambiaria en el repo (Ecuador dolarizado, pero tampoco hay tasas activas/pasivas). Sigue fuera de alcance. |
| Riesgo Operacional | — | ❌ No hay registro de eventos de pérdida operacional. Sigue fuera de alcance. |
| Riesgo de Tasa de Interés (repricing gap, sensibilidad) | — | ❌ No hay calendario de repreciación ni tasas por instrumento. Sigue fuera de alcance. |
| Stress Testing | Series históricas de balance/PyG/CAMEL | ✅ **Implementado en Fase 2** (`analytics/stress_testing.py`, `pages/stress_testing.py`) — sensibilidad de balance/rentabilidad ante shocks configurables aplicados a las series reales; explícitamente etiquetado como no-regulatorio y no-VaR; no estima impacto en dólares del Seguro de Depósitos (sin datos de depositante) |
| Mapas Interactivos | — | ❌ No hay coordenadas/provincia de agencias en los datos procesados. Sigue fuera de alcance. |
| Modelos Predictivos / ML (forecasting, anomalías, clustering) | Series temporales mensuales reales | ✅ **Implementado en Fase 2** (`models/forecasting.py`, `models/anomaly_detection.py`, `models/clustering.py`, `pages/modelos_predictivos.py`) — Holt/Isolation Forest/K-Means sobre series reales; modelos supervisados (XGBoost/LSTM) siguen fuera (requieren variable objetivo validada, ver `models/README.md`) |
| Asistente de IA | — | ✅ **Implementado en Fase 2** como asistente determinístico (`services/assistant_engine.py`, `pages/asistente_riesgos.py`) sobre datos reales; integración con un LLM externo queda como stub documentado (`ProveedorLLM`) para cuando se provean credenciales |

**Regla aplicada en todo el refactor**: donde el dato no existe, la pestaña (si se construye) muestra un aviso institucional explícito de "módulo en preparación — requiere fuente de datos: X", nunca un número inventado.

## 7. Alcance de las fases

**Fase 1** (completada): rebranding institucional completo + reorganización de arquitectura + **todas las pestañas marcadas como ✅ con datos reales** en la tabla anterior (Panorama, Balance General, P&G, CAMEL, Riesgo de Crédito, Riesgo de Liquidez, Riesgo de Solvencia, Riesgo de Concentración, Ranking, Comparativos, Evolución Histórica, Alertas Tempranas, Calidad de Datos, Reportes, Configuración, Resumen Ejecutivo, Monitoreo Prudencial).

**Fase 2** (completada): los 4 módulos que eran viables con metodología propia sobre datos reales — Riesgo Sistémico (índice compuesto), Stress Testing (sensibilidad de balance), Modelos Predictivos (forecasting/anomalías/clustering) y Asistente de Riesgos (determinístico). Ver `docs/ManualTecnico.md` para cada metodología.

**Fase 3** (completada): forecasting con validación real (backtesting:
MAE/RMSE/MAPE sobre datos históricos ya conocidos), Alertas Predictivas
(mismo modelo aplicado hacia adelante, avisa deterioro proyectado antes de
que ocurra) y Calificación de Riesgo Consolidada (rating A-E por banco,
70% CAMEL + 30% resiliencia en stress testing — ver
`docs/ManualTecnico.md` para la justificación de por qué NO incluye el
Índice Sistémico en ese compuesto).

**Sigue fuera de alcance** (sin fuente de datos real, no se aborda hasta que exista): Riesgo de Mercado (VaR/CVaR), Riesgo Operacional, Riesgo de Tasa de Interés, Mapas Interactivos, red de interconexión/contagio interbancario, modelos supervisados de ML (XGBoost/LSTM) e integración con un LLM real para el Asistente.

## 7.1 Verificación de la Fase 1 (ejecutada)

Se corrieron las 21 páginas (4 originales conservadas para comparación + 4
migradas + 13 nuevas) con `streamlit.testing.v1.AppTest` (ejecución headless
server-side, sin navegador). Resultado: **21/21 sin excepciones**. Un hallazgo
menor durante la verificación (`st.page_link` lanzaba `KeyError` cuando
`resumen_ejecutivo.py` se probaba de forma aislada, fuera del contexto de
`st.navigation`) se corrigió envolviendo esas llamadas en `try/except`, igual
que ya hacía `ui/sidebar.py`; confirmado que `app.py` completo (con
navegación real) nunca tuvo esta excepción.

También se observa que Streamlit 1.59.2 emite un `DeprecationWarning` en cada
`use_container_width=True` (parámetro reemplazado por `width='stretch'`,
remoción anunciada después de 2025-12-31). Aparece tanto en las páginas
originales como en las migradas/nuevas — no es una regresión de este
refactor. Sigue funcionando (es warning, no error); se recomienda una pasada
mecánica de reemplazo en una fase posterior.

## 7.2 Hallazgo de calidad de datos (detectado por la herramienta de Fase 2)

Verificando el forecasting de ROA promedio del sistema, se detectó que el
banco **Amibank** reporta un ROA de **467.6%** en 4 meses de 2004 (pico:
2004-09-30), muy por encima de cualquier valor plausible — esto infla el
promedio simple del sistema en esos meses a >25% (vs. ~0.7% típico). Es un
problema de la fuente de datos original (`master_data/camel.parquet`), no
introducido por este refactor; no se modifica porque alterar datos
históricos está fuera de alcance sin aprobación explícita. La página
**Modelos Predictivos → Detección de Anomalías** (Fase 2) está justamente
diseñada para exponer este tipo de casos; se recomienda como fast-follow
validar con el área de datos si ese registro debe corregirse en el pipeline
de origen (`scripts/procesar_camel.py`).

## 7.3 Bug de nombres de banco (encontrado y corregido en el pulido de 2026-07-27)

Al corregir los `FutureWarning` de pandas sobre `groupby`/`pivot_table` con
columnas categóricas, se verificó el contenido real de la categoría `banco`
en `master_data/*.parquet` y se descubrió que **`BANCOS_SISTEMA` y
`COLORES_BANCOS` en `config/indicator_mapping.py` tenían 3 nombres
desalineados** con los datos reales:

| Config (antes) | Dato real en parquet |
|---|---|
| `Atlantida` | `Atlantida (antes DMiro)` |
| `Comercial Manabi` | `Comercial Manabí` |
| `Ruminahui` | `Rumiñahui` |

Esto tenía dos consecuencias reales en producción, ambas silenciosas:

1. `obtener_color_banco()` no encontraba coincidencia exacta para esos 3
   bancos y les asignaba el color gris de respaldo (`#636363`) en **todas**
   las visualizaciones de la plataforma, en vez de su color distintivo.
2. `detectar_bancos_faltantes()` (usado en la página Calidad de Datos)
   reportaba falsamente esos 3 bancos como "sin datos", cuando en realidad
   **los 24 bancos de `BANCOS_SISTEMA` tienen datos completos** en los 3
   datasets (se verificó fila por fila) — contradiciendo también una nota
   heredada del README original ("Banco Amazonas: no tiene datos"), que
   tampoco es correcta: Amazonas tiene 381,156 filas en `balance.parquet`.

Se corrigieron los nombres en `config/indicator_mapping.py` (mismo color
asignado, solo se corrigió la ortografía de la clave) y se actualizó
`QUICKSTART.md` (decía "23 de 24 bancos", ahora dice "24 bancos"). No se
modificó ningún cálculo ni el pipeline de datos — es una corrección de
mapeo de nombres, con el mismo efecto de "arreglar un bug", igual que la
columna `hoja` de la sección 5.

## 8. Otras observaciones (rendimiento, UX, seguridad)

- **Caching**: `data_loader.py` usa `@st.cache_data(ttl=3600)` correctamente en las 3 cargas principales; la mayoría de funciones de agregación en las páginas también cachean. `data_quality.py` no cachea nada — bajo impacto porque hoy no está en navegación activa, pero se corrige al revivir el módulo.
- **Seguridad**: no hay uso de `eval`/`exec`/subprocess con input de usuario, ni SQL. El único punto de exportación a archivo (`exportar_reporte_calidad`) usa un buffer en memoria (`io.BytesIO`), no escribe a disco con rutas derivadas de input de usuario.
- **Dependencias**: el entorno de ejecución de esta máquina tenía `numpy` ausente (paquete corrupto/incompleto) pese a que `pandas`/`scikit-learn`/`streamlit` sí estaban instalados — se reinstaló como parte de la verificación de esta auditoría; no es un problema del código del proyecto.
- **UX**: los 3 selectores jerárquicos duplicados de `2_Balance_General.py` no solo son deuda técnica sino una inconsistencia de experiencia (comportamiento sutilmente distinto si se edita uno y no los otros dos).
- **Branding actual**: el pie de página de `Inicio.py` y el `README.md` atribuyen el proyecto a "Juan Pablo Erráez T." — se reemplaza por la autoría institucional solicitada (Eco. Cristian Coronel Quezada, MBA — Coordinación Técnica de Riesgos y Estudios — COSEDE) en el marco de esta refactorización, sin alterar el historial de git.
