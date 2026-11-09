"""Sistema escolar para explorar la humedad del suelo con datos simulados."""

import csv
import math
import random
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk


MAXIMO_BLOQUES = 2000
COLOR_FONDO = "#f3f7f4"
COLOR_VERDE = "#2f855a"
COLOR_VERDE_OSCURO = "#14532d"
COLOR_AZUL = "#247ba0"
COLOR_SECO = "#ef6a62"
COLOR_MEDIO = "#f2c14e"
COLOR_HUMEDO = "#69b578"
COLOR_SIN_MEDIR = "#e8eeea"


def crear_bloques(largo, ancho, tamano_bloque):
    """Divide el terreno y calcula el centro real de cada bloque."""
    if largo <= 0 or ancho <= 0 or tamano_bloque <= 0:
        raise ValueError("Las dimensiones y el bloque deben ser positivos.")

    columnas = math.ceil(largo / tamano_bloque - 1e-12)
    filas = math.ceil(ancho / tamano_bloque - 1e-12)
    if filas * columnas > MAXIMO_BLOQUES:
        raise ValueError(
            f"El terreno supera el límite de {MAXIMO_BLOQUES} bloques."
        )

    bloques = []
    numero = 1
    for fila in range(filas):
        y_inicio = fila * tamano_bloque
        y_final = min(y_inicio + tamano_bloque, ancho)
        if y_final <= y_inicio:
            continue

        for columna in range(columnas):
            x_inicio = columna * tamano_bloque
            x_final = min(x_inicio + tamano_bloque, largo)
            if x_final <= x_inicio:
                continue

            bloques.append({
                "numero": numero,
                "fila": fila,
                "columna": columna,
                "x": (x_inicio + x_final) / 2,
                "y": (y_inicio + y_final) / 2,
                "largo": x_final - x_inicio,
                "ancho": y_final - y_inicio,
            })
            numero += 1
    return bloques


def crear_ruta_serpentina(bloques):
    """Ordena los bloques por filas, alternando la dirección de cada fila."""
    ruta = []
    filas = sorted({bloque["fila"] for bloque in bloques})
    for fila in filas:
        bloques_fila = sorted(
            (bloque for bloque in bloques if bloque["fila"] == fila),
            key=lambda bloque: bloque["columna"],
        )
        if fila % 2 == 1:
            bloques_fila.reverse()
        ruta.extend(bloques_fila)
    return ruta


def clasificar_humedad(humedad, limite_bajo, limite_alto):
    """Devuelve el estado de una lectura simulada."""
    if humedad is None:
        return "Sin medir"
    if humedad < limite_bajo:
        return "Baja"
    if humedad < limite_alto:
        return "Media"
    return "Alta"


class AplicacionHumedad:
    """Interfaz principal de la aplicación."""

    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("EcoSuelo | Monitoreo de humedad")
        self.ventana.geometry("1240x850")
        self.ventana.minsize(800, 600)
        self.ventana.configure(bg=COLOR_FONDO)

        self.nombre_terreno = ""
        self.largo = 0.0
        self.ancho = 0.0
        self.tamano_bloque = 0.0
        self.bloques = []
        self.lecturas = {}
        self.historial = []
        self.ruta_principal = []
        self.modo_ruta = None
        self.limite_bajo = 30.0
        self.limite_alto = 60.0
        self.ordenar_descendente = False

        self.ventana.protocol("WM_DELETE_WINDOW", self.salir_del_sistema)
        self._configurar_estilos()
        self._crear_interfaz()

    def _configurar_estilos(self):
        estilos = ttk.Style()
        estilos.theme_use("clam")
        estilos.configure("TFrame", background=COLOR_FONDO)
        estilos.configure("Card.TFrame", background="white")
        estilos.configure("Header.TFrame", background=COLOR_VERDE_OSCURO)
        estilos.configure("Card.TLabelframe", background="white")
        estilos.configure(
            "Card.TLabelframe.Label", background="white",
            foreground=COLOR_VERDE_OSCURO, font=("Segoe UI", 9, "bold")
        )
        estilos.configure("TLabel", background=COLOR_FONDO, foreground="#23352c")
        estilos.configure(
            "Title.TLabel", font=("Segoe UI", 20, "bold"),
            foreground="white", background=COLOR_VERDE_OSCURO
        )
        estilos.configure(
            "Subtitle.TLabel", font=("Segoe UI", 10),
            foreground="#d8e9de", background=COLOR_VERDE_OSCURO
        )
        estilos.configure(
            "Section.TLabel", font=("Segoe UI", 11, "bold"),
            foreground=COLOR_VERDE_OSCURO, background="white"
        )
        estilos.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(10, 7))
        estilos.configure(
            "Primary.TButton", background=COLOR_VERDE, foreground="white"
        )
        estilos.map(
            "Primary.TButton",
            background=[("active", "#276749"), ("pressed", COLOR_VERDE_OSCURO)],
            foreground=[("disabled", "#dce3e0")],
        )
        estilos.configure(
            "Exit.TButton", background="#fce8e6", foreground="#9b2c2c"
        )
        estilos.map(
            "Exit.TButton",
            background=[("active", "#f8d7d4"), ("pressed", "#f1b8b2")],
        )
        estilos.configure(
            "Treeview", rowheight=27, font=("Segoe UI", 9),
            background="white", fieldbackground="white"
        )
        estilos.configure(
            "Treeview.Heading", font=("Segoe UI", 9, "bold"),
            background="#e6efe9", foreground=COLOR_VERDE_OSCURO,
            padding=(6, 7)
        )
        estilos.configure(
            "TNotebook", background=COLOR_FONDO, borderwidth=0
        )
        estilos.configure(
            "TNotebook.Tab", padding=(16, 9), font=("Segoe UI", 9, "bold")
        )
        estilos.map(
            "TNotebook.Tab",
            background=[("selected", "white"), ("!selected", "#e7eee9")],
            foreground=[("selected", COLOR_VERDE_OSCURO), ("!selected", "#52675c")],
        )
        estilos.configure(
            "Info.TLabel", background="white", foreground=COLOR_VERDE_OSCURO,
            font=("Segoe UI", 10, "bold"), padding=(12, 9)
        )

    def _crear_interfaz(self):
        principal = ttk.Frame(self.ventana, padding=14)
        principal.pack(fill="both", expand=True)
        principal.rowconfigure(0, weight=1)
        principal.columnconfigure(0, weight=1)
        self.divisor = ttk.Panedwindow(principal, orient="horizontal")
        self.divisor.grid(row=0, column=0, sticky="nsew")
        self._divisor_inicializado = False
        self.divisor.bind("<Configure>", self._inicializar_divisor)

        lateral = ttk.Frame(self.divisor, width=300)
        lateral.rowconfigure(0, weight=1)
        lateral.columnconfigure(0, weight=1)
        self.lienzo_lateral = tk.Canvas(
            lateral, background=COLOR_FONDO, highlightthickness=0, width=300
        )
        barra_lateral = ttk.Scrollbar(
            lateral, orient="vertical", command=self.lienzo_lateral.yview
        )
        self.lienzo_lateral.configure(yscrollcommand=barra_lateral.set)
        self.lienzo_lateral.grid(row=0, column=0, sticky="nsew")
        barra_lateral.grid(row=0, column=1, sticky="ns")
        self.panel_controles = ttk.Frame(self.lienzo_lateral)
        self.ventana_lateral = self.lienzo_lateral.create_window(
            (0, 0), window=self.panel_controles, anchor="nw"
        )
        self.panel_controles.bind(
            "<Configure>",
            lambda _evento: self.lienzo_lateral.configure(
                scrollregion=self.lienzo_lateral.bbox("all")
            ),
        )
        self.lienzo_lateral.bind("<Configure>", self._ajustar_panel_lateral)

        self.informacion = ttk.Label(
            self.panel_controles,
            text="Configura el terreno y selecciona «Generar terreno».",
            style="Info.TLabel",
            wraplength=250,
        )
        self.informacion.pack(fill="x", pady=(0, 8))

        encabezado = ttk.Frame(
            self.panel_controles, padding=(16, 14), style="Header.TFrame"
        )
        encabezado.pack(fill="x", pady=(0, 8))
        titulo = ttk.Frame(encabezado, style="Header.TFrame")
        titulo.pack(fill="x")
        ttk.Label(
            titulo, text="EcoSuelo", style="Title.TLabel"
        ).pack(anchor="w")
        self.subtitulo = ttk.Label(
            titulo,
            text="Monitoreo y exploración de humedad del terreno",
            style="Subtitle.TLabel",
            wraplength=250,
        )
        self.subtitulo.pack(anchor="w", pady=(2, 0))

        self._crear_configuracion()
        self._crear_barra_acciones()

        ttk.Button(
            self.panel_controles,
            text="Salir", style="Exit.TButton",
            command=self.salir_del_sistema,
        ).pack(fill="x", pady=(0, 8))

        area_contenido = ttk.Frame(self.divisor)
        area_contenido.rowconfigure(0, weight=1)
        area_contenido.columnconfigure(0, weight=1)
        self.pestanas = ttk.Notebook(area_contenido)
        self.pestanas.grid(row=0, column=0, sticky="nsew")
        self.divisor.add(lateral, weight=0)
        self.divisor.add(area_contenido, weight=1)
        self._crear_pestana_mapa()
        self._crear_pestana_resultados()
        self._crear_pestana_historial()

    def _ajustar_panel_lateral(self, evento):
        self.lienzo_lateral.itemconfigure(
            self.ventana_lateral, width=evento.width
        )
        ancho_texto = max(160, evento.width - 44)
        self.informacion.configure(wraplength=ancho_texto)
        self.aviso_simulacion.configure(wraplength=ancho_texto)
        self.subtitulo.configure(wraplength=max(150, evento.width - 52))

    def _inicializar_divisor(self, evento):
        if not self._divisor_inicializado and evento.width > 700:
            self.divisor.sashpos(0, min(340, evento.width - 400))
            self._divisor_inicializado = True

    def _crear_configuracion(self):
        marco = ttk.LabelFrame(
            self.panel_controles, text="Configuración del terreno",
            padding=(10, 8), style="Card.TLabelframe"
        )
        marco.pack(fill="x", pady=(0, 8))

        self.entrada_nombre = self._campo(
            marco, "Nombre del terreno", "Terreno escolar", 24, 0
        )
        self.entrada_largo = self._campo(marco, "Largo X (m)", "20", 10, 2)
        self.entrada_ancho = self._campo(marco, "Ancho Y (m)", "10", 10, 4)
        self.entrada_bloque = self._campo(marco, "Bloque (m)", "2", 10, 6)

        ttk.Button(
            marco, text="Generar terreno", style="Primary.TButton",
            command=self.generar_terreno
        ).pack(fill="x", pady=(8, 10))

        ttk.Label(
            marco, text="Límites de humedad", style="Section.TLabel"
        ).pack(anchor="w", pady=(0, 4))
        limites = ttk.Frame(marco, style="Card.TFrame")
        limites.pack(fill="x")
        limite_bajo = ttk.Frame(limites, style="Card.TFrame")
        limite_bajo.pack(side="left", fill="x", expand=True, padx=(0, 4))
        limite_alto = ttk.Frame(limites, style="Card.TFrame")
        limite_alto.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ttk.Label(limite_bajo, text="Baja <").pack(anchor="w")
        self.entrada_limite_bajo = ttk.Entry(limite_bajo, width=8)
        self.entrada_limite_bajo.insert(0, "30")
        self.entrada_limite_bajo.pack(fill="x", pady=(2, 0))
        ttk.Label(limite_alto, text="Alta ≥").pack(anchor="w")
        self.entrada_limite_alto = ttk.Entry(limite_alto, width=8)
        self.entrada_limite_alto.insert(0, "60")
        self.entrada_limite_alto.pack(fill="x", pady=(2, 0))
        ttk.Button(
            marco, text="Aplicar límites", command=self.aplicar_limites
        ).pack(fill="x", pady=(8, 0))

    @staticmethod
    def _campo(marco, etiqueta, valor, ancho, columna):
        campo = ttk.Frame(marco, style="Card.TFrame")
        campo.pack(fill="x", pady=3)
        ttk.Label(campo, text=etiqueta).pack(anchor="w")
        entrada = ttk.Entry(campo, width=ancho)
        entrada.insert(0, valor)
        entrada.pack(fill="x", pady=(2, 0))
        return entrada

    def _crear_barra_acciones(self):
        barra = ttk.LabelFrame(
            self.panel_controles, text="Acciones", padding=(8, 7),
            style="Card.TLabelframe",
        )
        barra.pack(fill="x", pady=(0, 2))
        ttk.Button(
            barra, text="Generar ruta zigzag", command=self.generar_ruta
        ).pack(fill="x", pady=3)
        ttk.Button(
            barra, text="Mostrar / ocultar ruta",
            command=self.alternar_ruta
        ).pack(fill="x", pady=3)
        ttk.Button(
            barra, text="Simular mediciones", style="Primary.TButton",
            command=self.simular_mediciones
        ).pack(fill="x", pady=3)
        ttk.Button(
            barra, text="Ruta de zonas secas",
            command=self.mostrar_ruta_seca
        ).pack(fill="x", pady=3)
        ttk.Button(
            barra, text="Exportar CSV", command=self.exportar_csv
        ).pack(fill="x", pady=3)
        ttk.Button(
            barra, text="Reiniciar terreno", command=self.reiniciar_terreno
        ).pack(fill="x", pady=(8, 3))

    def _crear_pestana_mapa(self):
        pestana = ttk.Frame(self.pestanas, padding=10)
        self.pestanas.add(pestana, text="Mapa del terreno")

        leyenda = ttk.Frame(pestana)
        leyenda.pack(fill="x", pady=(0, 7))
        for color, texto in (
            (COLOR_SECO, "Baja / necesita riego"),
            (COLOR_MEDIO, "Media"),
            (COLOR_HUMEDO, "Alta"),
            (COLOR_SIN_MEDIR, "Sin medir"),
        ):
            muestra = tk.Label(
                leyenda, text="   ", bg=color, relief="solid", bd=1
            )
            muestra.pack(side="left", padx=(8, 3))
            ttk.Label(leyenda, text=texto).pack(side="left")

        contenedor = ttk.Frame(pestana)
        contenedor.pack(fill="both", expand=True)
        self.lienzo = tk.Canvas(
            contenedor, background="#f8fbf8", highlightthickness=1,
            highlightbackground="#d2ded5"
        )
        barra_y = ttk.Scrollbar(
            contenedor, orient="vertical", command=self.lienzo.yview
        )
        barra_x = ttk.Scrollbar(
            contenedor, orient="horizontal", command=self.lienzo.xview
        )
        self.lienzo.configure(
            yscrollcommand=barra_y.set, xscrollcommand=barra_x.set
        )
        self.lienzo.grid(row=0, column=0, sticky="nsew")
        barra_y.grid(row=0, column=1, sticky="ns")
        barra_x.grid(row=1, column=0, sticky="ew")
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)
        self.lienzo.bind("<Configure>", self._al_cambiar_mapa)
        self.lienzo.create_text(
            350, 180,
            text="El mapa aparecerá aquí cuando generes un terreno.",
            fill="#52675c", font=("Segoe UI", 12),
        )

    def _crear_pestana_resultados(self):
        pestana = ttk.Frame(self.pestanas, padding=10)
        self.pestanas.add(pestana, text="Resultados y estadísticas")

        estadisticas = ttk.Frame(pestana)
        estadisticas.pack(fill="x", pady=(0, 10))
        self.etiquetas_estadisticas = {}
        nombres = (
            ("promedio", "Promedio"),
            ("maximo", "Máxima"),
            ("minimo", "Mínima"),
            ("baja", "Bloques secos"),
            ("media", "Humedad media"),
            ("alta", "Humedad alta"),
        )
        for clave, titulo in nombres:
            tarjeta = tk.Frame(
                estadisticas, bg="white", highlightbackground="#dce6df",
                highlightthickness=1, padx=12, pady=8,
            )
            tarjeta.pack(side="left", fill="x", expand=True, padx=3)
            tk.Label(
                tarjeta, text=titulo, bg="white", fg="#52675c",
                font=("Segoe UI", 9),
            ).pack(anchor="w")
            etiqueta = tk.Label(
                tarjeta, text="—", bg="white", fg="#1f5138",
                font=("Segoe UI", 15, "bold"),
            )
            etiqueta.pack(anchor="w")
            self.etiquetas_estadisticas[clave] = etiqueta

        self.resumen_extremos = ttk.Label(
            pestana,
            text="Bloque más seco: —     |     Bloque más húmedo: —",
            padding=(4, 4),
        )
        self.resumen_extremos.pack(fill="x")

        marco_tabla = ttk.Frame(pestana)
        marco_tabla.pack(fill="both", expand=True, pady=(5, 0))
        columnas = (
            "numero", "x", "y", "orden", "lectura", "humedad", "estado"
        )
        self.tabla = ttk.Treeview(
            marco_tabla, columns=columnas, show="headings", height=12
        )
        encabezados = {
            "numero": ("Bloque", 75),
            "x": ("X (m)", 90),
            "y": ("Y (m)", 90),
            "orden": ("Orden de visita", 110),
            "lectura": ("Lectura simulada (u.a.)", 165),
            "humedad": ("% humedad", 110),
            "estado": ("Estado", 125),
        }
        for clave, (titulo, ancho) in encabezados.items():
            self.tabla.heading(
                clave, text=titulo,
                command=lambda col=clave: self.ordenar_tabla(col)
            )
            self.tabla.column(clave, width=ancho, anchor="center")
        self.tabla.tag_configure("seca", background="#fff0ef")
        self.tabla.tag_configure("media", background="#fff8e4")
        self.tabla.tag_configure("alta", background="#edf8ef")
        self.tabla.tag_configure("sin_medicion", background="#f1f3f2")
        barra = ttk.Scrollbar(
            marco_tabla, orient="vertical", command=self.tabla.yview
        )
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        ttk.Label(
            pestana,
            text="Pulsa el encabezado de una columna para ordenar la tabla.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(5, 0))

    def _crear_pestana_historial(self):
        pestana = ttk.Frame(self.pestanas, padding=10)
        self.pestanas.add(pestana, text="Historial de mediciones")
        ttk.Label(
            pestana,
            text="Cada simulación agrega una lectura ficticia por bloque.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(0, 8))
        columnas = ("fecha", "bloque", "x", "y", "humedad", "estado")
        self.tabla_historial = ttk.Treeview(
            pestana, columns=columnas, show="headings"
        )
        titulos = {
            "fecha": ("Fecha y hora", 190),
            "bloque": ("Bloque", 80),
            "x": ("X (m)", 95),
            "y": ("Y (m)", 95),
            "humedad": ("% humedad simulada", 160),
            "estado": ("Estado", 120),
        }
        for clave, (titulo, ancho) in titulos.items():
            self.tabla_historial.heading(clave, text=titulo)
            self.tabla_historial.column(clave, width=ancho, anchor="center")
        barra = ttk.Scrollbar(
            pestana, orient="vertical", command=self.tabla_historial.yview
        )
        self.tabla_historial.configure(yscrollcommand=barra.set)
        self.tabla_historial.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def generar_terreno(self):
        nombre = self.entrada_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Dato incorrecto", "Escribe el nombre del terreno.")
            return

        try:
            largo = float(self.entrada_largo.get())
            ancho = float(self.entrada_ancho.get())
            tamano = float(self.entrada_bloque.get())
            self._validar_numero_positivo(largo, "largo")
            self._validar_numero_positivo(ancho, "ancho")
            self._validar_numero_positivo(tamano, "tamaño del bloque")
            nuevos_bloques = crear_bloques(largo, ancho, tamano)
        except ValueError as error:
            messagebox.showerror("Dato incorrecto", str(error))
            return

        if self.bloques and not messagebox.askyesno(
            "Reemplazar terreno",
            "Se borrarán el mapa, las lecturas y el historial actuales. "
            "¿Deseas continuar?",
        ):
            return

        self.nombre_terreno = nombre
        self.largo = largo
        self.ancho = ancho
        self.tamano_bloque = tamano
        self.bloques = nuevos_bloques
        self.lecturas.clear()
        self.historial.clear()
        self.ruta_principal = []
        self.modo_ruta = None
        self._actualizar_vistas()
        self._actualizar_historial()
        self.informacion.config(
            text=f"{nombre}  ·  {largo:g} × {ancho:g} m  ·  "
                 f"{len(nuevos_bloques)} bloques"
        )

    @staticmethod
    def _validar_numero_positivo(valor, nombre):
        if not math.isfinite(valor) or valor <= 0:
            raise ValueError(f"El {nombre} debe ser un número mayor que cero.")

    def generar_ruta(self):
        if not self.bloques:
            messagebox.showwarning("Falta el terreno", "Genera primero el terreno.")
            return
        self.ruta_principal = crear_ruta_serpentina(self.bloques)
        self.modo_ruta = "principal"
        self._dibujar_mapa()
        self._actualizar_tabla()
        messagebox.showinfo(
            "Ruta generada",
            f"Ruta en zigzag preparada para {len(self.ruta_principal)} bloques. "
            "Solo es una visualización; no controla un carrito.",
        )

    def alternar_ruta(self):
        if not self.ruta_principal:
            messagebox.showwarning(
                "Ruta no generada", "Pulsa «Generar ruta zigzag» primero."
            )
            return
        self.modo_ruta = (
            None if self.modo_ruta == "principal" else "principal"
        )
        self._dibujar_mapa()

    def mostrar_ruta_seca(self):
        if not self.bloques:
            messagebox.showwarning("Falta el terreno", "Genera primero el terreno.")
            return
        if not self.lecturas:
            messagebox.showwarning(
                "Faltan lecturas", "Simula las mediciones antes de crear "
                "la ruta de zonas secas."
            )
            return
        bloques_secos = [
            bloque for bloque in self.bloques
            if self._estado(bloque["numero"]) == "Baja"
        ]
        if not bloques_secos:
            messagebox.showinfo(
                "Sin zonas secas", "No hay bloques con humedad baja."
            )
            return
        self.modo_ruta = "seca"
        self.ruta_principal = crear_ruta_serpentina(self.bloques)
        self._dibujar_mapa()
        self._actualizar_tabla()
        self.pestanas.select(0)
        messagebox.showinfo(
            "Ruta de zonas secas",
            f"La ruta marcada en naranja visita {len(bloques_secos)} "
            "bloques con humedad baja.",
        )

    def _leer_limites(self):
        limite_bajo = float(self.entrada_limite_bajo.get())
        limite_alto = float(self.entrada_limite_alto.get())
        if (
            not math.isfinite(limite_bajo)
            or not math.isfinite(limite_alto)
            or limite_bajo < 0
            or limite_alto > 100
            or limite_bajo >= limite_alto
        ):
            raise ValueError(
                "Usa límites entre 0 y 100, y asegúrate de que "
                "el límite bajo sea menor que el alto."
            )
        return limite_bajo, limite_alto

    def aplicar_limites(self):
        try:
            self.limite_bajo, self.limite_alto = self._leer_limites()
        except ValueError as error:
            messagebox.showerror("Límites incorrectos", str(error))
            return
        if self.lecturas:
            self.modo_ruta = None
            self._actualizar_vistas()
            self._actualizar_historial()
        messagebox.showinfo(
            "Límites aplicados",
            f"Baja: menos de {self.limite_bajo:g} % · "
            f"Alta: desde {self.limite_alto:g} %.",
        )

    def simular_mediciones(self):
        if not self.bloques:
            messagebox.showwarning("Falta el terreno", "Genera primero el terreno.")
            return
        try:
            self.limite_bajo, self.limite_alto = self._leer_limites()
        except ValueError as error:
            messagebox.showerror("Límites incorrectos", str(error))
            return

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for bloque in self.bloques:
            numero = bloque["numero"]
            lectura = random.randint(0, 1023)
            humedad = lectura / 1023 * 100
            self.lecturas[numero] = {
                "lectura": lectura,
                "humedad": humedad,
                "fecha": fecha,
            }
            self.historial.append({
                "fecha": fecha,
                "bloque": bloque,
                "humedad": humedad,
            })

        self.modo_ruta = None
        self._actualizar_vistas()
        self._actualizar_historial()
        self.pestanas.select(1)

    def reiniciar_terreno(self):
        if not self.bloques:
            messagebox.showinfo("Sin terreno", "No hay un terreno que reiniciar.")
            return
        if not messagebox.askyesno(
            "Reiniciar terreno",
            "Se borrarán el terreno, las mediciones y el historial. "
            "¿Deseas continuar?",
        ):
            return

        self.bloques.clear()
        self.lecturas.clear()
        self.historial.clear()
        self.ruta_principal.clear()
        self.modo_ruta = None
        self._actualizar_vistas()
        self._actualizar_historial()
        self.informacion.config(
            text="Configura el terreno y selecciona «Generar terreno»."
        )

    def exportar_csv(self):
        if not self.bloques:
            messagebox.showwarning("Falta el terreno", "Genera primero el terreno.")
            return
        archivo = filedialog.asksaveasfilename(
            title="Guardar resultados simulados",
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="resultados_humedad.csv",
        )
        if not archivo:
            return

        ordenes = {
            bloque["numero"]: orden
            for orden, bloque in enumerate(self.ruta_principal, start=1)
        }
        try:
            with open(
                archivo, "w", newline="", encoding="utf-8-sig"
            ) as archivo_csv:
                escritor = csv.writer(archivo_csv)
                escritor.writerow([
                    "Nombre del terreno",
                    "Largo (m)",
                    "Ancho (m)",
                    "Tamaño del bloque (m)",
                    "Número de bloque",
                    "Coordenada X (m)",
                    "Coordenada Y (m)",
                    "Orden de ruta zigzag",
                    "Lectura simulada (u.a.)",
                    "Humedad (%)",
                    "Estado del bloque",
                ])
                for bloque in self.bloques:
                    numero = bloque["numero"]
                    medicion = self.lecturas.get(numero)
                    escritor.writerow([
                        self.nombre_terreno,
                        self.largo,
                        self.ancho,
                        self.tamano_bloque,
                        numero,
                        round(bloque["x"], 3),
                        round(bloque["y"], 3),
                        ordenes.get(numero, ""),
                        "" if medicion is None else medicion["lectura"],
                        "" if medicion is None else round(medicion["humedad"], 2),
                        self._estado(numero),
                    ])
        except OSError as error:
            messagebox.showerror(
                "Error al exportar", f"No se pudo guardar el CSV:\n{error}"
            )
            return
        messagebox.showinfo(
            "CSV exportado", "Los resultados se guardaron correctamente."
        )

    def _estado(self, numero):
        medicion = self.lecturas.get(numero)
        humedad = None if medicion is None else medicion["humedad"]
        return clasificar_humedad(
            humedad, self.limite_bajo, self.limite_alto
        )

    def _actualizar_vistas(self):
        self._dibujar_mapa()
        self._actualizar_tabla()
        self._actualizar_estadisticas()

    def _actualizar_tabla(self):
        for elemento in self.tabla.get_children():
            self.tabla.delete(elemento)
        ordenes = {}
        if self.ruta_principal:
            ruta = self.ruta_principal
            if self.modo_ruta == "seca":
                ruta = [
                    bloque for bloque in ruta
                    if self._estado(bloque["numero"]) == "Baja"
                ]
            ordenes = {
                bloque["numero"]: indice
                for indice, bloque in enumerate(ruta, start=1)
            }

        bloques = list(self.bloques)
        columna = getattr(self, "columna_orden", "numero")
        descendente = self.ordenar_descendente
        if columna in ("humedad", "lectura"):
            bloques.sort(
                key=lambda bloque: (
                    self.lecturas.get(bloque["numero"]) is None,
                    self.lecturas.get(bloque["numero"], {}).get(
                        "humedad" if columna == "humedad" else "lectura", 0
                    ),
                ),
                reverse=descendente,
            )
            if descendente:
                medidos = [
                    bloque for bloque in bloques
                    if self.lecturas.get(bloque["numero"]) is not None
                ]
                sin_medicion = [
                    bloque for bloque in bloques
                    if self.lecturas.get(bloque["numero"]) is None
                ]
                bloques = medidos + sin_medicion
        else:
            bloques.sort(
                key=lambda bloque: self._valor_orden(bloque, columna, ordenes),
                reverse=descendente,
            )

        for bloque in bloques:
            numero = bloque["numero"]
            medicion = self.lecturas.get(numero)
            lectura = "Sin medir" if medicion is None else str(medicion["lectura"])
            humedad = (
                "—" if medicion is None
                else f"{medicion['humedad']:.1f} %"
            )
            estado = self._estado(numero)
            etiqueta = {
                "Baja": "seca",
                "Media": "media",
                "Alta": "alta",
                "Sin medir": "sin_medicion",
            }[estado]
            self.tabla.insert(
                "", "end",
                values=(
                    numero,
                    f"{bloque['x']:.2f}",
                    f"{bloque['y']:.2f}",
                    ordenes.get(numero, "—"),
                    lectura,
                    humedad,
                    estado,
                ),
                tags=(etiqueta,),
            )

    def _valor_orden(self, bloque, columna, ordenes):
        if columna == "orden":
            valor = ordenes.get(bloque["numero"])
            return (valor is None, 0 if valor is None else valor)
        if columna in ("x", "y"):
            return bloque[columna]
        if columna == "estado":
            return {
                "Baja": 0, "Media": 1, "Alta": 2, "Sin medir": 3
            }[self._estado(bloque["numero"])]
        return bloque["numero"]

    def ordenar_tabla(self, columna):
        if getattr(self, "columna_orden", None) == columna:
            self.ordenar_descendente = not self.ordenar_descendente
        else:
            self.columna_orden = columna
            self.ordenar_descendente = False
        self._actualizar_tabla()

    def _actualizar_estadisticas(self):
        humedades = [
            medicion["humedad"] for medicion in self.lecturas.values()
        ]
        if not humedades:
            for etiqueta in self.etiquetas_estadisticas.values():
                etiqueta.config(text="—")
            self.resumen_extremos.config(
                text="Bloque más seco: —     |     Bloque más húmedo: —"
            )
            return

        estados = [
            self._estado(bloque["numero"]) for bloque in self.bloques
        ]
        valores = {
            "promedio": f"{sum(humedades) / len(humedades):.1f} %",
            "maximo": f"{max(humedades):.1f} %",
            "minimo": f"{min(humedades):.1f} %",
            "baja": str(estados.count("Baja")),
            "media": str(estados.count("Media")),
            "alta": str(estados.count("Alta")),
        }
        for clave, valor in valores.items():
            self.etiquetas_estadisticas[clave].config(text=valor)

        seco = min(
            self.lecturas,
            key=lambda numero: self.lecturas[numero]["humedad"],
        )
        humedo = max(
            self.lecturas,
            key=lambda numero: self.lecturas[numero]["humedad"],
        )
        self.resumen_extremos.config(
            text=f"Bloque más seco: #{seco} "
                 f"({self.lecturas[seco]['humedad']:.1f} %)     |     "
                 f"Bloque más húmedo: #{humedo} "
                 f"({self.lecturas[humedo]['humedad']:.1f} %)"
        )

    def _actualizar_historial(self):
        for elemento in self.tabla_historial.get_children():
            self.tabla_historial.delete(elemento)
        for registro in reversed(self.historial):
            bloque = registro["bloque"]
            humedad = registro["humedad"]
            estado = clasificar_humedad(
                humedad, self.limite_bajo, self.limite_alto
            )
            self.tabla_historial.insert(
                "", "end",
                values=(
                    registro["fecha"],
                    bloque["numero"],
                    f"{bloque['x']:.2f}",
                    f"{bloque['y']:.2f}",
                    f"{humedad:.1f} %",
                    estado,
                ),
            )

    def salir_del_sistema(self):
        if messagebox.askyesno(
            "Salir de EcoSuelo", "¿Deseas cerrar la aplicación?"
        ):
            self.ventana.destroy()

    def _al_cambiar_mapa(self, evento):
        if self.bloques and evento.width > 1 and evento.height > 1:
            self._dibujar_mapa()

    def _dibujar_mapa(self):
        self.lienzo.delete("all")
        if not self.bloques:
            self.lienzo.configure(scrollregion=(0, 0, 1, 1))
            self.lienzo.create_text(
                max(self.lienzo.winfo_width() / 2, 300),
                max(self.lienzo.winfo_height() / 2, 180),
                text="El mapa aparecerá aquí cuando generes un terreno.",
                fill="#52675c", font=("Segoe UI", 12),
            )
            return

        vista_ancho = max(self.lienzo.winfo_width(), 500)
        vista_alto = max(self.lienzo.winfo_height(), 350)
        escala_ajustada = min(
            (vista_ancho - 100) / self.largo,
            (vista_alto - 90) / self.ancho,
            86,
        )
        escala = max(4, escala_ajustada)
        mapa_ancho = self.largo * escala
        mapa_alto = self.ancho * escala
        margen_x = max(50, (vista_ancho - mapa_ancho) / 2)
        margen_y = max(38, (vista_alto - mapa_alto) / 2)

        self.lienzo.create_text(
            margen_x + mapa_ancho / 2, max(20, margen_y - 23),
            text=f"{self.nombre_terreno}   ·   {self.largo:g} × "
                 f"{self.ancho:g} m",
            fill=COLOR_VERDE_OSCURO, font=("Segoe UI", 11, "bold"),
        )

        for bloque in self.bloques:
            x1 = margen_x + bloque["columna"] * self.tamano_bloque * escala
            x2 = x1 + bloque["largo"] * escala
            y1 = margen_y + (
                self.ancho - bloque["y"] - bloque["ancho"] / 2
            ) * escala
            y2 = y1 + bloque["ancho"] * escala

            estado = self._estado(bloque["numero"])
            color = {
                "Sin medir": COLOR_SIN_MEDIR,
                "Baja": COLOR_SECO,
                "Media": COLOR_MEDIO,
                "Alta": COLOR_HUMEDO,
            }[estado]
            self.lienzo.create_rectangle(
                x1, y1, x2, y2, fill=color, outline="#ffffff", width=1
            )
            centro_x = margen_x + bloque["x"] * escala
            centro_y = margen_y + (self.ancho - bloque["y"]) * escala
            ancho_celda = x2 - x1
            alto_celda = y2 - y1
            medicion = self.lecturas.get(bloque["numero"])

            if ancho_celda >= 105 and alto_celda >= 75:
                humedad = (
                    "Sin medir" if medicion is None
                    else f"{medicion['humedad']:.1f} %"
                )
                self.lienzo.create_text(
                    centro_x, y1 + 13, text=f"#{bloque['numero']}",
                    fill="#20362a", font=("Segoe UI", 9, "bold"),
                )
                self.lienzo.create_text(
                    centro_x, centro_y - 9,
                    text=f"X {bloque['x']:.1f} · Y {bloque['y']:.1f} m",
                    fill="#35483c", font=("Segoe UI", 8),
                )
                self.lienzo.create_text(
                    centro_x, y2 - 11, text=humedad,
                    fill="#20362a", font=("Segoe UI", 8, "bold"),
                )
            elif ancho_celda >= 38 and alto_celda >= 34:
                humedad = (
                    "Sin medir" if medicion is None
                    else f"{medicion['humedad']:.0f} %"
                )
                self.lienzo.create_text(
                    centro_x, y1 + 9, text=f"#{bloque['numero']}",
                    fill="#20362a", font=("Segoe UI", 7, "bold"),
                )
                self.lienzo.create_text(
                    centro_x, y2 - 7, text=humedad,
                    fill="#35483c", font=("Segoe UI", 6),
                )
            else:
                self.lienzo.create_text(
                    centro_x, centro_y, text=str(bloque["numero"]),
                    fill="#20362a", font=("Segoe UI", 7, "bold"),
                )

            self.lienzo.create_oval(
                centro_x - 3, centro_y - 3, centro_x + 3, centro_y + 3,
                fill=COLOR_VERDE_OSCURO, outline="white", width=1,
            )

        self.lienzo.create_rectangle(
            margen_x, margen_y, margen_x + mapa_ancho,
            margen_y + mapa_alto, outline="#789083", width=2,
        )

        if self.modo_ruta == "principal" and self.ruta_principal:
            self._dibujar_ruta(self.ruta_principal, margen_x, margen_y, escala)
        elif self.modo_ruta == "seca":
            bloques_secos = [
                bloque for bloque in crear_ruta_serpentina(self.bloques)
                if self._estado(bloque["numero"]) == "Baja"
            ]
            self._dibujar_ruta(bloques_secos, margen_x, margen_y, escala, seca=True)

        self.lienzo.create_text(
            margen_x + mapa_ancho / 2, margen_y + mapa_alto + 20,
            text=f"{self.largo:g} m",
            fill="#52675c", font=("Segoe UI", 9),
        )
        self.lienzo.create_text(
            max(margen_x - 23, 8), margen_y + mapa_alto / 2,
            text=f"{self.ancho:g} m", angle=90,
            fill="#52675c", font=("Segoe UI", 9),
        )
        self.lienzo.configure(
            scrollregion=(
                0, 0, margen_x + mapa_ancho + 35,
                margen_y + mapa_alto + 45,
            )
        )

    def _dibujar_ruta(self, ruta, margen_x, margen_y, escala, seca=False):
        if not ruta:
            return
        color = "#d97706" if seca else COLOR_AZUL
        for actual, siguiente in zip(ruta, ruta[1:]):
            x1 = margen_x + actual["x"] * escala
            y1 = margen_y + (self.ancho - actual["y"]) * escala
            x2 = margen_x + siguiente["x"] * escala
            y2 = margen_y + (self.ancho - siguiente["y"]) * escala
            self.lienzo.create_line(
                x1, y1, x2, y2, fill=color, width=3,
                arrow="last", arrowshape=(9, 11, 4),
            )
        for orden, bloque in enumerate(ruta, start=1):
            centro_x = margen_x + bloque["x"] * escala
            centro_y = margen_y + (self.ancho - bloque["y"]) * escala
            self.lienzo.create_oval(
                centro_x + 5, centro_y - 17, centro_x + 23, centro_y + 1,
                fill=color, outline="white",
            )
            self.lienzo.create_text(
                centro_x + 14, centro_y - 8, text=str(orden),
                fill="white", font=("Segoe UI", 7, "bold"),
            )


def iniciar_aplicacion():
    ventana = tk.Tk()
    AplicacionHumedad(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    iniciar_aplicacion()
