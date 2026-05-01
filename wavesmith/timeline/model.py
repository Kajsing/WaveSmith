"""Frame-time feature lookup."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from wavesmith.audio.features import AudioAnalysis, TimeSeries


@dataclass(frozen=True)
class Timeline:
    """Interpolated feature lookup over an audio analysis payload."""

    analysis: AudioAnalysis

    def at(self, time_seconds: float) -> dict[str, Any]:
        """Return feature values at a render timestamp."""
        time_seconds = _clamp(time_seconds, 0.0, self.analysis.duration_seconds)
        return {
            "time_seconds": time_seconds,
            "duration_seconds": self.analysis.duration_seconds,
            "sample_rate": self.analysis.sample_rate,
            "tempo_bpm": self.analysis.tempo_bpm,
            "beat": _is_near_event(time_seconds, self.analysis.beats),
            "onset": _is_near_event(time_seconds, self.analysis.onsets),
            "rms": _interpolate_series(self.analysis.rms, time_seconds),
            "bass_energy": _interpolate_series(self.analysis.bass_energy, time_seconds),
            "mid_energy": _interpolate_series(self.analysis.mid_energy, time_seconds),
            "treble_energy": _interpolate_series(self.analysis.treble_energy, time_seconds),
            "spectrum": _interpolate_series(self.analysis.spectrum, time_seconds),
            "waveform_preview": _interpolate_series(
                self.analysis.waveform_preview,
                time_seconds,
            ),
        }


def _interpolate_series(series: TimeSeries, time_seconds: float) -> float | list[float]:
    if not series.times or not series.values:
        return 0.0

    first_value = series.values[0]
    if isinstance(first_value, list):
        matrix = np.asarray(series.values, dtype=float)
        times = np.asarray(series.times, dtype=float)
        if time_seconds <= times[0]:
            return _rounded_vector(matrix[0])
        if time_seconds >= times[-1]:
            return _rounded_vector(matrix[-1])
        interpolated = [
            np.interp(time_seconds, times, matrix[:, index]) for index in range(matrix.shape[1])
        ]
        return _rounded_vector(np.array(interpolated))

    values = np.asarray(series.values, dtype=float)
    interpolated = np.interp(time_seconds, np.asarray(series.times, dtype=float), values)
    return round(float(interpolated), 6)


def _is_near_event(time_seconds: float, events: list[float], window_seconds: float = 0.05) -> bool:
    return any(abs(time_seconds - event) <= window_seconds for event in events)


def _rounded_vector(values: np.ndarray) -> list[float]:
    return [round(float(value), 6) for value in values]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)
