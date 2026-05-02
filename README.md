# WaveSmith

WaveSmith is a local-first Python CLI tool for turning audio files into beat-reactive
music visualizer videos.

## Requirements

- WSL2 or Linux
- Python 3.11+
- ffmpeg

## Setup

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
```

## Render A Video

```bash
wavesmith render song.mp3 out.mp4 --preset neon_orb --resolution 1920x1080 --fps 30
```

CPU is the stable reference backend. The `gpu` backend flag is reserved for the future shader
renderer and currently fails explicitly instead of silently falling back:

```bash
wavesmith render song.mp3 out.mp4 --backend cpu
```

## Quick Preview

```bash
wavesmith preview song.mp3 preview.mp4 --preset neon_orb
wavesmith render song.mp3 preview.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 20
```

GPU rendering is experimental and optional:

```bash
pip install -e .[dev,gpu]
wavesmith gpu-info
wavesmith preview song.mp3 gpu-preview.mp4 --backend gpu --preset gpu_shader_bloom
```

For richer shader-style visuals, try:

```bash
wavesmith render song.mp3 shader-preview.mp4 --preset shader_bloom --resolution 640x360 --fps 15 --max-seconds 20
```

For a more dramatic elemental look with fire, water, plasma, and heavier motion:

```bash
wavesmith render song.mp3 storm-preview.mp4 --preset elemental_storm --resolution 640x360 --fps 15 --max-seconds 20
```

For a cinematic portal/waveform look inspired by fire visualizer posters:

```bash
wavesmith render song.mp3 inferno-preview.mp4 --preset inferno_portal --resolution 640x360 --fps 15 --max-seconds 20
```

For organic earth visuals with fine audio-reactive growth spikes:

```bash
wavesmith preview song.mp3 earth-surface.mp4 --preset earth_surface_spikes
wavesmith preview song.mp3 earth-orb.mp4 --preset earth_orb_spikes
```

Advanced presets can also use a local image as a cinematic backdrop with the `image_backdrop`
module. This keeps the workflow local while allowing generated or hand-made style frames to drive
the look.

## Lyrics

WaveSmith can burn timed `.lrc` or `.srt` lyrics into a render:

```bash
wavesmith render song.mp3 lyric-video.mp4 --preset shader_bloom --lyrics song.lrc --lyrics-offset 0.25
```

Inspect timing before rendering:

```bash
wavesmith lyrics-inspect song.lrc
```

Lyrics can also drive local art direction:

```bash
wavesmith art-brief --lyrics song.lrc --out song.art.json
```

## Prompt To Preset

Generate editable preset YAML locally from a short style prompt:

```bash
wavesmith make-preset "dark cyberpunk shader bloom" --name dark_cyber --out presets/dark_cyber.yaml
wavesmith validate-preset presets/dark_cyber.yaml
```

## Optional AI Assist

WaveSmith does not upload audio, lyrics, or art briefs by default. You can prepare a local AI prompt
manifest for a later explicit OpenAI/Hugging Face workflow:

```bash
wavesmith ai-prompt song.art.json --target poster --provider openai --out song.ai-prompt.json
```

## Thumbnail

```bash
wavesmith render song.mp3 preview.mp4 --preset neon_orb --thumbnail --thumbnail-at 50%
```

`--thumbnail-at` accepts seconds, percentages, `best`, and named positions such as `intro`,
`middle`, and `end`. `best` chooses a strong local moment from the audio analysis.

Thumbnails are extracted locally from the rendered MP4 with ffmpeg by default. Use poster style for
a designed local thumbnail based on preset colors and audio features:

```bash
wavesmith render song.mp3 preview.mp4 --preset shader_bloom --thumbnail --thumbnail-style poster
```

## List Presets

```bash
wavesmith list-presets
wavesmith list-presets --details
wavesmith list-presets --family earth --details
wavesmith list-presets --tag fire
```

## Validate A Preset

```bash
wavesmith validate-preset presets/neon_orb.yaml
```

## Batch Render

```bash
wavesmith batch ./songs ./renders --preset spectrum_ring --resolution 640x360 --fps 15
```

Batch render writes `batch-summary.json` and thumbnails under the output directory by default.

## Development Validation

```bash
ruff check .
python -m pytest
```

## Generated Files

Rendered videos, user audio, logs, and large analysis caches should not be committed to Git.
Use `.tmp/art/` for generated image experiments. Move selected reusable textures, backdrops, or
reference frames into `assets/` when they should become part of the project.

## Roadmap

See `ROADMAP.md` for planned future work, including shader-style visual upgrades, lyrics display,
lyrics-driven art direction, poster thumbnails, optional AI assistance, and GPU acceleration.
