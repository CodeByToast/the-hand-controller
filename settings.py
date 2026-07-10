"""Persist user preferences (camera flip, mouse direction) across sessions."""

from __future__ import annotations

import json

import config

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


def save() -> None:
    data = {
        "mirror_camera": config.MIRROR_CAMERA,
        "invert_mouse_x": config.INVERT_MOUSE_X,
    }
    SETTINGS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
