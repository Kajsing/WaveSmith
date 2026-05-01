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

## Quick Preview

```bash
wavesmith render song.mp3 preview.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 20
```

For richer shader-style visuals, try:

```bash
wavesmith render song.mp3 shader-preview.mp4 --preset shader_bloom --resolution 640x360 --fps 15 --max-seconds 20
```

## Lyrics

WaveSmith can burn timed `.lrc` or `.srt` lyrics into a render:

```bash
wavesmith render song.mp3 lyric-video.mp4 --preset shader_bloom --lyrics song.lrc --lyrics-offset 0.25
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

## Thumbnail

```bash
wavesmith render song.mp3 preview.mp4 --preset neon_orb --thumbnail --thumbnail-at 50%
```

Thumbnails are extracted locally from the rendered MP4 with ffmpeg by default. Use poster style for
a designed local thumbnail based on preset colors and audio features:

```bash
wavesmith render song.mp3 preview.mp4 --preset shader_bloom --thumbnail --thumbnail-style poster
```

## List Presets

```bash
wavesmith list-presets
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

## Roadmap

See `ROADMAP.md` for planned future work, including shader-style visual upgrades, lyrics display,
lyrics-driven art direction, poster thumbnails, optional AI assistance, and GPU acceleration.
