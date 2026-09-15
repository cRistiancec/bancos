# -*- coding: utf-8 -*-
"""
Exportación de reportes institucionales a PDF (reportlab).

Genera un reporte ejecutivo con los KPIs y alertas reales del sistema al
momento de la generación -- no incluye ninguna cifra que no venga de
services/analytics ya calculados en el resto de la plataforma.
"""

import io
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

AZUL_INSTITUCIONAL = colors.HexColor('#1B4C8C')
GRIS_TEXTO = colors.HexColor('#2B2F33')
VERDE = colors.HexColor('#1B8A5A')
NARANJA = colors.HexColor('#E8871E')
ROJO = colors.HexColor('#C1272D')

COLOR_SEVERIDAD_PDF = {'OK': VERDE, 'ALERTA': NARANJA, 'CRITICO': ROJO}


def _estilos():
    hoja = getSampleStyleSheet()
    hoja.add(ParagraphStyle(name='TituloInstitucional', fontSize=16, textColor=AZUL_INSTITUCIONAL,
                             spaceAfter=4, fontName='Helvetica-Bold'))
    hoja.add(ParagraphStyle(name='Subtitulo', fontSize=9, textColor=GRIS_TEXTO, spaceAfter=14))
    hoja.add(ParagraphStyle(name='SeccionTitulo', fontSize=12, textColor=AZUL_INSTITUCIONAL,
                             spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'))
    return hoja


def generar_reporte_ejecutivo_pdf(contexto: dict, metricas: dict, resumen_alertas: dict) -> bytes:
    """Reporte ejecutivo de una pagina: KPIs del sistema + alertas activas.

    Args:
        contexto: salida de services.data_service.obtener_contexto_sistema()
        metricas: salida de services.data_service.calcular_metricas_sistema()
        resumen_alertas: salida de analytics.early_warning.resumen_alertas()
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    estilos = _estilos()
    elementos = []

    elementos.append(Paragraph("SISTEMA FINANCIERO PRIVADO", estilos['TituloInstitucional']))
    elementos.append(Paragraph(
        "Sistema Inteligente para el Monitoreo Integral del Sistema Bancario Privado del Ecuador — "
        "DATA METRICS, Business Intelligence and Analytics", estilos['Subtitulo']))
    elementos.append(Paragraph(f"Reporte generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilos['Normal']))

    fecha_corte = contexto.get('fecha_corte')
    fecha_corte_str = fecha_corte.strftime('%B %Y').title() if fecha_corte is not None else "N/D"
    elementos.append(Paragraph(f"Corte de datos: {fecha_corte_str}", estilos['Normal']))

    elementos.append(Paragraph("Indicadores del Sistema", estilos['SeccionTitulo']))
    filas_kpi = [
        ["Indicador", "Valor"],
        ["Total Activos", f"${metricas.get('total_activos', 0):,.0f}M"],
        ["Cartera de Créditos", f"${metricas.get('total_cartera', 0):,.0f}M"],
        ["Depósitos del Público", f"${metricas.get('total_depositos', 0):,.0f}M"],
        ["Patrimonio", f"${metricas.get('total_patrimonio', 0):,.0f}M"],
        ["Bancos Activos", f"{metricas.get('num_bancos', 0)}"],
    ]
    tabla_kpi = Table(filas_kpi, colWidths=[9 * cm, 6 * cm])
    tabla_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_INSTITUCIONAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F7FA')]),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla_kpi)

    elementos.append(Paragraph("Alertas Tempranas Activas", estilos['SeccionTitulo']))
    filas_alertas = [
        ["Severidad", "Cantidad"],
        ["Crítico", str(resumen_alertas.get('criticas', 0))],
        ["Alerta", str(resumen_alertas.get('alertas', 0))],
        ["Bancos afectados", str(resumen_alertas.get('bancos_afectados', 0))],
    ]
    tabla_alertas = Table(filas_alertas, colWidths=[9 * cm, 6 * cm])
    tabla_alertas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_INSTITUCIONAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('TEXTCOLOR', (0, 1), (0, 1), ROJO),
        ('TEXTCOLOR', (0, 2), (0, 2), NARANJA),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla_alertas)

    elementos.append(Spacer(1, 16))
    elementos.append(Paragraph(
        "Este reporte se genera automáticamente a partir de los datos cargados en la plataforma "
        "(fuente: Superintendencia de Bancos del Ecuador). No reemplaza el análisis prudencial experto.",
        estilos['Subtitulo']))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


def generar_tabla_pdf(titulo: str, df: pd.DataFrame, max_filas: int = 200) -> bytes:
    """PDF simple con una tabla (para exportar una vista filtrada de datos).
    Se limita a `max_filas` para mantener el PDF legible -- las tablas de
    miles de filas se exportan mejor a Excel/CSV (ver pages/reportes.py).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    estilos = _estilos()
    elementos = [
        Paragraph("SISTEMA FINANCIERO PRIVADO", estilos['TituloInstitucional']),
        Paragraph(titulo, estilos['Subtitulo']),
        Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} — "
                  f"{len(df):,} registros totales" + (f" (mostrando primeros {max_filas})" if len(df) > max_filas else ""),
                  estilos['Normal']),
        Spacer(1, 10),
    ]

    df_mostrar = df.head(max_filas)
    data = [list(df_mostrar.columns)] + df_mostrar.astype(str).values.tolist()
    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_INSTITUCIONAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F7FA')]),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
    ]))
    elementos.append(tabla)

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()
