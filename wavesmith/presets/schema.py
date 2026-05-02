"""Preset schema models."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Color = tuple[int, int, int]


def _validate_color(value: list[int] | tuple[int, int, int]) -> Color:
    if len(value) != 3:
        raise ValueError("Color must contain exactly three RGB values.")
    color = tuple(int(channel) for channel in value)
    if any(channel < 0 or channel > 255 for channel in color):
        raise ValueError("Color channels must be between 0 and 255.")
    return color


class PresetModule(BaseModel):
    """A visual module declared by a preset."""

    model_config = ConfigDict(extra="allow")

    type: Literal[
        "center_orb",
        "spectrum_ring",
        "waveform_ribbon",
        "particles",
        "shader_field",
        "elemental_field",
        "portal_ring",
        "spectrum_wall",
        "cinematic_backdrop",
        "image_backdrop",
    ]
    id: str = Field(min_length=1)


class CanvasConfig(BaseModel):
    """Canvas-level preset settings."""

    model_config = ConfigDict(extra="allow")

    background: str = Field(min_length=1)
    glow: bool = True


class PaletteConfig(BaseModel):
    """Reactive RGB palette."""

    model_config = ConfigDict(extra="allow")

    mode: str = "reactive"
    base: Color
    accent: Color
    beat: Color

    @field_validator("base", "accent", "beat", mode="before")
    @classmethod
    def validate_color(cls, value: list[int] | tuple[int, int, int]) -> Color:
        """Validate color triples before coercion."""
        return _validate_color(value)


class WatermarkConfig(BaseModel):
    """Default watermark settings."""

    model_config = ConfigDict(extra="allow")

    enabled: bool = True
    text: str | None = None
    position: str = "bottom_right"
    opacity: float = Field(default=0.55, ge=0.0, le=1.0)


class PresetMetadata(BaseModel):
    """Human-facing browsing metadata for a preset."""

    model_config = ConfigDict(extra="allow")

    family: str = Field(default="general", min_length=1)
    tags: list[str] = Field(default_factory=list)

    @field_validator("family", mode="before")
    @classmethod
    def validate_family(cls, value: str) -> str:
        """Normalize family values for stable CLI filtering."""
        return str(value).strip().lower()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        """Normalize tag values while preserving YAML readability."""
        tags = [str(tag).strip().lower() for tag in value if str(tag).strip()]
        return sorted(set(tags))


class PresetConfig(BaseModel):
    """Validated v1 preset contract."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1)
    version: int = Field(ge=1)
    description: str = Field(min_length=1)
    metadata: PresetMetadata = Field(default_factory=PresetMetadata)
    canvas: CanvasConfig
    palette: PaletteConfig
    watermark: WatermarkConfig | None = None
    modules: list[PresetModule] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_module_ids(self) -> "PresetConfig":
        """Require module IDs to be unique inside one preset."""
        module_ids = [module.id for module in self.modules]
        if len(module_ids) != len(set(module_ids)):
            raise ValueError("Preset module IDs must be unique.")
        return self
