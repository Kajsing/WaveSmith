"""Lyric timing models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LyricCue:
    """One timed lyric line."""

    start: float
    end: float
    text: str
