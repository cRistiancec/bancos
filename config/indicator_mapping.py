# -*- coding: utf-8 -*-
"""
Mapeo de codigos contables e indicadores financieros.
Fuente: Superintendencia de Bancos del Ecuador - Catalogo Unico de Cuentas
"""

# =============================================================================
# CODIGOS DE BALANCE GENERAL (Hoja BAL)
# =============================================================================

CODIGOS_BALANCE = {
    # ACTIVOS (Codigo 1)
    'activo_total': '1',
    'fondos_disponibles': '11',
    'operaciones_interbancarias': '12',
    'inversiones': '13',
    'cartera_creditos': '14',
    'deudores_aceptaciones': '15',
    'cuentas_por_cobrar': '16',
    'bienes_arrendamiento': '17',
    'activos_fijos': '18',
    'otros_activos': '19',

    # PASIVOS (Codigo 2)
    'pasivo_total': '2',
    'obligaciones_publico': '21',
    'operaciones_interbancarias_pas': '22',
    'obligaciones_inmediatas': '23',
    'aceptaciones_circulacion': '24',
    'cuentas_por_pagar': '25',
    'obligaciones_financieras': '26',
    'valores_circulacion': '27',
    'obligaciones_convertibles': '28',
    'otros_pasivos': '29',

    # PATRIMONIO (Codigo 3)
    'patrimonio': '3',
    'capital_social': '31',
    'prima_descuento': '32',
    'reservas': '33',
    'otros_aportes': '34',
    'superavit_valuaciones': '35',
    'resultados': '36',
}

# Subcuentas importantes de cartera
CODIGOS_CARTERA = {
    'cartera_comercial': '1401',
    'cartera_consumo': '1402',
    'cartera_vivienda': '1403',
    'cartera_microcredito': '1404',
    'cartera_educativo': '1405',
    'cartera_inversion_publica': '1406',
    'cartera_vencida': '1421',
    'provision_cartera': '1499',
}

# =============================================================================
# CODIGOS DE ESTADO DE RESULTADOS (Hoja PYG)
# =============================================================================

CODIGOS_RESULTADOS = {
    # INGRESOS (Codigo 5)
    'ingresos_total': '5',
    'intereses_descuentos_ganados': '51',
    'comisiones_ganadas': '52',
    'utilidades_financieras': '53',
    'ingresos_servicios': '54',
    'otros_ingresos_operacionales': '55',
    'otros_ingresos': '56',

    # GASTOS (Codigo 4)
    'gastos_total': '4',
    'intereses_causados': '41',
    'comisiones_causadas': '42',
    'perdidas_financieras': '43',
    'provisiones': '44',
    'gastos_operacion': '45',
    'otras_perdidas_operacionales': '46',
    'otros_gastos_perdidas': '47',
    'impuestos_participaciones': '48',
}

# =============================================================================
# INDICADORES FINANCIEROS (Hojas CAMEL, INDICAD, INDIC CARTERA)
# =============================================================================

# Indicadores exactos por codigo (para busqueda precisa en camel.parquet)
INDICADORES_CAMEL = {
    # CAPITAL (C) - 1 indicador
    'solvencia': 'SOL',

    # ASSETS (A) - Calidad de Activos - 29 indicadores

    # Morosidad por tipo de cartera (9)
    'morosidad_total': 'MOR_TOT',
    'morosidad_consumo': 'MOR_CONS',
    'morosidad_inmobiliaria': 'MOR_INMOB',
    'morosidad_vivienda_vip': 'MOR_INMOB_VIP',
    'morosidad_vivienda_social': 'MOR_VIS',
    'morosidad_microcredito': 'MOR_MICRO',
    'morosidad_educativo': 'MOR_EDU',
    'morosidad_productivo': 'MOR_PROD',
    'morosidad_inversion_publica': 'MOR_INV_PUB',

    # Cobertura por tipo de cartera (11)
    'cobertura_total': 'COB_TOT',
    'cobertura_consumo': 'COB_CONS',
    'cobertura_inmobiliaria': 'COB_INMOB',
    'cobertura_vivienda_vip': 'COB_INMOB_VIP',
    'cobertura_vivienda_social': 'COB_VIS',
    'cobertura_microcredito': 'COB_MICRO',
    'cobertura_educativo': 'COB_EDU',
    'cobertura_productivo': 'COB_PROD',
    'cobertura_inversion_publica': 'COB_INV_PUB',
    'cobertura_comercial_prioritario': 'COB_COM_PRIO',
    'cobertura_consumo_prioritario': 'COB_CONS_PRIO',

    # Participacion por tipo de cartera (8)
    'participacion_consumo': 'PART_CONS',
    'participacion_inmobiliaria': 'PART_INMOB',
    'participacion_vivienda_vip': 'PART_INMOB_VIP',
    'participacion_vivienda_social': 'PART_VIS',
    'participacion_microcredito': 'PART_MICRO',
    'participacion_educativo': 'PART_EDU',
    'participacion_productivo': 'PART_PROD',
    'participacion_inversion_publica': 'PART_INV_PUB',

    # Calidad de activos (3)
    'activos_improductivos_netos': 'AIN',
    'cartera_activos': 'CAR_ACT',
    'inversiones_activos': 'INV_ACT',

    # MANAGEMENT (M) - Eficiencia - 4 indicadores
    'gastos_margen_financiero': 'GO_MNF',
    'gastos_activo_promedio': 'GO_ACT',
    'gastos_personal': 'GP_ACT',
    'activos_productivos_pasivos_costo': 'AP_PC',

    # EARNINGS (E) - Rentabilidad - 4 indicadores
    'roe': 'ROE',
    'roa': 'ROA',
    'depositos_brecha': 'DEP_BRECHA',
    'depositos_spread': 'DEP_SPREAD',

    # LIQUIDITY (L) - Liquidez - 1 indicador
    'liquidez': 'LIQ',
}

# Indicadores agrupados por categoria CAMEL para UI
GRUPOS_INDICADORES = {
    'C - Capital y Solvencia': [
        'SOL',  # Indice de Solvencia
    ],
    'A - Morosidad por Cartera': [
        'MOR_TOT',        # Morosidad Total
        'MOR_CONS',       # Morosidad Consumo
        'MOR_INMOB',      # Morosidad Inmobiliaria
        'MOR_INMOB_VIP',  # Morosidad Vivienda VIP
        'MOR_VIS',        # Morosidad Vivienda Social
        'MOR_MICRO',      # Morosidad Microcredito
        'MOR_EDU',        # Morosidad Educativo
        'MOR_PROD',       # Morosidad Productivo
        'MOR_INV_PUB',    # Morosidad Inversion Publica
    ],
    'A - Cobertura por Cartera': [
        'COB_TOT',        # Cobertura Total
        'COB_CONS',       # Cobertura Consumo
        'COB_INMOB',      # Cobertura Inmobiliaria
        'COB_INMOB_VIP',  # Cobertura Vivienda VIP
        'COB_VIS',        # Cobertura Vivienda Social
        'COB_MICRO',      # Cobertura Microcredito
        'COB_EDU',        # Cobertura Educativo
        'COB_PROD',       # Cobertura Productivo
        'COB_INV_PUB',    # Cobertura Inversion Publica
        'COB_COM_PRIO',   # Cobertura Comercial Prioritario
        'COB_CONS_PRIO',  # Cobertura Consumo Prioritario
    ],
    'A - Participacion por Cartera': [
        'PART_CONS',      # Participacion Consumo
        'PART_INMOB',     # Participacion Inmobiliaria
        'PART_INMOB_VIP', # Participacion Vivienda VIP
        'PART_VIS',       # Participacion Vivienda Social
        'PART_MICRO',     # Participacion Microcredito
        'PART_EDU',       # Participacion Educativo
        'PART_PROD',      # Participacion Productivo
        'PART_INV_PUB',   # Participacion Inversion Publica
    ],
    'A - Calidad de Activos': [
        'AIN',       # Activos Improductivos Netos
        'CAR_ACT',   # Cartera / Activos
        'INV_ACT',   # Inversiones / Activos
    ],
    'M - Management y Eficiencia': [
        'GO_MNF',       # Gastos Operacion / Margen Neto Financiero
        'GO_ACT',       # Gastos Operacion / Activo Promedio
        'GP_ACT',       # Gastos Personal / Activo Promedio
        'AP_PC',        # Activos Productivos / Pasivos con Costo
    ],
    'E - Earnings (Rentabilidad)': [
        'ROE',          # Resultados / Patrimonio Promedio
        'ROA',          # Resultados / Activo Promedio
        'DEP_BRECHA',   # Depositos Brecha
        'DEP_SPREAD',   # Depositos Spread
    ],
    'L - Liquidez': [
        'LIQ',  # Fondos Disponibles / Depositos Corto Plazo
    ],
}

# =============================================================================
# ETIQUETAS AMIGABLES PARA UI
# =============================================================================

ETIQUETAS_BALANCE = {
    '1': 'Total Activos',
    '11': 'Fondos Disponibles',
    '13': 'Inversiones',
    '14': 'Cartera de Creditos',
    '2': 'Total Pasivos',
    '21': 'Depositos del Publico',
    '26': 'Obligaciones Financieras',
    '3': 'Patrimonio',
    '31': 'Capital Social',
}

ETIQUETAS_INDICADORES = {
    # Capital
    'SOL': 'Solvencia',

    # Morosidad
    'MOR_TOT': 'Morosidad Total',
    'MOR_CONS': 'Morosidad Consumo',
    'MOR_INMOB': 'Morosidad Inmobiliaria',
    'MOR_INMOB_VIP': 'Morosidad Vivienda VIP',
    'MOR_VIS': 'Morosidad Vivienda Social',
    'MOR_MICRO': 'Morosidad Microcredito',
    'MOR_EDU': 'Morosidad Educativo',
    'MOR_PROD': 'Morosidad Productivo',
    'MOR_INV_PUB': 'Morosidad Inversion Publica',

    # Cobertura
    'COB_TOT': 'Cobertura Total',
    'COB_CONS': 'Cobertura Consumo',
    'COB_INMOB': 'Cobertura Inmobiliaria',
    'COB_INMOB_VIP': 'Cobertura Vivienda VIP',
    'COB_VIS': 'Cobertura Vivienda Social',
    'COB_MICRO': 'Cobertura Microcredito',
    'COB_EDU': 'Cobertura Educativo',
    'COB_PROD': 'Cobertura Productivo',
    'COB_INV_PUB': 'Cobertura Inversion Publica',
    'COB_COM_PRIO': 'Cobertura Comercial Prioritario',
    'COB_CONS_PRIO': 'Cobertura Consumo Prioritario',

    # Participacion
    'PART_CONS': 'Participacion Consumo',
    'PART_INMOB': 'Participacion Inmobiliaria',
    'PART_INMOB_VIP': 'Participacion Vivienda VIP',
    'PART_VIS': 'Participacion Vivienda Social',
    'PART_MICRO': 'Participacion Microcredito',
    'PART_EDU': 'Participacion Educativo',
    'PART_PROD': 'Participacion Productivo',
    'PART_INV_PUB': 'Participacion Inversion Publica',

    # Calidad de Activos
    'AIN': 'Activos Improductivos Netos',
    'CAR_ACT': 'Cartera / Activos',
    'INV_ACT': 'Inversiones / Activos',

    # Eficiencia
    'GO_MNF': 'Gastos Op / Margen Neto Financiero',
    'GO_ACT': 'Gastos Op / Activo Promedio',
    'GP_ACT': 'Gastos Personal / Activo Promedio',
    'AP_PC': 'Activos Productivos / Pasivos Costo',

    # Rentabilidad
    'ROE': 'ROE',
    'ROA': 'ROA',
    'DEP_BRECHA': 'Depositos Brecha',
    'DEP_SPREAD': 'Depositos Spread',

    # Liquidez
    'LIQ': 'Liquidez',
}

# =============================================================================
# UMBRALES Y RANGOS ESPERADOS (para validacion)
# =============================================================================

RANGOS_INDICADORES = {
    'morosidad': {'min': 0, 'max': 100, 'alerta': 5, 'critico': 10},
    'cobertura': {'min': 0, 'max': 500, 'alerta': 100, 'critico': 80},
    'roe': {'min': -50, 'max': 50, 'alerta': 5, 'critico': 0},
    'roa': {'min': -10, 'max': 10, 'alerta': 0.5, 'critico': 0},
    'solvencia': {'min': 0, 'max': 100, 'alerta': 12, 'critico': 9},
    'liquidez': {'min': 0, 'max': 200, 'alerta': 20, 'critico': 15},
}

# =============================================================================
# LISTA DE BANCOS ESPERADOS
# =============================================================================
# IMPORTANTE: estos nombres deben coincidir EXACTAMENTE con los valores reales
# de la columna 'banco' en master_data/*.parquet (incluye tildes/variantes de
# nombre tal como los reporta la Superintendencia). Antes del pulido de
# 2026-07-27 esta lista tenia 'Atlantida', 'Comercial Manabi' y 'Ruminahui'
# sin tilde/variante -- corregido entonces, ver docs/AUDITORIA_COMPLETA.md.
#
# Segunda corrección (2026-08-31, integración con la línea de datos del
# repositorio original): al reemplazar master_data/*.parquet (dic-2025) por
# el corte real más reciente (jun-2026, pipeline de `jp1309/bancos`), se
# verificó de nuevo la columna 'banco' contra los tres parquet y aparecieron
# variantes distintas para 3 entidades, más una que no existe en absoluto en
# los datos publicados por ese pipeline:
#   'Atlantida (antes DMiro)'  -> 'Atlantida'
#   'Comercial Manabí'         -> 'Comercial de Manabí'
#   'Rumiñahui'                -> 'General Rumiñahui'
#   'Visionfund'                -> 'VisionFund' (capitalización)
#   'Amibank'                   -> eliminado: 0 filas en balance/pyg/camel en
#                                  las 276 fechas del pipeline vigente (no es
#                                  una entidad que dejó de reportar; nunca
#                                  aparece en esta fuente). NO VERIFICABLE si
#                                  se trataba de un artefacto de parseo del
#                                  pipeline anterior o de una entidad distinta
#                                  — no se investiga más a fondo porque no
#                                  afecta ninguna cifra ya publicada.
# Sin este ajuste, estas 4 entidades habrían vuelto a heredar el mismo bug
# de color gris de respaldo / "sin datos" falso que ya se había corregido.

BANCOS_SISTEMA = [
    'Amazonas',
    'Atlantida',
    'Austro',
    'Bolivariano',
    'Capital',
    'Citibank',
    'Codesarrollo',
    'Comercial de Manabí',
    'Coopnacional',
    'DelBank',
    'Diners',
    'General Rumiñahui',
    'Guayaquil',
    'Internacional',
    'Litoral',
    'Loja',
    'Machala',
    'Pacifico',
    'Pichincha',
    'Procredit',
    'Produbanco',
    'Solidario',
    'VisionFund',
]

# =============================================================================
# PALETA DE COLORES POR BANCO
# =============================================================================
# Colores únicos y consistentes para cada banco en todas las visualizaciones
# Paleta basada en colores distinguibles y accesibles

COLORES_BANCOS = {
    'Pichincha': '#1f77b4',      # Azul (banco más grande)
    'Guayaquil': '#ff7f0e',      # Naranja
    'Pacifico': '#2ca02c',       # Verde
    'Produbanco': '#d62728',     # Rojo
    'Bolivariano': '#9467bd',    # Púrpura
    'Internacional': '#8c564b',   # Marrón
    'Austro': '#e377c2',         # Rosa
    'Machala': '#7f7f7f',        # Gris
    'Loja': '#bcbd22',           # Verde oliva
    'Solidario': '#17becf',      # Cian
    'General Rumiñahui': '#aec7e8', # Azul claro
    'Diners': '#ffbb78',         # Naranja claro
    'Capital': '#98df8a',        # Verde claro
    'Procredit': '#ff9896',      # Rojo claro
    'Coopnacional': '#c5b0d5',   # Púrpura claro
    'DelBank': '#c49c94',        # Marrón claro
    'Litoral': '#f7b6d2',        # Rosa claro
    'Citibank': '#c7c7c7',       # Gris claro
    'Comercial de Manabí': '#dbdb8d', # Verde oliva claro
    'Codesarrollo': '#9edae5',   # Cian claro
    'VisionFund': '#e7ba52',     # Dorado
    'Atlantida': '#ad494a',      # Rojo oscuro
    'Amazonas': '#de9ed6',       # Rosa medio
}

def obtener_color_banco(banco: str) -> str:
    """Retorna el color asignado a un banco.

    Args:
        banco: Nombre del banco

    Returns:
        Código hexadecimal del color
    """
    return COLORES_BANCOS.get(banco, '#636363')  # Color gris por defecto


# =============================================================================
# INDICADORES CAMEL: escalas de color y rangos de referencia para heatmaps
# =============================================================================
# Migrado desde pages/4_CAMEL.py (antes duplicado ahi como unica fuente).
# Centralizado aqui para que cualquier pagina que visualice indicadores CAMEL
# use la misma convencion de color/rango.

INDICADORES_PRINCIPALES = {
    grupo: [(codigo, ETIQUETAS_INDICADORES.get(codigo, codigo)) for codigo in codigos]
    for grupo, codigos in GRUPOS_INDICADORES.items()
}

ESCALAS_COLORES_HEATMAP = {
    # Mayor es mejor
    'SOL': 'RdYlGn', 'ROA': 'RdYlGn', 'ROE': 'RdYlGn', 'LIQ': 'RdYlGn',
    'AP_PC': 'RdYlGn', 'CAR_ACT': 'RdYlGn',
    'COB_TOT': 'RdYlGn', 'COB_CONS': 'RdYlGn', 'COB_INMOB': 'RdYlGn',
    'COB_INMOB_VIP': 'RdYlGn', 'COB_VIS': 'RdYlGn', 'COB_MICRO': 'RdYlGn',
    'COB_EDU': 'RdYlGn', 'COB_PROD': 'RdYlGn', 'COB_INV_PUB': 'RdYlGn',
    'COB_COM_PRIO': 'RdYlGn', 'COB_CONS_PRIO': 'RdYlGn',

    # Menor es mejor
    'AIN': 'RdYlGn_r', 'GO_MNF': 'RdYlGn_r', 'GO_ACT': 'RdYlGn_r', 'GP_ACT': 'RdYlGn_r',
    'MOR_TOT': 'RdYlGn_r', 'MOR_CONS': 'RdYlGn_r', 'MOR_INMOB': 'RdYlGn_r',
    'MOR_INMOB_VIP': 'RdYlGn_r', 'MOR_VIS': 'RdYlGn_r', 'MOR_MICRO': 'RdYlGn_r',
    'MOR_EDU': 'RdYlGn_r', 'MOR_PROD': 'RdYlGn_r', 'MOR_INV_PUB': 'RdYlGn_r',

    # Neutros
    'INV_ACT': 'Blues', 'DEP_BRECHA': 'Blues', 'DEP_SPREAD': 'Blues',
    'PART_CONS': 'Blues', 'PART_INMOB': 'Blues', 'PART_INMOB_VIP': 'Blues',
    'PART_VIS': 'Blues', 'PART_MICRO': 'Blues', 'PART_EDU': 'Blues',
    'PART_PROD': 'Blues', 'PART_INV_PUB': 'Blues',
}

RANGOS_HEATMAP = {
    'SOL': [0, 20],
    'ROA': [-5, 5], 'ROE': [-20, 30], 'DEP_BRECHA': [0, 10], 'DEP_SPREAD': [0, 10],
    'LIQ': [0, 50],
    'AIN': [0, 40], 'CAR_ACT': [0, 100], 'INV_ACT': [0, 50],
    'MOR_TOT': [0, 10], 'MOR_CONS': [0, 10], 'MOR_INMOB': [0, 10],
    'MOR_INMOB_VIP': [0, 10], 'MOR_VIS': [0, 10], 'MOR_MICRO': [0, 10],
    'MOR_EDU': [0, 10], 'MOR_PROD': [0, 10], 'MOR_INV_PUB': [0, 10],
    'COB_TOT': [0, 300], 'COB_CONS': [0, 300], 'COB_INMOB': [0, 300],
    'COB_INMOB_VIP': [0, 300], 'COB_VIS': [0, 300], 'COB_MICRO': [0, 300],
    'COB_EDU': [0, 300], 'COB_PROD': [0, 300], 'COB_INV_PUB': [0, 300],
    'COB_COM_PRIO': [0, 300], 'COB_CONS_PRIO': [0, 300],
    'PART_CONS': [0, 100], 'PART_INMOB': [0, 100], 'PART_INMOB_VIP': [0, 100],
    'PART_VIS': [0, 100], 'PART_MICRO': [0, 100], 'PART_EDU': [0, 100],
    'PART_PROD': [0, 100], 'PART_INV_PUB': [0, 100],
    'AP_PC': [80, 120], 'GO_MNF': [0, 200], 'GO_ACT': [0, 10], 'GP_ACT': [0, 5],
}
