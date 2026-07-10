"""MediaPipe hand landmark helpers."""

from __future__ import annotations

import math
from typing import Sequence

import config

# Standard 21-point hand model indices
WRIST = 0
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_TIP = 8
INDEX_PIP = 6
MIDDLE_MCP = 9
MIDDLE_TIP = 12
MIDDLE_PIP = 10
RING_TIP = 16
RING_PIP = 14
PINKY_TIP = 20
PINKY_PIP = 18


def lm_xy(landmarks: Sequence, index: int) -> tuple[float, float]:
    point = landmarks[index]
    return point.x, point.y


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def finger_extended(
    landmarks: Sequence,
    tip: int,
    pip: int,
    wrist: int = WRIST,
) -> bool:
    """True when the fingertip is farther from the wrist than the PIP joint."""
    wrist_pt = lm_xy(landmarks, wrist)
    tip_pt = lm_xy(landmarks, tip)
    pip_pt = lm_xy(landmarks, pip)
    return distance(tip_pt, wrist_pt) > distance(pip_pt, wrist_pt) * 1.05


def lm_xyz(landmarks: Sequence, index: int) -> tuple[float, float, float]:
    point = landmarks[index]
    return point.x, point.y, point.z


def distance_3d(
    landmarks: Sequence,
    a: int,
    b: int,
) -> float:
    ax, ay, az = lm_xyz(landmarks, a)
    bx, by, bz = lm_xyz(landmarks, b)
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def pointer_position(landmarks: Sequence) -> tuple[float, float]:
    """
    Project cursor along the wrist→fingertip line so pointing at the screen
    feels natural with an overhead camera (parallax correction).
    """
    wrist = lm_xy(landmarks, WRIST)
    tip = midpoint(lm_xy(landmarks, INDEX_TIP), lm_xy(landmarks, MIDDLE_TIP))

    dx = tip[0] - wrist[0]
    dy = tip[1] - wrist[1]
    extend = config.POINTER_RAY_EXTEND

    _, _, index_z = lm_xyz(landmarks, INDEX_TIP)
    _, _, middle_z = lm_xyz(landmarks, MIDDLE_TIP)
    z_shift = ((index_z + middle_z) / 2) * config.POINTER_Z_Y_SCALE

    return (
        _clamp01(tip[0] + dx * extend),
        _clamp01(tip[1] + dy * extend + z_shift),
    )


def midpoint(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2


def _extended_count(landmarks: Sequence) -> int:
    pairs = (
        (INDEX_TIP, INDEX_PIP),
        (MIDDLE_TIP, MIDDLE_PIP),
        (RING_TIP, RING_PIP),
        (PINKY_TIP, PINKY_PIP),
    )
    return sum(1 for tip, pip in pairs if finger_extended(landmarks, tip, pip))


def is_closed_fist(landmarks: Sequence) -> bool:
    """True when all fingers and thumb are clearly curled."""
    if _extended_count(landmarks) > config.FIST_MAX_EXTENDED:
        return False
    thumb_near_palm = distance(lm_xy(landmarks, THUMB_TIP), lm_xy(landmarks, INDEX_MCP)) < 0.09
    return thumb_near_palm


def is_mouse_pinch(landmarks: Sequence, tip_2d: float, was_pinched: bool) -> bool:
    """Index + middle tips together with fingers out — not a fist."""
    if is_closed_fist(landmarks):
        return False

    threshold = config.PINCH_TIP_2D_OFF if was_pinched else config.PINCH_TIP_2D_ON
    if tip_2d >= threshold:
        return False

    index_out = finger_extended(landmarks, INDEX_TIP, INDEX_PIP)
    middle_out = finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP)
    if index_out and middle_out:
        return True

    return tip_2d < config.PINCH_TIP_2D_TIGHT and _extended_count(landmarks) >= 2


def is_scroll_spread(landmarks: Sequence, tip_2d: float, was_pinched: bool) -> bool:
    """Peace-sign spread: both fingers out and tips clearly apart."""
    threshold = config.SPREAD_TIP_2D_OFF if was_pinched else config.SPREAD_TIP_2D_ON
    if tip_2d <= threshold:
        return False

    return (
        finger_extended(landmarks, INDEX_TIP, INDEX_PIP)
        and finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP)
    )
