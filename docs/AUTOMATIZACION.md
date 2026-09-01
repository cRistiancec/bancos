# Automatización mensual de datos

## Objetivo

Publicar un nuevo corte mensual solo cuando los 23 boletines por entidad contienen internamente el mes objetivo y los tres datasets resultantes superan la puerta de calidad.

La automatización está definida en `.github/workflows/actualizar-datos.yml` y opera sobre la rama `main`.

## Calendario

GitHub Actions intenta la actualización los días 6, 8, 10, 12, 14, 16, 18 y 20 de cada mes a las 13:00 UTC (08:00 de Ecuador continental, UTC-5).

El período objetivo se calcula en tiempo de ejecución como el mes calendario anterior. En enero, el cálculo cambia automáticamente al diciembre del año anterior.

Los reintentos existen porque la publicación oficial no ocurre siempre el mismo día. Un intento sin avance es un no-op normal, no un incidente.

## Flujo del workflow

```text
schedule / workflow_dispatch
        │
        ▼
checkout main + Python 3.11 + Chrome + dependencias
        │
        ▼
validar los tres Parquet contra el mes objetivo
        │
        ├── completos ─► resumen y fin
        │
        ▼
scripts/actualizar_datos.py
        │
        ├── código 2 ─► fuente sin avance, fin sin commit
        ├── error ────► job fallido, datos anteriores preservados
        ▼
validar_actualizacion.py
        │
        ▼
commit de cinco artefactos + push a main
        │
        ▼
Streamlit detecta el commit y redespliega
```

## Artefactos publicados como una unidad

```text
master_data/balance.parquet
master_data/pyg.parquet
master_data/camel.parquet
master_data/metadata.json
master_data/update_status.json
```

No se debe publicar un subconjunto de estos archivos para un corte nuevo.

## Validación de la fuente

`scripts/descargar.py` y `scripts/fuente_bancos.py` verifican antes de reemplazar la fuente local:

- exactamente 23 descargas;
- cada archivo es un ZIP legible;
- rutas internas seguras, sin extracción fuera del staging;
- exactamente un XLSX por entidad;
- hojas `BAL`, `PYG` y `CAMEL` presentes;
- fecha interna uniforme entre hojas y bancos;
- fecha de corte igual al mes objetivo y posterior al Parquet publicado.

La descarga se realiza en archivos y directorios temporales. La fuente vigente solo se reemplaza después de validar el staging completo.

## Orquestador transaccional

`scripts/actualizar_datos.py`:

1. Comprueba el estado real de los Parquet.
2. Captura el estado anterior de meses y bancos.
3. Descarga y valida la fuente.
4. Respalda los tres Parquet y los dos JSON en un directorio temporal.
5. Ejecuta Balance, PyG y CAMEL.
6. Comprueba que los artefactos existan.
7. Ejecuta la puerta de calidad con el estado anterior.
8. Genera `update_status.json` y limpia temporales.
9. Si algo falla desde el ETL en adelante, restaura los cinco artefactos respaldados.

## Códigos de salida

| Código | Significado | GitHub Actions |
|---:|---|---|
| `0` | Actualización correcta o publicación ya completa | Éxito |
| `2` | Fuente oficial todavía sin el mes objetivo | Éxito sin ETL/commit |
| Otro | Error real de descarga, procesamiento o validación | Falla el job |

El workflow usa `set +e` únicamente alrededor del orquestador para capturar el código `2`; después restablece `set -e`.

## Puerta de publicación

`scripts/validar_actualizacion.py` exige para Balance, PyG y CAMEL:

- Parquet existente, legible y no vacío;
- esquema obligatorio;
- fecha válida y fecha máxima exacta;
- continuidad mensual global;
- 23 bancos únicos y 23 en el último corte;
- cero duplicados en la clave de cada dataset;
- fecha coherente en `metadata.json` y `bancos_error` vacío;
- sin pérdida de meses, bancos o inicio histórico respecto del estado previo.

Solo si esta validación pasa se prepara el commit automático.

## Ejecución manual en GitHub

Interfaz:

1. Abrir el workflow **Actualizar Datos Bancarios** en la pestaña Actions del repositorio.
2. Seleccionar **Run workflow**.
3. Usar la rama `main`.
4. Revisar el resumen y los pasos omitidos o ejecutados.

CLI:

```bash
gh workflow run actualizar-datos.yml --repo cRistiancec/bancos --ref main
gh run list --repo cRistiancec/bancos --workflow actualizar-datos.yml --limit 5
gh run watch RUN_ID --repo cRistiancec/bancos --exit-status
gh run view RUN_ID --repo cRistiancec/bancos --log
```

## Ejecución manual local

```bash
python -m pip install -r requirements-scraping.txt
python scripts/actualizar_datos.py
echo $?
```

En PowerShell, el código se consulta con `$LASTEXITCODE`.

Antes de publicar un resultado local:

```bash
python -m pytest tests/ -v
python scripts/validar_actualizacion.py
git diff --check
```

## Permisos y configuración de producción

- La rama por defecto debe ser `main`; los cron solo se ejecutan desde la rama por defecto.
- El workflow declara `permissions: contents: write` para el commit automático.
- Streamlit Cloud debe apuntar al repositorio de despliegue vigente, rama `main`, archivo `app.py`.
- El workflow tiene timeout de 30 minutos.
- `NUMERO_ESPERADO_BANCOS = 23` es una barrera intencional. Una fusión, cierre o nueva entidad requiere revisión humana antes de cambiarlo.

## Monitoreo

Un run correcto puede terminar de dos formas:

- **rápido/no-op:** la publicación ya está completa o la fuente aún no avanzó;
- **actualización:** descarga, ETL, validación, commit y push.

Revise siempre:

- commit utilizado por el run;
- período objetivo;
- `Necesitaba actualizar` y `Datos nuevos` del resumen;
- fecha y cobertura reportadas por la puerta de calidad;
- existencia del commit automático cuando hubo avance real;
- mes visible en la aplicación después del redespliegue.

Para incidentes y rollback, consulte [OPERACION_Y_RECUPERACION.md](OPERACION_Y_RECUPERACION.md).
