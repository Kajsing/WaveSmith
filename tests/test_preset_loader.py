import pytest

from wavesmith.presets.loader import PresetError, list_builtin_presets, load_preset


def test_builtin_presets_are_available() -> None:
    assert list_builtin_presets() == [
        "elemental_storm",
        "fire_dual_lines",
        "fire_natural_v2",
        "ice_cracked_shards",
        "inferno_portal",
        "neon_orb",
        "shader_bloom",
        "spectrum_ring",
        "waveform_ribbon",
    ]


def test_load_builtin_preset_by_name() -> None:
    preset = load_preset("neon_orb")

    assert preset.name == "neon_orb"
    assert preset.modules[0].type == "center_orb"
    assert preset.palette.base == (180, 80, 255)


@pytest.mark.parametrize(
    "name",
    [
        "elemental_storm",
        "fire_dual_lines",
        "fire_natural_v2",
        "ice_cracked_shards",
        "inferno_portal",
        "neon_orb",
        "shader_bloom",
        "spectrum_ring",
        "waveform_ribbon",
    ],
)
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


def test_shader_field_module_is_valid() -> None:
    preset = load_preset("shader_bloom")

    assert preset.modules[0].type == "shader_field"
    assert preset.modules[0].model_extra["style"] == "aurora"


def test_elemental_field_module_is_valid() -> None:
    preset = load_preset("elemental_storm")

    assert preset.modules[0].type == "elemental_field"
    assert preset.modules[0].model_extra["element"] == "water"


def test_cinematic_modules_are_valid() -> None:
    preset = load_preset("inferno_portal")

    module_types = {module.type for module in preset.modules}
    assert "portal_ring" in module_types
    assert "spectrum_wall" in module_types


def test_image_backdrop_module_type_is_valid(tmp_path) -> None:
    preset_file = tmp_path / "image.yaml"
    preset_file.write_text(
        """
name: image
version: 1
description: Image backdrop preset.
canvas:
  background: black
palette:
  base: [1, 2, 3]
  accent: [4, 5, 6]
  beat: [7, 8, 9]
modules:
  - type: image_backdrop
    id: image
    path: /tmp/example.png
""",
        encoding="utf-8",
    )

    preset = load_preset(preset_file)

    assert preset.modules[0].type == "image_backdrop"
