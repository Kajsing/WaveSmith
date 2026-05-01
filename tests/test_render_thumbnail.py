from PIL import Image

from wavesmith.presets.loader import load_preset
from wavesmith.render.thumbnail import write_poster_thumbnail


def test_write_poster_thumbnail_creates_jpg(tmp_path) -> None:
    output = tmp_path / "poster.jpg"
    features = {
        "rms": 0.6,
        "bass_energy": 0.7,
        "treble_energy": 0.4,
        "spectrum": [0.1, 0.8, 0.4, 0.9],
    }

    write_poster_thumbnail(
        output_image=output,
        preset=load_preset("shader_bloom"),
        features=features,
        title="test song",
        width=320,
        height=180,
    )

    assert output.exists()
    with Image.open(output) as image:
        assert image.size == (320, 180)
        assert image.mode == "RGB"
