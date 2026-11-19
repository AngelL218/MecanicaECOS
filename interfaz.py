"""Interfaz gráfica de EcoSuelo y coordinación de sus módulos."""

import queue
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from comunicacion import ComunicacionESP32
from graficas import GraficaHumedad
from mediciones import RegistroMediciones


class InterfazEcoSuelo:
    """Aplicación Tkinter; toda actualización visual ocurre en el hilo UI."""

    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("EcoSuelo | Monitoreo de humedad")
        self.ventana.geometry("920x680")
        self.ventana.minsize(720, 520)
        self.comunicacion = ComunicacionESP32()
        ruta_datos = Path(__file__).resolve().parent / "datos" / "historial.csv"
        self.registro = RegistroMediciones(ruta_datos)
        self.esp32_listo = False
        self.monitoreando = False
        self.umbral_seco = 30.0
        self._crear_interfaz()
        self._cargar_historial()
        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.ventana.after(100, self._procesar_eventos)

    def _crear_interfaz(self):
        contenedor = ttk.Frame(self.ventana, padding=14)
        contenedor.pack(fill="both", expand=True)
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(2, weight=1)
        encabezado = ttk.Frame(contenedor)
        encabezado.grid(row=0, column=0, sticky="ew")
        ttk.Label(
            encabezado, text="EcoSuelo", font=("Segoe UI", 20, "bold")
        ).pack(anchor="w")
        ttk.Label(
            encabezado,
            text="Monitoreo de humedad por USB Serial · ESP32 / FC-28",
        ).pack(anchor="w")

        conexion = ttk.LabelFrame(
            contenedor, text="Conexión y monitoreo", padding=10
        )
        conexion.grid(row=1, column=0, sticky="ew", pady=(12, 8))
        conexion.columnconfigure(1, weight=1)
        ttk.Label(conexion, text="Puerto COM").grid(
            row=0, column=0, padx=(0, 6), sticky="w"
        )
        self.puerto = ttk.Combobox(conexion, state="readonly", width=14)
        self.puerto.grid(row=0, column=1, sticky="w")
        ttk.Button(
            conexion, text="Actualizar", command=self.actualizar_puertos
        ).grid(row=0, column=2, padx=4)
        self.boton_conexion = ttk.Button(
            conexion, text="Conectar", command=self.alternar_conexion
        )
        self.boton_conexion.grid(row=0, column=3, padx=4)
        self.estado_conexion = tk.StringVar(value="Desconectado")
        ttk.Label(
            conexion, textvariable=self.estado_conexion
        ).grid(row=0, column=4, padx=(10, 0), sticky="e")

        ttk.Label(conexion, text="Intervalo (s)").grid(
            row=1, column=0, padx=(0, 6), pady=(9, 0), sticky="w"
        )
        self.intervalo = ttk.Entry(conexion, width=8)
        self.intervalo.insert(0, "10")
        self.intervalo.grid(row=1, column=1, pady=(9, 0), sticky="w")
        ttk.Label(conexion, text="Umbral seco (%)").grid(
            row=1, column=2, padx=(12, 4), pady=(9, 0), sticky="e"
        )
        self.umbral = ttk.Entry(conexion, width=8)
        self.umbral.insert(0, "30")
        self.umbral.grid(row=1, column=3, pady=(9, 0), sticky="w")
        self.boton_iniciar = ttk.Button(
            conexion, text="Iniciar", command=self.iniciar_monitoreo,
            state="disabled",
        )
        self.boton_iniciar.grid(row=2, column=1, pady=(10, 0), sticky="w")
        self.boton_detener = ttk.Button(
            conexion, text="Detener", command=self.detener_monitoreo,
            state="disabled",
        )
        self.boton_detener.grid(row=2, column=2, pady=(10, 0), sticky="w")
        ttk.Button(
            conexion, text="Guardar CSV como…", command=self.guardar_csv
        ).grid(row=2, column=3, pady=(10, 0), sticky="e")

        datos = ttk.LabelFrame(contenedor, text="Última medición", padding=10)
        datos.grid(row=2, column=0, sticky="nsew", pady=8)
        datos.columnconfigure(0, weight=1)
        datos.rowconfigure(1, weight=1)
        indicadores = ttk.Frame(datos)
        indicadores.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.adc = tk.StringVar(value="—")
        self.humedad = tk.StringVar(value="—")
        self.estado_tierra = tk.StringVar(value="Esperando medición")
        for titulo, variable in (
            ("ADC", self.adc),
            ("Humedad estimada", self.humedad),
            ("Estado de la tierra", self.estado_tierra),
        ):
            tarjeta = ttk.LabelFrame(indicadores, text=titulo, padding=8)
            tarjeta.pack(side="left", fill="x", expand=True, padx=4)
            ttk.Label(
                tarjeta, textvariable=variable,
                font=("Segoe UI", 13, "bold"),
            ).pack()

        panel = ttk.Panedwindow(datos, orient="vertical")
        panel.grid(row=1, column=0, sticky="nsew")
        grafica_marco = ttk.LabelFrame(panel, text="Evolución de humedad")
        historial_marco = ttk.LabelFrame(panel, text="Historial")
        panel.add(grafica_marco, weight=1)
        panel.add(historial_marco, weight=1)
        self.canvas_grafica = tk.Canvas(
            grafica_marco, background="white", highlightthickness=0
        )
        self.canvas_grafica.pack(fill="both", expand=True, padx=5, pady=5)
        self.grafica = GraficaHumedad(self.canvas_grafica)

        columnas = ("fecha_hora", "adc", "humedad_pct", "estado")
        self.tabla = ttk.Treeview(
            historial_marco, columns=columnas, show="headings", height=7
        )
        titulos = {
            "fecha_hora": ("Fecha y hora", 220),
            "adc": ("ADC promedio", 120),
            "humedad_pct": ("Humedad estimada", 150),
            "estado": ("Estado", 130),
        }
        for clave, (titulo, ancho) in titulos.items():
            self.tabla.heading(clave, text=titulo)
            self.tabla.column(clave, width=ancho, anchor="center")
        barra = ttk.Scrollbar(
            historial_marco, orient="vertical", command=self.tabla.yview
        )
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.actualizar_puertos()

    def actualizar_puertos(self):
        try:
            puertos = self.comunicacion.listar_puertos()
        except RuntimeError as error:
            messagebox.showerror("Error de puertos", str(error))
            return
        seleccionado = self.puerto.get()
        self.puerto["values"] = puertos
        if seleccionado in puertos:
            self.puerto.set(seleccionado)
        elif puertos:
            self.puerto.current(0)
        else:
            self.puerto.set("")
            if not self.comunicacion.conectado:
                self.estado_conexion.set("No se detectaron puertos COM")

    def alternar_conexion(self):
        if self.comunicacion.conectado:
            self.comunicacion.desconectar()
            self.esp32_listo = False
            self.monitoreando = False
            self._actualizar_botones()
            self.estado_conexion.set("Desconectado")
            return
        puerto = self.puerto.get()
        if not puerto:
            messagebox.showwarning(
                "Selecciona un puerto", "Elige el puerto COM del ESP32."
            )
            return
        try:
            self.comunicacion.conectar(puerto)
        except RuntimeError as error:
            messagebox.showerror("Error de conexión", str(error))
            self.estado_conexion.set("Error de conexión")
            return
        self.esp32_listo = False
        self.estado_conexion.set(f"Conectado a {puerto}; esperando al ESP32…")
        self.boton_conexion.configure(text="Desconectar")

    def iniciar_monitoreo(self):
        try:
            segundos = float(self.intervalo.get())
            umbral = float(self.umbral.get())
            if not 1 <= segundos <= 86400:
                raise ValueError("El intervalo debe estar entre 1 y 86400 segundos.")
            if not 0 <= umbral <= 100:
                raise ValueError("El umbral seco debe estar entre 0 y 100 %.")
        except ValueError as error:
            messagebox.showerror("Configuración inválida", str(error))
            return
        if not self.esp32_listo:
            messagebox.showwarning(
                "ESP32 no listo",
                "Espera a que el ESP32 responda por el puerto serial.",
            )
            return
        try:
            self.comunicacion.enviar({
                "command": "start",
                "interval_ms": round(segundos * 1000),
            })
        except RuntimeError as error:
            messagebox.showerror("Error de comunicación", str(error))
            return
        self.umbral_seco = umbral
        self.monitoreando = True
        self._actualizar_botones()
        self.estado_conexion.set("Monitoreo solicitado")

    def detener_monitoreo(self):
        if not self.comunicacion.conectado:
            return
        try:
            self.comunicacion.enviar({"command": "stop"})
        except RuntimeError as error:
            messagebox.showerror("Error de comunicación", str(error))
            return
        self.monitoreando = False
        self._actualizar_botones()
        self.estado_conexion.set("Deteniendo monitoreo…")

    def _procesar_eventos(self):
        while True:
            try:
                evento = self.comunicacion.eventos.get_nowait()
            except queue.Empty:
                break
            tipo = evento.get("type")
            if tipo == "connection":
                conectado = evento.get("connected", False)
                self.esp32_listo = False
                if not conectado:
                    self.monitoreando = False
                    self.estado_conexion.set("Desconectado")
                    self.boton_conexion.configure(text="Conectar")
                self._actualizar_botones()
            elif tipo == "status":
                self.esp32_listo = True
                self.monitoreando = bool(evento.get("monitoring", False))
                estado = "Monitoreando" if self.monitoreando else "Conectado"
                self.estado_conexion.set(estado)
                self._actualizar_botones()
            elif tipo == "measurement":
                self._procesar_medicion(evento)
            elif tipo == "error":
                messagebox.showerror(
                    "Error de EcoSuelo", evento.get("message", "Error desconocido")
                )
        self.ventana.after(100, self._procesar_eventos)

    def _procesar_medicion(self, mensaje):
        try:
            registro = self.registro.agregar(mensaje, self.umbral_seco)
        except (OSError, ValueError) as error:
            messagebox.showerror("Medición inválida", str(error))
            return
        if registro is None:
            return
        self.adc.set(str(registro["adc"]))
        self.humedad.set(f'{registro["humedad_pct"]:.1f} %')
        self.estado_tierra.set(registro["estado"])
        self.tabla.insert(
            "", "end",
            values=(
                registro["fecha_hora"], registro["adc"],
                f'{registro["humedad_pct"]:.1f} %', registro["estado"],
            ),
        )
        self.tabla.yview_moveto(1)
        self.grafica.actualizar(self.registro.registros)

    def _cargar_historial(self):
        for registro in self.registro.registros:
            self.tabla.insert(
                "", "end",
                values=(
                    registro["fecha_hora"], registro["adc"],
                    f'{registro["humedad_pct"]:.1f} %', registro["estado"],
                ),
            )
        if self.registro.registros:
            ultimo = self.registro.registros[-1]
            self.adc.set(str(ultimo["adc"]))
            self.humedad.set(f'{ultimo["humedad_pct"]:.1f} %')
            self.estado_tierra.set(ultimo["estado"])
        self.grafica.actualizar(self.registro.registros)

    def guardar_csv(self):
        destino = filedialog.asksaveasfilename(
            title="Guardar historial de EcoSuelo",
            defaultextension=".csv",
            initialfile="historial_ecosuelo.csv",
            filetypes=[("Archivo CSV", "*.csv")],
        )
        if not destino:
            return
        try:
            self.registro.exportar(destino)
        except OSError as error:
            messagebox.showerror("Error al guardar CSV", str(error))
            return
        messagebox.showinfo("CSV guardado", f"Historial exportado a:\n{destino}")

    def _actualizar_botones(self):
        conectado = self.comunicacion.conectado
        self.boton_conexion.configure(
            text="Desconectar" if conectado else "Conectar"
        )
        self.boton_iniciar.configure(
            state="normal" if self.esp32_listo and not self.monitoreando else "disabled"
        )
        self.boton_detener.configure(
            state="normal" if conectado and self.monitoreando else "disabled"
        )

    def cerrar(self):
        if self.monitoreando and self.comunicacion.conectado:
            try:
                self.comunicacion.enviar({"command": "stop"})
            except RuntimeError:
                pass
        self.comunicacion.desconectar()
        self.ventana.destroy()


def iniciar_aplicacion():
    ventana = tk.Tk()
    try:
        InterfazEcoSuelo(ventana)
    except (OSError, ValueError) as error:
        messagebox.showerror("No se pudo iniciar EcoSuelo", str(error))
        ventana.destroy()
        return
    ventana.mainloop()
