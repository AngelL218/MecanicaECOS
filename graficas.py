"""Gráfica de humedad dibujada con Canvas, sin dependencias externas."""


class GraficaHumedad:
    """Representa el historial porcentual dentro de un Canvas de Tkinter."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.registros = []
        self.canvas.bind("<Configure>", lambda _evento: self.dibujar())

    def actualizar(self, registros):
        self.registros = list(registros)
        self.dibujar()

    def dibujar(self):
        lienzo = self.canvas
        lienzo.delete("all")
        ancho = max(lienzo.winfo_width(), 360)
        alto = max(lienzo.winfo_height(), 220)
        izquierda, derecha, arriba, abajo = 54, ancho - 20, 20, alto - 38
        if derecha <= izquierda or abajo <= arriba:
            return

        for porcentaje in (0, 25, 50, 75, 100):
            y = abajo - (abajo - arriba) * porcentaje / 100
            lienzo.create_line(izquierda, y, derecha, y, fill="#dce6df")
            lienzo.create_text(
                izquierda - 9, y, text=str(porcentaje), anchor="e",
                fill="#52675c",
            )
        lienzo.create_line(izquierda, arriba, izquierda, abajo, fill="#718579")
        lienzo.create_line(izquierda, abajo, derecha, abajo, fill="#718579")
        lienzo.create_text(
            (izquierda + derecha) / 2, alto - 12,
            text="Mediciones (más recientes a la derecha)",
            fill="#52675c",
        )

        puntos = self.registros[-100:]
        if not puntos:
            lienzo.create_text(
                (izquierda + derecha) / 2, (arriba + abajo) / 2,
                text="Esperando la primera medición",
                fill="#52675c",
            )
            return

        coordenadas = []
        for indice, registro in enumerate(puntos):
            proporcion = indice / max(len(puntos) - 1, 1)
            x = izquierda + proporcion * (derecha - izquierda)
            y = abajo - (abajo - arriba) * registro["humedad_pct"] / 100
            coordenadas.extend((x, y))
        if len(puntos) > 1:
            lienzo.create_line(
                *coordenadas, fill="#247ba0", width=2, smooth=True
            )
        for x, y in zip(coordenadas[::2], coordenadas[1::2]):
            lienzo.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill="#14532d", outline="white",
            )
