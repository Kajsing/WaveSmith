"""Base visual primitives."""

from dataclasses import dataclass
from typing import Any

from PIL import Image, ImageDraw


@dataclass(frozen=True)
class FrameContext:
    """Shared drawing context for one rendered frame."""

    image: Image.Image
    draw: ImageDraw.ImageDraw
    width: int
    height: int
    time_seconds: float
    progress: float
    features: dict[str, Any]
    preset_name: str
    palette_base: tuple[int, int, int]
    palette_accent: tuple[int, int, int]
    palette_beat: tuple[int, int, int]


def feature_float(features: dict[str, Any], name: str, default: float = 0.0) -> float:
    """Read a normalized scalar feature safely."""
    value = features.get(name, default)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if not isinstance(value, int | float):
        return default
    return max(0.0, min(1.0, float(value)))


def feature_vector(features: dict[str, Any], name: str) -> list[float]:
    """Read a normalized vector feature safely."""
    value = features.get(name, [])
    if not isinstance(value, list):
        return []
    return [max(0.0, min(1.0, float(item))) for item in value if isinstance(item, int | float)]


def blend_color(
    a: tuple[int, int, int],
    b: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:
    """Blend two RGB colors."""
    amount = max(0.0, min(1.0, amount))
    return tuple(round(left + (right - left) * amount) for left, right in zip(a, b, strict=True))
