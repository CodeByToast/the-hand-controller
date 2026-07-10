# The Hand Controller

Control your Windows PC with hand gestures using your webcam. Built with [MediaPipe Hands](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker) for real-time tracking and [pynput](https://pynput.readthedocs.io/) for mouse input.

## Gestures

| Gesture | Action |
|---|---|
| Index + thumb tap | Left click |
| Double index + thumb tap | Double left click |
| Pinky + thumb tap | Right click |
| Closed fist tap | Browser back (Alt+←) |
| Index + middle finger together (fingers out) | Move mouse |
| Index + middle finger apart, then move hand | Scroll up/down or left/right |

## Requirements

- Windows 10/11
- Python 3.9–3.12
- Webcam

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

A preview window shows the camera feed, detected hand landmarks, and the active mode. Press **Q** or **Esc** to quit. Camera flip (**C**) and mouse direction (**X**) are remembered between runs.

## Tuning

Edit `config.py` to adjust pinch sensitivity, scroll speed, mouse smoothing, and camera settings:

- `PINCH_ON` / `PINCH_OFF` — how close fingertips must be to register a pinch (lower = stricter)
- `SMOOTHING` — mouse movement smoothing (0–1, higher = more responsive)
- `SCROLL_STEP` — scroll amount per movement
- `CAMERA_INDEX` — change if you have multiple cameras
- `POINTER_RAY_EXTEND` — how far to project along your finger toward the screen (try `0.4`–`0.8`)
- `POINTER_Z_Y_SCALE` — fine-tune vertical aim for an overhead camera
- `MIRROR_CAMERA` — flip the webcam preview (or press **C** while running)
- `INVERT_MOUSE_X` — flip horizontal mouse direction (or press **X** while running)

## Tips

- Use good, even lighting and keep your full hand in frame.
- For mouse mode, pinch index + middle fingertips together (fingers out) and move your hand.
- For scrolling, spread index + middle into a peace sign, then move your hand.
- For back, make a tight closed fist briefly, then open — not a loose curl.
- Quick pinch-and-release for clicks; holding too long won't register as a tap.

## Project layout

```
main.py          Entry point and camera loop
gestures.py      Gesture detection logic
landmarks.py     MediaPipe landmark helpers
mouse_input.py   Windows mouse/scroll control
config.py        Tunable thresholds
```
