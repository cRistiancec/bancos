> **Documento histórico** — describe el dashboard de 4 módulos
> (`Inicio.py` + `pages/1-4_*.py`) previo a la refactorización institucional
> de 2026-07-27 y a la integración con la automatización de datos de
> 2026-08-31. El entry point actual es `app.py` (23 páginas en
> `pages/*.py`, sin `Inicio.py` ni `archived_pages/`). Para el estado
> actual, ver `README.md`, `docs/ARQUITECTURA.md` y `docs/CONTEXTO.md`. Se
> conserva sin modificar como registro histórico.

# Estructura Final del Dashboard - Radar Bancario Ecuador

**Version**: 4.2.1
**Fecha**: 05 de febrero de 2026
**Estado**: Implementado y Documentado

---

## Resumen Ejecutivo

El dashboard de Business Intelligence para el sistema bancario ecuatoriano esta enfocado en 4 modulos principales:

1. **Vista General** - Panorama del sistema
2. **Analisis de Balance** - Evolucion temporal de activos y pasivos
3. **Analisis de Resultados** - Perdidas y ganancias (PYG)
4. **Indicadores CAMEL** - Salud financiera por dimension

**Nota**: El modulo de Calidad de Datos fue archivado y esta en `archived_pages/0_Calidad_old.py`.

---

## Arquitectura del Dashboard

### Estructura de Archivos

```
bancos/
????????? Inicio.py                      # Punto de entrada principal
????????? pages/                         # Modulos del dashboard
???   ????????? 1_Panorama.py             # Vista general del sistema
???   ????????? 2_Balance_General.py      # Analisis temporal de balance
???   ????????? 3_P??rdidas_y_Ganancias.py # Resultados PYG
???   ????????? 4_CAMEL.py                # Indicadores CAMEL
????????? archived_pages/                # Modulos archivados
???   ????????? 0_Calidad_old.py          # Calidad de datos (archivado)
????????? utils/                         # Utilidades compartidas
???   ????????? data_loader.py            # Carga centralizada de datos
???   ????????? data_quality.py           # Validaciones de calidad
???   ????????? charts.py                 # Componentes graficos
????????? config/                        # Configuracion
???   ????????? indicator_mapping.py      # Mapeo de codigos contables
????????? master_data/                   # Datos procesados (Parquet)
???   ????????? balance.parquet           # Balance General
???   ????????? pyg.parquet               # Perdidas y Ganancias
???   ????????? camel.parquet             # Indicadores CAMEL
???   ????????? metadata.json             # Info de ultima actualizacion
???   ????????? update_status.json        # Estado del proceso
????????? docs/                          # Documentacion tecnica
????????? scripts/                       # Scripts ETL
    ????????? actualizar_datos.py         # Orquestador
    ????????? descargar.py                # Descarga y descompresion
    ????????? procesar_balance.py         # Procesa BAL -> balance.parquet
    ????????? procesar_pyg.py             # Procesa PYG -> pyg.parquet
    ????????? procesar_camel.py           # Procesa CAMEL -> camel.parquet
```

---

## Modulos Implementados

### Modulo 1: Panorama del Sistema

**Archivo**: `pages/1_Panorama.py`
**Proposito**: Vista general del sistema bancario ecuatoriano

**Visualizaciones**:
1. **KPIs del Sistema**
   - Total Activos
   - Total Cartera de Creditos
   - Total Depositos
   - Total Patrimonio
   - Fondos Disponibles
   - Bancos Activos

2. **Treemap Jerarquico**
   - Composicion de activos con drill-down
   - Composicion de pasivos + patrimonio con drill-down

3. **Ranking de Bancos**
   - Barras horizontales por activos y pasivos

4. **Crecimiento Anual**
   - Variacion YoY de cartera y depositos

**Filtros**:
- Selector de fecha (mes/anio)
- Comparacion automatica vs anio anterior

---

### Modulo 2: Balance General

**Archivo**: `pages/2_Balance_General.py`
**Proposito**: Analisis temporal de las cuentas de balance

**Secciones**:
1. **Evolucion Comparativa** (lineas multi-banco)
2. **Heatmap YoY** (matriz banco x mes)
3. **Ranking por Banco** (comparacion para un mes especifico)

**Filtros**:
- Selector de cuenta con jerarquia 1->2->4->6 digitos
- Multiselect de bancos (hasta 10)
- Rango de fechas
- Modo: Absoluto, Indexado, Participacion

---

### Modulo 3: Perdidas y Ganancias

**Archivo**: `pages/3_P??rdidas_y_Ganancias.py`
**Proposito**: Analisis de resultados y rentabilidad (PYG)

**Secciones**:
1. **Evolucion Comparativa** (serie temporal por indicador)
2. **Ranking por Indicador** (comparacion de bancos en un mes)

**Notas tecnicas**:
- Usa `valor_12m` (suma movil 12 meses) para comparabilidad

---

### Modulo 4: Indicadores CAMEL

**Archivo**: `pages/4_CAMEL.py`
**Proposito**: Evaluacion bancaria por dimensiones CAMEL

**Secciones**:
1. **Analisis por Indicador** (ranking)
2. **Evolucion Temporal** (lineas multi-banco)
3. **Heatmap Mensual** (banco x mes)

---

## Datos Procesados (actual)

- **balance.parquet**: Balance General (BAL)
- **pyg.parquet**: Perdidas y Ganancias (PYG)
- **camel.parquet**: Indicadores CAMEL

Periodo: Enero 2003 - Diciembre 2025 (276 meses)

---

## Notas de Mantenimiento

- El entrypoint real es `Inicio.py` (no `app.py`).
- La documentacion tecnica del pipeline esta en `docs/PIPELINE.md`.
