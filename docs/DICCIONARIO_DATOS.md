# Diccionario de datos

## Convenciones generales

- **Frecuencia:** mensual, con fecha de cierre al último día del mes.
- **Identificador de entidad:** `banco`, nombre normalizado desde la carpeta del boletín.
- **Moneda:** los importes de Balance y PyG se conservan en miles de USD, tal como se usan en la fuente; la UI divide por 1.000 para mostrar millones.
- **Porcentajes:** CAMEL almacena proporciones decimales; la UI multiplica por 100.
- **Texto repetitivo:** banco, código, cuenta, indicador y categoría se almacenan como diccionarios/categorías en Parquet para reducir memoria.

## Fotografía validada

| Archivo | Filas | Tamaño | Fecha mínima | Fecha máxima | Bancos último mes |
|---|---:|---:|---:|---:|---:|
| `balance.parquet` | 8.152.043 | 18,31 MB | 2003-01-31 | 2026-06-30 | 23 |
| `pyg.parquet` | 755.584 | 9,41 MB | 2003-01-31 | 2026-06-30 | 23 |
| `camel.parquet` | 230.102 | 1,52 MB | 2003-01-31 | 2026-06-30 | 23 |

Fotografía verificada el 18 de julio de 2026. Para el estado vigente, consultar `master_data/metadata.json` y ejecutar `scripts/validar_actualizacion.py`.

## `balance.parquet`

Fuente: hoja `BAL` de cada XLSX.

Clave de validación: `banco + fecha + codigo + cuenta`.

| Columna | Tipo lógico | Nulos | Descripción |
|---|---|---|---|
| `banco` | categoría/string | No en clave | Institución financiera |
| `fecha` | timestamp mensual | No | Fecha de corte |
| `codigo` | categoría/string | No en clave | Código del Catálogo Único de Cuentas |
| `cuenta` | categoría/string | No en clave | Nombre de la cuenta |
| `valor` | float64 | Puede existir en fuente; loader filtra clave/valor inválido | Importe en miles de USD |
| `nivel` | int8 | No | Nivel jerárquico derivado del código |

Semántica de `nivel`:

| Nivel | Regla |
|---:|---|
| `0` | Código vacío o no numérico |
| `1` | Hasta 1 dígito |
| `2` | Hasta 2 dígitos |
| `3` | Hasta 4 dígitos |
| `4` | Hasta 6 dígitos |
| `5` | Más de 6 dígitos |

Códigos usados con frecuencia por la interfaz: `1` activos, `14` cartera, `21` obligaciones con el público y `3` patrimonio.

## `pyg.parquet`

Fuente: hoja `PYG`.

Clave de validación: `banco + fecha + codigo`.

| Columna | Tipo lógico | Descripción |
|---|---|---|
| `banco` | categoría/string | Institución financiera |
| `fecha` | timestamp mensual | Fecha de corte |
| `codigo` | categoría/string | Código contable o código resumen |
| `cuenta` | categoría/string | Nombre de la cuenta o margen |
| `valor_acumulado` | float64 | Valor acumulado oficial dentro del año, en miles de USD |
| `valor_mes` | float64 | Enero: acumulado; febrero-diciembre: acumulado actual menos mes anterior |
| `valor_12m` | float64 | Suma móvil de los últimos 12 valores mensuales |

Los primeros once meses de una serie pueden no tener `valor_12m`. La UI filtra esos nulos al usar comparaciones de 12 meses.

Códigos resumen:

| Código | Indicador |
|---|---|
| `MNI` | Margen Neto de Intereses |
| `MBF` | Margen Bruto Financiero |
| `MNF` | Margen Neto Financiero |
| `MDI` | Margen de Intermediación |
| `MOP` | Margen Operacional |
| `GAI` | Ganancia antes de impuestos |
| `GDE` | Ganancia o pérdida del ejercicio |

El archivo también conserva cuentas contables de ingresos y gastos, no solo estos siete resúmenes.

## `camel.parquet`

Fuente: hoja `CAMEL`.

Clave de validación: `banco + fecha + codigo`.

| Columna | Tipo lógico | Descripción |
|---|---|---|
| `banco` | categoría/string | Institución financiera |
| `fecha` | timestamp mensual | Fecha de corte |
| `codigo` | categoría/string | Código corto del indicador |
| `indicador` | categoría/string | Etiqueta descriptiva |
| `valor` | float64 | Proporción decimal; `0.10` equivale a `10%` |
| `categoria` | categoría/string | Dimensión o familia analítica |

Familias principales:

| Familia | Ejemplos |
|---|---|
| Capital | `SOL` |
| Calidad de activos | `MOR_*`, `COB_*`, `AIN`, `CAR_ACT`, `INV_ACT` |
| Composición de cartera | `PART_*` |
| Management | `AP_PC`, `GO_MNF`, `GO_ACT`, `GP_ACT` |
| Earnings | `ROA`, `ROE`, `DEP_BRECHA`, `DEP_SPREAD` |
| Liquidity | `LIQ` |

El corte actual contiene 39 indicadores. El nombre y agrupación visible se gobiernan también desde `config/indicator_mapping.py` y `pages/4_CAMEL.py`.

## `metadata.json`

Lo genera el procesador de Balance y lo usa la portada.

Campos actuales:

| Campo | Descripción |
|---|---|
| `ultima_actualizacion` | Timestamp de generación |
| `bancos_procesados` | Lista de entidades procesadas |
| `bancos_error` | Entidades fallidas; debe estar vacío para publicar |
| `total_bancos` | Cantidad procesada |
| `total_registros` | Filas de Balance |
| `fecha_min`, `fecha_max` | Rango temporal de Balance |
| `hojas_procesadas` | Hojas declaradas por el procesador |

`metadata.json` no sustituye la inspección de los Parquet: la puerta de calidad contrasta ambos.

## `update_status.json`

Registro operativo del último proceso:

| Campo | Descripción |
|---|---|
| `fecha_ejecucion` | Timestamp del intento exitoso |
| `periodo_objetivo` | Mes que se intentó procesar |
| `exitoso` | Resultado del ETL |
| `pasos_completados` | Etapas completadas |
| `ultimo_periodo_descargado` | Período derivado de la fecha máxima real |

En un no-op por fuente sin avance pueden aparecer `ultimo_intento`, `ultimo_intento_periodo`, `ultimo_intento_exitoso` y `sin_datos_nuevos`.

El estado JSON es informativo. La decisión de actualización se basa en los Parquet reales.

## Invariantes de calidad

Una publicación válida cumple:

- tres Parquet legibles y no vacíos;
- esquema completo;
- continuidad mensual global;
- fecha máxima exacta en los tres;
- 23 bancos en el último mes;
- claves sin duplicados;
- `metadata.fecha_max` coherente;
- `bancos_error` vacío;
- no pérdida de historia respecto de la publicación anterior.

## Lectura recomendada

```python
import pandas as pd

balance = pd.read_parquet(
    "master_data/balance.parquet",
    columns=["banco", "fecha", "codigo", "valor"],
)
```

Seleccione solo las columnas necesarias: Balance supera ocho millones de filas.
