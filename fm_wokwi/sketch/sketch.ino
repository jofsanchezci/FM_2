// FM didactica: TX por acumulador de fase, RX por periodo entre flancos.
// Arduino UNO: conectar D9 (TX) a D2 (RX). No genera radiofrecuencia.
#include <Arduino.h>
#include <avr/interrupt.h>
#include <util/atomic.h>
#include <math.h>

const float FS = 20000.0f;
const float FC = 200.0f;
const float FM = 0.5f;
volatile uint32_t incremento = 42949673UL;
volatile uint32_t fase = 0;
volatile uint32_t ultimoFlanco = 0, periodo = 0;
volatile bool valido = false;

ISR(TIMER1_COMPA_vect) {
  fase += incremento;
  // D9 = PB1: amplitud logica fija, frecuencia variable.
  if (fase & 0x80000000UL) PORTB |= _BV(PB1);
  else PORTB &= ~_BV(PB1);
}

void flancoRecibido() {
  uint32_t ahora = micros();
  if (ultimoFlanco != 0) {
    periodo = ahora - ultimoFlanco;
    valido = true;
  }
  ultimoFlanco = ahora;
}

void setup() {
  pinMode(9, OUTPUT);
  pinMode(2, INPUT);
  Serial.begin(115200);
  attachInterrupt(digitalPinToInterrupt(2), flancoRecibido, RISING);
  // Timer1: 16 MHz / 8 / 100 = 20 kHz. No usar analogWrite en D9/D10.
  noInterrupts();
  TCCR1A = 0;
  TCCR1B = _BV(WGM12) | _BV(CS11);
  TCNT1 = 0;
  OCR1A = 99;
  TIMSK1 = _BV(OCIE1A);
  interrupts();
}

void loop() {
  static uint32_t ultimaActualizacion = 0, ultimaImpresion = 0;
  static float mensaje = 0, recuperado = 0;
  // El potenciometro ajusta desviacion entre 20 y 120 Hz.
  // Lectura lenta: suficiente para el mensaje de 0.5 Hz.
  static float desviacion = 70;
  uint32_t ahora = micros();
  if (ahora - ultimaActualizacion >= 2000UL) {
    ultimaActualizacion = ahora;
    desviacion = 20.0f + analogRead(A0) * (100.0f / 1023.0f);
    // Modulo temporal evita perder precision al funcionar mucho tiempo.
    float tiempo = (ahora % 2000000UL) * 1e-6f;
    mensaje = sinf(2.0f * PI * FM * tiempo);
    float frecuencia = FC + desviacion * mensaje;
    uint32_t nuevo = (uint32_t)(frecuencia * (4294967296.0f / FS));
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { incremento = nuevo; }
  }
  if (ahora - ultimaImpresion >= 25000UL) {
    ultimaImpresion = ahora;
    uint32_t p, borde;
    bool hay;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
      p = periodo; borde = ultimoFlanco; hay = valido;
    }
    if (hay && p > 0 && ahora - borde < 100000UL) {
      float frecuenciaRX = 1000000.0f / p;
      float estimacion = (frecuenciaRX - FC) / desviacion;
      recuperado += 0.6f * (estimacion - recuperado);
      Serial.print("Mensaje:"); Serial.print(mensaje, 3);
      Serial.print("\tRecuperado:"); Serial.print(recuperado, 3);
      Serial.println("\tMin:-1.3\tMax:1.3");
    }
  }
}
