#include <ESP32Servo.h>
#include <esp_system.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// Pines correspondientes a las conexiones indicadas para EcoSuelo.
constexpr uint8_t SENSOR_PIN = 34;
constexpr uint8_t SERVO_PIN = 18;
constexpr uint8_t NUM_LECTURAS = 20;
constexpr uint32_t ESPERA_CONTACTO_MS = 1000;
constexpr uint32_t ESPERA_ENTRE_LECTURAS_MS = 10;

// Sustituye estos extremos tras calibrar el sensor en suelo seco y húmedo.
// En ESP32 la lectura ADC configurada abajo va de 0 a 4095.
constexpr int ADC_SECO = 4095;
constexpr int ADC_HUMEDO = 0;
static_assert(ADC_SECO != ADC_HUMEDO, "Los valores de calibracion deben diferir.");

Servo servoSensor;
char bufferSerial[128];
size_t indiceSerial = 0;
bool monitoreoActivo = false;
uint32_t intervaloMs = 10000;
uint32_t ultimaMedicionMs = 0;
uint32_t secuencia = 0;
uint32_t identificadorArranque = 0;

void enviarEstado() {
  Serial.printf(
      "{\"type\":\"status\",\"connected\":true,\"monitoring\":%s,"
      "\"interval_ms\":%lu}\n",
      monitoreoActivo ? "true" : "false",
      static_cast<unsigned long>(intervaloMs));
}

void enviarError(const char *mensaje) {
  Serial.printf("{\"type\":\"error\",\"message\":\"%s\"}\n", mensaje);
}

bool leerCampoCadena(const char *json, const char *clave, char *salida,
                     size_t capacidad) {
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
  size_t largo = static_cast<size_t>(fin - (posicion + 1));
  if (largo == 0 || largo >= capacidad) return false;
  memcpy(salida, posicion + 1, largo);
  salida[largo] = '\0';
  return true;
}

bool leerCampoEntero(const char *json, const char *clave, uint32_t *valor) {
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

void procesarComando(const char *json) {
  char comando[16];
  if (!leerCampoCadena(json, "command", comando, sizeof(comando))) {
    enviarError("Comando JSON no valido");
    return;
  }

  if (strcmp(comando, "start") == 0) {
    uint32_t nuevoIntervalo = 0;
    if (!leerCampoEntero(json, "interval_ms", &nuevoIntervalo) ||
        nuevoIntervalo < 1000 || nuevoIntervalo > 86400000UL) {
      enviarError("interval_ms debe estar entre 1000 y 86400000");
      return;
    }
    intervaloMs = nuevoIntervalo;
    monitoreoActivo = true;
    ultimaMedicionMs = millis();
    enviarEstado();
  } else if (strcmp(comando, "stop") == 0) {
    monitoreoActivo = false;
    servoSensor.write(0);
    enviarEstado();
  } else if (strcmp(comando, "status") == 0) {
    enviarEstado();
  } else {
    enviarError("Comando no reconocido");
  }
}

void leerSerial() {
  while (Serial.available() > 0) {
    char caracter = static_cast<char>(Serial.read());
    if (caracter == '\r') continue;
    if (caracter == '\n') {
      bufferSerial[indiceSerial] = '\0';
      if (indiceSerial > 0) procesarComando(bufferSerial);
      indiceSerial = 0;
    } else if (indiceSerial < sizeof(bufferSerial) - 1) {
      bufferSerial[indiceSerial++] = caracter;
    } else {
      indiceSerial = 0;
      enviarError("Comando serial demasiado largo");
    }
  }
}

void realizarMedicion() {
  servoSensor.write(90);
  delay(ESPERA_CONTACTO_MS);

  uint32_t suma = 0;
  for (uint8_t indice = 0; indice < NUM_LECTURAS; indice++) {
    suma += analogRead(SENSOR_PIN);
    delay(ESPERA_ENTRE_LECTURAS_MS);
  }
  uint16_t adcPromedio = static_cast<uint16_t>(
      (suma + NUM_LECTURAS / 2) / NUM_LECTURAS);

  // El servo siempre vuelve a la posición inicial al terminar la lectura.
  servoSensor.write(0);

  float humedad = (static_cast<float>(ADC_SECO) - adcPromedio) * 100.0f /
                  (static_cast<float>(ADC_SECO) - ADC_HUMEDO);
  if (humedad < 0.0f) humedad = 0.0f;
  if (humedad > 100.0f) humedad = 100.0f;

  char id[32];
  snprintf(id, sizeof(id), "%08lx-%lu",
           static_cast<unsigned long>(identificadorArranque),
           static_cast<unsigned long>(++secuencia));
  uint16_t humedadDecimas = static_cast<uint16_t>(lroundf(humedad * 10.0f));
  Serial.printf(
      "{\"type\":\"measurement\",\"id\":\"%s\",\"seq\":%lu,"
      "\"adc\":%u,\"humidity\":%u.%u}\n",
      id, static_cast<unsigned long>(secuencia),
      static_cast<unsigned int>(adcPromedio),
      static_cast<unsigned int>(humedadDecimas / 10),
      static_cast<unsigned int>(humedadDecimas % 10));
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  pinMode(SENSOR_PIN, INPUT);
  servoSensor.setPeriodHertz(50);
  servoSensor.attach(SERVO_PIN, 500, 2500);
  servoSensor.write(0);
  identificadorArranque = esp_random();
  delay(250);
  enviarEstado();
}

void loop() {
  leerSerial();
  uint32_t ahora = millis();
  if (monitoreoActivo &&
      static_cast<uint32_t>(ahora - ultimaMedicionMs) >= intervaloMs) {
    ultimaMedicionMs = ahora;
    realizarMedicion();
  }
}
