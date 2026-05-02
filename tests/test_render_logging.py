from pathlib import Path

from wavesmith.utils.logging import render_log_path, write_render_log


def test_render_log_path_uses_audio_stem(tmp_path) -> None:
    path = render_log_path(Path("song.wav"), log_dir=tmp_path)

    assert path.parent == tmp_path
    assert path.name.endswith("-song.log")


def test_render_log_paths_do_not_collide(tmp_path) -> None:
    first = render_log_path(Path("song.wav"), log_dir=tmp_path)
    second = render_log_path(Path("song.wav"), log_dir=tmp_path)

    assert first != second


def test_write_render_log_includes_cache_and_command(tmp_path) -> None:
    log_path = tmp_path / "render.log"

    write_render_log(
        path=log_path,
        status="success",
        input_audio=Path("song.wav"),
        output_video=Path("out.mp4"),
        preset="neon_orb",
        duration_seconds=5.0,
        resolution="640x360",
        fps=15,
        backend="gpu",
        crf=12,
        ffmpeg_preset="slow",
        frame_count=75,
        total_elapsed_seconds=4.5,
        encode_elapsed_seconds=3.0,
        effective_fps=25.0,
        output_size_bytes=12345,
        cache_status="hit",
        cache_path=Path(".cache/analysis/example.json"),
        ffmpeg_command=["ffmpeg", "-i", "pipe:0", "out.mp4"],
        thumbnail_time_seconds=2.5,
    )

    text = log_path.read_text(encoding="utf-8")

    assert "status=success" in text
    assert "backend=gpu" in text
    assert "crf=12" in text
    assert "ffmpeg_preset=slow" in text
    assert "frame_count=75" in text
    assert "encode_elapsed_seconds=3.0" in text
    assert "effective_fps=25.0" in text
    assert "output_size_bytes=12345" in text
    assert "analysis_cache_status=hit" in text
    assert "thumbnail_time_seconds=2.5" in text
    assert "ffmpeg_command=ffmpeg -i pipe:0 out.mp4" in text
