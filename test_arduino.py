import serial
import time

import glob

BAUD = 9600


def find_port() -> str:
    ports = sorted(glob.glob("/dev/cu.usbserial*"))
    if not ports:
        raise SystemExit("Arduino portu yok. USB takın.")
    return ports[-1]


def send_line(ser: serial.Serial, cmd: str) -> None:
    ser.write((cmd + "\n").encode("ascii"))
    ser.flush()


PORT = find_port()
print(f"Port: {PORT}")
arduino = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

print("WARNING (3s) — sarı LED / orta PWM / yumuşak buzzer")
send_line(arduino, "WARNING")
time.sleep(3)

print("DANGER (3s) — kırmızı / tam PWM / hızlı buzzer")
send_line(arduino, "DANGER")
time.sleep(3)

print("SAFE — normal")
send_line(arduino, "SAFE")

arduino.close()
print("BITTI")
