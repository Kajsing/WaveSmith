"""Text and watermark visual helpers."""

from PIL import ImageFont

from wavesmith.visuals.base import FrameContext


def draw_watermark(ctx: FrameContext, text: str | None) -> None:
    """Draw a small watermark unless explicitly disabled."""
    if text == "":
        return

    watermark = text or "WaveSmith"
    font = ImageFont.load_default()
    margin = max(10, min(ctx.width, ctx.height) // 55)
    ctx.draw.text(
        (ctx.width - margin, ctx.height - margin),
        watermark,
        fill=ctx.palette_beat,
        font=font,
        anchor="rd",
    )
