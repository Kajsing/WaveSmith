from pathlib import Path

from wavesmith.render.ffmpeg import build_rawvideo_command


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
