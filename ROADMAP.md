# WaveSmith Roadmap

WaveSmith starts as a local-first music visualizer. The future direction is a local creative engine
that can use richer shader-style visuals, lyrics, art direction, optional AI assistance, and
eventually GPU acceleration without compromising the offline MVP.

## Principles

- Keep core rendering local by default.
- Never upload user audio, lyrics, or generated media without explicit opt-in.
- Keep CPU rendering as the reference implementation and fallback.
- Treat shader-style art direction as a core creative feature, not only an optimization.
- Use AI assistance for art direction, preset generation, transcription, or poster concepts, not as
  a hard dependency for normal rendering.
- Prefer structured outputs such as JSON and YAML over arbitrary generated code.

## Current MVP

WaveSmith can:

- Render MP3/WAV files to MP4.
- Analyze audio and drive reactive visuals.
- Use three built-in presets.
- Cache analysis.
- Write render logs.
- Batch render folders.
- Extract local thumbnails from rendered MP4 files.

## v0.2 - Real Music Validation And Art Pass

Goal: make the MVP feel better on real songs before adding more system complexity.

Deliverables:

- Render several real MP3/WAV tracks.
- Tune visual response curves for bass, RMS, treble, spectrum, and waveform.
- Improve preset-specific module parameters.
- Add stronger preset identities and better default palettes.
- Add performance notes for 640x360, 1080p, and full-song renders.

Validation:

```bash
wavesmith render .tmp/music/song.mp3 .tmp/music/song-preview.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 20 --thumbnail
wavesmith render .tmp/music/song.mp3 .tmp/music/song-full.mp4 --preset neon_orb --resolution 640x360 --fps 15 --thumbnail
python -m pytest
```

Done when multiple real songs produce acceptable videos without code changes.

## v0.3 - Shader Visual Language

Goal: make WaveSmith noticeably more expressive before changing the backend.

This milestone focuses on "shader thinking" in the current renderer: layered fields, glow,
distortion, trails, palettes, masks, and audio-reactive parameters that can later map cleanly onto
a GPU backend.

Deliverables:

- Add a shader-style preset/module vocabulary for richer visuals.
- Add layered glow, bloom-like softness, trails, and motion smear where practical.
- Add audio-reactive distortion, pulse, rotation, field strength, and palette shifts.
- Add reusable visual primitives for rings, orbs, spectrum fields, waveform ribbons, and particles.
- Extend preset YAML so modules can express intensity curves and blend modes.
- Keep all new effects available through CPU rendering first.
- Add performance notes for the heavier effects and define sensible preview defaults.

Validation:

```bash
wavesmith render .tmp/music/song.mp3 .tmp/music/song-shader-preview.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 20 --thumbnail
wavesmith render .tmp/music/song.mp3 .tmp/music/song-shader-1080p.mp4 --preset neon_orb --resolution 1920x1080 --fps 30 --max-seconds 10
python -m pytest
```

Done when at least one preset feels like a real visual upgrade, renders reliably on CPU, and has a
clear path to GPU acceleration later.

## v0.4 - Lyrics Display

Goal: support lyrics when timed lyric files are already available.

Deliverables:

- Parse `.lrc`.
- Parse `.srt`.
- Add `--lyrics`.
- Add `--lyrics-offset`.
- Add simple bottom-center lyric rendering.
- Add fade in/out and line wrapping.
- Keep lyric display preset-aware but non-invasive.

Possible CLI:

```bash
wavesmith render song.mp3 out.mp4 --lyrics song.lrc --lyrics-offset 0.25
```

Validation:

- Render with `.lrc`.
- Render with `.srt`.
- Verify offset adjustment.
- Verify text does not collide with watermark or waveform at common resolutions.

Done when timed lyrics can be displayed clearly without requiring transcription.

## v0.5 - Lyrics As Art Direction

Goal: use lyrics as a creative signal, not only on-screen text.

Deliverables:

- `wavesmith art-brief --lyrics song.lrc --out song.art.json`
- Extract themes, mood, imagery, intensity, and palette hints.
- Generate compact local art briefs from lyrics.
- Use art briefs to recommend presets and module parameters.
- Use selected lyrics or summaries, not full copyrighted lyrics, for optional cloud workflows.

Possible art brief:

```json
{
  "mood": ["dark", "intimate", "restless"],
  "imagery": ["low light", "skin", "pressure"],
  "palette": ["deep violet", "cold cyan", "soft white"],
  "motion": "slow pressure waves with sharp chorus pulses"
}
```

Done when a lyric file can influence preset selection or preset YAML without hand editing.

## v0.6 - Prompt-To-Preset

Goal: let users describe a style and receive editable preset YAML.

Deliverables:

- `wavesmith make-preset "dark cyberpunk bass visualizer" --out presets/custom.yaml`
- Validate generated preset YAML before saving.
- Prefer deterministic templates and schema-bound structured output.
- Optional OpenAI-assisted preset generation behind explicit opt-in.

Rules:

- Generate YAML, not Python.
- Validate before writing.
- Never overwrite user presets without confirmation or explicit flag.

Done when generated presets validate and render.

## v0.7 - Poster Thumbnails

Goal: move beyond frame extraction when the user wants more intentional thumbnails.

Deliverables:

- Keep current ffmpeg frame extraction as default.
- Add poster-frame render mode using local visuals.
- Add `--thumbnail-style frame|poster`.
- Optional AI-generated poster concepts behind explicit opt-in.
- Support lyric/art-brief-driven poster prompts.

Done when thumbnails can be either faithful extracted frames or more designed poster images.

## v0.8 - GPU Render Backend

Goal: make the shader visual language faster and more scalable for high-resolution visuals.

Deliverables:

- Define `RenderBackend`.
- Move current Pillow renderer behind `CpuRenderBackend`.
- Add `--backend cpu|gpu`.
- Prototype ModernGL or another local GPU path.
- Port the v0.3 shader-style primitives to the GPU backend incrementally.
- Start with orb/ring rendering, glow fields, and palette shifts.
- Keep CPU fallback working unchanged.

Validation:

- CPU and GPU backends render the same song.
- GPU backend can render a short 1080p preview.
- Visual output is nonblank and audio muxing still works.
- GPU render timing is tracked against CPU timing for the same preset and resolution.

Done when GPU rendering can be selected explicitly and CPU remains the stable fallback.

## v0.9 - Optional AI Assist

Goal: use external AI only where it clearly helps and only with user consent.

Potential integrations:

- OpenAI image generation for poster art and styleboards.
- OpenAI transcription for lyric timing assistance when lyrics are missing.
- OpenAI structured output for preset YAML or art briefs.
- Hugging Face Diffusers for local or user-run image generation.
- Hugging Face local/audio models for mood, genre, or energy tagging.

Privacy rules:

- Default behavior remains local.
- Cloud features require explicit flags and clear user messaging.
- Prefer sending summaries or art briefs instead of full lyrics/audio.

Done when optional AI workflows are useful but never required for normal rendering.

## Parking Lot

- Album-art palette extraction.
- Multi-thumbnail contact sheets.
- Per-word karaoke display when enhanced LRC is available.
- Subtitle burn-in modes for YouTube/social formats.
- Cache pruning.
- JSON render logs or richer batch reports.
- Web UI wrapper.
- Render queue.
- Project files.
