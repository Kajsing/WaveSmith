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

Result: blocked because the current WSL `python3` is Python 3.10.12, while WaveSmith
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

### Known Issues

- Rendering, audio analysis, batch processing, and ffmpeg integration are placeholders until later
  milestones.
- The local WSL environment needs Python 3.11+ installed before the normal
  `pip install -e .[dev]` command can pass without the temporary validation workaround.
