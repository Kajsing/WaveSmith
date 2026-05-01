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
            "beat_decay": _event_decay(time_seconds, self.analysis.beats, release_seconds=1.4),
            "rms": _interpolate_series(self.analysis.rms, time_seconds),
            "bass_energy": _interpolate_series(self.analysis.bass_energy, time_seconds),
            "mid_energy": _interpolate_series(self.analysis.mid_energy, time_seconds),
            "treble_energy": _interpolate_series(self.analysis.treble_energy, time_seconds),
            "slow_bass": _windowed_average(self.analysis.bass_energy, time_seconds, 1.35),
            "slow_mid": _windowed_average(self.analysis.mid_energy, time_seconds, 1.75),
            "slow_pulse": _slow_pulse(self.analysis, time_seconds),
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


def _event_decay(time_seconds: float, events: list[float], release_seconds: float) -> float:
    past_events = [event for event in events if event <= time_seconds]
    if not past_events:
        return 0.0
    elapsed = time_seconds - past_events[-1]
    return round(_clamp(1.0 - elapsed / release_seconds, 0.0, 1.0), 6)


def _windowed_average(series: TimeSeries, time_seconds: float, window_seconds: float) -> float:
    if not series.times or not series.values or isinstance(series.values[0], list):
        return 0.0
    times = np.asarray(series.times, dtype=float)
    values = np.asarray(series.values, dtype=float)
    start = max(times[0], time_seconds - window_seconds)
    left = int(np.searchsorted(times, start, side="left"))
    right = int(np.searchsorted(times, time_seconds, side="right"))
    if right <= left:
        return float(_interpolate_series(series, time_seconds))
    return round(float(np.mean(values[left:right])), 6)


def _slow_pulse(analysis: AudioAnalysis, time_seconds: float) -> float:
    slow_bass = _windowed_average(analysis.bass_energy, time_seconds, 1.35)
    slow_mid = _windowed_average(analysis.mid_energy, time_seconds, 1.75)
    beat_decay = _event_decay(time_seconds, analysis.beats, release_seconds=1.4)
    pulse = max(slow_bass, slow_mid * 0.82) + beat_decay * 0.22
    return round(_clamp(pulse, 0.0, 1.0), 6)


def _rounded_vector(values: np.ndarray) -> list[float]:
    return [round(float(value), 6) for value in values]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)
