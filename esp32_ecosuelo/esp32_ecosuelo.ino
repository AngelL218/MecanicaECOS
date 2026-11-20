
#include <ESP32Servo.h>
#include <BluetoothSerial.h>
#include <esp_system.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>

// ==========================================
// CONFIGURACION DE HARDWARE
// ==========================================

constexpr uint8_t SENSOR_PIN = 34;
constexpr uint8_t SERVO_PIN = 18;

constexpr uint8_t NUM_LECTURAS = 20;
constexpr uint32_t ESPERA_ENTRE_LECTURAS_MS = 10;

// Posiciones del servomotor
constexpr int ANGULO_REPOSO = 90;
constexpr int ANGULO_MEDICION = 0;

// Tiempo para que el sensor llegue a la tierra
constexpr uint32_t TIEMPO_ESPERA_MEDICION_MS = 700;

// Calibracion del sensor
constexpr int ADC_SECO = 4095;
constexpr int ADC_HUMEDO = 0;

// ==========================================
// OBJETOS Y VARIABLES
// ==========================================

Servo servoSensor;
BluetoothSerial SerialBT;

char bufferSerial[128];
size_t indiceSerial = 0;

char bufferBluetooth[128];
size_t indiceBluetooth = 0;

bool monitoreoActivo = false;
bool medicionPendiente = false;

uint32_t tiempoInicioMedicion = 0;
uint32_t secuencia = 0;
uint32_t identificadorArranque = 0;

// ==========================================
// COMUNICACION
// ==========================================

void enviarLinea(const char *linea) {
  Serial.printf("%s\n", linea);

  if (SerialBT.hasClient()) {
    SerialBT.printf("%s\n", linea);
  }
}

void enviarEstado() {
  char respuesta[160];

  snprintf(
    respuesta,
    sizeof(respuesta),
    "{\"type\":\"status\",\"connected\":true,\"monitoring\":%s}",
    monitoreoActivo ? "true" : "false"
  );

  enviarLinea(respuesta);
}

void enviarError(const char *mensaje) {
  char respuesta[160];

  snprintf(
    respuesta,
    sizeof(respuesta),
    "{\"type\":\"error\",\"message\":\"%s\"}",
    mensaje
  );

  enviarLinea(respuesta);
}

// ==========================================
// LECTURA DE CAMPOS JSON
// ==========================================

bool leerCampoCadena(
  const char *json,
  const char *clave,
  char *salida,
  size_t capacidad
) {
  char patron[32];

  snprintf(patron, sizeof(patron), "\"%s\"", clave);

  const char *posicion = strstr(json, patron);

  if (posicion == nullptr) return false;

  posicion = strchr(posicion + strlen(patron), ':');

  if (posicion == nullptr) return false;

  posicion = strchr(posicion + 1, '"');

  if (posicion == nullptr) return false;

  const char *fin = strchr(posicion + 1, '"');

  if (fin == nullptr) return false;

  size_t largo = static_cast<size_t>(
    fin - (posicion + 1)
  );

  if (largo == 0 || largo >= capacidad) return false;

  memcpy(salida, posicion + 1, largo);
  salida[largo] = '\0';

  return true;
}

bool leerCampoEntero(
  const char *json,
  const char *clave,
  uint32_t *valor
) {
  char patron[32];

  snprintf(patron, sizeof(patron), "\"%s\"", clave);

  const char *posicion = strstr(json, patron);

  if (posicion == nullptr) return false;

  posicion = strchr(posicion + strlen(patron), ':');

  if (posicion == nullptr) return false;

  char *fin = nullptr;

  unsigned long numero = strtoul(posicion + 1, &fin, 10);

  if (fin == posicion + 1) return false;

  *valor = static_cast<uint32_t>(numero);

  return true;
}

// ==========================================
// POSICIONES DEL SERVO
// ==========================================

void posicionarServoReposo() {
  servoSensor.write(ANGULO_REPOSO);
}

void posicionarServoMedicion() {
  servoSensor.write(ANGULO_MEDICION);
}

// ==========================================
// REALIZAR UNA MEDICION
// ==========================================

void realizarMedicion() {

  uint32_t suma = 0;

  // Tomar 20 lecturas del sensor
  for (uint8_t i = 0; i < NUM_LECTURAS; i++) {

    suma += analogRead(SENSOR_PIN);

    if (i + 1 < NUM_LECTURAS) {
      delay(ESPERA_ENTRE_LECTURAS_MS);
    }
  }

  // Calcular promedio ADC
  uint16_t adcPromedio = static_cast<uint16_t>(
    (suma + NUM_LECTURAS / 2) / NUM_LECTURAS
  );

  // Convertir ADC a porcentaje de humedad
  float humedad =
    ((float)(ADC_SECO - adcPromedio) * 100.0f) /
    (ADC_SECO - ADC_HUMEDO);

  humedad = constrain(humedad, 0.0f, 100.0f);

  // Crear identificador de medicion
  char id[32];

  snprintf(
    id,
    sizeof(id),
    "%08lx-%lu",
    (unsigned long)identificadorArranque,
    (unsigned long)(secuencia + 1)
  );

  secuencia++;

  // Preparar porcentaje con un decimal
  uint16_t humedadDecimas = static_cast<uint16_t>(
    lroundf(humedad * 10.0f)
  );

  // Crear mensaje JSON
  char mensaje[180];

  snprintf(
    mensaje,
    sizeof(mensaje),
    "{\"type\":\"measurement\",\"id\":\"%s\","
    "\"seq\":%lu,\"adc\":%u,\"humidity\":%u.%u}",
    id,
    (unsigned long)secuencia,
    (unsigned int)adcPromedio,
    (unsigned int)(humedadDecimas / 10),
    (unsigned int)(humedadDecimas % 10)
  );

  // Enviar resultado a Python
  enviarLinea(mensaje);
}

// ==========================================
// PROCESAR COMANDOS
// ==========================================

void procesarComando(const char *json) {

  char comando[16];

  if (!leerCampoCadena(
    json,
    "command",
    comando,
    sizeof(comando)
  )) {
    enviarError("Comando JSON no valido");
    return;
  }

  // CONSULTAR ESTADO
  if (strcmp(comando, "status") == 0) {

    enviarEstado();

  }

  // MOVER SERVO MANUALMENTE
  else if (strcmp(comando, "servo") == 0) {

    uint32_t angulo = 0;

    if (!leerCampoEntero(json, "angle", &angulo) ||
        angulo > 180) {

      enviarError("angle debe estar entre 0 y 180");
      return;
    }

    // No permitir movimiento manual durante una medicion
    if (medicionPendiente) {
      enviarError("Hay una medicion en proceso");
      return;
    }

    servoSensor.write(static_cast<int>(angulo));

    enviarEstado();

  }

  // INICIAR UNA SOLA MEDICION
  else if (strcmp(comando, "start") == 0) {

    if (medicionPendiente) {
      enviarError("Ya hay una medicion en proceso");
      return;
    }

    // Activar proceso
    monitoreoActivo = true;
    medicionPendiente = true;

    // Bajar el sensor a la tierra
    posicionarServoMedicion();

    // Esperar 700 milisegundos antes de medir
    tiempoInicioMedicion = millis() +
                           TIEMPO_ESPERA_MEDICION_MS;

    enviarEstado();

  }

  // CANCELAR MEDICION
  else if (strcmp(comando, "stop") == 0) {

    medicionPendiente = false;
    monitoreoActivo = false;

    posicionarServoReposo();

    enviarEstado();

  }

  else {

    enviarError("Comando no reconocido");

  }
}

// ==========================================
// LECTURA SERIAL
// ==========================================

void leerLineaSerial(char *linea, size_t longitud) {

  if (longitud == 0 || linea[0] == '\0') {
    return;
  }

  procesarComando(linea);
}

void leerSerial() {

  while (Serial.available() > 0) {

    char caracter = static_cast<char>(Serial.read());

    if (caracter == '\r') continue;

    if (caracter == '\n') {

      bufferSerial[indiceSerial] = '\0';

      leerLineaSerial(bufferSerial, indiceSerial);

      indiceSerial = 0;

    }

    else if (indiceSerial < sizeof(bufferSerial) - 1) {

      bufferSerial[indiceSerial++] = caracter;

    }

    else {

      indiceSerial = 0;

      enviarError("Comando serial demasiado largo");

    }
  }
}

// ==========================================
// LECTURA BLUETOOTH
// ==========================================

void leerBluetooth() {

  while (SerialBT.available() > 0) {

    char caracter = static_cast<char>(SerialBT.read());

    if (caracter == '\r') continue;

    if (caracter == '\n') {

      bufferBluetooth[indiceBluetooth] = '\0';

      leerLineaSerial(
        bufferBluetooth,
        indiceBluetooth
      );

      indiceBluetooth = 0;

    }

    else if (indiceBluetooth < sizeof(bufferBluetooth) - 1) {

      bufferBluetooth[indiceBluetooth++] = caracter;

    }

    else {

      indiceBluetooth = 0;

      enviarError("Comando Bluetooth demasiado largo");

    }
  }
}

// ==========================================
// CONFIGURACION INICIAL
// ==========================================

void setup() {

  Serial.begin(115200);

  SerialBT.begin("EcoSuelo");

  // Configurar ADC
  analogReadResolution(12);

  pinMode(SENSOR_PIN, INPUT);

  // Configurar servomotor
  servoSensor.setPeriodHertz(50);

  servoSensor.attach(
    SERVO_PIN,
    500,
    2500
  );

  // Posicion inicial
  posicionarServoReposo();

  // Identificador de arranque
  identificadorArranque = esp_random();

  delay(250);

  enviarEstado();
}

// ==========================================
// BUCLE PRINCIPAL
// ==========================================

void loop() {

  // Revisar comandos USB y Bluetooth
  leerSerial();

  leerBluetooth();

  // Verificar si ya transcurrio el tiempo de espera
  if (
    medicionPendiente &&
    (int32_t)(millis() - tiempoInicioMedicion) >= 0
  ) {

    // Evitar que se inicie otra medicion
    medicionPendiente = false;

    // Tomar una sola medicion
    realizarMedicion();

    // Desactivar monitoreo
    monitoreoActivo = false;

    // Regresar el sensor a reposo
    posicionarServoReposo();

    // Informar que termino el proceso
    enviarEstado();

  }
}
