# -*- coding: utf-8 -*-
"""
Resumen Ejecutivo — Home tipo Executive Dashboard.

Pagina nueva (Fase 1). Todos los numeros provienen de balance.parquet /
camel.parquet ya cargados por services.data_service; el resumen ejecutivo es
texto generado por reglas simples sobre esos valores reales (no usa un LLM).
"""

import streamlit as st
import pandas as pd

from ui.layout import render_page
from services.data_service import cargar_balance, cargar_camel, calcular_metricas_sistema, obtener_fechas_disponibles
from components.kpi_card import render_kpi_card
from analytics.early_warning import generar_alertas, resumen_alertas
from charts.builders import crear_sparkline
from config.theme_tokens import COLORES

render_page("Resumen Ejecutivo", icono="🏠")

st.title("Resumen Ejecutivo")
st.markdown("Vista consolidada del Sistema Financiero Privado del Ecuador.")

try:
    df_balance, calidad_balance = cargar_balance()
    df_camel, calidad_camel = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

fechas_balance = obtener_fechas_disponibles(df_balance)
fecha_actual = fechas_balance[0]

metricas = calcular_metricas_sistema(df_balance, fecha_actual)


@st.cache_data
def serie_promedio_sistema(df_camel: pd.DataFrame, codigo: str) -> pd.DataFrame:
    """Promedio simple entre bancos del indicador, por fecha (agregado real,
    no ponderado por tamaño — se documenta explícitamente como tal)."""
    df_ind = df_camel[df_camel['codigo'] == codigo]
    serie = df_ind.groupby('fecha')['valor'].mean().reset_index()
    serie['valor_pct'] = serie['valor'] * 100
    return serie.sort_values('fecha')


st.markdown("### Indicadores Clave del Sistema")
col1, col2, col3, col4 = st.columns(4)

with col1:
    render_kpi_card(f"${metricas['total_activos']:,.0f}M", "Total Activos del Sistema", color=COLORES['azul_institucional'])
with col2:
    render_kpi_card(f"${metricas['total_cartera']:,.0f}M", "Cartera de Créditos", color=COLORES['azul_petroleo'])
with col3:
    render_kpi_card(f"${metricas['total_depositos']:,.0f}M", "Depósitos del Público", color=COLORES['azul_info'])
with col4:
    render_kpi_card(f"{metricas['num_bancos']}", "Bancos Activos", color=COLORES['verde'])

st.markdown("### Indicadores Prudenciales (promedio simple entre bancos)")
col5, col6, col7, col8 = st.columns(4)

indicadores_spark = [
    ('SOL', 'Solvencia Promedio', col5),
    ('ROA', 'ROA Promedio', col6),
    ('ROE', 'ROE Promedio', col7),
    ('MOR_TOT', 'Morosidad Promedio', col8),
]

for codigo, label, columna in indicadores_spark:
    serie = serie_promedio_sistema(df_camel, codigo)
    with columna:
        if not serie.empty:
            ultimo = serie['valor_pct'].iloc[-1]
            st.metric(label, f"{ultimo:.2f}%")
            st.plotly_chart(crear_sparkline(serie['valor_pct'].tail(24)), width='stretch',
                             config={'displayModeBar': False})
        else:
            st.metric(label, "N/D")

st.markdown("---")

# --- SEMAFORO Y ALERTAS ---
col_resumen, col_alertas = st.columns([2, 1])

with col_resumen:
    st.markdown("### Resumen Ejecutivo Automático")
    sol = serie_promedio_sistema(df_camel, 'SOL')
    roa = serie_promedio_sistema(df_camel, 'ROA')
    mor = serie_promedio_sistema(df_camel, 'MOR_TOT')

    sol_val = sol['valor_pct'].iloc[-1] if not sol.empty else None
    roa_val = roa['valor_pct'].iloc[-1] if not roa.empty else None
    mor_val = mor['valor_pct'].iloc[-1] if not mor.empty else None

    # NOTA: se escapa "$" como "\$" porque st.markdown interpreta cualquier
    # par de simbolos "$" como delimitadores de formula LaTeX (MathJax) -- con
    # dos montos en dolares en el mismo parrafo, todo el texto entre el primer
    # y el segundo "$" se renderizaba como una sola formula rota. Ver
    # docs/AUDITORIA_COMPLETA.md.
    partes = [
        f"Al corte de **{fecha_actual.strftime('%B %Y').title()}**, el Sistema Financiero Privado del Ecuador está "
        f"conformado por **{metricas['num_bancos']} instituciones activas**, con activos totales de "
        f"**\\${metricas['total_activos']:,.0f} millones** y una cartera de créditos de "
        f"**\\${metricas['total_cartera']:,.0f} millones**."
    ]
    if sol_val is not None:
        partes.append(f"La solvencia promedio del sistema se ubica en **{sol_val:.1f}%**"
                       f"{' (por encima del mínimo regulatorio de referencia)' if sol_val >= 9 else ' (bajo atención: cerca del mínimo regulatorio de referencia)'}.")
    if roa_val is not None:
        partes.append(f"El ROA promedio es **{roa_val:.2f}%**.")
    if mor_val is not None:
        partes.append(f"La morosidad total promedio es **{mor_val:.2f}%**.")

    st.markdown(" ".join(partes))
    st.caption("Texto generado automáticamente a partir de los indicadores cargados — no reemplaza el análisis prudencial experto.")

with col_alertas:
    st.markdown("### Alertas Activas")
    df_alertas = generar_alertas(df_camel)
    resumen = resumen_alertas(df_alertas)

    st.metric("Alertas totales", resumen['total'])
    st.metric("Críticas", resumen['criticas'])
    st.metric("Bancos con alertas", resumen['bancos_afectados'])
    try:
        st.page_link("pages/alertas_tempranas.py", label="Ver detalle de alertas", icon="🚨")
    except Exception:
        # st.page_link requiere contexto de st.navigation (ver ui/sidebar.py);
        # se omite en silencio si la pagina se ejecuta fuera de app.py.
        pass

st.markdown("---")
st.markdown("### Accesos Rápidos")
c1, c2, c3, c4 = st.columns(4)
try:
    with c1:
        st.page_link("pages/panorama_bancario.py", label="Panorama Bancario", icon="📊")
    with c2:
        st.page_link("pages/indicadores_camel.py", label="Indicadores CAMEL", icon="📈")
    with c3:
        st.page_link("pages/ranking_bancos.py", label="Ranking de Bancos", icon="🏆")
    with c4:
        st.page_link("pages/reportes.py", label="Reportes", icon="📤")
except Exception:
    pass
