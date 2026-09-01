import unittest

from dashboard_metadata import resumir_metadata


class DashboardMetadataTests(unittest.TestCase):
    def test_resume_portada_desde_metadata_publicada(self):
        resumen = resumir_metadata({
            "fecha_min": "2003-01-31 00:00:00",
            "fecha_max": "2026-06-30 00:00:00",
            "total_bancos": 23,
            "total_registros": 8_152_043,
        })

        self.assertTrue(resumen["completa"])
        self.assertEqual(resumen["bancos"], 23)
        self.assertEqual(resumen["meses"], 282)
        self.assertEqual(resumen["anos"], 23)
        self.assertEqual(resumen["datos_al"], "Jun 2026")
        self.assertEqual(resumen["periodo"], "Enero 2003 - Junio 2026")
        self.assertEqual(resumen["registros"], "8,2 millones")

    def test_no_inventa_cifras_si_falta_metadata(self):
        resumen = resumir_metadata(None)

        self.assertFalse(resumen["completa"])
        self.assertEqual(resumen["bancos"], "N/D")
        self.assertEqual(resumen["datos_al"], "N/D")


if __name__ == "__main__":
    unittest.main()
