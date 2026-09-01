# Pipeline ejecutable

Este documento es la versión breve. La arquitectura completa está en [ARQUITECTURA.md](ARQUITECTURA.md) y la operación mensual en [AUTOMATIZACION.md](AUTOMATIZACION.md).

## Ruta recomendada

```bash
python -m pip install -r requirements-scraping.txt
python scripts/actualizar_datos.py
```

El orquestador incluye descarga, respaldo, los tres procesadores, validación y rollback.

## Ruta de diagnóstico

Solo para aislar un problema, no para publicar parcialmente:

```bash
python scripts/descargar.py
python scripts/procesar_balance.py
python scripts/procesar_pyg.py
python scripts/procesar_camel.py
python scripts/validar_actualizacion.py
```

Dependencias entre productos:

```text
XLSX/BAL   ─► balance.parquet ─┐
XLSX/PYG   ─► pyg.parquet     ─┼─► validar ─► publicar ─► Streamlit
XLSX/CAMEL ─► camel.parquet   ─┘
```

## Contrato de publicación

- Un corte mensual se acepta solo si los tres datasets llegan a la fecha objetivo.
- La cobertura esperada es 23 bancos en el último mes.
- Código `2` significa fuente sin avance y debe terminar sin commit.
- Cualquier otro fallo conserva o restaura los artefactos anteriores.
- La publicación incluye Parquet, `metadata.json` y `update_status.json`.
