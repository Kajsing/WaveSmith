"""Audio feature models."""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class TimeSeries(BaseModel):
    """A normalized feature series sampled over time."""

    model_config = ConfigDict(extra="forbid")

    times: list[float] = Field(default_factory=list)
    values: list[float] | list[list[float]] = Field(default_factory=list)

    def validate_lengths(self) -> None:
        """Ensure the time and value axes match."""
        if len(self.times) != len(self.values):
            raise ValueError("Time series must have the same number of times and values.")


class AudioAnalysis(BaseModel):
    """Serializable audio feature payload used by timelines and caches."""

    model_config = ConfigDict(extra="forbid")

    duration_seconds: float
    sample_rate: int
    tempo_bpm: float
    beats: list[float]
    onsets: list[float]
    rms: TimeSeries
    left_energy: TimeSeries = Field(default_factory=TimeSeries)
    right_energy: TimeSeries = Field(default_factory=TimeSeries)
    left_bass: TimeSeries = Field(default_factory=TimeSeries)
    right_bass: TimeSeries = Field(default_factory=TimeSeries)
    left_treble: TimeSeries = Field(default_factory=TimeSeries)
    right_treble: TimeSeries = Field(default_factory=TimeSeries)
    bass_energy: TimeSeries
    mid_energy: TimeSeries
    treble_energy: TimeSeries
    spectrum: TimeSeries
    waveform_preview: TimeSeries

    def model_post_init(self, __context: object) -> None:
        """Validate nested time series lengths after pydantic construction."""
        for series in (
            self.rms,
            self.left_energy,
            self.right_energy,
            self.left_bass,
            self.right_bass,
            self.left_treble,
            self.right_treble,
            self.bass_energy,
            self.mid_energy,
            self.treble_energy,
            self.spectrum,
            self.waveform_preview,
        ):
            series.validate_lengths()

    def write_json(self, path: Path) -> None:
        """Write analysis JSON with stable formatting."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")


def read_analysis(path: Path) -> AudioAnalysis:
    """Read an analysis JSON file."""
    return AudioAnalysis.model_validate(json.loads(path.read_text(encoding="utf-8")))
