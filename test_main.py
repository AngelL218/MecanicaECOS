import unittest

from main import clasificar_humedad, crear_bloques, crear_ruta_serpentina


class PruebasTerreno(unittest.TestCase):
    def test_bloques_de_orilla_se_recortan_y_miden_su_centro(self):
        bloques = crear_bloques(5, 3, 2)

        self.assertEqual(len(bloques), 6)
        bloque_esquina = bloques[-1]
        self.assertAlmostEqual(bloque_esquina["x"], 4.5)
        self.assertAlmostEqual(bloque_esquina["y"], 2.5)
        self.assertAlmostEqual(bloque_esquina["largo"], 1)
        self.assertAlmostEqual(bloque_esquina["ancho"], 1)

    def test_dimension_decimal_no_crea_bloque_extra(self):
        bloques = crear_bloques(0.3, 0.3, 0.1)

        self.assertEqual(len(bloques), 9)

    def test_rechaza_dimensiones_invalidas(self):
        for dimensiones in ((0, 2, 1), (2, -1, 1), (2, 2, 0)):
            with self.subTest(dimensiones=dimensiones):
                with self.assertRaises(ValueError):
                    crear_bloques(*dimensiones)

    def test_ruta_alterna_la_direccion_en_cada_fila(self):
        bloques = crear_bloques(3, 2, 1)

        self.assertEqual(
            [bloque["numero"] for bloque in crear_ruta_serpentina(bloques)],
            [1, 2, 3, 6, 5, 4],
        )

    def test_limites_de_clasificacion(self):
        self.assertEqual(clasificar_humedad(None, 30, 60), "Sin medir")
        self.assertEqual(clasificar_humedad(29.9, 30, 60), "Baja")
        self.assertEqual(clasificar_humedad(30, 30, 60), "Media")
        self.assertEqual(clasificar_humedad(59.9, 30, 60), "Media")
        self.assertEqual(clasificar_humedad(60, 30, 60), "Alta")


if __name__ == "__main__":
    unittest.main()
