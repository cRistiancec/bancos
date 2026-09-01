# Guía Rápida — Sistema Financiero Privado

Esta guía cubre cinco tareas: preparar el entorno, ejecutar la plataforma,
validar los datos, actualizar los datos localmente y disparar la
actualización en GitHub Actions.

## 1. Preparar el entorno

Se recomienda Python 3.11 (la misma versión usada en GitHub Actions);
probado también en 3.14.

```bash
git clone <url-del-repositorio>
cd bancos
python -m venv .venv
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source .venv/bin/activate
```

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Ejecutar la plataforma

```bash
streamlit run app.py
```

Se abre automáticamente en `http://localhost:8501`. Para un puerto
específico: `streamlit run app.py --server.port 8502`.

Comprobación mínima:

- Resumen Ejecutivo muestra el mismo mes que `master_data/metadata.json`.
- Panorama Bancario carga todas las entidades del último corte.
- Balance General, Pérdidas y Ganancias e Indicadores CAMEL abren sin excepción.

### Navegación

El sidebar agrupa 23 páginas en 7 secciones: **General**, **Monitoreo
Prudencial**, **Riesgos**, **Estados Financieros**, **Análisis Comparativo**,
**Analítica Avanzada** y **Calidad y Reportes**. La página de inicio
(Resumen Ejecutivo) resume el estado del sistema y da accesos rápidos a las
demás. Ver `docs/ManualUsuario.md` para el detalle de cada módulo.

## 3. Ejecutar pruebas y puerta de datos

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -v
python scripts/validar_actualizacion.py
```

Una validación correcta termina con `VALIDACION MENSUAL OK` y resume filas,
bancos y fecha máxima de los tres datasets.

## 4. Actualizar datos localmente

Requisitos adicionales:

- Google Chrome estable;
- conexión al portal de la Superintendencia;
- espacio temporal suficiente para ZIP, XLSX y respaldo de Parquet.

```bash
python -m pip install -r requirements-scraping.txt
python scripts/actualizar_datos.py
```

Interpretación del resultado:

- `0`: actualización correcta o datos ya completos;
- `2`: la fuente todavía no publicó el mes objetivo; no es un error;
- otro código: fallo real; el orquestador restaura los datos maestros anteriores.

No ejecute los procesadores (`procesar_balance.py`, etc.) por separado salvo
diagnóstico. El orquestador agrega respaldo, validación y rollback.

## 5. Ejecutar la actualización en GitHub Actions

1. Abrir el workflow **Actualizar Datos Bancarios** en la pestaña Actions del repositorio.
2. Elegir **Run workflow**.
3. Confirmar la rama por defecto.
4. Esperar el resultado del job `actualizar-datos`.

Desde GitHub CLI (ajustar `--repo` al fork correspondiente):

```bash
gh workflow run actualizar-datos.yml --repo <owner>/bancos --ref main
gh run list --repo <owner>/bancos --workflow actualizar-datos.yml --limit 3
```

## Casos de Uso Comunes

### Ver el tamaño del sistema bancario actual
1. Ve a **Panorama Bancario**.
2. Selecciona el último mes disponible en el sidebar.
3. Observa los KPIs en la parte superior.

### Comparar el crecimiento de dos bancos
1. Ve a **Estados Financieros → Balance General → Evolución Comparativa**.
2. Selecciona la cuenta (p. ej. "1 - Activo").
3. Elige los bancos en el selector.
4. Cambia a modo "Indexado (Base 100)" para comparar crecimiento relativo.

### Analizar la morosidad de un banco en el tiempo
1. Ve a **Riesgos → Riesgo de Crédito**.
2. Elige el segmento de cartera.
3. En el panel de Morosidad, pestaña "Evolución", selecciona el banco.

### Ver qué bancos están en alerta ahora mismo
1. Ve a **Monitoreo Prudencial → Alertas Tempranas**.
2. Revisa la lista filtrable por banco/severidad.

### Exportar datos para análisis externo
1. Ve a **Calidad y Reportes → Reportes**.
2. Elige el dataset, filtra por banco/fecha si quieres.
3. Descarga en CSV, Excel o PDF.

## Consejos de Uso

- El primer acceso a cada dataset puede tardar unos segundos (se cachea con
  `st.cache_data`); las siguientes cargas son instantáneas mientras no
  cambien los archivos Parquet.
- Si actualizaste `master_data/*.parquet` manualmente, usa **Configuración →
  Limpiar caché de datos** para forzar la recarga.
- **Hover** sobre los gráficos para ver valores exactos; **click y arrastra**
  para hacer zoom; **doble click** para resetear.

## Solución de Problemas

### La plataforma no inicia

```bash
python -m streamlit --version
python -m pip install -r requirements.txt
```

Confirme que está ejecutando `app.py` (no `Inicio.py`, que ya no existe en
esta versión del proyecto).

### Falta un Parquet o `metadata.json`

Debe existir:

```text
master_data/balance.parquet
master_data/pyg.parquet
master_data/camel.parquet
master_data/metadata.json
master_data/update_status.json
```

Restaure una versión conocida; no genere solo uno de los archivos para
publicarlo aisladamente. Consulte
[docs/OPERACION_Y_RECUPERACION.md](docs/OPERACION_Y_RECUPERACION.md).

### Streamlit Cloud muestra una versión anterior

1. Confirme que el commit está en la rama que sirve Streamlit Cloud.
2. Confirme que Streamlit Cloud apunta al repositorio, rama y archivo
   (`app.py`) correctos en la configuración de despliegue.
3. Espere el redespliegue o use **Reboot app** en Streamlit Cloud.
4. Recargue la aplicación y compare el mes visible con `metadata.json`.

### Módulos "en preparación"

Algunas pestañas (Riesgo de Mercado, Riesgo Operacional, red de
interconexión interbancaria, LCR/NSFR) todavía no tienen fuente de datos
real conectada — es intencional, no un error. Ver
`docs/AUDITORIA_COMPLETA.md` sección 6.

## Siguiente lectura

- [README principal](README.md)
- [Automatización mensual](docs/AUTOMATIZACION.md)
- [Diccionario de datos](docs/DICCIONARIO_DATOS.md)
- [Arquitectura](docs/ARQUITECTURA.md)
- [Manual de usuario](docs/ManualUsuario.md)

---

**Sistema Financiero Privado** — Eco. Cristian Coronel Quezada, MBA — Coordinación Técnica de Riesgos y Estudios, COSEDE
