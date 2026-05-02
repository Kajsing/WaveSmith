from PIL import Image

from wavesmith.audio.features import AudioAnalysis, TimeSeries
from wavesmith.presets.loader import load_preset
from wavesmith.render.thumbnail import (
    choose_reactive_thumbnail_time,
    resolve_thumbnail_time,
    write_poster_thumbnail,
)


def test_write_poster_thumbnail_creates_jpg(tmp_path) -> None:
    output = tmp_path / "poster.jpg"
    features = {
        "rms": 0.6,
        "bass_energy": 0.7,
        "treble_energy": 0.4,
        "spectrum": [0.1, 0.8, 0.4, 0.9],
    }

    write_poster_thumbnail(
        output_image=output,
        preset=load_preset("shader_bloom"),
        features=features,
        title="test song",
        width=320,
        height=180,
    )

    assert output.exists()
    with Image.open(output) as image:
        assert image.size == (320, 180)
        assert image.mode == "RGB"


def test_choose_reactive_thumbnail_time_prefers_strong_music_moment() -> None:
    analysis = _analysis_for_thumbnail(
        times=[0.0, 1.0, 2.0, 3.0, 4.0],
        rms=[0.1, 0.2, 0.95, 0.4, 0.2],
        bass=[0.1, 0.2, 0.9, 0.5, 0.2],
        mid=[0.1, 0.3, 0.7, 0.4, 0.2],
        treble=[0.1, 0.2, 0.8, 0.4, 0.2],
        beats=[2.0],
    )

    assert choose_reactive_thumbnail_time(analysis, 4.0) == 2.0


def test_resolve_thumbnail_time_accepts_best_and_explicit_values() -> None:
    analysis = _analysis_for_thumbnail(
        times=[0.0, 5.0, 10.0],
        rms=[0.1, 0.9, 0.2],
        bass=[0.1, 0.8, 0.2],
        mid=[0.1, 0.7, 0.2],
        treble=[0.1, 0.6, 0.2],
        beats=[],
    )

    assert resolve_thumbnail_time("best", 10.0, analysis) == 5.0
    assert resolve_thumbnail_time("middle", 10.0, analysis) == 5.0


def _analysis_for_thumbnail(
    *,
    times: list[float],
    rms: list[float],
    bass: list[float],
    mid: list[float],
    treble: list[float],
    beats: list[float],
) -> AudioAnalysis:
    spectrum = TimeSeries(times=times, values=[[0.1, 0.2, 0.3, 0.4] for _ in times])
    waveform = TimeSeries(times=times, values=[[0.5, 0.5, 0.5, 0.5] for _ in times])
    return AudioAnalysis(
        duration_seconds=times[-1],
        sample_rate=22_050,
        tempo_bpm=120.0,
        beats=beats,
        onsets=[],
        rms=TimeSeries(times=times, values=rms),
        bass_energy=TimeSeries(times=times, values=bass),
        mid_energy=TimeSeries(times=times, values=mid),
        treble_energy=TimeSeries(times=times, values=treble),
        spectrum=spectrum,
        waveform_preview=waveform,
    )
