"""Comunicación USB Serial no bloqueante con el ESP32."""

import json
import queue
import threading


def analizar_linea(linea):
    """Decodifica un mensaje JSON recibido y comprueba su estructura."""
    mensaje = json.loads(linea)
    if not isinstance(mensaje, dict) or not isinstance(mensaje.get("type"), str):
        raise ValueError("El mensaje JSON no contiene un campo 'type' válido.")
    return mensaje


class ComunicacionESP32:
    """Lee y escribe mensajes JSON en un hilo independiente de Tkinter."""

    def __init__(self):
        self.eventos = queue.Queue()
        self._serial = None
        self._lock = threading.Lock()
        self._detener_lector = None

    @staticmethod
    def listar_puertos():
        """Devuelve los nombres de puertos COM disponibles."""
        try:
            from serial.tools import list_ports
        except ImportError as error:
            raise RuntimeError(
                "Falta pySerial. Instálalo ejecutando "
                "'python -m pip install -r requirements.txt'."
            ) from error
        return [puerto.device for puerto in list_ports.comports()]

    @property
    def conectado(self):
        with self._lock:
            return self._serial is not None

    def conectar(self, puerto):
        """Abre el puerto y arranca el lector sin bloquear la interfaz."""
        try:
            import serial
        except ImportError as error:
            raise RuntimeError(
                "Falta pySerial. Instálalo ejecutando "
                "'python -m pip install -r requirements.txt'."
            ) from error

        self.desconectar()
        try:
            conexion = serial.Serial(
                puerto, baudrate=115200, timeout=0.2, write_timeout=1
            )
        except (serial.SerialException, OSError) as error:
            raise RuntimeError(
                f"No se pudo abrir {puerto}: {error}"
            ) from error

        detener = threading.Event()
        with self._lock:
            self._serial = conexion
            self._detener_lector = detener
        self.eventos.put({"type": "connection", "connected": True, "port": puerto})
        lector = threading.Thread(
            target=self._leer, args=(conexion, detener), daemon=True,
            name="EcoSueloSerial",
        )
        lector.start()

    def desconectar(self):
        """Cierra el puerto, si estaba abierto."""
        with self._lock:
            conexion = self._serial
            detener = self._detener_lector
            self._serial = None
            self._detener_lector = None
        if detener is not None:
            detener.set()
        if conexion is not None:
            try:
                conexion.close()
            except OSError as error:
                self.eventos.put({
                    "type": "error",
                    "message": f"Error al cerrar el puerto serial: {error}",
                })
            self.eventos.put({"type": "connection", "connected": False})

    def enviar(self, comando):
        """Envía un objeto como una línea JSON."""
        with self._lock:
            conexion = self._serial
            if conexion is None:
                raise RuntimeError("No hay un ESP32 conectado.")
            try:
                contenido = json.dumps(comando, separators=(",", ":")) + "\n"
                conexion.write(contenido.encode("utf-8"))
            except OSError as error:
                fallo = error
            else:
                return
        self._perder_conexion(conexion, fallo)
        raise RuntimeError(f"Error al enviar datos al ESP32: {fallo}") from fallo

    def _leer(self, conexion, detener):
        while not detener.is_set():
            try:
                linea = conexion.readline()
            except OSError as error:
                if not detener.is_set():
                    self._perder_conexion(conexion, error)
                return
            if not linea:
                continue
            try:
                mensaje = analizar_linea(linea.decode("utf-8").strip())
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
                self.eventos.put({
                    "type": "error",
                    "message": f"Se recibió una línea serial inválida: {error}",
                })
                continue
            self.eventos.put(mensaje)

    def _perder_conexion(self, conexion, error):
        with self._lock:
            if self._serial is not conexion:
                return
            self._serial = None
            detener = self._detener_lector
            self._detener_lector = None
        if detener is not None:
            detener.set()
        try:
            conexion.close()
        except OSError:
            pass
        self.eventos.put({"type": "connection", "connected": False})
        self.eventos.put({
            "type": "error",
            "message": f"Se perdió la conexión con el ESP32: {error}",
        })
