# 2026-05-02 Render Metrics Notes

## Context

After adding multiple GPU presets, we need quick local feedback on performance and output size
without manually timing commands.

## Notes

- `RenderResult` now carries backend, frame count, total elapsed time, encode elapsed time,
  effective FPS, and output size.
- Render logs include the same fields plus CRF and ffmpeg preset.
- CLI render summaries print backend, encode time, and effective FPS when available.
- Batch summaries retain per-item timing fields for later comparison.

## Local Smoke

```bash
.venv/bin/wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-crystal-storm-metrics-smoke.mp4 --backend gpu --preset gpu_crystal_storm --seconds 5 --fps 30 --thumbnail-at best --crf 12 --ffmpeg-preset slow --watermark ""
```

Observed locally on the RTX 3080 Ti WSL setup:

- `frame_count=150`
- `encode_elapsed_seconds=2.888`
- `effective_fps=51.9`
- `output_size_bytes=1326450`
