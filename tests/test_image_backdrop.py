from PIL import Image, ImageChops, ImageDraw

from wavesmith.presets.schema import PresetModule
from wavesmith.visuals.base import FrameContext
from wavesmith.visuals.image_backdrop import draw_image_backdrop


def test_draw_image_backdrop_changes_image(tmp_path) -> None:
    source = tmp_path / "backdrop.png"
    Image.new("RGB", (80, 40), (220, 80, 20)).save(source)
    image = Image.new("RGB", (160, 90), (0, 0, 0))
    before = image.copy()
    ctx = FrameContext(
        image=image,
        draw=ImageDraw.Draw(image),
        width=160,
        height=90,
        time_seconds=1.0,
        progress=0.5,
        features={"rms": 0.5, "bass_energy": 0.5},
        preset_name="test",
        palette_base=(180, 28, 8),
        palette_accent=(255, 78, 16),
        palette_beat=(255, 238, 150),
    )

    draw_image_backdrop(
        ctx,
        PresetModule(type="image_backdrop", id="image", path=str(source), dim=0.2),
    )

    assert ImageChops.difference(before, image).getbbox() is not None
