# -*- coding: utf-8 -*-
"""
Modelos Predictivos — forecasting, detección de anomalías y clustering de
bancos sobre series reales de indicadores CAMEL (Fase 2).

Ver models/README.md para el alcance completo (qué se implementó y qué
sigue pendiente por falta de variable objetivo o de datos).
"""

import streamlit as st
import plotly.graph_objects as go

from ui.layout import render_page
from services.data_service import cargar_camel, obtener_fechas_disponibles
from analytics.camel_explorer import obtener_evolucion, serie_promedio_sistema
from models.forecasting import proyectar_serie, backtest_serie, SerieInsuficiente as SerieInsuficienteForecast
from models.anomaly_detection import detectar_anomalias, SerieInsuficiente as SerieInsuficienteAnomalia
from models.clustering import clusterizar_bancos
from config.indicator_mapping import INDICADORES_PRINCIPALES
from config.theme_tokens import COLORES

render_page("Modelos Predictivos", icono="🔮")

st.title("Modelos Predictivos")
st.caption("Herramientas exploratorias sobre datos históricos reales. Las proyecciones son estadísticas, "
           "no predicciones garantizadas; ver metodología en docs/ManualTecnico.md.")

try:
    df_camel, _ = cargar_camel()
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

bancos_disponibles = sorted(df_camel['banco'].unique())

tab_forecast, tab_anomalias, tab_clustering = st.tabs(["📈 Forecasting", "🔍 Detección de Anomalías", "🧬 Clustering de Bancos"])

# ============================================================================
# TAB 1: FORECASTING
# ============================================================================
with tab_forecast:
    col1, col2, col3 = st.columns(3)
    with col1:
        categoria_f = st.selectbox("Categoría", options=list(INDICADORES_PRINCIPALES.keys()), key='cat_forecast')
        opciones_f = {nombre: cod for cod, nombre in INDICADORES_PRINCIPALES[categoria_f]}
        indicador_nombre_f = st.selectbox("Indicador", options=list(opciones_f.keys()), key='ind_forecast')
        codigo_f = opciones_f[indicador_nombre_f]
    with col2:
        ambito_f = st.radio("Ámbito", options=["Promedio del Sistema", "Banco específico"], key='ambito_forecast')
        banco_f = None
        if ambito_f == "Banco específico":
            banco_f = st.selectbox("Banco", options=bancos_disponibles, key='banco_forecast')
    with col3:
        n_periodos = st.slider("Meses a proyectar", min_value=3, max_value=24, value=6, key='n_periodos_forecast')

    if ambito_f == "Promedio del Sistema":
        serie_base = serie_promedio_sistema(df_camel, codigo_f)
        fechas_s, valores_s = serie_base['fecha'], serie_base['valor_pct']
    else:
        serie_base = obtener_evolucion(df_camel, codigo_f, [banco_f])
        fechas_s, valores_s = serie_base['fecha'], serie_base['valor_pct']

    try:
        proyeccion = proyectar_serie(fechas_s, valores_s, n_periodos=n_periodos)

        hist = proyeccion[proyeccion['tipo'] == 'historico']
        fore = proyeccion[proyeccion['tipo'] == 'proyeccion']

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist['fecha'], y=hist['valor'], mode='lines', name='Histórico',
                                  line=dict(width=2, color=COLORES['azul_info'])))
        fig.add_trace(go.Scatter(x=fore['fecha'], y=fore['valor'], mode='lines+markers', name='Proyección',
                                  line=dict(width=2, color=COLORES['naranja'], dash='dash')))
        fig.add_trace(go.Scatter(
            x=list(fore['fecha']) + list(fore['fecha'][::-1]),
            y=list(fore['banda_sup']) + list(fore['banda_inf'][::-1]),
            fill='toself', fillcolor='rgba(232,135,30,0.15)', line=dict(width=0),
            name='Banda de incertidumbre (aprox.)', hoverinfo='skip'
        ))
        fig.update_layout(
            title=f"Proyección: {indicador_nombre_f}" + (f" — {banco_f}" if banco_f else " — Sistema"),
            height=450, yaxis_title="%", hovermode='x unified',
            legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']),
        )
        st.plotly_chart(fig, width='stretch')
        st.caption("Método: suavizado exponencial de Holt (tendencia aditiva, sin estacionalidad). "
                   "Banda: aproximación tipo caminata aleatoria sobre el residuo del modelo, no un intervalo de confianza formal.")

        st.markdown("---")
        st.markdown("##### Precisión del modelo (backtesting)")
        st.caption("Mide qué tan bien este mismo método habría predicho los últimos meses ya conocidos — "
                   "no garantiza nada sobre la proyección futura de arriba, pero indica si esta serie en particular "
                   "es fácil o difícil de proyectar.")
        try:
            bt = backtest_serie(fechas_s, valores_s, n_periodos_test=min(6, n_periodos))
            col_bt1, col_bt2, col_bt3 = st.columns(3)
            with col_bt1:
                st.metric("Error absoluto medio (MAE)", f"{bt['mae']:.2f} pp")
            with col_bt2:
                st.metric("RMSE", f"{bt['rmse']:.2f} pp")
            with col_bt3:
                st.metric("MAPE", f"{bt['mape']:.1f}%" if bt['mape'] is not None else "N/A (valores cerca de 0)")

            fig_bt = go.Figure()
            fig_bt.add_trace(go.Scatter(x=bt['fecha_test'], y=bt['valor_real_test'], mode='lines+markers',
                                         name='Real', line=dict(width=2, color=COLORES['verde'])))
            fig_bt.add_trace(go.Scatter(x=bt['fecha_test'], y=bt['valor_predicho_test'], mode='lines+markers',
                                         name='Predicho (backtesting)', line=dict(width=2, color=COLORES['naranja'], dash='dash')))
            fig_bt.update_layout(
                title="Real vs. predicho en el período de prueba", height=320, yaxis_title="%", hovermode='x unified',
                legend=dict(orientation='h', y=-0.3, x=0.5, xanchor='center'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']),
            )
            st.plotly_chart(fig_bt, width='stretch')
        except SerieInsuficienteForecast as e:
            st.info(f"No se pudo calcular el backtesting: {e}")
    except SerieInsuficienteForecast as e:
        st.warning(str(e))

# ============================================================================
# TAB 2: ANOMALIAS
# ============================================================================
with tab_anomalias:
    col1, col2, col3 = st.columns(3)
    with col1:
        categoria_a = st.selectbox("Categoría", options=list(INDICADORES_PRINCIPALES.keys()), key='cat_anom')
        opciones_a = {nombre: cod for cod, nombre in INDICADORES_PRINCIPALES[categoria_a]}
        indicador_nombre_a = st.selectbox("Indicador", options=list(opciones_a.keys()), key='ind_anom')
        codigo_a = opciones_a[indicador_nombre_a]
    with col2:
        ambito_a = st.radio("Ámbito", options=["Promedio del Sistema", "Banco específico"], key='ambito_anom')
        banco_a = None
        if ambito_a == "Banco específico":
            banco_a = st.selectbox("Banco", options=bancos_disponibles, key='banco_anom')
    with col3:
        contaminacion = st.slider("Sensibilidad (% de puntos marcados como atípicos)", min_value=1, max_value=15, value=5, key='contam_anom') / 100

    if ambito_a == "Promedio del Sistema":
        serie_base_a = serie_promedio_sistema(df_camel, codigo_a)
    else:
        serie_base_a = obtener_evolucion(df_camel, codigo_a, [banco_a])

    try:
        resultado_a = detectar_anomalias(serie_base_a['fecha'], serie_base_a['valor_pct'], contaminacion=contaminacion)
        normales = resultado_a[~resultado_a['anomalia']]
        atipicos = resultado_a[resultado_a['anomalia']]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=resultado_a['fecha'], y=resultado_a['valor'], mode='lines', name='Serie',
                                   line=dict(width=2, color=COLORES['azul_info'])))
        fig2.add_trace(go.Scatter(x=atipicos['fecha'], y=atipicos['valor'], mode='markers', name='Período atípico',
                                   marker=dict(size=10, color=COLORES['rojo'], symbol='x')))
        fig2.update_layout(
            title=f"Detección de anomalías: {indicador_nombre_a}" + (f" — {banco_a}" if banco_a else " — Sistema"),
            height=450, yaxis_title="%", hovermode='x unified',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']),
        )
        st.plotly_chart(fig2, width='stretch')
        st.metric("Períodos atípicos detectados", len(atipicos))
        st.caption("Método: Isolation Forest sobre nivel + variación mes a mes. Herramienta exploratoria, no un sistema de alertas regulatorio.")
    except SerieInsuficienteAnomalia as e:
        st.warning(str(e))

# ============================================================================
# TAB 3: CLUSTERING
# ============================================================================
with tab_clustering:
    col1, col2 = st.columns([2, 1])
    with col1:
        indicadores_cluster = st.multiselect(
            "Indicadores a usar (los bancos sin dato en alguno se excluyen, no se imputan valores)",
            options=['SOL', 'MOR_TOT', 'COB_TOT', 'ROE', 'ROA', 'LIQ'],
            default=['SOL', 'MOR_TOT', 'ROA', 'LIQ'],
        )
    with col2:
        fechas_cluster = obtener_fechas_disponibles(df_camel)
        fecha_cluster = st.selectbox("Fecha", options=fechas_cluster, format_func=lambda x: x.strftime('%B %Y').title(), index=0)
        n_clusters = st.slider("Número de grupos", min_value=2, max_value=6, value=3)

    if len(indicadores_cluster) >= 2:
        resultado_c = clusterizar_bancos(df_camel, fecha_cluster, indicadores_cluster, n_clusters=n_clusters)

        if resultado_c.empty:
            st.warning("No hay suficientes bancos con dato completo en todos los indicadores seleccionados para esta fecha.")
        else:
            fig3 = go.Figure()
            for cluster_id in sorted(resultado_c['cluster'].unique()):
                subset = resultado_c[resultado_c['cluster'] == cluster_id]
                fig3.add_trace(go.Scatter(
                    x=subset['pc1'], y=subset['pc2'], mode='markers+text', name=f"Grupo {cluster_id}",
                    text=subset['banco'], textposition='top center', marker=dict(size=12),
                ))
            fig3.update_layout(
                title=f"Clustering de bancos — {fecha_cluster.strftime('%B %Y').title()}", height=500,
                xaxis_title="Componente principal 1", yaxis_title="Componente principal 2",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORES['texto_primario']),
            )
            st.plotly_chart(fig3, width='stretch')

            tabla = resultado_c[['banco', 'cluster'] + indicadores_cluster].copy()
            for col in indicadores_cluster:
                tabla[col] = tabla[col].apply(lambda v: f"{v:.2f}%")
            st.dataframe(tabla.rename(columns={'banco': 'Banco', 'cluster': 'Grupo'}), hide_index=True, width='stretch')
            st.caption("Método: K-Means sobre valores estandarizados; PCA a 2 componentes solo para visualizar. "
                       "Agrupación exploratoria, no una clasificación regulatoria de riesgo.")
    else:
        st.info("Selecciona al menos 2 indicadores para clusterizar.")
