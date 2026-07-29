"""Screen corner calibration — maps hand range to full monitor."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

import config

MIN_CALIBRATION_SPAN = 0.05


@dataclass(frozen=True)
class ScreenCalibration:
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    def remap(self, norm_x: float, norm_y: float) -> tuple[float, float]:
        span_x = max(self.max_x - self.min_x, MIN_CALIBRATION_SPAN)
        span_y = max(self.max_y - self.min_y, MIN_CALIBRATION_SPAN)
        x = (norm_x - self.min_x) / span_x
        y = (norm_y - self.min_y) / span_y
        return max(0.0, min(1.0, x)), max(0.0, min(1.0, y))


class CalStep(Enum):
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_RIGHT = auto()
    BOTTOM_LEFT = auto()


STEP_PROMPTS = {
    CalStep.TOP_LEFT: "Step 1/4: Point at TOP-LEFT of screen, press SPACE",
    CalStep.TOP_RIGHT: "Step 2/4: Point at TOP-RIGHT of screen, press SPACE",
    CalStep.BOTTOM_RIGHT: "Step 3/4: Point at BOTTOM-RIGHT of screen, press SPACE",
    CalStep.BOTTOM_LEFT: "Step 4/4: Point at BOTTOM-LEFT of screen, press SPACE",
}

STEP_ORDER = (
    CalStep.TOP_LEFT,
    CalStep.TOP_RIGHT,
    CalStep.BOTTOM_RIGHT,
    CalStep.BOTTOM_LEFT,
)


class Calibrator:
    def __init__(self) -> None:
        self.active = False
        self._step_index = 0
        self._points: list[tuple[float, float]] = []
        self._message = ""

    @property
    def prompt(self) -> str:
        if not self.active:
            return ""
        return STEP_PROMPTS[STEP_ORDER[self._step_index]]

    @property
    def message(self) -> str:
        return self._message

    def start(self) -> None:
        self.active = True
        self._step_index = 0
        self._points = []
        self._message = "Calibration started. Pinch index+middle to point."

    def cancel(self) -> None:
        self.active = False
        self._step_index = 0
        self._points = []
        self._message = "Calibration cancelled."

    def capture(self, pointer: tuple[float, float] | None) -> bool:
        """Record a corner. Returns True when all four corners are captured."""
        if not self.active or pointer is None:
            self._message = "Show your hand (pinch index+middle) and try again."
            return False

        self._points.append(pointer)
        self._step_index += 1

        if self._step_index >= len(STEP_ORDER):
            result = self._build_calibration()
            self.active = False
            if result is None:
                self._message = "Range too small — press K to try again."
                return False
            config.SCREEN_CALIBRATION = result
            self._message = "Calibration saved!"
            return True

        self._message = ""
        return False

    def _build_calibration(self) -> ScreenCalibration | None:
        if len(self._points) < len(STEP_ORDER):
            return None

        xs = [p[0] for p in self._points]
        ys = [p[1] for p in self._points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        if (max_x - min_x) < MIN_CALIBRATION_SPAN or (max_y - min_y) < MIN_CALIBRATION_SPAN:
            return None

        return ScreenCalibration(min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y)


def clear_calibration() -> None:
    config.SCREEN_CALIBRATION = None


def calibration_from_dict(data: dict) -> ScreenCalibration | None:
    try:
        return ScreenCalibration(
            min_x=float(data["min_x"]),
            max_x=float(data["max_x"]),
            min_y=float(data["min_y"]),
            max_y=float(data["max_y"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def calibration_to_dict(cal: ScreenCalibration) -> dict:
    return {
        "min_x": cal.min_x,
        "max_x": cal.max_x,
        "min_y": cal.min_y,
        "max_y": cal.max_y,
    }
