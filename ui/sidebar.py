# -*- coding: utf-8 -*-
"""Contenido adicional del sidebar (la navegacion principal la genera
st.navigation() automaticamente desde config/nav_registry.py). Aqui se
agrega: estado de conexion a datos, indicadores rapidos y accesos directos.
"""

import streamlit as st

from services.data_service import obtener_contexto_sistema


def render_sidebar_extra():
    contexto = obtener_contexto_sistema()

    st.sidebar.markdown("---")
    st.sidebar.markdown("##### Estado de datos")

    if contexto.get('datos_disponibles'):
        st.sidebar.success("Conectado a master_data/", icon="🟢")
    else:
        st.sidebar.error("Sin datos disponibles", icon="🔴")

    num_bancos = contexto.get('num_bancos')
    fecha_corte = contexto.get('fecha_corte')
    if num_bancos:
        st.sidebar.caption(f"{num_bancos} bancos · corte "
                            f"{fecha_corte.strftime('%b %Y') if fecha_corte is not None else 'N/D'}")

    st.sidebar.markdown("##### Accesos rápidos")
    try:
        st.sidebar.page_link("pages/resumen_ejecutivo.py", label="Resumen Ejecutivo", icon="🏠")
        st.sidebar.page_link("pages/alertas_tempranas.py", label="Alertas Tempranas", icon="🚨")
        st.sidebar.page_link("pages/reportes.py", label="Reportes", icon="📤")
    except Exception:
        # st.page_link requiere que la pagina este registrada en st.navigation;
        # si se invoca fuera de ese contexto (p.ej. pruebas), se omite en silencio.
        pass

    st.sidebar.markdown("---")
    st.sidebar.caption("Manual de usuario: docs/ManualUsuario.md")
