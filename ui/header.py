# -*- coding: utf-8 -*-
"""Header institucional: logo, nombre del sistema, reloj, estado operativo
y semaforo general de riesgo. Se renderiza en cada pagina via ui.layout.
"""

import base64
from pathlib import Path
from datetime import datetime
import streamlit as st

from services.data_service import obtener_contexto_sistema, cargar_camel
from analytics.early_warning import generar_alertas, resumen_alertas
from components.semaforo import render_badge_severidad

LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo-datametrics.png"

NOMBRE_SISTEMA = "SISTEMA FINANCIERO PRIVADO"
SUBTITULO_SISTEMA = "Sistema Inteligente para el Monitoreo Integral del Sistema Bancario Privado del Ecuador"


def _obtener_semaforo_general() -> tuple:
    """Retorna (severidad, mensaje) para el semaforo del header, basado en
    analytics.early_warning sobre la ultima fecha disponible de camel.parquet.
    """
    try:
        df_camel, _ = cargar_camel()
        df_alertas = generar_alertas(df_camel)
        resumen = resumen_alertas(df_alertas)
    except Exception:
        return 'SIN_DATO', 'Datos no disponibles'

    if resumen['criticas'] > 0:
        return 'CRITICO', f"{resumen['criticas']} indicador(es) crítico(s)"
    if resumen['alertas'] > 0:
        return 'ALERTA', f"{resumen['alertas']} indicador(es) en alerta"
    return 'OK', 'Parámetros normales'


def render_header():
    contexto = obtener_contexto_sistema()
    severidad, mensaje_semaforo = _obtener_semaforo_general()

    ahora = datetime.now()
    fecha_corte = contexto.get('fecha_corte')
    fecha_corte_str = fecha_corte.strftime('%B %Y').title() if fecha_corte is not None else "N/D"
    ultima_act = contexto.get('fecha_actualizacion') or "N/D"
    num_bancos = contexto.get('num_bancos') or "N/D"
    total_registros = contexto.get('total_registros')
    total_registros_str = f"{total_registros:,}" if total_registros else "N/D"
    estado_operativo = "Operativo" if contexto.get('datos_disponibles') else "Sin conexión a datos"

    if LOGO_PATH.exists():
        logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode('utf-8')
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:52px;" />'
    else:
        # No hay asset de marca en el repo: se usa un wordmark de texto como
        # respaldo. Colocar el logo oficial en assets/logo-datametrics.png lo
        # reemplaza automaticamente, sin cambios de codigo.
        logo_html = '<div class="sfp-wordmark">DATAMETRICS</div>'

    st.markdown(f"""
        <div class="sfp-header">
            <div class="sfp-header-top">
                <div class="sfp-brand">
                    {logo_html}
                    <div class="sfp-title">
                        <h1>{NOMBRE_SISTEMA}</h1>
                        <p>{SUBTITULO_SISTEMA}</p>
                    </div>
                </div>
                <div class="sfp-header-meta">
                    <div><strong>{ahora.strftime('%d/%m/%Y')}</strong>Fecha</div>
                    <div><strong>{ahora.strftime('%H:%M')}</strong>Hora local</div>
                    <div><strong>{fecha_corte_str}</strong>Corte de datos</div>
                    <div><strong>{ultima_act}</strong>Última actualización</div>
                    <div><strong>{num_bancos}</strong>Bancos</div>
                    <div><strong>{total_registros_str}</strong>Registros</div>
                    <div><strong>{estado_operativo}</strong>Estado</div>
                </div>
            </div>
            <div style="margin-top:0.75rem;">
                {render_badge_severidad(severidad, mensaje_semaforo)}
            </div>
        </div>
    """, unsafe_allow_html=True)
