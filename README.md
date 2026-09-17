[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bancos-dqebh5jqc3r5scsjrlwfxp.streamlit.app)  [![Actualizar Datos](https://github.com/cRistiancec/bancos/actions/workflows/actualizar-datos.yml/badge.svg)](https://github.com/cRistiancec/bancos/actions/workflows/actualizar-datos.yml)

# Sistema Financiero Privado

**Sistema Inteligente para el Monitoreo Integral del Sistema Bancario Privado del Ecuador**

Plataforma institucional de inteligencia de riesgos construida sobre datos públicos de la Superintendencia de Bancos del Ecuador.

**Autor institucional:** Eco. Cristian Coronel Quezada, MBA  
**Solución de:** DATA METRICS — Business Intelligence and Analytics

> Este proyecto es la evolución institucional de "Radar Bancario Ecuador"
> (desarrollo original: Juan Pablo Erráez T., [jp1309/bancos](https://github.com/jp1309/bancos),
> bajo licencia MIT). Se mantiene la atribución al autor original conforme a los
> términos de dicha licencia.

---

## 🌐 Dashboard en vivo

**[→ Abrir el dashboard en Streamlit](https://bancos-dqebh5jqc3r5scsjrlwfxp.streamlit.app)**

La plataforma se actualiza automáticamente cada mes mediante el pipeline ETL de GitHub Actions.

---

## 🎯 ¿Qué hace este sistema?

Monitorea el estado financiero de los **23 bancos privados del Ecuador** con datos oficiales de la Superintendencia de Bancos (SBS), procesando más de **8 millones de registros** históricos desde 2003.

### Módulos principales

| Módulo | Descripción |
|---|---|
| **Resumen Ejecutivo** | Vista consolidada del sistema: activos, cartera, depósitos y alertas |
| **Indicadores CAMEL** | Capital, Activos, Gestión, Rentabilidad y Liquidez por banco |
| **Alertas Tempranas** | Semáforo automático de riesgo por institución |
| **Riesgo de Crédito** | Morosidad, cobertura y calidad de cartera |
| **Riesgo de Liquidez** | Fondos disponibles y cobertura de depósitos |
| **Riesgo de Solvencia** | Patrimonio técnico e índice de solvencia |
| **Balance General** | Estados financieros por banco y fecha |
| **Pérdidas y Ganancias** | Resultados acumulados y desacumulados por mes |
| **Ranking de Bancos** | Clasificación por indicador y periodo |
| **Calidad de Datos** | Integridad y completitud del dataset |

---

## 🗂️ Estructura del repositorio

```
bancos/
├── app.py                     # Punto de entrada Streamlit
├── pages/                     # Módulos del dashboard
│   ├── resumen_ejecutivo.py
│   ├── indicadores_camel.py
│   ├── alertas_tempranas.py
│   ├── riesgo_credito.py
│   └── ...
├── services/
│   └── data_service.py        # Carga centralizada de datos
├── scripts/
│   ├── descargar.py           # ETL: descarga desde SBS
│   └── actualizar_datos.py    # Orquestador del pipeline
├── master_data/               # Datos procesados (parquet)
│   ├── balance.parquet        # Estados de cuenta (BAL)
│   ├── pyg.parquet            # Pérdidas y Ganancias
│   ├── camel.parquet          # Indicadores CAMEL
│   └── metadata.json          # Metadatos de la última actualización
├── config/                    # Configuración y mapeos
├── analytics/                 # Módulos analíticos (alertas, CAMEL)
├── charts/                    # Constructores de gráficos
├── ui/                        # Componentes de interfaz
└── .github/workflows/
    └── actualizar-datos.yml   # Pipeline CI/CD de actualización mensual
```

---

## ⚙️ Pipeline ETL automático

El sistema se actualiza automáticamente mediante **GitHub Actions**:

1. **Descarga** los archivos ZIP desde el portal SBS Ecuador
2. **Procesa** Balance, P&G e Indicadores CAMEL de cada banco
3. **Valida** la integridad (23 bancos, sin pérdida de datos históricos)
4. **Genera** los archivos `master_data/*.parquet` actualizados
5. **Commit** automático de los nuevos datos al repositorio

La actualización se dispara manualmente o puede programarse mensualmente.

**Cobertura temporal:** enero 2003 – presente  
**Fuente de datos:** [SBS Ecuador – Series Históricas](https://www.superbancos.gob.ec/estadisticas/)

---

## 🚀 Ejecución local

### Requisitos

```bash
pip install streamlit pandas pyarrow plotly requests openpyxl
```

### Iniciar el dashboard

```bash
streamlit run app.py
```

### Actualizar datos manualmente

```bash
python scripts/actualizar_datos.py
```

---

## 📊 Datos

| Archivo | Contenido | Registros aprox. |
|---|---|---|
| `balance.parquet` | Cuentas contables por banco y fecha | ~6.5M |
| `pyg.parquet` | P&G acumulado y mensualizado | ~1M |
| `camel.parquet` | Indicadores CAMEL calculados | ~700K |

Todos los datos son **públicos** y provienen del portal oficial de la SBS.

---

## 📄 Licencia

Este proyecto se distribuye bajo la **licencia MIT** del proyecto original.  
Ver [LICENSE](LICENSE) para los términos completos.
