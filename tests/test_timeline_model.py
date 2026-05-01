import pytest

from wavesmith.audio.features import AudioAnalysis, TimeSeries
from wavesmith.timeline.model import Timeline


def test_timeline_interpolates_scalar_and_vector_features() -> None:
    series = TimeSeries(times=[0.0, 1.0], values=[0.0, 1.0])
    vector_series = TimeSeries(times=[0.0, 1.0], values=[[0.0, 1.0], [1.0, 0.0]])
    analysis = AudioAnalysis(
        duration_seconds=1.0,
        sample_rate=22_050,
        tempo_bpm=120.0,
        beats=[0.5],
        onsets=[],
        rms=series,
        bass_energy=series,
        mid_energy=series,
        treble_energy=series,
        spectrum=vector_series,
        waveform_preview=vector_series,
    )

    features = Timeline(analysis).at(0.5)

    assert features["rms"] == 0.5
    assert features["bass_energy"] == 0.5
    assert features["spectrum"] == [0.5, 0.5]
    assert features["beat"] is True
    assert features["tempo_bpm"] == 120.0


def test_timeline_exposes_slow_pulse_features() -> None:
    low = TimeSeries(
        times=[0.0, 0.5, 1.0, 1.5, 2.0],
        values=[0.0, 1.0, 0.25, 0.25, 0.25],
    )
    mid = TimeSeries(
        times=[0.0, 0.5, 1.0, 1.5, 2.0],
        values=[0.0, 0.2, 0.8, 0.8, 0.2],
    )
    vector_series = TimeSeries(times=[0.0, 2.0], values=[[0.0], [1.0]])
    analysis = AudioAnalysis(
        duration_seconds=2.0,
        sample_rate=22_050,
        tempo_bpm=90.0,
        beats=[0.5],
        onsets=[],
        rms=low,
        bass_energy=low,
        mid_energy=mid,
        treble_energy=low,
        spectrum=vector_series,
        waveform_preview=vector_series,
    )

    features = Timeline(analysis).at(1.0)

    assert features["beat_decay"] == 0.642857
    assert features["slow_bass"] == 0.416667
    assert features["slow_mid"] == 0.333333
    assert features["slow_pulse"] == pytest.approx(0.558096, abs=0.000001)


def test_timeline_clamps_out_of_range_time() -> None:
    series = TimeSeries(times=[0.0, 1.0], values=[0.25, 0.75])
    vector_series = TimeSeries(times=[0.0, 1.0], values=[[0.0], [1.0]])
    analysis = AudioAnalysis(
        duration_seconds=1.0,
        sample_rate=22_050,
        tempo_bpm=0.0,
        beats=[],
        onsets=[],
        rms=series,
        bass_energy=series,
        mid_energy=series,
        treble_energy=series,
        spectrum=vector_series,
        waveform_preview=vector_series,
    )

    features = Timeline(analysis).at(9.0)

    assert features["time_seconds"] == 1.0
    assert features["rms"] == 0.75
