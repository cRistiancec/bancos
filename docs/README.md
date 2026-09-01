# Documentación técnica

Este directorio contiene la documentación del Sistema Financiero Privado (evolución institucional del Radar Bancario Ecuador). Los documentos de la primera tabla son las fuentes de verdad operativas; si una nota histórica contradice estos archivos o el código, prevalecen el código vigente y esta documentación autoritativa.

## Documentos autoritativos

| Documento | Audiencia | Contenido |
|---|---|---|
| [AUTOMATIZACION.md](AUTOMATIZACION.md) | Operación/DevOps | GitHub Actions, calendario, flujo mensual y exit codes |
| [OPERACION_Y_RECUPERACION.md](OPERACION_Y_RECUPERACION.md) | Operación | Runbook, incidentes, rollback y recuperación |
| [DICCIONARIO_DATOS.md](DICCIONARIO_DATOS.md) | Datos/analítica | Parquet, columnas, claves, unidades y metadata |
| [ARQUITECTURA.md](ARQUITECTURA.md) | Desarrollo | Pipeline de datos + capas de la aplicación Streamlit |
| [PIPELINE.md](PIPELINE.md) | Desarrollo/operación | Secuencia ejecutable resumida del pipeline |
| [AUDITORIA_COMPLETA.md](AUDITORIA_COMPLETA.md) | Desarrollo | Auditoría previa al refactor institucional, matriz de factibilidad de datos |
| [ManualTecnico.md](ManualTecnico.md) | Analítica/riesgos | Metodologías, umbrales, qué no está implementado y por qué |
| [ManualUsuario.md](ManualUsuario.md) | Usuarios finales | Manual funcional por módulo |
| [DESPLIEGUE.md](DESPLIEGUE.md) | Operación/DevOps | Streamlit Cloud, servidor propio, Docker |
| [CONTEXTO.md](CONTEXTO.md) | Asistentes/contribuyentes | Ancla anti-alucinación: entrypoint, estructura y errores previos a evitar — debe actualizarse en cada cambio relevante |

Documentos en la raíz:

| Documento | Contenido |
|---|---|
| [../README.md](../README.md) | Presentación, estado, instalación y mapa de documentación |
| [../QUICKSTART.md](../QUICKSTART.md) | Puesta en marcha local y ejecución manual |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Reglas para cambios, pruebas y PR |
| [../RESUMEN_PROYECTO.md](../RESUMEN_PROYECTO.md) | Ficha ejecutiva del proyecto |
| [../LICENSE](../LICENSE) | Licencia MIT del software y nota de fuente de datos |

## Fuente de verdad por tema

| Pregunta | Fuente |
|---|---|
| ¿Cuál es el último mes publicado? | `master_data/metadata.json` y los tres Parquet |
| ¿Cuántos bancos debe tener el corte? | `scripts/config.py` (`NUMERO_ESPERADO_BANCOS`) |
| ¿Qué impide una publicación incompleta? | `scripts/validar_actualizacion.py` |
| ¿Cuándo corre el job? | `.github/workflows/actualizar-datos.yml` |
| ¿Qué consume Streamlit? | `services/data_service.py` y `master_data/` |
| ¿Qué códigos usa la UI? | `config/indicator_mapping.py` |
| ¿Qué ocurrió en el último intento? | `master_data/update_status.json` y logs de Actions |

## Notas de diseño e historia

Los siguientes documentos se conservan como referencia especializada o histórica. Pueden contener capturas, tamaños, versiones o diseños anteriores y no deben usarse como runbook de producción:

- `BI_MASTER_FILES.md`
- `ESTRUCTURA_EXCEL.md`
- `ESTRUCTURA_FINAL.md`
- `GUIA_RAPIDA.md`
- `INSTRUCCIONES_DESCARGA.md`
- `MODULO_PANORAMA.md`
- `MODULO_RENTABILIDAD.md`
- `MODULO_SERIES_TEMPORALES.md`
- `PROCESAMIENTO_PYG.md`
- `SCRIPTS_PROCESAMIENTO.md`
- `VISUALIZACION_CRECIMIENTO.md`
- `VISUALIZACIONES.md`

## Mantenimiento documental

Cuando cambie el pipeline:

1. Actualizar `AUTOMATIZACION.md` y `ARQUITECTURA.md`.
2. Actualizar el diccionario si cambia un esquema o unidad.
3. Añadir el procedimiento de recuperación correspondiente.
4. Verificar todos los enlaces Markdown.
5. Evitar cifras sin fecha de corte; preferir metadata o tablas marcadas como fotografía.
