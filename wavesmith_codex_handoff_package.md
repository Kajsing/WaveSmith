# WaveSmith — Codex Handoff Package

## 1. Human-Readable Summary

**Project name:** WaveSmith  
**Working tagline:** Local-first audio-reactive video generation for music, AI songs, demos, and creative experiments.

WaveSmith is a local Python/WSL CLI tool that turns audio files into visually interesting beat-reactive videos. It analyzes an input audio file, extracts music features, applies a configurable visual preset, renders frames, and encodes a final video with the original audio.

The project starts as a practical CLI-first renderer, not a GUI application. The architecture must allow future growth into a larger creative engine with preset authoring, lyrics/subtitles, batch rendering, thumbnails, and optional GPU/shader backends.

The v1 goal is intentionally narrow:

> Given an MP3 or WAV file, WaveSmith can render a complete MP4 music visualizer video using one of several built-in presets, with deterministic output, basic render logging, and repeatable validation commands.

---

## 2. Project Core v0.1

### One-sentence goal

Build a local-first Python CLI application that converts audio files into beat-reactive music videos using configurable visual presets.

### Problem being solved

The user wants a personal, scriptable, extensible visualizer tool for generating interesting music videos from MP3 files without relying on cloud services, paid APIs, or opaque online video generators.

### Target user

Primary target user:

- Christian Kajsing, technical power user on Windows using WSL and Python.

Secondary future users:

- Hobby musicians.
- AI music creators.
- People generating videos for YouTube, Suno-style songs, demos, experiments, and personal projects.

### Primary workflow

1. User provides an audio file.
2. User selects a visual preset.
3. WaveSmith analyzes the audio.
4. WaveSmith renders frames according to the preset.
5. WaveSmith encodes an MP4 with the original audio.
6. WaveSmith writes metadata, logs, and optionally a thumbnail.

### Expected input

Minimum v1 input:

- `.mp3`
- `.wav`

Future input:

- `.flac`
- `.m4a`
- `.ogg`
- `.srt`
- `.lrc`
- album art image
- prompt describing desired style

### Expected output

Minimum v1 output:

- `.mp4` video with original audio
- render log
- optional analysis cache JSON

Future output:

- thumbnail image
- multiple aspect ratios
- project metadata JSON
- subtitle-burned video
- WebM export

### Platform/runtime

- Windows host
- WSL2 runtime
- Python 3.11+
- ffmpeg installed in WSL

### Local/cloud/offline requirements

- Must run fully local in v1.
- Must not require cloud services.
- Must not require paid APIs.
- Must not upload user audio anywhere.

---

## 3. Facts, Assumptions, Unknowns, and Decisions

### Facts

- User works on Windows and uses WSL for Docker/Python workflows.
- User wants Python.
- User wants a creative audio visualizer/video generator.
- User wants a Codex-ready project specification.
- Final handoff output should be in English.
- The project should be suitable for autonomous milestone-based implementation.

### Assumptions

- ASSUMPTION: The initial implementation should prioritize CLI usage over GUI.
- ASSUMPTION: The tool should be local-first and offline-capable.
- ASSUMPTION: ffmpeg is acceptable as an external dependency.
- ASSUMPTION: Python CPU rendering is acceptable for v1 even if slower than GPU rendering.
- ASSUMPTION: User prefers extensibility and maintainability over maximum initial render speed.
- ASSUMPTION: Generated output files should not be committed to Git.
- ASSUMPTION: The project can start with MP3/WAV support only.

### Unknowns

- UNKNOWN: Final project name. This package uses `WaveSmith` as a working name.
- UNKNOWN: Preferred license.
- UNKNOWN: Whether the final tool should have a GUI.
- UNKNOWN: Whether GPU/shader rendering is required later.
- UNKNOWN: Whether lyrics/subtitle sync is a hard requirement.
- UNKNOWN: Whether the user wants watermarking enabled by default.

### Initial decision log

| ID | Decision | Status | Reason |
|---|---|---:|---|
| D001 | Use Python 3.11+ | Locked for v1 | User requested Python; good Codex compatibility. |
| D002 | Use ffmpeg for encoding/muxing | Locked for v1 | Robust, standard, avoids custom codec work. |
| D003 | CLI-first, no GUI in v1 | Locked for v1 | Keeps MVP small and testable. |
| D004 | CPU renderer first | Reversible | Easier implementation/debugging; GPU can be added behind backend interface. |
| D005 | YAML presets | Reversible | Human-editable, good for style configs. |
| D006 | Cache audio analysis as JSON | Planned | Avoids repeated analysis and supports debugging. |
| D007 | No cloud dependencies | Locked for v1 | Local-first requirement. |

---

## 4. Product Requirements

### Goal

WaveSmith should make it easy to generate visually engaging audio-reactive videos from local music files with repeatable commands and configurable visual styles.

### User stories

#### US001 — Render one audio file

As a user, I want to run one command with an MP3 file and get an MP4 video, so that I can quickly generate a music visualizer.

Acceptance criteria:

- Command accepts an input audio path.
- Command accepts an output video path.
- Command renders a complete MP4.
- Output video contains the original audio.
- Command exits non-zero on failure.

#### US002 — Select visual preset

As a user, I want to choose between visual presets, so that different songs can have different moods.

Acceptance criteria:

- CLI exposes `--preset`.
- At least three presets exist in v1.
- Unknown preset names produce a clear error.
- Presets are listed via `wavesmith list-presets`.

#### US003 — Analyze audio once and cache it

As a user, I want WaveSmith to cache audio analysis, so that repeated renders do not reprocess the same audio unnecessarily.

Acceptance criteria:

- Analysis can be written to cache.
- Cache can be reused automatically when valid.
- User can force re-analysis.
- Cache format is JSON.

#### US004 — Batch render a folder

As a user, I want to render multiple songs from a folder, so that I can create videos for several tracks without manual repetition.

Acceptance criteria:

- CLI supports batch input directory.
- Batch mode writes one output per source audio file.
- Batch mode continues or stops according to a clear failure policy.
- Render summary is written after batch completion.

#### US005 — Control output format

As a user, I want to choose resolution, FPS, duration limit, and quality, so that I can make quick previews or final renders.

Acceptance criteria:

- CLI supports `--resolution`.
- CLI supports `--fps`.
- CLI supports `--max-seconds` for preview renders.
- CLI supports ffmpeg CRF or quality preset.

#### US006 — Add personal watermark/credit

As a user, I want to configure watermark text, so that generated videos can carry my own credit instead of a tool credit.

Acceptance criteria:

- CLI supports `--watermark`.
- Empty string disables watermark.
- Presets may define default watermark placement/style.
- Watermark rendering does not crash if fonts are unavailable.

---

## 5. Non-goals

The following are explicitly not v1 goals:

- No GUI.
- No web app.
- No Electron app.
- No live preview.
- No cloud rendering.
- No user accounts.
- No upload service.
- No plugin marketplace.
- No AI-generated video.
- No paid API dependency.
- No real-time VJ/live audio input.
- No professional NLE replacement.
- No advanced timeline editor.

Future scope may revisit these, but they must not leak into v1 implementation.

---

## 6. MVP Scope

### v1.0 MVP must include

- CLI executable/module.
- Single-file render command.
- MP3/WAV input support.
- MP4 output with original audio.
- ffmpeg integration.
- Audio feature extraction.
- Basic analysis cache.
- Three built-in presets:
  - `neon_orb`
  - `spectrum_ring`
  - `waveform_ribbon`
- Configurable resolution/FPS/duration limit.
- Configurable watermark text.
- Render log.
- Unit tests for non-rendering logic.
- Smoke test that renders a short sample.

### v1.1 should include

- Batch rendering.
- Thumbnail output.
- More robust preset schema validation.
- More presets.
- Improved docs and examples.

### Future scope

- Lyrics/subtitle import.
- Whisper-assisted transcription.
- Prompt-to-preset generation.
- Album art color extraction.
- GPU/shader backend.
- Web UI wrapper.
- Render queue.
- Project files.
- YouTube/Social presets.

---

## 7. Success Criteria

WaveSmith v1 is successful when:

1. A user can install dependencies in WSL using documented commands.
2. A user can render a 20-second preview from an MP3 with one command.
3. A user can render a full MP4 from an MP3 with one command.
4. Output video includes synchronized original audio.
5. At least three visual presets work.
6. Audio analysis can be cached and reused.
7. Generated outputs are excluded from Git.
8. Tests pass with `pytest`.
9. Lint/type checks pass or documented exceptions exist.
10. A render smoke test can be run locally.

---

## 8. Technical Decisions

| Area | Decision | Reason |
|---|---|---|
| Language | Python 3.11+ | Good ecosystem and Codex friendliness. |
| Runtime | WSL2/Linux | User environment; ffmpeg is straightforward. |
| CLI | Typer or argparse | Typer preferred for cleaner CLI; argparse acceptable if dependency minimization wins. |
| Audio analysis | librosa + numpy | Mature audio feature extraction. |
| Rendering v1 | NumPy + Pillow/OpenCV | Local, inspectable, easy to debug. |
| Encoding | ffmpeg subprocess | Robust video/audio muxing. |
| Preset format | YAML | Human-editable visual configs. |
| Config validation | pydantic or jsonschema | Prevent broken presets. |
| Testing | pytest | Standard Python test runner. |
| Linting | ruff | Fast and simple. |
| Typing | mypy optional in v1 | Useful, but not a blocker if graphics code becomes noisy. |
| Logging | Python logging + per-render log file | Debuggability. |
| Cache | JSON files keyed by audio hash | Repeatability and transparency. |
| Packaging | pyproject.toml | Modern Python project layout. |

### Recommended dependency set

Minimum:

```txt
numpy
pillow
librosa
soundfile
pyyaml
pydantic
rich
typer
pytest
ruff
```

System dependency:

```bash
ffmpeg
```

Optional later:

```txt
opencv-python
moderngl
moviepy
whisper
```

---

## 9. Architecture

### Architecture overview

WaveSmith is a modular CLI application with five primary layers:

1. CLI layer
2. Audio analysis layer
3. Timeline/features layer
4. Visual preset/rendering layer
5. Encoding/output layer

The core design rule:

> Audio analysis, visual state, frame rendering, and ffmpeg encoding must be separate modules. Presets must configure behavior without requiring style-specific logic in the core pipeline.

### Data flow

```text
Audio file
  ↓
CLI command validates input/output/options
  ↓
Audio analyzer loads audio and extracts features
  ↓
Analysis cache stores/reuses feature JSON
  ↓
Timeline model exposes per-frame feature values
  ↓
Preset loader loads YAML visual style config
  ↓
Render pipeline creates frame stream
  ↓
Frame writer pipes raw video frames to ffmpeg
  ↓
ffmpeg muxes rendered frames with source audio
  ↓
MP4 + render log + optional metadata/thumbnail
```

### Component responsibilities

#### `wavesmith/cli.py`

Owns:

- Command parsing.
- User-facing errors.
- Invoking render/analyze/batch/list commands.

Must not own:

- Audio analysis implementation.
- Visual rendering implementation.
- ffmpeg command construction details.

#### `wavesmith/audio/analyzer.py`

Owns:

- Loading audio.
- Sampling/resampling policy.
- Extracting features.
- Returning normalized analysis model.

Must not own:

- Video frame rendering.
- Preset styling.
- ffmpeg encoding.

#### `wavesmith/audio/cache.py`

Owns:

- Hashing audio inputs.
- Cache path creation.
- Reading/writing analysis JSON.
- Cache invalidation rules.

#### `wavesmith/timeline/model.py`

Owns:

- Frame-time feature lookup.
- Interpolation/smoothing.
- Beat/onset lookup.
- Section-like timeline abstraction.

#### `wavesmith/presets/loader.py`

Owns:

- Loading built-in or user-supplied YAML presets.
- Validating schema.
- Returning normalized preset config.

#### `wavesmith/render/pipeline.py`

Owns:

- Connecting timeline, preset, visual modules, and encoder.
- Iterating frames.
- Progress reporting.
- Render cancellation/failure propagation.

#### `wavesmith/render/ffmpeg.py`

Owns:

- ffmpeg path detection.
- Command construction.
- Raw frame pipe management.
- Audio muxing.
- Encoding error reporting.

#### `wavesmith/visuals/*`

Owns:

- Visual primitives and modules.
- Drawing frame elements.
- Accepting normalized feature inputs.
- Avoiding global mutable state unless justified.

---

## 10. Visual Preset Model

### Preset design goal

Presets should be editable files that describe visual behavior without requiring users to modify Python code.

### Example preset file

`presets/neon_orb.yaml`

```yaml
name: neon_orb
version: 1
description: Neon bass orb with spectrum ring, waveform ribbon, glow, and particles.

canvas:
  background: radial_void
  glow: true

palette:
  mode: reactive
  base: [180, 80, 255]
  accent: [80, 220, 255]
  beat: [255, 255, 255]

watermark:
  enabled: true
  text: "Christian Kajsing // kajsing.com"
  position: bottom_right
  opacity: 0.55

modules:
  - type: center_orb
    id: bass_orb
    radius:
      base: 90
      feature: bass_energy
      scale: 120
      smoothing: 0.22
    glow:
      feature: rms
      scale: 1.5

  - type: spectrum_ring
    id: main_ring
    radius:
      base: 220
      feature: rms
      scale: 40
    bars:
      count: 128
      height_feature: spectrum
      scale: 180

  - type: waveform_ribbon
    id: lower_ribbon
    position: bottom
    height: 160
    feature: waveform
    opacity: 0.75

  - type: particles
    id: foxfire_particles
    count: 500
    velocity_feature: treble_energy
    burst_on: beat
```

### Preset schema requirements

Each preset must have:

- `name`
- `version`
- `description`
- `canvas`
- `palette`
- `modules`

Each module must have:

- `type`
- `id`

Invalid presets must fail before rendering starts.

---

## 11. Audio Feature Model

### Required v1 features

WaveSmith v1 should expose these normalized features:

```yaml
features:
  duration_seconds: float
  sample_rate: int
  tempo_bpm: float
  beats: list[float]
  onsets: list[float]
  rms: time_series[float]
  bass_energy: time_series[float]
  mid_energy: time_series[float]
  treble_energy: time_series[float]
  spectrum: time_series[list[float]]
  waveform_preview: time_series[list[float]]
```

### Normalization rule

Feature values used by visual modules should generally be normalized to `0.0–1.0`, unless explicitly documented otherwise.

### Time lookup rule

Visual modules should not index raw audio arrays directly. They should ask the timeline model for feature values at render time:

```python
features = timeline.at(time_seconds)
```

---

## 12. CLI Design

### Commands

```bash
wavesmith render INPUT_AUDIO OUTPUT_VIDEO [options]
wavesmith analyze INPUT_AUDIO [options]
wavesmith batch INPUT_DIR OUTPUT_DIR [options]
wavesmith list-presets
wavesmith validate-preset PRESET_FILE
```

### Render command options

```bash
wavesmith render song.mp3 out.mp4 \
  --preset neon_orb \
  --resolution 1920x1080 \
  --fps 30 \
  --max-seconds 20 \
  --watermark "Christian Kajsing // kajsing.com" \
  --crf 18 \
  --ffmpeg-preset medium \
  --force-analysis
```

### Batch command example

```bash
wavesmith batch ./songs ./renders \
  --preset spectrum_ring \
  --resolution 1920x1080 \
  --fps 30 \
  --crf 20
```

### Analyze command example

```bash
wavesmith analyze song.mp3 --out .cache/song.analysis.json
```

---

## 13. Error Handling Philosophy

Errors must be specific and actionable.

Good:

```text
Preset 'cyber_void' was not found. Run 'wavesmith list-presets' to see available presets.
```

Bad:

```text
Error: failed.
```

### Required failure cases

WaveSmith must handle:

- Missing input file.
- Unsupported input extension.
- Missing ffmpeg binary.
- Invalid output path.
- Invalid preset name.
- Invalid preset schema.
- Audio analysis failure.
- ffmpeg process failure.
- Broken pipe during frame streaming.
- User interruption.

### Exit code policy

- `0`: success
- `1`: generic failure
- `2`: invalid user input
- `3`: dependency missing
- `4`: render failed
- `5`: validation failed

---

## 14. Logging Strategy

Each render should write:

- command options
- resolved input/output paths
- selected preset
- duration
- resolution
- FPS
- analysis cache status
- render start/end timestamps
- ffmpeg command
- error details if failed

Default log location:

```text
.renders/logs/<timestamp>-<audio-stem>.log
```

Generated logs should be excluded from Git unless they are tiny curated examples.

---

## 15. Storage Layout

Default generated files:

```text
.renders/
  videos/
  thumbnails/
  logs/
.cache/
  analysis/
```

Git policy:

- Do not commit rendered videos.
- Do not commit user audio files.
- Do not commit large generated caches.
- Commit small synthetic test fixtures only.

---

## 16. Suggested Repository Structure

```text
wavesmith/
  AGENTS.md
  PLAN.md
  IMPLEMENT.md
  DOCUMENTATION.md
  SPEC.yaml
  ARCHITECTURE.md
  README.md
  pyproject.toml
  .gitignore
  .env.example

  wavesmith/
    __init__.py
    cli.py

    audio/
      __init__.py
      analyzer.py
      cache.py
      features.py

    timeline/
      __init__.py
      model.py
      smoothing.py
      sections.py

    presets/
      __init__.py
      loader.py
      schema.py

    render/
      __init__.py
      pipeline.py
      ffmpeg.py
      frame_writer.py
      options.py

    visuals/
      __init__.py
      base.py
      background.py
      center_orb.py
      spectrum_ring.py
      waveform_ribbon.py
      particles.py
      text.py

    utils/
      __init__.py
      paths.py
      logging.py
      colors.py
      math.py

  presets/
    neon_orb.yaml
    spectrum_ring.yaml
    waveform_ribbon.yaml

  examples/
    README.md
    sample_commands.md

  tests/
    test_preset_loader.py
    test_audio_cache.py
    test_timeline_model.py
    test_ffmpeg_command.py
    test_cli_validation.py

  docs/
    decisions/
      0001-cli-first.md
      0002-cpu-renderer-first.md
      0003-yaml-presets.md
    risks.md
    validation.md
    project-format.md

  .logs/
    README.md
```

---

## 17. Validation Plan

### Setup validation

```bash
python3 --version
ffmpeg -version
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
```

### Static validation

```bash
ruff check .
python -m pytest
```

Optional:

```bash
mypy wavesmith
```

### CLI validation

```bash
wavesmith --help
wavesmith list-presets
wavesmith validate-preset presets/neon_orb.yaml
```

### Render smoke validation

Use a tiny generated test tone or a short checked-in fixture.

```bash
python scripts/generate_test_audio.py .tmp/test-tone.wav --seconds 5
wavesmith render .tmp/test-tone.wav .tmp/test-tone.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5
```

Expected result:

- `.tmp/test-tone.mp4` exists.
- File size is greater than zero.
- ffprobe can read duration and video stream.

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 .tmp/test-tone.mp4
```

### Manual visual validation

For each preset:

- Render 10–20 seconds.
- Confirm no blank frames.
- Confirm visible audio reactivity.
- Confirm watermark option works.
- Confirm output contains audio.

---

## 18. Milestone Plan

### M0 — Repository scaffold

Goal:

Create the repository structure, packaging, basic CLI entrypoint, docs, and validation commands.

Deliverables:

- `pyproject.toml`
- `README.md`
- `AGENTS.md`
- package folders
- placeholder CLI
- tests folder

Acceptance criteria:

- `pip install -e .[dev]` works.
- `wavesmith --help` works.
- `pytest` runs.
- `ruff check .` runs.

Validation commands:

```bash
pip install -e .[dev]
wavesmith --help
ruff check .
python -m pytest
```

Stop conditions:

- Python packaging cannot be made to work.
- CLI command cannot be installed.

---

### M1 — Single-file render skeleton

Goal:

Render a basic MP4 from an audio file using generated frames and ffmpeg muxing.

Deliverables:

- ffmpeg adapter
- frame writer
- render pipeline skeleton
- basic generated visual frame
- output MP4 with audio

Acceptance criteria:

- `wavesmith render input.wav output.mp4` creates a valid MP4.
- Output contains video and audio streams.
- Missing ffmpeg produces a clear error.
- Render supports `--max-seconds`.

Validation commands:

```bash
python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
wavesmith render .tmp/test.wav .tmp/test.mp4 --max-seconds 5 --resolution 640x360 --fps 15
ffprobe -v error -show_streams .tmp/test.mp4
python -m pytest
```

Stop conditions:

- ffmpeg cannot receive raw frames reliably.
- Audio muxing fails repeatedly.

---

### M2 — Audio analysis and timeline model

Goal:

Extract useful audio features and expose them through a timeline model.

Deliverables:

- audio analyzer
- feature model
- timeline lookup
- smoothing/interpolation utilities
- tests for feature normalization and time lookup

Acceptance criteria:

- Analyzer extracts duration, tempo, beats, RMS, bass/mid/treble energy.
- Features are normalized for visual use.
- Timeline lookup works for arbitrary frame times.
- Analysis failures are clear.

Validation commands:

```bash
wavesmith analyze .tmp/test.wav --out .tmp/test.analysis.json
python -m pytest tests/test_timeline_model.py tests/test_audio_cache.py
```

Stop conditions:

- librosa dependency cannot load audio in target WSL environment.
- Feature extraction is too slow for short files without a clear mitigation.

---

### M3 — First real preset: neon_orb

Goal:

Create the first visually engaging audio-reactive preset.

Deliverables:

- `neon_orb.yaml`
- center orb visual module
- spectrum ring visual module
- waveform ribbon visual module
- watermark module

Acceptance criteria:

- Bass energy changes center orb radius.
- Beats trigger visible pulse/shockwave effect.
- Spectrum ring responds to frequency energy.
- Waveform ribbon is visible.
- Watermark can be set or disabled.

Validation commands:

```bash
wavesmith validate-preset presets/neon_orb.yaml
wavesmith render .tmp/test.wav .tmp/neon.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5
python -m pytest
```

Manual validation:

- Open output video.
- Confirm visible motion and beat response.

Stop conditions:

- Render performance is unusable even at 640x360/15fps.

---

### M4 — Preset schema and additional presets

Goal:

Make presets first-class and add two more built-in styles.

Deliverables:

- preset schema
- preset loader
- preset validation command
- `spectrum_ring.yaml`
- `waveform_ribbon.yaml`

Acceptance criteria:

- Invalid presets fail before rendering.
- `wavesmith list-presets` lists built-ins.
- Three presets can render a short preview.

Validation commands:

```bash
wavesmith list-presets
wavesmith validate-preset presets/neon_orb.yaml
wavesmith validate-preset presets/spectrum_ring.yaml
wavesmith validate-preset presets/waveform_ribbon.yaml
for p in neon_orb spectrum_ring waveform_ribbon; do wavesmith render .tmp/test.wav .tmp/$p.mp4 --preset $p --resolution 640x360 --fps 15 --max-seconds 5; done
python -m pytest
```

Stop conditions:

- Preset schema becomes too complex for v1.

---

### M5 — Analysis cache and render logs

Goal:

Avoid repeated analysis and make render runs debuggable.

Deliverables:

- audio hash function
- analysis cache read/write
- `--force-analysis`
- per-render log file
- render summary output

Acceptance criteria:

- First render analyzes audio.
- Second render reuses cache.
- Forced analysis bypasses cache.
- Render log contains command/options/timestamps/errors.

Validation commands:

```bash
wavesmith render .tmp/test.wav .tmp/cache1.mp4 --preset neon_orb --max-seconds 5
wavesmith render .tmp/test.wav .tmp/cache2.mp4 --preset neon_orb --max-seconds 5
wavesmith render .tmp/test.wav .tmp/cache3.mp4 --preset neon_orb --max-seconds 5 --force-analysis
python -m pytest
```

Stop conditions:

- Cache invalidation cannot be made deterministic.

---

### M6 — Batch rendering and thumbnails

Goal:

Support rendering multiple files and creating thumbnails.

Deliverables:

- batch command
- batch summary
- optional thumbnail output
- failure policy

Acceptance criteria:

- Batch command processes a folder.
- Batch command writes outputs to target folder.
- Batch command reports successes/failures.
- Thumbnail generation works for at least one frame.

Validation commands:

```bash
mkdir -p .tmp/batch-in .tmp/batch-out
python scripts/generate_test_audio.py .tmp/batch-in/a.wav --seconds 5
python scripts/generate_test_audio.py .tmp/batch-in/b.wav --seconds 5
wavesmith batch .tmp/batch-in .tmp/batch-out --preset neon_orb --max-seconds 5 --resolution 640x360 --fps 15
python -m pytest
```

Stop conditions:

- Batch failure handling creates ambiguous or dangerous output behavior.

---

## 19. Risks

### R001 — Render performance may be slow

Impact: Medium  
Likelihood: Medium

Mitigation:

- Start with low-resolution smoke tests.
- Optimize only after correctness.
- Keep backend interface ready for GPU/shader backend.

### R002 — Audio analysis dependency issues in WSL

Impact: Medium  
Likelihood: Low/Medium

Mitigation:

- Document system dependencies.
- Add generated WAV test fixture.
- Keep analyzer isolated behind adapter.

### R003 — Preset schema may become too ambitious

Impact: Medium  
Likelihood: High

Mitigation:

- Keep v1 schema small.
- Hard-code only stable module types.
- Defer advanced mapping language.

### R004 — ffmpeg command complexity

Impact: Medium  
Likelihood: Medium

Mitigation:

- Centralize ffmpeg command construction.
- Unit-test command generation.
- Log exact ffmpeg command for every render.

### R005 — Scope creep into GUI/AI features

Impact: High  
Likelihood: High

Mitigation:

- Explicit non-goals.
- Milestone stop conditions.
- Future features documented but not implemented in v1.

### R006 — Copyright/licensing confusion

Impact: Medium  
Likelihood: Medium

Mitigation:

- Do not ship user audio.
- Document dependency licenses.
- Keep generated outputs user-owned unless project license says otherwise.

---

## 20. Security and Privacy Expectations

- No audio files are uploaded anywhere.
- No telemetry in v1.
- No network access required.
- No shell execution except controlled ffmpeg subprocess calls.
- User-provided paths must be handled safely.
- Logs must not include secrets.
- Generated files must be written only to user-specified or documented output folders.

---

## 21. `SPEC.yaml`

```yaml
project:
  name: WaveSmith
  version: 0.1.0
  description: Local-first audio-reactive video generator for music visualizers.
  target_user: Technical Windows/WSL user creating music videos from local audio files.

runtime:
  language: Python
  python_version: ">=3.11"
  platform:
    - WSL2
    - Linux
  system_dependencies:
    - ffmpeg

requirements:
  local_first: true
  cloud_required: false
  paid_api_required: false
  gui_required_v1: false
  input_formats_v1:
    - mp3
    - wav
  output_formats_v1:
    - mp4

commands:
  - name: render
    purpose: Render one audio file to one video file.
  - name: analyze
    purpose: Analyze audio and write feature cache JSON.
  - name: batch
    purpose: Render multiple files from a directory.
  - name: list-presets
    purpose: List available visual presets.
  - name: validate-preset
    purpose: Validate a preset file before rendering.

v1_presets:
  - neon_orb
  - spectrum_ring
  - waveform_ribbon

features_v1:
  - duration_seconds
  - sample_rate
  - tempo_bpm
  - beats
  - onsets
  - rms
  - bass_energy
  - mid_energy
  - treble_energy
  - spectrum
  - waveform_preview

non_goals_v1:
  - gui
  - web_app
  - live_preview
  - cloud_rendering
  - ai_video_generation
  - prompt_to_preset
  - real_time_audio_input

validation:
  required_commands:
    - ruff check .
    - python -m pytest
    - wavesmith --help
    - wavesmith list-presets
  smoke_render:
    input: .tmp/test-tone.wav
    output: .tmp/test-tone.mp4
    max_seconds: 5
    resolution: 640x360
    fps: 15
```

---

## 22. `AGENTS.md`

```markdown
# AGENTS.md — WaveSmith

## Mission

Build WaveSmith as a local-first Python CLI application that turns audio files into beat-reactive MP4 videos using configurable visual presets.

## Hard rules

- Do not add cloud dependencies.
- Do not add paid API dependencies.
- Do not build a GUI in v1.
- Do not commit generated videos, user audio, large caches, or render logs.
- Keep audio analysis, timeline modeling, visual rendering, preset loading, and ffmpeg encoding as separate modules.
- Keep visual style behavior configurable through presets where practical.
- Do not hardcode preset-specific behavior into the core render pipeline unless documented.
- Every milestone must include validation commands.
- Update `DOCUMENTATION.md` after each meaningful change.
- Log non-trivial implementation notes under `.logs/` when useful.

## Required reading order

1. `SPEC.yaml`
2. `PLAN.md`
3. `ARCHITECTURE.md`
4. `IMPLEMENT.md`
5. `DOCUMENTATION.md`

## Development style

- Make the smallest useful change for the current milestone.
- Prefer boring, testable code over clever rendering tricks.
- Keep external processes behind adapters.
- Keep CLI errors actionable.
- Prefer generated synthetic audio fixtures for tests.
- Use type hints for public functions where practical.

## Validation commands

Run at minimum:

```bash
ruff check .
python -m pytest
```

For render milestones, also run a short smoke render:

```bash
python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
wavesmith render .tmp/test.wav .tmp/test.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5
ffprobe -v error -show_streams .tmp/test.mp4
```

## Stop conditions

Stop and report if:

- ffmpeg cannot be used reliably.
- A dependency requires cloud or paid access.
- The current milestone requires GUI work.
- Generated output would need to be committed.
- Validation cannot be made to pass after focused repair.
- A core architecture boundary must be changed.
```

---

## 23. `PLAN.md`

```markdown
# PLAN.md — WaveSmith Milestone Plan

## M0 — Repository scaffold

Create package structure, CLI placeholder, docs, tests, and validation tooling.

Validation:

```bash
pip install -e .[dev]
wavesmith --help
ruff check .
python -m pytest
```

Done when the CLI can be invoked and tests run.

## M1 — Single-file render skeleton

Render generated frames through ffmpeg and mux with input audio.

Validation:

```bash
python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
wavesmith render .tmp/test.wav .tmp/test.mp4 --max-seconds 5 --resolution 640x360 --fps 15
ffprobe -v error -show_streams .tmp/test.mp4
python -m pytest
```

Done when output MP4 contains video and audio.

## M2 — Audio analysis and timeline

Extract audio features and expose frame-time lookup.

Validation:

```bash
wavesmith analyze .tmp/test.wav --out .tmp/test.analysis.json
python -m pytest
```

Done when features are normalized and timeline lookup is tested.

## M3 — First real preset: neon_orb

Implement center orb, spectrum ring, waveform ribbon, beat pulse, and watermark.

Validation:

```bash
wavesmith validate-preset presets/neon_orb.yaml
wavesmith render .tmp/test.wav .tmp/neon.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5
python -m pytest
```

Done when the output visibly reacts to audio.

## M4 — Preset schema and additional presets

Add schema validation and two additional built-in presets.

Validation:

```bash
wavesmith list-presets
wavesmith validate-preset presets/neon_orb.yaml
wavesmith validate-preset presets/spectrum_ring.yaml
wavesmith validate-preset presets/waveform_ribbon.yaml
python -m pytest
```

Done when three presets validate and render.

## M5 — Analysis cache and render logs

Add cache reuse, forced reanalysis, and render logs.

Validation:

```bash
wavesmith render .tmp/test.wav .tmp/cache1.mp4 --preset neon_orb --max-seconds 5
wavesmith render .tmp/test.wav .tmp/cache2.mp4 --preset neon_orb --max-seconds 5
wavesmith render .tmp/test.wav .tmp/cache3.mp4 --preset neon_orb --max-seconds 5 --force-analysis
python -m pytest
```

Done when cache reuse is observable and logs are written.

## M6 — Batch rendering and thumbnails

Add batch command and optional thumbnails.

Validation:

```bash
mkdir -p .tmp/batch-in .tmp/batch-out
python scripts/generate_test_audio.py .tmp/batch-in/a.wav --seconds 5
python scripts/generate_test_audio.py .tmp/batch-in/b.wav --seconds 5
wavesmith batch .tmp/batch-in .tmp/batch-out --preset neon_orb --max-seconds 5 --resolution 640x360 --fps 15
python -m pytest
```

Done when batch render produces expected outputs and summary.
```

---

## 24. `IMPLEMENT.md`

```markdown
# IMPLEMENT.md — WaveSmith Execution Runbook

## Standard execution loop

1. Read `AGENTS.md`, `SPEC.yaml`, `PLAN.md`, `ARCHITECTURE.md`, and `DOCUMENTATION.md`.
2. Identify the current milestone.
3. Make the smallest useful implementation change.
4. Add or update tests.
5. Run validation commands.
6. Fix failures.
7. Update `DOCUMENTATION.md` with what changed, commands run, and known issues.
8. Stop if a stop condition is reached.

## Environment setup

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
```

## Common validation

```bash
ruff check .
python -m pytest
wavesmith --help
wavesmith list-presets
```

## Render smoke test

```bash
python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
wavesmith render .tmp/test.wav .tmp/test.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5
ffprobe -v error -show_streams .tmp/test.mp4
```

## Documentation update format

After each milestone or significant change, append to `DOCUMENTATION.md`:

```markdown
## YYYY-MM-DD — Milestone/Change title

### Changed

- ...

### Validation run

```bash
...
```

### Result

- Passed/failed.
- Notes.

### Known issues

- ...
```

## Failure handling

If tests fail:

1. Read the failing assertion/error.
2. Fix the smallest relevant issue.
3. Re-run the failing test.
4. Re-run full validation.
5. Document the fix.

If ffmpeg fails:

1. Log the exact ffmpeg command.
2. Reproduce with a short generated test file.
3. Check whether failure is input, pipe, codec, or muxing.
4. Keep ffmpeg-specific logic inside `wavesmith/render/ffmpeg.py`.

If a dependency fails:

1. Confirm it is required for current milestone.
2. Prefer a simpler dependency if possible.
3. Do not add a cloud dependency to solve local dependency problems.
```

---

## 25. `ARCHITECTURE.md`

```markdown
# ARCHITECTURE.md — WaveSmith

## Overview

WaveSmith is a local-first CLI pipeline:

```text
audio file -> audio analysis -> timeline model -> preset-driven visuals -> frame stream -> ffmpeg -> MP4
```

## Boundaries

### CLI layer

Responsible for commands, options, and user-facing errors.

May call:

- audio analyzer
- preset loader
- render pipeline

Must not implement:

- rendering details
- ffmpeg command internals
- audio feature extraction internals

### Audio layer

Responsible for loading audio and extracting normalized features.

Must not know about visual presets.

### Timeline layer

Responsible for exposing per-time feature values to visuals.

Visual modules call the timeline instead of reading raw arrays.

### Preset layer

Responsible for loading, validating, and normalizing YAML preset config.

Invalid presets must fail before rendering.

### Render layer

Responsible for coordinating frames, progress, visual modules, and ffmpeg.

Must keep ffmpeg integration behind `render/ffmpeg.py`.

### Visual modules

Responsible for drawing frame elements based on feature values and preset config.

Visual modules should be composable.

## Backend policy

v1 uses CPU rendering. The render pipeline should still allow a future backend interface.

Potential future interface:

```python
class RenderBackend:
    def begin(self, options): ...
    def render_frame(self, frame_index, time_seconds, frame_context): ...
    def end(self): ...
```

Do not implement GPU backend in v1.

## File ownership

- `audio/*`: analysis and cache only.
- `timeline/*`: feature lookup only.
- `presets/*`: preset loading and validation only.
- `render/*`: render coordination and ffmpeg only.
- `visuals/*`: visual drawing primitives only.
- `utils/*`: shared helpers only.
```

---

## 26. `README.md`

```markdown
# WaveSmith

WaveSmith is a local-first Python CLI tool for turning audio files into beat-reactive music visualizer videos.

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

## Render a video

```bash
wavesmith render song.mp3 out.mp4 --preset neon_orb --resolution 1920x1080 --fps 30
```

## Quick preview

```bash
wavesmith render song.mp3 preview.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 20
```

## List presets

```bash
wavesmith list-presets
```

## Validate a preset

```bash
wavesmith validate-preset presets/neon_orb.yaml
```

## Batch render

```bash
wavesmith batch ./songs ./renders --preset spectrum_ring
```

## Development validation

```bash
ruff check .
python -m pytest
```

## Generated files

Rendered videos, user audio, logs, and large analysis caches should not be committed to Git.
```

---

## 27. `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.ruff_cache/
.mypy_cache/
*.egg-info/
dist/
build/

# Local config
.env

# Generated outputs
.renders/
.cache/
.tmp/
.logs/*.log
*.mp4
*.webm
*.mov
*.mkv

# User audio
*.mp3
*.wav
*.flac
*.m4a
*.ogg

# Keep docs/examples placeholders
!.logs/README.md
!examples/README.md
```

---

## 28. `.env.example`

```bash
# WaveSmith currently does not require secrets.
# This file exists for future local-only configuration.

WAVESMITH_CACHE_DIR=.cache/analysis
WAVESMITH_RENDER_DIR=.renders
WAVESMITH_DEFAULT_PRESET=neon_orb
WAVESMITH_DEFAULT_WATERMARK="Christian Kajsing // kajsing.com"
```

---

## 29. First Concrete Codex Task

```markdown
You are implementing WaveSmith M0.

Read:

- AGENTS.md
- SPEC.yaml
- PLAN.md
- ARCHITECTURE.md
- IMPLEMENT.md
- DOCUMENTATION.md

Implement only M0.

Tasks:

1. Create Python package structure under `wavesmith/`.
2. Add `pyproject.toml` with runtime and dev dependencies.
3. Add a Typer-based CLI with commands:
   - `wavesmith --help`
   - `wavesmith list-presets`
   - placeholder `render`
   - placeholder `analyze`
   - placeholder `batch`
   - placeholder `validate-preset`
4. Add empty built-in preset files or minimal valid placeholders for:
   - `neon_orb`
   - `spectrum_ring`
   - `waveform_ribbon`
5. Add initial tests proving the CLI imports and help command works.
6. Add `.gitignore`, `.env.example`, and README setup commands.
7. Run validation:

```bash
pip install -e .[dev]
wavesmith --help
wavesmith list-presets
ruff check .
python -m pytest
```

8. Update `DOCUMENTATION.md` with:
   - files created
   - commands run
   - validation result
   - known issues

Stop if:

- packaging fails in a way that cannot be quickly repaired
- CLI entrypoint cannot be installed
- a dependency requires cloud/paid access

Do not implement rendering yet.
```

---

## 30. Future Design Notes

### Prompt-to-preset

Future feature:

```bash
wavesmith make-preset "dark cyberpunk bass visualizer with foxfire particles and violet shockwaves" --out presets/cyber_foxfire.yaml
```

This should generate preset YAML, not arbitrary Python code.

### Lyrics/subtitles

Future feature:

```bash
wavesmith render song.mp3 out.mp4 --lyrics song.lrc --preset lyric_orb
```

Must support at least:

- `.srt`
- `.lrc`

Whisper transcription should be optional and local-only unless explicitly changed.

### GPU backend

Future feature:

- Add renderer backend interface.
- Implement ModernGL or shader backend.
- Keep CPU backend as fallback.

Do not begin this until CPU renderer is stable.

---

## 31. Definition of Done for v1

WaveSmith v1 is done when:

- The project installs in WSL.
- `wavesmith render` can produce MP4 from MP3/WAV.
- Output video includes original audio.
- Three presets render successfully.
- `--resolution`, `--fps`, `--max-seconds`, `--preset`, and `--watermark` work.
- Audio analysis cache works.
- Render logs are written.
- `ruff check .` passes.
- `python -m pytest` passes.
- A documented smoke render passes.
- README contains working setup and usage commands.
- Generated outputs are ignored by Git.

---

## 32. Recommended Next User Decisions

Before implementation begins, decide:

1. Final project name.
2. License.
3. Default watermark text.
4. Whether the default public-facing credit should mention WaveSmith.
5. Whether v1 must include batch rendering or if that can be v1.1.
6. Whether preset names should lean technical, musical, or mythic.

Recommended defaults:

```yaml
project_name: WaveSmith
license: MIT
watermark: "Christian Kajsing // kajsing.com"
default_credit_mentions_tool: false
batch_rendering: v1.1
preset_style: mythic + technical
```

---

## 33. Suggested Initial Presets

### `neon_orb`

A central bass-reactive orb, circular spectrum ring, beat shockwaves, waveform ribbon, and floating particles.

Mood:

- clean
- neon
- cyber
- general-purpose

### `spectrum_ring`

A symmetrical circular spectrum visualizer with strong frequency motion and minimal background clutter.

Mood:

- technical
- sharp
- classic visualizer

### `waveform_ribbon`

Flowing horizontal or diagonal waveform ribbons with smooth glow and slower cinematic motion.

Mood:

- elegant
- ambient
- good for vocals or slower songs

Future mythic preset:

### `foxfire_shrine`

A darker, more atmospheric visualizer with shrine-like symmetry, ember particles, moonlit palette, and foxfire beat pulses.

Do not include in v1 unless the first three presets are done.

