from pathlib import Path

from wavesmith.render.ffmpeg import verify_media_streams


def test_verify_media_streams_on_existing_smoke_output() -> None:
    output = Path(".tmp/test.mp4")
    if not output.exists():
        return

    has_video, has_audio = verify_media_streams(output)

    assert output.stat().st_size > 0
    assert has_video
    assert has_audio
