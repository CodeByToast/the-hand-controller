"""Persist user preferences (camera flip, mouse direction) across sessions."""

from __future__ import annotations

import json

from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from calibration import ScreenCalibration
from calibration import calibration_from_dict, calibration_to_dict, clear_calibration

SETTINGS_PATH = config.ROOT_DIR / "user_settings.json"


def load() -> None:
    if not SETTINGS_PATH.is_file():
        return

    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return

    if "mirror_camera" in data:
        config.MIRROR_CAMERA = bool(data["mirror_camera"])
    if "invert_mouse_x" in data:
        config.INVERT_MOUSE_X = bool(data["invert_mouse_x"])

    cal_data = data.get("calibration")
    if cal_data:
        cal = calibration_from_dict(cal_data)
        config.SCREEN_CALIBRATION = cal
    else:
        config.SCREEN_CALIBRATION = None


def save() -> None:
    data = {
        "mirror_camera": config.MIRROR_CAMERA,
        "invert_mouse_x": config.INVERT_MOUSE_X,
    }
    if config.SCREEN_CALIBRATION is not None:
        data["calibration"] = calibration_to_dict(config.SCREEN_CALIBRATION)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def clear_calibration_and_save() -> None:
    clear_calibration()
    save()
