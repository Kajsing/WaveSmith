import json

import pytest

from tests.audio_fixtures import write_test_tone
from wavesmith.audio.analyzer import DEFAULT_FEATURE_FPS, AudioAnalysisError, analyze_audio
from wavesmith.audio.features import read_analysis


def test_analyze_audio_returns_required_normalized_features(tmp_path) -> None:
    audio = tmp_path / "tone.wav"
    write_test_tone(audio)

    analysis = analyze_audio(audio)

    assert analysis.duration_seconds == pytest.approx(1.0, rel=0.05)
    assert analysis.sample_rate == 22_050
    assert analysis.tempo_bpm >= 0
    assert len(analysis.rms.times) == len(analysis.rms.values)
    assert len(analysis.spectrum.values[0]) == 32
    assert len(analysis.waveform_preview.values[0]) == 32
    assert all(0.0 <= value <= 1.0 for value in analysis.rms.values)
    assert all(0.0 <= value <= 1.0 for row in analysis.spectrum.values for value in row)


def test_analysis_json_roundtrip(tmp_path) -> None:
    audio = tmp_path / "tone.wav"
    output = tmp_path / "tone.analysis.json"
    write_test_tone(audio)

    analysis = analyze_audio(audio)
    analysis.write_json(output)
    loaded = read_analysis(output)

    assert json.loads(output.read_text(encoding="utf-8"))["duration_seconds"]
    assert loaded.duration_seconds == analysis.duration_seconds
    assert loaded.rms.times == analysis.rms.times


def test_analyze_audio_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(AudioAnalysisError, match="does not exist"):
        analyze_audio(tmp_path / "missing.wav")


def test_analyze_audio_limits_serialized_feature_rate(tmp_path) -> None:
    audio = tmp_path / "tone.wav"
    write_test_tone(audio, seconds=2.0)

    analysis = analyze_audio(audio, feature_fps=5)

    assert len(analysis.rms.values) <= int(analysis.duration_seconds * 5) + 1
    assert len(analysis.spectrum.values) == len(analysis.rms.values)
    assert len(analysis.waveform_preview.values) == len(analysis.rms.values)


def test_analyze_audio_uses_default_feature_rate_limit(tmp_path) -> None:
    audio = tmp_path / "tone.wav"
    write_test_tone(audio, seconds=2.0)

    analysis = analyze_audio(audio)

    assert len(analysis.rms.values) <= int(analysis.duration_seconds * DEFAULT_FEATURE_FPS) + 1


def test_analyze_audio_rejects_invalid_feature_rate(tmp_path) -> None:
    audio = tmp_path / "tone.wav"
    write_test_tone(audio)

    with pytest.raises(AudioAnalysisError, match="feature_fps"):
        analyze_audio(audio, feature_fps=0)
