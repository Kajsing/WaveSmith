# GPU Rendering

WaveSmith keeps the CPU renderer as the default and reference path. GPU rendering is experimental,
opt-in, and currently targets a ModernGL fullscreen shader backend under WSL.

## Current Target

- Backend: ModernGL with an offscreen standalone context.
- Local validation target: NVIDIA GeForce RTX 3080 Ti exposed through WSL.
- Setup:

```bash
pip install -e .[dev,gpu]
wavesmith gpu-info
```

## First GPU Preset

`gpu_shader_bloom` is the first GPU-first preset. It uses a fullscreen fragment shader with domain
warp, bloom-like glow, palette mixing, and 32-bin spectrum reactivity. It is intentionally not a
port of the CPU presets.

## Validation

```bash
wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-bloom-preview.mp4 --backend gpu --preset gpu_shader_bloom --seconds 10 --fps 30 --thumbnail-at best
ruff check .
python -m pytest
```

GPU failures should be explicit. Missing dependencies or context failures should mention:
`pip install -e .[gpu]`.

## Initial Local Validation

On May 2, 2026, `wavesmith gpu-info` detected:

- Renderer: `D3D12 (NVIDIA GeForce RTX 3080 Ti)`
- Version: `4.2 (Core Profile) Mesa 23.2.1-1ubuntu3.1~22.04.3`

A 10 second 640x360 preview rendered successfully with:

```bash
wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-bloom-preview-v2.mp4 --backend gpu --preset gpu_shader_bloom --seconds 10 --fps 30 --thumbnail-at best
```
