# IMPLEMENT.md - WaveSmith Execution Runbook

## Standard Execution Loop

1. Read `AGENTS.md`, `SPEC.yaml`, `PLAN.md`, `ARCHITECTURE.md`, and `DOCUMENTATION.md`.
2. Identify the current milestone.
3. Make the smallest useful implementation change.
4. Add or update tests.
5. Run validation commands.
6. Fix failures.
7. Update `DOCUMENTATION.md` with what changed, commands run, and known issues.
8. Stop if a stop condition is reached.

## Environment Setup

Preferred when system Python 3.11+ is available:

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
```

If WSL only has Python 3.10 and sudo is unavailable, use local `uv` Python instead:

```bash
python3 -m pip install --user uv
~/.local/bin/uv python install 3.11
~/.local/bin/uv venv --clear --python 3.11 .venv
~/.local/bin/uv pip install --python .venv/bin/python -e '.[dev]'
```

## Common Validation

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/wavesmith --help
.venv/bin/wavesmith list-presets
```

## GitHub Push From WSL

Prefer SSH for pushes from WSL:

```bash
git push git@github.com:Kajsing/WaveSmith.git Main
```

The HTTPS remote may prompt for credentials and block non-interactive Codex runs.

## Render Smoke Test

```bash
python scripts/generate_test_audio.py .tmp/test.wav --seconds 5
wavesmith render .tmp/test.wav .tmp/test.mp4 --preset neon_orb --resolution 640x360 --fps 15 --max-seconds 5
ffprobe -v error -show_streams .tmp/test.mp4
```

## Documentation Update Format

After each milestone or significant change, append to `DOCUMENTATION.md`:

```markdown
## YYYY-MM-DD - Milestone/Change title

### Changed

- ...

### Validation Run

Commands run and results.

### Known Issues

- ...
```

## Failure Handling

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
