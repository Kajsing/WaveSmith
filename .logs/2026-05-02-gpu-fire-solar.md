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

## Branching Filament Pass

The flare loops now branch into several offset strands per active loop. The lifecycle separates
growth from fade, so flares can grow larger while their outer filaments lose brightness.

Latest local preview:

```bash
.venv/bin/wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-fire-solar-preview-v7-wide-filaments.mp4 --backend gpu --preset gpu_fire_solar --seconds 10 --fps 30 --thumbnail-at best --crf 12 --ffmpeg-preset slow --watermark ""
```

Future option: add a sibling preset that places the whole sun in the center of frame with magnetic
arcs around the full circumference.

## Soft Eruption Pass

The branching version was still too sharp/spiky. The shader now shifts toward softer solar
simulation cues:

- broader loop distance fields;
- turbulent eruption clouds near active flare sources;
- visible source hotspots on the solar rim;
- lower hard-line dominance and warmer plasma color mixing.

Latest local preview:

```bash
.venv/bin/wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-fire-solar-preview-v11-soft-bursts.mp4 --backend gpu --preset gpu_fire_solar --seconds 10 --fps 30 --thumbnail-at best --crf 12 --ffmpeg-preset slow --watermark ""
```

More test songs are needed to tune the music mapping: bass should push eruption size, transient
hits should create short source flashes, and treble should add fine outer filament motion.
