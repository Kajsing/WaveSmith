from PIL import Image, ImageChops, ImageDraw

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext
from wavesmith.visuals.elemental_field import draw_elemental_field


def test_draw_elemental_field_changes_image() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()
    ctx = FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=160,
        height=90,
        time_seconds=1.25,
        progress=0.5,
        features={
            "rms": 0.7,
            "bass_energy": 0.8,
            "treble_energy": 0.6,
            "beat": True,
        },
        preset_name="test",
        palette_base=(34, 214, 255),
        palette_accent=(255, 76, 64),
        palette_beat=(255, 246, 210),
    )
    module = PresetModule(
        type="elemental_field",
        id="fire",
        element="fire",
        density=18,
        bands=3,
        opacity=0.7,
    )

    draw_elemental_field(ctx, module)

    assert ImageChops.difference(before, image).getbbox() is not None


def test_draw_lightning_element_changes_image() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()
    ctx = FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=160,
        height=90,
        time_seconds=1.25,
        progress=0.5,
        features={
            "rms": 0.7,
            "bass_energy": 0.8,
            "treble_energy": 0.9,
            "beat": True,
        },
        preset_name="test",
        palette_base=(34, 214, 255),
        palette_accent=(255, 76, 64),
        palette_beat=(255, 246, 210),
    )
    module = PresetModule(
        type="elemental_field",
        id="lightning",
        element="lightning",
        density=24,
        bands=5,
        opacity=0.8,
    )

    draw_elemental_field(ctx, module)

    assert ImageChops.difference(before, image).getbbox() is not None
