"""Audio analysis entry points."""

from pathlib import Path

import librosa
import numpy as np

from wavesmith.audio.features import AudioAnalysis, TimeSeries

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav"}
DEFAULT_SAMPLE_RATE = 22_050
HOP_LENGTH = 512
N_FFT = 2048
SPECTRUM_BINS = 32
WAVEFORM_PREVIEW_BINS = 32


class AudioAnalysisError(RuntimeError):
    """Raised when audio analysis cannot be completed."""


def analyze_audio(path: Path, *, sample_rate: int = DEFAULT_SAMPLE_RATE) -> AudioAnalysis:
    """Analyze an MP3 or WAV file into normalized feature series."""
    if not path.exists():
        raise AudioAnalysisError(f"Input audio file does not exist: {path}")
    if path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise AudioAnalysisError("Input audio must be an MP3 or WAV file.")

    try:
        audio, sr = librosa.load(path, sr=sample_rate, mono=True)
    except Exception as exc:  # pragma: no cover - library-specific errors vary
        raise AudioAnalysisError(f"Could not load audio file: {path}") from exc

    if audio.size == 0:
        raise AudioAnalysisError("Input audio contains no samples.")

    duration = float(librosa.get_duration(y=audio, sr=sr))
    if duration <= 0:
        raise AudioAnalysisError("Input audio duration must be greater than zero.")

    frame_times = _frame_times(audio, sr)
    magnitude = np.abs(librosa.stft(audio, n_fft=N_FFT, hop_length=HOP_LENGTH))
    rms = librosa.feature.rms(y=audio, frame_length=N_FFT, hop_length=HOP_LENGTH)[0]
    tempo_bpm, beat_frames = librosa.beat.beat_track(y=audio, sr=sr, hop_length=HOP_LENGTH)
    onset_times = librosa.onset.onset_detect(
        y=audio,
        sr=sr,
        hop_length=HOP_LENGTH,
        units="time",
    )

    spectrum = librosa.feature.melspectrogram(
        y=audio,
        sr=sr,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=SPECTRUM_BINS,
        power=2.0,
    )
    spectrum_db = librosa.power_to_db(spectrum, ref=np.max)
    spectrum_normalized = _normalize_array(spectrum_db).T

    return AudioAnalysis(
        duration_seconds=round(duration, 6),
        sample_rate=int(sr),
        tempo_bpm=round(_coerce_tempo(tempo_bpm), 6),
        beats=_round_list(librosa.frames_to_time(beat_frames, sr=sr, hop_length=HOP_LENGTH)),
        onsets=_round_list(onset_times),
        rms=_series(frame_times, _normalize_array(rms)),
        bass_energy=_series(frame_times, _band_energy(magnitude, sr, 20.0, 250.0)),
        mid_energy=_series(frame_times, _band_energy(magnitude, sr, 250.0, 4_000.0)),
        treble_energy=_series(frame_times, _band_energy(magnitude, sr, 4_000.0, sr / 2)),
        spectrum=_vector_series(frame_times, spectrum_normalized),
        waveform_preview=_vector_series(
            frame_times,
            _waveform_preview(audio, sr, frame_times, duration),
        ),
    )


def _frame_times(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    frame_count = 1 + int(np.floor(max(0, audio.size - 1) / HOP_LENGTH))
    return librosa.frames_to_time(np.arange(frame_count), sr=sample_rate, hop_length=HOP_LENGTH)


def _band_energy(
    magnitude: np.ndarray,
    sample_rate: int,
    low_hz: float,
    high_hz: float,
) -> np.ndarray:
    freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=N_FFT)
    mask = (freqs >= low_hz) & (freqs < high_hz)
    if not np.any(mask):
        return np.zeros(magnitude.shape[1], dtype=float)
    return _normalize_array(np.mean(magnitude[mask, :], axis=0))


def _waveform_preview(
    audio: np.ndarray,
    sample_rate: int,
    frame_times: np.ndarray,
    duration: float,
) -> np.ndarray:
    if audio.size == 1:
        return np.full((frame_times.size, WAVEFORM_PREVIEW_BINS), 0.5, dtype=float)

    half_window_seconds = min(0.05, duration / 2)
    sample_positions = np.linspace(0, duration, audio.size)
    previews: list[np.ndarray] = []
    for time_seconds in frame_times:
        start = max(0.0, float(time_seconds) - half_window_seconds)
        end = min(duration, float(time_seconds) + half_window_seconds)
        if start == end:
            end = min(duration, start + 1 / sample_rate)
        target_times = np.linspace(start, end, WAVEFORM_PREVIEW_BINS)
        samples = np.interp(target_times, sample_positions, audio)
        previews.append(np.clip((samples + 1.0) / 2.0, 0.0, 1.0))
    return np.vstack(previews)


def _normalize_array(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return values
    min_value = float(np.min(values))
    max_value = float(np.max(values))
    if np.isclose(max_value, min_value):
        return np.zeros_like(values, dtype=float)
    return np.clip((values - min_value) / (max_value - min_value), 0.0, 1.0)


def _series(times: np.ndarray, values: np.ndarray) -> TimeSeries:
    length = min(times.size, values.size)
    return TimeSeries(times=_round_list(times[:length]), values=_round_list(values[:length]))


def _vector_series(times: np.ndarray, values: np.ndarray) -> TimeSeries:
    length = min(times.size, values.shape[0])
    return TimeSeries(
        times=_round_list(times[:length]),
        values=[_round_list(row) for row in values[:length]],
    )


def _round_list(values: np.ndarray) -> list[float]:
    return [round(float(value), 6) for value in values]


def _coerce_tempo(value: object) -> float:
    array = np.asarray(value, dtype=float)
    if array.size == 0:
        return 0.0
    return float(array.reshape(-1)[0])
