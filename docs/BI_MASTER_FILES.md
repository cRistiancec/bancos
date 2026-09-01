# Master Files para Business Intelligence (Estado Actual)

Este documento describe los archivos Parquet **actualmente** generados por el proyecto.

---

## Archivos Generados (actual)

Ubicacion:
```
master_data/
????????? balance.parquet   # Balance General
????????? pyg.parquet       # Perdidas y Ganancias
????????? camel.parquet     # Indicadores CAMEL
????????? metadata.json     # Info de ultima actualizacion
????????? update_status.json # Estado del proceso
```

### 1. balance.parquet
**Fuente**: Hoja BAL
**Columnas**:
- `banco`
- `fecha`
- `codigo`
- `cuenta`
- `valor`
- `nivel`

### 2. pyg.parquet
**Fuente**: Hoja PYG
**Columnas**:
- `banco`
- `fecha`
- `codigo`
- `cuenta`
- `valor_acumulado`
- `valor_mes`
- `valor_12m`

### 3. camel.parquet
**Fuente**: Hoja CAMEL
**Columnas**:
- `banco`
- `fecha`
- `codigo`
- `indicador`
- `valor`
- `categoria`

---

## Proceso de Generacion

```
python scripts/descargar.py
python scripts/procesar_balance.py
python scripts/procesar_pyg.py
python scripts/procesar_camel.py
```

O bien:
```
python scripts/actualizar_datos.py
```

---

## Nota sobre archivos historicos

En versiones anteriores se generaban otros master files (`indicadores.parquet`, `cartera.parquet`, `fuentes_usos.parquet`).
Actualmente **no** se generan y no forman parte del flujo oficial del dashboard.
