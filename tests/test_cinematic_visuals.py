from PIL import Image, ImageChops, ImageDraw

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext
from wavesmith.visuals.cinematic_backdrop import draw_cinematic_backdrop
from wavesmith.visuals.portal_ring import draw_portal_ring
from wavesmith.visuals.spectrum_wall import draw_spectrum_wall


def _ctx(image: Image.Image) -> FrameContext:
    return FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=image.width,
        height=image.height,
        time_seconds=1.0,
        progress=0.5,
        features={
            "rms": 0.7,
            "bass_energy": 0.8,
            "treble_energy": 0.65,
            "beat": True,
            "spectrum": [0.2, 0.8, 0.4, 0.9, 0.5, 0.7],
            "waveform_preview": [0.3, 0.6, 0.2, 0.8, 0.4, 0.7],
        },
        preset_name="test",
        palette_base=(180, 28, 8),
        palette_accent=(255, 78, 16),
        palette_beat=(255, 238, 150),
    )


def test_draw_portal_ring_changes_image() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()

    draw_portal_ring(_ctx(image), PresetModule(type="portal_ring", id="portal"))

    assert ImageChops.difference(before, image).getbbox() is not None


def test_draw_spectrum_wall_changes_image() -> None:
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()

    draw_spectrum_wall(_ctx(image), PresetModule(type="spectrum_wall", id="wall"))

    assert ImageChops.difference(before, image).getbbox() is not None


def test_draw_cinematic_backdrop_changes_image() -> None:
    image = Image.new("RGB", (160, 90), (40, 40, 40))
    before = image.copy()

    draw_cinematic_backdrop(_ctx(image), PresetModule(type="cinematic_backdrop", id="backdrop"))

    assert ImageChops.difference(before, image).getbbox() is not None
