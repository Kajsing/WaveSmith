from pathlib import Path

import pytest

from tests.audio_fixtures import write_test_tone
from wavesmith.render.batch import discover_audio_files, run_batch
from wavesmith.render.pipeline import RenderResult


def test_discover_audio_files_is_sorted_and_filters_extensions(tmp_path) -> None:
    write_test_tone(tmp_path / "b.wav")
    write_test_tone(tmp_path / "a.wav")
    (tmp_path / "notes.txt").write_text("skip me", encoding="utf-8")

    assert [path.name for path in discover_audio_files(tmp_path)] == ["a.wav", "b.wav"]


def test_run_batch_writes_summary_and_thumbnails(monkeypatch, tmp_path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    write_test_tone(input_dir / "a.wav")
    write_test_tone(input_dir / "b.wav")

    def fake_render(options):
        options.output_video.parent.mkdir(parents=True, exist_ok=True)
        options.output_video.write_bytes(b"video")
        if options.thumbnail_path:
            options.thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            options.thumbnail_path.write_bytes(b"jpg")
        return RenderResult(
            duration_seconds=1.0,
            cache_status="hit",
            cache_path=Path(".cache/example.json"),
            log_path=Path(".renders/logs/example.log"),
            thumbnail_path=options.thumbnail_path,
        )

    monkeypatch.setattr("wavesmith.render.batch.render_video", fake_render)

    summary = run_batch(
        input_dir=input_dir,
        output_dir=output_dir,
        preset="neon_orb",
        width=640,
        height=360,
        fps=15,
        max_seconds=1,
        watermark="",
        crf=18,
        ffmpeg_preset="medium",
        force_analysis=False,
        thumbnails=True,
        thumbnail_at="50%",
        thumbnail_style="frame",
        stop_on_error=False,
    )

    assert summary.total == 2
    assert summary.succeeded == 2
    assert summary.failed == 0
    assert (output_dir / "batch-summary.json").exists()
    assert (output_dir / "thumbnails/a.jpg").exists()


def test_run_batch_can_stop_on_error(monkeypatch, tmp_path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    write_test_tone(input_dir / "a.wav")
    write_test_tone(input_dir / "b.wav")

    def fake_render(options):
        raise RuntimeError("boom")

    monkeypatch.setattr("wavesmith.render.batch.render_video", fake_render)

    summary = run_batch(
        input_dir=input_dir,
        output_dir=output_dir,
        preset="neon_orb",
        width=640,
        height=360,
        fps=15,
        max_seconds=1,
        watermark="",
        crf=18,
        ffmpeg_preset="medium",
        force_analysis=False,
        thumbnails=False,
        thumbnail_at="50%",
        thumbnail_style="frame",
        stop_on_error=True,
    )

    assert summary.total == 1
    assert summary.failed == 1


def test_run_batch_rejects_missing_input_dir(tmp_path) -> None:
    with pytest.raises(ValueError, match="Input directory"):
        run_batch(
            input_dir=tmp_path / "missing",
            output_dir=tmp_path / "out",
            preset="neon_orb",
            width=640,
            height=360,
            fps=15,
            max_seconds=1,
            watermark="",
            crf=18,
            ffmpeg_preset="medium",
            force_analysis=False,
            thumbnails=False,
            thumbnail_at="50%",
            thumbnail_style="frame",
            stop_on_error=True,
        )
