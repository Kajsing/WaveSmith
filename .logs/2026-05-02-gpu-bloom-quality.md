# 2026-05-02 GPU Bloom Quality Notes

## Context

The first GPU bloom preview rendered correctly, but glow-heavy frames showed visible block-like
field artifacts. The issue was most visible around bright edges and in the background mist.

## Notes

- Lower CRF helps compression, but the largest artifacts were present before encoding and came from
  the shader field itself.
- Broad value noise created large block/facet shapes, so the background mist now uses smoother
  trigonometric flow.
- Fine noise remains in the shader, but it is used as subtle grain instead of a strong color driver.
- The backend now draws one oversized fullscreen triangle to avoid possible two-triangle quad seams.
- For glow-heavy visual checks, use `--crf 12 --ffmpeg-preset slow`.

## Latest Local Preview

```bash
.venv/bin/wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-bloom-preview-quality-v10-smooth.mp4 --backend gpu --preset gpu_shader_bloom --seconds 10 --fps 30 --thumbnail-at best --crf 12 --ffmpeg-preset slow --watermark ""
```
