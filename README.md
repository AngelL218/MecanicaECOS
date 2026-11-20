# EcoSuelo

Aplicación de escritorio para monitorear por USB Serial la humedad del suelo
con un ESP32, un sensor FC-28 y un servomotor MG995. La interfaz Tkinter
recibe mensajes JSON, muestra las lecturas y su gráfica, y conserva las
mediciones en CSV. La comunicación principal es USB; el firmware incluye
BluetoothSerial para pruebas futuras.

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

Al arrancar, el servo se coloca en 90°. Al recibir `start`, se mueve a 15° y
envía inmediatamente una medición promedio de 20 lecturas ADC. Las siguientes
mediciones respetan el intervalo configurado. Al recibir `stop`, el servo vuelve
a 90°. El ángulo de reposo y el de medición son constantes editables en el
firmware.

### Porcentaje de humedad

La versión inicial usa
`humedad = ((4095 - ADC_promedio) * 100) / 4095` y limita el resultado entre
0 y 100 %. Puede variar según el sensor, el montaje y el sustrato; por eso se
deberá calibrar antes de interpretarla como contenido de agua universal.

## Instalar y ejecutar

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Uso

1. Selecciona el puerto COM del ESP32 y pulsa **Conectar**.
2. Pulsa **Mover servomotor a 15°** para probar manualmente esa posición.
3. Define el intervalo entre 1 y 86400 segundos y pulsa **Iniciar**. La primera
   medición llega inmediatamente y el servo permanece a 15°.
4. Pulsa **Detener** para finalizar las mediciones y devolver el servo a 90°.

Los formatos principales son `{"command":"status"}`,
`{"command":"servo","angle":15}`, `{"command":"start","interval_ms":10000}`
y `{"command":"stop"}`.

## Diagnóstico de carga USB

`No serial data received` no demuestra que el código tenga un error. Antes de
modificarlo, usa un cable USB con datos, selecciona el puerto COM correcto,
cierra el Monitor Serial y confirma el controlador CP210x o CH340/CH343 en
Administrador de dispositivos. Si no entra automáticamente en modo descarga,
mantén BOOT y pulsa/release RESET mientras inicia la carga. Confirma la variante
de la placa y las bibliotecas ESP32Servo/ESP32. Comprueba la alimentación del
servo por separado y evita topes mecánicos.

Para ejecutar las pruebas Python:

```powershell
python -m unittest -v
```
