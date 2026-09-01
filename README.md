# Sistema Financiero Privado

**Sistema Inteligente para el Monitoreo Integral del Sistema Bancario Privado del Ecuador**

Plataforma institucional de inteligencia de riesgos construida sobre datos
públicos de la Superintendencia de Bancos del Ecuador.

**Autor institucional:** Eco. Cristian Coronel Quezada, MBA
**Área:** Coordinación Técnica de Riesgos y Estudios — COSEDE

> Este proyecto es la evolución institucional de "Radar Bancario Ecuador"
> (desarrollo original: Juan Pablo Erráez T., [jp1309/bancos](https://github.com/jp1309/bancos),
> licencia MIT), refactorizado hacia una plataforma de monitoreo prudencial
> en julio de 2026 e integrado luego con la automatización de actualización
> mensual de datos desarrollada en paralelo en el repositorio original. Ver
> `docs/AUDITORIA_COMPLETA.md` y `CHANGELOG.md` para el detalle completo del
> proceso.

## Estado de los datos

La cifra vigente no se mantiene a mano en la interfaz: la aplicación lee
`master_data/metadata.json` en cada carga. Antes de publicar, el pipeline
exige que los tres Parquet lleguen al mismo mes y que todas las entidades
estén presentes en ese corte — ver `master_data/metadata.json` y
`docs/DICCIONARIO_DATOS.md` para el estado exacto vigente.

## Ejecutar la plataforma

```bash
pip install -r requirements.txt
streamlit run app.py
```

Ver `QUICKSTART.md` para una guía paso a paso y `docs/ManualUsuario.md` para
el manual funcional completo.

## Qué incluye

23 páginas agrupadas en 7 secciones — Resumen Ejecutivo, Panorama Bancario,
Monitoreo Prudencial, Indicadores CAMEL, Alertas Tempranas, Alertas
Predictivas, Calificación de Riesgo, Riesgo de
Crédito/Liquidez/Solvencia/Concentración/Sistémico, Balance General,
Pérdidas y Ganancias, Ranking de Bancos, Comparativos entre Bancos,
Evolución Histórica, Stress Testing, Modelos Predictivos, Asistente de
Riesgos, Calidad de Datos, Reportes y Configuración — todas construidas
sobre datos reales del sistema. Ver `docs/ManualUsuario.md` para el detalle
de cada una.

**Principio de esta plataforma: cero cifras inventadas.** Donde un análisis
solicitado (p. ej. LCR/NSFR, VaR, red de interconexión interbancaria,
vintage de cartera) no tiene una fuente de datos real en el pipeline actual,
la página lo declara explícitamente como "módulo en preparación" en vez de
mostrar un número calculado sobre supuestos. La matriz completa de qué es
real y qué no está en `docs/AUDITORIA_COMPLETA.md`.

## Fuente de Datos

- **Origen**: Superintendencia de Bancos del Ecuador — [Boletines de Series por Entidad](https://www.superbancos.gob.ec/estadisticas/portalestudios/bancos-2/) (Catálogo Único de Cuentas)
- **Período**: desde enero 2003, con actualización mensual automática (ver más abajo)
- **Formato**: Parquet (`master_data/balance.parquet`, `pyg.parquet`, `camel.parquet`) + `metadata.json` con el estado exacto de cada publicación

## Actualización de datos

La vía recomendada es el workflow **Actualizar Datos Bancarios** en GitHub
Actions (heredado y adaptado de `jp1309/bancos`). Intenta la actualización
los días 6, 8, 10, 12, 14, 16, 18 y 20 de cada mes a las 13:00 UTC (08:00
Ecuador continental), y se detiene en cuanto los tres datasets llegan al mes
objetivo con la puerta de calidad en verde. El detalle completo del ciclo
(reintentos, códigos de salida, qué pasa si la fuente no publica a tiempo)
está en `docs/AUTOMATIZACION.md`.

Ejecución manual local:

```bash
python -m pip install -r requirements-scraping.txt
python scripts/actualizar_datos.py
```

| Código de salida | Significado | Acción |
|---:|---|---|
| `0` | Actualización completa o publicación ya vigente | No requiere corrección |
| `2` | La fuente oficial aún no avanzó al mes objetivo | No-op; esperar el siguiente intento |
| Otro | Fallo real de descarga, ETL o validación | Revisar logs; se conserva la última versión válida |

No se debe forzar un commit cuando el proceso devuelve `2`, ni publicar un
subconjunto de los cinco artefactos (`balance.parquet`, `pyg.parquet`,
`camel.parquet`, `metadata.json`, `update_status.json`) para un corte nuevo.

## Validación

```bash
python -m pytest tests/ -v
python scripts/validar_actualizacion.py
```

La puerta de publicación (`scripts/validar_actualizacion.py`) comprueba
esquema, continuidad mensual, ausencia de duplicados, cobertura de
entidades, coherencia con `metadata.json`, y que la nueva publicación no
pierda meses ni bancos ya publicados respecto del estado anterior. Ver
`docs/AUTOMATIZACION.md`.

## Arquitectura

```text
Superintendencia de Bancos
        │  ZIP por entidad
        ▼
scripts/descargar.py + fuente_bancos.py       (valida ZIP, XLSX, hojas, fecha interna)
        ▼
scripts/procesar_{balance,pyg,camel}.py  ─►  master_data/*.parquet + metadata.json
        ▼
scripts/validar_actualizacion.py              (puerta de calidad)
        ▼
GitHub main ─► Streamlit Community Cloud
        │
        ▼
app.py (st.navigation)
  ├── pages/            23 vistas agrupadas en 7 secciones
  ├── ui/                tema, header, sidebar, layout compartidos
  ├── components/         widgets reutilizables (selectores, tarjetas, paneles)
  ├── charts/              builders de Plotly
  ├── analytics/            HHI/CR5/CR10, semáforo, alertas, score CAMEL, índice sistémico, stress testing, calificación de riesgo
  ├── models/                 forecasting (+backtesting), detección de anomalías, clustering
  ├── services/                carga/caché de datos (Parquet) + motor del Asistente de Riesgos
  └── config/                   códigos contables, paleta, registro de navegación
```

Detalle completo en `docs/ARQUITECTURA.md`. Manual técnico (metodologías,
umbrales, qué no está implementado y por qué) en `docs/ManualTecnico.md`.

## Documentación

| Documento | Contenido |
|---|---|
| `docs/AUDITORIA_COMPLETA.md` | Auditoría previa al refactor institucional: arquitectura anterior, deuda técnica, matriz de factibilidad de datos |
| `docs/ARQUITECTURA.md` | Arquitectura técnica actual (pipeline de datos + aplicación) |
| `docs/ManualUsuario.md` | Manual funcional por módulo |
| `docs/ManualTecnico.md` | Metodologías, umbrales, fórmulas y qué no está implementado |
| `docs/DESPLIEGUE.md` | Streamlit Cloud, servidor propio, Docker |
| `docs/AUTOMATIZACION.md` | GitHub Actions, calendario, códigos de salida y monitoreo |
| `docs/OPERACION_Y_RECUPERACION.md` | Runbook operativo, incidentes, rollback y recuperación |
| `docs/DICCIONARIO_DATOS.md` | Esquemas, claves, unidades y semántica de los datos |
| `QUICKSTART.md` | Guía de instalación y primeros pasos |
| `CHANGELOG.md` | Historial de versiones |

## Instalación y requisitos

- Python 3.11+ (recomendado; probado también en 3.14)
- `pip install -r requirements.txt` (Streamlit, Pandas, NumPy, Plotly, PyArrow, scikit-learn, statsmodels, reportlab)
- `pip install -r requirements-dev.txt` para correr la suite de pruebas (`pytest tests/`)
- `pip install -r requirements-scraping.txt` únicamente para ejecutar localmente la actualización de datos (Selenium + Chrome)

## Alcance y uso responsable

- Los valores monetarios provienen de la fuente en miles de USD; la interfaz los convierte a millones cuando corresponde.
- Los indicadores CAMEL se almacenan como proporciones y se muestran como porcentajes.
- PyG contiene valores acumulados oficiales, valores mensuales desacumulados y sumas móviles de 12 meses.
- El dashboard es una herramienta analítica; no sustituye estados financieros auditados ni pronunciamientos regulatorios.
- Los datos oficiales conservan sus términos y atribución de origen.

## Licencia

Este proyecto utiliza datos públicos de la Superintendencia de Bancos del Ecuador.
