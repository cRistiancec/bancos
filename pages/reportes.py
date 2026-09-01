# -*- coding: utf-8 -*-
"""
Reportes — centro de exportación de datos a CSV / Excel / PDF.

Pagina nueva (Fase 1, PDF agregado en pulido posterior). Exporta los
datasets reales tal cual estan cargados (sin transformar valores),
filtrados opcionalmente por fecha y banco; y un reporte ejecutivo PDF con
los KPIs y alertas reales del sistema al momento de generarlo.
"""

import io
import pandas as pd
import streamlit as st

from ui.layout import render_page
from services.data_service import cargar_balance, cargar_pyg, cargar_camel, calcular_metricas_sistema, obtener_contexto_sistema, obtener_fechas_disponibles
from analytics.early_warning import generar_alertas, resumen_alertas
from utils.pdf_export import generar_reporte_ejecutivo_pdf, generar_tabla_pdf

render_page("Reportes", icono="📤")

st.title("Reportes")
st.markdown("Exporta los datos del sistema a Excel, CSV o PDF para análisis externo.")

st.markdown("### Reporte Ejecutivo (PDF)")
st.caption("KPIs y alertas activas del sistema al corte más reciente — mismo cálculo que Resumen Ejecutivo y Alertas Tempranas.")

try:
    df_balance_pdf, _ = cargar_balance()
    df_camel_pdf, _ = cargar_camel()
    fecha_pdf = obtener_fechas_disponibles(df_balance_pdf)[0]
    metricas_pdf = calcular_metricas_sistema(df_balance_pdf, fecha_pdf)
    contexto_pdf = obtener_contexto_sistema()
    alertas_pdf = resumen_alertas(generar_alertas(df_camel_pdf))

    pdf_bytes = generar_reporte_ejecutivo_pdf(contexto_pdf, metricas_pdf, alertas_pdf)
    st.download_button("📄 Descargar Reporte Ejecutivo (PDF)", data=pdf_bytes,
                        file_name="reporte_ejecutivo_sistema_financiero_privado.pdf", mime="application/pdf")
except Exception as e:
    st.warning(f"No se pudo generar el reporte ejecutivo PDF: {e}")

st.markdown("---")
st.markdown("### Exportar Dataset")

DATASETS = {
    "Balance General": cargar_balance,
    "Pérdidas y Ganancias": cargar_pyg,
    "Indicadores CAMEL": cargar_camel,
}

dataset_sel = st.selectbox("Dataset a exportar", options=list(DATASETS.keys()))

try:
    df, calidad = DATASETS[dataset_sel]()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    bancos_filtro = st.multiselect("Filtrar por banco (opcional)", options=sorted(df['banco'].unique()))
with col2:
    fechas_disponibles = sorted(df['fecha'].dropna().unique(), reverse=True)
    rango_fechas = st.select_slider(
        "Rango de fechas",
        options=fechas_disponibles,
        value=(fechas_disponibles[-1], fechas_disponibles[0]),
        format_func=lambda x: x.strftime('%b %Y')
    )

df_export = df.copy()
if bancos_filtro:
    df_export = df_export[df_export['banco'].isin(bancos_filtro)]
df_export = df_export[(df_export['fecha'] >= rango_fechas[0]) & (df_export['fecha'] <= rango_fechas[1])]

st.markdown(f"**{len(df_export):,} registros** listos para exportar (de {calidad.get('registros_limpios', 0):,} totales en el dataset).")
st.dataframe(df_export.head(50), width='stretch', height=300)
if len(df_export) > 50:
    st.caption("Mostrando las primeras 50 filas. La exportación incluye el conjunto completo filtrado.")

col_csv, col_xlsx, col_pdf = st.columns(3)
with col_csv:
    csv_bytes = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Descargar CSV", data=csv_bytes,
                        file_name=f"{dataset_sel.lower().replace(' ', '_')}.csv", mime="text/csv")

with col_xlsx:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='Datos', index=False)
    buffer.seek(0)
    st.download_button("⬇️ Descargar Excel", data=buffer,
                        file_name=f"{dataset_sel.lower().replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with col_pdf:
    if len(df_export) > 200:
        st.caption("PDF limitado a 200 filas (usa CSV/Excel para el set completo).")
    pdf_tabla = generar_tabla_pdf(f"{dataset_sel} — datos filtrados", df_export, max_filas=200)
    st.download_button("📄 Descargar PDF", data=pdf_tabla,
                        file_name=f"{dataset_sel.lower().replace(' ', '_')}.pdf", mime="application/pdf")
