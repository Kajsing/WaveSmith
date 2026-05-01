"""Text and watermark visual helpers."""

from PIL import Image, ImageDraw, ImageFont

from wavesmith.visuals.base import FrameContext


def draw_watermark(ctx: FrameContext, text: str | None) -> None:
    """Draw a small watermark unless explicitly disabled."""
    if text == "":
        return

    watermark = text or "WaveSmith"
    font = _load_font(max(16, min(ctx.width, ctx.height) // 20))
    margin = max(10, min(ctx.width, ctx.height) // 55)
    ctx.draw.text(
        (ctx.width - margin, ctx.height - margin),
        watermark,
        fill=ctx.palette_beat,
        font=font,
        anchor="rd",
    )


def draw_lyrics(ctx: FrameContext, text: str | None) -> None:
    """Draw active lyric text near the bottom center."""
    if not text:
        return

    font = ImageFont.load_default()
    margin = max(16, min(ctx.width, ctx.height) // 18)
    max_width = int(ctx.width * 0.86)
    lines = _wrap_text(text, font, max_width)
    if not lines:
        return

    line_height = _text_height(font) + max(3, ctx.height // 180)
    total_height = line_height * len(lines)
    preferred_y = int(ctx.height * 0.68)
    lowest_y = int(ctx.height - margin * 3.7 - total_height)
    y = min(preferred_y, lowest_y)
    overlay = Image.new("RGBA", (ctx.width, ctx.height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    max_line_width = max(_text_width(line, font) for line in lines)
    box_padding_x = max(12, ctx.width // 55)
    box_padding_y = max(6, ctx.height // 90)
    box_left = max(ctx.width * 0.06, (ctx.width - max_line_width) / 2 - box_padding_x)
    box_right = min(ctx.width * 0.94, (ctx.width + max_line_width) / 2 + box_padding_x)
    box_top = y - box_padding_y
    box_bottom = y + total_height + box_padding_y
    overlay_draw.rounded_rectangle(
        (
            box_left,
            box_top,
            box_right,
            box_bottom,
        ),
        radius=max(4, ctx.height // 90),
        fill=(0, 0, 0, 132),
    )

    for index, line in enumerate(lines):
        line_width = _text_width(line, font)
        x = (ctx.width - line_width) / 2
        overlay_draw.text(
            (x, y + index * line_height),
            line,
            font=font,
            fill=(*ctx.palette_beat, 232),
        )

    composited = Image.alpha_composite(ctx.image.convert("RGBA"), overlay)
    ctx.image.paste(composited.convert("RGB"))


def _wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and _text_width(candidate, font) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _text_width(text: str, font: ImageFont.ImageFont) -> int:
    left, _, right, _ = font.getbbox(text)
    return right - left


def _text_height(font: ImageFont.ImageFont) -> int:
    _, top, _, bottom = font.getbbox("Ag")
    return bottom - top


def _load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default()
