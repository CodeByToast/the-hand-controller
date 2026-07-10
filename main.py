"""
Hand Controller — control Windows with hand gestures via MediaPipe.

Gestures:
  - Index + thumb tap        → left click
  - Double index + thumb tap → double left click
  - Pinky + thumb tap        → right click
  - Index + middle together  → move mouse
  - Index + middle apart     → scroll (move hand)
"""

from __future__ import annotations

import sys
import time

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarksConnections

import config
from gestures import GestureMode, GestureRecognizer
from mouse_input import MouseController
import settings

MODE_LABELS = {
    GestureMode.IDLE: "idle",
    GestureMode.MOUSE: "mouse",
    GestureMode.SCROLL: "scroll",
}

MODE_COLORS = {
    GestureMode.IDLE: (180, 180, 180),
    GestureMode.MOUSE: (80, 220, 80),
    GestureMode.SCROLL: (80, 180, 255),
}


def create_hand_landmarker() -> vision.HandLandmarker:
    if not config.MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Missing model at {config.MODEL_PATH}. "
            "Download hand_landmarker.task from Google's MediaPipe model zoo."
        )

    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(config.MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=config.MAX_NUM_HANDS,
        min_hand_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
        min_hand_presence_confidence=config.MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
    )
    return vision.HandLandmarker.create_from_options(options)


def draw_overlay(frame, mode: GestureMode, fps: float, tip_gap: float = 0.0) -> None:
    h, w = frame.shape[:2]
    label = MODE_LABELS[mode]
    color = MODE_COLORS[mode]
    mirror_x = "on" if config.INVERT_MOUSE_X else "off"
    mirror_cam = "on" if config.MIRROR_CAMERA else "off"

    cv2.rectangle(frame, (0, 0), (w, 100), (30, 30, 30), -1)
    cv2.putText(
        frame,
        f"Mode: {label.upper()}  |  finger gap: {tip_gap:.3f}",
        (16, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"{fps:.0f} FPS  |  cam mirror: {mirror_cam} (C)  |  mouse flip: {mirror_x} (X)  |  Q quit",
        (16, 54),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "Tips together+out=mouse | Peace-sign spread=scroll | Tight fist tap=back",
        (16, 76),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (180, 180, 180),
        1,
        cv2.LINE_AA,
    )

    hints = [
        "Index+thumb tap: left click",
        "Double index+thumb: double click",
        "Pinky+thumb tap: right click",
        "Closed fist tap: browser back",
    ]
    y = h - 16
    for hint in reversed(hints):
        cv2.putText(
            frame,
            hint,
            (16, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (210, 210, 210),
            1,
            cv2.LINE_AA,
        )
        y -= 20


def main() -> int:
    settings.load()

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        print("Could not open webcam. Check CAMERA_INDEX in config.py.")
        return 1

    landmarker = create_hand_landmarker()
    recognizer = GestureRecognizer()
    mouse = MouseController()
    current_mode = GestureMode.IDLE
    tip_gap = 0.0

    frame_ts_ms = 0
    fps_clock = time.perf_counter()
    fps = 30.0

    print("Hand Controller running. Press Q in the preview window to quit.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read camera frame.")
                break

            now = time.perf_counter()
            fps = 0.9 * fps + 0.1 / max(now - fps_clock, 1e-6)
            fps_clock = now

            frame = cv2.flip(frame, 1) if config.MIRROR_CAMERA else frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            frame_ts_ms += 33
            result = landmarker.detect_for_video(mp_image, frame_ts_ms)

            if result.hand_landmarks:
                for hand_landmarks in result.hand_landmarks:
                    drawing_utils.draw_landmarks(
                        frame,
                        hand_landmarks,
                        HandLandmarksConnections.HAND_CONNECTIONS,
                    )
                    state = recognizer.recognize(hand_landmarks)
                    mouse.apply(state)
                    current_mode = state.mode
                    tip_gap = state.tip_gap
                    if state.pointer_norm and current_mode == GestureMode.MOUSE:
                        h, w = frame.shape[:2]
                        px = int(state.pointer_norm[0] * w)
                        py = int(state.pointer_norm[1] * h)
                        cv2.circle(frame, (px, py), 12, (0, 255, 255), 2)
                        cv2.circle(frame, (px, py), 3, (0, 255, 255), -1)

            draw_overlay(frame, current_mode, fps, tip_gap)
            cv2.imshow("Hand Controller", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
            if key in (ord("x"), ord("X")):
                config.INVERT_MOUSE_X = not config.INVERT_MOUSE_X
                settings.save()
                print(f"INVERT_MOUSE_X = {config.INVERT_MOUSE_X}")
            if key in (ord("c"), ord("C")):
                config.MIRROR_CAMERA = not config.MIRROR_CAMERA
                settings.save()
                print(f"MIRROR_CAMERA = {config.MIRROR_CAMERA}")
    finally:
        settings.save()
        cap.release()
        cv2.destroyAllWindows()
        landmarker.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
