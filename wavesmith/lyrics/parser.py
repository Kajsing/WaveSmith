"""LRC and SRT lyric parsing."""

import re
from pathlib import Path

from wavesmith.lyrics.model import LyricCue

LRC_TIMESTAMP_RE = re.compile(r"\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?]")
SRT_TIMING_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{1,3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{1,3})"
)


class LyricsError(ValueError):
    """Raised when a lyric file cannot be parsed."""


def load_lyrics(path: Path) -> list[LyricCue]:
    """Load timed lyrics from an LRC or SRT file."""
    suffix = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise LyricsError(f"Could not read lyric file: {path}") from exc

    if suffix == ".lrc":
        cues = parse_lrc(text)
    elif suffix == ".srt":
        cues = parse_srt(text)
    else:
        raise LyricsError("Lyric files must be .lrc or .srt.")

    if not cues:
        raise LyricsError(f"No timed lyrics found in: {path}")
    return cues


def parse_lrc(text: str) -> list[LyricCue]:
    """Parse an LRC lyric string."""
    starts_and_text: list[tuple[float, str]] = []
    for line in text.splitlines():
        matches = list(LRC_TIMESTAMP_RE.finditer(line))
        if not matches:
            continue
        lyric_text = LRC_TIMESTAMP_RE.sub("", line).strip()
        if not lyric_text:
            continue
        for match in matches:
            starts_and_text.append((_parse_lrc_match(match), lyric_text))

    starts_and_text.sort(key=lambda item: item[0])
    cues: list[LyricCue] = []
    for index, (start, lyric_text) in enumerate(starts_and_text):
        if index + 1 < len(starts_and_text):
            next_start = starts_and_text[index + 1][0]
        else:
            next_start = start + 4.0
        end = max(start + 0.2, next_start)
        cues.append(LyricCue(start=start, end=end, text=lyric_text))
    return cues


def parse_srt(text: str) -> list[LyricCue]:
    """Parse an SRT subtitle string."""
    cues: list[LyricCue] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    for block in re.split(r"\n\s*\n", normalized.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        timing_index = 1 if lines[0].isdigit() and len(lines) > 1 else 0
        match = SRT_TIMING_RE.match(lines[timing_index])
        if not match:
            continue
        lyric_text = " ".join(lines[timing_index + 1 :]).strip()
        if not lyric_text:
            continue
        start = _parse_srt_time(match, 1)
        end = _parse_srt_time(match, 5)
        cues.append(LyricCue(start=start, end=max(start + 0.2, end), text=lyric_text))
    return sorted(cues, key=lambda cue: cue.start)


def active_lyric_text(cues: list[LyricCue], time_seconds: float, offset: float = 0.0) -> str | None:
    """Return the lyric active at a render timestamp."""
    for cue in cues:
        if cue.start + offset <= time_seconds < cue.end + offset:
            return cue.text
    return None


def _parse_lrc_match(match: re.Match[str]) -> float:
    minutes = int(match.group(1))
    seconds = int(match.group(2))
    fraction_text = match.group(3) or "0"
    fraction = int(fraction_text) / 10 ** len(fraction_text)
    return minutes * 60 + seconds + fraction


def _parse_srt_time(match: re.Match[str], start_index: int) -> float:
    hours = int(match.group(start_index))
    minutes = int(match.group(start_index + 1))
    seconds = int(match.group(start_index + 2))
    milliseconds = int(match.group(start_index + 3).ljust(3, "0")[:3])
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
