
"""Comunicación USB Serial no bloqueante con el ESP32."""

import json
import queue
import threading
import time


def analizar_linea(linea):
    """Decodifica un mensaje JSON válido."""
    try:
        mensaje = json.loads(linea)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(mensaje, dict):
        return None

    if not isinstance(mensaje.get("type"), str):
        return None

    return mensaje


class ComunicacionESP32:
    """Comunicación serial con el ESP32 mediante JSON."""

    def __init__(self):
        self.eventos = queue.Queue()
        self._serial = None
        self._lock = threading.Lock()
        self._detener_lector = None

    @staticmethod
    def listar_puertos():
        """Obtiene los puertos COM disponibles."""
        try:
            from serial.tools import list_ports
        except ImportError as error:
            raise RuntimeError(
                "Falta pySerial. Instálalo con: "
                "python -m pip install pyserial"
            ) from error

        return [
            puerto.device
            for puerto in list_ports.comports()
        ]

    @property
    def conectado(self):
        with self._lock:
            return self._serial is not None

    def conectar(self, puerto):
        """Abre el puerto y comienza la lectura serial."""

        try:
            import serial
        except ImportError as error:
            raise RuntimeError(
                "Falta pySerial. Instálalo con: "
                "python -m pip install pyserial"
            ) from error

        self.desconectar()

        try:
            conexion = serial.Serial(
                port=puerto,
                baudrate=115200,
                timeout=0.2,
                write_timeout=1
            )

        except (serial.SerialException, OSError) as error:
            raise RuntimeError(
                f"No se pudo abrir {puerto}: {error}"
            ) from error

        detener = threading.Event()

        with self._lock:
            self._serial = conexion
            self._detener_lector = detener

        self.eventos.put({
            "type": "connection",
            "connected": True,
            "port": puerto
        })

        lector = threading.Thread(
            target=self._leer,
            args=(conexion, detener),
            daemon=True,
            name="EcoSueloSerial"
        )

        lector.start()

    def desconectar(self):
        """Cierra la conexión serial."""

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
            except OSError:
                pass

            self.eventos.put({
                "type": "connection",
                "connected": False
            })

    def enviar(self, comando):
        """Envía comandos JSON al ESP32."""

        with self._lock:
            conexion = self._serial

            if conexion is None:
                raise RuntimeError(
                    "No hay un ESP32 conectado."
                )

            try:
                contenido = (
                    json.dumps(
                        comando,
                        separators=(",", ":")
                    ) + "\n"
                )

                conexion.write(
                    contenido.encode("utf-8")
                )

            except (OSError, Exception) as error:
                fallo = error

            else:
                return

        self._perder_conexion(conexion, fallo)

        raise RuntimeError(
            f"Error al enviar datos al ESP32: {fallo}"
        ) from fallo

    def _leer(self, conexion, detener):
        """Lee mensajes sin bloquear la interfaz."""

        while not detener.is_set():

            try:
                linea = conexion.readline()

            except (OSError, Exception) as error:

                if not detener.is_set():
                    self._perder_conexion(
                        conexion,
                        error
                    )

                return

            if not linea:
                continue

            try:
                texto = linea.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if not texto:
                    continue

                mensaje = analizar_linea(texto)

                # Ignorar mensajes de arranque
                # y cualquier línea que no sea JSON válido.
                if mensaje is None:
                    continue

                self.eventos.put(mensaje)

            except Exception:
                # No interrumpir la comunicación
                # por una línea inesperada.
                continue

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

        self.eventos.put({
            "type": "connection",
            "connected": False
        })

        self.eventos.put({
            "type": "error",
            "message": (
                f"Se perdió la conexión con el ESP32: {error}"
            )
        })
