"""Punto de entrada de la aplicación de monitoreo EcoSuelo."""

import math


MAXIMO_BLOQUES = 2000


def crear_bloques(largo, ancho, tamano_bloque):
    """Divide un terreno en bloques y calcula el centro de cada uno."""
    if largo <= 0 or ancho <= 0 or tamano_bloque <= 0:
        raise ValueError("Las dimensiones y el bloque deben ser positivos.")

    columnas = math.ceil(largo / tamano_bloque - 1e-12)
    filas = math.ceil(ancho / tamano_bloque - 1e-12)
    if filas * columnas > MAXIMO_BLOQUES:
        raise ValueError(
            f"El terreno supera el límite de {MAXIMO_BLOQUES} bloques."
        )

    bloques = []
    for fila in range(filas):
        y_inicio = fila * tamano_bloque
        y_final = min(y_inicio + tamano_bloque, ancho)
        for columna in range(columnas):
            x_inicio = columna * tamano_bloque
            x_final = min(x_inicio + tamano_bloque, largo)
            bloques.append({
                "numero": fila * columnas + columna + 1,
                "fila": fila,
                "columna": columna,
                "x": (x_inicio + x_final) / 2,
                "y": (y_inicio + y_final) / 2,
                "largo": x_final - x_inicio,
                "ancho": y_final - y_inicio,
            })
    return bloques


def crear_ruta_serpentina(bloques):
    """Ordena bloques por filas alternando el sentido de recorrido."""
    ruta = []
    filas = sorted({bloque["fila"] for bloque in bloques})
    for fila in filas:
        bloques_fila = sorted(
            (bloque for bloque in bloques if bloque["fila"] == fila),
            key=lambda bloque: bloque["columna"],
        )
        if fila % 2:
            bloques_fila.reverse()
        ruta.extend(bloques_fila)
    return ruta


def clasificar_humedad(humedad, limite_bajo, limite_alto):
    """Conserva la clasificación usada por la versión de simulación."""
    if humedad is None:
        return "Sin medir"
    if humedad < limite_bajo:
        return "Baja"
    if humedad < limite_alto:
        return "Media"
    return "Alta"


def iniciar_aplicacion():
    """Crea y ejecuta la interfaz Tkinter de monitoreo USB."""
    from interfaz import iniciar_aplicacion as ejecutar_interfaz

    ejecutar_interfaz()


if __name__ == "__main__":
    iniciar_aplicacion()
