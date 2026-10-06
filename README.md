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
- 64-bit Python 3.9 or newer; package availability can limit support for the newest releases
- Webcam

## Setup

On Windows, double-click `install.bat`. It uses the Windows Python Launcher to select your default Python 3 (or `python` if the launcher is unavailable), creates an isolated environment, and installs the required packages. An internet connection is needed for first-time setup. Python 3.13.5 is supported by the app's current installed dependencies; newer versions can work when compatible package builds are available.

Manual setup:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
run.bat
```

After installation, double-click `run.bat` to start the app. On its first run, it creates a **The Hand Controller** shortcut on your Desktop; later runs leave that shortcut in place. You can also launch manually with `.venv\Scripts\python.exe main.py`. Preferences are stored in your Windows user profile, so the app folder does not need write access.

A preview window shows the camera feed, detected hand landmarks, and the active mode. Press **Q** or **Esc** to quit. Press **C** to turn the camera off or back on, **M** to mirror the preview, and **X** to reverse mouse direction. Mirror and mouse settings are remembered between runs.

At startup, the app probes common camera resolutions and uses the highest mode it can confirm from captured frames. MediaPipe processes those same frames; its model chooses its own internal input scaling. Higher camera resolutions can increase processing load.

### Calibration

Press **K** to calibrate pointer range (saved automatically):

1. Pinch index + middle and point at the **top-left** of your screen → **SPACE**
2. Point at **top-right** → **SPACE**
3. Point at **bottom-right** → **SPACE**
4. Point at **bottom-left** → **SPACE**

Your hand positions are mapped to the full screen, removing dead zones at the edges. Press **R** to reset calibration.

## Tuning

Edit `config.py` to adjust pinch sensitivity, scroll speed, mouse smoothing, and camera settings:

- `PINCH_ON` / `PINCH_OFF` — how close fingertips must be to register a pinch (lower = stricter)
- `SMOOTHING` — mouse movement smoothing (0–1, higher = more responsive)
- `SCROLL_STEP` — scroll amount per movement
- `CAMERA_INDEX` — change if you have multiple cameras
- `POINTER_RAY_EXTEND` — how far to project along your finger toward the screen (try `0.4`–`0.8`)
- `POINTER_Z_Y_SCALE` — fine-tune vertical aim for an overhead camera
- `MIRROR_CAMERA` — flip the webcam preview (or press **M** while running)
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
