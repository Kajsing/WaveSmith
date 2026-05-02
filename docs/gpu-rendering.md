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

`gpu_crystal_storm` is the second GPU-first preset. It uses the same uniform contract, but targets a
crystal/fracture visual language with radial shards, spectrum-driven sparkle, and beat bloom.

The preset exposes shader quality controls through module fields:

- `detail`
- `bloom_strength`
- `warp_strength`
- `line_strength`
- `exposure`
- `softness`

The backend renders the shader with a single oversized fullscreen triangle. This avoids the
diagonal interpolation seam that can show up with two-triangle fullscreen quads on high-glow
shaders.

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

## Quality Pass

On May 2, 2026, the bloom shader was softened to reduce large block-like field artifacts:

- replaced the broad background value-noise field with a smoother flow field;
- kept fine noise mostly as subtle grain rather than a strong color driver;
- added preset-level tuning knobs for bloom, warp, line, exposure, softness, and detail;
- switched the GPU fullscreen primitive from a quad to one oversized triangle.
- generalized shader loading so built-in GPU presets can select other bundled `.glsl` shaders
  without opening arbitrary file paths.

High-quality local comparison render:

```bash
wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-bloom-preview-quality-v10-smooth.mp4 --backend gpu --preset gpu_shader_bloom --seconds 10 --fps 30 --thumbnail-at best --crf 12 --ffmpeg-preset slow --watermark ""
```

For quick previews, the default CRF remains fine. For visual inspection of glow-heavy GPU shaders,
use a lower CRF such as `--crf 12`.

Crystal storm comparison render:

```bash
wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-crystal-storm-preview-v2.mp4 --backend gpu --preset gpu_crystal_storm --seconds 10 --fps 30 --thumbnail-at best --crf 12 --ffmpeg-preset slow --watermark ""
```
