from pathlib import Path

import pytest

from wavesmith.render.options import RenderOptionsError, build_render_options, parse_resolution


def test_parse_resolution_accepts_even_dimensions() -> None:
    assert parse_resolution("640x360") == (640, 360)


@pytest.mark.parametrize("value", ["640", "640xnope", "15x16", "641x360"])
def test_parse_resolution_rejects_invalid_values(value: str) -> None:
    with pytest.raises(RenderOptionsError):
        parse_resolution(value)


def test_render_options_error_is_specific() -> None:
    with pytest.raises(RenderOptionsError, match="Input audio file does not exist"):
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


def test_render_options_accepts_lrc_lyrics(tmp_path: Path) -> None:
    audio = tmp_path / "song.mp3"
    audio.write_bytes(b"fake")
    lyrics = tmp_path / "song.lrc"
    lyrics.write_text("[00:01.00]hello", encoding="utf-8")

    options = build_render_options(
        input_audio=audio,
        output_video=tmp_path / "out.mp4",
        preset="neon_orb",
        resolution="640x360",
        fps=15,
        max_seconds=5,
        watermark=None,
        crf=18,
        ffmpeg_preset="medium",
        force_analysis=False,
        lyrics_path=lyrics,
        lyrics_offset=0.25,
    )

    assert options.lyrics_path == lyrics
    assert options.lyrics_offset == 0.25


def test_render_options_rejects_unsupported_lyrics(tmp_path: Path) -> None:
    audio = tmp_path / "song.mp3"
    audio.write_bytes(b"fake")
    lyrics = tmp_path / "song.txt"
    lyrics.write_text("hello", encoding="utf-8")

    with pytest.raises(RenderOptionsError, match=".lrc or .srt"):
        build_render_options(
            input_audio=audio,
            output_video=tmp_path / "out.mp4",
            preset="neon_orb",
            resolution="640x360",
            fps=15,
            max_seconds=5,
            watermark=None,
            crf=18,
            ffmpeg_preset="medium",
            force_analysis=False,
            lyrics_path=lyrics,
        )


def test_render_options_rejects_unsupported_thumbnail_style(tmp_path: Path) -> None:
    audio = tmp_path / "song.mp3"
    audio.write_bytes(b"fake")

    with pytest.raises(RenderOptionsError, match="frame or poster"):
        build_render_options(
            input_audio=audio,
            output_video=tmp_path / "out.mp4",
            preset="neon_orb",
            resolution="640x360",
            fps=15,
            max_seconds=5,
            watermark=None,
            crf=18,
            ffmpeg_preset="medium",
            force_analysis=False,
            thumbnail_style="ai_magic",
        )


def test_render_options_rejects_unsupported_backend(tmp_path: Path) -> None:
    audio = tmp_path / "song.mp3"
    audio.write_bytes(b"fake")

    with pytest.raises(RenderOptionsError, match="cpu or gpu"):
        build_render_options(
            input_audio=audio,
            output_video=tmp_path / "out.mp4",
            preset="neon_orb",
            resolution="640x360",
            fps=15,
            max_seconds=5,
            watermark=None,
            crf=18,
            ffmpeg_preset="medium",
            force_analysis=False,
            backend="metal",
        )
