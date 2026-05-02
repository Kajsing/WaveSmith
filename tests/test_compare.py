from pathlib import Path

import pytest

from tests.audio_fixtures import write_test_tone
from wavesmith.render.compare import run_compare
from wavesmith.render.pipeline import RenderResult


def test_run_compare_writes_summary_for_multiple_presets(monkeypatch, tmp_path) -> None:
    audio = tmp_path / "song.wav"
    output_dir = tmp_path / "compare"
    write_test_tone(audio)

    def fake_render(options):
        options.output_video.parent.mkdir(parents=True, exist_ok=True)
        options.output_video.write_bytes(b"video")
        if options.thumbnail_path:
            options.thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            options.thumbnail_path.write_bytes(b"jpg")
        return RenderResult(
            duration_seconds=2.0,
            cache_status="hit",
            cache_path=Path(".cache/example.json"),
            log_path=Path(".renders/logs/example.log"),
            thumbnail_path=options.thumbnail_path,
            backend=options.backend,
            encode_elapsed_seconds=1.0,
            effective_fps=30.0,
            output_size_bytes=5,
        )

    monkeypatch.setattr("wavesmith.render.compare.render_video", fake_render)

    summary = run_compare(
        input_audio=audio,
        output_dir=output_dir,
        presets=["neon_orb", "waveform_ribbon"],
        width=320,
        height=180,
        fps=15,
        seconds=2,
        watermark="",
        crf=18,
        ffmpeg_preset="medium",
        backend="cpu",
        force_analysis=False,
        thumbnails=True,
        thumbnail_at="best",
        thumbnail_style="frame",
        stop_on_error=False,
    )

    assert summary.total == 2
    assert summary.succeeded == 2
    assert summary.failed == 0
    assert (output_dir / "song-neon_orb.mp4").exists()
    assert (output_dir / "song-waveform_ribbon.mp4").exists()
    assert (output_dir / "thumbnails/song-neon_orb.jpg").exists()
    assert (output_dir / "compare-summary.json").exists()
    assert summary.results[0].backend == "cpu"
    assert summary.results[0].effective_fps == 30.0


def test_run_compare_rejects_empty_presets(tmp_path) -> None:
    audio = tmp_path / "song.wav"
    write_test_tone(audio)

    with pytest.raises(ValueError, match="At least one preset"):
        run_compare(
            input_audio=audio,
            output_dir=tmp_path / "compare",
            presets=[],
            width=320,
            height=180,
            fps=15,
            seconds=2,
            watermark="",
            crf=18,
            ffmpeg_preset="medium",
            backend="cpu",
            force_analysis=False,
            thumbnails=True,
            thumbnail_at="best",
            thumbnail_style="frame",
            stop_on_error=False,
        )
