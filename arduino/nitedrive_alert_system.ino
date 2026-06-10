/*
 * Drowsiness — Python ai_live_arduino.py ile uyumlu seri protokol.
 * Satir: SAFE, WARNING, DANGER + LF (ASCII)
 *
 * SERIAL_DEBUG 1 yapilirsa gelen satir USB uzerinden loglanir.
 */
#include <string.h>

#define SERIAL_DEBUG 0

const int BUZZER_PIN = 8;
const int LED_SAFE = 9;
const int LED_WARN = 10;
const int LED_DANGER = 11;
const int MOTOR_PWM_PIN = 5;

enum Mode : uint8_t { MODE_SAFE = 0, MODE_WARN, MODE_DANG };

Mode mode = MODE_SAFE;

// String sinifi yerine sabit buffer: parca mesaj / heap sorunlarini onler
static char lineBuf[48];
static uint8_t lineLen = 0;

const uint16_t buzzWarn[] = {70, 150, 70, 450};
const uint8_t buzzWarnLen = sizeof(buzzWarn) / sizeof(buzzWarn[0]);

const uint16_t buzzDanger[] = {50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 180};
const uint8_t buzzDangerLen = sizeof(buzzDanger) / sizeof(buzzDanger[0]);

uint8_t buzzIdx = 0;
bool buzzOn = false;
unsigned long buzzNext = 0;

static void toUpperAscii(char* s) {
  for (; *s; ++s) {
    if (*s >= 'a' && *s <= 'z') *s = (char)(*s - 'a' + 'A');
  }
}

static void trimInPlace(char* s) {
  char* p = s;
  while (*p == ' ' || *p == '\t' || *p == '\r') p++;
  if (p != s) memmove(s, p, strlen(p) + 1);
  size_t L = strlen(s);
  while (L > 0 && (s[L - 1] == ' ' || s[L - 1] == '\t' || s[L - 1] == '\r')) {
    s[L - 1] = '\0';
    L--;
  }
}

void setLeds(bool g, bool y, bool r) {
  digitalWrite(LED_SAFE, g ? HIGH : LOW);
  digitalWrite(LED_WARN, y ? HIGH : LOW);
  digitalWrite(LED_DANGER, r ? HIGH : LOW);
}

void applyMode() {
  buzzIdx = 0;
  buzzOn = false;
  buzzNext = 0;
  digitalWrite(BUZZER_PIN, LOW);

  switch (mode) {
    case MODE_SAFE:
      analogWrite(MOTOR_PWM_PIN, 0);
      setLeds(true, false, false);
      break;
    case MODE_WARN:
      analogWrite(MOTOR_PWM_PIN, 110);
      setLeds(false, true, false);
      break;
    case MODE_DANG:
      analogWrite(MOTOR_PWM_PIN, 255);
      setLeds(false, false, true);
      break;
  }
}

void parseLine(char* s) {
  trimInPlace(s);
  if (s[0] == '\0') return;
  toUpperAscii(s);

  if (strcmp(s, "SAFE") == 0) mode = MODE_SAFE;
  else if (strcmp(s, "WARNING") == 0) mode = MODE_WARN;
  else if (strcmp(s, "DANGER") == 0) mode = MODE_DANG;
  else return;

#if SERIAL_DEBUG
  Serial.print(F("RX ok -> mode "));
  Serial.println((int)mode);
#endif
  applyMode();
}

void buzzerUpdate(unsigned long now) {
  if (mode == MODE_SAFE) {
    digitalWrite(BUZZER_PIN, LOW);
    return;
  }

  const uint16_t* seq = (mode == MODE_WARN) ? buzzWarn : buzzDanger;
  const uint8_t len = (mode == MODE_WARN) ? buzzWarnLen : buzzDangerLen;

  if (buzzNext == 0) {
    buzzNext = now;
  }
  if ((long)(now - buzzNext) < 0) return;

  uint16_t dur = seq[buzzIdx % len];
  buzzOn = !buzzOn;
  digitalWrite(BUZZER_PIN, buzzOn ? HIGH : LOW);
  buzzNext = now + dur;
  buzzIdx++;
}

void ledPulse(unsigned long now) {
  if (mode == MODE_WARN) {
    bool b = ((now / 350) % 2) == 0;
    digitalWrite(LED_WARN, b ? HIGH : LOW);
  } else if (mode == MODE_DANG) {
    bool b = ((now / 120) % 2) == 0;
    digitalWrite(LED_DANGER, b ? HIGH : LOW);
  }
}

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_SAFE, OUTPUT);
  pinMode(LED_WARN, OUTPUT);
  pinMode(LED_DANGER, OUTPUT);
  pinMode(MOTOR_PWM_PIN, OUTPUT);

  Serial.begin(9600);
  lineLen = 0;
  lineBuf[0] = '\0';
  mode = MODE_SAFE;
  applyMode();
}

void loop() {
  unsigned long now = millis();

  while (Serial.available() > 0) {
    int r = Serial.read();
    if (r < 0) break;
    char c = (char)r;
    if (c == '\r') continue;
    if (c == '\n') {
      if (lineLen >= sizeof(lineBuf)) lineLen = sizeof(lineBuf) - 1;
      lineBuf[lineLen] = '\0';
#if SERIAL_DEBUG
      Serial.print(F("RX raw: ["));
      Serial.print(lineBuf);
      Serial.println(F("]"));
#endif
      parseLine(lineBuf);
      lineLen = 0;
      lineBuf[0] = '\0';
    } else {
      if (lineLen < sizeof(lineBuf) - 1) {
        lineBuf[lineLen++] = c;
      } else {
        // Tampon tasmasi: satiri birak, yeni satira hazirlan
        lineLen = 0;
        lineBuf[0] = '\0';
      }
    }
  }

  buzzerUpdate(now);
  ledPulse(now);
}
