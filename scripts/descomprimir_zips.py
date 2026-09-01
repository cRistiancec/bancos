#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para descomprimir archivos ZIP ya descargados
Útil si ya tienes los ZIPs y solo quieres extraer los archivos Excel
"""

import sys
import os
import re
import zipfile

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def descomprimir_directorio(zip_dir):
    """Descomprime todos los archivos ZIP en un directorio"""

    if not os.path.exists(zip_dir):
        print(f"Error: El directorio {zip_dir} no existe")
        return

    print(f"={'='*80}")
    print(f"DESCOMPRIMIENDO ARCHIVOS ZIP")
    print(f"={'='*80}\n")
    print(f"Directorio: {zip_dir}\n")

    # Crear carpeta para archivos descomprimidos
    extracted_dir = os.path.join(zip_dir, 'archivos_excel')
    os.makedirs(extracted_dir, exist_ok=True)

    # Buscar archivos ZIP
    archivos_zip = [f for f in os.listdir(zip_dir) if f.endswith('.zip')]

    if not archivos_zip:
        print("No se encontraron archivos ZIP en el directorio.")
        return

    print(f"Encontrados {len(archivos_zip)} archivos ZIP\n")

    descomprimidos = 0
    errores = 0

    for idx, zip_filename in enumerate(archivos_zip, 1):
        try:
            zip_path = os.path.join(zip_dir, zip_filename)
            banco_name = re.sub(r'^Series\s*Banco\s*', '', zip_filename.replace('.zip', ''), flags=re.IGNORECASE)

            print(f"[{idx:3}/{len(archivos_zip)}] {banco_name[:50]:50} ... ", end='', flush=True)

            # Crear carpeta para este banco
            banco_dir = os.path.join(extracted_dir, banco_name)
            os.makedirs(banco_dir, exist_ok=True)

            # Descomprimir
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(banco_dir)

            # Renombrar archivos Excel con el nombre del banco
            files = os.listdir(banco_dir)
            excel_files = [f for f in files if f.endswith(('.xlsx', '.xls'))]

            for excel_file in excel_files:
                old_path = os.path.join(banco_dir, excel_file)
                # Nuevo nombre: usar el nombre del banco
                new_name = f"{banco_name}.xlsx"
                new_path = os.path.join(banco_dir, new_name)

                # Renombrar solo si el nombre es diferente
                if old_path != new_path:
                    os.rename(old_path, new_path)

            print(f"✓ ({len(excel_files)} Excel)")
            descomprimidos += 1

        except Exception as e:
            print(f"✗ {str(e)[:40]}")
            errores += 1

    # Resumen
    print(f"\n{'='*80}")
    print(f"DESCOMPRESIÓN COMPLETADA")
    print(f"{'='*80}")
    print(f"  Exitosos:       {descomprimidos}")
    print(f"  Errores:        {errores}")
    print(f"  Total:          {len(archivos_zip)}")
    print(f"\nArchivos Excel extraídos en:")
    print(f"  {extracted_dir}")
    print(f"{'='*80}")

    # Mostrar resumen de archivos Excel por banco
    if descomprimidos > 0:
        print(f"\n📊 RESUMEN POR BANCO:")
        print(f"{'='*80}")

        total_excel = 0
        bancos_con_archivos = []

        for banco_folder in sorted(os.listdir(extracted_dir)):
            banco_path = os.path.join(extracted_dir, banco_folder)
            if os.path.isdir(banco_path):
                archivos = os.listdir(banco_path)
                excel_count = len([f for f in archivos if f.endswith(('.xlsx', '.xls'))])

                if excel_count > 0:
                    total_excel += excel_count
                    bancos_con_archivos.append((banco_folder, excel_count, archivos))
                    print(f"  {banco_folder[:55]:55} {excel_count:3} archivo(s)")

        print(f"{'='*80}")
        print(f"  TOTAL BANCOS:         {len(bancos_con_archivos)}")
        print(f"  TOTAL ARCHIVOS EXCEL: {total_excel}")
        print(f"{'='*80}\n")

        # Mostrar ejemplo de archivos de un banco
        if bancos_con_archivos:
            ejemplo_banco, ejemplo_count, ejemplo_archivos = bancos_con_archivos[0]
            print(f"Ejemplo de archivos extraídos ({ejemplo_banco}):")
            excel_ejemplo = [f for f in ejemplo_archivos if f.endswith(('.xlsx', '.xls'))]
            for f in excel_ejemplo[:5]:
                print(f"  • {f}")
            if len(excel_ejemplo) > 5:
                print(f"  • ... y {len(excel_ejemplo) - 5} más")
            print()

    if descomprimidos == len(archivos_zip):
        print("✓ TODOS LOS ARCHIVOS SE DESCOMPRIMIERON CORRECTAMENTE\n")
    else:
        print(f"⚠️  {errores} archivo(s) tuvieron errores.\n")

if __name__ == "__main__":
    # Directorio por defecto
    default_dir = "descargas/2025_diciembre/datos_bancos_diciembre_2025"

    if len(sys.argv) > 1:
        zip_dir = sys.argv[1]
    else:
        zip_dir = default_dir

    print(f"\n{'='*80}")
    print("Script de Descompresión de ZIPs - Boletines de Bancos")
    print(f"{'='*80}\n")

    descomprimir_directorio(zip_dir)
