# DOCUMENTATION.md - WaveSmith

This file records implementation notes, validation commands, and known issues as the project
evolves.

## 2026-05-01 - M0 Repository Scaffold

### Changed

- Created the initial Python project structure.
- Added package metadata, dependency declarations, and the `wavesmith` console script.
- Added Typer CLI placeholders for the planned v1 commands.
- Added minimal built-in preset YAML files.
- Added project specification, architecture, milestone plan, runbook, and README.
- Added initial tests for CLI startup, preset listing, and preset validation.
- Moved the original handoff package into `archive/`.

### Validation Run

Attempted the intended setup command first:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
```

Result: blocked because the system WSL `python3` is Python 3.10.12, while WaveSmith
correctly requires Python 3.11+.

Ran scaffold validation with the available Python 3.10 interpreter by installing only the M0
CLI/test dependencies and installing WaveSmith without runtime dependencies:

```bash
pip install typer rich pyyaml pydantic pytest ruff hatchling
pip install -e . --no-deps --ignore-requires-python
wavesmith --help
wavesmith list-presets
wavesmith validate-preset presets/neon_orb.yaml
ruff check .
python -m pytest
```

Result: passed.

- `wavesmith list-presets` showed `neon_orb`, `spectrum_ring`, and `waveform_ribbon`.
- `wavesmith validate-preset presets/neon_orb.yaml` passed.
- `ruff check .` passed.
- `python -m pytest` passed with 5 tests.

Installed a local user-managed Python 3.11.15 with `uv` because `sudo apt-get install` requires a
password in this WSL environment:

```bash
python3 -m pip install --user uv
~/.local/bin/uv python install 3.11
~/.local/bin/uv venv --clear --python 3.11 .venv
~/.local/bin/uv pip install --python .venv/bin/python -e '.[dev]'
.venv/bin/wavesmith --help
.venv/bin/wavesmith list-presets
.venv/bin/wavesmith validate-preset presets/neon_orb.yaml
.venv/bin/ruff check .
.venv/bin/python -m pytest
```

Result: passed with Python 3.11.15 and full project dependencies.

### Known Issues

- Rendering, audio analysis, batch processing, and ffmpeg integration are placeholders until later
  milestones.
- The system `python3` is still Python 3.10.12. Use the project `.venv` created with local
  `uv`/Python 3.11.15, or install Python 3.11+ system-wide later.
- GitHub push from WSL should use SSH, for example
  `git@github.com:Kajsing/WaveSmith.git`, because the current HTTPS remote prompts for
  credentials in a way Codex cannot answer non-interactively.

## 2026-05-01 - M1 Single-File Render Skeleton

### Changed

- Replaced the `render` placeholder with a working single-file MP4 render path.
- Added render option validation for input file, output extension, FPS, duration limit, and
  even-numbered MP4 resolutions.
- Added ffprobe duration probing and ffmpeg raw RGB frame streaming.
- Added deterministic placeholder frame generation with simple visual motion and watermark text.
- Added `scripts/generate_test_audio.py` for local WAV smoke-test fixtures.
- Added tests for ffmpeg command construction, render option validation, and placeholder frame
  generation.

### Validation Run

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
.venv/bin/wavesmith render .tmp/test.wav .tmp/test.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5
ffprobe -v error -show_streams .tmp/test.mp4
```

### Result

- Passed.
- Unit test suite: 13 tests passed.
- Smoke render produced `.tmp/test.mp4`.
- ffprobe confirmed one H.264 video stream and one AAC audio stream, both 5 seconds long.

### Known Issues

- Frames are deterministic placeholder visuals, not audio-reactive yet.
- Audio is re-encoded to AAC for MP4 compatibility. A future milestone should decide whether
  "original audio" means preserving the exact codec/stream where possible or including the same
  source audio content in an MP4-compatible form.
- Render logs and analysis cache remain future milestones.

## 2026-05-01 - M1 Hardening

### Changed

- Added CLI validation tests for missing input files, invalid output extension, and invalid
  resolution.
- Added ffmpeg/ffprobe failure tests for missing binaries and invalid audio probing.
- Added `verify_media_streams` to programmatically check whether smoke outputs contain video and
  audio streams.
- Added an optional smoke-output sanity test for `.tmp/test.mp4` when that local file exists.

### Validation Run

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
.venv/bin/wavesmith render .tmp/test.wav .tmp/test.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5
.venv/bin/python -m pytest tests/test_smoke_helpers.py
```

### Result

- Passed.
- Unit test suite: 20 tests passed.
- Smoke render succeeded.
- Smoke-output sanity test confirmed `.tmp/test.mp4` has a non-zero file size plus video and audio
  streams.

## 2026-05-01 - M2 Audio Analysis And Timeline

### Changed

- Added `AudioAnalysis` and `TimeSeries` JSON models for normalized audio features.
- Implemented `wavesmith analyze` for MP3/WAV files.
- Added librosa-based extraction for duration, sample rate, tempo, beats, onsets, RMS, bass/mid/treble
  energy, spectrum, and waveform preview.
- Added stable JSON read/write helpers for analysis payloads.
- Added `Timeline.at(time_seconds)` for scalar and vector feature interpolation.
- Added tests for analysis output, JSON roundtrip, CLI analyze, and timeline lookup.

### Validation Run

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
.venv/bin/wavesmith analyze .tmp/test.wav --out .tmp/test.analysis.json
```

### Result

- Passed.
- Unit test suite: 27 tests passed.
- `wavesmith analyze` wrote `.tmp/test.analysis.json`.
- Analysis JSON included all required M2 feature keys.
- Test analysis contained 216 RMS samples and 32 spectrum bins.

### Known Issues

- Analysis cache reuse is still future M5 work.
- Render output does not consume analysis/timeline data yet; M3 will connect visuals to features.
- Beat detection on very short synthetic fixtures may produce sparse or empty beat lists, which is
  acceptable for M2.

## 2026-05-01 - M2 Analysis Size Policy

### Changed

- Added a serialized feature-rate limit to audio analysis.
- `wavesmith analyze` now exposes `--feature-fps`, defaulting to 20.
- Analyzer internals still use librosa's normal hop resolution, then downsample serialized
  time-series features before writing JSON.
- Downsampling preserves shared time axes across RMS, band energy, spectrum, and waveform preview.
- Added tests for default feature-rate limiting, custom `--feature-fps`, and invalid feature rates.

### Validation Run

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
.venv/bin/wavesmith analyze .tmp/test.wav --out .tmp/test.analysis.json --feature-fps 10
```

### Result

- Passed.
- Unit test suite: 31 tests passed.
- A 5 second analysis with `--feature-fps 10` produced 51 RMS/spectrum samples and 32 spectrum bins.

### Known Issues

- This controls serialized JSON size, not M5 cache retention or eviction policy.
- M3 visuals should use timeline interpolation instead of assuming feature samples match render FPS.

## 2026-05-01 - M3 First Audio-Reactive Preset

### Changed

- Connected `wavesmith render` to the M2 analyzer and `Timeline`.
- Added audio-reactive `neon_orb` frame generation driven by per-frame timeline features.
- Implemented visual modules for:
  - reactive background
  - bass/RMS center orb
  - circular spectrum ring
  - waveform ribbon
  - beat shock ring
  - watermark text
- Kept ffmpeg muxing and render orchestration inside the render layer.
- Added tests proving reactive frames change when timeline features change.
- Hardened orb drawing for very small smoke-test resolutions.

### Validation Run

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
.venv/bin/wavesmith render .tmp/test.wav .tmp/neon.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5 --watermark "Christian Kajsing // kajsing.com"
ffprobe -v error -show_streams .tmp/neon.mp4
```

### Result

- Passed.
- Unit test suite: 32 tests passed.
- Smoke render produced `.tmp/neon.mp4`.
- ffprobe confirmed one 640x360 H.264 video stream with 75 frames and one 5 second AAC audio
  stream.
- A preview frame was extracted from the smoke render for visual sanity checking.

### Known Issues And Improvement Notes

- Preset YAML is validated but not yet used to configure module parameters. M4 should make preset
  modules first-class instead of relying on hardcoded `neon_orb` drawing defaults.
- Render currently analyzes audio every time. M5 should add cache reuse before full-length renders
  become routine.
- Beat/onset response is intentionally simple. M3 visuals should be reviewed with a real music file
  before tuning pulse widths, spectrum scale, and ribbon motion.
- The CPU/Pillow renderer is fine for smoke tests, but performance should be measured before larger
  resolutions or full songs.

## 2026-05-01 - M4 Preset Schema And Additional Presets

### Changed

- Tightened preset schema validation with typed canvas, palette, watermark, and module models.
- Restricted module types to implemented v1 primitives.
- Added validation for RGB palette triples and unique module IDs.
- Made render module order YAML-driven instead of drawing every visual unconditionally.
- Made preset palette and default watermark settings affect rendered output.
- Implemented the previously declared `particles` visual module so `spectrum_ring` has no dead
  preset entries.
- Added tests for all built-in presets, invalid module types, duplicate module IDs, and preset-driven
  frame generation.

### Validation Run

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python scripts/generate_test_audio.py .tmp/test.wav --seconds 3
.venv/bin/wavesmith validate-preset presets/neon_orb.yaml
.venv/bin/wavesmith validate-preset presets/spectrum_ring.yaml
.venv/bin/wavesmith validate-preset presets/waveform_ribbon.yaml
.venv/bin/wavesmith render .tmp/test.wav .tmp/neon_orb.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 3 --watermark ""
.venv/bin/wavesmith render .tmp/test.wav .tmp/spectrum_ring.mp4 --preset spectrum_ring --resolution 640x360 --fps 15 --max-seconds 3 --watermark ""
.venv/bin/wavesmith render .tmp/test.wav .tmp/waveform_ribbon.mp4 --preset waveform_ribbon --resolution 640x360 --fps 15 --max-seconds 3 --watermark ""
```

### Result

- Passed.
- All three built-in presets validated.
- All three built-in presets rendered 640x360 MP4 smoke outputs with 45 video frames.

### Improvement Notes

- Preset files now drive module selection, but module configuration is still intentionally small.
  Future work can make more style knobs explicit without adding arbitrary preset scripting.
- The current renderer supports all declared module types, which is safer than allowing presets to
  declare visuals the renderer silently ignores.

## 2026-05-01 - M5 Analysis Cache And Render Logs

### Changed

- Added deterministic analysis cache keys based on audio bytes plus analysis parameters.
- Added `.cache/analysis/*.analysis.json` cache read/write support.
- `wavesmith render` now reuses analysis cache by default.
- `--force-analysis` bypasses an existing cache entry and rewrites it.
- Added per-render logs under `.renders/logs/`.
- Render logs include status, input/output, preset, duration, resolution, FPS, cache status, cache
  path, and ffmpeg command.
- CLI render summary now reports analysis cache status and render log path.
- Added tests for cache keys, cache hits, forced rebuilds, render log content, and log path
  uniqueness.

### Validation Run

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
rm -rf .cache/analysis .renders/logs
.venv/bin/wavesmith render .tmp/test.wav .tmp/cache1.mp4 --preset neon_orb --max-seconds 3 --resolution 640x360 --fps 15
.venv/bin/wavesmith render .tmp/test.wav .tmp/cache2.mp4 --preset neon_orb --max-seconds 3 --resolution 640x360 --fps 15
.venv/bin/wavesmith render .tmp/test.wav .tmp/cache3.mp4 --preset neon_orb --max-seconds 3 --resolution 640x360 --fps 15 --force-analysis
find .renders/logs -maxdepth 1 -type f | wc -l
```

### Result

- Passed.
- Unit test suite: 44 tests passed.
- Render 1 reported `analysis_cache=miss`.
- Render 2 reported `analysis_cache=hit`.
- Render 3 reported `analysis_cache=forced`.
- Three render log files were written.

### Improvement Notes

- Initial M5 validation exposed a log filename collision when two renders finished in the same
  second. Log filenames now include microseconds.
- Cache invalidation is content-based and parameter-based, but M5 does not yet include a cache
  pruning policy.
- Logs are plain text for easy debugging; structured JSON logs could be useful later if batch
  rendering needs machine-readable summaries.

## 2026-05-01 - Post-M5 Polish

### Changed

- Compacted long cache paths in CLI render output so terminal summaries stay readable.
- Added a unit test for cache path display formatting.
- Suppressed known upstream `audioread` Python 3.13 deprecation warnings in pytest output.

### Validation Run

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/wavesmith render .tmp/test.wav .tmp/cli-output-check.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 2 --watermark ""
```

### Result

- Passed.
- Unit test suite: 45 tests passed.
- Render CLI output now shows compact cache/log paths.

## 2026-05-01 - M6 Batch Rendering And Thumbnails

### Changed

- Implemented local thumbnail extraction from rendered MP4 files via ffmpeg.
- Added single-render thumbnail options:
  - `--thumbnail`
  - `--thumbnail-at`, accepting seconds or percentages like `10s` or `50%`
- Implemented `wavesmith batch INPUT_DIR OUTPUT_DIR`.
- Batch render processes `.mp3` and `.wav` files in deterministic filename order.
- Batch render writes one MP4 per source file.
- Batch render writes JPG thumbnails under `OUTPUT_DIR/thumbnails/` by default.
- Batch render writes `OUTPUT_DIR/batch-summary.json`.
- Added `--no-thumbnails` and `--stop-on-error`.
- Added tests for thumbnail time parsing, local ffmpeg thumbnail extraction, audio discovery, batch
  summaries, thumbnail paths, and stop-on-error behavior.

### Validation Run

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python scripts/generate_test_audio.py .tmp/test.wav --seconds 3
.venv/bin/wavesmith render .tmp/test.wav .tmp/thumb-test.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 3 --watermark "" --thumbnail --thumbnail-at 50%
test -s .renders/thumbnails/thumb-test.jpg
mkdir -p .tmp/m6-batch-in
.venv/bin/python scripts/generate_test_audio.py .tmp/m6-batch-in/a.wav --seconds 3
.venv/bin/python scripts/generate_test_audio.py .tmp/m6-batch-in/b.wav --seconds 3 --frequency 660
.venv/bin/wavesmith batch .tmp/m6-batch-in .tmp/m6-batch-out --preset spectrum_ring --resolution 640x360 --fps 15 --max-seconds 3
test -s .tmp/m6-batch-out/a.mp4
test -s .tmp/m6-batch-out/b.mp4
test -s .tmp/m6-batch-out/thumbnails/a.jpg
test -s .tmp/m6-batch-out/thumbnails/b.jpg
test -s .tmp/m6-batch-out/batch-summary.json
```

### Result

- Passed.
- Unit test suite: 52 tests passed.
- Single render thumbnail extraction succeeded.
- Batch render completed with 2 successes and 0 failures.
- Batch summary recorded output videos, thumbnails, cache status, and render log paths.

### Improvement Notes

- Thumbnail generation is intentionally local-only and based on ffmpeg frame extraction from the
  finished MP4.
- Future thumbnail work can add poster-frame design, multiple candidate frames, or feature-based
  thumbnail selection without changing the local-first rule.
- Batch summary is JSON, which gives us a better foundation for future progress reporting and
  resumable batches.

## 2026-05-01 - Future GPU Render Note

### Changed

- Added a future GPU/shader backend note to `PLAN.md`.
- Clarified the CPU-renderer decision: CPU remains the reference implementation and fallback, while
  GPU rendering should arrive later behind a backend interface.

### Notes

- GPU rendering is not part of the current MVP.
- Recommended future sequence: backend interface, CPU backend wrapper, GPU backend prototype, then
  quality/performance comparison.
