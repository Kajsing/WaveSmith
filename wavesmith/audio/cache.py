"""Audio analysis cache utilities."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from wavesmith.audio.analyzer import DEFAULT_FEATURE_FPS, DEFAULT_SAMPLE_RATE, analyze_audio
from wavesmith.audio.features import AudioAnalysis, read_analysis

DEFAULT_ANALYSIS_CACHE_DIR = Path(".cache/analysis")
ANALYSIS_CACHE_VERSION = "v2"


@dataclass(frozen=True)
class CachedAnalysis:
    """Analysis payload with cache metadata."""

    analysis: AudioAnalysis
    cache_status: str
    cache_path: Path


def audio_cache_key(
    input_audio: Path,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    feature_fps: int = DEFAULT_FEATURE_FPS,
) -> str:
    """Hash audio bytes and analysis parameters into a deterministic cache key."""
    digest = hashlib.sha256()
    digest.update(ANALYSIS_CACHE_VERSION.encode("utf-8"))
    digest.update(str(sample_rate).encode("utf-8"))
    digest.update(str(feature_fps).encode("utf-8"))
    with input_audio.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analysis_cache_path(
    input_audio: Path,
    *,
    cache_dir: Path = DEFAULT_ANALYSIS_CACHE_DIR,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    feature_fps: int = DEFAULT_FEATURE_FPS,
) -> Path:
    """Return the cache path for an audio input and analysis parameters."""
    key = audio_cache_key(input_audio, sample_rate=sample_rate, feature_fps=feature_fps)
    return cache_dir / f"{key}.analysis.json"


def load_or_analyze_audio(
    input_audio: Path,
    *,
    force: bool = False,
    cache_dir: Path = DEFAULT_ANALYSIS_CACHE_DIR,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    feature_fps: int = DEFAULT_FEATURE_FPS,
) -> CachedAnalysis:
    """Load analysis from cache or run the analyzer and cache the result."""
    cache_path = analysis_cache_path(
        input_audio,
        cache_dir=cache_dir,
        sample_rate=sample_rate,
        feature_fps=feature_fps,
    )
    if cache_path.exists() and not force:
        try:
            return CachedAnalysis(read_analysis(cache_path), "hit", cache_path)
        except Exception:
            cache_status = "rebuilt"
        else:  # pragma: no cover - kept for readability around broad cache repair
            cache_status = "hit"
    else:
        cache_status = "forced" if force and cache_path.exists() else "miss"

    analysis = analyze_audio(input_audio, sample_rate=sample_rate, feature_fps=feature_fps)
    analysis.write_json(cache_path)
    return CachedAnalysis(analysis, cache_status, cache_path)
