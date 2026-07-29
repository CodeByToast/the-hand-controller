"""Tunable thresholds for gesture detection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from calibration import CalibrationBounds

ROOT_DIR = Path(__file__).resolve().parent
MODEL_PATH = ROOT_DIR / "models" / "hand_landmarker.task"

# Index + middle fingertip gap (2D) — tips only; knuckles stay close even when spread
PINCH_TIP_2D_ON = 0.058
PINCH_TIP_2D_OFF = 0.072
PINCH_TIP_2D_TIGHT = 0.040
SPREAD_TIP_2D_ON = 0.095
SPREAD_TIP_2D_OFF = 0.085

# Closed fist (browser back) — strict to avoid accidental triggers
FIST_MAX_EXTENDED = 0
MIN_FIST_HOLD = 0.15
MAX_FIST_HOLD = 0.35
BACK_COOLDOWN = 1.5

# Thumb pinch taps (left / right click)
PINCH_ON = 0.045
PINCH_OFF = 0.060

# Tap timing (seconds)
MAX_TAP_HOLD = 0.35
DOUBLE_TAP_WINDOW = 0.40
SINGLE_TAP_DELAY = 0.28

# Mouse movement (lower = smoother / less jitter)
SMOOTHING = 0.18
MOUSE_PAD_MARGIN = 0.12
# Extrapolate cursor along wrist→finger line (overhead camera parallax fix)
POINTER_RAY_EXTEND = 0.55
POINTER_Z_Y_SCALE = -0.30

# Scrolling
SCROLL_STEP = 120
SCROLL_DEADZONE = 0.008

# MediaPipe
MAX_NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.6

# Camera / direction
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
MIRROR_CAMERA = True   # flip the preview (selfie view)
INVERT_MOUSE_X = True  # flip horizontal mouse; press X at runtime to toggle

# Filled by corner calibration (K key); None uses MOUSE_PAD_MARGIN fallback
SCREEN_CALIBRATION = None

# Set by calibration (K key); None = use MOUSE_PAD_MARGIN fallback
CALIBRATION: CalibrationBounds | None = None
