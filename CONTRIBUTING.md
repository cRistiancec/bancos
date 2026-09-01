# Contribuir al Sistema Financiero Privado

Gracias por mejorar el proyecto. Los cambios deben preservar la reproducibilidad del pipeline y la cobertura bancaria publicada.

## Preparación

```bash
git clone <url-del-repositorio>
cd bancos
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-scraping.txt
```

Use una rama corta y descriptiva creada desde `main`.

## Tipos de cambios

### Interfaz

- Mantenga `app.py` como entrypoint (`Inicio.py` no existe en esta versión).
- Reutilice funciones de `services/`, `analytics/`, `charts/`, `components/` y mapeos de `config/indicator_mapping.py`.
- Obtenga bancos y fechas desde los datos; no escriba cifras mensuales a mano.
- Verifique la página afectada con datos reales y compruebe la consola del navegador.

### Pipeline o datos

- No publique un único Parquet sin los otros artefactos del mismo corte.
- Conserve la semántica de exit code `2` como no-op.
- Use escritura temporal y reemplazo atómico para artefactos.
- Mantenga el rollback del orquestador y la puerta de `validar_actualizacion.py`.
- Si cambia el número de bancos esperado, documente la evidencia oficial y actualice pruebas y configuración en el mismo cambio.

### Documentación

- Actualice primero los documentos autoritativos listados en `docs/README.md`.
- Evite cifras sin fecha de corte.
- Compruebe enlaces relativos y comandos desde la raíz del repositorio.

## Validación obligatoria

```bash
python -m pytest tests/ -v
python scripts/validar_actualizacion.py
python -m py_compile app.py dashboard_metadata.py scripts/*.py
```

En Windows, si el shell no expande `scripts/*.py`, use:

```powershell
Get-ChildItem scripts\*.py | ForEach-Object { python -m py_compile $_.FullName }
```

Para cambios visuales:

```bash
python -m streamlit run app.py
```

Revise Resumen Ejecutivo, Panorama Bancario, Balance General, Pérdidas y Ganancias e Indicadores CAMEL como mínimo.

## Estilo

- Python legible y compatible con 3.11.
- Variables de negocio en español son válidas; nombres técnicos pueden estar en inglés.
- Use `observed=True` en `groupby` sobre columnas categóricas.
- Evite convertir columnas categóricas masivas a `str` de forma indiscriminada.
- Añada una prueba de regresión para cada fallo corregido.
- Mantenga mensajes de commit breves y específicos.

## Pull request

Incluya:

- problema y causa;
- archivos y comportamiento modificados;
- impacto en datos o interfaz;
- comandos de validación ejecutados;
- captura para cambios visuales;
- plan de rollback si toca `master_data/` o automatización.

No incluya ZIP, Excel, respaldos temporales ni carpetas locales ajenas al cambio.

## Reportar problemas

Un issue útil contiene:

- URL o módulo afectado;
- banco, indicador y mes;
- comportamiento observado y esperado;
- pasos de reproducción;
- enlace al run de Actions si es un incidente de actualización;
- sistema operativo y versiones de Python/Streamlit para errores locales.

## Licencia y datos

Al contribuir, acepta que su código se distribuya bajo la [licencia MIT](LICENSE). Los datos provienen de la Superintendencia de Bancos del Ecuador y deben conservar atribución y condiciones de origen.
