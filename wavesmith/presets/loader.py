"""Preset loading helpers."""

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from wavesmith.presets.schema import PresetConfig

BUILTIN_PRESET_DIR = Path(__file__).resolve().parents[2] / "presets"


class PresetError(ValueError):
    """Raised when a preset cannot be loaded or validated."""


@dataclass(frozen=True)
class PresetSummary:
    """Compact metadata for browsing presets."""

    name: str
    description: str
    modules: tuple[str, ...]
    path: Path


def list_builtin_presets() -> list[str]:
    """Return built-in preset names in deterministic order."""
    if not BUILTIN_PRESET_DIR.exists():
        return []
    return sorted(path.stem for path in BUILTIN_PRESET_DIR.glob("*.yaml"))


def list_builtin_preset_summaries() -> list[PresetSummary]:
    """Return validated built-in preset summaries for CLI browsing."""
    summaries: list[PresetSummary] = []
    for name in list_builtin_presets():
        path = resolve_preset_path(name)
        preset = load_preset(path)
        summaries.append(
            PresetSummary(
                name=preset.name,
                description=preset.description,
                modules=tuple(module.type for module in preset.modules),
                path=path,
            )
        )
    return summaries


def resolve_preset_path(name_or_path: str | Path) -> Path:
    """Resolve a built-in preset name or explicit YAML path."""
    candidate = Path(name_or_path)
    if candidate.exists():
        return candidate

    if candidate.suffix:
        raise PresetError(f"Preset file was not found: {candidate}")

    builtin = BUILTIN_PRESET_DIR / f"{candidate.name}.yaml"
    if builtin.exists():
        return builtin

    available = ", ".join(list_builtin_presets()) or "none"
    raise PresetError(
        f"Preset '{candidate.name}' was not found. Available built-ins: {available}."
    )


def load_preset(name_or_path: str | Path) -> PresetConfig:
    """Load and validate a preset."""
    path = resolve_preset_path(name_or_path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PresetError(f"Could not read preset file: {path}") from exc
    except yaml.YAMLError as exc:
        raise PresetError(f"Preset YAML is invalid: {path}") from exc

    if not isinstance(data, dict):
        raise PresetError(f"Preset must be a YAML mapping: {path}")

    try:
        return PresetConfig.model_validate(data)
    except ValidationError as exc:
        raise PresetError(str(exc)) from exc
