from pathlib import Path

import pytest

from wavesmith.lyrics import LyricsError, active_lyric_text, load_lyrics
from wavesmith.lyrics.parser import parse_lrc, parse_srt


def test_parse_lrc_sorts_and_infers_end_times() -> None:
    cues = parse_lrc("[00:02.00]second\n[00:01.00]first\n")

    assert [cue.text for cue in cues] == ["first", "second"]
    assert cues[0].start == 1.0
    assert cues[0].end == 2.0
    assert cues[1].end == 6.0


def test_parse_lrc_accepts_multiple_timestamps_per_line() -> None:
    cues = parse_lrc("[00:01.00][00:03.00]echo\n")

    assert [(cue.start, cue.text) for cue in cues] == [(1.0, "echo"), (3.0, "echo")]


def test_parse_srt_reads_numbered_blocks() -> None:
    cues = parse_srt(
        """
1
00:00:01,500 --> 00:00:03,000
hello there

2
00:00:03,250 --> 00:00:05,000
second line
"""
    )

    assert [cue.text for cue in cues] == ["hello there", "second line"]
    assert cues[0].start == 1.5
    assert cues[0].end == 3.0


def test_active_lyric_text_applies_offset() -> None:
    cues = parse_lrc("[00:01.00]late\n")

    assert active_lyric_text(cues, 1.25, offset=0.0) == "late"
    assert active_lyric_text(cues, 1.25, offset=1.0) is None
    assert active_lyric_text(cues, 2.25, offset=1.0) == "late"


def test_load_lyrics_rejects_unsupported_suffix(tmp_path: Path) -> None:
    lyric_file = tmp_path / "lyrics.txt"
    lyric_file.write_text("[00:01.00]hello", encoding="utf-8")

    with pytest.raises(LyricsError, match=".lrc or .srt"):
        load_lyrics(lyric_file)
