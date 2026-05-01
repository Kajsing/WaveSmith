from wavesmith.presets.loader import list_builtin_presets, load_preset


def test_builtin_presets_are_available() -> None:
    assert list_builtin_presets() == ["neon_orb", "spectrum_ring", "waveform_ribbon"]


def test_load_builtin_preset_by_name() -> None:
    preset = load_preset("neon_orb")

    assert preset.name == "neon_orb"
    assert preset.modules[0].type == "center_orb"
