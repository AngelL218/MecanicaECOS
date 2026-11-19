# EcoSuelo

Aplicación de escritorio para monitorear por USB Serial la humedad del suelo
con un ESP32, un sensor FC-28 y un servomotor MG995. La interfaz Tkinter
recibe mensajes JSON, muestra las lecturas y su gráfica, y conserva las
mediciones en CSV. No utiliza Wi-Fi ni Bluetooth.

## Estructura

- `main.py`: inicio de la aplicación y funciones de terreno conservadas para
  compatibilidad con las pruebas existentes.
- `interfaz.py`: controles, estado de conexión, tabla e integración Tkinter.
- `comunicacion.py`: búsqueda de puertos COM y lectura/escritura JSON en un
  hilo separado de la interfaz.
- `mediciones.py`: validación, deduplicación y almacenamiento CSV.
- `graficas.py`: gráfica dibujada con Canvas de Tkinter.
- `esp32_ecosuelo/esp32_ecosuelo.ino`: firmware del ESP32.
- `requirements.txt`: dependencia de pySerial.
- `datos/historial.csv`: historial local persistente (se crea si no existe).

## Conexiones

Usa las conexiones indicadas para el montaje:

| Componente | Conexión |
|---|---|
| FC-28 AO | ESP32 GPIO 34 |
| FC-28 VCC | ESP32 3V3 |
| FC-28 GND | GND del ESP32 |
| MG995 señal (naranja) | ESP32 GPIO 18 |
| MG995 alimentación (rojo) | salida regulada de 5 V de la fuente/LM2596 |
| MG995 tierra (café) | GND común con ESP32 y fuente |

El servo **no** se alimenta desde 3V3. Si tu fuente entrega más de 5 V, ajusta
el LM2596 a 5 V antes de conectar el MG995. El LM2596 es reductor y no puede
elevar una entrada de 5 V a una salida regulada de 5 V; si tu fuente ya entrega
5 V regulados, alimenta el servo desde esa fuente externa sin pasar por el
convertidor. En ambos casos asegúrate de que la fuente pueda suministrar la
corriente que demande el servo, especialmente al arrancar o bajo carga.
Comparte GND entre la fuente y el ESP32. El pin GPIO 34 es solo entrada; no
conectes el pin DO del módulo en su lugar. Mantén AO dentro del rango de entrada
del ESP32 (máximo 3.3 V). Prueba el movimiento del servo sin carga mecánica y
comprueba que el recorrido de 0° a 90° no choque con el montaje.

## Cargar el firmware

1. Instala Arduino IDE y agrega el soporte de placas **ESP32 de Espressif** en
   el gestor de placas.
2. En el gestor de bibliotecas instala **ESP32Servo**.
3. Abre `esp32_ecosuelo/esp32_ecosuelo.ino`, selecciona la placa ESP32 Dev Module (o la
   variante correspondiente a tu DevKit V1) y el puerto COM del ESP32.
4. Carga el programa. Si el puerto no aparece, prueba otro cable USB con datos
   y revisa el controlador USB-Serial de la placa.
5. Cierra el monitor serial del IDE antes de conectar EcoSuelo: un puerto COM
   normalmente solo puede ser abierto por una aplicación a la vez.

El programa espera el intervalo configurado, mueve el servo a 90°, espera un
segundo, promedia 20 lecturas ADC y devuelve el servo a 0° tras cada medición.
El firmware utiliza `analogReadResolution(12)`, por lo que el valor ADC va de
0 a 4095.

### Calibrar el porcentaje

El porcentaje es una estimación, no una medición universal del contenido de
agua. En la parte superior de `esp32_ecosuelo/esp32_ecosuelo.ino`, ajusta `ADC_SECO` y
`ADC_HUMEDO` con las lecturas reales de tu sensor: toma el promedio en suelo
seco y en suelo húmedo, respectivamente. Los valores iniciales (4095 y 0) son
los extremos del ADC y sirven solo como referencia; no sustituyen la
calibración. La fórmula admite extremos en cualquiera de los dos sentidos.

## Instalar y ejecutar en VS Code (Windows)

Abre la carpeta del proyecto en VS Code y, en una terminal integrada de
PowerShell, instala la dependencia:

```powershell
python -m pip install -r requirements.txt
```

Selecciona el intérprete Python de tu entorno con **Python: Select Interpreter**
en la paleta de comandos. Tkinter viene incluido normalmente con Python para
Windows. Ejecuta:

```powershell
python main.py
```

Si `python` no está en PATH, usa `py -m pip install -r requirements.txt` y
`py main.py`.

## Uso

1. En **Puerto COM**, selecciona el puerto que aparece al conectar la placa. Si
   no aparece, pulsa **Actualizar**. En Windows se puede revisar el nombre en
   Administrador de dispositivos → Puertos (COM y LPT); cierra Arduino Serial
   Monitor u otra aplicación que lo esté usando.
2. Pulsa **Conectar** y espera el estado “Conectado”. El ESP32 envía un mensaje
   de estado al iniciar; los botones de monitoreo se habilitan cuando llega.
3. Define el intervalo entre 1 y 86400 segundos y pulsa **Iniciar**. El umbral
   “seco” se puede ajustar entre 0 y 100 %. Por debajo del umbral la interfaz
   clasifica la lectura como “Seca”; en o sobre él, como “Húmeda”.
4. **Detener** ordena al ESP32 dejar de programar mediciones. Si ya hay una
   lectura en curso, el firmware la termina y retorna el servo a 0° antes de
   procesar la orden.
5. La tabla, los indicadores y la gráfica se actualizan con cada mensaje. Las
   lecturas se anexan automáticamente a `datos/historial.csv`; el identificador
   único del arranque y secuencia evita volver a guardar un mensaje repetido.
   **Guardar CSV como…** exporta todo el historial a otra ubicación.
6. Desconectar detiene la comunicación. Si el cable se desconecta, la
   aplicación lo indica y conserva el historial ya guardado.

Los comandos y respuestas son objetos JSON terminados en salto de línea,
transmitidos a **115200 baudios**. La aplicación no requiere hardware para
ejecutar sus pruebas unitarias:

```powershell
python -m unittest -v
```
