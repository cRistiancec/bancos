#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script Maestro para Descarga de Boletines de Bancos
Superintendencia de Bancos del Ecuador

USO:
    python descargar.py

CONFIGURACION:
    Edita config.py antes de ejecutar
"""

import sys
import os
import re
import calendar
from datetime import datetime
from pathlib import Path

try:
    import config
    from fuente_bancos import validar_directorio_fuentes, validar_zip
except ImportError:
    print("ERROR: No se encontro el archivo config.py")
    print("Asegurate de estar en la carpeta correcta del proyecto")
    sys.exit(1)

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    import requests
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time
    import zipfile
    import shutil
except ImportError as e:
    print("ERROR: Faltan dependencias necesarias")
    print(f"Detalle: {e}")
    print("\nInstala las dependencias con:")
    print("  pip install selenium requests")
    sys.exit(1)


def main():
    """Funcion principal del descargador"""

    print("\n")
    config.mostrar_configuracion()

    if not config.validar_configuracion():
        sys.exit(1)

    print(f"\nIniciando descarga de {config.PERIODO_DESCARGA}...")

    chrome_options = Options()

    if config.CHROME_MAXIMIZADO:
        chrome_options.add_argument("--start-maximized")

    if config.CHROME_HEADLESS:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # En GitHub Actions, apuntar al Chrome instalado por browser-actions/setup-chrome
    if os.environ.get('GITHUB_ACTIONS'):
        chrome_path = os.environ.get('CHROME_PATH', '')
        if chrome_path and os.path.isfile(chrome_path):
            chrome_options.binary_location = chrome_path
        else:
            for candidate in [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
            ]:
                if os.path.isfile(candidate):
                    chrome_options.binary_location = candidate
                    print(f"Chrome detectado en: {candidate}")
                    break

    carpeta_final = Path(os.getcwd()) / config.get_carpeta_salida()
    carpeta_temporal = carpeta_final.with_name(f"{carpeta_final.name}.tmp")
    if carpeta_temporal.exists():
        shutil.rmtree(carpeta_temporal)
    carpeta_temporal.mkdir(parents=True)
    download_dir = str(carpeta_temporal)

    # Selenium Manager integrado desde Selenium 4.6+ - no requiere webdriver_manager
    print(f"\nIniciando navegador Chrome (Selenium Manager)...")
    driver = webdriver.Chrome(options=chrome_options)

    archivos_encontrados = []

    try:
        print(f"\n[1/5] Navegando a {config.URL_PORTAL}")
        driver.get(config.URL_PORTAL)
        time.sleep(config.TIEMPO_CARGA_PAGINA)
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(config.TIEMPO_ENTRE_SCROLL)

        print(f"[2/5] Buscando 'Anio {config.ANO_BUSCAR}'...")
        xpath_ano = config.get_ano_xpath()
        ano_elements = []
        for intento in range(6):
            ano_elements = driver.find_elements(By.XPATH, xpath_ano)
            if ano_elements:
                break
            print(f"  Esperando contenido dinamico... (intento {intento + 1}/6)")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(5)

        if not ano_elements:
            print(f"  Recargando pagina...")
            driver.refresh()
            time.sleep(config.TIEMPO_CARGA_PAGINA + 10)
            driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(5)
            for intento in range(3):
                ano_elements = driver.find_elements(By.XPATH, xpath_ano)
                if ano_elements:
                    break
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(5)

        if not ano_elements:
            all_entries = driver.find_elements(By.XPATH, "//*[contains(text(), 'Anio')]")
            if all_entries:
                print(f"  Carpetas encontradas:")
                for e in all_entries:
                    print(f"    - {e.text}")
            else:
                page_text = driver.find_element(By.TAG_NAME, "body").text[:500]
                print(f"  Contenido visible: {page_text[:200]}")
            raise Exception(f"Carpeta 'Anio {config.ANO_BUSCAR}' no encontrada")

        for elem in ano_elements:
            try:
                clickeable = elem
                for _ in range(5):
                    parent = clickeable.find_element(By.XPATH, "./..")
                    class_attr = parent.get_attribute('class') or ''
                    if 'entry' in class_attr or 'folder' in class_attr:
                        clickeable = parent
                        break
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickeable)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", clickeable)
                print(f"  Clic exitoso en 'Anio {config.ANO_BUSCAR}'")
                time.sleep(config.TIEMPO_DESPUES_CLIC)
                break
            except:
                continue

        print(f"[3/5] Buscando carpeta de boletines...")
        time.sleep(5)
        boletines_elements = driver.find_elements(By.XPATH,
            f"//*[contains(text(), '{config.CARPETA_BOLETINES_TEXTO}')]")

        if not boletines_elements:
            raise Exception("Carpeta de boletines no encontrada")

        for elem in boletines_elements:
            try:
                elem_text = elem.text
                if 'entid' in elem_text.lower() or 'bancos' in elem_text.lower():
                    clickeable = elem
                    for _ in range(5):
                        parent = clickeable.find_element(By.XPATH, "./..")
                        class_attr = parent.get_attribute('class') or ''
                        if 'entry' in class_attr or 'folder' in class_attr:
                            clickeable = parent
                            break
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickeable)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", clickeable)
                    print(f"  Clic exitoso en '{elem_text[:50]}'")
                    time.sleep(config.TIEMPO_CARGA_ARCHIVOS)
                    break
            except:
                continue

        print(f"[4/5] Cargando archivos...")
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(config.TIEMPO_ENTRE_SCROLL)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(config.TIEMPO_ENTRE_SCROLL)
        time.sleep(10)

        print(f"[5/5] Extrayendo enlaces de descarga...")
        script = """
        var entries = document.querySelectorAll('.entry');
        var results = [];
        entries.forEach(function(entry) {
            var nameElem = entry.querySelector('.entry_link.entry_action_download');
            if (nameElem && nameElem.textContent.includes('Series Banco') && nameElem.textContent.includes('.zip')) {
                var dataId = entry.getAttribute('data-id');
                if (dataId) results.push({nombre: nameElem.textContent.trim(), id: dataId});
            }
        });
        return results;
        """
        archivos_javascript = driver.execute_script(script)
        print(f"  Archivos encontrados: {len(archivos_javascript)}")

        for archivo in archivos_javascript:
            download_url = (
                f"https://www.superbancos.gob.ec/estadisticas/portalestudios/wp-admin/admin-ajax.php?"
                f"action=shareonedrive-download&id={archivo['id']}"
                f"&account_id=341c37a6-daa9-4b83-adad-506b00ccb984"
                f"&drive_id=b!Iz-mji9B1EqK1eiAuGWU7x82x3m7uftFja_xK_rSLWY6gLR41EOqTYg222Ho8lwD"
                f"&listtoken=cb2dcac486c20e9c7a63b3bc95e58f46"
            )
            archivos_encontrados.append({'nombre': archivo['nombre'], 'url': download_url, 'id': archivo['id']})

        archivos_unicos = {}
        for archivo in archivos_encontrados:
            if archivo['nombre'] not in archivos_unicos:
                archivos_unicos[archivo['nombre']] = archivo
        archivos_encontrados = list(archivos_unicos.values())

        print(f"\nARCHIVOS ENCONTRADOS: {len(archivos_encontrados)}")

        if len(archivos_encontrados) == 0:
            raise RuntimeError("No se encontraron archivos de descarga")

        for idx, f in enumerate(archivos_encontrados, 1):
            print(f"{idx:3}. {f['nombre'][:70]}")

        if len(archivos_encontrados) != config.NUMERO_ESPERADO_BANCOS:
            raise RuntimeError(f"Se esperaban {config.NUMERO_ESPERADO_BANCOS} bancos, encontrados {len(archivos_encontrados)}")

        print(f"\nDESCARGANDO {len(archivos_encontrados)} ARCHIVOS...")
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

        exitosos = 0
        fallidos = 0

        for idx, archivo in enumerate(archivos_encontrados, 1):
            filepath_temporal = None
            try:
                nombre_corto = archivo['nombre'][:45]
                print(f"[{idx:3}/{len(archivos_encontrados)}] {nombre_corto:45} ... ", end='', flush=True)
                response = session.get(archivo['url'], stream=True, timeout=config.TIMEOUT_DESCARGA)
                response.raise_for_status()
                filename = archivo['nombre']
                if not filename.endswith('.zip'):
                    filename += '.zip'
                filepath = os.path.join(download_dir, filename)
                filepath_temporal = f"{filepath}.part"
                with open(filepath_temporal, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=config.CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                validar_zip(Path(filepath_temporal))
                os.replace(filepath_temporal, filepath)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"OK ({size_mb:5.2f} MB)")
                exitosos += 1
            except Exception as e:
                print(f"FALLO {str(e)[:30]}")
                if filepath_temporal and os.path.exists(filepath_temporal):
                    os.remove(filepath_temporal)
                fallidos += 1

        if exitosos != len(archivos_encontrados):
            raise RuntimeError(f"{fallidos} archivo(s) fallaron durante la descarga")

        print(f"\nDESCOMPRIMIENDO ARCHIVOS ZIP...")
        extracted_dir = os.path.join(download_dir, 'archivos_excel')
        os.makedirs(extracted_dir, exist_ok=True)
        archivos_zip = [f for f in os.listdir(download_dir) if f.endswith('.zip')]
        descomprimidos = 0
        errores_zip = 0

        for idx, zip_filename in enumerate(archivos_zip, 1):
            try:
                zip_path = os.path.join(download_dir, zip_filename)
                validar_zip(Path(zip_path))
                banco_name = re.sub(r'^Series\s*Banco\s*', '', zip_filename.replace('.zip', ''), flags=re.IGNORECASE)
                print(f"[{idx:3}/{len(archivos_zip)}] {banco_name[:45]:45} ... ", end='', flush=True)
                banco_dir = os.path.join(extracted_dir, banco_name)
                os.makedirs(banco_dir, exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(banco_dir)
                files = os.listdir(banco_dir)
                excel_files = [f for f in files if f.endswith(('.xlsx', '.xls'))]
                for excel_file in excel_files:
                    old_path = os.path.join(banco_dir, excel_file)
                    new_path = os.path.join(banco_dir, f"{banco_name}.xlsx")
                    if old_path != new_path:
                        os.rename(old_path, new_path)
                print(f"OK ({len(excel_files)} Excel)")
                descomprimidos += 1
            except Exception as e:
                print(f"FALLO {str(e)[:30]}")
                errores_zip += 1

        fecha_esperada = datetime(
            config.ANO_OBJETIVO,
            config.MES_OBJETIVO,
            calendar.monthrange(config.ANO_OBJETIVO, config.MES_OBJETIVO)[1],
        )
        inspecciones = validar_directorio_fuentes(
            Path(extracted_dir),
            fecha_esperada=fecha_esperada,
            bancos_esperados=config.NUMERO_ESPERADO_BANCOS,
        )
        fecha_fuente = inspecciones[0].fecha_corte
        print(f"Fecha de corte validada: {fecha_fuente:%Y-%m-%d}")

        if fecha_fuente < fecha_esperada:
            print(f"La fuente llega a {fecha_fuente:%Y-%m-%d}; esperada {fecha_esperada:%Y-%m-%d}. Sin datos nuevos.")
            shutil.rmtree(carpeta_temporal, ignore_errors=True)
            sys.exit(2)

        sufijo_respaldo = datetime.now().strftime("%Y%m%d%H%M%S")
        carpeta_respaldo = carpeta_final.with_name(f"{carpeta_final.name}.bak-{sufijo_respaldo}-{os.getpid()}")
        if carpeta_final.exists():
            carpeta_final.replace(carpeta_respaldo)
        try:
            carpeta_temporal.replace(carpeta_final)
        except Exception:
            if carpeta_respaldo.exists() and not carpeta_final.exists():
                carpeta_respaldo.replace(carpeta_final)
            raise
        if carpeta_respaldo.exists():
            shutil.rmtree(carpeta_respaldo, ignore_errors=True)
        print(f"Fuente validada y publicada en: {carpeta_final}")

    except KeyboardInterrupt:
        print("\nDescarga cancelada.")
        sys.exit(0)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        shutil.rmtree(carpeta_temporal, ignore_errors=True)
        sys.exit(1)

    finally:
        if not config.CHROME_HEADLESS:
            time.sleep(10)
        driver.quit()


if __name__ == "__main__":
    main()
