from pathlib import Path

import pytest

from wavesmith.render.options import RenderOptionsError, parse_resolution


def test_parse_resolution_accepts_even_dimensions() -> None:
    assert parse_resolution("640x360") == (640, 360)


@pytest.mark.parametrize("value", ["640", "640xnope", "15x16", "641x360"])
def test_parse_resolution_rejects_invalid_values(value: str) -> None:
    with pytest.raises(RenderOptionsError):
        parse_resolution(value)


def test_render_options_error_is_specific() -> None:
    with pytest.raises(RenderOptionsError, match="Input audio file does not exist"):
        from wavesmith.render.options import build_render_options

        build_render_options(
            input_audio=Path("missing.wav"),
            output_video=Path("out.mp4"),
            preset="neon_orb",
            resolution="640x360",
            fps=15,
            max_seconds=5,
            watermark=None,
            crf=18,
            ffmpeg_preset="medium",
            force_analysis=False,
        )
