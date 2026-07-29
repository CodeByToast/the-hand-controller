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
from calibration import Calibrator
from gestures import GestureMode, GestureRecognizer
from landmarks import pointer_position
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
        f"{fps:.0f} FPS  |  calibrate: K  |  cam: {mirror_cam} (C)  |  flip: {mirror_x} (X)  |  Q quit",
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


def draw_calibration_overlay(frame, calibrator: Calibrator, pointer: tuple[float, float] | None) -> None:
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (20, 40, 80), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    cv2.putText(
        frame,
        "CALIBRATION",
        (16, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (80, 200, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        calibrator.prompt,
        (16, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (240, 240, 240),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "Pinch index+middle to point. SPACE=capture  ESC=cancel",
        (16, 115),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )

    if calibrator.message:
        cv2.putText(
            frame,
            calibrator.message,
            (16, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (100, 255, 150),
            2,
            cv2.LINE_AA,
        )

    # Corner guides
    pad = 28
    cv2.circle(frame, (pad, pad), 10, (0, 255, 255), 2)
    cv2.circle(frame, (w - pad, pad), 10, (0, 255, 255), 2)
    cv2.circle(frame, (w - pad, h - pad), 10, (0, 255, 255), 2)
    cv2.circle(frame, (pad, h - pad), 10, (0, 255, 255), 2)

    if pointer is not None:
        px = int(pointer[0] * w)
        py = int(pointer[1] * h)
        cv2.circle(frame, (px, py), 14, (0, 255, 255), 2)
        cv2.circle(frame, (px, py), 4, (0, 255, 255), -1)


def draw_calibration_bounds(frame) -> None:
    cal = config.SCREEN_CALIBRATION
    if cal is None:
        return
    h, w = frame.shape[:2]
    x1 = int(cal.min_x * w)
    y1 = int(cal.min_y * h)
    x2 = int(cal.max_x * w)
    y2 = int(cal.max_y * h)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 180, 0), 1)


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
    calibrator = Calibrator()
    current_mode = GestureMode.IDLE
    tip_gap = 0.0
    last_pointer: tuple[float, float] | None = None

    frame_ts_ms = 0
    fps_clock = time.perf_counter()
    fps = 30.0

    print("Hand Controller running. Press Q to quit, K to calibrate.")

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

            last_pointer = None
            if result.hand_landmarks:
                for hand_landmarks in result.hand_landmarks:
                    drawing_utils.draw_landmarks(
                        frame,
                        hand_landmarks,
                        HandLandmarksConnections.HAND_CONNECTIONS,
                    )
                    last_pointer = pointer_position(hand_landmarks)

                    if calibrator.active:
                        continue

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

            if calibrator.active:
                draw_calibration_overlay(frame, calibrator, last_pointer)
            else:
                draw_calibration_bounds(frame)
                draw_overlay(frame, current_mode, fps, tip_gap)
            cv2.imshow("Hand Controller", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q")) and not calibrator.active:
                break
            if key == 27:
                if calibrator.active:
                    calibrator.cancel()
                else:
                    break
            if key == ord(" ") and calibrator.active:
                if calibrator.capture(last_pointer):
                    settings.save()
                    mouse._pointer.reset()
                    print("Calibration saved.")
            if key in (ord("k"), ord("K")):
                if calibrator.active:
                    calibrator.cancel()
                else:
                    calibrator.start()
                    print("Calibration started — follow on-screen prompts.")
            if key in (ord("r"), ord("R")) and not calibrator.active:
                settings.clear_calibration_and_save()
                mouse._pointer.reset()
                print("Calibration cleared.")
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
