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

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
```

## Common Validation

```bash
ruff check .
python -m pytest
wavesmith --help
wavesmith list-presets
```

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
