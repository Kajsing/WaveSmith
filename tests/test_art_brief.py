from wavesmith.art import build_art_brief
from wavesmith.lyrics import LyricCue


def test_build_art_brief_extracts_local_direction() -> None:
    cues = [
        LyricCue(0.0, 1.0, "dark pressure under skin"),
        LyricCue(1.0, 2.0, "pulse signals rise in low light"),
    ]

    brief = build_art_brief(cues)

    assert "intimate" in brief.mood
    assert "body pressure" in brief.imagery
    assert brief.suggested_preset == "shader_bloom"
    assert brief.source_line_count == 2
