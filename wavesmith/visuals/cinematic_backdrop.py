"""Dark cinematic backdrop module."""

from PIL import Image, ImageDraw, ImageFilter

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext, blend_color, feature_float


def draw_cinematic_backdrop(ctx: FrameContext, module: PresetModule | None = None) -> None:
    """Replace the default grid with a dark vignette and soft volumetric haze."""
    module_config = module.model_extra or {} if module else {}
    darkness = max(0.0, min(float(module_config.get("darkness", 0.88)), 1.0))
    haze = max(0.0, min(float(module_config.get("haze", 0.4)), 1.0))
    rms = feature_float(ctx.features, "rms")
    treble = feature_float(ctx.features, "treble_energy")
    top = blend_color((1, 1, 3), ctx.palette_base, 0.06 + rms * 0.07)
    bottom = blend_color((10, 2, 1), ctx.palette_accent, 0.08 + treble * 0.08)

    draw = ImageDraw.Draw(ctx.image)
    for y in range(ctx.height):
        amount = y / max(1, ctx.height - 1)
        color = blend_color(top, bottom, amount)
        color = blend_color(color, (0, 0, 0), darkness * (0.45 + abs(amount - 0.5)))
        draw.line((0, y, ctx.width, y), fill=color)

    overlay = Image.new("RGBA", (ctx.width, ctx.height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for index in range(18):
        x = (index * 97 + ctx.time_seconds * 11) % (ctx.width * 1.2) - ctx.width * 0.1
        y = ctx.height * (0.18 + (index % 7) * 0.095)
        radius = ctx.width * (0.08 + (index % 5) * 0.018)
        alpha = int(255 * haze * (0.025 + rms * 0.02))
        color = blend_color(ctx.palette_accent, ctx.palette_beat, (index % 4) / 4)
        overlay_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))

    vignette = Image.new("RGBA", (ctx.width, ctx.height), (0, 0, 0, 0))
    vignette_draw = ImageDraw.Draw(vignette)
    for index in range(10):
        inset_x = ctx.width * index / 24
        inset_y = ctx.height * index / 24
        alpha = int(24 * (1 - index / 10))
        vignette_draw.rectangle(
            (inset_x, inset_y, ctx.width - inset_x, ctx.height - inset_y),
            outline=(0, 0, 0, alpha),
            width=max(1, ctx.width // 120),
        )

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(6, ctx.height // 28)))
    composited = Image.alpha_composite(ctx.image.convert("RGBA"), overlay)
    composited = Image.alpha_composite(composited, vignette)
    ctx.image.paste(composited.convert("RGB"))
