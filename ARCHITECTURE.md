# ARCHITECTURE.md - WaveSmith

## Overview

WaveSmith is a local-first CLI pipeline:

```text
audio file -> audio analysis -> timeline model -> preset-driven visuals -> frame stream -> ffmpeg -> MP4
```

## Boundaries

### CLI Layer

Responsible for commands, options, and user-facing errors.

May call:

- audio analyzer
- preset loader
- render pipeline

Must not implement:

- rendering details
- ffmpeg command internals
- audio feature extraction internals

### Audio Layer

Responsible for loading audio and extracting normalized features. It must not know about visual
presets.

### Timeline Layer

Responsible for exposing per-time feature values to visuals. Visual modules call the timeline
instead of reading raw arrays.

### Preset Layer

Responsible for loading, validating, and normalizing YAML preset config. Invalid presets must fail
before rendering.

### Render Layer

Responsible for coordinating frames, progress, visual modules, and ffmpeg. ffmpeg integration stays
behind `render/ffmpeg.py`.

### Visual Modules

Responsible for drawing frame elements based on feature values and preset config.

## Backend Policy

v1 uses CPU rendering. The render pipeline should still allow a future backend interface.

Potential future interface:

```python
class RenderBackend:
    def begin(self, options): ...
    def render_frame(self, frame_index, time_seconds, frame_context): ...
    def end(self): ...
```

Do not implement a GPU backend in v1.

## File Ownership

- `audio/*`: analysis and cache only.
- `timeline/*`: feature lookup only.
- `presets/*`: preset loading and validation only.
- `render/*`: render coordination and ffmpeg only.
- `visuals/*`: visual drawing primitives only.
- `utils/*`: shared helpers only.
