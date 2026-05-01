from pathlib import Path

from wavesmith.render.options import RenderOptions
from wavesmith.render.pipeline import generate_placeholder_frames


def test_generate_placeholder_frames_have_expected_byte_size() -> None:
    options = RenderOptions(
        input_audio=Path("song.wav"),
        output_video=Path("out.mp4"),
        preset="neon_orb",
        width=64,
        height=48,
        fps=2,
        max_seconds=1,
        watermark="",
        crf=18,
        ffmpeg_preset="medium",
    )

    frames = list(generate_placeholder_frames(options, duration_seconds=1.0))

    assert len(frames) == 2
    assert len(frames[0]) == 64 * 48 * 3
