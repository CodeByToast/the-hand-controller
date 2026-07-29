"""Windows mouse and scroll control via pynput."""

from __future__ import annotations

import ctypes
from ctypes import wintypes

import config
from gestures import ClickAction, GestureMode, GestureState
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Button, Controller

_mouse = Controller()
_keyboard = KeyboardController()

_user32 = ctypes.windll.user32
_screen_w = _user32.GetSystemMetrics(0)
_screen_h = _user32.GetSystemMetrics(1)


class SmoothPointer:
    def __init__(self, factor: float = config.SMOOTHING) -> None:
        self._factor = factor
        self._x: float | None = None
        self._y: float | None = None

    def reset(self) -> None:
        self._x = None
        self._y = None

    def map_to_screen(self, norm_x: float, norm_y: float) -> tuple[int, int]:
        if config.SCREEN_CALIBRATION is not None:
            x, y = config.SCREEN_CALIBRATION.remap(norm_x, norm_y)
        else:
            margin = config.MOUSE_PAD_MARGIN
            x = (norm_x - margin) / (1.0 - 2 * margin)
            y = (norm_y - margin) / (1.0 - 2 * margin)
            x = max(0.0, min(1.0, x))
            y = max(0.0, min(1.0, y))

        raw_x = (1.0 - x) if config.INVERT_MOUSE_X else x
        screen_y = y

        target_x = raw_x * _screen_w
        target_y = screen_y * _screen_h

        if self._x is None or self._y is None:
            self._x, self._y = target_x, target_y
        else:
            self._x += (target_x - self._x) * self._factor
            self._y += (target_y - self._y) * self._factor

        return int(self._x), int(self._y)


class ScrollTracker:
    def __init__(self) -> None:
        self._anchor: tuple[float, float] | None = None

    def reset(self) -> None:
        self._anchor = None

    def update(self, norm_x: float, norm_y: float) -> None:
        if self._anchor is None:
            self._anchor = (norm_x, norm_y)
            return

        dx = norm_x - self._anchor[0]
        dy = norm_y - self._anchor[1]
        self._anchor = (norm_x, norm_y)

        if config.INVERT_MOUSE_X:
            dx = -dx

        if abs(dy) >= abs(dx) and abs(dy) > config.SCROLL_DEADZONE:
            steps = max(1, int(abs(dy) / config.SCROLL_DEADZONE))
            _mouse.scroll(0, -int(dy / abs(dy)) * steps * (config.SCROLL_STEP // 3))
        elif abs(dx) > config.SCROLL_DEADZONE:
            steps = max(1, int(abs(dx) / config.SCROLL_DEADZONE))
            _horizontal_scroll(-int(dx / abs(dx)) * steps * (config.SCROLL_STEP // 3))


def _horizontal_scroll(amount: int) -> None:
    """Send a horizontal wheel event on Windows."""
    MOUSEEVENTF_HWHEEL = 0x0800
    WHEEL_DELTA = 120

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
        ]

    class INPUT(ctypes.Structure):
        class _U(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT)]

        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", _U)]

    inp = INPUT()
    inp.type = 0  # INPUT_MOUSE
    inp.mi.dx = 0
    inp.mi.dy = 0
    inp.mi.mouseData = amount * WHEEL_DELTA
    inp.mi.dwFlags = MOUSEEVENTF_HWHEEL
    inp.mi.time = 0
    inp.mi.dwExtraInfo = None
    _user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


class MouseController:
    def __init__(self) -> None:
        self._pointer = SmoothPointer()
        self._scroll = ScrollTracker()
        self._last_mode = GestureMode.IDLE

    def apply(self, state: GestureState) -> None:
        if state.mode != self._last_mode:
            if state.mode == GestureMode.IDLE:
                self._pointer.reset()
            if state.mode != GestureMode.SCROLL:
                self._scroll.reset()
            self._last_mode = state.mode

        if state.click == ClickAction.LEFT:
            _mouse.click(Button.left, 1)
        elif state.click == ClickAction.DOUBLE_LEFT:
            _mouse.click(Button.left, 2)
        elif state.click == ClickAction.RIGHT:
            _mouse.click(Button.right, 1)
        elif state.click == ClickAction.BACK:
            with _keyboard.pressed(Key.alt):
                _keyboard.press(Key.left)
                _keyboard.release(Key.left)

        if state.mode == GestureMode.MOUSE and state.pointer_norm is not None:
            x, y = self._pointer.map_to_screen(*state.pointer_norm)
            _mouse.position = (x, y)

        if state.mode == GestureMode.SCROLL and state.scroll_anchor is not None:
            self._scroll.update(*state.scroll_anchor)
