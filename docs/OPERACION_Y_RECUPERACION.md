# Operación y recuperación

## Objetivo del runbook

Mantener una publicación mensual verificable y recuperar el último estado bueno sin perder historia ni mezclar cortes.

## Comprobación diaria o posterior a un run

1. Abrir el run de **Actualizar Datos Bancarios**.
2. Confirmar que usa `main` y el commit esperado.
3. Revisar el período objetivo.
4. Distinguir no-op de actualización real.
5. Si hubo commit, comprobar `metadata.json` y los tres Parquet.
6. Abrir Streamlit y verificar Resumen Ejecutivo, Panorama Bancario, Balance General, Pérdidas y Ganancias e Indicadores CAMEL.

Comandos útiles:

```bash
gh run list --repo cRistiancec/bancos --workflow actualizar-datos.yml --limit 5
git status --short --branch
python scripts/validar_actualizacion.py
```

## Operación mensual normal

### Caso A: la publicación ya está completa

La prevalidación de Actions pasa y omite descarga, ETL y commit. No hay nada que corregir.

### Caso B: la fuente todavía no avanzó

El orquestador devuelve `2`. El workflow termina correctamente sin commit y reintenta en la siguiente fecha programada.

### Caso C: existe un mes nuevo

El flujo descarga 23 entidades, procesa los tres productos, valida y crea un commit automático. Streamlit redespliega desde `main`.

## Matriz de incidentes

| Síntoma | Causa probable | Acción segura |
|---|---|---|
| Portal no carga o Selenium agota espera | Caída o cambio del portal | Reintentar; si persiste, inspeccionar selectores de `descargar.py` |
| Código `2` | Fuente interna aún en el mes anterior | Esperar; no modificar estado ni forzar commit |
| Menos/más de 23 ZIP o XLSX | Fuente parcial o cambio institucional | No publicar; contrastar portal y revisar configuración |
| BAL/PYG/CAMEL con fechas distintas | Boletín inconsistente | No publicar; conservar corte anterior |
| Un banco queda rezagado | Fuente o procesador incompleto | Revisar entidad y hoja; la puerta debe fallar |
| Duplicados de clave | Error de extracción/consolidación | Corregir procesador; no eliminar a ciegas después del ETL |
| PyG o CAMEL pierde meses | Reemplazo histórico incorrecto | Restaurar y revisar lógica de solapamiento |
| `git push` denegado en Actions | Falta `contents: write` o protección de rama | Revisar permisos y reglas de `main` |
| GitHub está correcto pero Streamlit está viejo | Redespliegue pendiente o app mal configurada | Verificar repo/rama/entrypoint y hacer Reboot app |
| Primera visita tarda | App dormida en Community Cloud | Despertar la app; no es pérdida de datos |

## Recuperación automática local

Antes del ETL, el orquestador copia a un temporal:

```text
balance.parquet
pyg.parquet
camel.parquet
metadata.json
update_status.json
```

Si falla Balance, PyG, CAMEL, la existencia de artefactos o la validación, restaura esos archivos. El respaldo es temporal y vive solo durante el proceso.

## Revertir una publicación incorrecta en GitHub

Preferir un revert auditable:

```bash
git pull --ff-only origin main
git log --oneline --max-count=10
git revert COMMIT_INCORRECTO
git push origin main
```

Después:

```bash
python scripts/validar_actualizacion.py
```

La validación por defecto usa el mes objetivo actual. Si se revirtió deliberadamente al corte anterior porque la fuente nueva era inválida, documente el incidente y valide con una fecha explícita:

```bash
python scripts/validar_actualizacion.py --fecha-esperada YYYY-MM-DD
```

Luego confirme el mes visible en Streamlit.

## Restaurar artefactos desde un commit conocido

Úselo cuando el commit incorrecto mezcló archivos o el revert automático no deja la unidad de publicación coherente:

```bash
git restore --source=COMMIT_BUENO -- \
  master_data/balance.parquet \
  master_data/pyg.parquet \
  master_data/camel.parquet \
  master_data/metadata.json \
  master_data/update_status.json
```

Valide con la fecha del commit bueno, cree un commit de recuperación y haga push. Nunca restaure solo un Parquet.

## Recuperar una ejecución local interrumpida

1. No publique archivos presentes hasta comprobarlos.
2. Revise `git status --short` y `master_data/update_status.json`.
3. Ejecute la puerta con la fecha que realmente debería existir.
4. Si falla, restaure los cinco artefactos desde `HEAD`:

```bash
git restore -- \
  master_data/balance.parquet \
  master_data/pyg.parquet \
  master_data/camel.parquet \
  master_data/metadata.json \
  master_data/update_status.json
```

5. Elimine manualmente solo la carpeta temporal específica del período si quedó fuera del control del orquestador.
6. Reintente mediante `scripts/actualizar_datos.py`.

## Cambio en el número de bancos

La barrera de 23 no debe relajarse automáticamente. Ante una nueva entidad, cierre o fusión:

1. Verificar el cambio en la fuente oficial.
2. Comprobar cómo aparece en BAL, PYG y CAMEL.
3. Evaluar continuidad del nombre y posible serie histórica.
4. Actualizar `NUMERO_ESPERADO_BANCOS`, pruebas y documentación en el mismo commit.
5. Ejecutar una actualización completa y revisar los cuatro módulos.

## Transición de año

En enero el objetivo es diciembre del año anterior y la carpeta del portal cambia de año. Confirmar:

- `ANO_BUSCAR` calculado correctamente;
- carpeta `Año YYYY` disponible;
- nombres de salida con el año anterior;
- fecha interna 31 de diciembre;
- conservación de toda la historia.

## Cierre del incidente

Documentar:

- run y commit afectados;
- período esperado y observado;
- entidades o datasets involucrados;
- causa raíz;
- comando o commit de recuperación;
- validaciones posteriores;
- estado final de Streamlit.
