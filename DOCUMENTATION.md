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
