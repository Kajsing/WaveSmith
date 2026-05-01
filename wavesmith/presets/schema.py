"""Preset schema models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PresetModule(BaseModel):
    """A visual module declared by a preset."""

    model_config = ConfigDict(extra="allow")

    type: str
    id: str


class PresetConfig(BaseModel):
    """Minimal v1 preset contract."""

    model_config = ConfigDict(extra="allow")

    name: str
    version: int
    description: str
    canvas: dict[str, Any]
    palette: dict[str, Any]
    modules: list[PresetModule] = Field(min_length=1)
