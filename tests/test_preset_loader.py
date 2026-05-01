import pytest

from wavesmith.presets.loader import PresetError, list_builtin_presets, load_preset


def test_builtin_presets_are_available() -> None:
    assert list_builtin_presets() == ["neon_orb", "spectrum_ring", "waveform_ribbon"]


def test_load_builtin_preset_by_name() -> None:
    preset = load_preset("neon_orb")

    assert preset.name == "neon_orb"
    assert preset.modules[0].type == "center_orb"
    assert preset.palette.base == (180, 80, 255)


@pytest.mark.parametrize("name", ["neon_orb", "spectrum_ring", "waveform_ribbon"])
def test_all_builtin_presets_validate(name: str) -> None:
    preset = load_preset(name)

    assert preset.name == name
    assert preset.description
    assert preset.modules


def test_invalid_module_type_fails_before_render(tmp_path) -> None:
    preset_file = tmp_path / "bad.yaml"
    preset_file.write_text(
        """
name: bad
version: 1
description: Bad preset.
canvas:
  background: black
palette:
  base: [1, 2, 3]
  accent: [4, 5, 6]
  beat: [7, 8, 9]
modules:
  - type: unsupported
    id: nope
""",
        encoding="utf-8",
    )

    with pytest.raises(PresetError):
        load_preset(preset_file)


def test_duplicate_module_ids_fail_before_render(tmp_path) -> None:
    preset_file = tmp_path / "bad.yaml"
    preset_file.write_text(
        """
name: bad
version: 1
description: Bad preset.
canvas:
  background: black
palette:
  base: [1, 2, 3]
  accent: [4, 5, 6]
  beat: [7, 8, 9]
modules:
  - type: center_orb
    id: duplicate
  - type: spectrum_ring
    id: duplicate
""",
        encoding="utf-8",
    )

    with pytest.raises(PresetError, match="unique"):
        load_preset(preset_file)
