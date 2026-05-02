# 2026-05-02 Compare Command Notes

## Context

After adding multiple GPU presets and timing metrics, choosing a visual direction still required
manual one-off render commands. A compare command makes A/B testing presets repeatable.

## Notes

- `wavesmith compare INPUT_AUDIO OUTPUT_DIR --preset A --preset B` renders one MP4 per preset.
- The command writes thumbnails by default and records `compare-summary.json`.
- Summary rows include status, output path, thumbnail path, cache status, log path, backend,
  encode time, effective FPS, and output size.
- Default presets are CPU-friendly on the CPU backend and GPU-focused on `--backend gpu`.

## Local Smoke

```bash
.venv/bin/python scripts/generate_test_audio.py .tmp/compare-test.wav --seconds 2
.venv/bin/wavesmith compare .tmp/compare-test.wav .tmp/compare-smoke --preset neon_orb --preset waveform_ribbon --resolution 320x180 --fps 10 --seconds 2 --watermark "" --crf 23 --ffmpeg-preset veryfast --thumbnail-at middle
```

Result: 2 succeeded, 0 failed.
