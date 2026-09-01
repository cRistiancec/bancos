# Scripts de Procesamiento de Datos

Documentacion tecnica de los scripts de descarga y procesamiento del sistema bancario ecuatoriano.

---

## Flujo General

```
Portal SBS
   |
   v
scripts/descargar.py
   |
   v
scripts/procesar_balance.py  -> master_data/balance.parquet
scripts/procesar_pyg.py      -> master_data/pyg.parquet
scripts/procesar_camel.py    -> master_data/camel.parquet
```

Opcional:
- `scripts/actualizar_datos.py` orquesta todo el flujo y valida salidas.

---

## descargar.py

### Proposito
Descarga automatica de boletines mensuales desde el portal de la Superintendencia de Bancos del Ecuador usando Selenium.

### Ubicacion
`scripts/descargar.py`

### Dependencias
- selenium
- webdriver-manager
- requests
- `scripts/config.py`

### Salida esperada
```
datos_bancos_<mes>_<anio>/
????????? Series Banco <BANCO> <MES> <ANIO>.zip
????????? archivos_excel/
    ????????? <BANCO> <MES> <ANIO>/
        ????????? <BANCO> <MES> <ANIO>.xlsx
```

---

## procesar_balance.py

### Proposito
Procesa la hoja BAL (Balance General) y genera `master_data/balance.parquet`.

### Salida
`master_data/balance.parquet`

---

## procesar_pyg.py

### Proposito
Procesa la hoja PYG (Perdidas y Ganancias) con desacumulacion y suma movil 12M.

### Salida
`master_data/pyg.parquet`

---

## procesar_camel.py

### Proposito
Extrae indicadores CAMEL y genera `master_data/camel.parquet`.

### Salida
`master_data/camel.parquet`

---

## actualizar_datos.py

### Proposito
Script maestro que:
1. Verifica si hay datos nuevos
2. Descarga datos
3. Procesa BAL, PYG y CAMEL
4. Verifica archivos generados
5. Guarda estado en `master_data/update_status.json`

### Ejecucion
```bash
python scripts/actualizar_datos.py
```

---

## Notas

- El pipeline actual solo genera 3 parquets: BAL, PYG y CAMEL.
- Otros master files historicos (indicadores, cartera, fuentes_usos) ya no se generan.
