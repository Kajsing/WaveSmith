# Project Format

WaveSmith stores source code, preset definitions, tests, documentation, and local generated output
in separate areas:

- `wavesmith/`: Python package.
- `presets/`: built-in YAML presets.
- `assets/`: curated textures, backdrops, and reference frames that should be versioned.
- `tests/`: unit tests and CLI smoke tests.
- `docs/`: longer-form project documentation.
- `.renders/`: generated videos, thumbnails, and render logs.
- `.cache/analysis/`: generated audio analysis cache.
- `.tmp/`: local validation output.
- `.tmp/art/`: generated image experiments and loose visual references.

Generated output folders are ignored by Git.
