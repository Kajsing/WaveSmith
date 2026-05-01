# AGENTS.md - WaveSmith

## Mission

Build WaveSmith as a local-first Python CLI application that turns audio files into
beat-reactive MP4 videos using configurable visual presets.

## Hard Rules

- Do not add cloud dependencies.
- Do not add paid API dependencies.
- Do not build a GUI in v1.
- Do not commit generated videos, user audio, large caches, or render logs.
- Keep audio analysis, timeline modeling, visual rendering, preset loading, and ffmpeg
  encoding as separate modules.
- Keep visual style behavior configurable through presets where practical.
- Do not hardcode preset-specific behavior into the core render pipeline unless documented.
- Every milestone must include validation commands.
- Update `DOCUMENTATION.md` after each meaningful change.
- Log non-trivial implementation notes under `.logs/` when useful.

## Required Reading Order

1. `SPEC.yaml`
2. `PLAN.md`
3. `ARCHITECTURE.md`
4. `IMPLEMENT.md`
5. `DOCUMENTATION.md`

## Development Style

- Make the smallest useful change for the current milestone.
- Prefer boring, testable code over clever rendering tricks.
- Keep external processes behind adapters.
- Keep CLI errors actionable.
- Prefer generated synthetic audio fixtures for tests.
- Use type hints for public functions where practical.

## Validation Commands

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

## Stop Conditions

Stop and report if:

- ffmpeg cannot be used reliably.
- A dependency requires cloud or paid access.
- The current milestone requires GUI work.
- Generated output would need to be committed.
- Validation cannot be made to pass after focused repair.
- A core architecture boundary must be changed.
