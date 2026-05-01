"""Image-backed cinematic backdrop module."""

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext, feature_float


def draw_image_backdrop(ctx: FrameContext, module: PresetModule | None = None) -> None:
    """Draw a cover-cropped image backdrop with audio-reactive grading."""
    module_config = module.model_extra or {} if module else {}
    path_text = module_config.get("path")
    if not isinstance(path_text, str) or not path_text:
        return

    source = _load_image(path_text)
    frame = _cover(source, ctx.width, ctx.height)
    rms = feature_float(ctx.features, "rms")
    bass = feature_float(ctx.features, "bass_energy")
    dim = max(0.0, min(float(module_config.get("dim", 0.18)), 0.95))
    blur = max(0.0, min(float(module_config.get("blur", 0.0)), 20.0))
    contrast = max(0.1, float(module_config.get("contrast", 1.08)))
    saturation = max(0.0, float(module_config.get("saturation", 1.08)))
    pulse = max(0.0, min(float(module_config.get("pulse", 0.08)), 0.5))

    frame = ImageEnhance.Contrast(frame).enhance(contrast + rms * pulse)
    frame = ImageEnhance.Color(frame).enhance(saturation + bass * pulse)
    if blur:
        frame = frame.filter(ImageFilter.GaussianBlur(radius=blur))
    if dim:
        black = Image.new("RGB", frame.size, (0, 0, 0))
        frame = Image.blend(frame, black, dim)

    ctx.image.paste(frame)


@lru_cache(maxsize=16)
def _load_image(path_text: str) -> Image.Image:
    path = Path(path_text).expanduser()
    return Image.open(path).convert("RGB")


def _cover(image: Image.Image, width: int, height: int) -> Image.Image:
    source_ratio = image.width / image.height
    target_ratio = width / height
    if source_ratio > target_ratio:
        new_height = height
        new_width = round(height * source_ratio)
    else:
        new_width = width
        new_height = round(width / source_ratio)
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = max(0, (new_width - width) // 2)
    top = max(0, (new_height - height) // 2)
    return resized.crop((left, top, left + width, top + height))
