import subprocess
from pathlib import Path

import pytest

from wavesmith.render.ffmpeg import (
    FfmpegMissingError,
    FfmpegRenderError,
    build_rawvideo_command,
    probe_duration_seconds,
    require_binary,
    verify_media_streams,
)


def test_build_rawvideo_command_contains_video_and_audio_inputs(monkeypatch) -> None:
    monkeypatch.setattr("wavesmith.render.ffmpeg.require_binary", lambda name: f"/usr/bin/{name}")

    command = build_rawvideo_command(
        input_audio=Path("song.wav"),
        output_video=Path("out.mp4"),
        width=640,
        height=360,
        fps=15,
        duration_seconds=5,
        crf=18,
        ffmpeg_preset="medium",
    )

    assert command[:2] == ["/usr/bin/ffmpeg", "-y"]
    assert "-s" in command
    assert "640x360" in command
    assert "pipe:0" in command
    assert "song.wav" in command
    assert "out.mp4" in command
    assert "-shortest" in command


def test_require_binary_raises_for_missing_binary(monkeypatch) -> None:
    monkeypatch.setattr("wavesmith.render.ffmpeg.shutil.which", lambda name: None)

    with pytest.raises(FfmpegMissingError, match="ffmpeg"):
        require_binary("ffmpeg")


def test_probe_duration_raises_for_invalid_audio(monkeypatch) -> None:
    monkeypatch.setattr("wavesmith.render.ffmpeg.require_binary", lambda name: f"/usr/bin/{name}")

    def fake_run(command, capture_output, check, text):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="invalid data")

    monkeypatch.setattr("wavesmith.render.ffmpeg.subprocess.run", fake_run)

    with pytest.raises(FfmpegRenderError, match="invalid data"):
        probe_duration_seconds(Path("broken.wav"))


def test_verify_media_streams_detects_audio_and_video(monkeypatch) -> None:
    monkeypatch.setattr("wavesmith.render.ffmpeg.require_binary", lambda name: f"/usr/bin/{name}")

    def fake_run(command, capture_output, check, text):
        return subprocess.CompletedProcess(command, 0, stdout="video\naudio\n", stderr="")

    monkeypatch.setattr("wavesmith.render.ffmpeg.subprocess.run", fake_run)

    assert verify_media_streams(Path("out.mp4")) == (True, True)
