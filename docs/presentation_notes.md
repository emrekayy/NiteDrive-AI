# NiteDrive AI — Presentation Notes

## Project summary

NiteDrive AI is a real-time driver drowsiness detection system that combines computer vision, machine learning, and an Arduino-based alert module.

## Live demo talking points

- The system analyzes the driver in real time using a camera feed.
- OpenCV and MediaPipe process face and eye landmarks.
- EAR, PERCLOS, head angle, and fatigue score are computed on each frame.
- When drowsiness is detected, a serial command is sent to Arduino.
- Arduino activates LEDs and a buzzer to warn the driver before a critical situation.

## Results (test environment)

- Real-time operation at approximately 28–30 FPS
- Alarm response under 1 second
- Random Forest classifier accuracy around 92%
- Low-cost, extensible embedded architecture

## Demo video

See `demo/demo_video_link.txt` for the external demo video link.
