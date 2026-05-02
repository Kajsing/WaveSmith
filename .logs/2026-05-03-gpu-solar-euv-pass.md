# GPU Solar EUV Pass

Goal: move `gpu_fire_solar` closer to the solar-observatory references: low solar limb, dark sky,
soft magnetic prominence loops, local footpoint hotspots, and less broad yellow haze.

Notes:

- Several reversed `smoothstep` calls in `solar_fire.glsl` were replaced with explicit
  `1.0 - smoothstep(...)` masks. Reversed edges are undefined in GLSL and were contributing to
  unstable broad glow.
- The volumetric veil/eruption layers were reduced after preview testing because they washed the
  sky into diffuse haze instead of drawing readable prominence shapes.
- Active flare sources are now constrained to the upper solar limb so the audio-reactive motion is
  visible in the current low-sun perspective.
- The current look is intentionally stylized EUV rather than a physical simulation. More test songs
  should be used to tune how quickly hotspots appear, fade, and reappear.

Primary preview:

```bash
.venv/bin/wavesmith preview .tmp/music/Low\ Under-Skin.mp3 .tmp/music/gpu-fire-solar-preview-v19-hotspot-arcs.mp4 --backend gpu --preset gpu_fire_solar --seconds 10 --fps 30 --thumbnail-at best --crf 12 --ffmpeg-preset slow --watermark=
```
