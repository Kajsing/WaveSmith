# 2026-05-02 GPU Crystal Storm Notes

## Context

The first GPU milestone proved a single bloom shader. The next step was to make the GPU backend
support more than one bundled shader and add a second aesthetic target.

## Notes

- `gpu_crystal_storm` uses the same uniform contract as `gpu_shader_bloom`.
- The shader-loader now accepts safe bundled shader names and rejects path traversal or unknown
  shaders.
- The first crystal preview read too much like a soft portal, so the shader was tuned toward
  stronger radial shards, fracture lines, and brighter spectrum sparks.
- The latest local preview was:

```bash
.venv/bin/wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-crystal-storm-preview-v2.mp4 --backend gpu --preset gpu_crystal_storm --seconds 10 --fps 30 --thumbnail-at best --crf 12 --ffmpeg-preset slow --watermark ""
```
