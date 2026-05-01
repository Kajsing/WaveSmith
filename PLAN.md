# PLAN.md - WaveSmith Milestone Plan

## M0 - Repository Scaffold

Create package structure, CLI placeholder, docs, tests, and validation tooling.

Validation:

```bash
pip install -e .[dev]
wavesmith --help
ruff check .
python -m pytest
```

Done when the CLI can be invoked and tests run.

## M1 - Single-File Render Skeleton

Render generated frames through ffmpeg and mux with input audio.

Validation:

```bash
python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
wavesmith render .tmp/test.wav .tmp/test.mp4 --max-seconds 5 --resolution 640x360 --fps 15
ffprobe -v error -show_streams .tmp/test.mp4
python -m pytest
```

Done when output MP4 contains video and audio.

## M2 - Audio Analysis And Timeline

Extract audio features and expose frame-time lookup.

Validation:

```bash
wavesmith analyze .tmp/test.wav --out .tmp/test.analysis.json
python -m pytest
```

Done when features are normalized and timeline lookup is tested.

## M3 - First Real Preset: neon_orb

Implement center orb, spectrum ring, waveform ribbon, beat pulse, and watermark.

Validation:

```bash
wavesmith validate-preset presets/neon_orb.yaml
wavesmith render .tmp/test.wav .tmp/neon.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5
python -m pytest
```

Done when the output visibly reacts to audio.

## M4 - Preset Schema And Additional Presets

Add schema validation and two additional built-in presets.

Validation:

```bash
wavesmith list-presets
wavesmith validate-preset presets/neon_orb.yaml
wavesmith validate-preset presets/spectrum_ring.yaml
wavesmith validate-preset presets/waveform_ribbon.yaml
python -m pytest
```

Done when three presets validate and render.

## M5 - Analysis Cache And Render Logs

Add cache reuse, forced reanalysis, and render logs.

Validation:

```bash
wavesmith render .tmp/test.wav .tmp/cache1.mp4 --preset neon_orb --max-seconds 5
wavesmith render .tmp/test.wav .tmp/cache2.mp4 --preset neon_orb --max-seconds 5
wavesmith render .tmp/test.wav .tmp/cache3.mp4 --preset neon_orb --max-seconds 5 --force-analysis
python -m pytest
```

Done when cache reuse is observable and logs are written.

## M6 - Batch Rendering And Thumbnails

Add batch command and optional thumbnails.

Validation:

```bash
mkdir -p .tmp/batch-in .tmp/batch-out
python scripts/generate_test_audio.py .tmp/batch-in/a.wav --seconds 5
python scripts/generate_test_audio.py .tmp/batch-in/b.wav --seconds 5
wavesmith batch .tmp/batch-in .tmp/batch-out --preset neon_orb --max-seconds 5 --resolution 640x360 --fps 15
python -m pytest
```

Done when batch render produces expected outputs and summary.
