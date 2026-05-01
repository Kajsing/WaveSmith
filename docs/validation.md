# Validation

## Setup

```bash
python3 --version
ffmpeg -version
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
```

## Static Validation

```bash
ruff check .
python -m pytest
```

## CLI Validation

```bash
wavesmith --help
wavesmith list-presets
wavesmith validate-preset presets/neon_orb.yaml
```

## Future Smoke Render

```bash
python scripts/generate_test_audio.py .tmp/test-tone.wav --seconds 5
wavesmith render .tmp/test-tone.wav .tmp/test-tone.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 .tmp/test-tone.mp4
```
