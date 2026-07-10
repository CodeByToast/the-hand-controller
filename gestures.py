"""Gesture state machines built on top of hand landmarks."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Sequence

import config
from landmarks import (
    INDEX_TIP,
    MIDDLE_TIP,
    PINKY_TIP,
    THUMB_TIP,
    distance,
    finger_extended,
    is_closed_fist,
    is_mouse_pinch,
    is_scroll_spread,
    lm_xy,
    pointer_position,
)


class GestureMode(Enum):
    IDLE = auto()
    MOUSE = auto()
    SCROLL = auto()


class ClickAction(Enum):
    LEFT = auto()
    DOUBLE_LEFT = auto()
    RIGHT = auto()
    BACK = auto()


@dataclass
class GestureState:
    mode: GestureMode = GestureMode.IDLE
    click: ClickAction | None = None
    pointer_norm: tuple[float, float] | None = None
    scroll_anchor: tuple[float, float] | None = None
    tip_gap: float = 0.0


class PinchTapDetector:
    """Detect quick pinch-and-release taps for click gestures."""

    def __init__(self) -> None:
        self._active_pinch: str | None = None
        self._pinch_start = 0.0
        self._last_tap_kind: str | None = None
        self._last_tap_time = 0.0
        self._pending_single: ClickAction | None = None
        self._pending_deadline = 0.0

    def _pinch_active(self, kind: str, pinched: bool) -> bool:
        if self._active_pinch == kind:
            if not pinched:
                held = time.monotonic() - self._pinch_start
                self._active_pinch = None
                if held <= config.MAX_TAP_HOLD:
                    return True
            return False

        if pinched and self._active_pinch is None:
            self._active_pinch = kind
            self._pinch_start = time.monotonic()
        return False

    def update(
        self,
        index_thumb: bool,
        pinky_thumb: bool,
    ) -> ClickAction | None:
        now = time.monotonic()
        click: ClickAction | None = None

        if self._pending_single and now >= self._pending_deadline:
            click = self._pending_single
            self._pending_single = None

        if self._pinch_active("index_thumb", index_thumb):
            click = self._register_tap("index_thumb", ClickAction.LEFT, ClickAction.DOUBLE_LEFT)
        elif self._pinch_active("pinky_thumb", pinky_thumb):
            click = self._register_tap("pinky_thumb", ClickAction.RIGHT, None)

        return click

    def _register_tap(
        self,
        kind: str,
        single: ClickAction,
        double: ClickAction | None,
    ) -> ClickAction | None:
        now = time.monotonic()
        if (
            double is not None
            and self._last_tap_kind == kind
            and now - self._last_tap_time <= config.DOUBLE_TAP_WINDOW
        ):
            self._last_tap_kind = None
            self._pending_single = None
            return double

        self._last_tap_kind = kind
        self._last_tap_time = now

        if double is None:
            return single

        self._pending_single = single
        self._pending_deadline = now + config.SINGLE_TAP_DELAY
        return None


class FistBackDetector:
    """Deliberate fist clench + release triggers browser back."""

    def __init__(self) -> None:
        self._fist_active = False
        self._fist_start = 0.0
        self._cooldown_until = 0.0

    def update(self, is_fist: bool, *, blocked: bool) -> bool:
        now = time.monotonic()
        if blocked or now < self._cooldown_until:
            if not is_fist:
                self._fist_active = False
            return False

        if self._fist_active:
            if not is_fist:
                held = now - self._fist_start
                self._fist_active = False
                if config.MIN_FIST_HOLD <= held <= config.MAX_FIST_HOLD:
                    self._cooldown_until = now + config.BACK_COOLDOWN
                    return True
            return False

        if is_fist:
            self._fist_active = True
            self._fist_start = now
        return False


class GestureRecognizer:
    """
    Index + middle tips together  → mouse
    Index + middle tips spread    → scroll
    Quick thumb pinches (idle)    → clicks
    """

    def __init__(self) -> None:
        self._index_thumb_pinched = False
        self._pinky_thumb_pinched = False
        self._tap_detector = PinchTapDetector()
        self._fist_detector = FistBackDetector()
        self._index_middle_pinched = False

    def _tip_gap(self, landmarks: Sequence) -> float:
        return distance(lm_xy(landmarks, INDEX_TIP), lm_xy(landmarks, MIDDLE_TIP))

    def _resolve_pointer_mode(
        self,
        landmarks: Sequence,
        tip_2d: float,
        *,
        thumb_busy: bool,
    ) -> GestureMode:
        if is_closed_fist(landmarks):
            return GestureMode.IDLE

        was_pinched = self._index_middle_pinched
        mouse_pinch = is_mouse_pinch(landmarks, tip_2d, was_pinched)
        self._index_middle_pinched = mouse_pinch

        if mouse_pinch:
            return GestureMode.MOUSE

        if thumb_busy:
            return GestureMode.IDLE

        if is_scroll_spread(landmarks, tip_2d, was_pinched):
            return GestureMode.SCROLL

        return GestureMode.IDLE

    def recognize(self, landmarks: Sequence) -> GestureState:
        thumb = lm_xy(landmarks, THUMB_TIP)
        index = lm_xy(landmarks, INDEX_TIP)
        pinky = lm_xy(landmarks, PINKY_TIP)

        index_thumb_dist = distance(thumb, index)
        pinky_thumb_dist = distance(thumb, pinky)
        tip_2d = self._tip_gap(landmarks)

        if self._index_thumb_pinched:
            index_thumb = index_thumb_dist < config.PINCH_OFF
        else:
            index_thumb = index_thumb_dist < config.PINCH_ON

        if self._pinky_thumb_pinched:
            pinky_thumb = pinky_thumb_dist < config.PINCH_OFF
        else:
            pinky_thumb = pinky_thumb_dist < config.PINCH_ON

        self._index_thumb_pinched = index_thumb
        self._pinky_thumb_pinched = pinky_thumb

        fist = is_closed_fist(landmarks)
        thumb_busy = index_thumb or pinky_thumb or self._tap_detector._active_pinch is not None

        pointer = pointer_position(landmarks)
        mode = self._resolve_pointer_mode(landmarks, tip_2d, thumb_busy=thumb_busy)

        state = GestureState(tip_gap=tip_2d)

        click = self._tap_detector.update(index_thumb, pinky_thumb)
        if click is not None:
            state.click = click
        elif self._fist_detector.update(
            fist,
            blocked=thumb_busy or mode == GestureMode.MOUSE,
        ):
            state.click = ClickAction.BACK

        if mode == GestureMode.MOUSE:
            state.mode = GestureMode.MOUSE
            state.pointer_norm = pointer
        elif mode == GestureMode.SCROLL:
            state.mode = GestureMode.SCROLL
            state.scroll_anchor = pointer
        else:
            state.mode = GestureMode.IDLE

        return state
