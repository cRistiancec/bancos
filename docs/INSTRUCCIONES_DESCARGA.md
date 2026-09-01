# Instrucciones Detalladas para Descargas Futuras

Esta guía te ayudará a replicar el proceso de descarga para períodos futuros (Enero 2026, Febrero 2026, etc.).

## 📅 Calendario de Actualizaciones

- **Enero 2026**: Cambiar a carpeta "Año 2026"
- **Febrero 2026**: Mantener carpeta "Año 2026", actualizar período
- **Marzo - Diciembre 2026**: Mantener carpeta "Año 2026", actualizar período
- **Enero 2027**: Cambiar a carpeta "Año 2027"
- Y así sucesivamente...

## 🔄 Proceso Paso a Paso

### 1. Verificar Disponibilidad de Datos

Antes de ejecutar el script, verifica manualmente que los datos estén disponibles:

1. Visita: https://www.superbancos.gob.ec/estadisticas/portalestudios/bancos-2/
2. Navega: **Inicio** > **Año 2026** (o el año correspondiente) > **Boletines de series por entidad Bancos Privados**
3. Verifica que veas los archivos ZIP de todos los bancos

### 2. Actualizar Configuración

Abre el archivo [`scripts/config.py`](../scripts/config.py) y actualiza estas líneas:

```python
# ============================================================================
# CONFIGURACIÓN PRINCIPAL - ACTUALIZAR PARA CADA NUEVA DESCARGA
# ============================================================================

# Año de la carpeta a buscar (cambia cada enero)
ANO_BUSCAR = "2026"  # Cambiar de "2025" a "2026" en enero 2026

# Mes y año para el nombre de la carpeta de salida
PERIODO_DESCARGA = "enero_2026"  # Formato: mes_año (ej: "febrero_2026", "marzo_2026")
```

**Ejemplos de configuración por período:**

- **Enero 2026**:
  ```python
  ANO_BUSCAR = "2026"
  PERIODO_DESCARGA = "enero_2026"
  ```

- **Febrero 2026**:
  ```python
  ANO_BUSCAR = "2026"
  PERIODO_DESCARGA = "febrero_2026"
  ```

- **Diciembre 2026**:
  ```python
  ANO_BUSCAR = "2026"
  PERIODO_DESCARGA = "diciembre_2026"
  ```

- **Enero 2027**:
  ```python
  ANO_BUSCAR = "2027"
  PERIODO_DESCARGA = "enero_2027"
  ```

### 3. Ejecutar el Script

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
python descargar.py
```

**Qué esperarás ver:**

```
================================================================================
CONFIGURACIÓN ACTUAL
================================================================================
  Año a buscar: 2026
  Período: enero_2026
  Carpeta de salida: datos_bancos_enero_2026
  Bancos esperados: 24
  URL: https://www.superbancos.gob.ec/estadisticas/portalestudios/bancos-2/
================================================================================

¿Proceder con la descarga de boletines de enero_2026?
Iniciando descarga automáticamente...

Iniciando navegador Chrome...

[1/5] Navegando a https://www.superbancos.gob.ec/...
[2/5] Buscando y haciendo clic en 'Año 2026'...
  ✓ Clic exitoso en 'Año 2026'
[3/5] Buscando carpeta de boletines...
  ✓ Clic exitoso en 'Boletines de series por entidad Bancos Privados'
[4/5] Cargando archivos...
[5/5] Extrayendo enlaces de descarga...
  Archivos encontrados: 24

================================================================================
ARCHIVOS ENCONTRADOS: 24
================================================================================

  1. Series Banco Visionfund ENERO 2026.zip
  2. Series Banco Solidario ENERO 2026.zip
  ...
 24. Series Banco Amazonas ENERO 2026.zip

================================================================================
DESCARGANDO 24 ARCHIVOS
Carpeta: c:\...\bancos\datos_bancos_enero_2026
================================================================================

[  1/24] Series Banco Visionfund ENERO 2026.zip    ... ✓ ( 1.86 MB)
[  2/24] Series Banco Solidario ENERO 2026.zip     ... ✓ ( 4.87 MB)
...
[24/24] Series Banco Amazonas ENERO 2026.zip      ... ✓ ( 4.83 MB)

✓ TODOS LOS ARCHIVOS SE DESCARGARON CORRECTAMENTE

================================================================================
DESCOMPRIMIENDO ARCHIVOS ZIP
================================================================================

[  1/24] Amazonas ENERO 2026                       ... ✓ (1 Excel)
...
[24/24] Visionfund ENERO 2026                     ... ✓ (1 Excel)

✓ TODOS LOS ARCHIVOS SE DESCOMPRIMIERON CORRECTAMENTE

📊 RESUMEN DE ARCHIVOS EXCEL:
================================================================================
  Amazonas ENERO 2026                                1 archivo(s)
  ...
  Visionfund ENERO 2026                              1 archivo(s)
================================================================================
  TOTAL ARCHIVOS EXCEL: 24
================================================================================

Cerrando navegador en 10 segundos...
```

### 4. Verificar la Descarga

#### A. Verificar Cantidad de Archivos

```bash
# Contar archivos ZIP
ls datos_bancos_enero_2026/*.zip | wc -l
# Debe mostrar: 24 (o el número actual de bancos)

# Contar archivos Excel
ls datos_bancos_enero_2026/archivos_excel/*/*.xlsx | wc -l
# Debe mostrar: 24 (o el número actual de bancos)
```

#### B. Verificar Tamaños de Archivos

Los archivos deben tener tamaños **DIFERENTES**:

```bash
ls -lh datos_bancos_enero_2026/archivos_excel/*/
```

**Ejemplo de salida correcta:**
```
Visionfund ENERO 2026.xlsx    1.9M
Solidario ENERO 2026.xlsx     4.9M
Pichincha ENERO 2026.xlsx     5.9M
...
```

**⚠️ IMPORTANTE**: Si todos los archivos tienen el mismo tamaño, hay un problema con la descarga.

#### C. Verificar Contenido (Opcional)

Abre algunos archivos Excel de diferentes bancos y verifica que:
- Los datos sean del banco correcto
- Los datos sean del período correcto (Enero 2026)
- Los valores sean diferentes entre bancos

### 5. Organizar Archivos

El script crea automáticamente la siguiente estructura:

```
datos_bancos_enero_2026/
├── Series Banco Amazonas ENERO 2026.zip
├── Series Banco Pichincha ENERO 2026.zip
├── ... (24 archivos ZIP)
└── archivos_excel/
    ├── Amazonas ENERO 2026/
    │   └── Amazonas ENERO 2026.xlsx
    ├── Pichincha ENERO 2026/
    │   └── Pichincha ENERO 2026.xlsx
    └── ... (24 carpetas)
```

**Opcional**: Si quieres mover a una ubicación específica:

```bash
# Mover a carpeta de descargas organizada
mkdir -p descargas/2026_enero
mv datos_bancos_enero_2026 descargas/2026_enero/
```

## 🔧 Configuración Avanzada

### Ajustar Tiempos de Espera

Si tu conexión es lenta o el sitio tarda en cargar, ajusta estos valores en [`scripts/config.py`](../scripts/config.py):

```python
# Tiempos de espera (en segundos)
TIEMPO_CARGA_PAGINA = 10      # Era 8, aumentar si la página tarda
TIEMPO_DESPUES_CLIC = 12      # Era 10, aumentar si el clic no funciona
TIEMPO_CARGA_ARCHIVOS = 20    # Era 15, aumentar si no carga todos los archivos
TIEMPO_ENTRE_SCROLL = 3       # Era 2, aumentar en conexiones lentas
```

### Modo Headless (Sin Ventana)

Para ejecutar sin que se abra la ventana de Chrome:

```python
# config.py
CHROME_HEADLESS = True  # Cambiar de False a True
```

### Cambiar Número Esperado de Bancos

Si la Superintendencia agrega o elimina bancos:

```python
# config.py
NUMERO_ESPERADO_BANCOS = 25  # Actualizar según corresponda
```

## 🐛 Solución de Problemas

### Problema: No encuentra "Año 2026"

**Error**:
```
✗ No se encontró la carpeta 'Año 2026'
```

**Soluciones**:
1. Verifica manualmente que la carpeta exista en el portal
2. Verifica que `ANO_BUSCAR` esté correcto en `config.py`
3. Espera unos días si es principio de año (pueden tardar en crear la carpeta)

### Problema: Encuentra 0 archivos

**Error**:
```
[ERROR] No se encontraron archivos con URLs de descarga.
```

**Soluciones**:
1. Verifica manualmente que los archivos existan en el portal
2. Aumenta `TIEMPO_CARGA_ARCHIVOS` en `config.py`
3. Verifica tu conexión a internet
4. Intenta de nuevo más tarde

### Problema: Se descargan menos de 24 archivos

**Advertencia**:
```
⚠️  ADVERTENCIA: Se esperaban 24 bancos, pero se encontraron 22
```

**Soluciones**:
1. Esto puede ser normal si hubo fusiones o cierres de bancos
2. Verifica manualmente cuántos bancos hay en el portal
3. Actualiza `NUMERO_ESPERADO_BANCOS` en `config.py` si es necesario

### Problema: Archivos Excel todos iguales

**Síntomas**: Todos los archivos tienen el mismo tamaño o contienen datos del mismo banco.

**Solución**:
1. ✅ Este problema está resuelto en la versión 2.0 del script
2. Asegúrate de estar usando `descargar.py` actualizado
3. Si persiste, contacta al mantenedor del proyecto

### Problema: Error de ChromeDriver

**Error**:
```
WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

**Solución**:
```bash
pip install --upgrade webdriver-manager
```

## 📝 Checklist de Descarga

Usa este checklist cada vez que descargues datos de un nuevo período:

- [ ] Verificar que los datos estén disponibles en el portal web
- [ ] Actualizar `ANO_BUSCAR` en `config.py`
- [ ] Actualizar `PERIODO_DESCARGA` en `config.py`
- [ ] Ejecutar `python descargar.py`
- [ ] Verificar que se descarguen 24 archivos (o el número esperado)
- [ ] Verificar que los archivos tengan tamaños diferentes
- [ ] Verificar contenido de al menos 2-3 archivos Excel diferentes
- [ ] Mover archivos a ubicación final (si aplica)
- [ ] Actualizar documentación si hubo cambios en el proceso

## 🤝 Mantenimiento del Script

Si en el futuro el script deja de funcionar, probablemente se deba a cambios en la estructura del sitio web. En ese caso:

1. **Verificar selectores**: Los selectores XPath pueden haber cambiado
2. **Verificar IDs**: Los parámetros de URL (account_id, drive_id) pueden haber cambiado
3. **Contactar soporte**: Si no puedes resolver el problema

### Archivos clave del proyecto

- `descargar.py`: Script principal (contiene la lógica de descarga)
- `config.py`: Configuración (actualizar aquí año y período)
- `descomprimir_zips.py`: Script auxiliar para solo descomprimir

## 📞 Recursos Adicionales

- **Portal**: https://www.superbancos.gob.ec/estadisticas/portalestudios/bancos-2/
- **README**: [README.md](README.md) - Documentación completa
- **Guía Rápida**: [GUIA_RAPIDA.md](GUIA_RAPIDA.md) - Referencia rápida

---

**Última actualización**: 22 de enero de 2025
**Versión**: 2.0
**Mantenedor**: Actualizar según necesidad
