# Contexto Persistente - Sistema Financiero Privado

Este archivo es la fuente de verdad para recuperar contexto cuando el asistente pierda memoria.
Si estas leyendo esto, **DEBES actualizar este archivo** con cualquier cambio relevante antes de terminar la tarea.

## Instrucciones para el asistente
- Siempre leer `docs/CONTEXTO.md` al inicio de una nueva sesion.
- Actualizar este archivo al finalizar cambios.
- Si se detectan errores cometidos previamente, registrarlos aqui.

## Resumen del proyecto (actual)
- App Streamlit institucional ("Sistema Financiero Privado", COSEDE) para
  analisis del sistema bancario ecuatoriano, evolucion de "Radar Bancario
  Ecuador" (autor original: Juan Pablo Erraez T., `jp1309/bancos`).
- Entry point: `app.py` (`st.navigation`). **`Inicio.py` NO existe en esta
  version** — fue reemplazado en la refactorizacion institucional de Fase 1
  (2026-07-27) y eliminado definitivamente al integrar esta linea con la
  automatizacion de datos del repositorio original.
- 23 paginas activas en `pages/*.py` (sin prefijos numericos), registradas
  en `config/nav_registry.py` y agrupadas en 7 secciones de sidebar. Ver
  `docs/ARQUITECTURA.md` para el listado completo y la estructura de
  capas (`ui/`, `components/`, `charts/`, `analytics/`, `models/`,
  `services/`, `config/`).
- No existe `archived_pages/`; el modulo de Calidad de Datos esta activo en
  `pages/calidad_datos.py`.

## Pipeline de datos
1. `scripts/descargar.py` + `scripts/fuente_bancos.py`: descarga y valida ZIPs/XLSX.
2. `scripts/procesar_balance.py` -> `master_data/balance.parquet`.
3. `scripts/procesar_pyg.py` -> `master_data/pyg.parquet`.
4. `scripts/procesar_camel.py` -> `master_data/camel.parquet`.
5. `scripts/validar_actualizacion.py`: puerta de calidad antes de publicar.
6. Orquestador transaccional: `scripts/actualizar_datos.py` (respaldo,
   ETL, validacion, commit o rollback — invocado por
   `.github/workflows/actualizar-datos.yml`, reintentos dias 6-20 de cada
   mes).

## Datos principales
- `master_data/balance.parquet`
- `master_data/pyg.parquet`
- `master_data/camel.parquet`
- `master_data/metadata.json`
- `master_data/update_status.json`

Estos cinco artefactos son una unidad de publicacion — nunca se
commitea/actualiza uno solo de forma aislada.

## Documentacion clave
- `README.md`
- `RESUMEN_PROYECTO.md` (documento historico, congelado — no modificar)
- `docs/ARQUITECTURA.md`
- `docs/AUDITORIA_COMPLETA.md`
- `docs/AUTOMATIZACION.md`
- `docs/OPERACION_Y_RECUPERACION.md`
- `docs/DICCIONARIO_DATOS.md`
- `docs/ManualTecnico.md` / `docs/ManualUsuario.md`
- `CHANGELOG.md` (historial completo, incluida la integracion con la
  automatizacion del repositorio original)

## Errores previos a evitar
- Asumir que el entrypoint es `Inicio.py` (es `app.py`; `Inicio.py` fue
  eliminado).
- Referenciar `pages/1_Panorama.py`, `pages/2_Balance_General.py`,
  `pages/3_Perdidas_Ganancias.py` o `pages/4_CAMEL.py` (numerados) como
  activos — fueron reemplazados por los archivos sin prefijo en `pages/`.
- Referenciar `archived_pages/0_Calidad_old.py` como el modulo de Calidad
  vigente — fue eliminado; el modulo activo es `pages/calidad_datos.py`.
- Referenciar `utils/data_loader.py` como el loader activo — fue
  renombrado/superado por `services/data_service.py`.
- Referenciar `crear_master.py` como activo (fue eliminado hace tiempo).
- Listar `indicadores.parquet`, `cartera.parquet`, `fuentes_usos.parquet`
  como salidas actuales (no se procesan; solo BAL/PYG/CAMEL).
- Escribir cifras de cobertura (num. de bancos, periodo, meses) a mano en
  código o documentación de estado — deben leerse de
  `master_data/metadata.json` en tiempo de ejecución.

## Ultima actualizacion
- Fecha: 2026-08-31
- Motivo: Integración de la línea de refactor institucional (Fases 1-3,
  `app.py` + arquitectura por capas) con la línea de automatización de
  datos del repositorio original (`jp1309/bancos` rama `main`: GitHub
  Actions, `scripts/actualizar_datos.py`, `requirements.txt` fijado).
  Ver `CHANGELOG.md` sección `[Sin publicar]` para el detalle completo.
