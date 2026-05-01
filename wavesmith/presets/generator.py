"""Deterministic prompt-to-preset generation."""

from wavesmith.presets.schema import PresetConfig


def generate_preset_dict(prompt: str, *, name: str = "custom_prompt") -> dict[str, object]:
    """Generate a schema-bound preset dictionary from a short style prompt."""
    normalized = prompt.lower()
    palette = _palette(normalized)
    if any(word in normalized for word in ["vortex", "spiral", "tunnel"]):
        shader_style = "vortex"
    else:
        shader_style = "aurora"
    if any(word in normalized for word in ["spark", "stars", "particles"]):
        particle_count = 260
    else:
        particle_count = 160
    preset = {
        "name": _safe_name(name),
        "version": 1,
        "description": f"Generated local preset from prompt: {prompt}",
        "canvas": {"background": "radial_void", "glow": True},
        "palette": palette,
        "watermark": {
            "enabled": True,
            "text": "Christian Kajsing // kajsing.com",
            "position": "bottom_right",
            "opacity": 0.5,
        },
        "modules": [
            {
                "type": "shader_field",
                "id": "prompt_field",
                "style": shader_style,
                "layers": 5,
                "density": 46,
                "blur": 8,
                "opacity": 0.62,
                "intensity_feature": "rms",
                "bass_feature": "bass_energy",
                "distortion_feature": "treble_energy",
            },
            {
                "type": "spectrum_ring",
                "id": "prompt_ring",
                "radius": {"base": 215, "feature": "rms", "scale": 55},
                "bars": {"count": 180, "height_feature": "spectrum", "scale": 175},
                "rotation_speed": 0.16,
            },
            {
                "type": "center_orb",
                "id": "prompt_orb",
                "radius": {"base": 70, "feature": "bass_energy", "scale": 115},
            },
            {
                "type": "particles",
                "id": "prompt_particles",
                "count": particle_count,
                "velocity_feature": "treble_energy",
                "burst_on": "beat",
            },
        ],
    }
    PresetConfig.model_validate(preset)
    return preset


def _palette(prompt: str) -> dict[str, object]:
    if any(word in prompt for word in ["dark", "cyber", "neon", "night"]):
        return {
            "mode": "reactive",
            "base": [62, 255, 188],
            "accent": [255, 64, 170],
            "beat": [255, 255, 245],
        }
    if any(word in prompt for word in ["warm", "gold", "sun", "amber"]):
        return {
            "mode": "reactive",
            "base": [255, 160, 70],
            "accent": [80, 190, 255],
            "beat": [255, 245, 210],
        }
    if any(word in prompt for word in ["cold", "ice", "blue"]):
        return {
            "mode": "reactive",
            "base": [80, 210, 255],
            "accent": [210, 120, 255],
            "beat": [245, 255, 255],
        }
    return {
        "mode": "reactive",
        "base": [180, 80, 255],
        "accent": [80, 220, 255],
        "beat": [255, 255, 255],
    }


def _safe_name(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned or "custom_prompt"
