
from tests.audio_fixtures import write_test_tone
from wavesmith.audio.cache import analysis_cache_path, audio_cache_key, load_or_analyze_audio


def test_audio_cache_key_changes_with_feature_rate(tmp_path) -> None:
    audio = tmp_path / "tone.wav"
    write_test_tone(audio)

    first = audio_cache_key(audio, feature_fps=10)
    second = audio_cache_key(audio, feature_fps=20)

    assert first != second


def test_load_or_analyze_audio_reuses_cache(tmp_path) -> None:
    audio = tmp_path / "tone.wav"
    cache_dir = tmp_path / "cache"
    write_test_tone(audio)

    first = load_or_analyze_audio(audio, cache_dir=cache_dir, feature_fps=5)
    second = load_or_analyze_audio(audio, cache_dir=cache_dir, feature_fps=5)

    assert first.cache_status == "miss"
    assert second.cache_status == "hit"
    assert first.cache_path == second.cache_path
    assert second.cache_path.exists()


def test_load_or_analyze_audio_force_rebuilds_existing_cache(tmp_path) -> None:
    audio = tmp_path / "tone.wav"
    cache_dir = tmp_path / "cache"
    write_test_tone(audio)

    cache_path = analysis_cache_path(audio, cache_dir=cache_dir, feature_fps=5)
    load_or_analyze_audio(audio, cache_dir=cache_dir, feature_fps=5)
    forced = load_or_analyze_audio(audio, cache_dir=cache_dir, feature_fps=5, force=True)

    assert forced.cache_status == "forced"
    assert forced.cache_path == cache_path
