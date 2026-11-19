"""Validación y almacenamiento persistente de las mediciones."""

import csv
import math
from datetime import datetime
from pathlib import Path


COLUMNAS = ("fecha_hora", "id", "adc", "humedad_pct", "estado")


class RegistroMediciones:
    """Guarda cada medición en CSV y descarta IDs ya registrados."""

    def __init__(self, ruta):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.registros = []
        self._ids = set()
        self._cargar()

    def _cargar(self):
        if not self.ruta.exists():
            with self.ruta.open("w", newline="", encoding="utf-8-sig") as archivo:
                csv.DictWriter(archivo, fieldnames=COLUMNAS).writeheader()
            return

        with self.ruta.open("r", newline="", encoding="utf-8-sig") as archivo:
            lector = csv.DictReader(archivo)
            if lector.fieldnames is None or not set(COLUMNAS).issubset(
                lector.fieldnames
            ):
                raise ValueError(
                    f"El archivo {self.ruta} no tiene las columnas esperadas."
                )
            for fila in lector:
                try:
                    registro = {
                        "fecha_hora": fila["fecha_hora"],
                        "id": fila["id"],
                        "adc": int(fila["adc"]),
                        "humedad_pct": float(fila["humedad_pct"]),
                        "estado": fila["estado"],
                    }
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"Hay una fila inválida en {self.ruta}."
                    ) from error
                self.registros.append(registro)
                self._ids.add(registro["id"])

    def agregar(self, mensaje, umbral_seco):
        """Valida, persiste y devuelve un registro; retorna None si es duplicado."""
        identificador = mensaje.get("id")
        adc = mensaje.get("adc")
        humedad = mensaje.get("humidity")
        if not isinstance(identificador, str) or not identificador:
            raise ValueError("La medición no contiene un identificador válido.")
        if identificador in self._ids:
            return None
        if isinstance(adc, bool) or not isinstance(adc, int) or not 0 <= adc <= 4095:
            raise ValueError("El ADC recibido debe ser un entero entre 0 y 4095.")
        if isinstance(humedad, bool) or not isinstance(humedad, (int, float)):
            raise ValueError("La humedad recibida no es un número.")
        humedad = float(humedad)
        if not math.isfinite(humedad) or not 0 <= humedad <= 100:
            raise ValueError("La humedad recibida debe estar entre 0 y 100 %.")

        registro = {
            "fecha_hora": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "id": identificador,
            "adc": adc,
            "humedad_pct": humedad,
            "estado": "Seca" if humedad < umbral_seco else "Húmeda",
        }
        with self.ruta.open("a", newline="", encoding="utf-8") as archivo:
            csv.DictWriter(archivo, fieldnames=COLUMNAS).writerow(registro)
        self.registros.append(registro)
        self._ids.add(identificador)
        return registro

    def exportar(self, destino):
        """Exporta todo el historial a la ruta seleccionada."""
        with Path(destino).open("w", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
            escritor.writeheader()
            escritor.writerows(self.registros)
