# -*- coding: utf-8 -*-
"""
Alertas Predictivas (Fase 3) — proyecta los indicadores N meses adelante y
avisa cuáles cruzarían el umbral de alerta/crítico antes de que ocurra.

Ver analytics/predictive_alerts.py para la metodología y
docs/ManualTecnico.md para la validación (backtesting) del modelo de
proyección subyacente.
"""

import streamlit as st

from ui.layout import render_page
from services.data_service import cargar_camel
from analytics.predictive_alerts import resumen_predictivo_sistema, detalle_predictivo_bancos
from components.semaforo import render_badge_severidad

render_page("Alertas Predictivas", icono="🔭")

st.title("Alertas Predictivas")
st.info("Proyección estadística sobre las series históricas reales (mismo modelo de "
        "**Modelos Predictivos → Forecasting**, con backtesting propio ahí). No es una predicción "
        "garantizada — es una señal de alerta temprana basada en la tendencia reciente.", icon="🔭")

try:
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

n_periodos = st.slider("Horizonte de proyección (meses)", min_value=3, max_value=12, value=6)

st.markdown("### Resumen del sistema")
resumen = resumen_predictivo_sistema(df_camel, n_periodos=n_periodos)

if resumen.empty:
    st.warning("No hay suficiente historia para proyectar los indicadores del sistema.")
else:
    alertas_sistema = resumen[resumen['empeora']]
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Indicadores del sistema con deterioro proyectado", len(alertas_sistema))
    with col2:
        st.metric("Indicadores monitoreados", len(resumen))

    if not alertas_sistema.empty:
        for _, fila in alertas_sistema.iterrows():
            st.markdown(
                f"**{fila['indicador']}**: {fila['valor_actual']:.2f}% actual → "
                f"{fila['valor_proyectado']:.2f}% proyectado en {n_periodos} meses "
                f"({render_badge_severidad(fila['severidad_actual'])} → {render_badge_severidad(fila['severidad_proyectada'])})",
                unsafe_allow_html=True
            )
    else:
        st.success("Ningún indicador del sistema muestra deterioro proyectado en este horizonte.")

st.markdown("---")
st.markdown("### Detalle por banco")
n_bancos = df_camel['banco'].nunique()
st.caption(f"Calcula la proyección para los {n_bancos} bancos × 6 indicadores (~15-20 segundos la primera vez; "
           "queda en caché después). Se muestran solo los casos donde la severidad proyectada empeora.")

if st.button("🔍 Calcular detalle por banco"):
    with st.spinner("Proyectando indicadores por banco... esto puede tardar unos segundos."):
        detalle = detalle_predictivo_bancos(df_camel, n_periodos=n_periodos)

    if detalle.empty:
        st.success("Ningún banco muestra deterioro proyectado de severidad en este horizonte.")
    else:
        st.warning(f"{len(detalle)} caso(s) de deterioro proyectado detectados.")
        detalle_display = detalle.copy()
        detalle_display['Valor actual'] = detalle_display['valor_actual'].apply(lambda v: f"{v:.2f}%")
        detalle_display['Valor proyectado'] = detalle_display['valor_proyectado'].apply(lambda v: f"{v:.2f}%")
        detalle_display['Severidad actual'] = detalle_display['severidad_actual'].apply(render_badge_severidad)
        detalle_display['Severidad proyectada'] = detalle_display['severidad_proyectada'].apply(render_badge_severidad)

        st.markdown(
            detalle_display[['banco', 'indicador', 'Valor actual', 'Valor proyectado', 'Severidad actual', 'Severidad proyectada']]
            .rename(columns={'banco': 'Banco', 'indicador': 'Indicador'})
            .to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
