import json
import tempfile
import unittest
from pathlib import Path
import sys
import zipfile

import pandas as pd
from openpyxl import Workbook


ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import fuente_bancos
import validar_actualizacion as validador

# scripts/config.py (config del scraper) y el paquete config/ de la app
# (config/indicator_mapping.py, etc.) comparten el nombre "config". Al
# correr la suite completa en un solo proceso, el "import config" de
# validar_actualizacion cachea scripts/config.py bajo sys.modules['config'],
# lo que rompe "from config.indicator_mapping import ..." en los demas
# modulos de prueba que se coleccionan despues. Se revierte el path y se
# limpia el cache para no filtrar este "config" al resto de la suite.
sys.path.remove(str(ROOT / "scripts"))
sys.modules.pop("config", None)


def crear_excel(ruta: Path, fecha: str, omitir: str | None = None):
    libro = Workbook()
    libro.remove(libro.active)
    for nombre in fuente_bancos.HOJAS_REQUERIDAS:
        if nombre == omitir:
            continue
        hoja = libro.create_sheet(nombre)
        hoja.cell(5, 3, pd.Timestamp(fecha).to_pydatetime())
    libro.save(ruta)


class FuenteBancosTests(unittest.TestCase):
    def test_inspeccion_exige_tres_hojas_y_fecha_uniforme(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "Banco.xlsx"
            crear_excel(ruta, "2026-06-30")
            inspeccion = fuente_bancos.inspeccionar_excel_banco(ruta)
            self.assertEqual(inspeccion.fecha_corte, pd.Timestamp("2026-06-30"))
            self.assertEqual(set(inspeccion.fechas_maximas), {"BAL", "PYG", "CAMEL"})

    def test_inspeccion_rechaza_hoja_faltante(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "Banco.xlsx"
            crear_excel(ruta, "2026-06-30", omitir="PYG")
            with self.assertRaisesRegex(ValueError, "PYG"):
                fuente_bancos.inspeccionar_excel_banco(ruta)

    def test_directorio_rechaza_fechas_mezcladas(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            crear_excel(base / "A.xlsx", "2026-06-30")
            crear_excel(base / "B.xlsx", "2026-05-31")
            with self.assertRaisesRegex(ValueError, "fecha de corte uniforme"):
                fuente_bancos.validar_directorio_fuentes(
                    base, pd.Timestamp("2026-06-30"), bancos_esperados=2
                )

    def test_zip_debe_contener_un_unico_xlsx(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "fuente.zip"
            with zipfile.ZipFile(ruta, "w") as archivo:
                archivo.writestr("A.xlsx", b"uno")
                archivo.writestr("B.xlsx", b"dos")
            with self.assertRaisesRegex(ValueError, "unico XLSX"):
                fuente_bancos.validar_zip(ruta)


class ValidadorPublicacionTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.master = Path(self.temporal.name)
        self.master_original = validador.MASTER_DATA_DIR
        validador.MASTER_DATA_DIR = self.master
        self.addCleanup(setattr, validador, "MASTER_DATA_DIR", self.master_original)

    def escribir_datasets(self, pyg_rezagado=False):
        bancos = ["A", "B"]
        fechas = pd.to_datetime(["2026-05-31", "2026-06-30"])

        balance = pd.DataFrame([
            {"banco": banco, "fecha": fecha, "codigo": "1", "cuenta": "ACTIVO",
             "valor": 1.0, "nivel": 1}
            for banco in bancos for fecha in fechas
        ])
        pyg = pd.DataFrame([
            {"banco": banco, "fecha": fecha, "codigo": "GDE", "cuenta": "GANANCIA",
             "valor_acumulado": 1.0, "valor_mes": 1.0, "valor_12m": 1.0}
            for banco in bancos
            for fecha in fechas
            if not (pyg_rezagado and banco == "B" and fecha == fechas[-1])
        ])
        camel = pd.DataFrame([
            {"banco": banco, "fecha": fecha, "codigo": "ROE", "indicador": "ROE",
             "valor": 0.1, "categoria": "E"}
            for banco in bancos for fecha in fechas
        ])
        balance.to_parquet(self.master / "balance.parquet", index=False)
        pyg.to_parquet(self.master / "pyg.parquet", index=False)
        camel.to_parquet(self.master / "camel.parquet", index=False)
        (self.master / "metadata.json").write_text(json.dumps({
            "fecha_max": "2026-06-30 00:00:00",
            "bancos_error": [],
        }), encoding="utf-8")

    def test_valida_tres_datasets_completos(self):
        self.escribir_datasets()
        estado = validador.validar_actualizacion(
            pd.Timestamp("2026-06-30"), bancos_esperados=2
        )
        self.assertEqual(estado["pyg"]["bancos_ultimo_mes"], ["A", "B"])

    def test_rechaza_banco_rezagado_en_pyg(self):
        self.escribir_datasets(pyg_rezagado=True)
        with self.assertRaisesRegex(ValueError, "pyg: solo 1 bancos"):
            validador.validar_actualizacion(
                pd.Timestamp("2026-06-30"), bancos_esperados=2
            )

    def test_rechaza_perdida_de_historia(self):
        self.escribir_datasets()
        anterior = validador.capturar_estado()
        anterior["balance"]["meses"].insert(0, "2026-04")
        with self.assertRaisesRegex(ValueError, "perdio meses publicados"):
            validador.validar_actualizacion(
                pd.Timestamp("2026-06-30"), anterior, bancos_esperados=2
            )


if __name__ == "__main__":
    unittest.main()
