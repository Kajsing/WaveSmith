from pathlib import Path

from wavesmith.audio.features import AudioAnalysis, TimeSeries
from wavesmith.presets.loader import load_preset
from wavesmith.render.options import RenderOptions
from wavesmith.render.pipeline import generate_placeholder_frames, generate_reactive_frames
from wavesmith.timeline.model import Timeline


def test_generate_placeholder_frames_have_expected_byte_size() -> None:
    options = RenderOptions(
        input_audio=Path("song.wav"),
        output_video=Path("out.mp4"),
        preset="neon_orb",
        width=64,
        height=48,
        fps=2,
        max_seconds=1,
        watermark="",
        crf=18,
        ffmpeg_preset="medium",
    )

    frames = list(generate_placeholder_frames(options, duration_seconds=1.0))

    assert len(frames) == 2
    assert len(frames[0]) == 64 * 48 * 3


def test_generate_reactive_frames_change_with_timeline_features() -> None:
    options = RenderOptions(
        input_audio=Path("song.wav"),
        output_video=Path("out.mp4"),
        preset="neon_orb",
        width=96,
        height=72,
        fps=2,
        max_seconds=1,
        watermark="",
        crf=18,
        ffmpeg_preset="medium",
    )
    scalar = TimeSeries(times=[0.0, 1.0], values=[0.0, 1.0])
    spectrum = TimeSeries(
        times=[0.0, 1.0],
        values=[[0.0, 0.0, 0.2, 0.2], [1.0, 0.8, 0.4, 0.1]],
    )
    waveform = TimeSeries(
        times=[0.0, 1.0],
        values=[[0.5, 0.5, 0.5, 0.5], [0.1, 0.9, 0.1, 0.9]],
    )
    analysis = AudioAnalysis(
        duration_seconds=1.0,
        sample_rate=22_050,
        tempo_bpm=120.0,
        beats=[0.0],
        onsets=[],
        rms=scalar,
        bass_energy=scalar,
        mid_energy=scalar,
        treble_energy=scalar,
        spectrum=spectrum,
        waveform_preview=waveform,
    )

    frames = list(
        generate_reactive_frames(options, 1.0, Timeline(analysis), load_preset("neon_orb"))
    )

    assert len(frames) == 2
    assert frames[0] != frames[1]


def test_generate_reactive_frames_follow_preset_module_list() -> None:
    options = RenderOptions(
        input_audio=Path("song.wav"),
        output_video=Path("out.mp4"),
        preset="waveform_ribbon",
        width=96,
        height=72,
        fps=2,
        max_seconds=1,
        watermark="",
        crf=18,
        ffmpeg_preset="medium",
    )
    scalar = TimeSeries(times=[0.0, 1.0], values=[0.5, 0.5])
    vector = TimeSeries(times=[0.0, 1.0], values=[[0.2, 0.8, 0.2, 0.8], [0.8, 0.2, 0.8, 0.2]])
    analysis = AudioAnalysis(
        duration_seconds=1.0,
        sample_rate=22_050,
        tempo_bpm=120.0,
        beats=[],
        onsets=[],
        rms=scalar,
        bass_energy=scalar,
        mid_energy=scalar,
        treble_energy=scalar,
        spectrum=vector,
        waveform_preview=vector,
    )

    frames = list(
        generate_reactive_frames(options, 1.0, Timeline(analysis), load_preset("waveform_ribbon"))
    )

    assert len(frames) == 2
    assert len(frames[0]) == 96 * 72 * 3
