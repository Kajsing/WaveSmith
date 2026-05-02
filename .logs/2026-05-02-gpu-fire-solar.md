# 2026-05-02 GPU Fire Solar Notes

## Context

The CPU fire experiments were useful, but the desired direction was closer to solar prominences:
normal-looking solar arcs that flare with music and decay naturally. This adds the first GPU fire
family preset.

## Notes

- `gpu_fire_solar` uses the shared GPU uniform contract.
- The sun is intentionally low in frame, leaving visual space for prominence arcs.
- The shader uses a solar disk, rim glow, corona, granule texture, 24 spectrum-driven prominence
  anchors, and small sparks.
- The first shader compile failed because `active` is a reserved GLSL word; it was renamed to
  `active_level`.
- `compare --backend gpu` now includes `gpu_fire_solar` by default.

## Local Validation

```bash
.venv/bin/wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-fire-solar-preview-v1.mp4 --backend gpu --preset gpu_fire_solar --seconds 10 --fps 30 --thumbnail-at best --crf 12 --ffmpeg-preset slow --watermark ""
.venv/bin/wavesmith compare .tmp/music/Low\ Under-Skin.mp3 .tmp/gpu-compare-solar-v1 --backend gpu --seconds 10 --fps 30 --crf 12 --ffmpeg-preset slow --watermark ""
```

Compare result: 3 succeeded, 0 failed.

- `gpu_shader_bloom`: about 58.8 effective FPS
- `gpu_crystal_storm`: about 61.6 effective FPS
- `gpu_fire_solar`: about 63.3 effective FPS

## Flare Loop Pass

The first version looked too much like a row of small comb-like plumes. The shader now uses fewer
large magnetic-loop arcs:

- loop arcs are drawn with segment-distance fields instead of sampled dots;
- active loops fade in and out more slowly;
- subtle plasma noise modulates the loops so they feel less like smooth neon tubes.

Latest local preview:

```bash
.venv/bin/wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-fire-solar-preview-v5-plasma.mp4 --backend gpu --preset gpu_fire_solar --seconds 10 --fps 30 --thumbnail-at best --crf 12 --ffmpeg-preset slow --watermark ""
```
