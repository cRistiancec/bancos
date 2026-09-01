# Arquitectura — Sistema Financiero Privado

Documento técnico de arquitectura. Cubre las dos mitades del sistema: el
pipeline de datos (heredado y adaptado de `jp1309/bancos`, automatizado vía
GitHub Actions) y la aplicación Streamlit (refactorizada institucionalmente
en Fase 1-3, ver `docs/AUDITORIA_COMPLETA.md`).

## Vista general

```text
┌──────────────────────────────────────────────────────────────┐
│ Superintendencia de Bancos: Boletines de Series por Entidad  │
└───────────────────────────┬──────────────────────────────────┘
                            │ Selenium + descargas HTTP
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Staging: ZIP por entidad → XLSX → BAL / PYG / CAMEL           │
│ fuente_bancos.py valida estructura y fecha interna            │
└───────────────────────────┬──────────────────────────────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Balance ETL       PyG ETL        CAMEL ETL
             │              │              │
             └──────────────┼──────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ master_data: tres Parquet + metadata.json + update_status.json│
└───────────────────────────┬──────────────────────────────────┘
                            │ puerta de calidad (validar_actualizacion.py)
                            ▼
                   GitHub main / versionado
                            │
                            ▼
                Streamlit Community Cloud
                            │
                            ▼
                    app.py (st.navigation)
```

## Parte 1 — Pipeline de datos

### 1. Fuente

`scripts/config.py` calcula el mes anterior y define el portal `bancos-2/`, el número esperado de entidades y los tiempos de Selenium.

`scripts/descargar.py` navega el portal, obtiene los ZIP y promueve el staging solo después de validarlo. `scripts/fuente_bancos.py` inspecciona ZIP/XLSX y fecha interna.

Decisión clave: una URL estable o un HTTP 200 no demuestra avance; el contenido puede seguir en el mes anterior.

### 2. Transformación

- `procesar_balance.py`: normaliza la hoja BAL, calcula jerarquía y consolida historia.
- `procesar_pyg.py`: conserva acumulados, desacumula meses y calcula rolling de 12 meses.
- `procesar_camel.py`: extrae los indicadores y los categoriza.

Cada procesador falla si encuentra entidades ausentes, vacías o no procesables y escribe el Parquet mediante temporal y reemplazo.

### 3. Publicación de datos

`master_data/` es la interfaz estable entre ETL y frontend. Los cinco artefactos versionados (`balance.parquet`, `pyg.parquet`, `camel.parquet`, `metadata.json`, `update_status.json`) forman una unidad lógica — nunca se publica un subconjunto.

`scripts/validar_actualizacion.py` actúa como publication gate y usa PyArrow para inspección de esquema y lecturas acotadas de claves.

### 4. Orquestación transaccional

`scripts/actualizar_datos.py` (invocado por `.github/workflows/actualizar-datos.yml`) es la frontera transaccional:

1. staging de fuente;
2. respaldo de los cinco artefactos publicados;
3. los tres procesadores;
4. validación conjunta contra el estado anterior;
5. commit de la unidad de publicación, o restauración del respaldo si algo falla.

Un fallo antes del commit no modifica la publicación remota. Un fallo de ETL local restaura el respaldo temporal. Ver `docs/AUTOMATIZACION.md` para el calendario de reintentos (días 6-20) y los códigos de salida.

## Parte 2 — Aplicación Streamlit

### Punto de entrada

```
streamlit run app.py
```

`app.py` construye la navegación (`config/nav_registry.construir_navegacion()`,
basada en `st.navigation()`/`st.Page()`, Streamlit ≥1.36) y ejecuta la página
seleccionada. La app completa vive en `pages/*.py` (23 vistas) registradas
explícitamente en `config/nav_registry.py`, agrupadas en 7 secciones de
sidebar. Ya no existen `Inicio.py` ni los `pages/N_*.py` numerados del
proyecto original — ver `CHANGELOG.md` `[5.0.0]` para el detalle del
reemplazo.

### Estructura de carpetas

```
bancos/
├── app.py                     # entry point unico de la app Streamlit
├── .streamlit/config.toml     # tema oscuro institucional (nativo de Streamlit)
├── ui/                        # chrome compartido por toda pagina
│   ├── theme.py                   # inyeccion de styles/institutional.css
│   ├── header.py                  # header institucional (logo, reloj, semaforo)
│   ├── sidebar.py                  # contenido adicional del sidebar
│   └── layout.py                   # render_page(): page_config + tema + header + sidebar
├── pages/                     # 23 vistas (una por archivo, sin prefijos numericos)
├── components/                # widgets reutilizables entre paginas
│   ├── kpi_card.py                 # tarjetas KPI
│   ├── semaforo.py                  # badge de severidad OK/ALERTA/CRITICO
│   ├── account_selector.py         # selector jerarquico de cuentas (1→2→4→6 digitos)
│   ├── mode_selector.py            # Absoluto/Indexado/Participacion
│   └── indicator_panel.py          # panel Ranking+Evolucion+Heatmap para un indicador CAMEL
├── charts/
│   └── builders.py                 # builders de Plotly (ranking, treemap, linea, radar, gauge, heatmap, sparkline...)
├── analytics/                 # calculos de riesgo sobre datos reales
│   ├── concentracion.py            # HHI, CR5, CR10
│   ├── camel_scoring.py            # semaforo por umbral + score 0-100 para radar CAMEL
│   ├── camel_explorer.py           # ranking/evolucion/heatmap genericos sobre camel.parquet
│   ├── early_warning.py            # motor de alertas por umbral (reglas, no ML)
│   ├── systemic_index.py           # indice sistemico propio (tamaño x estres)
│   ├── stress_testing.py           # sensibilidad a escenarios hipoteticos configurables
│   ├── predictive_alerts.py        # alertas de deterioro proyectado (forecasting + semaforo)
│   └── risk_rating.py              # calificacion A-E (70% CAMEL + 30% resiliencia)
├── models/                     # analitica avanzada real sobre series reales
│   ├── forecasting.py               # suavizado exponencial de Holt + backtesting (statsmodels)
│   ├── anomaly_detection.py         # Isolation Forest (scikit-learn)
│   └── clustering.py                # K-Means + PCA (scikit-learn)
├── services/
│   ├── data_service.py             # carga y cache de balance/pyg/camel/metadata
│   └── assistant_engine.py         # motor del Asistente de Riesgos (determinista + stub LLM)
├── utils/
│   ├── data_quality.py             # validaciones de calidad de datos (para la pagina Calidad de Datos)
│   └── pdf_export.py               # exportacion de reportes/tablas a PDF (reportlab)
├── config/
│   ├── indicator_mapping.py        # codigos contables, indicadores CAMEL, colores, umbrales
│   ├── theme_tokens.py             # paleta de colores institucional
│   └── nav_registry.py             # registro de paginas para st.navigation
├── assets/                    # logo_cosede.png + wordmark de respaldo
├── styles/
│   └── institutional.css           # refinamientos visuales sobre el tema nativo
├── master_data/                # balance.parquet, pyg.parquet, camel.parquet, metadata.json, update_status.json
├── scripts/                    # pipeline de descarga/procesamiento/validacion/orquestacion (Parte 1)
├── tests/                      # suite pytest
├── .github/workflows/          # automatizacion mensual
└── docs/
```

### Flujo de datos dentro de la app

```
master_data/*.parquet → services/data_service.py (carga + @st.cache_data) → pages/*.py
```

Ninguna página lee `master_data/*.parquet` directamente: siempre pasa por
`services/data_service.py`, que es la única fuente de verdad para carga y
limpieza dentro de la aplicación.

### Capas y responsabilidad

| Capa | Responsabilidad | No debe contener |
|---|---|---|
| `services/` | Leer parquet, cachear, limpiar, exponer DataFrames | Lógica de presentación |
| `analytics/` | Cálculos derivados (HHI, semáforo, alertas, scores) sobre DataFrames ya cargados | Llamadas a `st.*` |
| `charts/` | Construir figuras Plotly a partir de DataFrames ya calculados | Lógica de negocio |
| `components/` | Widgets Streamlit reutilizables (selectores, tarjetas, paneles) | Cálculos de negocio propios |
| `ui/` | Chrome de página (tema, header, sidebar, layout) | Contenido específico de una página |
| `pages/` | Orquestación: llama a services → analytics → charts/components | Duplicar lógica ya existente en las capas anteriores |

### Por qué `st.navigation()` en vez del mecanismo clásico de `pages/`

Frente al mecanismo clásico (carpeta `pages/` con prefijos numéricos para el
orden), `st.navigation()`/`st.Page()` permite: agrupar páginas en secciones
de sidebar con títulos propios, controlar el orden sin depender de nombres
de archivo, y definir una página por defecto (`Resumen Ejecutivo`) sin
trucos de nombre. `app.py` es el único script que llama a
`st.set_page_config()` — cada página también puede llamarlo porque
`st.navigation().run()` ejecuta la página seleccionada como si fuera el
script principal de esa corrida.

### Principio de no-fabricación de datos

Toda pestaña que requiere una fuente de datos que **no existe** en
`master_data/` (LCR/NSFR, VaR/CVaR, red de interconexión interbancaria,
vintage/roll-rate de cartera, tasas de mercado, mapas geográficos) usa
`ui.layout.render_modulo_en_preparacion()` en vez de calcular o inventar un
valor. Ver la matriz de factibilidad completa en
`docs/AUDITORIA_COMPLETA.md` sección 6.

## Rendimiento

- Parquet columnar reduce I/O y almacenamiento.
- `@st.cache_data` evita recargar datos en cada interacción, tanto en `services/data_service.py` como en las funciones de agregación de `analytics/` y `utils/data_quality.py`.
- Los selectores limitan comparaciones simultáneas (hasta 10 bancos), pero rankings y cobertura incluyen todas las entidades.

## Seguridad e integridad

- No hay credenciales de la fuente; los boletines son públicos.
- GitHub Actions usa `GITHUB_TOKEN` con `contents: write` limitado al workflow de actualización.
- La extracción de ZIP rechaza rutas inseguras (protección contra path traversal).
- El pipeline no ejecuta macros de los XLSX.
- Los datos se publican solo después de la puerta de calidad determinística (`validar_actualizacion.py`).
- `.streamlit/config.toml` deshabilita `showErrorDetails` en producción para no exponer trazas internas a usuarios públicos no autenticados.

## Decisiones y tradeoffs

### Parquet dentro de Git

Ventajas: despliegue sencillo, reproducibilidad por commit y rollback directo. Costos: repositorio más pesado y commits de datos binarios. Los tamaños actuales permanecen bajo el límite duro de GitHub, aunque deben vigilarse.

### Reescritura de Balance

Balance consolida una historia extensa y puede ser la etapa más costosa del ETL. La escritura atómica prioriza seguridad sobre una actualización mínima de bytes.

### Número fijo de entidades esperadas

La expectativa de un número fijo de bancos funciona como alarma contra fuentes parciales. El costo es que un cambio institucional legítimo (fusión, cierre, entrada de un nuevo banco) exige intervención humana y actualización coordinada de configuración, pruebas y documentación.

## Extender el sistema

Para agregar un dataset nuevo al pipeline:

1. definir fuente y clave estable;
2. crear procesador con salida atómica;
3. agregar esquema y clave a `DATASETS` del validador (`scripts/validar_actualizacion.py`);
4. incluirlo en respaldo, rollback y commit del workflow de Actions;
5. documentarlo en `docs/DICCIONARIO_DATOS.md`;
6. añadir pruebas de cobertura, fecha, duplicados e historia;
7. integrar la carga en `services/data_service.py` y consumirla desde una página nueva.

No conecte una página directamente a archivos temporales o descargas crudas — siempre a través de `services/data_service.py`.
