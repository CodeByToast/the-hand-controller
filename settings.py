"""Persist user preferences (camera flip, mouse direction) across sessions."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from calibration import ScreenCalibration
from calibration import calibration_from_dict, calibration_to_dict, clear_calibration

if sys.platform == "win32":
    SETTINGS_DIR = (
        Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        / "TheHandController"
    )
else:
    SETTINGS_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "TheHandController"
SETTINGS_PATH = SETTINGS_DIR / "user_settings.json"


def load() -> None:
    source_path = SETTINGS_PATH
    if not source_path.is_file():
        legacy_path = config.ROOT_DIR / "user_settings.json"
        if not legacy_path.is_file():
            return
        source_path = legacy_path

    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return
    if not isinstance(data, dict):
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


def save() -> bool:
    data = {
        "mirror_camera": config.MIRROR_CAMERA,
        "invert_mouse_x": config.INVERT_MOUSE_X,
    }
    if config.SCREEN_CALIBRATION is not None:
        data["calibration"] = calibration_to_dict(config.SCREEN_CALIBRATION)
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError:
        print(f"Preferences could not be saved. Check write access to: {SETTINGS_DIR}")
        return False
    return True


def clear_calibration_and_save() -> None:
    clear_calibration()
    save()
