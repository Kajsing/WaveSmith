from wavesmith.presets.generator import generate_preset_dict
from wavesmith.presets.schema import PresetConfig


def test_generate_preset_dict_returns_valid_schema() -> None:
    preset = generate_preset_dict("dark cyberpunk vortex sparks", name="Dark Cyber")

    validated = PresetConfig.model_validate(preset)

    assert validated.name == "dark_cyber"
    assert validated.modules[0].type == "shader_field"
    assert validated.palette.base == (62, 255, 188)
