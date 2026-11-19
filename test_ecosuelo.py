import csv
import tempfile
import unittest
from pathlib import Path

from comunicacion import analizar_linea
from mediciones import RegistroMediciones


class PruebasComunicacion(unittest.TestCase):
    def test_decodifica_mensaje_de_medicion(self):
        mensaje = analizar_linea(
            '{"type":"measurement","id":"abc-1","adc":2100,"humidity":48.5}'
        )

        self.assertEqual(mensaje["id"], "abc-1")
        self.assertEqual(mensaje["adc"], 2100)

    def test_rechaza_json_sin_tipo(self):
        with self.assertRaises(ValueError):
            analizar_linea('{"adc":2100}')


class PruebasRegistroMediciones(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.directorio.cleanup)
        ruta = Path(self.directorio.name) / "historial.csv"
        self.registro = RegistroMediciones(ruta)

    def test_persiste_una_medicion_y_descarta_el_id_duplicado(self):
        mensaje = {
            "id": "boot-1",
            "adc": 2500,
            "humidity": 29.5,
        }

        primera = self.registro.agregar(mensaje, 30)
        duplicada = self.registro.agregar(mensaje, 30)

        self.assertEqual(primera["estado"], "Seca")
        self.assertIsNone(duplicada)
        with self.registro.ruta.open(
            "r", newline="", encoding="utf-8-sig"
        ) as archivo:
            filas = list(csv.DictReader(archivo))
        self.assertEqual(len(filas), 1)

    def test_rechaza_valores_adc_fuera_de_rango(self):
        with self.assertRaises(ValueError):
            self.registro.agregar(
                {"id": "boot-2", "adc": 4096, "humidity": 50}, 30
            )

    def test_reconoce_ids_ya_guardados_tras_reabrir_el_csv(self):
        mensaje = {"id": "boot-3", "adc": 1500, "humidity": 70}
        self.registro.agregar(mensaje, 30)
        reiniciado = RegistroMediciones(self.registro.ruta)

        self.assertIsNone(reiniciado.agregar(mensaje, 30))


if __name__ == "__main__":
    unittest.main()
