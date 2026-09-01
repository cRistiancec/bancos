# Guía de Despliegue — Sistema Financiero Privado

## Requisitos

- Python 3.10+ (probado con 3.11 y 3.14)
- ~40 MB de espacio para `master_data/*.parquet` + dependencias
- Sin bases de datos externas ni servicios adicionales — todo corre desde
  los archivos Parquet locales en `master_data/`

## Opción 1 — Streamlit Community Cloud

1. Sube el repositorio a GitHub (asegúrate de que `master_data/*.parquet`
   esté versionado — no está en `.gitignore`).
2. En [share.streamlit.io](https://share.streamlit.io), conecta el repositorio.
3. Archivo principal: `app.py`.
4. No requiere `secrets.toml` para funcionar (todos los módulos actuales
   usan solo los datos locales). Si más adelante conectas un LLM real para
   el Asistente de Riesgos, configura los secretos vía el panel de la app
   siguiendo la plantilla en `.streamlit/secrets.toml.example`.

## Opción 2 — Servidor propio / VM

```bash
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Recomendado correr detrás de un reverse proxy (nginx/Caddy) con TLS si se
expone fuera de una red interna.

## Opción 3 — Docker

```bash
docker build -t sistema-financiero-privado .
docker run -p 8501:8501 sistema-financiero-privado
```

El `Dockerfile` copia todo el repositorio (incluye `master_data/`), instala
`requirements.txt` y expone el puerto 8501. Healthcheck incluido contra
`/_stcore/health`.

## Actualización de datos en producción

Los archivos `master_data/*.parquet` se regeneran corriendo el pipeline
(`scripts/descargar.py` → `scripts/descomprimir_zips.py` →
`scripts/procesar_{balance,pyg,camel}.py`) y reemplazando los archivos.
Después de actualizar, usa el botón "Limpiar caché de datos" en
**Configuración** (o reinicia el proceso de Streamlit) para forzar la
recarga — los datos se cachean con `st.cache_data(ttl=3600)`.

## Variables de entorno / secretos

Ninguno es requerido hoy. `.streamlit/secrets.toml.example` documenta el
único secreto previsto a futuro (API key de un LLM para el Asistente de
Riesgos, ver `services/assistant_engine.py::ProveedorLLM`) — no crear
`secrets.toml` hasta que se implemente esa integración.

## Rendimiento esperado

- Primera carga de cada dataset: ~1-3s (lectura de Parquet + limpieza),
  cacheada por 1 hora.
- La mayoría de páginas renderizan en <2s tras el primer acceso.
- `Riesgo Sistémico` (evolución de 36 meses) y páginas de `Modelos
  Predictivos` son las más pesadas computacionalmente; están cacheadas con
  `@st.cache_data` para que el costo solo se pague una vez por combinación
  de filtros.
