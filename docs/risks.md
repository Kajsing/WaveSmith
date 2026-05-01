# Risks

## R001 - Render Performance May Be Slow

Mitigation: start with low-resolution smoke tests, optimize only after correctness, and keep a
future backend boundary open.

## R002 - Audio Analysis Dependency Issues In WSL

Mitigation: document system dependencies and keep audio analysis isolated behind an adapter.

## R003 - Preset Schema May Become Too Ambitious

Mitigation: keep the v1 schema small and defer advanced mapping language.

## R004 - ffmpeg Command Complexity

Mitigation: centralize ffmpeg command construction and unit-test command generation.

## R005 - Scope Creep Into GUI/AI Features

Mitigation: keep v1 non-goals visible in the spec and milestone plan.

## R006 - Copyright/Licensing Confusion

Mitigation: do not ship user audio and document dependency licenses.
